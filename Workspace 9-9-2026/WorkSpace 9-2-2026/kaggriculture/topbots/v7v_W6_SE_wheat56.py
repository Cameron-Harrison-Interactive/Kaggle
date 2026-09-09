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
COOP_SPOTS = ()
PASTURE_SPOTS = ((4, 6), (5, 6), (3, 6), (6, 6), (4, 2), (5, 2), (2, 4), (2, 5),
                 (7, 4), (7, 5), (4, 7), (5, 7),
                 (3, 4), (3, 5), (6, 4), (6, 5), (4, 3), (5, 3), (3, 3), (6, 3))
CROP_INFO = {  # crop: (first_yield_day, max_yield_day, max_yield, ongoing)
    "WHEAT": (2, 4, 6, False),
    "CARROT": (2, 3, 4, False),
    "TOMATO": (8, 99, 4, True),
    "STRAWBERRY": (10, 99, 4, True),
    "MELON": (10, 12, 6, False),
}
TARGET_GEESE = 0
TARGET_COWS = 9
TARGET_SHEEP = 8


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
    strb_needs_fert = []
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
                        _age = day - t.get("planted_day", 0)
                        _cu = t.get("consecutive_unwatered", 0)
                        if ongoing and _age >= 19 and t.get("yield_units", 0) <= 1:
                            weed_jobs.append((x, y))
                        elif ongoing:
                            _pays = (_age + 1 >= fyd and (_age + 1 - fyd) % 2 == 0)
                            if _pays or _cu >= 1:
                                water_jobs.append((x, y))
                                if _cu >= 1:
                                    dying_jobs.append((x, y))
                        else:
                            water_jobs.append((x, y))
                            if _cu >= 1:
                                dying_jobs.append((x, y))
                    if ongoing:
                        _yu = t.get("yield_units", 0)
                        _aage = day - t.get("planted_day", 0)
                        if _yu >= 2 or (_yu >= 1 and _aage >= 17):
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
                        if t.get("fertilized_until_day", -1) < day:
                            strb_needs_fert.append((x, y))
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
    # race detection (H2H: opponent is an active bot, not a pass_agent) --
    # gates H2H-only economy behavior; inert in solo play.
    race = False
    try:
        _fs = obs.get("farms") or []
        if len(_fs) > 1:
            _opp = _fs[1 - int(obs.get("player") or 0)]
            if _opp is not None:
                if ((len(_opp.get("hands") or []) > 0)
                        or (_opp.get("money") or 0) > 4200):
                    race = True
                else:
                    _np = 0
                    for _row in (_opp.get("tiles") or []):
                        for _t in _row:
                            if isinstance(_t, dict) and (
                                    _t.get("kind") == "PLANT"
                                    or _t.get("animal")):
                                _np += 1
                                if _np >= 2:
                                    break
                        if _np >= 2:
                            break
                    race = _np >= 2
    except Exception:
        race = False

    market = []
    n_hands = len(farm.get("hands") or [])
    if day < 5 or money < 600:
        target_hands = 5
    elif day < 8 or money < 900:
        target_hands = 8
    elif day < 12 or money < 1500:
        target_hands = 10
    else:
        target_hands = 12
    if race:
        # H2H: hands are the service bottleneck (weeds, feed, muling)
        target_hands = 12 if (day >= 6 or money > 2500) else (8 if day >= 3 else 5)
    # seeds first
    if seeds.get("WHEAT", 0) < 24 and money > 100:
        market.append(["BUY_SEED", "WHEAT", 56 - int(seeds.get("WHEAT", 0))])
    if day >= 2 and seeds.get("CARROT", 0) < 5 and money > 300:
        market.append(["BUY_SEED", "CARROT", 10 - int(seeds.get("CARROT", 0))])
    if ((1 if race else 0) <= day <= 12 and money > (900 if race else 1000)
            and seeds.get("STRAWBERRY", 0) + strb_tiles < 33):
        market.append(["BUY_SEED", "STRAWBERRY",
                       min(8, 33 - strb_tiles - int(seeds.get("STRAWBERRY", 0)),
                           (money - 700) // 100)])
    if day <= 1 and seeds.get("MELON", 0) < 12 and money > 2200:
        market.append(["BUY_SEED", "MELON", 12 - int(seeds.get("MELON", 0))])
    # land: NE early, SW when rich
    unlocked = len(farm.get("unlocked_quadrants") or ["NW"])
    if unlocked < 2 and 4 <= day <= 20 and money > 1600:
        market.append(["BUY_LAND"])
    elif unlocked == 2 and day <= 14 and money > 2800:
        market.append(["BUY_LAND"])
    elif unlocked == 3 and day <= 22 and money > 4200:
        market.append(["BUY_LAND"])
    # animals
    wheat_secure = wheat_tiles >= n_animals + 1
    if (8 <= day <= 24 and n_geese < TARGET_GEESE and money > 420
            and coops_empty and hour <= 12 and shed.get("GOOSE", 0) == 0
            and (wheat_secure or n_geese < 5)):
        market.append(["BUY_ANIMAL", "GOOSE", 1])
    tgt_cows = 6 if race else TARGET_COWS
    cow_early = race and day <= 6 and n_cows < 4
    sheep_early = race and day <= 8 and n_sheep < 4
    feed_ok = (wheat_tiles >= n_animals + 2
               or shed.get("WHEAT", 0) >= 2 * n_animals + 2)
    if (1 <= day <= 20 and n_cows < tgt_cows
            and money > (750 if race else 900)
            and (pastures_total > n_cows or cow_early)
            and hour <= 12
            and shed.get("COW", 0) == 0
            and (not race or feed_ok)):
        market.append(["BUY_ANIMAL", "COW", 1])
    if (2 <= day <= 22 and n_sheep < TARGET_SHEEP
            and money > (850 if race else 800)
            and (pastures_empty or sheep_early) and hour <= 12
            and shed.get("SHEEP", 0) == 0
            and (sheep_early or (wheat_secure and n_cows >= 3))
            and (not race or feed_ok)):
        market.append(["BUY_ANIMAL", "SHEEP", 1])
    # emergency feed: buy wheat when the herd would otherwise starve
    _feed_px = ((obs.get("market") or {}).get("prices") or {}).get("WHEAT", 25) or 25
    if (race and day <= 27 and n_animals > 0 and money > 300
            and shed.get("WHEAT", 0) < n_animals + 1
            and len(wheat_ripe) < 3 and _feed_px < 80):
        market.append(["BUY_PRODUCT", "WHEAT",
                       min(2 * n_animals + 2 - shed.get("WHEAT", 0),
                           max(1, money // max(1, int(_feed_px) + 5)))])
    elif (day <= 27 and n_animals > 0 and money > 400
            and shed.get("WHEAT", 0) < n_animals
            and len(wheat_ripe) < max(1, n_animals - shed.get("WHEAT", 0))):
        market.append(["BUY_PRODUCT", "WHEAT", min(2 * n_animals,
                                                   money // 40)])
    elif (day <= 27 and n_animals > 0 and money > 800
            and shed.get("WHEAT", 0) < n_animals):
        market.append(["BUY_PRODUCT", "WHEAT",
                       min(2 * n_animals, (money - 500) // 40)])

    # sells: price-aware. Town drains inventory every 4 steps, so holding
    # surplus builds scarcity premiums (esp. hinge items: EGG/CARROT/TOMATO).
    prices = (obs.get("market") or {}).get("prices") or {}
    wheat_keep = max(16, n_animals + 12)
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
                           ("STRAWBERRY", 0), ("MELON", 0)) if not race else (
                tuple(sorted((("WHEAT", wheat_keep), ("CARROT", 0), ("EGG", 0),
                              ("MILK", 0), ("WOOL", 0), ("TOMATO", 0),
                              ("STRAWBERRY", 0), ("MELON", 0)),
                             key=lambda ik: -(prices.get(ik[0], 0) or 0)))):
            have = shed.get(item, 0)
            if have <= keep:
                continue
            surplus = have - keep
            p = prices.get(item, BASE[item])
            base = BASE[item]
            if day >= 29:
                q = surplus                  # endgame dump
            elif race:
                q = surplus                  # H2H race: liquidate; holding
                                             # loses to price decay + shed
                                             # cap-100 discards
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

    # ---------- v7 unified opportunistic tasking ----------
    # race detection: is the opponent an active bot? (pass_agent => no plants,
    # no animals, no hands, money stays at start) -- engine-legal read of the
    # shared farms list; gates H2H-only behavior so the solo benchmark stays
    # byte-identical.
    race = False
    try:
        _fs = obs.get("farms") or []
        if len(_fs) > 1:
            _opp = _fs[1 - int(obs.get("player") or 0)]
            if _opp is not None:
                if ((len(_opp.get("hands") or []) > 0)
                        or (_opp.get("money") or 0) > 4200):
                    race = True
                else:
                    _np = 0
                    for _row in (_opp.get("tiles") or []):
                        for _t in _row:
                            if isinstance(_t, dict) and (
                                    _t.get("kind") == "PLANT"
                                    or _t.get("animal")):
                                _np += 1
                                if _np >= 2:
                                    break
                        if _np >= 2:
                            break
                    race = _np >= 2
    except Exception:
        race = False

    positions = []
    fp = farm.get("farmer")
    positions.append((int(fp[0]), int(fp[1])) if fp and len(fp) >= 2 else None)
    for hp in (farm.get("hands") or []):
        positions.append((int(hp[0]), int(hp[1])) if hp and len(hp) >= 2 else None)
    n_units = len(positions)

    def inv_of(i):
        inv = invs[i] if i < len(invs) and isinstance(invs[i], dict) else {}
        return inv

    PROD = {"GOOSE": (4, 1), "COW": (8, 2), "SHEEP": (6, 3)}
    PS = set(PASTURE_SPOTS)
    shed_tot = sum(v for v in shed.values() if isinstance(v, (int, float)))
    wheat_floor = max(6, n_animals + 6)

    def plan_crop():
        if seeds.get("MELON", 0) > 0 and day <= 5 and melon_tiles < 12:
            return "MELON"
        if (seeds.get("STRAWBERRY", 0) > 0 and 2 <= day <= 12
                and strb_tiles < 33 and wheat_tiles >= 6):
            return "STRAWBERRY"
        if (seeds.get("CARROT", 0) > 0 and day <= 26
                and wheat_tiles >= wheat_floor and carrot_tiles < 12):
            return "CARROT"
        if seeds.get("WHEAT", 0) > 0 and day <= 27:
            return "WHEAT"
        return None

    # ---- global job list: (x, y, op, value, arg) ----
    jobs = []
    hungry_n = 0
    for y in range(n):
        row = tiles[y]
        for x in range(n):
            t = row[x]
            if not isinstance(t, dict):
                continue
            k = t.get("kind")
            if k == "PLANT":
                crop = t.get("crop")
                fyd, myd, maxy, ongoing = CROP_INFO.get(crop, (2, 4, 6, False))
                age = day - t.get("planted_day", 0)
                yu = t.get("yield_units", 0)
                if not t.get("watered_today"):
                    cu = t.get("consecutive_unwatered", 0)
                    if cu >= 1:
                        v = 250.0 if race else 150.0
                    elif ongoing:
                        v = 130.0 if (age + 1 >= fyd and (age + 1 - fyd) % 2 == 0) else (100.0 if race else 15.0)
                    elif ((myd + 1) // 2) <= age <= myd and yu < maxy:
                        v = 300.0 if crop == "MELON" else 55.0
                    else:
                        v = 100.0 if race else 15.0
                    jobs.append((x, y, "WATER", v, None))
                if ((not ongoing and (age >= myd or yu >= maxy))
                        or (ongoing and (yu >= 2 or (yu >= 1 and age >= 17)))):
                    pv = {"WHEAT": 1.0, "CARROT": 1.4, "MELON": 10.0,
                          "STRAWBERRY": 4.8}.get(crop, 1.6)
                    jobs.append((x, y, "HARVEST", 60.0 + 18.0 * pv, None))
                if (crop == "MELON" and 6 <= age <= 12
                        and t.get("fertilized_until_day", -1) < day):
                    jobs.append((x, y, "FERTILIZE", 220.0, None))
                if (crop == "STRAWBERRY"
                        and t.get("fertilized_until_day", -1) < day):
                    jobs.append((x, y, "FERTILIZE", 120.0, None))
            elif "animal" in t:
                fy, iv = PROD.get(t.get("animal"), (4, 1))
                aage = day - t.get("placed_day", 0)
                prod = aage + 1 >= fy and (aage + 1 - fy) % iv == 0
                if not t.get("fed_today"):
                    hungry_n += 1
                    v = 80.0 + (300.0 if t.get("consecutive_unfed", 0) >= 1 else 0.0) \
                        + (60.0 if prod else 0.0)
                    jobs.append((x, y, "FEED", v, None))
                if not t.get("cared_today") and (prod or t.get("pending_care_bonus", 0) == 0):
                    jobs.append((x, y, "CARE", 90.0, None))
                if t.get("fertilizer_available", 0):
                    jobs.append((x, y, "COLLECT_FERTILIZER", 60.0, None))
            elif k == "WEED":
                jobs.append((x, y, "DIG", 45.0, None))

    # planting jobs
    if empty_tiles and day <= 27:
        for (x, y) in empty_tiles:
            c = plan_crop()
            if c:
                v = {"MELON": 150.0, "STRAWBERRY": 80.0,
                     "WHEAT": 50.0, "CARROT": 35.0}[c]
                jobs.append((x, y, "PLANT", v, c))
    # pasture builds
    if day >= 1 and pastures_total < TARGET_COWS + TARGET_SHEEP:
        for c in PASTURE_SPOTS:
            if tiles[c[1]][c[0]] is None:
                jobs.append((c[0], c[1], "BUILD_PASTURE", 240.0, None))

    claimed = set()
    wheat_alloc = 0
    acts = []

    for i in range(n_units):
        p = positions[i]
        if p is None:
            acts.append(["PASS"])
            continue
        px, py = p
        inv = inv_of(i)
        my_carry = sum(int(v) for v in inv.values()
                       if isinstance(v, (int, float)))
        act = None
        t_here = tiles[py][px] if 0 <= px < n and 0 <= py < n else None

        # ---- 1) free action on my own tile ----
        if isinstance(t_here, dict):
            k = t_here.get("kind")
            if k == "PLANT":
                crop = t_here.get("crop")
                fyd, myd, maxy, ongoing = CROP_INFO.get(crop, (2, 4, 6, False))
                age = day - t_here.get("planted_day", 0)
                yu = t_here.get("yield_units", 0)
                if ((not ongoing and (age >= myd or yu >= maxy))
                        or (ongoing and (yu >= 2 or (yu >= 1 and age >= 17)))):
                    act = ["HARVEST"]
                elif not t_here.get("watered_today"):
                    act = ["WATER"]
                elif (inv.get("FERTILIZER", 0) > 0
                        and t_here.get("fertilized_until_day", -1) < day
                        and crop in ("MELON", "STRAWBERRY")):
                    act = ["FERTILIZE"]
            elif "animal" in t_here:
                if (not t_here.get("fed_today") and inv.get("WHEAT", 0) > 0):
                    act = ["FEED"]
                elif t_here.get("yield_units", 0) >= 2:
                    act = ["HARVEST"]
                elif not t_here.get("cared_today"):
                    act = ["CARE"]
                elif t_here.get("fertilizer_available", 0):
                    act = ["COLLECT_FERTILIZER"]
            elif k == "WEED":
                act = ["DIG"]
        elif t_here is None and (px, py) not in claimed:
            if (day >= 1 and (px, py) in PS
                    and pastures_total < TARGET_COWS + TARGET_SHEEP):
                act = ["BUILD_PASTURE"]
                claimed.add((px, py))
            elif day <= 27:
                c = plan_crop()
                if c:
                    act = ["PLANT", c]
                    claimed.add((px, py))

        # ---- shed tile logic ----
        if act is None and (px, py) in SHED_TILES:
            if (inv.get("WHEAT", 0) == 0 and shed.get("WHEAT", 0) > 0
                    and hungry_n > 0 and wheat_alloc < hungry_n):
                q = min(4, shed.get("WHEAT", 0), hungry_n - wheat_alloc)
                act = ["PICKUP", "WHEAT", q]
                wheat_alloc += q
            elif my_carry >= 6 and shed_tot < 92:
                item = next((kk for kk, vv in inv.items() if vv), "WHEAT")
                act = ["DROP", item, 99]
                shed_tot += my_carry
            else:
                for a_kind in ("COW", "SHEEP", "GOOSE"):
                    if shed.get(a_kind, 0) > 0 and (
                            a_kind == "GOOSE" and coops_empty
                            or a_kind != "GOOSE" and pastures_empty):
                        act = ["PICKUP", a_kind, 1]
                        break

        # ---- 2) claim & walk to the best global job ----
        if act is None:
            best, best_s = None, 0.0
            have_wheat = inv.get("WHEAT", 0) > 0
            have_fert = inv.get("FERTILIZER", 0) > 0
            for (jx, jy, op, v, arg) in jobs:
                key = (op, jx, jy)
                if key in claimed:
                    continue
                if op == "FEED" and not have_wheat:
                    continue
                if op == "FERTILIZE" and not have_fert:
                    continue
                d = abs(jx - px) + abs(jy - py)
                s = v / (1.0 + d)
                if op in ("FEED", "FERTILIZE", "PLACE"):
                    s *= 1.8
                if s > best_s:
                    best_s, best = s, (jx, jy, op, arg)
            # carrying an animal: place it
            carry_animal = next((kk for kk in ("GOOSE", "COW", "SHEEP")
                                 if inv.get(kk, 0) > 0), None)
            if carry_animal:
                spots = (coops_empty if carry_animal == "GOOSE" else pastures_empty)
                if spots:
                    t = min(spots, key=lambda s2: abs(s2[0] - px) + abs(s2[1] - py))
                    d = abs(t[0] - px) + abs(t[1] - py)
                    s = 350.0 / (1.0 + d)
                    if s > best_s:
                        best_s, best = s, (t[0], t[1], "PLACE", carry_animal)
            # no wheat but hungry herd and shed has wheat: go get some
            if (not have_wheat and hungry_n > 0
                    and shed.get("WHEAT", 0) > 0 and wheat_alloc < hungry_n):
                t = min(SHED_TILES,
                        key=lambda s2: abs(s2[0] - px) + abs(s2[1] - py))
                d = abs(t[0] - px) + abs(t[1] - py)
                s = 120.0 / (1.0 + d)
                if s > best_s:
                    best_s, best = s, (t[0], t[1], "PICKUP", "WHEAT")
            # heavy inventory: bank it
            if my_carry >= 6 and shed_tot < 92:
                t = min(SHED_TILES,
                        key=lambda s2: abs(s2[0] - px) + abs(s2[1] - py))
                d = abs(t[0] - px) + abs(t[1] - py)
                s = 90.0 / (1.0 + d)
                if s > best_s:
                    best_s, best = s, (t[0], t[1], "DROP", None)
            if best:
                jx, jy, op, arg = best
                if (px, py) == (jx, jy):
                    act = ([op] if arg is None else [op, arg])
                else:
                    claimed.add((op, jx, jy))
                    act = _gb_move(px, py, jx, jy)
        acts.append(act or ["PASS"])
    if race:
        # 10-order cap: animals/feed/hires must not be starved by sell spam
        _pri = {"BUY_ANIMAL": 0, "BUY_PRODUCT": 1, "HIRE": 2, "BUY_SEED": 3,
                "BUY_LAND": 4}
        market.sort(key=lambda o: _pri.get(
            o[0] if isinstance(o, list) and o else "", 5))
    return {"farmer": acts[0], "hands": acts[1:], "market": market[:10]}


def _gb_move(px, py, tx, ty):
    dx, dy = tx - px, ty - py
    if abs(dx) >= abs(dy) and dx != 0:
        return ["EAST"] if dx > 0 else ["WEST"]
    if dy != 0:
        return ["SOUTH"] if dy > 0 else ["NORTH"]
    return ["PASS"]
