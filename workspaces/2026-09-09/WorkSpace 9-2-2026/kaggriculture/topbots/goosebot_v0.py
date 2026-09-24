# goosebot_v0.py — from-scratch goose policy modeled on Crop Dusta's build.
# Wheat/carrot volume backbone + 6 free coops + 6 geese + feeder-hand loop.
# Engine laws baked in:
#   - planting day counts as unwatered day 1 -> water EVERY plant EVERY day
#   - weeds block build/plant -> DIG them
#   - hires cost fib(n) * 1 (trivial) -> run 6-12 hands daily
#   - market ops: HIRE / BUY_LAND / BUY_SEED / BUY_ANIMAL / SELL
#   - CARE is free and stacks pending_care_bonus (+1 yield per fed production day)
#   - every animal makes 1 free fertilizer/day -> collect + FERTILIZE crops
#   - non-ongoing crops: harvest at age >= max_yield_day (maturity)

SHED_TILES = ((4, 4), (5, 4), (4, 5), (5, 5))
COOP_RING = ((3, 4), (3, 5), (6, 4), (6, 5), (4, 3), (5, 3),
             (6, 3), (3, 3), (6, 6), (3, 6))
CROP_INFO = {  # crop: (first_yield_day, max_yield_day, max_yield, ongoing)
    "WHEAT": (2, 4, 6, False),
    "CARROT": (2, 3, 4, False),
    "TOMATO": (8, 99, 4, True),
    "STRAWBERRY": (10, 99, 4, True),
    "MELON": (10, 12, 6, False),
}
TARGET_GEESE = 6
TARGET_COOPS = 6


