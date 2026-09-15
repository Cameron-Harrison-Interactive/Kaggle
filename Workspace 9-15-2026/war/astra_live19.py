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
        STATE[seat] = {"goals": {}, "plans": {}, "ptrs": {},
                    "plan_day": -1, "planned_seeds": -1, "plan_workers": 0, "crew": 1}
    state = STATE.setdefault(seat, {"goals": {}, "plans": {}, "ptrs": {},
                                     "plan_day": -1, "planned_seeds": -1,
                                     "plan_workers": 0, "crew": 1})
    old_goals = state["goals"]

    farm = obs["farms"][seat]
    opponent = obs["farms"][1 - seat]
    # War mode (TRACE-06 + mirror lesson): vs a strb-heavy opponent
    # (standing >= 35, e.g. Tetsu's ~35-40), escalate strb target 33 -> 45
    # (volume = denial ammunition: our extra units crash the shared strb
    # market they depend on; measured -79k -> -57k). Vs balanced opponents
    # (e.g. our own 33-standing line) stay at 33: in a mutual-dump market
    # the LOWER-volume clone takes less inframarginal price damage
    # (measured: fixed-45 loses 0-20 to the 33-build). Latch: once the
    # opponent crosses the threshold, war stays on for the season.
    opp_strb = sum(
        1 for row in opponent.get("tiles", [])
        for t in row
        if isinstance(t, dict) and t.get("kind") == "PLANT"
        and t.get("crop") == "STRAWBERRY")
    if opp_strb >= 35:
        state["war"] = True
    strb_target = 45 if state.get("war") else 33
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
    STRB_TARGET = strb_target
    # Coverage rollout (user directive 09-10: "there should never be an
    # empty spot 'dirt'" — verified one quad at a time). Phase A: NW only.
    # Filler coverage measured NEGATIVE in every form (round 5): wheat
    # ungated -4.3k net, wheat price-gated -7.3k, carrot -8k+ — late
    # markets are saturated by our own volume; dirt is worth $1-2/unit
    # vs 4-6 labor ops/tile. Strb/melon/animal economy deploys the labor
    # better. (Round-4 NW-only filler was also net -12k at T33.)
    COVERAGE_QUADS = ()

    # tile sets shared by the planner, the market pipeline and the log
    crop_empty = [p for p in empty if not animal_line(p)]
    crop_weeds = [p for p in weeds if not animal_line(p)]
    available_sites = [
        pos for pos, tile in tile_map.items()
        if pos not in SHED and animal_line(pos) and (
            tile is None
            or (isinstance(tile, dict) and (
                tile.get("kind") == "WEED"
                or (tile.get("kind") in ("COOP", "PASTURE")
                    and not tile.get("animal"))))
        )
    ]

    # ---------- Planned dispatch (user's main.py architecture port) ----------
    # The day is planned before the field is entered: every must-job is
    # routed into a per-worker timeline with an exact hour budget (Manhattan
    # distance is exact; movement is never blocked). Crew size comes from
    # the plan itself — hire until ZERO must-jobs drop. Workers then follow
    # their timelines; jobs already done are skipped, so live-board drift
    # self-corrects. Same-day service is STRUCTURAL: every PLANT carries its
    # WATER, survival water is scheduled first, and there is no priority
    # auction to lose to — nothing needs a deadline overlay.

    # engine crop table (line-verified): first_yield, max_yield_day,
    # interval, max_yield, ongoing
    ECROPS = {
        "WHEAT": (2, 4, 0, 6, False),
        "CARROT": (2, 3, 0, 4, False),
        "TOMATO": (8, 8, 1, 4, True),
        "STRAWBERRY": (10, 10, 2, 4, True),
        "MELON": (10, 12, 0, 6, False),
    }

    def serpentine(quad_name):
        ys = range(5) if quad_name[0] == "N" else range(5, 10)
        xs = range(5) if quad_name[1] == "W" else range(5, 10)
        order, flip = [], 0
        for y in ys:
            row = list(xs)
            if flip:
                row.reverse()
            flip ^= 1
            order += [(x, y) for x in row]
        return order

    def needs_water(tile):
        # survival: one miss from death; ongoing: production days only
        # (EOD +1 is automatic; water enables the fertilized +2); finite:
        # bonus window while still gaining yield.
        crop = tile["crop"]
        if int(tile.get("consecutive_unwatered", 0)) >= 1:
            return True
        first, max_day, interval, cap, ongoing = ECROPS[crop]
        age = day - int(tile.get("planted_day", day))
        if ongoing:
            tick = first - 1
            return age >= tick and (age - tick) % interval == 0
        ws = (max_day + 1) // 2
        return ws <= age <= max_day and int(tile.get("yield_units", 0)) < cap

    def plan_crop_choice(vseeds, filler=False):
        # strawberry blueprint quota first (live18 plant-time semantics),
        # then the argmax over live-scored crops. MELON standing cap: the
        # planner plants everything that fits (unlike the old auction,
        # which starved PLANT priority) and a melon flood (measured 18-27
        # standing vs live18's 2-3) eats the daily labor budget — each
        # melon tile needs daily water in its gain window plus harvest —
        # starving the harvests that ARE revenue (strb 4-10 units and
        # melon 8-20 units left unharvested at h23). Cap standing melon
        # like the strb target; live18's winning shape ran 2-3.
        if (not final_day and vseeds.get("STRAWBERRY", 0) > 0
                and counts["STRAWBERRY"] < STRB_TARGET):
            return "STRAWBERRY"
        live = [
            c for c in CROPS
            if vseeds.get(c, 0) > 0 and crop_score(c) > 0
            and not (c == "MELON" and counts["MELON"] >= 12)
        ]
        if filler:
            # Coverage fallback (user directive: no dirt). Fillers sit at
            # the bottom of the priority order — only chosen when no
            # scored crop fits. CARROT only while its fast-cash window is
            # open; WHEAT is the standing filler (4-day cycles).
            for c in ("CARROT", "WHEAT"):
                if vseeds.get(c, 0) > 0 and c not in live:
                    if c == "CARROT" and day > 8:
                        continue
                    if c == "WHEAT" and day > 26:
                        continue
                    live.append(c)
        if not live:
            # Sunk planting (endgame waste, measured: 10-12 carrot + 10
            # wheat seeds dead in pocket at the whistle while carrot
            # fetched $72 — a paid seed's cost is spent; any yield is
            # free). Window-viable = first yield lands before the end.
            # Not gated by quad: the seed is already owned.
            for c in ("CARROT", "WHEAT"):
                if (vseeds.get(c, 0) > 0 and day >= 24
                        and day + ECROPS[c][0] <= total_days - 2):
                    return c
            return None
        return max(live, key=lambda c: (crop_score(c), c))

    def build_plan(n_workers, budget, pinned=None):
        """Route the whole day exactly. Returns (timelines, dropped)."""
        pinned = None  # pinning measured net -6.5k solo: the hourly
        # rebuild's free re-optimization beats walk continuity; the
        # replay-visible churn IS the adaptive value.
        pin_ex = set()
        workers = []
        for i in range(n_workers):
            # A planned phantom (hire not yet landed) spawns at h1 at the
            # earliest — budget 24h for it and its tail job dies mid-walk
            # at h23 (measured: 10/11 workers exactly one job short).
            wbudget = budget if i < len(positions) else budget - 1
            start = positions[i] if i < len(positions) else SHED[i % 4]
            # Seed cargo from the LIVE inventory: hourly replans (seed
            # arrivals) reset pointers, and a rebuild that starts cargo at
            # zero orphans everything workers already carry — measured as
            # sells firing only at h0 (one EOD burst) instead of hourly.
            inv0 = inventories[i] if i < len(inventories) else {}
            carried = sum(
                q for k, q in inv0.items()
                if k in MARKET and k not in ("WHEAT", "FERTILIZER") and q > 0
            )
            workers.append({"pos": start, "busy": 0, "plan": [],
                            "cargo": carried, "wbudget": wbudget})
        dropped = 0

        def maybe_drop(w):
            # hourly dump cycle: return cargo to the shed in small chunks so
            # the market sells absorb into rising prices instead of one
            # end-of-day glut burst. (Threshold 2 measured CATASTROPHIC:
            # constant shed returns from the far fields ate the workday —
            # $40-65k. Keep 4; the EOD auto-drop rescues the remainder.)
            if w["cargo"] < 4:
                return
            st = shed_near(w["pos"])
            if w["busy"] + distance(w["pos"], st) + 1 <= budget:
                w["plan"].append(("DROP", st, None))
                w["busy"] += distance(w["pos"], st) + 1
                w["pos"] = st
                w["cargo"] = 0

        # ---- 0. INSTALLS FIRST (scheduling fix) ----
        # Measured defect: installs sat at pointer 4-6 behind sweep/water
        # jobs; workers reached the shed at h9-14 and 9 animals parked in
        # the shed for days. Workers START on shed tiles — the pickup is
        # free — so the whole DIG->BUILD->PLACE chain runs by mid-morning.
        # Feeding shifts a few hours later, which is safe: escapes need TWO
        # consecutive unfed days and fed_today counts whenever it happens.
        # Cost = walk-to-shed + 1 (PICKUP) + walk-to-target + 2 (BUILD +
        # PLACE — the engine needs both, L493-505). Real bodies get jobs
        # before planned phantoms; a job that fits nobody counts dropped.
        install_jobs = []
        if not final_day:
            sites = available_sites
            qherd = Counter((quadrant(pos_s), tile["animal"])
                            for pos_s, tile in animals)
            used = set()
            for kind in ("GOOSE", "COW", "SHEEP"):
                for _ in range(held_animals[kind]):
                    matching = []
                    for pos_s in sites:
                        if pos_s in used:
                            continue
                        q = quadrant(pos_s)
                        if qherd[q, kind] >= QUOTAS[q][kind]:
                            continue
                        t_s = tile_map[pos_s]
                        if (isinstance(t_s, dict)
                                and t_s.get("kind") in ("COOP", "PASTURE")
                                and t_s["kind"] != ANIMALS[kind][1]):
                            continue
                        existing = (isinstance(t_s, dict)
                                    and t_s.get("kind") == ANIMALS[kind][1])
                        matching.append((
                            0 if existing else 1,
                            distance(pos_s, shed_near(pos_s)), pos_s))
                    if not matching:
                        break
                    pos_s = min(matching)[2]
                    used.add(pos_s)
                    qherd[quadrant(pos_s), kind] += 1
                    install_jobs.append((pos_s, kind))
            order = (list(range(min(n_workers, len(positions))))
                     + list(range(len(positions), n_workers)))
            hw = 0
            for pos_s, kind in install_jobs:
                placed_install = False
                for _ in range(n_workers):
                    w = workers[order[hw % n_workers]]
                    hw += 1
                    st = shed_near(w["pos"])
                    cost = (distance(w["pos"], st) + 1
                            + distance(st, pos_s) + 2)
                    if w["busy"] + cost <= budget:
                        w["plan"].append(("PICKUP_ANIMAL", st, kind))
                        w["plan"].append(("INSTALL", pos_s, kind))
                        w["busy"] += cost
                        w["pos"] = pos_s
                        placed_install = True
                        break
                if not placed_install:
                    dropped += 1

        # ---- 1. batched animal sweep: contiguous slice per worker, one
        #      wheat pickup for the whole slice, feed/collect/harvest/care
        #      in one pass (animals sit in lines next to the shed) ----
        sorted_animals = sorted(animals, key=lambda a: (a[0][1], a[0][0]))
        n_a = len(sorted_animals)
        if n_a:
            per = max(1, (n_a + n_workers - 1) // n_workers)
            shed_wheat = shed["WHEAT"]
            for i, w in enumerate(workers):
                mine = sorted_animals[i * per:(i + 1) * per]
                if not mine:
                    continue
                to_feed = [a for a in mine
                           if not a[1].get("fed_today")] if not final_day else []
                if to_feed and shed_wheat > 0:
                    st = shed_near(w["pos"])
                    take = min(shed_wheat, len(to_feed))
                    if w["busy"] + distance(w["pos"], st) + 1 <= budget:
                        w["plan"].append(("PICKUP_WHEAT", st, take))
                        w["busy"] += distance(w["pos"], st) + 1
                        w["pos"] = st
                        shed_wheat -= take
                for pos_a, tile in mine:
                    d = distance(w["pos"], pos_a)
                    if (not tile.get("fed_today") and w["busy"] + d + 1 <= budget
                            and ("FEED", pos_a) not in pin_ex):
                        w["plan"].append(("FEED", pos_a, None))
                        w["busy"] += d + 1
                        w["pos"] = pos_a
                        d = 0
                    if (tile.get("fertilizer_available")
                            and w["busy"] + d + 1 <= budget
                            and ("COLLECT_FERTILIZER", pos_a) not in pin_ex):
                        w["plan"].append(("COLLECT_FERTILIZER", pos_a, None))
                        w["busy"] += d + 1
                        w["pos"] = pos_a
                        w["cargo"] += 1
                        d = 0
                        maybe_drop(w)
                    if (int(tile.get("yield_units", 0)) >= 1
                            and w["busy"] + d + 1 <= budget
                            and ("HARVEST", pos_a) not in pin_ex):
                        w["plan"].append(("HARVEST", pos_a, None))
                        w["busy"] += d + 1
                        w["pos"] = pos_a
                        w["cargo"] += 1
                        d = 0
                        maybe_drop(w)
                    if (not final_day and not tile.get("cared_today")
                            and w["busy"] + d + 1 <= budget
                            and ("CARE", pos_a) not in pin_ex):
                        w["plan"].append(("CARE", pos_a, None))
                        w["busy"] += d + 1
                        w["pos"] = pos_a

        # ---- 2. survival water (cuw >= 1 dies tonight unserved) ----
        survival, scheduled = [], []
        for pos_p, tile in plants:
            if tile.get("watered_today") or final_day:
                continue
            if needs_water(tile) and ("WATER", pos_p) not in pin_ex:
                (survival if int(tile.get("consecutive_unwatered", 0)) >= 1
                 else scheduled).append(("WATER", pos_p, None))
        for job in survival:
            best = None
            for w in workers:
                d = distance(w["pos"], job[1])
                if (w["busy"] + d + 1 <= w["wbudget"]
                        and (best is None or (d, w["busy"]) < best[:2])):
                    best = (d, w["busy"], w)
            if best is None:
                dropped += 1
                continue
            _, _, w = best
            d = distance(w["pos"], job[1])
            w["plan"].append(job)
            w["busy"] += d + 1
            w["pos"] = job[1]

        # ---- 4. fertilize scheduled targets (pickup + spray) ----
        for pos_f in sorted(fert_targets, key=lambda p: quadrant(p)):
            best = None
            for w in workers:
                st = shed_near(w["pos"])
                c = distance(w["pos"], st) + 1 + distance(st, pos_f) + 1
                if w["busy"] + c <= budget and (best is None or c < best[0]):
                    best = (c, w, st)
            if best is None:
                dropped += 1
                continue
            _, w, st = best
            w["plan"].append(("PICKUP_FERT", st, 1))
            w["plan"].append(("FERTILIZE", pos_f, None))
            w["busy"] += distance(w["pos"], st) + 1 + distance(st, pos_f) + 1
            w["pos"] = pos_f

        # ---- 5. crop pass: scheduled water + harvests in serpentine
        #      order, round-robin; harvest -> replant -> water same tile ----
        vseeds = {c: seeds[c] for c in CROPS}
        order_index = {}
        for q in sorted(owned):
            for idx, t in enumerate(serpentine(q)):
                order_index[t] = idx

        # Tier the crop pass so COVERAGE never crowds out revenue volume
        # (measured: same-priority wheat window-waters pushed late-serpentine
        # strb/melon harvests off the crew tail: -29 strb, -16 melon, -18
        # wool on seed 42). Tier 1 = survival + ongoing-tick + melon-window
        # waters. Tier 2 = ALL harvests. Tier 3 = filler (wheat/carrot)
        # non-survival waters — they absorb slack labor only; a missed
        # filler water costs yield (6 -> 4 units), never a harvest.
        def _filler_water(job):
            if job[0] != "WATER":
                return False
            t = tile_map.get(job[1])
            if not (t and t.get("kind") == "PLANT"):
                return False
            if int(t.get("consecutive_unwatered", 0)) >= 1:
                return False  # survival stays tier 1
            return t["crop"] in ("WHEAT", "CARROT")

        crit_jobs = [j for j in scheduled if not _filler_water(j)]
        filler_water_jobs = [j for j in scheduled if _filler_water(j)]
        harvest_jobs = [
            ("HARVEST", pos_p, None) for pos_p, tile in plants
            if harvestable(tile) and ("HARVEST", pos_p) not in pin_ex
        ] + ([("HARVEST", pos_p, None) for pos_p, tile in plants
              if final_day and int(tile.get("yield_units", 0)) > 0
              and not harvestable(tile)] if final_day else [])
        # Within tier 2, harvests run by crop VALUE first (melon 6x$250,
        # strb 2x$120+), then serpentine — a $1,200 melon dump never waits
        # behind a $150 wheat harvest.
        hv_rank = {"MELON": 0, "STRAWBERRY": 1, "TOMATO": 2, "CARROT": 3,
                   "WHEAT": 4}
        harvest_jobs.sort(key=lambda j: (
            hv_rank.get((tile_map.get(j[1]) or {}).get("crop", "?"), 9),
            order_index.get(j[1], 999)))
        for jobs in (crit_jobs, filler_water_jobs):
            jobs.sort(key=lambda j: order_index.get(j[1], 999))
        crop_jobs = crit_jobs + harvest_jobs + filler_water_jobs
        for job in crop_jobs:
            best = None
            for w in workers:
                d = distance(w["pos"], job[1])
                if (w["busy"] + d + 1 <= w["wbudget"]
                        and (best is None or (d, w["busy"]) < best[:2])):
                    best = (d, w["busy"], w)
            if best is None:
                dropped += 1
                continue
            _, _, w = best
            d = distance(w["pos"], job[1])
            w["plan"].append(job)
            w["busy"] += d + 1
            w["pos"] = job[1]
            if job[0] == "HARVEST":
                w["cargo"] += 1
                maybe_drop(w)
                t_h = tile_map.get(job[1])
                if (t_h and t_h.get("kind") == "PLANT"
                        and t_h["crop"] not in ("TOMATO", "STRAWBERRY")
                        and not final_day):
                    crop = plan_crop_choice(
                        vseeds, filler=quadrant(job[1]) in COVERAGE_QUADS)
                    if crop is not None and w["busy"] + 2 <= budget:
                        w["plan"].append(("PLANT", job[1], crop))
                        w["plan"].append(("WATER", job[1], None))
                        w["busy"] += 2
                        vseeds[crop] -= 1

        # ---- 6. coverage pass: fill empty AND weed tiles, one quad at a
        #      time (NW -> NE -> SW -> SE), nearest-shed within a quad.
        #      Weed tiles run DIG -> PLANT -> WATER in one chain so a dead
        #      plant's tile is replanted the SAME day, never left dirt. ----
        weed_set = set(crop_weeds)
        quad_rank = {"NW": 0, "NE": 1, "SW": 2, "SE": 3}
        fill_tiles = [(p, "WEED" if p in weed_set else "EMPTY")
                      for p in crop_empty + crop_weeds]
        fill_tiles.sort(key=lambda tw: (
            quad_rank.get(quadrant(tw[0]), 9),
            distance(tw[0], shed_near(tw[0]))))
        for pos_e, tile_kind in fill_tiles:
            if (("PLANT", pos_e) in pin_ex
                    or ("DIG", pos_e) in pin_ex):
                continue
            crop = plan_crop_choice(
                vseeds, filler=quadrant(pos_e) in COVERAGE_QUADS)
            if crop is None:
                break
            cost = 3 if tile_kind == "WEED" else 2  # (dig+)plant+water
            best = None
            for w in workers:
                d = distance(w["pos"], pos_e)
                if w["busy"] + d + cost <= budget and (best is None or d < best[0]):
                    best = (d, w)
            if best is None:
                dropped += 1
                continue
            _, w = best
            if tile_kind == "WEED":
                w["plan"].append(("DIG", pos_e, None))
            w["plan"].append(("PLANT", pos_e, crop))
            w["plan"].append(("WATER", pos_e, None))
            w["busy"] += distance(w["pos"], pos_e) + cost
            w["pos"] = pos_e
            vseeds[crop] -= 1

        # ---- 7. dig weeds in slack ----
        for pos_w in sorted(crop_weeds, key=lambda p: distance(p, shed_near(p))):
            if ("DIG", pos_w) in pin_ex:
                continue
            best = None
            for w in workers:
                d = distance(w["pos"], pos_w)
                if w["busy"] + d + 1 <= budget and (best is None or d < best[0]):
                    best = (d, w)
            if best is None:
                continue
            _, w = best
            w["plan"].append(("DIG", pos_w, None))
            w["busy"] += d + 1
            w["pos"] = pos_w

        # ---- 8. end-of-plan cargo drops (shed feeds the hourly sells) ----
        for w in workers:
            if w["cargo"] > 0:
                st = shed_near(w["pos"])
                if w["busy"] + distance(w["pos"], st) + 1 <= budget:
                    w["plan"].append(("DROP", st, None))
                    w["busy"] += distance(w["pos"], st) + 1

        return {i: w["plan"] for i, w in enumerate(workers)}, dropped

    # ---- replan policy: first decision of the day, or new seeds/workers
    #      arrived mid-day (the plan is a pure function of the live board;
    #      rebuilding it from current positions self-corrects any drift) ----
    # Faithful to user_main: plan ONCE at day start; new bodies (hires
    # landing) get their pre-built timeline on arrival via one rebuild.
    # Seed arrivals do NOT rebuild — mid-day buys plant next morning (the
    # hourly-rebuild variant reset pointers constantly: tail DROPs and
    # INSTALLs never executed before the next reset; measured $47-66k vs
    # live18's $94k).
    _plans_cur = state.get("plans") or {}
    _ptrs_cur = state.get("ptrs") or {}
    _pending_install = any(
        j[0] in ("INSTALL", "PICKUP_ANIMAL")
        for _i, _pl in _plans_cur.items()
        for j in _pl[_ptrs_cur.get(_i, 0):])
    _held_now = sum(
        q for k, q in shed.items() if k in ANIMALS) + sum(
        q for inv in inventories for k, q in inv.items() if k in ANIMALS)
    _short = (len(positions) < int(state.get("plan_workers", 0)))
    # Orphan rebuild only when ACTIONABLE: held animals with no pending
    # install AND a site a rebuild could allocate (measured: an unhousable
    # sheep — 5 animals bought, 4 NW sites, goose/cow quotas consume them
    # — fired the trigger EVERY HOUR for days: ~50-150 full-plan pointer
    # resets/season = the "workers walking over work already done" in
    # replays). Dedup key: same day+hour+held+sites never rebuilds twice.
    _orphan_animals = (_held_now > 0 and not _pending_install)
    if (state.get("plan_day") != day
            or len(positions) > state.get("plan_workers", 0)
            or len(owned) > int(state.get("plan_quads", 0) or 0)
            or (hour == 4 and state.get("h4_done") != day and _short)
            or _orphan_animals):
        budget = turns - hour
        state["h4_done"] = day
        # Crew sizes to WORK (zero drops, cap 15) — cash caps the hire
        # loop, not the plan: mid-game h0 cash is thin (spend-to-floor)
        # and affordability-capped crews of 6-11 starved harvests while
        # units wasted at the per-tile cap (measured seed 202 d14-21:
        # $7k revenue vs live18's $41k).
        # Mid-day rebuild: pin each real worker's in-flight job chain
        # (current job + same-tile successors, e.g. DIG->PLANT->WATER)
        # so the rebuild re-plans the REMAINING work without abandoning
        # walks in progress — the replay-visible "walking over work
        # already done". Fresh day builds have nothing in flight.
        pinned = {}
        if state.get("plan_day") == day and hour > 0:
            _oldp = state.get("plans") or {}
            _oldt = state.get("ptrs") or {}
            _pin_ops = {"WATER", "HARVEST", "PLANT", "DIG", "FERTILIZE",
                        "INSTALL", "FEED", "CARE", "COLLECT_FERTILIZER"}
            for _i in range(min(len(positions), 16)):
                _pl_old = _oldp.get(_i)
                if not _pl_old:
                    continue
                _k = _oldt.get(_i, 0)
                if _k >= len(_pl_old):
                    continue
                _chain = []
                for _j in range(_k, min(_k + 3, len(_pl_old))):
                    _job = _pl_old[_j]
                    if _job[0] not in _pin_ops:
                        break
                    if _j > _k and _job[1] != _pl_old[_k][1]:
                        break
                    _chain.append(_job)
                if _chain:
                    pinned[_i] = _chain
        best_plans, best_n, best_dropped = None, len(positions), 10 ** 9
        for n in range(max(1, len(positions)), 15):
            p_try, dropped = build_plan(n, budget, pinned=pinned)
            if dropped < best_dropped:
                best_plans, best_n, best_dropped = p_try, n, dropped
            if dropped == 0:
                break
        plans = best_plans
        ptrs = {i: 0 for i in plans}
        state["plans"] = plans
        state["ptrs"] = ptrs
        state["plan_day"] = day
        state["plan_quads"] = len(owned)
        state["plan_workers"] = best_n
        state["crew"] = best_n
    else:
        plans = state.get("plans") or {}
        ptrs = dict(state.get("ptrs") or {})

    # ---- execute timelines (stale jobs skip; resources reserved
    #      within the turn exactly like the old dispatcher) ----
    free_shed = Counter(shed)
    free_seeds = Counter(seeds)
    actions = [["PASS"] for _ in positions]

    for i in range(len(positions)):
        pos, inv = positions[i], inventories[i]
        plan_i = plans.get(i) or []
        ptr = ptrs.get(i, 0)
        act = None

        while act is None and ptr < len(plan_i):
            op, tgt, arg = plan_i[ptr]
            tile = tile_map.get(tgt) if tgt else None

            if op == "PICKUP_WHEAT":
                if pos == tgt:
                    take = min(arg, free_shed["WHEAT"])
                    if take > 0:
                        free_shed["WHEAT"] -= take
                        act = ["PICKUP", "WHEAT", take]
                    ptr += 1
                    continue
                act = move(pos, tgt)
                break
            if op == "PICKUP_ANIMAL":
                if pos == tgt:
                    if free_shed[arg] > 0:
                        free_shed[arg] -= 1
                        act = ["PICKUP", arg, 1]
                    ptr += 1
                    continue
                act = move(pos, tgt)
                break
            if op == "PICKUP_FERT":
                if pos == tgt:
                    if free_shed["FERTILIZER"] > 0:
                        free_shed["FERTILIZER"] -= 1
                        act = ["PICKUP", "FERTILIZER", 1]
                    ptr += 1
                    continue
                act = move(pos, tgt)
                break
            if op == "DROP":
                if pos == tgt:
                    act = ["DROP"]
                    ptr += 1
                    break
                act = move(pos, tgt)
                break

            # tile jobs: staleness from the live board
            if op == "WATER":
                ok = (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                      and not tile.get("watered_today"))
            elif op == "FEED":
                ok = (isinstance(tile, dict) and tile.get("animal")
                      and not tile.get("fed_today")
                      and inv.get("WHEAT", 0) > 0)
            elif op == "CARE":
                ok = (isinstance(tile, dict) and tile.get("animal")
                      and not tile.get("cared_today"))
            elif op == "COLLECT_FERTILIZER":
                ok = (isinstance(tile, dict) and tile.get("animal")
                      and tile.get("fertilizer_available"))
            elif op == "HARVEST":
                ok = isinstance(tile, dict) and int(tile.get("yield_units", 0)) > 0
            elif op == "FERTILIZE":
                ok = (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                      and int(tile.get("fertilized_until_day", -1)) < day
                      and inv.get("FERTILIZER", 0) > 0)
            elif op == "DIG":
                ok = isinstance(tile, dict) and tile.get("kind") == "WEED"
            elif op == "PLANT":
                ok = ((tile is None or (isinstance(tile, dict)
                        and tile.get("kind") == "WEED"))
                      and free_seeds.get(arg, 0) > 0)
            elif op == "INSTALL":
                # tile None (and NOT a shed tile) => BUILD; WEED => DIG;
                # existing matching structure => PLACE.
                ok = (inv.get(arg, 0) > 0 and tgt not in SHED
                      and (tile is None
                           or (isinstance(tile, dict)
                               and (tile.get("kind") == "WEED"
                                    or tile.get("kind") == ANIMALS[arg][1]
                                    or tile.get("kind") in ("COOP", "PASTURE")))))
            else:
                ok = False

            if not ok:
                ptr += 1
                continue

            if pos != tgt:
                act = move(pos, tgt)
                break

            consumed = True
            if op == "PLANT":
                if isinstance(tile, dict) and tile.get("kind") == "WEED":
                    # weed chain: DIG first, PLANT lands next decision
                    # (same structural pattern as the INSTALL chain)
                    act = ["DIG"]
                    consumed = False
                else:
                    free_seeds[arg] -= 1
                    act = ["PLANT", arg]
            elif op == "INSTALL":
                # Engine truth (L493-505): BUILD_* only creates the EMPTY
                # structure — the animal is placed by a later PLACE. The
                # job stays current until the animal is actually on the
                # tile (DIG -> BUILD -> PLACE across decisions).
                if isinstance(tile, dict) and tile.get("kind") == "WEED":
                    act = ["DIG"]
                    consumed = False
                elif tile is None:
                    act = ["BUILD_" + ANIMALS[arg][1]]
                    consumed = False
                elif tile.get("kind") in ("COOP", "PASTURE"):
                    act = ["PLACE", arg]
                else:
                    act = None  # incompatible structure: stale
                    consumed = False
            else:
                act = [op]
            if act is not None:
                ptr += 1 if consumed else 0
                break
            ptr += 1 if not consumed else 0
            continue

        if act is None:
            # timeline exhausted: late-day cargo safety return
            cargo = sum(q for k, q in inv.items()
                        if k in MARKET and k not in ("WHEAT", "FERTILIZER"))
            if cargo > 0 and remaining <= distance(pos, shed_near(pos)) + 2:
                act = (["DROP"] if pos in SHED
                       else move(pos, shed_near(pos)))
            else:
                act = ["PASS"]

        actions[i] = act
        ptrs[i] = ptr

    state["ptrs"] = ptrs

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

    # Pending fert sprays: keep shed fertilizer for plan pickups still to
    # run today (hourly sales otherwise starve afternoon sprays — measured
    # 2-6 starved pickups/day d15+). Bounded: at most 6, fert only — a
    # stuck/reserved unit costs a falling $50-100 price, a starved spray
    # costs a doubled production tick.
    pending_plan_pickups = Counter()
    _plans_now = state.get("plans") or {}
    _ptrs_now = state.get("ptrs") or {}
    for _j, _pl in _plans_now.items():
        for _job in _pl[_ptrs_now.get(_j, 0):]:
            if _job[0] == "PICKUP_FERT":
                pending_plan_pickups["FERTILIZER"] += 1
    pending_plan_pickups["FERTILIZER"] = min(
        pending_plan_pickups["FERTILIZER"], 6)

    sellable = {}
    for item in MARKET:
        keep = reserve_wheat if item == "WHEAT" else (
            fert_keep if item == "FERTILIZER" and not final_day else 0
        )
        # Do not sell stock reserved for a PICKUP issued this turn, nor
        # stock owed to PENDING plan pickups later today (the old reserve
        # only covered same-turn pickups, so hourly fert sales starved
        # afternoon sprays — measured 2-6 starved pickups/day d15+).
        reserved_pickup = max(0, shed[item] - free_shed[item])
        qty = max(0, shed[item] - max(keep, reserved_pickup,
                                      pending_plan_pickups[item]))
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

    # ---------- Land: expansion gate (TRACE-03 fix + TRACE-05 blueprint path) ----------
    # (live19 note: ordered BEFORE hires — a 13-hand crew fills all 10
    #  market slots at h0-3 and starves BUY_LAND; land is one-shot and
    #  cannot wait for the day to fill.)
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
        # urgent must match the watering schedule: ongoing crops sit at
        # cuw=1 every other morning BY DESIGN (their water is planned for
        # today). Counting them blocked every BUY_LAND for days (live17's
        # measured lesson, now correct under planned watering).
        urgent = sum(
            not t.get("watered_today")
            and int(t.get("consecutive_unwatered", 0)) >= 1
            and t["crop"] not in ("TOMATO", "STRAWBERRY")
            for _, t in plants
        )
        quota_pressure = (
            1 <= day <= 16 and counts["STRAWBERRY"] < STRB_TARGET
        )
        # Land discipline (replays 107580250/107583283): the panic arm
        # (money >= cost + 8000) stacked NE + SW in one day "catching up"
        # and the fill cash was gone — NE sat until d15. Now: at most ONE
        # quad per day (land_day latch, in the outer condition), fields we
        # own must be real-full (density >= .80) or the strb blueprint
        # needs the escape hatch, and the 4th quad (SE — the animal quad)
        # only opens once the herd can populate it.
        herd_ready = (len(owned) < 3
                      or (day >= 16
                          and len(animals) + sum(held_animals.values()) >= 8))
        # Post-purchase solvency: after the land payment we must still
        # afford the opener seeds (same-turn pre-buy) AND a wage/seed
        # operating buffer. Replay 107580250 + local seed 202: SW bought
        # with $2161 -> $170 left -> crew stuck at 1 -> the new quad's 37
        # planned jobs sat unexecuted for days (solo -41k).
        _next_q = next((q for q in ("NE", "SW", "SE") if q not in owned), None)
        _fill_cost = 0
        if _next_q is not None:
            _qt = sum(1 for y in range(10) for x in range(10)
                      if quadrant((x, y)) == _next_q
                      and not animal_line((x, y)) and (x, y) not in SHED)
            _fill_cost = _qt * (20 if day <= 12 else 10)
        # Two-case solvency: an ESTABLISHED crew (>= 6 bodies, revenue
        # flowing) may buy land on the old bar (land + 150) — the
        # same-turn pre-buy then buys whatever opener seeds the remaining
        # cash covers (7-of-20 same-day beats 3 days of dirt: measured
        # seed 101, SW blocked $250 short for 3 days = -23k). A FRAGILE
        # crew (< 6) must pass FULL solvency (land + 150 + fill + 400) —
        # seed 202 bought SW with $2161 -> $170 left, crew stuck at 1,
        # new quad's 37 jobs sat dead (-41k).
        _bar = (land_cost + 150 if len(positions) >= 6
                else land_cost + 150 + _fill_cost + 400)
        if ((density >= .80 or quota_pressure)
                and money >= _bar
                and herd_ready
                and urgent <= max(2, len(positions))):
            land_ok = True
            if buy_order(["BUY_LAND"], land_cost, 150):
                state["land_day"] = day
                state["land_fill"] = _next_q

    # ---------- Quad-opening fill: same-turn seed pre-buy ----------
    # (replay 107581262: NE opened with 6 dirt, no planting for 2 days —
    # the pipeline had no seeds for the new tiles). Buy the opener crop
    # the SAME TURN as the land purchase, AFTER it (land keeps cash
    # priority). No idle stock, no leak window into other quads' dirt:
    # carrots while their economics hold, wheat for late quads.
    if (not final_day and state.get("land_day") == day
            and state.get("land_fill")):
        _qf = state["land_fill"]
        q_tiles = sum(
            1 for y in range(10) for x in range(10)
            if quadrant((x, y)) == _qf
            and not animal_line((x, y)) and (x, y) not in SHED)
        opener = "CARROT" if day <= 12 else "WHEAT"
        want = max(0, q_tiles - seeds[opener])
        if want > 0:
            unit = CROPS[opener][0]
            qty = min(want, int(max(0, virtual_cash - 150) // unit))
            if qty > 0 and buy_order(
                ["BUY_SEED", opener, qty], unit * qty, 150
            ):
                seeds[opener] += qty

    # ---------- Hire based on the PLAN (single source of truth) ----------
    # The morning planner already computed the smallest crew that routes
    # every must-job with zero drops; hire toward that number. Actual
    # positions are used each turn; hires are never assumed to exist
    # before they appear in the observation.

    harvest_count = sum(harvestable(t) for _, t in plants)
    desired_hands = max(3, min(14, int(state.get("crew", 1)) - 1))
    if day <= 1:
        desired_hands = max(desired_hands, 8)

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


    # ---------- Strawberry blueprint quota: spend-to-floor funding ----------
    # TRACE-05 cadence: Tetsu bought 33 strb seeds across d2-8 with money at
    # $27-2k (feed and herd keep priority; the argmax pipeline yields cash
    # to this quota). Replant-on-death keeps the factory at target through
    # d16; natural die-off ends it d20+ exactly like the captured run.
    if 1 <= day <= 16 and not final_day:
        strb_gap = STRB_TARGET - counts["STRAWBERRY"] - seeds["STRAWBERRY"]
        if strb_gap > 0:
            # Buy rate 4/day (measured: live18's effective rate — the
            # factory must reach 33 by ~d8 or production ramps a week
            # late; live19's 2/day reached it d15, costing the d14-21
            # strb volume). Still cash-gated with the 150 reserve.
            qty = min(4, strb_gap, int(max(0, virtual_cash - 150) // 100))
            if qty > 0 and buy_order(
                ["BUY_SEED", "STRAWBERRY", qty], 100 * qty, 150
            ):
                seeds["STRAWBERRY"] += qty

    # ---------- Coverage fillers: never an empty spot (dirt) ----------
    # Buy wheat (carrot while its window is open) to cover every empty +
    # weed tile in the coverage quads. Cash-gated, 150 reserve, <=10/day.
    if day >= 1 and not final_day:
        cov_slots = sum(
            1 for p in crop_empty + crop_weeds
            if quadrant(p) in COVERAGE_QUADS)
        filler_crop = "CARROT" if day <= 6 else "WHEAT"
        filler_seeds = sum(
            seeds[c] for c in ("WHEAT", "CARROT") if c == filler_crop)
        gap = min(10, cov_slots - filler_seeds)
        if gap > 0:
            unit = CROPS[filler_crop][0]
            qty = min(gap, int(max(0, virtual_cash - 150) // unit))
            if qty > 0 and buy_order(
                ["BUY_SEED", filler_crop, qty], unit * qty, 150
            ):
                seeds[filler_crop] += qty

    # ---------- Crop replacement / expansion seed pipeline ----------
    if day >= 2 and not final_day:
        # live12 log measured: d20+ the 12-stock is clogged with strb
        # seeds no live crop_score would ever sow (factory at target or
        # window closed) while standing collapses 46->17 with tiles empty.
        # Count only seeds the model would still plant toward the stock,
        # so the pipeline can keep buying LIVE seeds late. (live13's cap
        # change is NOT included — that was its measured failure mode.)
        standing_seeds = sum(
            seeds[c] for c in CROPS if crop_score(c) > 0
        )
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
        # Window gate: first yield must land before the season ends
        # (measured: 12 dead melon seeds bought after d18 = $960 sunk).
        cands = [c for c in CROPS if day + ECROPS[c][0] <= total_days - 2]
        for _ in range(need) if cands else []:
            crop = max(cands, key=lambda c: (crop_score(c, projected), c))
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
        with open("/tmp/astra_econ19.txt", "a") as _lf:
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
