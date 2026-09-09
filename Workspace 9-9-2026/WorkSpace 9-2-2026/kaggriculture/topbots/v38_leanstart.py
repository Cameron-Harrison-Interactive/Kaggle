# v28.19 "HARVEST MOON" (labor-tuned: drop12, dist0-bonus) — Harrison Interactive original build (2026-09-08).
# Elite-class agent: exact price-curve market brain + sector-zoned labor planner.
#
# Design (every root cause fixed at the architecture level):
#   MARKET: SELL fills instantly at P(I); selling past I0 crashes linear/sq items.
#     -> drain-cap rule: sell_qty <= deficit(I0 - I) for crashables; never push I above I0.
#     -> wheat carry (buy <=29, sell >=40), fert/egg/carrot early cash flow,
#     -> cash-floor liquidation, endgame dump days 28-29.
#   ORDERS: strict priority assembly, 10/turn cap; FEED first, HIRES last; re-hire at h1.
#   LABOR: farmer = logistics; hands = angular sectors around the shed (local mowing).
#     Sticky locks; water-danger and feed at prio 0; collect-fert/care/fertilize are money.
#   FEED: stock target = animals*3 wheat, bought at any price <= 36, funded by liquidation.
#     Care on fed days (+1 production unit = $160 milk).

import math

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP", "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}
MARKET_PARAMS = {
    "WHEAT":      {"base": 25, "I0": 10000, "T": 400, "below_func": "sqrt", "below_target": 0.80, "above_func": "log", "above_target": 0.20},
    "CARROT":     {"base": 35, "I0": 10000, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt", "above_target": 0.70},
    "TOMATO":     {"base": 60, "I0": 10000, "T": 200, "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt", "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": 10000, "T": 100, "below_func": "sqrt", "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": 10000, "T": 300, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.60},
    "EGG":        {"base": 50, "I0": 10000, "T": 332, "below_func": "hinge", "below_target": 0.40, "above_func": "log", "above_target": 0.20},
    "MILK":       {"base": 160, "I0": 10000, "T": 122, "below_func": "sqrt", "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": 10000, "T": 105, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": 10000, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}
SHOPS = {
    "BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"], "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"], "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
HINGE_GAIN = 8.0
I0 = 10000

def _shape(func, x, T=None):
    x = max(0.0, x)
    if func == "linear": return x
    if func == "sq": return x * x
    if func == "sqrt": return math.sqrt(x)
    if func == "log": return math.log(1.0 + x)
    if func == "hinge":
        if not T or T <= 0: return x
        u = x / T
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x

def price_of(item, inventory):
    p = MARKET_PARAMS[item]
    base, T = p["base"], p["T"]
    if inventory < I0:
        amp = p["below_target"] * base / _shape(p["below_func"], T, T)
        pr = base + amp * _shape(p["below_func"], I0 - inventory, T)
    else:
        amp = p["above_target"] * base / _shape(p["above_func"], T, T)
        pr = base - amp * _shape(p["above_func"], inventory - I0, T)
    return max(1, int(round(pr)))

SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
_SESSIONS = {}
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]

def _owned(farm):
    for y in range(10):
        for x in range(10):
            q = "NW"
            if x >= 5 and y < 5: q = "NE"
            elif x < 5 and y >= 5: q = "SW"
            elif x >= 5 and y >= 5: q = "SE"
            if q in farm["unlocked_quadrants"]:
                yield x, y, farm["tiles"][y][x]

def _d(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def _shed_near(pos):
    return min(SHED_TILES, key=lambda s: _d(pos, s))

def agent(obs, config=None):
    p = int(obs["player"])
    st = _SESSIONS.setdefault(p, {"sheep_ok": None, "locks": {}})
    farm = obs["farms"][p]
    priv = obs["private"]
    shed = priv.get("shed", {})
    seeds = priv.get("seeds", {})
    invs = priv.get("inventories", [{}])
    minv = obs["market"]["inventory"]
    town = obs["town"]["unlocked_shops"]
    step = int(obs.get("step", 0))
    day, hour = step // 24, step % 24
    money = farm["money"]
    units = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
    n_units = len(units)
    while len(invs) < n_units:
        invs.append({})
    carrying = [dict(iv) for iv in invs[:n_units]]

    shop_count = {}
    for s in town:
        shop_count[s] = shop_count.get(s, 0) + 1
    def drain_per_day(item):
        r = 0.0
        for s, c in shop_count.items():
            prods = SHOPS.get(s, [])
            if item in prods:
                r += c * (2 if len(prods) == 1 else 1) * 6
        return r + 1.0

    # ---------- state census ----------
    animals = {}
    structures_free = {"COOP": [], "PASTURE": []}
    for x, y, t in _owned(farm):
        if isinstance(t, dict):
            if "animal" in t:
                animals[t["animal"]] = animals.get(t["animal"], 0) + 1
            elif t.get("kind") in structures_free:
                structures_free[t["kind"]].append((x, y))

    sheep_ok = True  # wool sells at base $200+ solo; H2H floor-gated

    milk_px = price_of("MILK", minv["MILK"]) if "MILK" in minv else 160
    egg_px = price_of("EGG", minv["EGG"]) if "EGG" in minv else 50
    target_cows = 8 if milk_px >= 120 else (6 if milk_px >= 90 else (5 if milk_px >= 60 else 3))
    target_geese = 2 if egg_px >= 24 else 1
    wool_px = price_of("WOOL", minv["WOOL"]) if "WOOL" in minv else 200
    wool_flood = minv.get("WOOL", 10000) - 10000  # opponent dumping wool = surplus grows early
    target_sheep = 0 if wool_flood > 10 else (6 if wool_px >= 120 else (3 if wool_px >= 60 else 0))
    n_animals = sum(animals.values()) + sum(shed.get(a, 0) for a in ("COW", "GOOSE", "SHEEP"))
    feed_want = max(6, n_animals * 2)
    feed_stock = shed.get("WHEAT", 0) + sum(iv.get("WHEAT", 0) for iv in carrying)

    # ================= MARKET BRAIN =================
    P = {}
    o_feed, o_sell, o_animal, o_seed, o_land, o_carry, o_hire = [], [], [], [], [], [], []

    def sell(item, qty, bucket):
        q = min(int(qty), shed.get(item, 0))
        if q > 0:
            bucket.append(["SELL", item, q])
            return q
        return 0

    def drain_cap(item):
        return max(0, I0 - minv[item])

    endgame = day >= 26

    # ---- product sells (every turn) ----
    if endgame:
        for it in ("TOMATO", "MILK", "STRAWBERRY", "CARROT", "EGG", "FERTILIZER", "WHEAT", "WOOL"):
            q = shed.get(it, 0)
            if it == "WHEAT" and day <= 28:
                q = max(0, q - (n_animals if n_animals else 0))
            sell(it, q, o_sell)
    else:
        # volume mode: standing sells at small floors (solo prices sit far above;
        # H2H: shed never clogs, feed never blocked, cash always flowing)
        # v32.1: daily volume sells (cash feeds asset compounding — sheep beat
        # price appreciation), take-profit override retained for peak capture.
        FLOORS = {"MILK": 20, "TOMATO": 35, "STRAWBERRY": 50, "MELON": 80,
                  "CARROT": 15, "EGG": 20, "WOOL": 50}
        TAKE = {"MILK": 20, "TOMATO": 35, "STRAWBERRY": 50, "MELON": 80,
                "CARROT": 15, "EGG": 20, "WOOL": 50}
        for it, fl in FLOORS.items():
            if price_of(it, minv[it]) >= fl:
                sell(it, shed.get(it, 0), o_sell)
        if price_of("FERTILIZER", minv["FERTILIZER"]) >= 20:
            sell("FERTILIZER", max(0, shed.get("FERTILIZER", 0) - 2), o_sell)
        pw = price_of("WHEAT", minv["WHEAT"])
        sw = shed.get("WHEAT", 0)
        if pw >= 30 and sw > feed_want:
            sell("WHEAT", sw - feed_want, o_sell)

    # ---- shed-pressure clearance: an unclogged shed is worth more than price optimization ----
    shed_used = sum(shed.values())
    if shed_used > 62 and day < 26:
        for it in ("MILK", "TOMATO", "STRAWBERRY", "MELON", "CARROT", "EGG"):
            if shed.get(it, 0) > 0 and price_of(it, minv[it]) >= 8:
                sell(it, shed.get(it, 0), o_sell)

    # ---- cash floor: liquidate non-core for operating cash ----
    if money < 600 and day < 27:
        need = 800 - money
        got = 0
        for it in ("FERTILIZER", "EGG", "CARROT"):
            if got >= need: break
            q = shed.get(it, 0)
            keep = 4 if it == "FERTILIZER" else 0
            if q > keep:
                pr = price_of(it, minv[it])
                take = min(q - keep, max(1, (need - got) // max(1, pr)))
                o_sell.append(["SELL", it, take])
                got += take * pr

    # ---- wheat carry: the deficit runs all game (mirror: $28->$44); ride it ----
    pw = price_of("WHEAT", minv["WHEAT"])
    shed_room = 100 - sum(shed.values())
    if day <= 22 and pw <= 33 and money >= 2200 and shed_room >= 30:
        q = min(20, shed_room - 20, int((money - 1800) // max(1, pw)))
        if q > 0:
            o_carry.append(["BUY_PRODUCT", "WHEAT", q])
    elif day >= 12 and pw >= 42 and shed.get("WHEAT", 0) > feed_want:
        o_carry.append(["SELL", "WHEAT", min(shed.get("WHEAT", 0) - feed_want, 25)])

    # ---- milk desk: post-melon surplus rides the town drain ----
    pm = price_of("MILK", minv["MILK"])
    if 12 <= day <= 22 and pm <= 195 and money >= 5500 and shed_room >= 30:
        q = min(25, shed_room - 20, int((money - 5000) // max(1, pm)))
        if q > 0:
            o_carry.append(["BUY_PRODUCT", "MILK", q])

    # ---- standing feed buy (any hour, sacred; skipped if morning buy emitted) ----
    if o_feed and n_animals > 0 and feed_stock < n_animals * 2 and money >= 200 and pw <= 55 and False:
        qb = min(10, int((money - 150) // max(1, pw)))
        if qb > 0:
            o_feed.append(["BUY_PRODUCT", "WHEAT", qb])

    # ---- morning (hour 0/1): buys ----
    if hour <= 1:
        # FEED FIRST (sacred): fund by liquidation if needed
        if n_animals > 0 and feed_stock < feed_want:
            deficit = feed_want - feed_stock
            buy_n = min(deficit, int((money - 120) // max(1, pw))) if money > 120 else 0  # any price: feed is life
            if buy_n > 0:
                o_feed.append(["BUY_PRODUCT", "WHEAT", buy_n]); money -= buy_n * pw
            still = feed_want - feed_stock - max(0, buy_n)
            if still > 0:
                for li in ("FERTILIZER", "EGG", "CARROT"):
                    if still <= 0 or money > 120 + still * pw:
                        break
                    q = shed.get(li, 0)
                    keep = 4 if li == "FERTILIZER" else 0
                    if q > keep:
                        pr = price_of(li, minv[li])
                        sn = min(q - keep, still * 2)
                        if sn > 0:
                            o_sell.append(["SELL", li, sn]); money += sn * pr
                more = min(feed_want - feed_stock - max(0, buy_n), int((money - 80) // max(1, pw)))
                if more > 0:
                    o_feed.append(["BUY_PRODUCT", "WHEAT", more]); money -= more * pw
        # HERD: geese first (eggs d4+), cows to 8. All-in: floor = cost + 250.
        total_animals = sum(animals.values()) + sum(shed.get(a, 0) for a in ("COW", "GOOSE", "SHEEP")) + sum(iv.get(a, 0) for iv in carrying for a in ("COW", "GOOSE", "SHEEP"))
        if day <= 22 and total_animals < 18:
            plan = []
            if animals.get("GOOSE", 0) + shed.get("GOOSE", 0) < target_geese:
                plan.append(("GOOSE", min(2, target_geese - animals.get("GOOSE", 0) - shed.get("GOOSE", 0))))
            if animals.get("COW", 0) + shed.get("COW", 0) < target_cows:
                plan.append(("COW", min(3 if day >= 3 else 2, target_cows - animals.get("COW", 0) - shed.get("COW", 0))))
            if 3 <= day <= 16 and animals.get("SHEEP", 0) + shed.get("SHEEP", 0) < target_sheep:
                plan.append(("SHEEP", min(2, target_sheep - animals.get("SHEEP", 0) - shed.get("SHEEP", 0))))
            for aname, n in plan:
                cost = ANIMALS[aname]["cost"] * n
                if money - cost >= 250 + n_animals * 20 and (aname != "COW" or animals.get("COW", 0) + shed.get("COW", 0) >= 2 or day >= 3):
                    o_animal.append(["BUY_ANIMAL", aname, n]); money -= cost
        # LAND: tiles are the engine
        if len(farm["unlocked_quadrants"]) == 1 and day >= 1 and money >= 1300:
            o_land.append(["BUY_LAND"]); money -= 1000
        elif len(farm["unlocked_quadrants"]) == 2 and day >= 4 and money >= 2700:
            o_land.append(["BUY_LAND"]); money -= 2000
        # SEEDS: staggered tomato waves + strb + carrot
        def bs(crop, n):
            nonlocal money
            c = CROPS[crop]["seed"] * n
            if money - c >= 50:
                o_seed.append(["BUY_SEED", crop, n]); money -= c
        if hour == 0:
            W = {0: [("WHEAT", 8), ("MELON", 12)],
                 1: [("WHEAT", 6), ("CARROT", 4)],
                 2: [("WHEAT", 6), ("CARROT", 4)],
                 3: [("WHEAT", 4)], 4: [("WHEAT", 4), ("CARROT", 2)],
                 5: [("WHEAT", 4), ("CARROT", 2)],
                 6: [("WHEAT", 4), ("TOMATO", 4)],
                 7: [("WHEAT", 4), ("CARROT", 2)],
                 8: [("WHEAT", 4), ("TOMATO", 4)],
                 9: [("WHEAT", 4)],
                 10: [("WHEAT", 4), ("TOMATO", 4)],
                 11: [("WHEAT", 4)],
                 12: [("WHEAT", 4), ("TOMATO", 4)],
                 14: [("WHEAT", 4), ("TOMATO", 4)],
                 16: [("TOMATO", 4)], 18: [("TOMATO", 4)],
                 20: [("TOMATO", 4)], 22: [("TOMATO", 4)]}
            for d in (5, 7, 9):        # strb: small affordable waves during the crunch
                W.setdefault(d, []).append(("STRAWBERRY", 4))
            for d in (11, 13, 15, 17, 19, 21, 23):   # scale after melon money lands
                W.setdefault(d, []).append(("STRAWBERRY", 8 if d <= 15 else 6))
            for crop, n in W.get(day, []):
                if crop == "STRAWBERRY" and price_of("STRAWBERRY", minv["STRAWBERRY"]) < 110:
                    continue
                if crop == "MELON" and day >= 9 and price_of("MELON", minv["MELON"]) < 140:
                    continue
                bs(crop, n)
        # HIRES: scale with the field, fill leftover slots
        n_tiles = sum(1 for x, y, t in _owned(farm) if isinstance(t, dict) and (t.get("kind") == "PLANT" or "animal" in t))
        want = max(5, min(12, 5 + n_tiles // 4))
        if day < 8: want = 5                      # lean start: no idle crew while cash-starved
        elif day >= 12 and n_tiles >= 40 and farm["money"] >= 3000: want = 14
        if day >= 27: want = 6
        have = len(farm["hands"])
        for i in range(want - have):
            c = FIB[have + i] if have + i < len(FIB) else 999
            if money - c >= 20:
                o_hire.append(["HIRE"]); money -= c
            else:
                break

    # ---- assemble: at h0/h1 buys first (sells can fire any hour); else sells first ----
    o_sell.sort(key=lambda o: -(o[2] * price_of(o[1], minv[o[1]])))
    orders = []
    if hour <= 1:
        seq = (o_feed, o_animal, o_seed, o_land, o_hire)
        for bucket in seq:
            for o in bucket:
                if len(orders) < 10:
                    orders.append(o)
        for o in o_sell[:2]:          # at most 2 sell orders in the morning
            if len(orders) < 10:
                orders.append(o)
        for o in o_carry:
            if len(orders) < 10:
                orders.append(o)
    else:
        for bucket in (o_feed, o_sell, o_carry):
            for o in bucket:
                if len(orders) < 10:
                    orders.append(o)

    # ================= LABOR BRAIN =================
    logi, field = [], []   # farmer / hands
    tot_carry = [sum(iv.values()) for iv in carrying]

    def crop_count(crop):
        return sum(1 for x, y, t in _owned(farm) if isinstance(t, dict) and t.get("crop") == crop)

    empty_tiles = sorted([(x, y) for x, y, t in _owned(farm) if t is None], key=lambda c: _d(c, (4, 4)))
    weeds_tiles = [(x, y) for x, y, t in _owned(farm) if isinstance(t, dict) and t.get("kind") == "WEED"]

    # ---- animal pipeline: BUILD -> PICKUP -> PLACE (carried tracked) ----
    build_targets = set()
    for aname in ("COW", "GOOSE", "SHEEP"):
        an_shed = shed.get(aname, 0)
        an_carried = sum(iv.get(aname, 0) for iv in carrying)
        an = an_shed + an_carried
        if an <= 0: continue
        struct = ANIMALS[aname]["structure"]
        free = structures_free[struct]
        if len(free) < an:
            need = an - len(free)
            for c in empty_tiles:
                if c not in build_targets:
                    build_targets.add(c)
                    logi.append([0, c, "BUILD_" + struct, None, None])
                    need -= 1
                    if need <= 0: break
        for c in free[:an]:
            logi.append([0, c, "PLACE", aname, aname])
        if free and an_shed > 0 and an_carried == 0:
            logi.append([0, _shed_near(units[0]), "PICKUP", aname, None])

    # ---- per-tile tasks ----
    for x, y, t in _owned(farm):
        if not isinstance(t, dict): continue
        if t.get("kind") == "PLANT":
            cd = CROPS[t["crop"]]
            age = day - t["planted_day"]
            if not t.get("watered_today", False):
                danger = t.get("consecutive_unwatered", 0) >= 1
                field.append([0 if danger else 2, (x, y), "WATER", None, None])
            if not cd["ongoing"]:
                if t.get("yield_units", 0) >= cd["max_yield"] or (age >= cd["max_yield_day"] and t.get("yield_units", 0) > 0):
                    field.append([1, (x, y), "HARVEST", None, None])
            else:
                if t.get("crop") == "MELON":
                    if t.get("yield_units", 0) >= 2 or (t.get("planted_day", 0) + 14 <= day and t.get("yield_units", 0) > 0):
                        field.append([1, (x, y), "HARVEST", None, None])
                elif t.get("yield_units", 0) >= 4 or (t.get("yield_units", 0) >= 2 and day >= 26):
                    field.append([1, (x, y), "HARVEST", None, None])
            if t.get("fertilized_until_day", -1) < day and t.get("planted_day", 0) + 1 < day:
                field.append([1, (x, y), "FERTILIZE", None, "FERTILIZER"])
        elif "animal" in t:
            if not t.get("fed_today", False):
                ft = [0, (x, y), "FEED", None, "WHEAT"]
                logi.append(ft); field.append(ft)  # shared object: one taker
            if t.get("yield_units", 0) >= 3 or (t.get("yield_units", 0) >= 1 and day >= 27):
                field.append([1, (x, y), "HARVEST", None, None])
            if t.get("fertilizer_available", False):
                field.append([1, (x, y), "COLLECT_FERTILIZER", None, None])
            if not t.get("cared_today", False):
                field.append([1, (x, y), "CARE", None, None])

    # ---- DIG weeds ----
    for c in weeds_tiles[:10]:
        field.append([4, c, "DIG", None, None])

    # ---- PLANT: cycle-crop treadmill (tiles expire; count PRODUCTIVE only) ----
    EXPIRY = {"STRAWBERRY": 18, "TOMATO": 13, "WHEAT": 5, "CARROT": 4, "MELON": 14}
    def productive(crop):
        n = 0
        for x, y, t in _owned(farm):
            if isinstance(t, dict) and t.get("crop") == crop:
                if day - t.get("planted_day", 0) <= EXPIRY.get(crop, 99):
                    n += 1
        return n
    # DIG spent tiles to free land
    for x, y, t in _owned(farm):
        if isinstance(t, dict) and t.get("kind") == "PLANT":
            crop = t.get("crop")
            if (day - t.get("planted_day", 0) > EXPIRY.get(crop, 99)
                    and t.get("yield_units", 0) == 0):
                field.append([3, (x, y), "DIG", None, None])
    if day <= 25:
        want_crops = []
        m_target = 12 if day < 5 else 0
        if crop_count("MELON") < m_target and seeds.get("MELON", 0) > 0: want_crops.append("MELON")
        if seeds.get("CARROT", 0) > 0 and ((day <= 12 and productive("CARROT") < 6) or (day >= 21 and productive("CARROT") < 10)): want_crops.append("CARROT")
        w_target = 18 if day < 22 else 12
        if productive("WHEAT") < w_target and seeds.get("WHEAT", 0) > 0: want_crops.append("WHEAT")
        spx = price_of("STRAWBERRY", minv["STRAWBERRY"])
        strb_flood = minv.get("STRAWBERRY", 10000) - 10000
        s_target = 16 if (day >= 10 and spx >= 110 and strb_flood <= 20) else (6 if day >= 8 else 0)
        if productive("STRAWBERRY") < s_target and seeds.get("STRAWBERRY", 0) > 0: want_crops.append("STRAWBERRY")
        t_target = 10 if day >= 6 else 0
        if productive("TOMATO") < t_target and seeds.get("TOMATO", 0) > 0: want_crops.append("TOMATO")
        if want_crops:
            plantable = [c for c in empty_tiles if c not in build_targets]
            want_crops.sort(key=lambda c: {"STRAWBERRY": 0, "MELON": 1, "TOMATO": 2, "WHEAT": 3, "CARROT": 4}.get(c, 5))
            strb_urgent = "STRAWBERRY" in want_crops and productive("STRAWBERRY") < s_target - 4
            for crop in want_crops:
                n_ok = min(10, seeds.get(crop, 0))
                pp = 1
                for c in plantable[:n_ok]:
                    field.append([pp, c, "PLANT", crop, None])
                plantable = plantable[n_ok:]

    # ---- pickups ----
    n_unfed = sum(1 for t in logi if t[2] == "FEED")
    if n_unfed > 0 and shed.get("WHEAT", 0) > 0:
        for i, u in enumerate(units):
            if carrying[i].get("WHEAT", 0) <= 0:
                pt = [0, _shed_near(u), "PICKUP", "WHEAT", None]
                logi.append(pt) if i == 0 else field.append(pt)
    if any(t[2] == "FERTILIZE" for t in field) and shed.get("FERTILIZER", 0) > 0:
        if sum(1 for iv in carrying if iv.get("FERTILIZER", 0) > 0) < 3:
            field.append([1, _shed_near(units[0] if n_units == 1 else units[1]), "PICKUP", "FERTILIZER", None])
    if tot_carry[0] >= 6:
        logi.append([1, _shed_near(units[0]), "DROP", None, None])
    for i in range(1, n_units):
        if tot_carry[i] >= (4 if carrying[i].get("MILK", 0) > 0 else 12):
            field.append([1, _shed_near(units[i]), "DROP", None, None])

    # ---- validity ----
    def valid(t):
        prio, pos, op, arg, need = t[:5]
        tile = farm["tiles"][pos[1]][pos[0]]
        if op == "WATER":
            return isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today")
        if op == "HARVEST":
            return isinstance(tile, dict) and tile.get("yield_units", 0) > 0
        if op == "PLANT":
            return tile is None and seeds.get(arg, 0) > 0
        if op == "DIG":
            return isinstance(tile, dict) and tile.get("kind") == "WEED"
        if op == "FEED":
            return isinstance(tile, dict) and "animal" in tile and not tile.get("fed_today")
        if op == "CARE":
            return isinstance(tile, dict) and "animal" in tile and not tile.get("cared_today")
        if op == "COLLECT_FERTILIZER":
            return isinstance(tile, dict) and "animal" in tile and tile.get("fertilizer_available")
        if op == "FERTILIZE":
            return isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("fertilized_until_day", -1) < day
        if op in ("BUILD_COOP", "BUILD_PASTURE"):
            return tile is None
        if op == "PLACE":
            return isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") and "animal" not in tile
        if op == "PICKUP":
            return shed.get(arg, 0) > 0
        if op == "DROP":
            return True
        return False

    for t in logi + field:
        t.append(False)

    n_hands = max(1, n_units - 1)
    def sector(pos):
        ang = (math.atan2(pos[1] - 4.5, pos[0] - 4.5) + math.pi) / (2 * math.pi)
        return int(ang * n_hands) % n_hands

    locks = st["locks"]
    acts = []

    def best_task(pool, u, i, restrict_sector=None):
        best, bs_ = None, None
        for t in pool:
            if t[5]: continue
            prio, pos, op, arg, need = t[:5]
            if restrict_sector is not None and sector(pos) != restrict_sector:
                continue
            if op == "PICKUP" and carrying[i].get(arg, 0) > 0:
                continue
            if need and carrying[i].get(need, 0) <= 0 and op != "PICKUP":
                continue
            score = -prio * 6 - _d(u, pos) + (3 if _d(u, pos) == 0 else 0)
            if bs_ is None or score > bs_:
                best, bs_ = t, score
        return best

    for i, u in enumerate(units):
        lk = locks.get(i)
        chosen = None
        if lk is not None:
            pool = (logi + field) if i == 0 else field
            for t in pool:
                if not t[5] and t[1] == lk[0] and t[2] == lk[1] and valid(t):
                    chosen = t; break
            if chosen is None:
                locks.pop(i, None)
        if chosen is None:
            if i == 0:
                chosen = best_task(logi, u, i) or best_task(field, u, i)
            else:
                # hands: sector first, then anywhere
                chosen = best_task(field, u, i, restrict_sector=sector(u)) \
                         or best_task(field, u, i, restrict_sector=(i - 1) % n_hands) \
                         or best_task(field, u, i)
        if chosen is None:
            acts.append(["PASS"]); continue
        chosen[5] = True
        locks[i] = (chosen[1], chosen[2])
        prio, pos, op, arg, need = chosen[:5]
        if u == pos:
            if not valid(chosen) and op not in ("DROP",):
                locks.pop(i, None); acts.append(["PASS"]); continue
            locks.pop(i, None)
            if op == "PICKUP":
                acts.append(["PICKUP", arg, max(1, min(6, shed.get(arg, 0)))])
            elif op in ("PLANT", "PLACE"):
                acts.append([op, arg])
            elif op in ("BUILD_COOP", "BUILD_PASTURE"):
                acts.append([op])
            else:
                acts.append([op])
        else:
            dx, dy = pos[0] - u[0], pos[1] - u[1]
            acts.append(["EAST" if dx > 0 else ("WEST" if dx < 0 else ("SOUTH" if dy > 0 else "NORTH"))])

    return {"farmer": acts[0] if acts else ["PASS"], "hands": acts[1:], "market": orders}

kaggle_entry_agent = agent
