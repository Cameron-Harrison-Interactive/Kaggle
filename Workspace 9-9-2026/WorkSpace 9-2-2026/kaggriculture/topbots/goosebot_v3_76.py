# goosebot_v3.py — full-herd animal economy modeled on Crop Dusta.
#
# Engine economics (all verified against the installed engine):
#   CARE is free and stacks: pending_care_bonus += 1 per fed+cared day,
#   consumed on production days -> goose 2 EGG/day, cow 3 MILK/2d, sheep 4 WOOL/3d.
#   Every animal: 1 free FERTILIZER/day. FEED costs 1 WHEAT/day (miss 2 days -> escape).
#   Market: inventory starts at I0=10000 (base price). Town shops drain 1 of each
#   of their products every 4 steps (x2 single-product shops); town center drains
#   1 of all-but-FERT daily. WHEAT/EGG glut curves are gentle (log); MILK/WOOL/STRB
#   v3.75: FERTILIZER -> SELL ALL daily (no drain but price only slides $0.2/unit;
#   $84-100/unit beats +$30-45 fertilizing wheat/carrot — v11 nets $21k/game selling it).
#   Ongoing crops (STRB) with fert+water: 2 units per interval = $120/day/tile.
#
# Build: wheat bootstrap -> 6 geese -> land + pastures -> 3 cows + 2 sheep
#        -> fertilized strawberry endgame. Compact diamond layout around shed.

SHED_TILES = ((4, 4), (5, 4), (4, 5), (5, 5))
COOP_SPOTS = ((3, 4), (3, 5), (6, 4), (6, 5), (4, 3), (5, 3), (3, 3), (6, 3))
PASTURE_SPOTS = ((4, 6), (5, 6), (3, 6), (6, 6), (4, 2), (5, 2), (2, 4), (2, 5),
                 (7, 4), (7, 5), (4, 7), (5, 7))
CROP_INFO = {  # crop: (first_yield_day, max_yield_day, max_yield, ongoing)
    "WHEAT": (2, 4, 6, False),
    "CARROT": (2, 3, 4, False),
    "TOMATO": (8, 99, 4, True),
    "STRAWBERRY": (10, 99, 4, True),
    "MELON": (10, 12, 6, False),
}
TARGET_GEESE = 8
TARGET_COWS = 6
TARGET_SHEEP = 4


