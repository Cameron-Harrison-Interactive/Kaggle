# v46.1 "SCRIPTED SEASON" — day-by-day offline-scripted engine (2026-09-09).
# Harrison Interactive original build.
#
# ARCHITECTURE (built on the daily-reset fact):
#   Every morning the engine hands us a clean slate: farmer at (4,4), zero
#   hands, inventories force-dropped to the shed, flags reset. Each day is an
#   INDEPENDENT planning problem with complete information. At h0 we plan the
#   entire day offline — market orders, hires, buys, full task routing with
#   carrying chains — validated in an intraday simulator that mirrors the
#   engine's unit-action semantics exactly. The rest of the day we emit
#   literal scripted actions. No live coordination, nothing wasted.
#
# ENGINE TRUTHS THIS BUILD OBEYS (from envsrc):
#   - op is "CARE" (not PET); PLANT consumes private.seeds directly; PLACE
#     takes the animal from INVENTORY while standing on an unoccupied
#     matching structure; BUY_ANIMAL/BUY_PRODUCT land in the SHED (cap 100).
#   - Plants: consecutive_unwatered >= 2 at EOD refresh -> WEED. Planting day
#     counts as unwatered, so EVERY plant is watered the day it is planted;
#     after that every-other-day water survives (water when cuw >= 1).
#     Non-ongoing crops rot intraday from (planted+max_yield_day+1)*24:
#     harvested at age == max_yield_day at the latest.
#   - Movement onto LOCKED tiles is legal (ops are not); board is 10x10.
#   - HIRE/BUY/SELL orders process in the market phase AFTER unit actions,
#     max 10/turn; bought seeds/animals are usable from the NEXT hour.
#   - Hands spawn at min-occupancy shed tile, NWSE preference: cycle
#     (5,4),(5,5),(4,5),(4,4) for hands 1..N (farmer occupies (4,4) first).
#   - FERTILIZE sets fertilized_until_day = day+2 (3 days), doubles the
#     water bonus of non-ongoing crops and the night production of ongoing.

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
SHED_TILES = ((4, 4), (5, 4), (4, 5), (5, 5))   # engine _shed_access_tiles order
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]

_SESSIONS = {}