def agent(obs, config=None):
    farm = obs["farms"][0]
    priv = obs["private"]
    shed = priv.get("shed") or {}
    seeds = priv.get("seeds") or {}
    money = farm.get("money", 0)
    tiles = farm["tiles"]
    n = len(tiles)
    half = n // 2
    unlocked = len(farm.get("unlocked_quadrants") or [1])
    day = obs.get("day", 0)
    hour = obs.get("hour", 0) if obs.get("hour") is not None else (obs.get("step", 0) % 24)

    # ---------- scan board ----------
    harvest_jobs = []
    water_jobs = []
    weed_jobs = []
    empty_tiles = []
    animals = []          # (x, y, tile)
    coops_empty = []
    coops_total = 0
    fert_window = []      # crop tiles worth fertilizing (in window now/soon)
    wheat_tiles = 0
    for y in range(n):
        row = tiles[y]
        for x in range(n):
            t = row[x]
            if t is None:
                if unlocked > 1 or (x < half and y < half):
                    empty_tiles.append((x, y))
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    fyd, myd, maxy, ongoing = CROP_INFO.get(crop, (2, 4, 6, False))
                    age = day - t.get("planted_day", 0)
                    if not t.get("watered_today"):
                        water_jobs.append((x, y))
                    if ongoing:
                        if t.get("yield_units", 0) >= 2:
                            harvest_jobs.append((x, y))
                        if 0 <= myd - age <= 4 or age >= myd - 2:
                            fert_window.append((x, y))
                    else:
                        if age >= myd or t.get("yield_units", 0) >= maxy:
                            harvest_jobs.append((x, y))
                        if (myd + 1) // 2 <= age <= myd:
                            fert_window.append((x, y))
                    if crop == "WHEAT":
                        wheat_tiles += 1
                elif k == "WEED":
                    weed_jobs.append((x, y))
                elif k in ("COOP", "PASTURE"):
                    if k == "COOP":
                        coops_total += 1
                    if t.get("animal"):
                        animals.append((x, y, t))
                        if t.get("yield_units", 0) >= 2:
                            harvest_jobs.append((x, y))
                    else:
                        coops_empty.append((x, y))

    invs = list(priv.get("inventories") or [])
    market = []

    # ---------- market layer ----------
    n_hands = len(farm.get("hands") or [])
    target_hands = 6 if day < 3 else (9 if day < 7 else 12)
    market = []
    seed_cap = 14 if money < 1500 else (30 if money < 4000 else 60)
    if seeds.get("WHEAT", 0) < seed_cap // 2 and money > 300:
        market.append(["BUY_SEED", "WHEAT", seed_cap - int(seeds.get("WHEAT", 0))])
    if day >= 2 and seeds.get("CARROT", 0) < seed_cap // 2 and money > 500:
        market.append(["BUY_SEED", "CARROT", seed_cap - int(seeds.get("CARROT", 0))])
    if unlocked < 3:
        price = (1000, 2000, 4000)[unlocked - 1]
        if money > price + 3000:
            market.append(["BUY_LAND"])
    n_geese = shed.get("GOOSE", 0) + sum(
        1 for a in animals if a[2].get("animal") == "GOOSE")
    if (day >= 5 and n_geese < TARGET_GEESE and money > 1400
            and coops_empty):
        market.append(["BUY_ANIMAL", "GOOSE", 1])
    n_geese_placed = sum(1 for a in animals if a[2].get("animal") == "GOOSE")
    wheat_keep = max(14, 5 * (n_geese_placed + shed.get("GOOSE", 0)))
    if hour >= 22 or hour == 0:
        for item, keep in (("WHEAT", wheat_keep), ("CARROT", 0), ("EGG", 0),
                           ("TOMATO", 0), ("STRAWBERRY", 0), ("MELON", 0),
                           ("FERTILIZER", 4), ("MILK", 0), ("WOOL", 0)):
            have = shed.get(item, 0)
            if have > keep:
                market.append(["SELL", item, have - keep])
    if hour <= 2 and n_hands < target_hands and money > 250:
        for _ in range(min(3, target_hands - n_hands)):
            market.append(["HIRE"])

    # ---------- unit tasking ----------
    positions = []
    fp = farm.get("farmer")
    positions.append((int(fp[0]), int(fp[1])) if fp and len(fp) >= 2 else None)
    for hp in (farm.get("hands") or []):
        positions.append((int(hp[0]), int(hp[1])) if hp and len(hp) >= 2 else None)
    n_units = len(positions)

    def inv_of(i):
        inv = invs[i] if i < len(invs) and isinstance(invs[i], dict) else {}
        return inv

    claimed = set()

    def zone_jobs(i, jobs):
        """Stable row band per unit; fall back to unclaimed leftovers."""
        if not jobs:
            return []
        band = set()
        rows_per = max(1, (n + n_units - 1) // n_units)
        lo, hi = i * rows_per, min(n, (i + 1) * rows_per)
        band = set(range(lo, hi))
        own = [j for j in jobs if j[1] in band and j not in claimed]
        if own:
            return own
        return [j for j in jobs if j not in claimed]

    def take_nearest(px, py, jobs):
        best, bd = None, 10 ** 9
        for j in jobs:
            d = abs(j[0] - px) + abs(j[1] - py)
            if d < bd:
                bd, best = d, j
        return best

    acts = []
    work_cap = 20 * max(1, n_units) - 4
    for i in range(n_units):
        p = positions[i]
        if p is None:
            acts.append(["PASS"])
            continue
        px, py = p
        inv = inv_of(i)
        my_carry = sum(int(v) for v in inv.values() if isinstance(v, (int, float)))
        act = None
        n_goose_now = sum(1 for a in animals if a[2].get("animal") == "GOOSE")
        is_feeder = ((i in (1, 2) and n_units > 2 and animals and
                      (i == 1 or n_goose_now >= 5)) or
                     (i == 0 and n_units == 1 and animals))

        def work(jobs, op, i=i, px=px, py=py):
            cand = zone_jobs(i, jobs)
            if not cand:
                return None
            t = take_nearest(px, py, cand)
            claimed.add(t)
            if (px, py) == t:
                return [op]
            return _gb_move(px, py, t[0], t[1])

        if is_feeder:
            hungry = [a for a in animals if not a[2].get("fed_today")]
            uncared = [a for a in animals if not a[2].get("cared_today")]
            eggy = [(a[0], a[1]) for a in animals
                    if a[2].get("yield_units", 0) >= 2]
            fert_here = [(x, y) for (x, y, t) in animals
                         if t.get("fertilizer_available", 0)]
            if hungry and inv.get("WHEAT", 0) > 0:
                act = work([(a[0], a[1]) for a in hungry], "FEED")
            elif eggy:
                act = work(eggy, "HARVEST")
            elif hungry and shed.get("WHEAT", 0) > 0:
                if (px, py) in SHED_TILES:
                    act = ["PICKUP", "WHEAT", min(len(hungry), shed["WHEAT"])]
                else:
                    ts = min(SHED_TILES,
                             key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                    act = _gb_move(px, py, ts[0], ts[1])
            elif fert_here:
                act = work(fert_here, "COLLECT_FERTILIZER")
            elif inv.get("FERTILIZER", 0) > 0 and fert_window:
                act = work(fert_window, "FERTILIZE")
            elif uncared:
                act = work([(a[0], a[1]) for a in uncared], "CARE")

        if act is None:
            if inv.get("GOOSE", 0) > 0 and coops_empty:
                cand = zone_jobs(i, coops_empty)
                if cand:
                    t = take_nearest(px, py, cand)
                    claimed.add(t)
                    act = (["PLACE", "GOOSE"] if (px, py) == t
                           else _gb_move(px, py, t[0], t[1]))
            elif my_carry >= 8:
                if (px, py) in SHED_TILES:
                    item = next((k for k, v in inv.items() if v), "WHEAT")
                    act = ["DROP", item, 99]
                else:
                    ts = min(SHED_TILES,
                             key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                    act = _gb_move(px, py, ts[0], ts[1])
            elif harvest_jobs:
                act = work(harvest_jobs, "HARVEST")
            elif water_jobs:
                act = work(water_jobs, "WATER")
            if act is None:
                if weed_jobs:
                    act = work(weed_jobs, "DIG")
                elif (day >= 3 and coops_total < TARGET_COOPS and my_carry == 0):
                    spots = [c for c in COOP_RING
                             if tiles[c[1]][c[0]] is None and c not in claimed]
                    if not spots:
                        cands = [e for e in empty_tiles if e not in claimed]
                        if cands:
                            cx, cy = SHED_TILES[0]
                            spots = [min(cands, key=lambda e: abs(e[0] - cx) + abs(e[1] - cy))]
                    if spots:
                        t = take_nearest(px, py, spots)
                        claimed.add(t)
                        act = (["BUILD_COOP"] if (px, py) == t
                               else _gb_move(px, py, t[0], t[1]))
                elif empty_tiles and (seeds.get("WHEAT", 0) > 0
                                      or seeds.get("CARROT", 0) > 0):
                    daily_cap = 4 * max(1, n_units)
                    if len(water_jobs) + len(harvest_jobs) < daily_cap:
                        cand = zone_jobs(i, empty_tiles)
                        if cand:
                            t = take_nearest(px, py, cand)
                            claimed.add(t)
                            wheat_floor = 6 + 2 * (n_geese_placed + shed.get("GOOSE", 0))
                            if (seeds.get("CARROT", 0) > 0
                                    and wheat_tiles >= wheat_floor):
                                crop = "CARROT"
                            elif seeds.get("WHEAT", 0) > 0:
                                crop = "WHEAT"
                            else:
                                crop = "CARROT"
                            act = (["PLANT", crop] if (px, py) == t
                                   else _gb_move(px, py, t[0], t[1]))
                elif shed.get("GOOSE", 0) > 0 and coops_empty and my_carry == 0:
                    if (px, py) in SHED_TILES:
                        act = ["PICKUP", "GOOSE", 1]
                    else:
                        ts = min(SHED_TILES,
                                 key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                        act = _gb_move(px, py, ts[0], ts[1])
                else:
                    act = ["PASS"]
        acts.append(act or ["PASS"])

    return {"farmer": acts[0], "hands": acts[1:], "market": market[:10]}


def _gb_move(px, py, tx, ty):
    dx, dy = tx - px, ty - py
    if abs(dx) >= abs(dy) and dx != 0:
        return ["EAST"] if dx > 0 else ["WEST"]
    if dy != 0:
        return ["SOUTH"] if dy > 0 else ["NORTH"]
    return ["PASS"]