def _dist_to_shed(x, y):
    return abs(x - 4.5) + abs(y - 4.5)


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
    animals = []            # (x, y, tile)
    coops_empty = []
    pastures_empty = []
    coops_total = 0
    pastures_total = 0
    fert_window = []
    wheat_tiles = 0
    strb_tiles = 0
    carrot_tiles = 0
    melon_tiles = 0
    plants_all = []
    wheat_ripe = []
    dying_jobs = []
    planted_today = 0
    for y in range(n):
        row = tiles[y]
        for x in range(n):
            t = row[x]
            if t is None:
                empty_tiles.append((x, y))
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    plants_all.append((x, y))
                    crop = t.get("crop")
                    fyd, myd, maxy, ongoing = CROP_INFO.get(crop, (2, 4, 6, False))
                    age = day - t.get("planted_day", 0)
                    if t.get("planted_day") == day:
                        planted_today += 1
                    if not t.get("watered_today"):
                        water_jobs.append((x, y))
                        if t.get("consecutive_unwatered", 0) >= 1:
                            dying_jobs.append((x, y))
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
                    elif crop == "STRAWBERRY":
                        strb_tiles += 1
                    elif crop == "CARROT":
                        carrot_tiles += 1
                    elif crop == "MELON":
                        melon_tiles += 1
                elif k == "WEED":
                    weed_jobs.append((x, y))
                elif k == "COOP":
                    coops_total += 1
                    if t.get("animal"):
                        animals.append((x, y, t))
                        if t.get("yield_units", 0) >= 2:
                            harvest_jobs.append((x, y))
                    else:
                        coops_empty.append((x, y))
                elif k == "PASTURE":
                    pastures_total += 1
                    if t.get("animal"):
                        animals.append((x, y, t))
                        if t.get("yield_units", 0) >= 2:
                            harvest_jobs.append((x, y))
                    else:
                        pastures_empty.append((x, y))

    pending_structs = set()
    if coops_total < TARGET_GEESE:
        pending_structs.update(c for c in COOP_SPOTS if tiles[c[1]][c[0]] is None)
    if pastures_total < TARGET_COWS + TARGET_SHEEP:
        pending_structs.update(c for c in PASTURE_SPOTS if tiles[c[1]][c[0]] is None)
    plantable = [e for e in empty_tiles if e not in pending_structs]
    plantable.sort(key=lambda p: _dist_to_shed(p[0], p[1]))
    empty_tiles = plantable
    invs = list(priv.get("inventories") or [])
    n_animals = len(animals)
    n_geese = shed.get("GOOSE", 0) + sum(
        1 for a in animals if a[2].get("animal") == "GOOSE")
    n_cows = shed.get("COW", 0) + sum(
        1 for a in animals if a[2].get("animal") == "COW")
    n_sheep = shed.get("SHEEP", 0) + sum(
        1 for a in animals if a[2].get("animal") == "SHEEP")

    # ---------- market layer ----------
    market = []
    n_hands = len(farm.get("hands") or [])
    if day < 5:
        target_hands = 8
    elif money < 1500:
        target_hands = 8
    else:
        target_hands = 10
    # seeds first
    if seeds.get("WHEAT", 0) < 10 and money > 100:
        market.append(["BUY_SEED", "WHEAT", 32 - int(seeds.get("WHEAT", 0))])
    if day >= 2 and seeds.get("CARROT", 0) < 5 and money > 300:
        market.append(["BUY_SEED", "CARROT", 10 - int(seeds.get("CARROT", 0))])
    if day <= 1 and seeds.get("MELON", 0) < 8 and money > 2200:
        market.append(["BUY_SEED", "MELON", 8 - int(seeds.get("MELON", 0))])
    if 11 <= day <= 20 and seeds.get("STRAWBERRY", 0) < 5 and money > 1000:
        market.append(["BUY_SEED", "STRAWBERRY", 10 - int(seeds.get("STRAWBERRY", 0))])
    # land: NE early, SW when rich
    unlocked = len(farm.get("unlocked_quadrants") or ["NW"])
    if unlocked < 2 and day <= 20 and money > 1600:
        market.append(["BUY_LAND"])
    elif unlocked == 2 and day <= 20 and money > 3800:
        market.append(["BUY_LAND"])
    # animals
    wheat_secure = wheat_tiles >= n_animals + 1
    if (5 <= day <= 24 and n_geese < TARGET_GEESE and money > 420
            and coops_empty and hour <= 12 and shed.get("GOOSE", 0) == 0
            and (wheat_secure or n_geese < 5)):
        market.append(["BUY_ANIMAL", "GOOSE", 1])
    if (9 <= day <= 23 and n_cows < TARGET_COWS and money > 800
            and pastures_empty and hour <= 12 and shed.get("COW", 0) == 0
            and wheat_secure and n_geese >= 4):
        market.append(["BUY_ANIMAL", "COW", 1])
    if (12 <= day <= 23 and n_sheep < TARGET_SHEEP and money > 1100
            and pastures_empty and hour <= 12 and shed.get("SHEEP", 0) == 0
            and wheat_secure and n_cows >= 3):
        market.append(["BUY_ANIMAL", "SHEEP", 1])
    # emergency feed: buy wheat when the herd would otherwise starve
    if (day <= 27 and n_animals > 0 and money > 400
            and shed.get("WHEAT", 0) < n_animals
            and len(wheat_ripe) < max(1, n_animals - shed.get("WHEAT", 0))):
        market.append(["BUY_PRODUCT", "WHEAT", min(2 * n_animals,
                                                   money // 40)])

    # sells: price-aware. Town drains inventory every 4 steps, so holding
    # surplus builds scarcity premiums (esp. hinge items: EGG/CARROT/TOMATO).
    prices = (obs.get("market") or {}).get("prices") or {}
    wheat_keep = max(16, 4 * n_animals + 8)
    BASE = {"FERTILIZER": 100, "WHEAT": 25, "CARROT": 35, "EGG": 50, "MILK": 160, "WOOL": 200,
            "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250}
    if hour >= 4:
        fert_q = shed.get("FERTILIZER", 0)
        if fert_q > 0:
            market.append(["SELL", "FERTILIZER", fert_q])
        shed_load = sum(v for v in shed.values()
                        if isinstance(v, (int, float)))
        if shed_load > 88:
            # overflow protection: shed cap 100 destroys surplus overnight
            for item in sorted(("FERTILIZER", "EGG", "MILK", "WOOL", "CARROT", "WHEAT"),
                               key=lambda k: -shed.get(k, 0)):
                if shed_load <= 82:
                    break
                q = min(shed.get(item, 0),
                        max(0, shed_load - 82))
                if q > 0:
                    market.append(["SELL", item, q])
                    shed_load -= q
        for item, keep in (("WHEAT", wheat_keep), ("CARROT", 0), ("EGG", 0),
                           ("MILK", 0), ("WOOL", 0), ("TOMATO", 0),
                           ("STRAWBERRY", 0), ("MELON", 0)):
            have = shed.get(item, 0)
            if have <= keep:
                continue
            surplus = have - keep
            p = prices.get(item, BASE[item])
            base = BASE[item]
            if day >= 29:
                q = surplus                  # endgame dump
            elif p >= base * 1.04:
                q = surplus                  # premium: sell everything
            elif p >= base * 0.94 or hour >= 22:
                q = min(surplus, 10)         # normal: trickle
            else:
                q = 0                        # hold for better price
            if q > 0:
                market.append(["SELL", item, q])
    if ((hour <= 3 or n_hands == 0) and n_hands < target_hands
            and money > 80):
        for _ in range(min(4, target_hands - n_hands)):
            market.append(["HIRE"])

    # ---------- unit tasking ----------
    positions = []
    fp = farm.get("farmer")
    positions.append((int(fp[0]), int(fp[1])) if fp and len(fp) >= 2 else None)
    for hp in (farm.get("hands") or []):
        positions.append((int(hp[0]), int(hp[1])) if hp and len(hp) >= 2 else None)
    n_units = len(positions)
    open_rows = set()
    for y in range(n):
        for x in range(n):
            if not isinstance(tiles[y][x], str):
                open_rows.add(y)
                break

    def inv_of(i):
        inv = invs[i] if i < len(invs) and isinstance(invs[i], dict) else {}
        return inv

    claimed = set()

    def take_nearest(px, py, jobs):
        best, bd = None, 10 ** 9
        for j in jobs:
            d = abs(j[0] - px) + abs(j[1] - py)
            if d < bd:
                bd, best = d, j
        return best

    def stripe_jobs(i, jobs):
        if not jobs:
            return []
        per = max(1, (n + n_units - 1) // n_units)
        xlo, xhi = i * per, min(n, (i + 1) * per)
        own = [j for j in jobs
               if xlo <= j[0] < xhi and j[1] in open_rows and j not in claimed]
        if own:
            return own
        return [j for j in jobs if j not in claimed]

    acts = []
    animals_all = list(animals)
    # feeder count scales with herd: each feeder handles ~4 animals
    k_feeders = max(1, min((n_animals + 3) // 4, max(1, n_units - 1)))
    for i in range(n_units):
        p = positions[i]
        if p is None:
            acts.append(["PASS"])
            continue
        px, py = p
        inv = inv_of(i)
        my_carry = sum(int(v) for v in inv.values() if isinstance(v, (int, float)))
        act = None

        # ---------- feeder circuit ----------
        is_feeder = ((1 <= i <= k_feeders and n_animals > 0) or
                     (i == 0 and n_units == 1 and n_animals > 0))
        if is_feeder:
            my_idx = i if i > 0 else 1
            my_animals = [a for a in animals_all[(my_idx - 1) % k_feeders::k_feeders]] \
                if k_feeders > 1 else animals_all
            hungry = [a for a in my_animals if not a[2].get("fed_today")]
            eggy = [(a[0], a[1]) for a in my_animals
                    if a[2].get("yield_units", 0) >= 2]
            uncared = [a for a in my_animals if not a[2].get("cared_today")]
            fert_here = [(x, y) for (x, y, t) in my_animals
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
                avail = [w for w in wheat_ripe if w not in claimed]
                if avail:
                    t = take_nearest(px, py, avail)
                    claimed.add(t)
                    act = (["HARVEST"] if (px, py) == t
                           else _gb_move(px, py, t[0], t[1]))
            elif eggy:
                t = take_nearest(px, py, eggy)
                act = (["HARVEST"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif uncared:
                t = take_nearest(px, py, [(a[0], a[1]) for a in uncared])
                act = (["CARE"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif fert_here:
                t = take_nearest(px, py, fert_here)
                act = (["COLLECT_FERTILIZER"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif inv.get("FERTILIZER", 0) > 0:
                if (px, py) in SHED_TILES:
                    act = ["DROP", "FERTILIZER", 99]
                else:
                    ts = min(SHED_TILES,
                             key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                    act = _gb_move(px, py, ts[0], ts[1])

        # ---------- fert runners: last 2 units gather & bank free fert ----------
        drafted_to_water = (len(dying_jobs) >= 4 and i < n_units - 2)
        is_fert_runner = (n_units >= 11 and i >= n_units - 3
                          and n_animals >= 4 and not drafted_to_water)
        if is_fert_runner and act is None:
            if inv.get("FERTILIZER", 0) >= 4 or (inv.get("FERTILIZER", 0) > 0 and hour >= 20):
                ts = min(SHED_TILES,
                         key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                act = (["DROP", "FERTILIZER", 99] if (px, py) in SHED_TILES
                       else _gb_move(px, py, ts[0], ts[1]))
            else:
                fsrc = [(ax, ay) for (ax, ay, at) in animals_all
                        if at.get("fertilizer_available", 0)]
                if fsrc:
                    t = take_nearest(px, py, fsrc)
                    act = (["COLLECT_FERTILIZER"] if (px, py) == t
                           else _gb_move(px, py, t[0], t[1]))
                elif inv.get("FERTILIZER", 0) > 0:
                    ts = min(SHED_TILES,
                             key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                    act = (["DROP", "FERTILIZER", 99] if (px, py) in SHED_TILES
                           else _gb_move(px, py, ts[0], ts[1]))

        # ---------- farm loop ----------
        if act is None:
            carry_animal = next((k for k in ("GOOSE", "COW", "SHEEP")
                                 if inv.get(k, 0) > 0), None)
            if carry_animal == "GOOSE" and coops_empty:
                t = take_nearest(px, py, coops_empty)
                act = (["PLACE", "GOOSE"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif carry_animal == "COW" and pastures_empty:
                t = take_nearest(px, py, pastures_empty)
                act = (["PLACE", "COW"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif carry_animal == "SHEEP" and pastures_empty:
                t = take_nearest(px, py, pastures_empty)
                act = (["PLACE", "SHEEP"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif shed.get("GOOSE", 0) > 0 and coops_empty and my_carry == 0:
                if (px, py) in SHED_TILES:
                    act = ["PICKUP", "GOOSE", 1]
                else:
                    ts = min(SHED_TILES,
                             key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                    act = _gb_move(px, py, ts[0], ts[1])
            elif (shed.get("COW", 0) > 0 and pastures_empty and my_carry == 0):
                if (px, py) in SHED_TILES:
                    act = ["PICKUP", "COW", 1]
                else:
                    ts = min(SHED_TILES,
                             key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                    act = _gb_move(px, py, ts[0], ts[1])
            elif (shed.get("SHEEP", 0) > 0 and pastures_empty and my_carry == 0):
                if (px, py) in SHED_TILES:
                    act = ["PICKUP", "SHEEP", 1]
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
            elif harvest_jobs or water_jobs:
                # fall through: unclaimed harvest first, then water
                cand = stripe_jobs(i, harvest_jobs) if harvest_jobs else []
                if cand:
                    t = take_nearest(px, py, cand)
                    claimed.add(t)
                    act = (["HARVEST"] if (px, py) == t
                           else _gb_move(px, py, t[0], t[1]))
                else:
                    cand = stripe_jobs(i, water_jobs) if water_jobs else []
                    if cand:
                        t = take_nearest(px, py, cand)
                        claimed.add(t)
                        act = (["WATER"] if (px, py) == t
                               else _gb_move(px, py, t[0], t[1]))

        if act is None:
            coop_spots = [c for c in COOP_SPOTS
                          if tiles[c[1]][c[0]] is None and c not in claimed]
            pasture_spots = [c for c in PASTURE_SPOTS
                             if tiles[c[1]][c[0]] is None and c not in claimed]
            weed_cand = stripe_jobs(i, weed_jobs) if weed_jobs else []
            if weed_cand:
                t = take_nearest(px, py, weed_cand)
                claimed.add(t)
                act = (["DIG"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif (day >= 3 and coops_total < TARGET_GEESE and my_carry == 0
                    and coop_spots):
                t = take_nearest(px, py, coop_spots)
                claimed.add(t)
                act = (["BUILD_COOP"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif (day >= 9 and pastures_total < TARGET_COWS + TARGET_SHEEP
                    and my_carry == 0 and pasture_spots):
                t = take_nearest(px, py, pasture_spots)
                claimed.add(t)
                act = (["BUILD_PASTURE"] if (px, py) == t
                       else _gb_move(px, py, t[0], t[1]))
            elif inv.get("FERTILIZER", 0) > 0:
                if (px, py) in SHED_TILES:
                    act = ["DROP", "FERTILIZER", 99]
                else:
                    ts = min(SHED_TILES,
                             key=lambda s: abs(s[0] - px) + abs(s[1] - py))
                    act = _gb_move(px, py, ts[0], ts[1])
            elif empty_tiles and (seeds.get("WHEAT", 0) > 0
                                  or seeds.get("CARROT", 0) > 0
                                  or seeds.get("MELON", 0) > 0
                                  or seeds.get("STRAWBERRY", 0) > 0):
                wheat_floor = max(6, n_animals + 6)
                p_max = max(12, (5 * (1 + target_hands) - 2 * n_animals) // 2)
                wheat_short = wheat_tiles < wheat_floor
                day_cap = 16 if wheat_short else 13
                if (len(plants_all) < p_max and planted_today < day_cap
                        and _dist_to_shed(*empty_tiles[0]) <= 6.5):
                    cand = stripe_jobs(i, empty_tiles)
                    if cand:
                        t = take_nearest(px, py, cand)
                        claimed.add(t)
                        if (seeds.get("MELON", 0) > 0 and 1 <= day <= 3
                                and melon_tiles < 8):
                            crop = "MELON"
                        elif (seeds.get("STRAWBERRY", 0) > 0 and 13 <= day <= 19
                                and wheat_tiles >= wheat_floor
                                and strb_tiles < 4 and n_animals >= 9
                                and money > 1100):
                            crop = "STRAWBERRY"
                        elif (seeds.get("CARROT", 0) > 0 and day <= 26
                              and wheat_tiles >= wheat_floor
                              and carrot_tiles < 12):
                            crop = "CARROT"
                        elif (seeds.get("WHEAT", 0) > 0 and day <= 27):
                            crop = "WHEAT"
                        elif (seeds.get("CARROT", 0) > 0 and day <= 26):
                            crop = "CARROT"
                        else:
                            crop = "WHEAT"
                        act = (["PLANT", crop] if (px, py) == t
                               else _gb_move(px, py, t[0], t[1]))
            if act is None:
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
