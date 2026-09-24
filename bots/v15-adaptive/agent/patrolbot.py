"""
HI_AgriBot v9.5 "Pathfinder"
================================
Kaggriculture agent. Utility job-board architecture: every turn a central
planner enumerates ALL jobs on the farm, scores them by economic urgency,
and assigns each to exactly one worker (no converging, no double-waters).

Strategy (decoded from the $139k-$141k top replays, episodes 90615567 and
90697169, pulled 2026-08-08):
  * Build-A skeleton: 3 quadrants (NE day 7, SW day 11), 8 cows + 6 sheep,
    day-0 opening identical to THUNDER/sleepyai/venks.
  * CARE on every animal every day: fed+cared cows give 2 milk/2d, sheep
    3 wool/3d — CARE doubles animal output. This is the top bots' engine.
  * Fertilizer engine: every unit collected daily and SOLD the same day
    (never stockpiled); a slice is diverted onto MELONS (+2 melons ~= $500
    of value for the $100 input) while melons are in their bonus window.
  * Wheat ring: wheat planted on shed-adjacent tiles so feed hauls are
    short; we aim to be a net wheat seller (THUNDER's $127k edge).
  * Full plot fill: plant on EVERY empty unlocked tile until day 25.
  * Market brain: exact replication of the price curve; sale batch sizes
    scale with current price vs base; late-game unconditional dump.
  * Safety invariants: animals never starve (emergency feed mode), plants
    never dry out (water before plant), feed wheat is never sold, land
    buys retry every hour, sells always appended last (never dropped by
    the 10-order cap), full cash-out by turn 720.

Single file, no external deps, no file reads (Kaggle sandbox safe).
"""

VERSION = "HI_AgriBot_v12.0_Patrol"

import math

# --------------------------------------------------------------------------
# Static game data (from the official rules tables)
# --------------------------------------------------------------------------
BOARD = 10
HALF = BOARD // 2
SHED_TILES = [(HALF - 1, HALF - 1), (HALF, HALF - 1), (HALF - 1, HALF), (HALF, HALF)]
SHED_SET = set(SHED_TILES)

QUAD_TILES = {
    "NW": [(x, y) for y in range(0, HALF) for x in range(0, HALF)],
    "NE": [(x, y) for y in range(0, HALF) for x in range(HALF, BOARD)],
    "SW": [(x, y) for y in range(HALF, BOARD) for x in range(0, HALF)],
    "SE": [(x, y) for y in range(HALF, BOARD) for x in range(HALF, BOARD)],
}

SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
BASE_PRICE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
              "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}
ANIMAL_COST = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
ANIMAL_STRUCT = {"COW": "PASTURE", "SHEEP": "PASTURE", "GOOSE": "COOP"}

SHOPS = {"BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
         "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"], "YARN_STORE": ["WOOL"],
         "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
         "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
         "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]}
FIRST_YIELD_DAY = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}
# Last day it is worth PLANTING each crop (so it pays before season end).
PLANT_UNTIL = {"WHEAT": 22, "CARROT": 24, "TOMATO": 17, "STRAWBERRY": 16, "MELON": 13}
# One-time crops: harvest target age (peak yield with daily watering).
PEAK_AGE = {"WHEAT": 4, "CARROT": 3, "MELON": 10}

# Market price model (exact replication of the env's price function) so we
# can forecast revenue of a sale batch before issuing it.
MARKET_MODEL = {
    #           base    T   below_func below_tgt above_func above_tgt
    "WHEAT":      (25, 400, "sqrt",    0.80,     "log",     0.20),
    "CARROT":     (35, 450, "log",     0.20,     "sqrt",    0.70),
    "TOMATO":     (60, 200, "linear",  0.40,     "sqrt",    0.60),
    "STRAWBERRY": (120, 100, "sqrt",   0.70,     "linear",  1.60),
    "MELON":      (250, 300, "log",    0.20,     "sq",      3.60),
    "EGG":        (50, 332, "linear",  0.40,     "log",     0.20),
    "MILK":       (160, 122, "sqrt",   0.60,     "linear",  1.60),
    "WOOL":       (200, 105, "log",    0.20,     "sq",      3.20),
    "FERTILIZER": (100, 200, "linear", 0.40,     "linear",  0.40),
}
I0 = 10000

FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]

# Pasture corridor: compact rows near the shed so one tender sweep feeds 6.
PASTURE_LAYOUT = [
    # NW block (days 0-1): 6 spots, rows 3-4 cols 1-4 (never on shed tiles)
    (3, 4), (4, 3), (3, 3), (2, 4), (2, 3), (1, 4),
    # NE: four closest non-shed tiles (max shed distance 2)
    (5, 3), (6, 4), (6, 3), (5, 2),
    # SW: four closest non-shed tiles (max shed distance 2)
    (3, 5), (4, 6), (2, 5), (3, 6),
]

CONFIG = {
    "target_cows": 8,
    "target_sheep": 6,
    "buy_ne_day": 7,
    "buy_sw_day": 10,   # optimizer r4: SW a day earlier = +$700
    "animal_buy_last_day_cow": 13,
    "animal_buy_last_day_sheep": 11,
    "feed_reserve_base": 6,          # shed wheat >= animals*1 + this (never sold)
    "feed_reserve_cap": 40,
    "shed_soft_cap": 88,             # pause harvesting above this until sells free room
    "fertilizer_for_melons": 14,     # units diverted onto melons over the season
    "fertilizer_for_strawberries": 30,  # doubles 2 ticks each ~ +$600 per fert
}

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _tile(farm, x, y):
    try:
        return farm["tiles"][y][x]
    except Exception:
        return "LOCKED"


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


CURRENT_FARM = [None]  # set each turn; used for locked-tile avoidance


def _is_locked(p):
    farm = CURRENT_FARM[0]
    if farm is None:
        return False
    try:
        return farm["tiles"][p[1]][p[0]] == "LOCKED"
    except Exception:
        return True


def _move_toward(pos, target):
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    if dx == 0 and dy == 0:
        return ["PASS"]
    horiz = ["EAST"] if dx > 0 else ["WEST"]
    vert = ["SOUTH"] if dy > 0 else ["NORTH"]
    h_next = (pos[0] + (1 if dx > 0 else -1), pos[1])
    v_next = (pos[0], pos[1] + (1 if dy > 0 else -1))
    h_locked = _is_locked(h_next)
    v_locked = _is_locked(v_next)
    if dx == 0:
        return vert
    if dy == 0:
        return horiz
    # prefer the axis that stays on unlocked ground; break ties by parity
    if h_locked and not v_locked:
        return vert
    if v_locked and not h_locked:
        return horiz
    if abs(dx) > abs(dy) or (abs(dx) == abs(dy) and (pos[0] + pos[1]) % 2 == 0):
        return horiz
    return vert


