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
        money = cash

    # (Dynamic bonus hires experiment: -$16k avg. Reverted. Fib cost of the
    # 13th+ hire ($233-$610) makes marginal hands not pay for themselves.)

    # ---------- BUY LAND: opportunistic at start of day ------------
    # Tighter reserves — SW/SE unlock as EARLY as possible so strawberry
    # gets its full production window (planted D6 vs D13 = double harvests).
    if buy_land and hour == 0:
        unlocked = set(board.unlocked)
        LAND_PRICES = {"NE": 1000, "SW": 2000, "SE": 4000}
        LAND_RESERVE = {"NE": 20, "SW": 20, "SE": 400}  # aggressive: buy SW ASAP
        # If cfg says skip_se, don't buy SE ($4000). BT tape shows meta bots
        # unlock only NW+NE+SW; the $4000 SE spend is often not worth it
        # given how late SE tiles would come online.
        skip_se = cfg.get("skip_se", False)
        skip_sw = cfg.get("skip_sw", False)
        for quad in ("NE", "SW", "SE"):
            if quad in unlocked:
                continue
            if quad == "SE" and skip_se:
                break
            if quad == "SW" and skip_sw:
                break
            price = LAND_PRICES[quad]
            if money >= price + LAND_RESERVE[quad]:
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
        feed_per_new = days_to_harvest
        # Cash reserve: keep enough to buy SW land ($2000) as soon as possible.
        # Without this, we blow all cash on animals D0-D3 and can't unlock SW
        # until D13, missing 5+ strawberry productions.
        cash_reserve = 100 if day == 0 else 20   # very loose

        n_pasture, n_coop = _count_animal_slots(board)
        pasture_used = counts["SHEEP"] + counts["COW"]

        # Mid-game rule: don't buy replacements if wheat is critically low.
        # Rebuying starving animals wastes $500 that could stabilize us.
        planned_herd_local = sheep_t + cow_t + goose_t
        wheat_safety_floor = planned_herd_local * 3
        starving_market = wheat_now < wheat_safety_floor and day >= 5

        def _can_feed_one_more():
            if starving_market:
                return False
            return (wheat_now - feed_needed_existing) >= feed_per_new

        # (Multiple attempts at D0 bootstrap wheat + animal all hurt solo
        # by $30k+; the cash drain from wheat purchase blocks other actions
        # for too many days.)

        # Multi-buy loop: buy as many animals as we can afford this hour.
        # Preference order: SHEEP (best margin) > COW > GOOSE (cheapest).
        # Each iteration re-evaluates cash and feed constraints.
        while len(orders) < 10:
            local_counts = dict(counts)
            for o in orders:
                if o[0] == "BUY_ANIMAL":
                    local_counts[o[1]] = local_counts.get(o[1], 0) + 1
            local_pasture_used = local_counts["SHEEP"] + local_counts["COW"]
            local_total = sum(local_counts.values())
            # feed cost for animals we already have PLUS ones we've queued
            feed_needed_local = local_total * max(0, 4 - day)
            can_feed = not starving_market and (wheat_now - feed_needed_local) >= max(0, 4-day)
            if not can_feed:
                break
            if local_counts["SHEEP"] < sheep_t and local_pasture_used < n_pasture \
                    and money >= 500 + cash_reserve:
                orders.append(["BUY_ANIMAL", "SHEEP", 1])
                money -= 500
            elif local_counts["COW"] < cow_t and local_pasture_used < n_pasture \
                    and money >= 400 + cash_reserve:
                orders.append(["BUY_ANIMAL", "COW", 1])
                money -= 400
            elif local_counts["GOOSE"] < goose_t and local_counts["GOOSE"] < n_coop \
                    and money >= 300 + cash_reserve:
                orders.append(["BUY_ANIMAL", "GOOSE", 1])
                money -= 300
            else:
                break

    # ---------- SEEDS ----------
    # Count empties by role and buy proportionally so we don't drain cash on
    # unplanted seeds. Strawberry seeds are $100 each — over-buying tanks us.
    from .plan import full_layout
    layout = full_layout()
    empty_wheat_tiles = 0
    empty_straw_tiles = 0
    empty_melon_tiles = 0
    empty_carrot_tiles = 0
    for (x, y), role in layout.items():
        if board.is_locked(x, y) or board.tile(x, y) is not None:
            continue
        if role == "CROP":
            empty_wheat_tiles += 1
        elif role == "CARROT":
            empty_carrot_tiles += 1
        elif role == "STRAW":
            empty_straw_tiles += 1
        elif role == "MELON":
            empty_melon_tiles += 1

    # WHEAT seeds
    have_wheat_seed = board.seeds.get("WHEAT", 0)
    # Cap at 25 seeds max - hands can't plant all 50 empties in one turn,
    # excess seeds ($10 each) waste cash. Seed 1 had 38 unused = $380.
    # Cap 25 saves ~$130 seed-cash waste vs unbounded (seed 1 had 38 unused)
    target_wheat_seeds = min(field_size, empty_wheat_tiles + 5, 25)
    wheat_deficit = target_wheat_seeds - have_wheat_seed
    if wheat_deficit > 0 and money > 200 and len(orders) < 10:
        buy_n = min(wheat_deficit, 10 - len(orders))
        orders.append(["BUY_SEED", "WHEAT", buy_n])
        money -= 10 * buy_n

    # STRAWBERRY seeds — only if we have land unlocked and empty straw tiles
    have_straw_seed = board.seeds.get("STRAWBERRY", 0)
    target_straw_seeds = empty_straw_tiles
    straw_deficit = target_straw_seeds - have_straw_seed
    if straw_deficit > 0 and money > 500 and len(orders) < 10:
        buy_n = min(straw_deficit, 3, 10 - len(orders))
        if buy_n > 0:
            orders.append(["BUY_SEED", "STRAWBERRY", buy_n])
            money -= 100 * buy_n

    # MELON seeds — $80 each, plant window closes ~D16.
    if day <= 17 and len(orders) < 10:
        have_melon_seed = board.seeds.get("MELON", 0)
        target_melon_seeds = empty_melon_tiles
        melon_deficit = target_melon_seeds - have_melon_seed
        if melon_deficit > 0 and money > 400:
            buy_n = min(melon_deficit, 3, 10 - len(orders))
            if buy_n > 0:
                orders.append(["BUY_SEED", "MELON", buy_n])
                money -= 80 * buy_n

    # CARROT seeds — $20 each, 3-day cycle. Plant window: last plant ~D26
    # (harvest D29). Great for early cash injection.
    if day <= 25 and len(orders) < 10:
        have_carrot_seed = board.seeds.get("CARROT", 0)
        target_carrot_seeds = empty_carrot_tiles
        carrot_deficit = target_carrot_seeds - have_carrot_seed
        if carrot_deficit > 0 and money > 150:
            buy_n = min(carrot_deficit, 5, 10 - len(orders))
            if buy_n > 0:
                orders.append(["BUY_SEED", "CARROT", buy_n])
                money -= 20 * buy_n

    # ---------- WHEAT: sell surplus / buy shortage ----------
    # Reserve = feed buffer. Sell above; BUY below (last-resort) to prevent
    # herd death when field production dips.
    planned_herd = sheep_t + cow_t + goose_t
    current_herd = sum(_count_animals(board).values())
    if day >= 25:
        wheat_reserve = max(6, current_herd * 15, planned_herd * 5)
    else:
        wheat_reserve = max(6, current_herd * 10, planned_herd * 3)
    wheat_in_shed = board.shed.get("WHEAT", 0)

    if wheat_in_shed > wheat_reserve and len(orders) < 10:
        n_sell = min(wheat_in_shed - wheat_reserve, 10 - len(orders))
        if n_sell > 0:
            orders.append(["SELL", "WHEAT", n_sell])
    # Emergency purchase: shed critically low + we have cash. Wheat market
    # buy price ≈ $25, cheaper than losing a $500 sheep.
    elif current_herd > 0 and wheat_in_shed < int(current_herd * 1) \
            and money > 200 and len(orders) < 10:
        n_buy = min(current_herd * 3, 10 - len(orders))
        if n_buy > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", n_buy])
            money -= 30 * n_buy

    # (Opportunistic FERT buy tested: hurt in H2H because buying fert
    # increased own fert inventory and pushed our sell price lower.)

    # ---------- SELL animal products, fertilizer, high-value crops ----------
    # Keep some fertilizer reserved for strawberry/tomato fertilization.
    # Rough count: 4 fert per strawberry plant over its 16-day life.
    from .plan import full_layout
    layout = full_layout()
    n_straw_tiles = sum(1 for (x, y), r in layout.items()
                        if r == "STRAW" and not board.is_locked(x, y))
    # Reserve enough fert for a wave of strawberry fertilization. Cap at 12
    # so we don't hoard too much (each fert=$100 sale opportunity).
    fert_reserve = min(12, n_straw_tiles)

    # Price-gated sells: MELON glut-crashes hard vs BT in H2H (price $272 -> $73
    # from D10 to D22 when we dumped). Only sell melon if price >= floor.
    # Threshold at $150 = still profitable ($1500 per 6-unit plant AT LEAST).
    # Other perishables sell freely — animal products don't recover once idle.
    MIN_MELON_PRICE = 80

    # Non-perishable HOLD-and-sell late: strawberry price rises through game
    # (BT depletes market). Sell aggressively late (D22+) to catch peak.
    # Perishable (EGG/MILK/WOOL): sell freely (shed capacity concern).
    # CARROT: sell freely too (base $35, price stable, above=sqrt at=0.70).
    for item in ("CARROT", "WOOL", "MILK", "EGG"):
        if len(orders) >= 10:
            break
        n = board.shed.get(item, 0)
        if n > 0:
            orders.append(["SELL", item, n])

    # STRAWBERRY: sell all if price above baseline ($120 base), else HOLD
    # unless late-game.
    if len(orders) < 10:
        n_straw = board.shed.get("STRAWBERRY", 0)
        if n_straw > 0:
            straw_price = board.price("STRAWBERRY")
            # Straw gate tested 0..180 (H2H BT 4-seed avg):
            # 0=-87.8k, 100=-87.9k, 120=-88.0k, 150=-88.3k, 180=-89.1k
            # Always-sell wins by small margin — straw price mostly rises,
            # holding rarely helps.
            if straw_price >= 0 or day >= 27:
                orders.append(["SELL", "STRAWBERRY", n_straw])

    # MELON: sell but respect floor. Staggering (max 2/turn) tested worse.
    if len(orders) < 10:
        n_melon = board.shed.get("MELON", 0)
        if n_melon > 0:
            melon_price = board.price("MELON")
            if melon_price >= MIN_MELON_PRICE or day >= 27:
                orders.append(["SELL", "MELON", n_melon])
            # else HOLD (price below floor and not end-game)
    # Fertilizer: sell excess above reserve (price gate tested, hurt H2H)
    if len(orders) < 10:
        n_fert = board.shed.get("FERTILIZER", 0)
        n_sell_fert = max(0, n_fert - fert_reserve)
        if n_sell_fert > 0:
            orders.append(["SELL", "FERTILIZER", n_sell_fert])

    # ---------- END-GAME FIRE SALE ----------
    # Terminal day ~D28-D30. Dump everything BUT:
    # 1) keep wheat to feed remaining animals (game runs to end of D29 = step 719)
    # 2) SKIP MELON if price crashed below $30 — dumping only pushes it lower
    #    (H2H vs V41: MELON price went $172 -> $7 as we dumped, useless)
    if day >= 28 and len(orders) < 10:
        current_herd = sum(_count_animals(board).values())
        days_left = max(0, 30 - day)  # rough
        end_feed_reserve = current_herd * (days_left + 1)
        # Non-melon items — sell freely
        for item in ("STRAWBERRY", "CARROT", "TOMATO",
                     "EGG", "MILK", "WOOL", "FERTILIZER"):
            if len(orders) >= 10:
                break
            n = board.shed.get(item, 0)
            if n > 0:
                orders.append(["SELL", item, n])
        # Melon: only if price is meaningful
        if len(orders) < 10:
            n_melon = board.shed.get("MELON", 0)
            if n_melon > 0 and board.price("MELON") >= 30:
                orders.append(["SELL", "MELON", n_melon])
        # Wheat: keep feed reserve
        n_wheat = board.shed.get("WHEAT", 0)
        n_sell = max(0, n_wheat - end_feed_reserve)
        if n_sell > 0 and len(orders) < 10:
            orders.append(["SELL", "WHEAT", n_sell])

    return orders[:10]
