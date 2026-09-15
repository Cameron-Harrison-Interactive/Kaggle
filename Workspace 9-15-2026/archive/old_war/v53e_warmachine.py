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
    return {
        "day": int(obs.get("day", 0)),
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
    if day <= 2: return 8
    if day <= 5: return 10
    if day <= 9: return 12
    if day >= 29: return 10
    return 14


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
        keep_w = 0            # horn: everything sells
    elif day >= 26:
        keep_w = max(4, n_an)  # 1-day feed only
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
    want = min(13, max(crew_target(day), min(10, 8 + (n_ops - 60) // 25)))
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

    # ---- 2.5) WAR SELLS: flood first, every morning, before anything else ----
    # MEGA-orders (huge n) drain the whole shed per item and abort when empty.
    # Our volume executes at the top of the day's price curve; everyone selling
    # after us eats the crash. Hourly standing repeats keep the pressure on.
    def qsell(item, n):
        n = min(n, shed.get(item, 0))
        if n > 0:
            emit(["SELL", item, n])
            shed[item] = shed.get(item, 0) - n

    fert_use = min(len([pl for pl in S["plants"] if pl["crop"] in ("MELON", "STRAWBERRY")]), 12)
    qsell("FERTILIZER", max(0, shed.get("FERTILIZER", 0) - max(4, min(fert_use, 6))))
    for it in ("MELON", "STRAWBERRY", "MILK", "WOOL", "EGG", "CARROT", "TOMATO"):
        qsell(it, 10 ** 6)
    qsell("WHEAT", max(0, shed.get("WHEAT", 0) - keep_w))

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
    # ---- WAR FARM PLAN: fixed ladder — we impose the market, never react ----
    # Full fields, 4 quads: wheat (feed + flood) / carrot (fast cash) /
    # strb (money printer) / melon waves; animals make eggs/milk/wool + fert.
    if day == 0:
        targets = {"WHEAT": 10, "MELON": 12}
    elif day == 1:
        targets = {"WHEAT": 16, "CARROT": 8}
    elif day <= 3:
        targets = {"WHEAT": 18, "CARROT": 10}
    elif day <= 6:
        targets = {"WHEAT": 22, "CARROT": 10, "STRAWBERRY": 14}
    elif day <= 9:
        targets = {"WHEAT": 24, "CARROT": 8, "STRAWBERRY": 22}
    elif day <= 16:
        targets = {"WHEAT": 26, "STRAWBERRY": 28}
    elif day <= 19:
        targets = {"WHEAT": 26, "STRAWBERRY": 26}
    elif day <= 27:
        targets = {"WHEAT": 28, "STRAWBERRY": 24}
    else:
        targets = {}
    pxm = px.get("MELON", 250)
    if day <= 1:
        targets["MELON"] = 12            # wave 1 sells into the d10-13 window
    elif 10 <= day <= 16 and pxm >= 100:
        targets["MELON"] = 12            # wave 2; last sow d16 ripens by d28
    # priority: wheat (feed floor) -> strb (the money printer) -> carrot -> melon
    order = ["WHEAT", "STRAWBERRY", "CARROT", "MELON"]
    seed_px = {c: CROPS[c]["seed"] for c in order}
    # ongoing crops: sustain a production pipeline (grow time included);
    # standing cap prevents tile runaway. non-ongoing: plain tile count.
    pipe_cap = {"STRAWBERRY": 30}
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

    # ---- 3.6) FULL-FIELDS FALLBACK: any tile the plan left empty gets wheat ----
    if 3 <= day <= 26 and n_empty > 0 and money >= 900:
        n = min(n_empty, 12, int((money - 300) // 10))
        if n > 0:
            idx = emit(["BUY_SEED", "WHEAT", n])
            arrive("seeds", "WHEAT", n, idx)
            money -= n * 10
            seeds["WHEAT"] = seeds.get("WHEAT", 0) + n

    # ---- 4) ANIMALS: war ramp (fixed ladder — eggs/milk/wool flood + fert) ----
    cow_t = min(9, max(1, day)) if day <= 9 else 9
    sheep_t = min(5, max(0, (day - 2) // 2)) if day <= 12 else 5
    tgt = {"GOOSE": (3 if day >= 3 else 0),
           "COW": cow_t,
           "SHEEP": sheep_t}
    have = {}
    for a in animals:
        have[a["kind"]] = have.get(a["kind"], 0) + 1
    for kind in ("GOOSE", "COW", "SHEEP"):
        have[kind] = have.get(kind, 0) + shed.get(kind, 0)
    shed_total = sum(shed.values())
    last_buy_day = {"GOOSE": 24, "COW": 16, "SHEEP": 18}  # must produce before d29
    for kind in ("GOOSE", "COW", "SHEEP"):
        if day > last_buy_day[kind]:
            continue
        if kind == "GOOSE":
            gate = 300
        elif kind == "COW":
            gate = max(300, 60 * (n_an + 1))   # never spend the hire/feed money
        else:
            gate = 350
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
    if nq == 1 and day >= 1 and money + sell_rev >= 1800:
        emit(["BUY_LAND"]); money -= 1000
    elif nq == 2 and day >= 4 and money + sell_rev >= 3600:
        emit(["BUY_LAND"]); money -= 2000
    elif nq == 3 and day >= 8 and money + sell_rev >= 7200:
        emit(["BUY_LAND"]); money -= 4000

    # ---- 6) FERTILIZER for melon/strb ----
    if fert_use > 0 and shed.get("FERTILIZER", 0) < fert_use and px.get("FERTILIZER", 100) <= 150:
        need = fert_use - shed.get("FERTILIZER", 0)
        if money >= need * 150:
            idx = emit(["BUY_PRODUCT", "FERTILIZER", need])
            arrive("shed", "FERTILIZER", need, idx)
            money -= need * px.get("FERTILIZER", 100)
            shed["FERTILIZER"] = shed.get("FERTILIZER", 0) + need

    # ---- arbitrage: buy wheat deep under base, hold for the rebound ----
    # (BUY_PRODUCT is wheat/fert only. Wheat's log cliff floors it ~$17-20,
    #  so anything <= $14 rebounds; town drain guarantees it.)
    n_ab = 0
    pwa = px.get("WHEAT", 25)
    if pwa <= 14 and day <= 26 and money >= 1800:
        n_ab = min(60, int((money - 1200) // max(1, pwa)))
        if n_ab > 0:
            emit(["BUY_PRODUCT", "WHEAT", n_ab])
            money -= n_ab * pwa
    # cheap fertilizer for the strb/melon desks (fert+water = +2 yield)
    if px.get("FERTILIZER", 100) <= 40 and day <= 20 and money >= 1200:
        need = 12
        idx = emit(["BUY_PRODUCT", "FERTILIZER", need])
        arrive("shed", "FERTILIZER", need, idx)
        money -= need * px.get("FERTILIZER", 100)

    # ---- endgame: from d27 dump EVERYTHING (d28-29 = pure liquidation) ----
    if day >= 27:
        for it in ("FERTILIZER", "MELON", "STRAWBERRY", "MILK", "WOOL",
                   "EGG", "CARROT", "TOMATO", "WHEAT"):
            qsell(it, 10 ** 6)

    obh = {h: flat[10 * h: 10 * h + 10] for h in range(max(1, (len(flat) + 9) // 10))}
    # ---- THE FLOOD: standing mega-sells every hour of every day ----
    # Anything units drop intraday converts the same hour; the market never
    # gets a chance to recover before we hit it again tomorrow morning.
    keep_eff = keep_w + n_ab            # hold today's arbitrage wheat for the rebound
    flood = [["SELL", it, 10 ** 6] for it in ("MELON", "STRAWBERRY", "MILK",
                                              "WOOL", "EGG", "CARROT")]
    if day >= 27:
        flood.append(["SELL", "WHEAT", 10 ** 6])
        flood.append(["SELL", "FERTILIZER", 10 ** 6])
    for h in range(len(obh), 24):
        obh[h] = list(flood[:10])
    return obh, {"money": money, "shed": shed, "seeds": seeds, "arrivals": arrivals,
                 "want": want, "targets": targets}


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




# ============================================================================
# REACTIVE ENGINE: no schedule, no position prediction. Every hour the real
# board is parsed and each unit takes ONE action from where it ACTUALLY is.
# ============================================================================

SHED_TILES = ((4, 4), (5, 4), (4, 5), (5, 5))
NEIGH = ((1, 0), (-1, 0), (0, 1), (0, -1))
MOVESTEP = {(1, 0): "EAST", (-1, 0): "WEST", (0, 1): "SOUTH", (0, -1): "NORTH"}


def _d(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _walk_step(u, tgt, owned):
    dx, dy = tgt[0] - u[0], tgt[1] - u[1]
    order = []
    if abs(dx) >= abs(dy):
        if dx: order.append((1 if dx > 0 else -1, 0))
        if dy: order.append((0, 1 if dy > 0 else -1))
    else:
        if dy: order.append((0, 1 if dy > 0 else -1))
        if dx: order.append((1 if dx > 0 else -1, 0))
    for sx, sy in order:
        nxt = (u[0] + sx, u[1] + sy)
        if nxt in owned:
            return [MOVESTEP[(sx, sy)]]
    for sx, sy in order:
        return [MOVESTEP[(sx, sy)]]
    return ["PASS"]


def _water_due(pl, day):
    if pl["watered"]:
        return False
    cd = CROPS[pl["crop"]]
    age = day - pl["planted"]
    if cd["ongoing"]:
        prod_today = (age + 1 >= cd["first_yield_day"]
                      and (age + 1 - cd["first_yield_day"]) % cd["interval"] == 0)
        return pl["cuw"] >= 1 or prod_today
    ws = (cd["max_yield_day"] + 1) // 2
    return pl["cuw"] >= 1 or (ws <= age <= cd["max_yield_day"])


def _water_prod_day(pl, day):
    cd = CROPS[pl["crop"]]
    if not cd["ongoing"]:
        return False
    age = day - pl["planted"]
    return (age + 1 >= cd["first_yield_day"]
            and (age + 1 - cd["first_yield_day"]) % cd["interval"] == 0)


def _harvest_ready(pl, day):
    cd = CROPS[pl["crop"]]
    age = day - pl["planted"]
    if age < cd["first_yield_day"]:
        return False
    if cd["ongoing"]:
        return pl["yield"] >= 2
    return pl["yield"] >= cd["max_yield"] or age >= cd["max_yield_day"]


def _fert_due(pl, day):
    if pl["crop"] not in ("MELON", "STRAWBERRY"):
        return False
    if pl["fert"] >= day:
        return False
    cd = CROPS[pl["crop"]]
    age = day - pl["planted"]
    if cd["ongoing"]:
        return age <= 16
    ws = (cd["max_yield_day"] + 1) // 2
    return ws - 2 <= age <= cd["max_yield_day"]


def _animal_harvest_ready(a):
    return a["yield"] >= (2 if a["kind"] == "GOOSE" else 3)


def _sow_crop(S, targets, pos, plant_budget=None):
    # standing counts by crop
    counts = {}
    for pl in S["plants"]:
        counts[pl["crop"]] = counts.get(pl["crop"], 0) + 1
    if plant_budget is not None:
        for c in list(counts):
            counts[c] += (S["seeds"].get(c, 0) - plant_budget.get(c, 0)) * 0  # placeholder
    best = None
    for crop in ("STRAWBERRY", "MELON", "TOMATO", "WHEAT", "CARROT"):
        avail = S["seeds"].get(crop, 0) if plant_budget is None else plant_budget.get(crop, 0)
        if avail <= 0:
            continue
        if counts.get(crop, 0) >= targets.get(crop, 0):
            continue
        # sow windows (last profitable sow day)
        if crop == "STRAWBERRY" and S["day"] > 19:
            continue
        if crop == "TOMATO" and (S["day"] < 8 or S["day"] > 21):
            continue
        if crop == "MELON" and S["day"] > 22:
            continue
        if crop == "CARROT" and S["day"] > 26:
            continue
        # prefer tiles near the shed (short future walks)
        best = crop
        break
    return best


def hourly_actions(obs, p, st):
    day = int(obs.get("day", 0))
    hour = int(obs.get("hour", 0))
    S = parse_state(obs, p)
    targets = st["targets"]
    farm = obs["farms"][p]
    poss = [tuple(farm["farmer"])] + [tuple(h) for h in (farm.get("hands") or [])]
    invs = (obs.get("private", {}) or {}).get("inventories", []) or []
    tile = {}
    for pl in S["plants"]:
        tile[pl["pos"]] = ("P", pl)
    for a in S["animals"]:
        tile[a["pos"]] = ("A", a)
    for s in S["structures"]:
        tile.setdefault(s["pos"], ("S", s))
    for w in S["weeds"]:
        tile.setdefault(w, ("W", None))
    for e in S["empties"]:
        tile.setdefault(e, ("E", None))

    claims = set()
    # sticky in-transit targets count as claimed — no dogpiling on one tile
    for tk in (st.get("tasks") or {}).values():
        if tk and len(tk) >= 2 and tk[1] not in ("drop", "fetch_wheat", "pickup_animal"):
            claims.add(tuple(tk[0]))
    # engine rule: if total PLANT demand for a crop this turn exceeds seeds,
    # ALL of that crop's PLANTs are dropped. Track a strict per-hour budget.
    plant_budget = {c: max(0, int(S["seeds"].get(c, 0))) for c in CROPS}
    # feed-room: only enough wheat leaves the shed as there are unfed animals,
    # counting wheat already carried. Stops the pickup/drop shuffle.
    total_unfed = sum(1 for a in S["animals"] if not a["fed"])
    wheat_carried = sum(int(inv.get("WHEAT", 0)) for inv in invs if isinstance(inv, dict))
    feed_room = total_unfed - wheat_carried
    tasks = st.setdefault("tasks", {})
    acts = []
    for i, u in enumerate(poss):
        inv = dict(invs[i]) if i < len(invs) else {}
        acts.append(unit_decide(i, u, inv, S, tile, targets, claims, hour, day,
                                plant_budget, feed_room, tasks))
    return acts


def unit_decide(i, u, inv, S, tile, targets, claims, h, day, plant_budget,
                feed_room=0, tasks=None):
    if tasks is None:
        tasks = {}
    owned = S["owned"]
    inv_n = sum(v for v in inv.values() if isinstance(v, (int, float)))
    shed = S["shed"]
    wheat = inv.get("WHEAT", 0)
    fert = inv.get("FERTILIZER", 0)
    carrying_animal = any(inv.get(k, 0) >= 1 for k in ("COW", "SHEEP", "GOOSE"))
    unfed_any = any(not a["fed"] for a in S["animals"])
    sellables = {k: v for k, v in inv.items()
                 if k not in ("COW", "SHEEP", "GOOSE") and (k != "WHEAT" or not unfed_any)}
    sell_n = sum(sellables.values())

    def clear():
        tasks.pop(i, None)

    # ---------- 1) act on the tile we actually stand on ----------
    if u in tile:
        kind, obj = tile[u]
        if kind == "A" and obj:
            if not obj["fed"] and wheat >= 1:
                return ["FEED"]
            if not obj["cared"]:
                return ["CARE"]
            if not obj["collected"]:
                return ["COLLECT_FERTILIZER"]
            if _animal_harvest_ready(obj):
                return ["HARVEST"]
        elif kind == "P" and obj:
            if _harvest_ready(obj, day):
                return ["HARVEST"]
            if _water_due(obj, day):
                return ["WATER"]
            if _fert_due(obj, day) and fert >= 1:
                return ["FERTILIZE"]
        elif kind == "E":
            if u not in SHED_TILES:
                for k in ("COW", "SHEEP", "GOOSE"):
                    if inv.get(k, 0) >= 1 and not _free_struct(S, k):
                        return ["BUILD_" + ANIMALS[k]["structure"]]
            crop = _sow_crop(S, targets, u, plant_budget)
            if crop:
                plant_budget[crop] -= 1
                clear()
                return ["PLANT", crop]
        elif kind == "S" and obj:
            for k in ("COW", "SHEEP", "GOOSE"):
                if inv.get(k, 0) >= 1 and ANIMALS[k]["structure"] == obj["kind"]:
                    clear()
                    return ["PLACE", k]
        elif kind == "W":
            clear()
            return ["DIG"]

    # shed-adjacent logistics (position ops, checked every hour we stand here)
    if u in SHED_TILES:
        if sell_n >= 1:
            return ["DROP"]
        if not carrying_animal:
            buildable = [e for e in S["empties"] if e not in SHED_TILES]
            for k in ("COW", "SHEEP", "GOOSE"):
                if shed.get(k, 0) > 0 and (_free_struct(S, k) or buildable):
                    return ["PICKUP", k, 1]
        if h >= 20 and inv_n > 0 and not carrying_animal:
            return ["DROP"]
        if feed_room > 0 and wheat < 1 and shed.get("WHEAT", 0) > 0:
            take = min(feed_room, 4, shed.get("WHEAT", 0))
            return ["PICKUP", "WHEAT", take]

    # farmer must not move at h0 (spawn-tile rule)
    if i == 0 and h == 0:
        return ["PASS"]

    # ---------- 2) sticky task: keep walking / acting until done ----------
    def _tk_valid(tk):
        pos, why, age = tk
        if age > 10:
            return False
        kind, obj = tile.get(pos, (None, None))
        if why in ("drop", "fetch_wheat", "pickup_animal"):
            if pos not in SHED_TILES:
                return False
            if why == "drop":
                return sell_n >= 2 or (h >= 21 and sell_n >= 1)
            if why == "fetch_wheat":
                return wheat < 1 and feed_room > 0 and shed.get("WHEAT", 0) > 0
            if why == "pickup_animal":
                if carrying_animal:
                    return False
                return any(shed.get(k, 0) > 0 and (_free_struct(S, k) or
                            [e for e in S["empties"] if e not in SHED_TILES])
                           for k in ("COW", "SHEEP", "GOOSE"))
        if why == "feed":
            return kind == "A" and obj is not None and not obj["fed"]
        if why == "care":
            return (kind == "A" and obj is not None and
                    (not obj["cared"] or not obj["collected"] or _animal_harvest_ready(obj)))
        if why == "water":
            return kind == "P" and obj is not None and _water_due(obj, day)
        if why == "fert":
            return (kind == "P" and obj is not None and _fert_due(obj, day) and
                    (fert >= 1 or shed.get("FERTILIZER", 0) > 0))
        if why == "harvest":
            if kind == "A" and obj is not None:
                return _animal_harvest_ready(obj)
            return kind == "P" and obj is not None and _harvest_ready(obj, day)
        if why == "plant":
            crop = _sow_crop(S, targets, pos, plant_budget)
            return kind == "E" and crop is not None
        if why == "weed":
            return kind == "W"
        if why == "build":
            return (carrying_animal and pos not in SHED_TILES and kind == "E")
        if why == "place":
            if not carrying_animal:
                return False
            for k in ("COW", "SHEEP", "GOOSE"):
                if inv.get(k, 0) >= 1 and ANIMALS[k]["structure"] == obj.get("kind") \
                        and kind == "S":
                    return True
            return False
        return False

    tk = tasks.get(i)
    if tk is not None:
        if _tk_valid(tk):
            pos = tk[0]
            tk[2] += 1
            if _d(u, pos) <= 0:
                return ["PASS"]  # stand & the on-tile branch will act next parse
            return _walk_step(u, pos, owned)
        clear()

    # ---------- 3) pick the best task within reach, claim it, save it ----------
    st_tile = min(SHED_TILES, key=lambda t: _d(u, t))
    cands = []   # (priority, pos, why)
    if sell_n >= 2 or (h >= 21 and sell_n >= 1):
        cands.append((85 - _d(u, st_tile) * 2, st_tile, "drop"))
    if wheat < 1 and feed_room > 0 and shed.get("WHEAT", 0) > 0:
        cands.append((85 - _d(u, st_tile) * 2, st_tile, "fetch_wheat"))
    for a in S["animals"]:
        pos = a["pos"]
        if pos in claims:
            continue
        if not a["fed"] and (wheat >= 1 or (feed_room > 0 and shed.get("WHEAT", 0) > 0)):
            cands.append((100 - _d(u, pos), pos, "feed"))
        elif not a["cared"] or not a["collected"] or _animal_harvest_ready(a):
            cands.append((78 - _d(u, pos), pos, "care"))
    for pl in S["plants"]:
        pos = pl["pos"]
        if pos in claims:
            continue
        if _harvest_ready(pl, day):
            # rot-watch: non-ongoing past window loses yield every 2h
            age = day - pl["planted"]
            urgent = (not CROPS[pl["crop"]]["ongoing"]) and age >= CROPS[pl["crop"]]["max_yield_day"]
            cands.append(((85 if urgent else 75) - _d(u, pos) * 2, pos, "harvest"))
        elif _water_due(pl, day):
            # war cadence: survival water every other day (cuw>=1 = dies
            # tonight if missed) + production days (watered = +yield bonus).
            # Daily luxury watering does not scale to a full 4-quad farm.
            if pl.get("cuw", 0) >= 1:
                cands.append((96 - _d(u, pos) * 2, pos, "water"))
            elif _water_prod_day(pl, day):
                cands.append((80 - _d(u, pos) * 2, pos, "water"))
        elif _fert_due(pl, day) and (fert >= 1 or shed.get("FERTILIZER", 0) > 0):
            cands.append((55 - _d(u, pos) * 2, pos, "fert"))
    for e in S["empties"]:
        if e in claims:
            continue
        crop = _sow_crop(S, targets, e, plant_budget)
        if crop and _d(u, e) <= 18:
            cands.append((64 - _d(u, e) * 2, e, "plant"))
    weed_pri = 45 + min(15, 2 * len(S["weeds"]))
    for w in S["weeds"]:
        if w not in claims:
            cands.append((weed_pri - _d(u, w) * 2, w, "weed"))
    if carrying_animal:
        placed = False
        for k in ("COW", "SHEEP", "GOOSE"):
            if inv.get(k, 0) >= 1:
                fs = _free_struct(S, k)
                if fs and fs not in claims:
                    cands.append((78 - _d(u, fs) * 2, fs, "place"))
                    placed = True
                    break
        if not placed:
            build_sites = [e for e in S["empties"] if e not in claims and e not in SHED_TILES]
            if build_sites:
                site = min(build_sites, key=lambda e: _d(u, e))
                cands.append((72 - _d(u, site) * 2, site, "build"))
    if not carrying_animal:
        for k in ("COW", "SHEEP", "GOOSE"):
            if shed.get(k, 0) > 0 and (_free_struct(S, k) or
                                        [e for e in S["empties"] if e not in SHED_TILES]):
                cands.append((65 - _d(u, st_tile), st_tile, "pickup_animal"))
                break

    if not cands:
        if S["plants"]:
            cx = sum(pl["pos"][0] for pl in S["plants"]) // len(S["plants"])
            cy = sum(pl["pos"][1] for pl in S["plants"]) // len(S["plants"])
            return _walk_step(u, (cx, cy), owned)
        return ["PASS"]
    cands.sort(reverse=True)
    _, best, why = cands[0]
    claims.add(best)
    tasks[i] = [best, why, 0]
    if _d(u, best) <= 0:
        return ["PASS"]
    return _walk_step(u, best, owned)


def _free_struct(S, kind):
    want = ANIMALS[kind]["structure"]
    taken = [a["pos"] for a in S["animals"]]
    for s in S["structures"]:
        if s["kind"] == want and s["pos"] not in taken:
            return s["pos"]
    return None


_SESSIONS = {}


def agent(obs, config=None):
    p = int(obs["player"])
    step = int(obs.get("step", 0))
    day, hour = step // 24, step % 24
    st = _SESSIONS.setdefault(p, {})
    if st.get("day") != day or hour == 0:
        S = parse_state(obs, p)
        obh, proj = plan_market(S, day)
        st.update({"day": day, "obh": obh, "targets": proj.get("targets", {})})
        st["tasks"] = {}   # hands respawn at EOD; unit indices reset
    plan = st["obh"]
    mkt = list(plan.get(hour, []))[:10] if hour < len(plan) or hour in plan else []
    if not mkt and hour >= 1:
        # hourly standing sells: repeat the morning sell list all day
        # (EOD auto-dump means yesterday's harvests are in the shed at h0;
        #  intraday DROPs convert when the list repeats. NO hourly dumping —
        #  MELON/STRB/MILK/WOOL prices cliff hard once inventory passes I0.
        #  NEVER clobber the plan's own hourly buy orders.)
        sells = [o for o in (plan.get(0) or []) if o and o[0] == "SELL"]
        if sells:
            mkt = sells[:10]
    acts = hourly_actions(obs, p, st)
    farm = obs["farms"][p]
    n_now = 1 + len(farm.get("hands") or [])
    farmer = acts[0] if acts else ["PASS"]
    hands = [acts[i] if i < len(acts) else ["PASS"] for i in range(1, n_now)]
    return {"farmer": farmer, "hands": hands, "market": mkt}


kaggle_entry_agent = agent