def _d(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _shed_near(pos):
    return min(SHED_TILES, key=lambda c: _d(pos, c))


# ----------------------------------------------------------------------------
# Morning state: parse the true engine state into a plain dict
# ----------------------------------------------------------------------------

def parse_state(obs, p):
    farm = obs["farms"][p]
    priv = obs.get("private", {}) or {}
    owned = set()
    animals = []    # dicts: pos, kind, fed, cared, collected, yield
    plants = []     # dicts: pos, crop, planted, watered, yield, cuw, fert
    empties = []
    structures = [] # (pos, kind) — unoccupied structures
    weeds = []
    for y, row in enumerate(farm["tiles"]):
        for x, t in enumerate(row):
            if t == "LOCKED":
                continue
            owned.add((x, y))
            if t is None:
                empties.append((x, y))
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    plants.append({"pos": (x, y), "crop": t["crop"], "planted": t.get("planted_day", 0),
                                   "watered": bool(t.get("watered_today", False)),
                                   "yield": t.get("yield_units", 0),
                                   "cuw": t.get("consecutive_unwatered", 0),
                                   "fert": t.get("fertilized_until_day", -1)})
                elif "animal" in t:
                    animals.append({"pos": (x, y), "kind": t["animal"], "fed": bool(t.get("fed_today", False)),
                                    "cared": bool(t.get("cared_today", False)),
                                    "collected": not bool(t.get("fertilizer_available", False)),
                                    "yield": t.get("yield_units", 0)})
                elif k in ("COOP", "PASTURE"):
                    structures.append({"pos": (x, y), "kind": k})
                elif k == "WEED":
                    weeds.append((x, y))
    mkt = obs.get("market", {}) or {}
    # ---- SPY: the shared obs exposes the enemy farm every hour ----
    enemy_wheat = 0
    enemy_animals = 0
    enemy_money = 0.0
    ef = obs["farms"][1 - p] if len(obs.get("farms", [])) > 1 else None
    if ef:
        enemy_money = float(ef.get("money", 0))
        for row in ef.get("tiles", []):
            for t in row:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT" and t.get("crop") == "WHEAT":
                        enemy_wheat += 1
                    elif "animal" in t:
                        enemy_animals += 1
    return {
        "day": int(obs.get("day", 0)),
        "enemy_wheat": enemy_wheat, "enemy_animals": enemy_animals,
        "enemy_money": enemy_money,
        "money": float(farm["money"]),
        "shed": dict(priv.get("shed", {}) or {}),
        "seeds": dict(priv.get("seeds", {}) or {}),
        "animals": animals, "plants": plants, "empties": empties,
        "structures": structures, "weeds": weeds, "owned": owned,
        "quadrants": set(farm.get("unlocked_quadrants", ["NW"])),
        "farmer": tuple(farm["farmer"]),
        "px": dict(mkt.get("prices", {}) or {}),
        "inv": dict(mkt.get("inventory", {}) or {}),
    }


# ----------------------------------------------------------------------------
# Farm plan: hires, land, animals, seeds, sells — per day
# ----------------------------------------------------------------------------

def crew_target(day):
    if day <= 3: return 8
    if day <= 7: return 10
    if day <= 11: return 11
    if day >= 27: return 9
    return 12


def plan_market(S, day):
    """Returns (orders_by_hour {h: [order,...]}, projection dict).

    Orders are queued flat then split 10-per-turn across hours 0..4 (the
    engine caps 10 market orders per turn). Arrivals (seeds/animals/products)
    are recorded with their order hour so the intraday sim knows from which
    hour they are usable (market phase runs AFTER unit actions, so an item
    ordered at hour h is usable from hour h+1).
    """
    flat = []          # orders in execution priority order
    arrivals = {"seeds": {}, "shed": {}}   # item -> list of (n, hour)
    money = S["money"]
    px = S["px"]
    shed = dict(S["shed"])
    seeds = dict(S["seeds"])
    animals = list(S["animals"])
    n_an = len(animals)

    def emit(order):
        flat.append(order)
        return len(flat) - 1

    def arrive(kind, item, n, idx):
        arrivals[kind].setdefault(item, []).append((n, idx // 10))

    # ---- 1) FEED FIRST: an unfed animal escapes after 2 missed days ----
    if day >= 29:
        keep_w = 0            # horn: feed wheat sells too
    elif day >= 26:
        keep_w = max(4, n_an)  # 1-day reserve (d28 feeding still buys d29 production)
    else:
        keep_w = max(8, n_an * 2)
    feed_stock = shed.get("WHEAT", 0)
    if n_an > 0 and feed_stock < n_an and px.get("WHEAT", 25) <= 60:
        need = n_an - feed_stock
        spend = min(money - 40, need * px.get("WHEAT", 25))
        if spend > 0:
            need = max(1, int(spend // px.get("WHEAT", 25)))
            idx = emit(["BUY_PRODUCT", "WHEAT", need])
            arrive("shed", "WHEAT", need, idx)
            money -= need * px.get("WHEAT", 25)
            shed["WHEAT"] = feed_stock + need

    # ---- 2) HIRES: task-driven; cap 12 (10 at h0, 2 at h1) ----
    n_ops = sum(1 for pl in S["plants"] if not pl["watered"]) + 2 * n_an + n_an // 2
    want = min(10, max(crew_target(day), min(10, 8 + (n_ops - 60) // 25)))
    cost = sum(FIB[i] for i in range(want))
    while want > 8 and money < cost + 400:
        want -= 1
        cost = sum(FIB[i] for i in range(want))
    if money >= cost + 150:
        for _ in range(want):
            emit(["HIRE"])
        money -= cost
    else:
        want = 8
        cost = sum(FIB[i] for i in range(want))
        if money >= cost:
            for _ in range(want):
                emit(["HIRE"])
            money -= cost
        else:
            want = 0

    # ---- 2.5) WAR SELLS (v50: volume + timing; playbook §8b) ----
    # Shared market, shed-direct execution, lockstep 1:1 per unit: sell max at
    # the earliest indices, ahead of seed buys (cash + price priority).
    fert_use = min(len([pl for pl in S["plants"] if pl["crop"] in ("MELON", "STRAWBERRY")]), 12)
    def qsell(item, n):
        n = min(n, shed.get(item, 0))
        if n > 0:
            emit(["SELL", item, n])
            shed[item] = shed.get(item, 0) - n

    qsell("FERTILIZER", max(0, shed.get("FERTILIZER", 0) - fert_use))
    # mega-orders: huge n drains the whole shed per item, aborts when empty —
    # intraday harvests convert to cash every hour via the standing sells.
    for it in ("MELON", "STRAWBERRY", "MILK", "WOOL", "EGG", "CARROT", "TOMATO"):
        qsell(it, 10 ** 6)
    # wheat: FLOOD only vs wheat-heavy enemies (spy obs.farms). Vs balanced
    # twins the flood is mutual harm — hold and sell into the late scarcity.
    my_w = sum(1 for pl in S["plants"] if pl["crop"] == "WHEAT")
    en_w = S.get("enemy_wheat", 0)
    wheat_heavy_enemy = en_w >= 10 and en_w >= 1.2 * max(1, my_w)
    if wheat_heavy_enemy:
        qsell("WHEAT", max(0, shed.get("WHEAT", 0) - keep_w))
    elif shed.get("WHEAT", 0) > keep_w and px.get("WHEAT", 25) >= 36:
        qsell("WHEAT", shed.get("WHEAT", 0) - keep_w)
    elif shed.get("WHEAT", 0) > 90:
        qsell("WHEAT", shed.get("WHEAT", 0) - 90)

    # ---- 3) SEEDS: gap-based steady-state targets ----
    # carrot is the early cash bridge; wheat feeds; melon two waves; strb build-up
    counts = {}
    standing = {}
    pipe = {}
    for pl in S["plants"]:
        counts[pl["crop"]] = counts.get(pl["crop"], 0) + _remaining(pl, day)
        standing[pl["crop"]] = standing.get(pl["crop"], 0) + 1
        pipe[pl["crop"]] = pipe.get(pl["crop"], 0) + _future_prods(pl, day)
    n_empty = len(S["empties"])
    # tiles freeing up today (non-ongoing past window, harvested by plan)
    # ---- price-adaptive targets: the market obs prices reveal the regime ----
    # solo: melon ~240, strb ~110, wheat ~24  -> melon-heavy
    # H2H vs wheat-desk: strb ~200+, milk ~300, wheat ~46, melon crashes -> strb/wheat
    pxm = px.get("MELON", 250); pxs = px.get("STRAWBERRY", 120)
    pxw = px.get("WHEAT", 25); pxt = px.get("TOMATO", 60)
    # H2H regime (wheat 46, strb 200+, milk 300): wheat volume desk + strb
    # solo regime (wheat 24, melon 240): melon waves + lean wheat
    # TT-router book (decoded from its tapes): no carrot bridge — wheat wave
    # funds the animal ramp; strb treadmill scaled to 33; wheat to 40.
    if day == 0:
        targets = {"WHEAT": 7}
    elif day <= 3:
        targets = {"WHEAT": 8}
    elif day <= 9:
        targets = {"WHEAT": 12}
    elif day <= 15:
        targets = {"WHEAT": 24}
    elif day <= 19:
        targets = {"WHEAT": 32}
    elif day <= 27:
        targets = {"WHEAT": 40}
    else:
        targets = {"WHEAT": 0}
    if day <= 1:
        targets["MELON"] = 12   # wave 1 (both bots plant it d0-1)
    elif 10 <= day <= 17 and pxm >= 120:
        targets["MELON"] = 12   # wave-2 rotation; d17 = last sow that ripens by d29
    if 3 <= day <= 5:
        targets["STRAWBERRY"] = 12
    elif 6 <= day <= 8:
        targets["STRAWBERRY"] = 20
    elif 9 <= day <= 19:
        targets["STRAWBERRY"] = 33   # treadmill; d19 last sow prods by d29
    # priority: wheat (feed) -> carrot (cash) -> melon (bulk) -> strb -> tomato
    # early bridge: carrot cash first; later: wheat feed + strb volume first
    if day <= 10 and len(S["quadrants"]) == 1:
        order = ["CARROT", "WHEAT", "STRAWBERRY", "MELON", "TOMATO"]
    else:
        order = ["WHEAT", "STRAWBERRY", "CARROT", "MELON", "TOMATO"]
    seed_px = {c: CROPS[c]["seed"] for c in order}
    # ongoing crops: sustain a production pipeline (grow time included);
    # standing cap prevents tile runaway. non-ongoing: plain tile count.
    pipe_cap = {"STRAWBERRY": 34, "TOMATO": 10}
    for crop in order:
        have_seeds = seeds.get(crop, 0)
        if CROPS[crop]["ongoing"]:
            gap = targets.get(crop, 0) * 2 - pipe.get(crop, 0) - have_seeds * 4
            if standing.get(crop, 0) + have_seeds >= pipe_cap.get(crop, 99):
                gap = 0
        else:
            gap = targets.get(crop, 0) - counts.get(crop, 0) - have_seeds
        gap = max(0, min(int(math.ceil(gap)), n_empty))
        while gap > 0 and money >= seed_px[crop] + 300:
            n = min(gap, max(1, int((money - 300) // seed_px[crop])))
            n = min(n, 10)
            idx = emit(["BUY_SEED", crop, n])
            arrive("seeds", crop, n, idx)
            money -= n * seed_px[crop]
            seeds[crop] = seeds.get(crop, 0) + n
            counts[crop] = counts.get(crop, 0) + n
            n_empty -= n
            gap -= n

    # ---- 4) ANIMALS: TT-style ramp — animals are the engine, buy early ----
    sheep_t = min(5, max(0, day - 4)) if day <= 12 else 5
    cow_t = min(9, max(2, day + 1)) if day <= 9 else 9
    tgt = {"GOOSE": (3 if day >= 4 else 0),
           "COW": cow_t,
           "SHEEP": sheep_t}
    have = {}
    for a in animals:
        have[a["kind"]] = have.get(a["kind"], 0) + 1
    for kind in ("GOOSE", "COW", "SHEEP"):
        have[kind] = have.get(kind, 0) + shed.get(kind, 0)
    shed_total = sum(shed.values())
    last_buy_day = {"GOOSE": 24, "COW": 16, "SHEEP": 18}  # d+first_yield <= 29
    for kind in ("GOOSE", "COW", "SHEEP"):
        if day > last_buy_day[kind]:
            continue
        if kind == "GOOSE":
            gate = 200
        elif kind == "COW":
            gate = 150
        else:
            gate = 150
        while have.get(kind, 0) < tgt[kind] and money - ANIMALS[kind]["cost"] >= gate and shed_total < 80:
            idx = emit(["BUY_ANIMAL", kind, 1])
            arrive("shed", kind, 1, idx)
            money -= ANIMALS[kind]["cost"]
            shed[kind] = shed.get(kind, 0) + 1
            have[kind] = have.get(kind, 0) + 1
            shed_total += 1

    # ---- 5) LAND (funded by cash + today's sell revenue) ----
    sell_rev = sum(int(S["px"].get(o[1], 0)) * o[2] for o in flat if o[0] == "SELL")
    nq = len(S["quadrants"])
    if nq == 1 and day >= 5 and money + sell_rev >= 1600:
        emit(["BUY_LAND"]); money -= 1000
    elif nq == 2 and day >= 9 and money + sell_rev >= 3200:
        emit(["BUY_LAND"]); money -= 2000
    elif nq == 3 and day >= 12 and money + sell_rev >= 6400 and sum(targets.values()) > 55:
        emit(["BUY_LAND"]); money -= 4000

    # ---- 6) FERTILIZER for melon/strb ----
    if fert_use > 0 and shed.get("FERTILIZER", 0) < fert_use and px.get("FERTILIZER", 100) <= 150:
        need = fert_use - shed.get("FERTILIZER", 0)
        if money >= need * 150:
            idx = emit(["BUY_PRODUCT", "FERTILIZER", need])
            arrive("shed", "FERTILIZER", need, idx)
            money -= need * px.get("FERTILIZER", 100)
            shed["FERTILIZER"] = shed.get("FERTILIZER", 0) + need


    # ---- wheat rebound arbitrage (engine: BUY_PRODUCT is WHEAT/FERT only) ----
    pwa = px.get("WHEAT", 25)
    if pwa <= 16 and money >= 2000 and day <= 26:
        n_ab = min(60, int((money - 1500) // max(1, pwa)))
        if n_ab > 0:
            emit(["BUY_PRODUCT", "WHEAT", n_ab])
            money -= n_ab * pwa
            shed["WHEAT"] = shed.get("WHEAT", 0) + n_ab

    obh = {h: flat[10 * h: 10 * h + 10] for h in range(max(1, (len(flat) + 9) // 10))}
    # ---- HOURLY STANDING SELLS: repeat the sell list all day (no-ops when
    # shed is empty; anything units DROP intraday converts to cash same day) ----
    sells_flat = [o for o in flat if o[0] == "SELL"]
    if sells_flat:
        for h in range(len(obh), 24):
            obh[h] = list(sells_flat[:10])
    return obh, {"money": money, "shed": shed, "seeds": seeds, "arrivals": arrivals,
                 "want": want}


# ----------------------------------------------------------------------------
# Task building (from true morning state + projected arrivals)
# ----------------------------------------------------------------------------

def _remaining(pl, day):
    """Fraction of a fresh tile's production left (ongoing crops have a
    lifetime cap: production stops after max_yield production events)."""
    cd = CROPS[pl["crop"]]
    if not cd["ongoing"]:
        return 1.0 if (day - pl["planted"]) <= cd["max_yield_day"] else 0.0
    age = day - pl["planted"]
    if age < cd["first_yield_day"]:
        return 1.0
    done = (age - cd["first_yield_day"]) // cd["interval"] + 1
    return max(0.0, cd["max_yield"] - done) / float(cd["max_yield"])


def _future_prods(pl, day):
    """Future production events of a tile (fresh seed = max_yield)."""
    cd = CROPS[pl["crop"]]
    if not cd["ongoing"]:
        return 4 if (day - pl["planted"]) <= cd["max_yield_day"] else 0
    age = day - pl["planted"]
    if age < cd["first_yield_day"]:
        return cd["max_yield"]
    done = (age - cd["first_yield_day"]) // cd["interval"] + 1
    return max(0, cd["max_yield"] - done)


def build_tasks(S, day):
    tasks = []
    for a in S["animals"]:
        if not a["fed"]:
            tasks.append(("FEED", a["pos"], "WHEAT"))
        if not a["cared"]:
            tasks.append(("CARE", a["pos"], None))
        if not a["collected"]:
            tasks.append(("COLLECT", a["pos"], None))
        if a["yield"] >= (2 if a["kind"] == "GOOSE" else 3):
            tasks.append(("HARVESTA", a["pos"], None))
    for pl in S["plants"]:
        cd = CROPS[pl["crop"]]
        age = day - pl["planted"]
        ws = (cd["max_yield_day"] + 1) // 2
        rem = _remaining(pl, day)
        if rem <= 0.0:
            tasks.append(("DIGP", pl["pos"], None))   # exhausted: recycle tile
            continue
        if not pl["watered"]:
            if cd["ongoing"]:
                # production happens at the EOD refresh when
                # days_since_first = (age + 1 - first) hits an interval multiple
                prod_today = (age + 1 >= cd["first_yield_day"]
                              and (age + 1 - cd["first_yield_day"]) % cd["interval"] == 0)
                if pl["cuw"] >= 1 or prod_today:
                    tasks.append(("WATER", pl["pos"], None))
            else:
                if pl["cuw"] >= 1 or (ws <= age <= cd["max_yield_day"]):
                    tasks.append(("WATER", pl["pos"], None))
        if pl["yield"] > 0 and age >= cd["first_yield_day"]:
            if not cd["ongoing"]:
                if age >= cd["max_yield_day"] or pl["yield"] >= cd["max_yield"]:
                    tasks.append(("HARVESTC", pl["pos"], None))
            elif pl["yield"] >= 2:
                tasks.append(("HARVESTC", pl["pos"], None))
        if pl["crop"] in ("MELON", "STRAWBERRY") and pl["fert"] < day:
            if cd["ongoing"] or (ws - 2 <= age <= cd["max_yield_day"]):
                tasks.append(("FERTILIZE", pl["pos"], "FERTILIZER"))
    return tasks


# ----------------------------------------------------------------------------
# Full-day plan: choreography + intraday simulation
# ----------------------------------------------------------------------------

def plan_day(S, day):
    obh, post = plan_market(S, day)
    tasks = build_tasks(S, day)
    want = max(0, post["want"])
    n_units = 1 + want

    # hand existence hours: order k of the HIREs lands in market phase of its
    # hour, so hand i (0-based) exists from hour (order_hour + 1).
    hire_hours = []
    for h in range(5):
        for o in obh.get(h, []):
            if o and o[0] == "HIRE":
                hire_hours.append(h)
    hand_ready = [h + 1 for h in hire_hours]
    while len(hand_ready) < want:
        hand_ready.append(3)
    n_h0 = sum(1 for hr in hand_ready if hr <= 1)   # hands existing from h1

    # spawn positions (engine: min occupancy, NWSE preference; farmer (4,4))
    nwse = [(4, 4), (5, 4), (4, 5), (5, 5)]
    occ = {t: 0 for t in nwse}
    if tuple(S["farmer"]) in occ:
        occ[tuple(S["farmer"])] += 1
    spawn = [tuple(S["farmer"])]
    for _ in range(min(want, n_h0)):
        best = min(nwse, key=lambda t: (occ[t], nwse.index(t)))
        spawn.append(best)
        occ[best] += 1

    # late hands (h1 hires) spawn at the h1 market from h1-end occupancy;
    # placeholder spawn now, computed exactly inside the hour loop.
    late_spawns = want - len(spawn) + 1
    for _ in range(max(0, late_spawns)):
        spawn.append(None)
    arr = post["arrivals"]
    # land bought today unlocks at (order hour + 1); plantable same day
    unlock = {}
    for hh in range(5):
        for o in obh.get(hh, []):
            if o and o[0] == "BUY_LAND":
                nq = len(S["quadrants"])
                q = ["NE", "SW", "SE"][nq - 1]
                for y in range(10):
                    for x in range(10):
                        if ((q == "NE" and x >= 5 and y < 5) or
                            (q == "SW" and x < 5 and y >= 5) or
                            (q == "SE" and x >= 5 and y >= 5)):
                            unlock[(x, y)] = hh + 1
    extra_empty = [pos for pos in unlock]
    sim = {
        "pos": list(spawn),
        "inv": [dict() for _ in range(n_units)],
        "fed": set(a["pos"] for a in S["animals"] if a["fed"]),
        "cared": set(a["pos"] for a in S["animals"] if a["cared"]),
        "collected": set(a["pos"] for a in S["animals"] if a["collected"]),
        "watered": set(pl["pos"] for pl in S["plants"] if pl["watered"]),
        "fert": set(pl["pos"] for pl in S["plants"] if pl["fert"] >= day),
        "harvested": set(),
        "animal_at": {a["pos"]: a["kind"] for a in S["animals"]},
        "animal_yield": {a["pos"]: a["yield"] for a in S["animals"]},
        "plant_at": {pl["pos"]: pl for pl in S["plants"]},
        "weed_at": set(S["weeds"]),
        "empty_at": set(S["empties"]) | set(extra_empty),
        "unlock": unlock,
        "struct_at": {s["pos"]: s["kind"] for s in S["structures"]},
        # shed/seeds pools with arrival hours (usable from hour+1)
        "shed_base": dict(S["shed"]),
        "shed_add": arr["shed"],
        "shed_taken": {},
        "seeds_base": dict(S["seeds"]),
        "seeds_add": arr["seeds"],
        "seeds_used": {},
    }

    def shed_avail(item, h):
        n = sim["shed_base"].get(item, 0)
        for cnt, hr in sim["shed_add"].get(item, []):
            if hr < h:
                n += cnt
        return n - sim["shed_taken"].get(item, 0)

    def shed_take(item, n, h):
        n = min(n, shed_avail(item, h))
        if n > 0:
            sim["shed_taken"][item] = sim["shed_taken"].get(item, 0) + n
        return n

    def seeds_avail(crop, h):
        n = sim["seeds_base"].get(crop, 0)
        for cnt, hr in sim["seeds_add"].get(crop, []):
            if hr < h:
                n += cnt
        return n - sim["seeds_used"].get(crop, 0)

    # ---- animal servers ----
    ani = S["animals"]
    routes = {i: [] for i in range(n_units)}
    if ani:
        units_by_c = sorted(range(1, n_units),
                            key=lambda i: min(_d(spawn[i] or (4, 4), a["pos"]) for a in ani))
        n_servers = max(2, min(4, (len(ani) + 2) // 3))
        servers = units_by_c[:n_servers]
        ani_sorted = sorted(ani, key=lambda a: (a["pos"][0] + a["pos"][1], a["pos"][0]))
        per = max(1, (len(ani_sorted) + n_servers - 1) // n_servers)
        for si, u in enumerate(servers):
            mine = ani_sorted[si * per:(si + 1) * per]
            if not mine:
                continue
            routes[u].append(("PICKUP", _shed_near(spawn[u] or (4, 4)), "WHEAT",
                              min(6, len(mine))))
            for a in mine:
                routes[u].append(("FEED", a["pos"], None))
                routes[u].append(("CARE", a["pos"], None))
                routes[u].append(("COLLECT", a["pos"], None))
                if a["yield"] >= (2 if a["kind"] == "GOOSE" else 3):
                    routes[u].append(("HARVESTA", a["pos"], None))

    # ---- field wedges (water / harvest / fertilize) ----
    field = [t for t in tasks if t[0] in ("WATER", "HARVESTC", "FERTILIZE", "DIGP")]
    if field:
        cx = sum(t[1][0] for t in field) / len(field)
        cy = sum(t[1][1] for t in field) / len(field)
        order = sorted(field, key=lambda t: math.atan2(t[1][1] - cy, t[1][0] - cx))
        avail = [i for i in range(1, n_units) if i not in (servers if ani else [])]
        if not avail:
            avail = list(range(1, n_units))
        K = len(avail)
        n_f = len(order)
        for j, i in enumerate(avail):
            wedge = order[j * n_f // K:(j + 1) * n_f // K]
            if not wedge:
                continue
            if any(t[0] == "FERTILIZE" for t in wedge):
                routes[i].append(("PICKUP", _shed_near(spawn[i] or (4, 4)), "FERTILIZER",
                                  min(6, sum(1 for t in wedge if t[0] == "FERTILIZE"))))
            pos = spawn[i] or (4, 4)
            rem = list(wedge)
            while rem:
                ni = min(range(len(rem)), key=lambda k: _d(pos, rem[k][1]))
                t = rem.pop(ni)
                routes[i].append((t[0], t[1], t[2]))
                pos = t[1]

    # ---- backlog: structures for bought animals, planting, weeding ----
    backlog = []   # mutable tasks: [kind, pos, arg, claim(-1=free)]
    bought_kinds = []
    for h in range(5):
        for o in obh.get(h, []):
            if o and o[0] == "BUY_ANIMAL":
                bought_kinds.append(o[1])
    # cows+sheep share PASTURE; geese need COOP. cluster near shed.
    reserved = set()
    for kind in bought_kinds:
        struct = ANIMALS[kind]["structure"]
        spots = [c for c in sorted(sim["empty_at"], key=lambda c: _d(c, (4, 4)))
                 if c not in reserved]
        if not spots:
            break
        c = spots[0]
        reserved.add(c)
        backlog.append(["BUILD", c, struct, -1])
        backlog.append(["PLACE", c, kind, -1])
    # existing empty structures + shed animals waiting: place them too
    for s in S["structures"]:
        if s["pos"] in sim["animal_at"]:
            continue
        for kind in ("COW", "SHEEP", "GOOSE"):
            if shed_avail(kind, 24) > 0 and ANIMALS[kind]["structure"] == s["kind"]:
                backlog.append(["PLACE", s["pos"], kind, -1])
                break
    # planting: highest-value crops on the best tiles (near shed)
    plant_jobs = []
    for crop in ("CARROT", "STRAWBERRY", "MELON", "TOMATO", "WHEAT"):
        n = int(seeds_avail(crop, 5))
        for _ in range(n):
            spots = [c for c in sorted(sim["empty_at"], key=lambda c: _d(c, (4, 4)))
                     if c not in reserved and c not in [j[1] for j in plant_jobs]]
            if not spots:
                break
            plant_jobs.append(["PLANT", spots[0], crop, -1])
    backlog.extend(plant_jobs)
    for w in sorted(sim["weed_at"], key=lambda c: _d(c, (4, 4)))[:14]:
        backlog.append(["DIG", w, None, -1])

    actions = [["PASS"] * n_units for _ in range(24)]
    ptr = [0] * n_units

    # ---- intraday simulation (mirrors engine semantics) ----
    def unit_step(i, h):
        u = sim["pos"][i]

        def walk(tgt):
            # engine: moves succeed only inside the 10x10 board
            cands = []
            dx, dy = tgt[0] - u[0], tgt[1] - u[1]
            if dx > 0: cands.append(("EAST", u[0] + 1, u[1]))
            elif dx < 0: cands.append(("WEST", u[0] - 1, u[1]))
            if dy > 0: cands.append(("SOUTH", u[0], u[1] + 1))
            elif dy < 0: cands.append(("NORTH", u[0], u[1] - 1))
            for m, nx, ny in cands:
                if 0 <= nx < 10 and 0 <= ny < 10:
                    sim["pos"][i] = (nx, ny)
                    return [m]
            return ["PASS"]

        # ---- fixed route ----
        rt = routes[i]
        while ptr[i] < len(rt):
            kind, pos, arg = rt[ptr[i]][:3]
            if kind == "PICKUP":
                if u == pos:
                    item = arg
                    n = shed_take(item, rt[ptr[i]][3] if len(rt[ptr[i]]) > 3 else 1, h)
                    if n <= 0:
                        ptr[i] += 1
                        continue
                    sim["inv"][i][item] = sim["inv"][i].get(item, 0) + n
                    ptr[i] += 1
                    return ["PICKUP", item, n]
                return walk(pos)
            if kind == "FEED":
                if pos in sim["fed"]:
                    ptr[i] += 1; continue
                if sim["inv"][i].get("WHEAT", 0) <= 0:
                    sh = _shed_near(u)
                    if u == sh:
                        n = shed_take("WHEAT", 6, h)
                        if n > 0:
                            sim["inv"][i]["WHEAT"] = sim["inv"][i].get("WHEAT", 0) + n
                            return ["PICKUP", "WHEAT", n]
                        ptr[i] += 1; continue
                    return walk(sh)
                if u == pos:
                    sim["inv"][i]["WHEAT"] -= 1
                    sim["fed"].add(pos)
                    ptr[i] += 1
                    return ["FEED"]
                return walk(pos)
            if kind == "CARE":
                if pos in sim["cared"]:
                    ptr[i] += 1; continue
                if u == pos:
                    sim["cared"].add(pos)
                    ptr[i] += 1
                    return ["CARE"]
                return walk(pos)
            if kind == "COLLECT":
                if pos in sim["collected"]:
                    ptr[i] += 1; continue
                if u == pos:
                    sim["collected"].add(pos)
                    sim["inv"][i]["FERTILIZER"] = sim["inv"][i].get("FERTILIZER", 0) + 1
                    ptr[i] += 1
                    return ["COLLECT_FERTILIZER"]
                return walk(pos)
            if kind == "HARVESTA":
                if pos in sim["harvested"]:
                    ptr[i] += 1; continue
                if u == pos:
                    kind_a = sim["animal_at"][pos]
                    prod = ANIMALS[kind_a]["product"]
                    yv = sim["animal_yield"].get(pos, 0)
                    sim["inv"][i][prod] = sim["inv"][i].get(prod, 0) + yv
                    sim["harvested"].add(pos)
                    ptr[i] += 1
                    return ["HARVEST"]
                return walk(pos)
            if kind == "WATER":
                if pos in sim["watered"]:
                    ptr[i] += 1; continue
                if u == pos:
                    sim["watered"].add(pos)
                    ptr[i] += 1
                    return ["WATER"]
                return walk(pos)
            if kind == "HARVESTC":
                if pos in sim["harvested"] or pos not in sim["plant_at"]:
                    ptr[i] += 1; continue
                if u == pos:
                    pl = sim["plant_at"][pos]
                    sim["inv"][i][pl["crop"]] = sim["inv"][i].get(pl["crop"], 0) + pl["yield"]
                    sim["harvested"].add(pos)
                    sim["plant_at"].pop(pos, None)
                    sim["empty_at"].add(pos)
                    ptr[i] += 1
                    return ["HARVEST"]
                return walk(pos)
            if kind == "DIGP":
                if pos not in sim["plant_at"] or pos in sim["harvested"]:
                    ptr[i] += 1
                    continue
                if u == pos:
                    sim["plant_at"].pop(pos, None)
                    sim["empty_at"].add(pos)
                    ptr[i] += 1
                    return ["DIG"]
                return walk(pos)
            if kind == "FERTILIZE":
                if pos in sim["fert"]:
                    ptr[i] += 1; continue
                if sim["inv"][i].get("FERTILIZER", 0) <= 0:
                    sh = _shed_near(u)
                    if u == sh:
                        n = shed_take("FERTILIZER", 6, h)
                        if n > 0:
                            sim["inv"][i]["FERTILIZER"] = sim["inv"][i].get("FERTILIZER", 0) + n
                            return ["PICKUP", "FERTILIZER", n]
                        ptr[i] += 1; continue
                    return walk(sh)
                if u == pos:
                    sim["inv"][i]["FERTILIZER"] -= 1
                    sim["fert"].add(pos)
                    ptr[i] += 1
                    return ["FERTILIZE"]
                return walk(pos)
            ptr[i] += 1

        # ---- backlog scan: first claimable, executable task ----
        if sim["inv"][i] and all(t[3] == -2 for t in backlog):
            backlog.append(["DROPC", None, None, -1])
        for t in backlog:                 # release my stale claims first
            if t[3] == i:
                t[3] = -1
        for t in backlog:
            kind, pos, arg, claim = t[0], t[1], t[2], t[3]
            if claim not in (-1, i):
                continue
            if kind == "BUILD":
                if sim["unlock"].get(pos, 0) > h:
                    continue              # tile unlocks later today
                if pos not in sim["empty_at"] or pos in sim["struct_at"]:
                    t[3] = -2   # done/invalid: retire
                    continue
                t[3] = i
                if u == pos:
                    sim["empty_at"].discard(pos)
                    sim["struct_at"][pos] = arg
                    t[3] = -2
                    return ["BUILD_PASTURE" if arg == "PASTURE" else "BUILD_COOP"]
                return walk(pos)
            if kind == "PLACE":
                built = pos in sim["struct_at"] and pos not in sim["animal_at"]
                build_pending = any(b[0] == "BUILD" and b[1] == pos and b[3] != -2 for b in backlog)
                if not built:
                    if build_pending:
                        continue          # builder en route; try other work
                    t[3] = -2
                    continue              # structure not happening today
                carrying = sim["inv"][i].get(arg, 0) > 0
                if not carrying:
                    sh = _shed_near(u)
                    if u != sh:
                        t[3] = i
                        return walk(sh)   # go get the animal
                    n = shed_take(arg, 1, h)
                    if n > 0:
                        sim["inv"][i][arg] = sim["inv"][i].get(arg, 0) + 1
                        t[3] = i
                        return ["PICKUP", arg, 1]
                    if any(cnt > 0 and hr >= h for cnt, hr in sim["shed_add"].get(arg, [])):
                        continue          # animal still in transit; other work
                    t[3] = -2
                    continue              # no animal available at all today
                if u == pos:
                    sim["inv"][i][arg] -= 1
                    sim["animal_at"][pos] = arg
                    sim["animal_yield"][pos] = 0
                    t[3] = -2
                    routes[i].insert(ptr[i], ("CARE", pos, None))
                    routes[i].insert(ptr[i], ("FEED", pos, None))
                    return ["PLACE", arg]
                t[3] = i
                return walk(pos)
            if kind == "PLANT":
                if sim["unlock"].get(pos, 0) > h:
                    continue              # tile unlocks later today
                if pos not in sim["empty_at"] or pos in sim["struct_at"]:
                    t[3] = -2
                    continue
                avail = seeds_avail(arg, h)
                if avail <= 0:
                    if any(cnt > 0 and hr >= h for cnt, hr in sim["seeds_add"].get(arg, [])):
                        continue          # seeds in transit
                    t[3] = -2
                    continue
                if h >= 22:
                    continue              # no time to plant+water today
                t[3] = i
                if u == pos:
                    sim["seeds_used"][arg] = sim["seeds_used"].get(arg, 0) + 1
                    sim["empty_at"].discard(pos)
                    sim["plant_at"][pos] = {"pos": pos, "crop": arg, "planted": day,
                                            "watered": False, "yield": 0, "cuw": 1, "fert": -1}
                    t[3] = -2
                    # same-day water is mandatory or the plant dies at EOD
                    routes[i].insert(ptr[i], ("WATER", pos, None))
                    return ["PLANT", arg]
                return walk(pos)
            if kind == "DROPC":
                if not sim["inv"][i]:
                    t[3] = -2
                    continue
                sh = _shed_near(u)
                if u == sh:
                    for item, n in list(sim["inv"][i].items()):
                        sim["shed_base"][item] = sim["shed_base"].get(item, 0) + n
                    sim["inv"][i] = {}
                    t[3] = -2
                    return ["DROP"]
                return walk(sh)
            if kind == "DIG":
                if pos not in sim["weed_at"]:
                    t[3] = -2
                    continue
                t[3] = i
                if u == pos:
                    sim["weed_at"].discard(pos)
                    sim["empty_at"].add(pos)
                    t[3] = -2
                    return ["DIG"]
                return walk(pos)
        return ["PASS"]

    MOVES = {"EAST", "WEST", "SOUTH", "NORTH"}
    for h in range(0, 24):
        for i in range(n_units):
            if i > 0 and hand_ready[i - 1] > h:
                continue
            if i > 0 and sim["pos"][i] is None:
                # spawn now (engine: min-occupancy shed tile at last hour end)
                occ = {t: 0 for t in nwse}
                for j in range(n_units):
                    if sim["pos"][j] is not None and sim["pos"][j] in occ:
                        occ[sim["pos"][j]] += 1
                best = min(nwse, key=lambda t: (occ[t], nwse.index(t)))
                sim["pos"][i] = best
            a = unit_step(i, h)
            if i == 0 and h == 0 and a[0] in MOVES:
                # farmer must NOT move at h0: hand spawn tiles are chosen at
                # the h0 market phase from current occupancy; a moved farmer
                # shifts every spawn tile and desyncs the whole day.
                sim["pos"][0] = spawn[0]
                a = ["PASS"]
            actions[h][i] = a

    return {"market": obh, "actions": actions}


# ----------------------------------------------------------------------------
# Agent entry
# ----------------------------------------------------------------------------

def agent(obs, config=None):
    p = int(obs["player"])
    step = int(obs.get("step", 0))
    day, hour = step // 24, step % 24
    st = _SESSIONS.setdefault(p, {})
    if st.get("day") != day or hour == 0:
        S = parse_state(obs, p)
        st["plan"] = plan_day(S, day)
        st["day"] = day
    plan = st["plan"]
    mkt = list(plan["market"].get(hour, []))[:10]
    farm = obs["farms"][p]
    n_now = 1 + len(farm["hands"])
    acts = plan["actions"][hour] if hour < len(plan["actions"]) else ["PASS"] * n_now
    farmer = acts[0] if acts else ["PASS"]
    hands = [acts[i] if i < len(acts) else ["PASS"] for i in range(1, n_now)]
    return {"farmer": farmer, "hands": hands, "market": mkt}


kaggle_entry_agent = agent
