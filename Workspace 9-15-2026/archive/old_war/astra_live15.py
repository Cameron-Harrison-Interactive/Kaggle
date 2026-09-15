"""
Kaggressure: live-route staged-growth agent.
Standard library only.

Experimental, unbenchmarked candidate:
- 2-goose opening
- target herd: 6 cows, 6 sheep, 8 geese
- hourly shed sales
- live routing with shared resource reservations
- no blind daily action tape

Uses the documented default 10x10 / 24-turn / 30-day game.
"""

import math
from collections import Counter

# ---------- Game tables ----------

CROPS = {
    # seed cost, productive horizon, expected unfertilized units, yield cap
    "WHEAT": (10, 4, 4, 6),
    "CARROT": (20, 3, 3, 4),
    "TOMATO": (50, 11, 4, 4),
    "STRAWBERRY": (100, 16, 4, 4),
    "MELON": (80, 10, 6, 6),
}

ANIMALS = {
    # purchase cost, structure, product, first production, interval, held cap
    "GOOSE": (300, "COOP", "EGG", 4, 1, 4),
    "COW": (400, "PASTURE", "MILK", 8, 2, 6),
    "SHEEP": (500, "PASTURE", "WOOL", 6, 3, 6),
}

# base, throughput, scarcity shape/target, glut shape/target
MARKET = {
    "WHEAT": (25, 400, "sqrt", .80, "log", .20),
    "CARROT": (35, 450, "hinge", 1.00, "sqrt", .70),
    "TOMATO": (60, 200, "hinge", .40, "sqrt", .60),
    "STRAWBERRY": (120, 100, "sqrt", .70, "linear", 1.60),
    "MELON": (250, 300, "log", .20, "sq", 3.60),
    "EGG": (50, 332, "hinge", .40, "log", .20),
    "MILK": (160, 122, "sqrt", .60, "linear", 1.60),
    "WOOL": (200, 105, "log", .20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", .40, "linear", .40),
}

SHOPS = {
    "BAKERY": {"EGG": 1, "WHEAT": 1},
    "PIZZA_SHOP": {"MILK": 1, "TOMATO": 1, "WHEAT": 1},
    "BRUNCH_SPOT": {"EGG": 1, "WHEAT": 1, "STRAWBERRY": 1},
    "YARN_STORE": {"WOOL": 2},
    "ICE_CREAM_SHOP": {"STRAWBERRY": 1, "MILK": 1, "WHEAT": 1},
    "PET_CAFE": {"CARROT": 2},
    "SMOOTHIE_SHOP": {"STRAWBERRY": 1, "MILK": 1},
    "FARMERS_MARKET": {
        "WHEAT": 1, "CARROT": 1, "TOMATO": 1, "STRAWBERRY": 1
    },
}

QUOTAS = {
    "NW": {"COW": 2, "SHEEP": 1, "GOOSE": 2},
    "NE": {"COW": 2, "SHEEP": 2, "GOOSE": 1},
    "SW": {"COW": 1, "SHEEP": 2, "GOOSE": 2},
    "SE": {"COW": 1, "SHEEP": 1, "GOOSE": 3},
}

SHED = ((4, 4), (5, 4), (4, 5), (5, 5))
FIB = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610)
STATE = {}

# ---------- Geometry and prices ----------

def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def shed_near(p):
    return min(SHED, key=lambda s: (distance(p, s), s))


def quadrant(p):
    return ("N" if p[1] < 5 else "S") + ("W" if p[0] < 5 else "E")


def animal_line(p):
    return p[1] in (4, 5)


def move(p, goal):
    dx, dy = goal[0] - p[0], goal[1] - p[1]
    if abs(dx) >= abs(dy) and dx:
        return ["EAST" if dx > 0 else "WEST"]
    if dy:
        return ["SOUTH" if dy > 0 else "NORTH"]
    return ["PASS"]


def shape(name, x, throughput):
    x = max(0.0, x)
    if name == "sqrt":
        return math.sqrt(x)
    if name == "sq":
        return x * x
    if name == "log":
        return math.log1p(x)
    if name == "log10":
        return math.log10(1 + x)
    if name == "hinge":
        u = x / throughput
        return u + 8 * max(0.0, u - 1) ** 2
    return x


