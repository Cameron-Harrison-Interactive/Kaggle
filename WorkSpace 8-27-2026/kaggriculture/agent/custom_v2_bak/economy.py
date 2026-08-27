"""
economy.py — market orders and hiring decisions.

Emits the `market` list of the action dict. Kept SEPARATE from tasks because
market decisions have no unit-routing cost — they just execute at the market
lockstep.
"""

from .board import CROPS, ANIMALS, PRODUCTS


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def hire_cost(hires_today):
    return _fib(hires_today)


def _count_animals(board):
    counts = {"SHEEP": 0, "COW": 0, "GOOSE": 0}
    for (x, y) in board.animals():
        a = board.tile(x, y).get("animal")
        if a in counts:
            counts[a] += 1
    # include shed'd (bought but not placed)
    for a in counts:
        counts[a] += board.shed.get(a, 0)
    return counts


def _count_animal_slots(board):
    """How many built pasture/coop slots exist (including empty ones)."""
    p = 0
    c = 0
    for (x, y) in board.owned_tiles():
        t = board.tile(x, y)
        if isinstance(t, dict):
            k = t.get("kind")
            if k == "PASTURE" and "animal" in t: p += 1
            elif k == "PASTURE": p += 1
            elif k == "COOP" and "animal" in t: c += 1
            elif k == "COOP": c += 1
    return p, c


