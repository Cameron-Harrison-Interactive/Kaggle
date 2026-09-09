# goosebot_v1.py — from-scratch goose policy modeled on Crop Dusta's build.
# Engine laws baked in:
#   - planting day counts as unwatered day 1 -> water EVERY plant EVERY day
#   - weeds block build/plant -> DIG them
#   - hires cost fib(n) * 1 -> run 8-13 units daily
#   - market ops: HIRE / BUY_LAND / BUY_SEED / BUY_ANIMAL / SELL
#   - CARE is free, stacks +1 yield on fed production days
#   - every animal makes 1 free fertilizer/day -> collect + FERTILIZE crops
#   - non-ongoing crops: harvest at age >= max_yield_day (maturity)
#   - ongoing crops (TOMATO d8+, STRB d10+): plant once, water forever
#   - locked tiles are the string "LOCKED"; None == unlocked & empty

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


def _crop_at(tiles, p):
    t = tiles[p[1]][p[0]]
    return t.get("crop") if isinstance(t, dict) else None


def agent(obs, config=None):
    seat = obs.get("player", 0) or 0
    farms_list = obs.get("farms") or []
    farm = farms_list[seat] if seat < len(farms_list) else farms_list[0]
    priv = obs["private"]
    shed = priv.get("shed") or {}
    seeds = priv.get("seeds") or {}
    money = farm.get("money", 0)
    tiles = farm["tiles"]
    n = len(tiles)
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
    fert_window = []
    wheat_tiles = 0
    plants_all = []
    wheat_ripe = []
    planted_today = 0
    open_rows = set()
    for y in range(n):
        row = tiles[y]
        for x in range(n):
            t = row[x]
            if t is None:
                empty_tiles.append((x, y))
                open_rows.add(y)
            elif isinstance(t, dict):
                open_rows.add(y)
                k = t.get("kind")
                if k == "PLANT":
                    plants_all.append((x, y))
                    if t.get("planted_day") == day:
                        planted_today += 1
                    crop = t.get("crop")
                    fyd, myd, maxy, ongoing = CROP_INFO.get(crop, (2, 4, 6, False))
                    age = day - t.get("planted_day", 0)
                    if not t.get("watered_today"):
                        water_jobs.append((x, y))
                    if ongoing:
                        if t.get("yield_units", 0) >= 2:
                            harvest_jobs.append((x, y))
                        if age >= 1:
                            fert_window.append((x, y))
                    else:
                        if age >= myd or t.get("yield_units", 0) >= maxy:
                            harvest_jobs.append((x, y))
                            if crop == "WHEAT":
                                wheat_ripe.append((x, y))
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
    n_geese = shed.get("GOOSE", 0) + sum(
        1 for a in animals if a[2].get("animal") == "GOOSE")
    n_animals = len(animals)

    # ---------- market layer ----------
    market = []
    n_hands = len(farm.get("hands") or [])
    # revenue-ramped hiring: fib costs explode; match labor to income
    if day < 5:
        target_hands = 8          # capital-funded bootstrap
    elif money < 1000:
        target_hands = 7
    elif money < 2000:
        target_hands = 9
    elif money < 3500:
        target_hands = 11
    else:
        target_hands = 12
    # seeds first: highest ROI in the game
    if seeds.get("WHEAT", 0) < 6 and money > 60:
        market.append(["BUY_SEED", "WHEAT", 20 - int(seeds.get("WHEAT", 0))])
    if day >= 2 and seeds.get("CARROT", 0) < 6 and money > 150:
        market.append(["BUY_SEED", "CARROT", 16 - int(seeds.get("CARROT", 0))])
    if 8 <= day <= 22 and seeds.get("TOMATO", 0) < 6 and money > 400:
        market.append(["BUY_SEED", "TOMATO", 12 - int(seeds.get("TOMATO", 0))])
    if 11 <= day <= 19 and seeds.get("STRAWBERRY", 0) < 6 and money > 800:
        market.append(["BUY_SEED", "STRAWBERRY", 12 - int(seeds.get("STRAWBERRY", 0))])
    unlocked = len(farm.get("unlocked_quadrants") or ["NW"])
    if unlocked < 3 and day <= 22:
        price = (1000, 2000, 4000)[unlocked - 1]
        if money > price + 1500:
            market.append(["BUY_LAND"])
    if (5 <= day <= 26 and n_geese < TARGET_GEESE and money > 800
            and coops_empty and hour <= 12 and shed.get("GOOSE", 0) == 0):
        market.append(["BUY_ANIMAL", "GOOSE", 1])
    wheat_keep = max(12, 2 * n_geese)
    n_ongoing = sum(1 for p in plants_all
                    if CROP_INFO.get(_crop_at(tiles, p), ("", 0, 0, 0, True))[-1])
    fert_keep = 6 if n_ongoing >= 3 else 0
    if hour >= 22 or hour == 0:
        for item, keep in (("WHEAT", wheat_keep), ("CARROT", 0), ("EGG", 0),
                           ("TOMATO", 0), ("STRAWBERRY", 0), ("MELON", 0),
                           ("FERTILIZER", fert_keep), ("MILK", 0), ("WOOL", 0)):
            have = shed.get(item, 0)
            if have > keep:
                market.append(["SELL", item, have - keep])
    if hour <= 3 and n_hands < target_hands and money > 60:
        for _ in range(min(4, target_hands - n_hands)):
            market.append(["HIRE"])

    # ---------- unit tasking ----------
    positions = []
    fp = farm.get("farmer")
    positions.append((int(fp[0]), int(fp[1])) if fp and len(fp) >= 2 else None)
    for hp in (farm.get("hands") or []):
        positions.append((int(hp[0]), int(hp[1])) if hp and len(hp) >= 2 else None)
    n_units = len(positions)
    open_rows = set(open_rows)

    def inv_of(i):
        inv = invs[i] if i < len(invs) and isinstance(invs[i], dict) else {}
        return inv

    claimed = set()

    def zone_jobs(i, jobs):
        """Stable vertical stripe per unit; fall back to unclaimed."""
        if not jobs:
            return []
        per = max(1, (n + n_units - 1) // n_units)
        xlo, xhi = i * per, min(n, (i + 1) * per)
        own = [j for j in jobs
               if xlo <= j[0] < xhi and j[1] in open_rows and j not in claimed]
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
    animals_all = list(animals)
    for i in range(n_units):
        p = positions[i]
        if p is None:
            acts.append(["PASS"])
            continue
        px, py = p
        inv = inv_of(i)
        my_carry = sum(int(v) for v in inv.values() if isinstance(v, (int, float)))
        act = None
        uncared_stripe = [(a[0], a[1]) for a in animals
                          if not a[2].get("cared_today")]
        n_goose_now = sum(1 for a in animals if a[2].get("animal") == "GOOSE")
        k_feeders = min(1 + (1 if len(animals) >= 4 else 0)
                        + (1 if len(animals) >= 6 else 0), max(1, n_units - 1))
        is_feeder = ((1 <= i <= k_feeders and animals) or
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
            k = 1 + (1 if len(animals) >= 4 else 0) + (1 if len(animals) >= 6 else 0)
            k = min(k, max(1, n_units - 1))
            my_idx = i if i > 0 else 1
            my_coops = [a for a in animals_all[my_idx % k::k]]
            hungry = [a for a in my_coops if not a[2].get("fed_today")]
            uncared = [a for a in my_coops if not a[2].get("cared_today")]
            eggy = [(a[0], a[1]) for a in my_coops
                    if a[2].get("yield_units", 0) >= 2]
            fert_here = [(x, y) for (x, y, t) in my_coops
                         if t.get("fertilizer_available", 0)]
            if hungry and inv.get("WHEAT", 0) > 0:
                t = take_nearest(px, py, [(a[0], a[1]) for a in hungry])
                act = (["FEED"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif hungry and shed.get("WHEAT", 0) > 0:
                if (px, py) in SHED_TILES:
                    act = ["PICKUP", "WHEAT", min(len(hungry), shed["WHEAT"])]
                else:
                    ts = min(SHED_TILES,
                             key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                    act = _gb_move(px, py, ts[0], ts[1])
            elif hungry and wheat_ripe:
                t = take_nearest(px, py, wheat_ripe)
                act = (["HARVEST"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif uncared:
                t = take_nearest(px, py, [(a[0], a[1]) for a in uncared])
                act = (["CARE"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif inv.get("FERTILIZER", 0) > 0 and fert_window:
                t = take_nearest(px, py, fert_window)
                act = (["FERTILIZE"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif eggy:
                t = take_nearest(px, py, eggy)
                act = (["HARVEST"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif fert_here:
                t = take_nearest(px, py, fert_here)
                act = (["COLLECT_FERTILIZER"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))

        if act is None:
            if inv.get("GOOSE", 0) > 0 and coops_empty:
                cand = zone_jobs(i, coops_empty)
                if cand:
                    t = take_nearest(px, py, cand)
                    claimed.add(t)
                    act = (["PLACE", "GOOSE"] if (px, py) == t
                           else _gb_move(px, py, t[0], t[1]))
            elif shed.get("GOOSE", 0) > 0 and coops_empty:
                if (px, py) in SHED_TILES:
                    act = ["PICKUP", "GOOSE", 1]
                else:
                    ts = min(SHED_TILES,
                             key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                    act = _gb_move(px, py, ts[0], ts[1])
            elif my_carry >= 6:
                if (px, py) in SHED_TILES:
                    item = next((k for k, v in inv.items() if v), "WHEAT")
                    act = ["DROP", item, 99]
                else:
                    ts = min(SHED_TILES,
                             key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                    act = _gb_move(px, py, ts[0], ts[1])
            if act is None and harvest_jobs:
                if len(harvest_jobs) <= 2 * n_units or hour >= 18:
                    act = work(harvest_jobs, "HARVEST")
            if act is None and water_jobs:
                act = work(water_jobs, "WATER")
            if act is None and uncared_stripe:
                act = work(uncared_stripe, "CARE")

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
                                  or seeds.get("CARROT", 0) > 0
                                  or seeds.get("STRAWBERRY", 0) > 0
                                  or seeds.get("TOMATO", 0) > 0):
                # capacity target: keep total plant load within labor budget
                p_max = max(8, (5 * (1 + target_hands) - 4 * n_geese) // 2 + 2)
                if len(plants_all) < p_max and planted_today < 9:
                    cand = zone_jobs(i, empty_tiles)
                    if cand:
                        t = take_nearest(px, py, cand)
                        claimed.add(t)
                        wheat_floor = max(5, 6 + n_geese)
                        if (seeds.get("STRAWBERRY", 0) > 0 and 11 <= day <= 20
                                and wheat_tiles >= wheat_floor
                                and money > 1200):
                            crop = "STRAWBERRY"
                        elif (seeds.get("TOMATO", 0) > 0 and 8 <= day <= 23
                              and wheat_tiles >= wheat_floor
                              and money > 800):
                            crop = "TOMATO"
                        elif (seeds.get("CARROT", 0) > 0 and day <= 27
                              and wheat_tiles >= wheat_floor):
                            crop = "CARROT"
                        elif seeds.get("WHEAT", 0) > 0:
                            crop = "WHEAT"
                        else:
                            crop = "CARROT"
                        act = (["PLANT", crop] if (px, py) == t
                               else _gb_move(px, py, t[0], t[1]))
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