def price(item, inventory, overrides=None):
    b, t, below, bt, above, at = MARKET[item]
    o = (overrides or {}).get(item, {})
    b = o.get("base", b)
    t = o.get("T", t)
    anchor = o.get("I0", 10000)
    below = o.get("below_func", below)
    above = o.get("above_func", above)
    bt = o.get("below_target", bt)
    at = o.get("above_target", at)
    scarce = inventory < anchor
    f, target = (below, bt) if scarce else (above, at)
    change = target * b * shape(f, abs(inventory - anchor), t)
    change /= max(1e-12, shape(f, t, t))
    return max(1, int(round(b + change if scarce else b - change)))


def sale_value(item, inventory, quantity, overrides=None):
    value = 0
    for _ in range(max(0, int(quantity))):
        p = price(item, inventory, overrides)
        value += p
        # Documented price-floor rule: floor sales do not increase inventory.
        if p > 1:
            inventory += 1
    return value


def stock_size(inventory):
    return sum(max(0, int(v)) for v in inventory.values())


# ---------- Agent ----------

def agent(obs, configuration=None):
    cfg = configuration or {}
    seat = int(obs["player"])
    day, hour = int(obs["day"]), int(obs["hour"])

    if day == 0 and hour == 0:
        STATE[seat] = {"goals": {}}
    state = STATE.setdefault(seat, {"goals": {}})
    old_goals = state["goals"]

    farm = obs["farms"][seat]
    opponent = obs["farms"][1 - seat]
    private = obs.get("private", {})
    grid = farm["tiles"]
    owned = set(farm.get("unlocked_quadrants", ["NW"]))
    money = float(farm.get("money", 0))
    shed = Counter(private.get("shed", {}))
    seeds = Counter(private.get("seeds", {}))
    inventories = list(private.get("inventories", [{}]))
    positions = [tuple(farm["farmer"])]
    positions += [tuple(p) for p in farm.get("hands", [])]
    while len(inventories) < len(positions):
        inventories.append({})

    market = obs.get("market", {})
    prices = market.get("prices", {})
    market_inventory = market.get("inventory", {})
    overrides = cfg.get("marketParams", {}) or {}
    turns = int(cfg.get("turnsPerDay", 24))
    episodes = int(cfg.get("episodeSteps", 720))
    total_days = max(1, math.ceil(episodes / turns))
    final_day = day >= total_days - 1
    remaining = turns - hour
    step = day * turns + hour
    final_step = episodes - 1

    def quoted(item):
        return prices.get(
            item,
            price(item, market_inventory.get(item, 10000), overrides)
        )

    plants, animals, structures, empty, weeds = [], [], [], [], []
    tile_map = {}
    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            pos = (x, y)
            if quadrant(pos) not in owned:
                continue
            tile_map[pos] = tile
            if tile is None:
                empty.append(pos)
            elif isinstance(tile, dict):
                if tile.get("kind") == "PLANT":
                    plants.append((pos, tile))
                elif tile.get("kind") == "WEED":
                    weeds.append(pos)
                elif tile.get("kind") in ("COOP", "PASTURE"):
                    structures.append((pos, tile))
                    if tile.get("animal"):
                        animals.append((pos, tile))

    counts = Counter(t["crop"] for _, t in plants)
    herd = Counter(t["animal"] for _, t in animals)
    held_animals = Counter({k: shed[k] for k in ANIMALS})
    all_carried = Counter()
    for inv in inventories:
        all_carried.update(inv)
        for kind in ANIMALS:
            held_animals[kind] += int(inv.get(kind, 0))

    opponent_crops = Counter()
    for row in opponent.get("tiles", []):
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                opponent_crops[tile["crop"]] += 1

    demand = Counter({k: 1 for k in MARKET if k != "FERTILIZER"})
    shop_ticks = turns / max(1, int(cfg.get("townShopSellInterval", 4)))
    for shop in obs.get("town", {}).get("unlocked_shops", []):
        for item, qty in SHOPS.get(shop, {}).items():
            demand[item] += qty * shop_ticks

    # ---------- Crop investment model ----------
    # This is a forecast, not a claim to know the opponent's future sales.

    def crop_score(crop, projected_counts=None):
        n = projected_counts if projected_counts is not None else counts
        cost, horizon, units, cap = CROPS[crop]
        if day + horizon >= total_days - 1:
            return -1e9

        # Opening bridge: avoid locking the opening wallet in slow crops.
        if day < 2 and crop not in ("WHEAT", "CARROT"):
            return -1e9

        inv = market_inventory.get(crop, 10000)
        own_supply = n[crop] * units * .65
        opposing_supply = opponent_crops[crop] * units * .45
        future_inv = inv + own_supply + opposing_supply - demand[crop] * horizon
        expected = sale_value(crop, future_inv, units, overrides)

        # Value per occupied day; mild preference for less service-heavy crops.
        score = (expected - cost) / (horizon + 1)
        if crop == "WHEAT" and herd:
            score *= 1.08
        return score

    # ---------- Harvest decisions ----------

    def harvestable(tile):
        crop = tile["crop"]
        units = int(tile.get("yield_units", 0))
        if units <= 0:
            return False
        if final_day:
            return True
        if crop in ("TOMATO", "STRAWBERRY"):
            return True
        age = day - int(tile.get("planted_day", day))
        target = {"WHEAT": 4, "CARROT": 3, "MELON": 6}[crop]
        peak = {"WHEAT": 4, "CARROT": 3, "MELON": 10}[crop]
        lifespan = int(tile.get("max_lifespan_step", -1))
        near_decay = lifespan >= 0 and lifespan <= step + turns
        return units >= target or age >= peak or near_decay

    # ---------- Fertilizer allocation ----------
    # Keep only fertilizer with a plausible profitable use today.

    fert_candidates = []
    if not final_day:
        for pos, tile in plants:
            crop = tile["crop"]
            if int(tile.get("fertilized_until_day", -1)) >= day:
                continue
            if harvestable(tile):
                continue

            age = day - int(tile.get("planted_day", day))
            units = int(tile.get("yield_units", 0))
            extra = 0

            if crop in ("WHEAT", "CARROT", "MELON"):
                start, end = {
                    "WHEAT": (2, 4),
                    "CARROT": (2, 3),
                    "MELON": (6, 12),
                }[crop]
                ticks = sum(start <= age + j <= end for j in range(3))
                extra = min(ticks, max(0, CROPS[crop][3] - units))
            else:
                production = (
                    (8, 9, 10, 11) if crop == "TOMATO"
                    else (10, 12, 14, 16)
                )
                extra = sum(age <= tick <= age + 2 for tick in production)

            value = extra * quoted(crop) - quoted("FERTILIZER")
            if value > 35:
                fert_candidates.append((value, pos))

    fert_candidates.sort(reverse=True)
    fert_total = shed["FERTILIZER"] + all_carried["FERTILIZER"]
    fert_targets = {
        pos for _, pos in fert_candidates[:min(6, fert_total)]
    }
    fert_keep = max(0, len(fert_targets) - all_carried["FERTILIZER"])

    # ---------- Strawberry blueprint quota (TRACE-05) ----------
    # Measured on the stored TRACE-05 capture (nb3_tetsu_r5, seed 42): the
    # +$91k gap is dominated by a 33-standing strawberry factory funded d2-8
    # at spend-to-floor priority (~$5-8k/day from d12; strb price ROSE
    # 128->232 all season because town demand eats market inventory, so the
    # 0.65 own-supply forecast can never argmax it — live7 planted zero).
    STRB_TARGET = 33
    # TRACE-05: wheat backbone 24-42 standing through the late game
    # (~$1.2k/day at rising prices 27->50). live14 lesson: starting it d2
    # displaced melon in tile-scarce quad 1 and shrank the d12-14 dump that
    # funds quads 3/4 — wheat begins AFTER the dump (d14), filling the
    # tiles strb die-off frees (Tetsu: wheat 24 -> 42 as strb dies d20+).
    WHEAT_TARGET = 24

    # ---------- Build live tile-service jobs ----------
    # job = (operation, position, argument, priority)

    jobs = []

    for pos, tile in animals:
        kind = tile["animal"]
        cost, structure, product, first, interval, cap = ANIMALS[kind]
        units = int(tile.get("yield_units", 0))
        unfed = int(tile.get("consecutive_unfed", 0))

        if not final_day and not tile.get("fed_today"):
            jobs.append(("FEED", pos, None, 1400 if unfed >= 1 else 760))

        if units:
            priority = 1100 if final_day or units >= cap - 1 else 730
            jobs.append(("HARVEST", pos, None, priority))

        if tile.get("fertilizer_available"):
            jobs.append((
                "COLLECT_FERTILIZER", pos, None,
                420 + min(200, quoted("FERTILIZER"))
            ))

        # Daily fed+care banks bonuses, including nonproduction days.
        if not final_day and not tile.get("cared_today"):
            jobs.append(("CARE", pos, None, 440))

    for pos, tile in plants:
        ready = harvestable(tile)
        if ready:
            jobs.append(("HARVEST", pos, None, 1200 if final_day else 900))
        elif not final_day and not tile.get("watered_today"):
            dry = int(tile.get("consecutive_unwatered", 0))
            jobs.append(("WATER", pos, None, 1400 if dry >= 1 else 740))

        if pos in fert_targets:
            jobs.append(("FERTILIZE", pos, None, 470))

    # Allocate actual unplaced animal stock to appropriate line cells.
    available_sites = [
        pos for pos, tile in tile_map.items()
        if animal_line(pos) and (
            tile is None
            or (
                isinstance(tile, dict)
                and (
                    tile.get("kind") == "WEED"
                    or (
                        tile.get("kind") in ("COOP", "PASTURE")
                        and not tile.get("animal")
                    )
                )
            )
        )
    ]

    qherd = Counter((quadrant(pos), tile["animal"]) for pos, tile in animals)
    installation = set()

    if not final_day:
        for kind in ("GOOSE", "COW", "SHEEP"):
            for _ in range(held_animals[kind]):
                matching = []
                for pos in available_sites:
                    if pos in installation:
                        continue
                    q = quadrant(pos)
                    if qherd[q, kind] >= QUOTAS[q][kind]:
                        continue
                    tile = tile_map[pos]
                    if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
                        if tile["kind"] != ANIMALS[kind][1]:
                            continue
                    existing = isinstance(tile, dict) and tile.get("kind") == ANIMALS[kind][1]
                    matching.append((
                        0 if existing else 1,
                        distance(pos, shed_near(pos)), pos
                    ))
                if not matching:
                    break
                pos = min(matching)[2]
                installation.add(pos)
                qherd[quadrant(pos), kind] += 1
                jobs.append(("INSTALL", pos, kind, 560))

    # Reserve the central rows for the eventual herd.
    crop_empty = [p for p in empty if not animal_line(p)]
    crop_weeds = [p for p in weeds if not animal_line(p)]

    plant_choices = [
        c for c in CROPS if seeds[c] > 0 and crop_score(c) > 0
    ]
    # Blueprint quota: strawberry creates PLANT jobs even while its score
    # gate is closed, otherwise quota seeds could never be sown.
    if (not final_day and seeds["STRAWBERRY"] > 0
            and counts["STRAWBERRY"] < STRB_TARGET
            and "STRAWBERRY" not in plant_choices):
        plant_choices.append("STRAWBERRY")
    if (not final_day and 14 <= day <= 25 and seeds["WHEAT"] > 0
            and counts["WHEAT"] < WHEAT_TARGET
            and "WHEAT" not in plant_choices):
        plant_choices.append("WHEAT")
    if plant_choices and not final_day:
        for pos in crop_empty:
            jobs.append(("PLANT", pos, None, 340))
        for pos in crop_weeds:
            jobs.append(("CLEAR", pos, None, 260))

    # ---------- Worker dispatch ----------
    # Shared reservations prevent duplicate tile service and overspending
    # the same shed stock / seed inventory within a single turn.

    free_shed = Counter(shed)
    free_seeds = Counter(seeds)
    claimed = set()
    new_goals = {}
    actions = [["PASS"] for _ in positions]

    def needs_plant_followup(i):
        """Successful planting creates a mandatory same-tile WATER follow-up.

        Use observed tile state: a failed PLANT must not create phantom work.
        """
        old = old_goals.get(i)
        if not old or old[0] != "PLANT":
            return False

        target = old[1]
        if positions[i] != target:
            return False

        tile = tile_map.get(target)
        return (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and int(tile.get("planted_day", -1)) == day
            and not tile.get("watered_today", False)
        )

    def worker_order(i):
        old = old_goals.get(i)
        at_goal = bool(old and positions[i] == old[1])
        inv = inventories[i]
        supplied = inv.get("WHEAT", 0) + inv.get("FERTILIZER", 0)

        # Planting follow-ups execute before another worker can claim
        # their tile for a different chore.
        return (
            not needs_plant_followup(i),
            not at_goal,
            -supplied,
            i,
        )

    def output_for(job, pos, inv):
        """Return next action, travel goal, estimated steps, resource."""
        op, target, arg, priority = job
        resource = None
        qty = 0

        if op == "FEED":
            resource, qty = "WHEAT", 1
        elif op == "FERTILIZE":
            resource, qty = "FERTILIZER", 1
        elif op == "INSTALL":
            resource, qty = arg, 1

        if resource and int(inv.get(resource, 0)) < qty:
            if free_shed[resource] <= 0:
                return None
            source = shed_near(pos)
            travel = distance(pos, source) + 1 + distance(source, target)
            take = min(free_shed[resource], 2 if resource == "WHEAT" else 1)
            if pos != source:
                return move(pos, source), source, travel + 1, None
            return ["PICKUP", resource, take], source, travel + 1, (resource, take)

        if op == "CARE":
            tile = tile_map[target]
            if not tile.get("fed_today"):
                return None

        if op == "INSTALL":
            tile = tile_map[target]
            if tile is None:
                command = ["BUILD_" + ANIMALS[arg][1]]
            elif tile.get("kind") == "WEED":
                command = ["DIG"]
            else:
                command = ["PLACE", arg]
        elif op == "CLEAR":
            command = ["DIG"]
        elif op == "PLANT":
            options = [c for c in plant_choices if free_seeds[c] > 0]
            if not options:
                return None
            # Blueprint quota: strawberry overrides the argmax while the
            # factory is under target (real price rose 128->232 all season;
            # the forecast model can never express that).
            if (counts["STRAWBERRY"] < STRB_TARGET
                    and free_seeds["STRAWBERRY"] > 0):
                crop = "STRAWBERRY"
            elif (14 <= day <= 25 and counts["WHEAT"] < WHEAT_TARGET
                    and free_seeds["WHEAT"] > 0):
                crop = "WHEAT"
            else:
                crop = max(options, key=lambda c: (crop_score(c), c))
            command = ["PLANT", crop]
        else:
            command = [op]

        action_steps = 2 if op == "PLANT" else 1
        travel = distance(pos, target) + action_steps

        if pos != target:
            return move(pos, target), target, travel, None
        return command, target, travel, None

    for i in sorted(range(len(positions)), key=worker_order):
        pos, inv = positions[i], inventories[i]

        # PLANT -> WATER is an execution commitment, not a soft preference.
        # The original planting feasibility check already reserves two
        # action slots; this branch enforces the second one.
        if needs_plant_followup(i):
            target = old_goals[i][1]
            if target not in claimed:
                actions[i] = ["WATER"]
                claimed.add(target)
                new_goals[i] = ("WATER", target, None)
                continue

        source = shed_near(pos)
        home_distance = distance(pos, source)

        cargo = {
            item: int(qty) for item, qty in inv.items()
            if item in MARKET and qty > 0
        }
        sale_cargo = {
            item: qty for item, qty in cargo.items()
            if item not in ("WHEAT", "FERTILIZER")
        }
        cargo_value = sum(qty * quoted(item) for item, qty in sale_cargo.items())

        # Final-day inventory has to reach the shed before the last sale.
        liquidation_load = stock_size(cargo) if final_day else stock_size(sale_cargo)
        force_home = (
            final_day and liquidation_load > 0
            and remaining <= home_distance + 3
        )

        choices = []
        if liquidation_load > 0:
            deposit_priority = (
                3000 if force_home
                else 360 + min(350, cargo_value / 5)
            )
            if final_day:
                deposit_priority += 350
            # DROP loses overflow. Do not knowingly issue an overflowing drop.
            if stock_size(shed) + stock_size(inv) <= 100:
                score = deposit_priority / ((home_distance + 2) ** .70)
                command = ["DROP"] if pos in SHED else move(pos, source)
                choices.append((score, ("DROP", source, None, deposit_priority),
                                command, None))

        for job in jobs:
            op, target, arg, priority = job
            if target in claimed:
                continue

            result = output_for(job, pos, inv)
            if result is None:
                continue
            command, goal, cost, pickup = result

            if cost > remaining:
                continue

            # Planting includes room for same-day water; clearing reserves
            # additional room for a possible plant/water follow-up.
            if op == "CLEAR" and cost + 2 > remaining:
                continue

            if final_day and op in ("HARVEST", "COLLECT_FERTILIZER"):
                # Harvest + deposit + at least one later sale opportunity.
                finish = cost + distance(target, shed_near(target)) + 2
                if finish > remaining:
                    continue

            # Locality, persistence and urgency combine; no rigid quadrant lock.
            score = priority / ((cost + 1) ** .70)
            old = old_goals.get(i)
            if old == (op, target, arg):
                score *= 1.22
            if pos == target:
                score *= 1.18
            if quadrant(pos) == quadrant(target):
                score *= 1.04

            choices.append((score, job, command, pickup))

        if not choices:
            continue

        _, job, command, pickup = max(
            choices, key=lambda z: (z[0], -z[1][1][1], -z[1][1][0])
        )
        op, target, arg, priority = job

        if op != "DROP":
            claimed.add(target)
        new_goals[i] = (op, target, arg)
        actions[i] = command

        if pickup:
            free_shed[pickup[0]] -= pickup[1]
        if command[0] == "PLANT":
            free_seeds[command[1]] -= 1

    state["goals"] = new_goals

    # ---------- Market: sell available production every hour ----------

    orders = []
    max_orders = int(cfg.get("maxMarketOrdersPerTurn", 10))
    virtual_cash = money

    feed_today = sum(not t.get("fed_today") for _, t in animals)
    pending_animals = sum(held_animals.values())
    reserve_wheat = (
        0 if final_day
        else max(4, feed_today + len(animals) + pending_animals
                 - all_carried["WHEAT"])
    )

    sellable = {}
    for item in MARKET:
        keep = reserve_wheat if item == "WHEAT" else (
            fert_keep if item == "FERTILIZER" and not final_day else 0
        )
        # Do not sell stock reserved for a PICKUP issued this turn.
        reserved_pickup = max(0, shed[item] - free_shed[item])
        qty = max(0, shed[item] - max(keep, reserved_pickup))
        if qty:
            sellable[item] = qty

    # Capture high-value inventory first, but retain order capacity for feed.
    sell_order = sorted(
        sellable,
        key=lambda item: -sale_value(
            item, market_inventory.get(item, 10000),
            sellable[item], overrides
        )
    )
    for item in sell_order:
        if len(orders) >= max_orders:
            break
        qty = sellable[item]
        orders.append(["SELL", item, qty])
        estimate = sale_value(
            item, market_inventory.get(item, 10000), qty, overrides
        )
        # Sales are uncertain against simultaneous opponent market orders.
        virtual_cash += estimate * .80

    def buy_order(order, estimated_cost, reserve=0):
        nonlocal virtual_cash
        if len(orders) >= max_orders:
            return False
        if virtual_cash < estimated_cost + reserve:
            return False
        orders.append(order)
        virtual_cash -= estimated_cost
        return True

    # Buy feed before growth. No arbitrary maximum acceptable wheat price:
    # saving an established animal can justify expensive emergency feed.
    if not final_day:
        feed_stock = shed["WHEAT"] + all_carried["WHEAT"]
        feed_target = max(4, feed_today + len(animals) + pending_animals)
        deficit = max(0, feed_target - feed_stock)
        if deficit:
            qty = min(deficit, 30)
            unit_estimate = price(
                "WHEAT",
                market_inventory.get("WHEAT", 10000) - qty,
                overrides
            )
            affordable = int(max(0, virtual_cash - 70) // max(1, unit_estimate))
            qty = min(qty, affordable)
            if qty:
                buy_order(["BUY_PRODUCT", "WHEAT", qty],
                          qty * unit_estimate, 70)

    # ---------- Hire based on workload ----------
    # Actual positions/hands are used each turn; hires are never assumed
    # to exist before they appear in the observation.

    harvest_count = sum(harvestable(t) for _, t in plants)
    prospective = min(12, len(crop_empty), max(0, sum(seeds.values())))
    estimated_work = (
        len(plants) * 2.1
        + len(animals) * 4.8
        + harvest_count * 2
        + prospective * 4.0
        + sum(held_animals.values()) * 6
    )

    desired_hands = max(3, min(14, math.ceil(estimated_work / 21)))
    if day <= 1:
        desired_hands = max(desired_hands, 8)
    if final_day:
        desired_hands = min(14, max(3, math.ceil(
            (harvest_count * 4 + len(animals) * 2) / 20
        )))

    hires_today = int(farm.get("hires_today", len(positions) - 1))
    hire_mult = float(cfg.get("farmHandCostMult", 1))
    if hour <= 3:
        while hires_today < desired_hands and hires_today < len(FIB):
            cost = FIB[hires_today] * hire_mult
            if not buy_order(["HIRE"], cost, 250 if day < 2 else 180):
                break
            hires_today += 1

    # ---------- Opening seed bridge ----------
    if day <= 1:
        for crop, target in (("WHEAT", 8), ("CARROT", 4)):
            need = max(0, target - counts[crop] - seeds[crop])
            if need:
                qty = min(need, int(max(0, virtual_cash - 800) // CROPS[crop][0]))
                if qty:
                    if buy_order(["BUY_SEED", crop, qty],
                                 qty * CROPS[crop][0], 800):
                        seeds[crop] += qty

    # ---------- Opening herd (TRACE-05 cadence) ----------
    # Tetsu's d0 order buys COW 2 + SHEEP 2 alongside the seeds,
    # spend-to-floor; the fert/wool/milk trickle ($300-900/day by d6) then
    # FUNDS the strb build and land. live9's quota starved d3-12 because a
    # geese-only opening ($200/day eggs) cannot fund it. Quad-NW quota
    # (2/1/2 = 5 sites) respected — all opening animals place immediately;
    # land gate and QUOTAS untouched.
    if day <= 1 and not final_day:
        for kind, want in (("GOOSE", 2), ("COW", 2), ("SHEEP", 1)):
            held = herd[kind] + held_animals[kind]
            if held >= want:
                continue
            qty = want - held
            if buy_order(["BUY_ANIMAL", kind, qty],
                         ANIMALS[kind][0] * qty, 80):
                held_animals[kind] += qty

    # ---------- Herd growth ----------
    # Includes animals already in the shed or carried by workers.

    buy_cand = None
    buy_ok = False
    land_ok = False
    targets = {
        "GOOSE": min(8, 2 + max(0, day - 3)),
        "COW": min(6, max(0, (day - 2) // 2)),
        "SHEEP": min(6, max(0, (day - 4) // 2)),
    }

    if day <= 18 and not final_day:
        candidates = []
        for kind in ("GOOSE", "COW", "SHEEP"):
            actual = herd[kind] + held_animals[kind]
            quota = sum(QUOTAS[q][kind] for q in owned)
            goal = min(targets[kind], quota)
            if actual >= goal:
                continue

            cost, structure, product, first, interval, cap = ANIMALS[kind]
            if day + first >= total_days - 2:
                continue
            if kind != "GOOSE" and (
                quoted(product) < (50 if kind == "COW" else 60)
                and quoted("FERTILIZER") < 25
            ):
                continue

            compatible = 0
            for pos in available_sites:
                tile = tile_map[pos]
                if tile is None or tile.get("kind") == "WEED":
                    compatible += 1
                elif tile.get("kind") == structure:
                    compatible += 1
            if compatible <= sum(held_animals.values()):
                continue

            candidates.append((actual / max(1, goal), kind))

        if candidates:
            kind = min(candidates)[1]
            current = herd[kind] + held_animals[kind]
            qty = 2 - current if day == 0 and kind == "GOOSE" else 1
            qty = max(1, qty)
            reserve = 650 if kind == "GOOSE" and current < 2 else 1100
            buy_cand = kind
            buy_ok = buy_order(["BUY_ANIMAL", kind, qty],
                               ANIMALS[kind][0] * qty, reserve)

    # ---------- Land: expansion gate (TRACE-03 fix + TRACE-05 blueprint path) ----------
    # Original paths kept: density>=.80 and cash-rich (cost+8000), day cap 21.
    # TRACE-05/live10/live11 measurements: the strb factory forms late while
    # quad 1 is monopolized — Tetsu buys quad 2 at d6 spend-to-floor. live10's
    # standalone land path starved the seed budget; live11's opening-herd
    # trickle ($500-900/day from d1) funds both. Blueprint path: while the
    # strb quota is unfilled, buy land at spend-to-floor (reserve 150),
    # ordered BEFORE seed buys so land takes cash priority. This diff vs
    # live11 touches ONLY the land gate (animal buys unchanged in this diff).
    if (
        hour <= 3 and 1 <= len(owned) < 4 and day <= 21
        and len(orders) < max_orders
    ):
        crop_capacity = 20 * len(owned)
        density = len(plants) / max(1, crop_capacity)
        land_cost = (1000, 2000, 4000)[len(owned) - 1]
        urgent = sum(
            not t.get("watered_today")
            and int(t.get("consecutive_unwatered", 0)) >= 1
            for _, t in plants
        )
        quota_pressure = (
            1 <= day <= 16 and counts["STRAWBERRY"] < STRB_TARGET
        )
        if ((density >= .80 or money >= land_cost + 8000
                or (quota_pressure and money >= land_cost + 150))
                and urgent <= max(2, len(positions))):
            land_ok = True
            buy_order(["BUY_LAND"], land_cost, 150)

    # ---------- Strawberry blueprint quota: spend-to-floor funding ----------
    # TRACE-05 cadence: Tetsu bought 33 strb seeds across d2-8 with money at
    # $27-2k (feed and herd keep priority; the argmax pipeline yields cash
    # to this quota). Replant-on-death keeps the factory at target through
    # d16; natural die-off ends it d20+ exactly like the captured run.
    if 1 <= day <= 16 and not final_day:
        strb_gap = STRB_TARGET - counts["STRAWBERRY"] - seeds["STRAWBERRY"]
        if strb_gap > 0:
            qty = min(2, strb_gap, int(max(0, virtual_cash - 150) // 100))
            if qty > 0 and buy_order(
                ["BUY_SEED", "STRAWBERRY", qty], 100 * qty, 150
            ):
                seeds["STRAWBERRY"] += qty

    # ---------- Wheat backbone quota funding (post-dump window) ----------
    # Cheap seeds ($10), spend-to-floor, after the strb quota. Window
    # d14-25: begins after the melon dump frees capital and tiles.
    if 14 <= day <= 25 and not final_day:
        wheat_gap = WHEAT_TARGET - counts["WHEAT"] - seeds["WHEAT"]
        if wheat_gap > 0:
            qty = min(4, wheat_gap, int(max(0, virtual_cash - 150) // 10))
            if qty > 0 and buy_order(
                ["BUY_SEED", "WHEAT", qty], 10 * qty, 150
            ):
                seeds["WHEAT"] += qty

    # ---------- Crop replacement / expansion seed pipeline ----------
    if day >= 2 and not final_day:
        standing_seeds = sum(seeds[c] for c in CROPS)
        slots = len(crop_empty) + sum(
            harvestable(t) and t["crop"] not in ("TOMATO", "STRAWBERRY")
            for _, t in plants
        )

        # Seed stock does not imply permission to exceed tending capacity.
        field_capacity = max(12, (desired_hands + 1) * 5 - len(animals))
        room = max(0, field_capacity - len(plants) + harvest_count)
        need = max(0, min(12, slots, room) - standing_seeds)

        projected = Counter(counts)
        projected.update(seeds)
        purchases = Counter()
        for _ in range(need):
            crop = max(CROPS, key=lambda c: (crop_score(c, projected), c))
            if crop_score(crop, projected) <= 0:
                break
            cost = CROPS[crop][0]
            if virtual_cash < cost + 600:
                break
            # Budget each seed now; append aggregated orders afterward.
            virtual_cash -= cost
            projected[crop] += 1
            purchases[crop] += 1

        for crop, qty in purchases.items():
            if len(orders) < max_orders:
                orders.append(["BUY_SEED", crop, qty])
            else:
                virtual_cash += qty * CROPS[crop][0]

    try:
        with open("/tmp/astra_econ15.txt", "a") as _lf:
            _lf.write(
                f"d{day} h{hour} cash={money:.0f} hands={len(positions)-1} "
                f"desired={desired_hands} orders={len(orders)} "
                f"an={len(animals)} shed_an={sum(int(shed[k]) for k in ANIMALS)} "
                f"car_an={sum(int(all_carried[k]) for k in ANIMALS)} "
                f"tgt={dict(targets)} owned={len(owned)} sites={len(available_sites)} "
                f"plants={len(plants)} seeds={int(sum(seeds.values()))} "
                f"crop_empty={len(crop_empty)} crop_weeds={len(crop_weeds)} "
                f"dens={len(plants)/max(1, 20*len(owned)):.2f} "
                f"land_req={(1000, 2000, 4000)[len(owned)-1] if len(owned) < 4 else 0} "
                f"qC={sum(QUOTAS[q]['COW'] for q in owned)} "
                f"qS={sum(QUOTAS[q]['SHEEP'] for q in owned)} "
                f"qG={sum(QUOTAS[q]['GOOSE'] for q in owned)} "
                f"buy_cand={buy_cand} buy_ok={buy_ok} land_ok={land_ok}\n"
            )
    except Exception:
        pass
    return {
        "farmer": actions[0],
        "hands": actions[1:],
        "market": orders[:max_orders],
    }