def plan_market_orders(board, cfg):
    """Return the `market` list for this turn.

    cfg is a dict with:
      field_size_target : total wheat tiles we're aiming for
      hires_target      : hires per day
      sheep_target, cow_target, goose_target : herd targets
      buy_land          : True/False whether to unlock quadrants opportunistically
    """
    orders = []
    day = board.day
    hour = board.hour
    money = board.money

    field_size = cfg["field_size_target"]
    hires_target = cfg["hires_target"]
    sheep_t = cfg.get("sheep_target", 0)
    cow_t   = cfg.get("cow_target", 0)
    goose_t = cfg.get("goose_target", 0)
    buy_land = cfg.get("buy_land", False)

    # ---------- HIRING: front-load at hour 1 -----------
    if hour == 1 and board.hires_today < hires_target:
        want = hires_target - board.hires_today
        cash = money
        n_hires = 0
        for i in range(want):
            c = hire_cost(board.hires_today + i)
            if cash >= c and n_hires < 10:
                cash -= c
                n_hires += 1
            else:
                break
        for _ in range(n_hires):
            orders.append(["HIRE"])
        money = cash  # reserve

    # ---------- BUY LAND: opportunistic at start of day ------------
    if buy_land and hour == 0:
        unlocked = set(board.unlocked)
        # priorities: NE > SW > SE, but only if we've got enough headroom
        LAND_PRICES = {"NE": 1000, "SW": 2000, "SE": 4000}
        LAND_RESERVE = 500  # keep at least this much after purchase for seeds/animals
        for quad in ("NE", "SW", "SE"):
            if quad in unlocked:
                continue
            price = LAND_PRICES[quad]
            if money >= price + LAND_RESERVE:
                orders.append(["BUY_LAND"])
                money -= price
            break  # one land purchase per day

    # ---------- BUY ANIMALS ----------
    # Rule: only buy an animal if we can actually feed it. Each animal eats 1
    # wheat/day. Wheat comes online at day 4 (first harvest). Before day 4,
    # every animal in inventory needs 1 wheat *already in shed* per day until
    # day 4. After day 4, we can rely on the field being productive.
    if len(orders) < 10 and hour <= 3:  # only buy early in the day
        counts = _count_animals(board)
        total_animals_now = sum(counts.values())
        wheat_now = board.shed.get("WHEAT", 0)
        # Feed we need to survive to day 4 (first harvest) for existing animals
        days_to_harvest = max(0, 4 - day)
        feed_needed_existing = total_animals_now * days_to_harvest
        # Each new animal we add needs 1 wheat/day to day 4
        feed_per_new = days_to_harvest
        # Cash reserve rule: keep at least $200 for daily hires + emergencies
        cash_reserve = 300 if day == 0 else 100

        n_pasture, n_coop = _count_animal_slots(board)
        pasture_used = counts["SHEEP"] + counts["COW"]

        def _can_feed_one_more():
            # existing feed already committed; new animal takes feed_per_new more
            return (wheat_now - feed_needed_existing) >= feed_per_new

        if counts["SHEEP"] < sheep_t and pasture_used < n_pasture \
                and money >= 500 + cash_reserve and _can_feed_one_more():
            orders.append(["BUY_ANIMAL", "SHEEP", 1])
            money -= 500
        elif counts["COW"] < cow_t and pasture_used < n_pasture \
                and money >= 400 + cash_reserve and _can_feed_one_more():
            orders.append(["BUY_ANIMAL", "COW", 1])
            money -= 400
        elif counts["GOOSE"] < goose_t and counts["GOOSE"] < n_coop \
                and money >= 300 + cash_reserve and _can_feed_one_more():
            orders.append(["BUY_ANIMAL", "GOOSE", 1])
            money -= 300

    # ---------- SEEDS: buy enough for the CURRENTLY empty CROP tiles,
    #                    not for the full theoretical field size. Otherwise
    #                    we blow $780 on 78 seeds before we've planted 15.
    empty_crop_tiles = 0
    from .plan import full_layout
    layout = full_layout()
    for (x, y), role in layout.items():
        if role == "CROP" and not board.is_locked(x, y) and board.tile(x, y) is None:
            empty_crop_tiles += 1
    have_seed = board.seeds.get("WHEAT", 0)
    # buffer: 5 seeds extra so we can plant immediately after harvest
    target_seeds = min(field_size, empty_crop_tiles + 5)
    seed_deficit = target_seeds - have_seed
    if seed_deficit > 0 and money > 200 and len(orders) < 10:
        buy_n = min(seed_deficit, 10 - len(orders))
        if buy_n > 0:
            orders.append(["BUY_SEED", "WHEAT", buy_n])

    # ---------- SELL WHEAT (above reserve) ----------
    # Reserve enough wheat to feed the planned herd for MANY days. Under-
    # reserve starves the herd during production dips (weeds, harvest lag).
    planned_herd = sheep_t + cow_t + goose_t
    current_herd = sum(_count_animals(board).values())
    # Bank ~7 days of feed for the actual herd, and always at least 3 days
    # of the target-size herd (so we don't dip right before we buy more).
    wheat_reserve = max(6, current_herd * 7, planned_herd * 3)
    wheat_in_shed = board.shed.get("WHEAT", 0)
    if wheat_in_shed > wheat_reserve and len(orders) < 10:
        n_sell = min(wheat_in_shed - wheat_reserve, 10 - len(orders))
        if n_sell > 0:
            orders.append(["SELL", "WHEAT", n_sell])

    # ---------- SELL animal products & fertilizer ----------
    for item in ("FERTILIZER", "WOOL", "MILK", "EGG"):
        if len(orders) >= 10:
            break
        n = board.shed.get(item, 0)
        if n > 0:
            orders.append(["SELL", item, n])

    # ---------- END-GAME FIRE SALE ----------
    # Terminal day ~D28-D30. Dump everything BUT keep enough wheat to feed
    # remaining animals through the last day (game runs to end of D29 = step 719).
    if day >= 28 and len(orders) < 10:
        current_herd = sum(_count_animals(board).values())
        days_left = max(0, 30 - day)  # rough
        end_feed_reserve = current_herd * (days_left + 1)
        for item in ("CARROT", "TOMATO", "STRAWBERRY", "MELON",
                     "EGG", "MILK", "WOOL", "FERTILIZER"):
            if len(orders) >= 10:
                break
            n = board.shed.get(item, 0)
            if n > 0:
                orders.append(["SELL", item, n])
        # Wheat: keep feed reserve
        n_wheat = board.shed.get("WHEAT", 0)
        n_sell = max(0, n_wheat - end_feed_reserve)
        if n_sell > 0 and len(orders) < 10:
            orders.append(["SELL", "WHEAT", n_sell])

    return orders[:10]
