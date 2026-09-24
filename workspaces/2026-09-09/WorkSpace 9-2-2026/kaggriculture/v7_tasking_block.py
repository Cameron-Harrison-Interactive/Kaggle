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