def _nearest(pos, targets):
    best, bd = None, 10 ** 9
    for t in targets:
        d = abs(t[0] - pos[0]) + abs(t[1] - pos[1])
        if d < bd:
            best, bd = t, d
    return best, bd


ROUTE_CACHE = {}


def _local_to_global(q, lx, ly):
    h = HALF
    if q == "NW":
        return (h - 1 - lx, h - 1 - ly)
    if q == "NE":
        return (h + lx, h - 1 - ly)
    if q == "SW":
        return (h - 1 - lx, h + ly)
    return (h + lx, h + ly)


def quad_route(q):
    if q not in ROUTE_CACHE:
        pts = []
        for c in range(HALF):
            rows = range(HALF) if c % 2 == 0 else range(HALF - 1, -1, -1)
            for r in rows:
                pts.append(_local_to_global(q, c, r))
        ROUTE_CACHE[q] = pts
    return ROUTE_CACHE[q]


def _shed_dist(pos):
    return min(_manhattan(pos, s) for s in SHED_TILES)


def _quad_of(x, y):
    if x < HALF:
        return "NW" if y < HALF else "SW"
    return "NE" if y < HALF else "SE"


def _unlocked(farm):
    return set(farm.get("unlocked_quadrants") or ["NW"])


def _owned_tiles(farm):
    u = _unlocked(farm)
    for q in ("NW", "NE", "SW", "SE"):
        if q in u:
            for p in QUAD_TILES[q]:
                yield p


def _f(x):  # shape functions
    import math
    return x


def price_at(item, inv):
    """Exact env price function. Used to forecast sale revenue."""
    import math
    base, T, bf, bt, af, at = MARKET_MODEL[item]

    def shape(fn, v):
        if fn == "linear":
            return v
        if fn == "sq":
            return v * v
        if fn == "sqrt":
            return math.sqrt(v)
        if fn == "log":
            return math.log(1 + v)
        return math.log10(1 + v)

    d = inv - I0
    if d == 0:
        return base
    if d < 0:
        amp = bt * base / max(shape(bf, T), 1e-9)
        p = base + amp * shape(bf, -d)
    else:
        amp = at * base / max(shape(af, T), 1e-9)
        p = base - amp * shape(af, d)
    return max(1, int(round(p)))


def batch_revenue(item, inv, n):
    """Expected revenue of selling n units starting at inventory inv."""
    total = 0
    for _ in range(int(n)):
        total += price_at(item, inv)
        inv += 1
    return total


# --------------------------------------------------------------------------
# Persistent memory (module level; Kaggle reuses the process across turns)
# --------------------------------------------------------------------------
MEM = {
    "fert_spent_on_melons": 0,
    "fert_spent_on_straw": 0,
    "last_inv": {},
    "opp_animals": 0,
    "opp_crops": 0,
    "wheat_bought": 0,
    "wheat_sold": 0,
}

# --------------------------------------------------------------------------
# Market planner
# --------------------------------------------------------------------------

def _animal_counts(farm, shed, inventories=None):
    cows = sheep = geese = 0
    for inv in (inventories or []):
        cows += (inv or {}).get("COW", 0)
        sheep += (inv or {}).get("SHEEP", 0)
        geese += (inv or {}).get("GOOSE", 0)
    for row in farm.get("tiles", []):
        for t in row:
            if isinstance(t, dict) and t.get("animal"):
                a = t["animal"]
                if a == "COW":
                    cows += 1
                elif a == "SHEEP":
                    sheep += 1
                elif a == "GOOSE":
                    geese += 1
    cows += shed.get("COW", 0)
    sheep += shed.get("SHEEP", 0)
    geese += shed.get("GOOSE", 0)
    return cows, sheep, geese


def _count_animals_on_farm(farm):
    n = 0
    for row in farm.get("tiles", []):
        for t in row:
            if isinstance(t, dict) and t.get("animal"):
                n += 1
    return n


def _empty_pastures(farm):
    out = []
    for row_i, row in enumerate(farm.get("tiles", [])):
        for col_i, t in enumerate(row):
            if isinstance(t, dict) and t.get("kind") == "PASTURE" and not t.get("animal"):
                out.append((col_i, row_i))
    return out


def unbuilt_pasture_slots(farm, unlocked):
    n = 0
    for (x, y) in PASTURE_LAYOUT:
        if _quad_of(x, y) in unlocked and _tile(farm, x, y) is None:
            n += 1
    return n


def _crop_counts(farm):
    c = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0}
    for row in farm.get("tiles", []):
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                c[t.get("crop")] = c.get(t.get("crop"), 0) + 1
    return c


def plan_market(obs, farm, private, jobs_ctx):
    day = obs.get("day", 0)
    hour = obs.get("hour", 0)
    cash = float(farm.get("money", 0) or 0)
    seeds = private.get("seeds", {}) or {}
    shed = private.get("shed", {}) or {}
    market_obs = obs.get("market", {}) or {}
    prices = market_obs.get("prices", {}) or {}
    inv = market_obs.get("inventory", {}) or {}
    unlocked = _unlocked(farm)
    final_day = day >= 29

    orders = []
    sells = []
    # Projected cash: fertilizer in the shed WILL sell this turn (or next);
    # the early game runs on this float exactly like the top replays do.
    proj = cash + min(shed.get("FERTILIZER", 0), 14) * 90

    if day == 0 and hour == 0:
        return []

    # ---------------- Day 0 opening (exact top-meta order set) -------------
    if day == 0 and hour == 1:
        orders.append(["HIRE"])
        orders.append(["HIRE"])
        orders.append(["HIRE"])
        orders.append(["HIRE"])
        orders.append(["HIRE"])
        orders.append(["BUY_ANIMAL", "COW", 2])
        orders.append(["BUY_ANIMAL", "SHEEP", 2])
        orders.append(["BUY_SEED", "WHEAT", 7])
        orders.append(["BUY_SEED", "MELON", 12])
        orders.append(["BUY_PRODUCT", "WHEAT", 5])
        return orders

    # ---------------- Land: retry every hour from target day ---------------
    if "NE" not in unlocked and day >= CONFIG["buy_ne_day"] and cash >= 1000 + 300:
        orders.append(["BUY_LAND"])
        cash -= 1000
    if "SW" not in unlocked and day >= CONFIG["buy_sw_day"] and "NE" in unlocked \
            and cash >= 2000 + 400:
        orders.append(["BUY_LAND"])
        cash -= 2000


    # ---------------- Hires (right after land so land never starves) -------
    if not final_day:
        if day <= 2:
            want = 6
        elif day <= 6:
            want = 8
        elif day <= 11:
            want = 13   # optimizer r0/r3: +1 mid-game hand pays +$3.3k
        elif day <= 20:
            want = 12
        elif day <= 26:
            want = 12   # optimizer r3: keep the crew through the strawberry sell
        else:
            want = 8
        if proj < 120:
            want = min(want, 2)
        elif proj < 400:
            want = min(want, 4)
        elif proj < 900:
            want = min(want, 7)
        committed = farm.get("hires_today", 0) or 0
        added = 0
        while committed + added < want and (committed + added) < len(FIB) and len(orders) < 8:
            cost = FIB[committed + added]
            if cash < cost + 20 and proj < cost + 60:
                break
            orders.append(["HIRE"])
            cash -= cost
            proj -= cost
            added += 1

    # ---------------- Animals: ramp toward targets with payback gates ------
    cows, sheep, geese = _animal_counts(farm, shed, private.get("inventories"))
    empty_past = len(_empty_pastures(farm))
    # planned-but-unbuilt pasture spots still affordable to build
    unbuilt = sum(1 for (x, y) in PASTURE_LAYOUT
                  if _quad_of(x, y) in unlocked and _tile(farm, x, y) is None)
    housing = empty_past + unbuilt

    def ramp_buy(kind, have, target, last_day, price_key, floor_price):
        nonlocal cash, housing
        if day > last_day or have >= target or housing <= 0:
            return
        if prices.get(price_key, BASE_PRICE[price_key]) < floor_price:
            return
        cost = ANIMAL_COST[kind]
        if cash >= cost + 200 and proj >= cost + 450 and len(orders) < 9:
            orders.append(["BUY_ANIMAL", kind, 1])
            cash -= cost
            housing -= 1

    ramp_buy("COW", cows, CONFIG["target_cows"], CONFIG["animal_buy_last_day_cow"], "MILK", 50)
    ramp_buy("SHEEP", sheep, CONFIG["target_sheep"], CONFIG["animal_buy_last_day_sheep"], "WOOL", 50)

    # ---------------- Seeds: just-in-time buffers --------------------------
    if not final_day and hour in (1, 8, 14) and len(orders) < 9:
        crops = _crop_counts(farm)
        # Wheat: the feed engine. Keep the seed bank deep through day 24 so
        # lanes never sit empty after a harvest (top bots buy ~110 wheat seed).
        if day <= 24 and seeds.get("WHEAT", 0) < 14 and proj >= 200:
            n = min(14 - seeds.get("WHEAT", 0), 10)
            orders.append(["BUY_SEED", "WHEAT", n])
            cash -= 10 * n
            proj -= 10 * n
        # Strawberry: the $153k builds (Ryan Shan / THUNDER lineage) buy
        # BIG batches right at the land unlocks — 19 on day 7, 23 on day 11 —
        # so every plant fires all 4 ticks (days 17-27). Strawberries are
        # the highest-value crop per tile when planted on schedule.
        sb = seeds.get("STRAWBERRY", 0) + _crop_counts(farm).get("STRAWBERRY", 0)
        # Our cash curve peaks a bit later than the $150k builds, so we buy
        # the strawberry waves days 8-13 (ticks 18-28 still all fire).
        if 8 <= day <= 10 and seeds.get("STRAWBERRY", 0) < 12 and proj >= 1300:
            n = min(12 - seeds.get("STRAWBERRY", 0), int((proj - 1100) // 100), 6)
            if n > 0:
                orders.append(["BUY_SEED", "STRAWBERRY", n])
                cash -= 100 * n
                proj -= 100 * n
        if 11 <= day <= 16 and sb < 44 and seeds.get("STRAWBERRY", 0) < 14 and proj >= 1500:
            n = min(14 - seeds.get("STRAWBERRY", 0), int((proj - 1300) // 100), 7)
            if n > 0:
                orders.append(["BUY_SEED", "STRAWBERRY", n])
                cash -= 100 * n
                proj -= 100 * n
        # Melon wave 1 (day 0 handled) + wave 2 once new land opens.
        if 7 <= day <= 16 and crops.get("MELON", 0) + seeds.get("MELON", 0) < 16 \
                and seeds.get("MELON", 0) < 8 and proj >= 800:
            n = min(8 - seeds.get("MELON", 0), 5)
            orders.append(["BUY_SEED", "MELON", n])
            cash -= 80 * n
            proj -= 80 * n
        # Late tomato wave: price climbs all month ($71 -> $95), ongoing crop
        # planted d12-17 ticks d20-28. Steady endgame filler.
        if 12 <= day <= 17 and seeds.get("TOMATO", 0) < 8 \
                and _crop_counts(farm).get("TOMATO", 0) + seeds.get("TOMATO", 0) < 12 \
                and proj >= 900:
            nt = min(8 - seeds.get("TOMATO", 0), 4)
            orders.append(["BUY_SEED", "TOMATO", nt])
            cash -= 50 * nt
            proj -= 50 * nt
        # Tomato mid-game bridge on the daily-yield curve.
        if 4 <= day <= 10 and seeds.get("TOMATO", 0) < 4 and crops.get("TOMATO", 0) < 8 \
                and proj >= 700:
            orders.append(["BUY_SEED", "TOMATO", min(4 - seeds.get("TOMATO", 0), 4)])
            cash -= 50 * min(4 - seeds.get("TOMATO", 0), 4)
            proj -= 50 * min(4 - seeds.get("TOMATO", 0), 4)

    # ---------------- Feed wheat: buy shortfall against the reserve --------
    animals = _count_animals_on_farm(farm)
    wheat = shed.get("WHEAT", 0) + jobs_ctx.get("wheat_in_transit", 0)
    reserve = min(CONFIG["feed_reserve_base"] + animals, CONFIG["feed_reserve_cap"])
    if day >= 28:
        reserve = 0  # escapes never process after turn 720; sell the wheat
    if not final_day and animals > 0:
        shortfall = reserve - wheat
        wp = prices.get("WHEAT", 25)
        if hour == 1 and shortfall > 0 and proj >= wp * 4 + 40:
            n = min(max(shortfall, 4), 14, max(1, int((proj - 40) // wp)))
            orders.append(["BUY_PRODUCT", "WHEAT", n])
            cash -= wp * n
            proj -= wp * n
            MEM["wheat_bought"] += n
        elif jobs_ctx.get("unfed_urgent", 0) > 0 and wheat < animals and proj >= wp * 2 + 30:
            n = min(6, animals - wheat + 2, max(1, int((proj - 30) // wp)))
            orders.append(["BUY_PRODUCT", "WHEAT", n])
            cash -= wp * n
            proj -= wp * n
            MEM["wheat_bought"] += n

    # ---------------- Opportunistic fertilizer buy for melons --------------
    melons_young = jobs_ctx.get("melons_unfertilized", 0)
    fert_price = prices.get("FERTILIZER", 100)
    if (not final_day and day <= 15 and melons_young >= 3
            and fert_price <= 80 and cash >= 1200
            and MEM["fert_spent_on_melons"] < CONFIG["fertilizer_for_melons"]):
        n = min(4, melons_young)
        if len(orders) < 9:
            orders.append(["BUY_PRODUCT", "FERTILIZER", n])
            cash -= fert_price * n

    # ---------------- Sells: price-aware pacing, appended LAST -------------
    def sell_all(item):
        n = shed.get(item, 0)
        if n > 0:
            sells.append(["SELL", item, n])

    if day >= 27:
        for item in ("MILK", "WOOL", "EGG", "MELON", "STRAWBERRY", "TOMATO",
                     "CARROT", "FERTILIZER", "WHEAT"):
            sell_all(item)
    elif day >= 11 and shed.get("MELON", 0) > 0:
        sell_all("MELON")  # RR blueprint: melons sell on harvest day ~$240
    else:
        # Fertilizer: sell every unit, every day (mandate). Split big holds.
        f_hold = shed.get("FERTILIZER", 0)
        if f_hold > 0:
            if f_hold <= 14:
                sells.append(["SELL", "FERTILIZER", f_hold])
            else:
                sells.append(["SELL", "FERTILIZER", 14])
                sells.append(["SELL", "FERTILIZER", f_hold - 14])
        # strawberry program: buy fert JUST-IN-TIME mid-game (price has
        # crashed by then) — never hold fert early, that kills the ramp
        program_need = min(10, jobs_ctx.get("straw_fert_want", 0))
        fp = prices.get("FERTILIZER", 100)
        if 15 <= day <= 23 and hour in (1, 8, 14) and program_need > f_hold \
                and fp <= 160 and cash >= fp * 6 + 300 and len(orders) < 8:
            nb = min(program_need - f_hold, 6)
            orders.append(["BUY_PRODUCT", "FERTILIZER", nb])
            cash -= fp * nb
            proj -= fp * nb

        inv_map = (obs.get("market", {}) or {}).get("inventory", {}) or {}
        opp_animal_heavy = MEM.get("opp_animals", 0) >= 10
        opp_crop_heavy = MEM.get("opp_crops", 0) >= 30

        # ATTACK MODE: dump a product when the opponent is lopsided on it
        # and our exposure is small (their payday crashes, ours barely moves)
        own_crops_now = _crop_counts(farm)
        own_cows, own_sheep, own_geese = _animal_counts(farm, shed,
                                                        private.get("inventories"))
        attack = {}
        if MEM.get("opp_cows", 0) >= 8 and MEM.get("opp_cows", 0) >= 2 * max(1, own_cows):
            attack["MILK"] = True
        if MEM.get("opp_sheep", 0) >= 8 and MEM.get("opp_sheep", 0) >= 2 * max(1, own_sheep):
            attack["WOOL"] = True
        if 12 <= day <= 24 and MEM.get("opp_straw", 0) >= 12 \
                and MEM.get("opp_straw", 0) >= 2 * max(1, own_crops_now.get("STRAWBERRY", 0)):
            attack["STRAWBERRY"] = True
        if 15 <= day <= 24 and MEM.get("opp_melon", 0) >= 8 \
                and MEM.get("opp_melon", 0) >= 2 * max(1, own_crops_now.get("MELON", 0)):
            attack["MELON"] = True

        # TOWN SUPPORT: shops consume products every 4 turns, propping prices
        town_boost = {}
        try:
            for shop in (obs.get("town", {}) or {}).get("unlocked_shops", []) or []:
                for prod in SHOPS.get(shop, []):
                    town_boost[prod] = town_boost.get(prod, 0) + 1
        except Exception:
            pass

        def momentum(item):
            h = MEM.get("price_hist", {}).get(item) or []
            if len(h) < 24:
                return 0.0
            return (h[-1] - h[-24]) / float(max(h[-24], 1))

        def paced(item, base):
            n = shed.get(item, 0)
            if n <= 0:
                return
            p = prices.get(item, base)
            ratio = p / float(base)
            inv = inv_map.get(item, I0)
            mom = momentum(item)
            # opponent build shifts how fast their dumps will crash our goods
            opp_pressure = ((item in ("MILK", "WOOL", "EGG") and opp_animal_heavy)
                            or (item in ("STRAWBERRY", "MELON", "TOMATO")
                                and opp_crop_heavy))
            sell_at = 0.65 if opp_pressure else 0.8
            half_at = 0.42 if opp_pressure else 0.55
            sell_at += 0.10 * min(3, town_boost.get(item, 0))  # town props price
            if attack.get(item):
                sell_at, half_at = 0.05, 0.0  # dump: crash their product
            # falling price: get ahead of the crash
            if mom <= -0.12:
                sell_at -= 0.15
                half_at -= 0.10
            if day >= 25 or n >= 40:
                sells.append(["SELL", item, n])
            elif inv <= I0 - 250 or ratio >= sell_at:
                # scarcity or healthy price: sell into strength
                sells.append(["SELL", item, n])
            elif ratio >= half_at:
                sells.append(["SELL", item, max(1, n // 2)])
            elif n >= 28:  # shed pressure: trickle even at bad prices
                sells.append(["SELL", item, min(n, 10)])
            # else HOLD: town demand recovers crashed premiums in 1-2 days;
            # unharvested product on the animal is our free warehouse.

        paced("MILK", 160)
        # wool crashes hardest (sq 3.2): hard-hold below 0.7 ratio
        wn = shed.get("WOOL", 0)
        if wn > 0:
            wp = prices.get("WOOL", 200)
            if day >= 26 or wn >= 40 or wp >= 140 or (day <= 9 and wp >= 150):
                sells.append(["SELL", "WOOL", wn])   # early clips at premium
            elif wp >= 100:
                sells.append(["SELL", "WOOL", max(1, wn // 2)])
        paced("EGG", 50)
        paced("MELON", 250)
        paced("STRAWBERRY", 120)
        paced("TOMATO", 60)
        paced("CARROT", 35)

        # Surplus wheat: sell only above the feed reserve (THUNDER edge:
        # batch dumps when price is healthy; hold when contested).
        w = shed.get("WHEAT", 0)
        if w > reserve + 4:
            extra = w - reserve
            wp = prices.get("WHEAT", 25)
            if wp >= 22 or extra > 20 or day >= 24:
                sells.append(["SELL", "WHEAT", extra])
                MEM["wheat_sold"] += extra
            elif wp >= 16:
                sells.append(["SELL", "WHEAT", max(1, extra // 2)])
                MEM["wheat_sold"] += max(1, extra // 2)

    # When cash-poor, put fertilizer sells FIRST in the ordered market list:
    # orders process in sequence, so the sale funds the same-turn buys.
    if cash < 300 and any(o[1] == "FERTILIZER" for o in sells):
        front = [o for o in sells if o[1] == "FERTILIZER"]
        rest = [o for o in sells if o[1] != "FERTILIZER"]
        orders = front + orders + rest
    else:
        orders.extend(sells)
    return orders[:10]


# --------------------------------------------------------------------------
# Labor planner: central job board with utility assignment
# --------------------------------------------------------------------------

def scan_farm(obs, farm, private):
    """Build the full job list plus context for the market planner."""
    day = obs.get("day", 0)
    hour = obs.get("hour", 0)
    seeds = private.get("seeds", {}) or {}
    shed = private.get("shed", {}) or {}
    prices = (obs.get("market", {}) or {}).get("prices", {}) or {}
    unlocked = _unlocked(farm)

    jobs = []
    ctx = {"unfed_urgent": 0, "wheat_in_transit": 0, "melons_unfertilized": 0,
           "straw_fert_want": 0,
           "shed_count": sum(shed.values()), "empty_tiles": 0, "crop_count": 0}
    unfed = []
    unwatered = []

    for (x, y) in _owned_tiles(farm):
        t = _tile(farm, x, y)
        if isinstance(t, dict):
            kind = t.get("kind")
            if t.get("animal"):
                a = t["animal"]
                if not t.get("fed_today") and day < 29:
                    cu = t.get("consecutive_unfed", 0) or 0
                    tier = 0 if cu >= 1 else 2
                    jobs.append({"tier": tier, "pos": (x, y), "act": ["FEED"],
                                 "need": "WHEAT", "cls": "animal", "key": ("feed", x, y)})
                    unfed.append((x, y))
                    if cu >= 1:
                        ctx["unfed_urgent"] += 1
                late_stop = day == 29 and hour >= 12
                if t.get("fertilizer_available") and not late_stop:
                    jobs.append({"tier": 4, "pos": (x, y), "act": ["COLLECT_FERTILIZER"],
                                 "cls": "animal", "key": ("fert", x, y)})
                if not t.get("cared_today") and not late_stop:
                    jobs.append({"tier": 4, "pos": (x, y), "act": ["CARE"],
                                 "cls": "animal", "key": ("care", x, y)})
                yu = t.get("yield_units") or 0
                if yu > 0:
                    prod = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}.get(a, "EGG")
                    price = prices.get(prod, BASE_PRICE.get(prod, 50))
                    base = BASE_PRICE.get(prod, 50)
                    cashout = day >= 26
                    if cashout or yu >= 5 or price >= base * 0.82:
                        jobs.append({"tier": 4 if not cashout else 2, "pos": (x, y),
                                     "act": ["HARVEST"], "cls": "animal",
                                     "key": ("aharv", x, y)})
            elif kind == "PLANT":
                ctx["crop_count"] += 1
                crop = t.get("crop")
                if not t.get("watered_today") and day < 29:
                    cu = t.get("consecutive_unwatered", 0) or 0
                    planted_today = t.get("planted_day") == day
                    ongoing = crop in ("STRAWBERRY", "TOMATO")
                    if planted_today and cu >= 1:
                        tier = 0
                    elif cu >= 1:
                        tier = 1
                    elif ongoing:
                        tier = 5
                    else:
                        tier = 3
                    jobs.append({"tier": tier, "pos": (x, y), "act": ["WATER"],
                                 "cls": "crop", "key": ("water", x, y)})
                    unwatered.append((x, y))
                    if cu >= 1:
                        ctx.setdefault("water_urgent_tiles", []).append((x, y))
                elif (t.get("yield_units") or 0) > 0:
                    age = day - t.get("planted_day", day)
                    ready = crop not in FIRST_YIELD_DAY or age >= FIRST_YIELD_DAY[crop]
                    if crop in PEAK_AGE:
                        # one-time: wait for peak unless decay looming or endgame
                        peak = PEAK_AGE[crop]
                        if age >= peak or day >= 27 or age >= peak + 1:
                            ht = 2 if (day >= 24 or age > peak) else 3
                            jobs.append({"tier": ht, "pos": (x, y), "act": ["HARVEST"],
                                         "cls": "crop", "key": ("charv", x, y)})
                    elif ready:
                        jobs.append({"tier": 3, "pos": (x, y), "act": ["HARVEST"],
                                     "cls": "crop", "key": ("charv", x, y)})
                # fertilize melons in the bonus window
                if crop == "MELON" and t.get("fertilized_until_day", -1) < day:
                    age = day - t.get("planted_day", day)
                    if 4 <= age <= 7 and day <= 16:
                        ctx["melons_unfertilized"] += 1
                        if MEM["fert_spent_on_melons"] < CONFIG["fertilizer_for_melons"]:
                            jobs.append({"tier": 5, "pos": (x, y), "act": ["FERTILIZE"],
                                         "need": "FERTILIZER", "cls": "crop", "key": ("fertm", x, y)})
                # fertilize STRAWBERRIES when the 3-day window covers 2 ticks
                # (doubles each covered tick — the biggest fert value in game)
                if crop == "STRAWBERRY" and t.get("fertilized_until_day", -1) < day:
                    age = day - t.get("planted_day", day)
                    ticks = sum(1 for d in (10, 12, 14, 16) if age <= d <= age + 2)
                    if ticks >= 2 and day <= 24:
                        ctx["straw_fert_want"] += 1
                        if MEM["fert_spent_on_straw"] < CONFIG["fertilizer_for_strawberries"]:
                            jobs.append({"tier": 3, "pos": (x, y), "act": ["FERTILIZE"],
                                         "need": "FERTILIZER", "cls": "crop",
                                         "key": ("ferts", x, y)})
            elif kind == "WEED":
                if not (day == 29 and hour >= 14):
                    jobs.append({"tier": 6 if day < 24 else 3, "pos": (x, y), "act": ["DIG"],
                                 "cls": "crop", "key": ("weed", x, y)})
        elif t is None:
            ctx["empty_tiles"] += 1
            if day <= 25 and hour <= 18:
                crop = _choose_plant((x, y), day, seeds, farm)
                if crop:
                    tier = 5 if day <= 22 else 4
                    jobs.append({"tier": tier, "pos": (x, y), "act": ["PLANT", crop],
                                 "seed": crop, "cls": "crop", "key": ("plant", x, y)})

    # Animal placement jobs: animals waiting IN THE SHED need collection.
    # (Animals already in unit inventories are handled by pre-pass A.)
    waiting = sum(shed.get(k, 0) for k in ("COW", "SHEEP", "GOOSE"))
    empty_past = _empty_pastures(farm)
    carrying_animals = sum(
        (private.get("inventories", []) or [{}])[i].get(k, 0)
        for i in range(len(private.get("inventories", []) or []))
        for k in ("COW", "SHEEP", "GOOSE")
    ) if private.get("inventories") else 0
    if waiting > 0 and (empty_past or unbuilt_pasture_slots(farm, unlocked)):
        slots = len(empty_past) + unbuilt_pasture_slots(farm, unlocked)
        for i in range(min(waiting, max(slots, 1), 2)):
            jobs.append({"tier": 3, "pos": None, "act": ["PLACE"],
                         "pickup_animal": True, "cls": "animal", "key": ("place", i)})
    # Proactive pasture building: keep housing ahead of the animal ramp so
    # bought animals never sit in the shed (a shed animal earns nothing).
    herd = _count_animals_on_farm(farm) + waiting + carrying_animals
    need_housing = herd < (CONFIG["target_cows"] + CONFIG["target_sheep"]) and day <= 18
    if (waiting + carrying_animals > 0 and len(empty_past) <= 1) or need_housing:
        built_jobs = 0
        for (x, y) in PASTURE_LAYOUT:
            if built_jobs >= 2:
                break
            if _quad_of(x, y) in unlocked and _tile(farm, x, y) is None:
                jobs.append({"tier": 4, "pos": (x, y), "act": ["BUILD_PASTURE"],
                             "cls": "animal", "key": ("build", x, y)})
                built_jobs += 1

    ctx["unfed_total"] = len(unfed)
    ctx["unwatered_total"] = len(unwatered)
    ctx["urgent_water_count"] = len(ctx.get("water_urgent_tiles", []))
    ctx["animal_jobs_pending"] = sum(1 for j in jobs if j.get("cls") == "animal")
    return jobs, ctx


def _choose_plant(pos, day, seeds, farm):
    """What to plant on an empty tile right now (fill mandate)."""
    x, y = pos
    if day > 25:
        return None
    sd = _shed_dist(pos)
    # Wheat ring: tiles close to the shed grow feed wheat first. The ring
    # widens to sd==3 mid-season so we FEED OURSELVES instead of buying
    # wheat into contested $35+ spikes (THUNDER's net-seller edge).
    ring = 3 if (8 <= day <= 24 and seeds.get("WHEAT", 0) > 8) else 2
    if sd <= ring and seeds.get("WHEAT", 0) > 0 and day <= PLANT_UNTIL["WHEAT"]:
        return "WHEAT"
    # Premiums by timing. Strawberry outranks melon inside its window:
    # 4 ticks of $120+ fruit beat one melon when the price is healthy.
    if seeds.get("STRAWBERRY", 0) > 0 and day <= PLANT_UNTIL["STRAWBERRY"]:
        return "STRAWBERRY"
    if seeds.get("MELON", 0) > 0 and day <= PLANT_UNTIL["MELON"]:
        return "MELON"
    if seeds.get("TOMATO", 0) > 0 and day <= PLANT_UNTIL["TOMATO"]:
        return "TOMATO"
    if seeds.get("CARROT", 0) > 0 and day <= PLANT_UNTIL["CARROT"]:
        return "CARROT"
    if seeds.get("WHEAT", 0) > 0 and day <= PLANT_UNTIL["WHEAT"]:
        return "WHEAT"
    return None


def _on_tile_action(u, farm, obs, ctx):
    """Opportunistic action for what is RIGHT UNDER the unit. This captures
    free wins (feed the animal you're standing on, water the crop you pass)
    exactly like the top bots' per-tile state machines do."""
    day = obs.get("day", 0)
    shed = ctx.get("_shed", {}) or {}
    x, y = u["pos"]
    t = _tile(farm, x, y)
    inv = u["inv"]
    wheat = inv.get("WHEAT", 0) or 0
    if isinstance(t, dict):
        if t.get("animal"):
            if not t.get("fed_today") and wheat > 0:
                return ["FEED"]
            if t.get("fertilizer_available"):
                return ["COLLECT_FERTILIZER"]
            if not t.get("cared_today"):
                return ["CARE"]
            if (t.get("yield_units") or 0) > 0:
                return ["HARVEST"]
            return None
        kind = t.get("kind")
        if kind == "PLANT":
            if not t.get("watered_today"):
                return ["WATER"]
            yu = t.get("yield_units") or 0
            if yu > 0:
                crop = t.get("crop")
                age = day - t.get("planted_day", day)
                if crop in PEAK_AGE:
                    if age >= PEAK_AGE[crop] or day >= 27:
                        return ["HARVEST"]
                elif age >= FIRST_YIELD_DAY.get(crop, 2):
                    return ["HARVEST"]
            return None
        if kind == "WEED" and day < 26:
            return ["DIG"]
        if kind in ("PASTURE", "COOP") and not t.get("animal"):
            for k in ("COW", "SHEEP", "GOOSE"):
                if inv.get(k, 0) > 0 and ANIMAL_STRUCT[k] == kind:
                    return ["PLACE", k]
        return None
    # empty tile / shed tiles
    if t is None:
        for k in ("COW", "SHEEP", "GOOSE"):
            if inv.get(k, 0) > 0:
                return None  # need a pasture, handled by job board
    return None


def _shed_drop_action(u, ctx, farm):
    """Drop produce at the shed when carrying any (keeps inventory free and
    goods sellable). Wheat/fertilizer mixing is harmless: wheat goes back to
    the feed reserve, fertilizer sells."""
    inv = u["inv"]
    # units carrying an animal never drop (the animal would get dumped too)
    if any(inv.get(k, 0) > 0 for k in ("COW", "SHEEP", "GOOSE")):
        return None
    # animals are NEVER goods (they get PLACE'd, not dropped back to the shed)
    has_goods = any(k not in ("WHEAT", "COW", "SHEEP", "GOOSE") and v > 0
                    for k, v in inv.items())
    if not has_goods:
        return None
    if _shed_dist(u["pos"]) == 0:
        return ["DROP"]
    return None


def assign_jobs(obs, farm, private, jobs, ctx):
    """PATROL ENGINE + ADAPTIVE SURVIVAL.
    Crop workers ping-pong tight segments (efficient watering/harvest/plant);
    tenders work the animal corridor; survival emergencies override everything
    and units rejoin their patrol automatically (position-derived)."""
    day = obs.get("day", 0)
    hour = obs.get("hour", 0)
    seeds = private.get("seeds", {}) or {}
    shed = private.get("shed", {}) or {}
    inv_list = private.get("inventories") or [{}]
    hands = farm.get("hands") or []
    farmer = farm.get("farmer")
    positions = ([farmer] if farmer else []) + hands
    units = [{"idx": i, "pos": tuple(p),
              "inv": inv_list[i] if i < len(inv_list) else {}}
             for i, p in enumerate(positions) if p is not None]
    n_units = len(units)
    assigned = {}
    if n_units == 0:
        return ["PASS"], []
    unlocked = _unlocked(farm)
    active_quads = [q for q in ("NW", "NE", "SW", "SE") if q in unlocked]

    def free_units():
        return [u for u in units if u["idx"] not in assigned]

    # ============ 1. ADAPTIVE SURVIVAL OVERRIDES (always wins) ============
    feed_em, water_em = [], []
    for (x, y) in _owned_tiles(farm):
        t = _tile(farm, x, y)
        if isinstance(t, dict):
            if t.get("animal") and not t.get("fed_today") \
                    and (t.get("consecutive_unfed", 0) or 0) >= 1:
                feed_em.append((x, y))
            elif t.get("kind") == "PLANT" and not t.get("watered_today") and day < 29:
                cu = t.get("consecutive_unwatered", 0) or 0
                if cu >= 1 or t.get("planted_day") == day:
                    water_em.append((x, y))
    wheat_pool = shed.get("WHEAT", 0) + sum(u["inv"].get("WHEAT", 0) for u in units)
    tender_ids_set = set(u["idx"] for u in units[:min(3, n_units)])
    for tile in feed_em:
        free = free_units()
        if not free:
            break
        carriers = [u for u in free if u["inv"].get("WHEAT", 0) > 0]
        if carriers:
            u = min(carriers, key=lambda u: _manhattan(u["pos"], tile))
            assigned[u["idx"]] = ["FEED"] if u["pos"] == tile else _move_toward(u["pos"], tile)
        elif wheat_pool > 0:
            pref = [u for u in free if u["idx"] in tender_ids_set] or free
            u = min(pref, key=lambda u: _shed_dist(u["pos"]))
            if _shed_dist(u["pos"]) == 0:
                assigned[u["idx"]] = ["PICKUP", "WHEAT", 6]
                wheat_pool = max(0, wheat_pool - 6)
            else:
                t2, _ = _nearest(u["pos"], SHED_TILES)
                assigned[u["idx"]] = _move_toward(u["pos"], t2)
        else:
            break
    for tile in water_em:
        # tenders stay on the animal line — workers cover watering
        free = [u for u in free_units() if u["idx"] not in tender_ids_set] \
            or free_units()
        if not free:
            break
        u = min(free, key=lambda u: _manhattan(u["pos"], tile))
        assigned[u["idx"]] = ["WATER"] if u["pos"] == tile else _move_toward(u["pos"], tile)

    # ============ 2. SHED ANIMALS: house them (max 2 units) ==============
    waiting = sum(shed.get(k, 0) for k in ("COW", "SHEEP", "GOOSE"))
    if waiting > 0:
        empty_past = _empty_pastures(farm)
        unbuilt = [(x, y) for (x, y) in PASTURE_LAYOUT
                   if _quad_of(x, y) in unlocked and _tile(farm, x, y) is None]
        duty = 0
        for u in free_units():
            if waiting <= 0 or duty >= 2:
                break
            held = next((k for k in ("COW", "SHEEP", "GOOSE") if u["inv"].get(k, 0)), None)
            if held and empty_past:
                tgt = min(empty_past, key=lambda p: _manhattan(u["pos"], p))
                if u["pos"] == tgt:
                    assigned[u["idx"]] = ["PLACE", held]
                    empty_past.remove(tgt)
                    waiting -= 1
                else:
                    assigned[u["idx"]] = _move_toward(u["pos"], tgt)
                duty += 1
            elif empty_past and shed.get("COW", 0) + shed.get("SHEEP", 0) + shed.get("GOOSE", 0) > 0:
                if _shed_dist(u["pos"]) == 0:
                    kind = next((k for k in ("COW", "SHEEP", "GOOSE") if shed.get(k, 0) > 0), None)
                    assigned[u["idx"]] = ["PICKUP", kind, 1]
                else:
                    t2, _ = _nearest(u["pos"], SHED_TILES)
                    assigned[u["idx"]] = _move_toward(u["pos"], t2)
                duty += 1
            elif unbuilt:
                tgt = min(unbuilt, key=lambda p: _manhattan(u["pos"], p))
                assigned[u["idx"]] = ["BUILD_PASTURE"] if u["pos"] == tgt else _move_toward(u["pos"], tgt)
                duty += 1

    # ============ 3. PATROL BEATS =========================================
    # tenders: the animal corridor (pasture tiles, sorted in a stable loop)
    pastures = []
    for (x, y) in _owned_tiles(farm):
        t = _tile(farm, x, y)
        if isinstance(t, dict) and t.get("kind") in ("PASTURE", "COOP") and t.get("animal"):
            pastures.append((x, y))
    pastures.sort(key=lambda p: (math.atan2(p[1] - 4.5, p[0] - 4.5), p))
    n_tenders = min(3, n_units)
    tenders = [u for u in units[:n_tenders]]
    workers = [u for u in units[n_tenders:]]
    # workers: quadrant serpents split into contiguous segments (ping-pong)
    seg_of = {}
    by_quad = {}
    for i, u in enumerate(workers):
        q = active_quads[i % len(active_quads)] if active_quads else "NW"
        by_quad.setdefault(q, []).append(u)
    for q, wlist in by_quad.items():
        route = quad_route(q)
        L = len(route)
        k = len(wlist)
        for j, u in enumerate(wlist):
            a = j * L // k
            b = max(a + 1, (j + 1) * L // k)
            seg_of[u["idx"]] = route[a:b]
    patrol = MEM.setdefault("patrol_state", {})

    def good_load(u):
        return sum(v for k2, v in u["inv"].items()
                   if v > 0 and k2 not in ("WHEAT", "COW", "SHEEP", "GOOSE"))

    # tenders first
    for i, u in enumerate(tenders):
        if u["idx"] in assigned:
            continue
        if good_load(u) >= 3:
            if _shed_dist(u["pos"]) == 0:
                assigned[u["idx"]] = ["DROP"]
            else:
                t2, _ = _nearest(u["pos"], SHED_TILES)
                assigned[u["idx"]] = _move_toward(u["pos"], t2)
            continue
        t = _tile(farm, u["pos"][0], u["pos"][1])
        act = None
        if isinstance(t, dict) and t.get("animal"):
            if not t.get("fed_today") and u["inv"].get("WHEAT", 0) > 0:
                act = ["FEED"]
            elif (t.get("yield_units") or 0) > 0:
                act = ["HARVEST"]
            elif t.get("fertilizer_available"):
                act = ["COLLECT_FERTILIZER"]
            elif not t.get("cared_today") and day >= 6 and day <= 27:
                act = ["CARE"]
        if act:
            assigned[u["idx"]] = act
            continue
        # refill wheat from the shed when running dry
        if u["inv"].get("WHEAT", 0) <= 1 and shed.get("WHEAT", 0) > 0 and pastures:
            if _shed_dist(u["pos"]) == 0:
                assigned[u["idx"]] = ["PICKUP", "WHEAT", 6]
                continue
            t2, _ = _nearest(u["pos"], SHED_TILES)
            assigned[u["idx"]] = _move_toward(u["pos"], t2)
            continue
        # patrol the corridor
        if not pastures:
            assigned[u["idx"]] = ["PASS"]
            continue
        key = "T" + str(u["idx"])
        st = patrol.get(key)
        if not st or st.get("n") != len(pastures):
            i_here = min(range(len(pastures)),
                         key=lambda ii: _manhattan(u["pos"], pastures[ii]))
            st = {"i": i_here, "d": 1, "n": len(pastures)}
            patrol[key] = st
        tgt = pastures[st["i"]]
        if u["pos"] != tgt:
            assigned[u["idx"]] = _move_toward(u["pos"], tgt)
            continue
        st["i"] += st["d"]
        if st["i"] >= len(pastures) or st["i"] < 0:
            st["d"] = -st["d"]
            st["i"] = min(max(st["i"], 0), len(pastures) - 1)
        assigned[u["idx"]] = ["PASS"]

    # crop workers
    for u in workers:
        if u["idx"] in assigned:
            continue
        if good_load(u) >= 3:
            if _shed_dist(u["pos"]) == 0:
                assigned[u["idx"]] = ["DROP"]
            else:
                t2, _ = _nearest(u["pos"], SHED_TILES)
                assigned[u["idx"]] = _move_toward(u["pos"], t2)
            continue
        seg = seg_of.get(u["idx"])
        if not seg:
            assigned[u["idx"]] = ["PASS"]
            continue
        t = _tile(farm, u["pos"][0], u["pos"][1])
        act = None
        if isinstance(t, dict) and t.get("kind") == "PLANT":
            crop = t.get("crop")
            age = day - t.get("planted_day", day)
            if crop in PEAK_AGE:
                if (t.get("yield_units") or 0) > 0 and (age >= PEAK_AGE[crop] or day >= 27):
                    act = ["HARVEST"]
            elif (t.get("yield_units") or 0) > 0 and \
                    (crop not in FIRST_YIELD_DAY or age >= FIRST_YIELD_DAY[crop]):
                act = ["HARVEST"]
            if act is None and not t.get("watered_today") and day < 29:
                act = ["WATER"]
        elif isinstance(t, dict) and t.get("kind") == "WEED" and day < 28:
            act = ["DIG"]
        elif t is None and day <= 26 and hour <= 18:
            crop = _choose_plant(u["pos"], day, seeds, farm)
            if crop and seeds.get(crop, 0) > 0:
                act = ["PLANT", crop]
        if act:
            assigned[u["idx"]] = act
            continue
        key = "W" + str(u["idx"])
        st = patrol.get(key)
        if not st or st.get("n") != len(seg):
            i_here = min(range(len(seg)),
                         key=lambda ii: _manhattan(u["pos"], seg[ii]))
            st = {"i": i_here, "d": 1, "n": len(seg)}
            patrol[key] = st
        nxt_i = st["i"] + st["d"]
        if nxt_i >= len(seg) or nxt_i < 0:
            st["d"] = -st["d"]
            nxt_i = st["i"] + st["d"]
        if len(seg) == 1:
            assigned[u["idx"]] = ["PASS"]
            continue
        st["i"] = nxt_i
        tgt = seg[nxt_i]
        assigned[u["idx"]] = _move_toward(u["pos"], tgt) if u["pos"] != tgt else ["PASS"]

    farmer_act = assigned.get(0, ["PASS"])
    hand_acts = [assigned.get(i + 1, ["PASS"]) for i in range(len(hands))]
    return farmer_act, hand_acts


def agent(obs):
    try:
        player = obs.get("player", 0)
        farms = obs.get("farms", []) or []
        if not farms or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        farm = farms[player]
        private = obs.get("private", {}) or {}
        CURRENT_FARM[0] = farm

        # opponent awareness (public farm): read their build every turn so
        # the market brain knows who is about to crash which product.
        try:
            opp = farms[1 - player]
            MEM["opp_animals"] = _count_animals_on_farm(opp)
            oc = ocows = osheep = ostrap = omelon = 0
            for row in opp.get("tiles", []):
                for t in row:
                    if isinstance(t, dict):
                        if t.get("kind") == "PLANT":
                            oc += 1
                            c = t.get("crop")
                            if c == "STRAWBERRY":
                                ostrap += 1
                            elif c == "MELON":
                                omelon += 1
                        elif t.get("animal") == "COW":
                            ocows += 1
                        elif t.get("animal") == "SHEEP":
                            osheep += 1
            MEM["opp_crops"] = oc
            MEM["opp_cows"] = ocows
            MEM["opp_sheep"] = osheep
            MEM["opp_straw"] = ostrap
            MEM["opp_melon"] = omelon
        except Exception:
            pass
        # price momentum (24-turn lookback) for sell timing
        try:
            prices_now = (obs.get("market", {}) or {}).get("prices", {}) or {}
            hist = MEM.setdefault("price_hist", {})
            for item, p in prices_now.items():
                hist.setdefault(item, []).append(p)
                if len(hist[item]) > 48:
                    hist[item] = hist[item][-48:]
        except Exception:
            pass

        jobs, ctx = scan_farm(obs, farm, private)
        market = plan_market(obs, farm, private, ctx)
        farmer_act, hand_acts = assign_jobs(obs, farm, private, jobs, ctx)

        return {"farmer": farmer_act or ["PASS"], "hands": hand_acts,
                "market": market[:10]}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}
