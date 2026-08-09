"""
HI_AgriBot v9.0 "Field Marshal II"
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

VERSION = "HI_AgriBot_v9.1_FieldMarshalII"

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
FIRST_YIELD_DAY = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}
# Last day it is worth PLANTING each crop (so it pays before season end).
PLANT_UNTIL = {"WHEAT": 22, "CARROT": 24, "TOMATO": 17, "STRAWBERRY": 15, "MELON": 17}
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
    # NE rows (after day 7): 6 spots
    (5, 3), (6, 3), (7, 3), (8, 3), (6, 4), (7, 4),
    # SW row (after day 11): 2 spots
    (3, 5), (2, 5),
]

CONFIG = {
    "target_cows": 8,
    "target_sheep": 6,
    "buy_ne_day": 7,
    "buy_sw_day": 11,
    "animal_buy_last_day_cow": 13,
    "animal_buy_last_day_sheep": 11,
    "feed_reserve_base": 6,          # shed wheat >= animals*1 + this (never sold)
    "feed_reserve_cap": 40,
    "shed_soft_cap": 88,             # pause harvesting above this until sells free room
    "fertilizer_for_melons": 14,     # units diverted onto melons over the season
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
            want = 12
        elif day <= 20:
            want = 12
        elif day <= 26:
            want = 11
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
    # Demand-aware: buy only what can actually be planted (empty tiles plus
    # tiles about to free up), and close each buy window ~2 days before that
    # crop stops being plantable — no dead seeds riding into turn 720.
    demand = jobs_ctx.get("empty_tiles", 0) + jobs_ctx.get("soon_empty", 0)
    if not final_day and hour in (1, 8, 14) and len(orders) < 9:
        crops = _crop_counts(farm)
        # Wheat: the feed engine (plantable through day 22 → buy to day 20).
        wseeds = seeds.get("WHEAT", 0)
        if day <= 19 and wseeds < 14 and demand > wseeds // 2 and proj >= 200:
            n = min(14 - wseeds, 10, max(2, demand))
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
        if 8 <= day <= 10 and seeds.get("STRAWBERRY", 0) < 12 and proj >= 1300 \
                and demand >= 4:
            n = min(12 - seeds.get("STRAWBERRY", 0), int((proj - 1100) // 100), 6, demand)
            if n > 0:
                orders.append(["BUY_SEED", "STRAWBERRY", n])
                cash -= 100 * n
                proj -= 100 * n
        if 11 <= day <= 11 and sb < 32 and seeds.get("STRAWBERRY", 0) < 12 and proj >= 1500 \
                and demand >= 6:
            n = min(12 - seeds.get("STRAWBERRY", 0), int((proj - 1300) // 100), 6, demand)
            if n > 0:
                orders.append(["BUY_SEED", "STRAWBERRY", n])
                cash -= 100 * n
                proj -= 100 * n
        # Melon wave 1 (day 0 handled) + wave 2 (plantable to day 17 → buy to 14).
        if 7 <= day <= 12 and crops.get("MELON", 0) + seeds.get("MELON", 0) < 16 \
                and seeds.get("MELON", 0) < 8 and proj >= 800 and demand >= 5:
            n = min(8 - seeds.get("MELON", 0), 5, demand)
            orders.append(["BUY_SEED", "MELON", n])
            cash -= 80 * n
            proj -= 80 * n
        # Tomato mid-game bridge (plantable to day 17 → buy to day 9).
        if 4 <= day <= 9 and seeds.get("TOMATO", 0) < 3 and crops.get("TOMATO", 0) < 8 \
                and proj >= 700 and demand >= 3:
            n = min(3 - seeds.get("TOMATO", 0), 3, demand)
            orders.append(["BUY_SEED", "TOMATO", n])
            cash -= 50 * n
            proj -= 50 * n

    # ---------------- Feed wheat: buy shortfall against the reserve --------
    animals = _count_animals_on_farm(farm)
    wheat = shed.get("WHEAT", 0) + jobs_ctx.get("wheat_in_transit", 0)
    reserve = min(CONFIG["feed_reserve_base"] + animals, CONFIG["feed_reserve_cap"])
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
    else:
        # Fertilizer: sell every unit, every day (mandate). Split big holds.
        f_hold = shed.get("FERTILIZER", 0)
        if f_hold > 0:
            if f_hold <= 14:
                sells.append(["SELL", "FERTILIZER", f_hold])
            else:
                sells.append(["SELL", "FERTILIZER", 14])
                sells.append(["SELL", "FERTILIZER", f_hold - 14])

        inv_map = (obs.get("market", {}) or {}).get("inventory", {}) or {}
        opp_animal_heavy = MEM.get("opp_animals", 0) >= 10
        opp_crop_heavy = MEM.get("opp_crops", 0) >= 30

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
            if day >= 26 or wn >= 40 or wp >= 140:
                sells.append(["SELL", "WOOL", wn])
            elif wp >= 100:
                sells.append(["SELL", "WOOL", max(1, wn // 2)])
        paced("EGG", 50)
        paced("MELON", 250)
        paced("STRAWBERRY", 120)
        paced("TOMATO", 60)
        paced("CARROT", 35)

        paced("MILK", 160)
        # wool crashes hardest (sq 3.2): hard-hold below 0.7 ratio
        wn = shed.get("WOOL", 0)
        if wn > 0:
            wp = prices.get("WOOL", 200)
            if day >= 26 or wn >= 40 or wp >= 140:
                sells.append(["SELL", "WOOL", wn])
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
           "shed_count": sum(shed.values()), "empty_tiles": 0, "crop_count": 0}
    unfed = []
    unwatered = []

    for (x, y) in _owned_tiles(farm):
        t = _tile(farm, x, y)
        if isinstance(t, dict):
            kind = t.get("kind")
            if t.get("animal"):
                a = t["animal"]
                if not t.get("fed_today"):
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
                if not t.get("watered_today"):
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

    # demand prediction: one-time crops within 1 day of harvest (or decay)
    # will free their tile soon — seeds should already be banked for them.
    soon_empty = 0
    for (x, y) in _owned_tiles(farm):
        t = _tile(farm, x, y)
        if isinstance(t, dict) and t.get("kind") == "PLANT":
            c = t.get("crop")
            if c in PEAK_AGE:
                age = day - t.get("planted_day", day)
                if age >= PEAK_AGE[c] - 1:
                    soon_empty += 1
    ctx["soon_empty"] = soon_empty
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
    """Serpentine lane through a quadrant, starting at its shed corner."""
    if q not in ROUTE_CACHE:
        pts = []
        for c in range(HALF):
            rows = range(HALF) if c % 2 == 0 else range(HALF - 1, -1, -1)
            for r in rows:
                pts.append(_local_to_global(q, c, r))
        ROUTE_CACHE[q] = pts
    return ROUTE_CACHE[q]


def assign_jobs(obs, farm, private, jobs, ctx):
    """Greedy utility assignment: one job per unit, one unit per job."""
    day = obs.get("day", 0)
    shed = private.get("shed", {}) or {}
    ctx["_shed"] = shed
    invs = private.get("inventories", []) or []
    seeds = private.get("seeds", {}) or {}

    units = []
    fpos = tuple(farm.get("farmer", [HALF - 1, HALF - 1]) or [HALF - 1, HALF - 1])
    units.append({"idx": 0, "pos": fpos, "inv": invs[0] if invs else {}, "farmer": True})
    for i, h in enumerate(farm.get("hands") or []):
        hi = i + 1
        units.append({"idx": hi, "pos": tuple(h),
                      "inv": invs[hi] if hi < len(invs) else {}, "farmer": False})

    assigned = {}   # unit idx -> action
    claimed = set()
    emergency_feed = ctx["unfed_urgent"] > 0
    n_units = len(units)
    animals_now = _count_animals_on_farm(farm)
    # 3 tenders is the measured optimum: 4 caused duty-overlap escapes, and
    # 2 starved the animals under pressure. The freed hand plants crops.
    if n_units >= 6 and animals_now >= 8:
        n_tenders = 3
    elif n_units >= 4:
        n_tenders = 2
    else:
        n_tenders = 1
    tenders = set(u["idx"] for u in sorted(units, key=lambda u: u["idx"])[:n_tenders])
    ctx["_tenders"] = tenders
    empty_past = _empty_pastures(farm)
    unlocked = _unlocked(farm)
    unbuilt_spots = [(x, y) for (x, y) in PASTURE_LAYOUT
                     if _quad_of(x, y) in unlocked and _tile(farm, x, y) is None]

    def carrying(u, item):
        return (u["inv"].get(item, 0) or 0) > 0

    def carried_animal(u):
        for k in ("COW", "SHEEP", "GOOSE"):
            if carrying(u, k):
                return k
        return None

    def carrying_nonwheat(u):
        return any(k != "WHEAT" and k != "FERTILIZER" and v > 0
                   for k, v in u["inv"].items())

    # Per-turn seed budget (shared by on-tile planting and job assignment)
    seed_budget = {k: v for k, v in seeds.items()}
    hour = obs.get("hour", 0)

    # ---- Pre-pass A: units carrying an animal MUST place it first. ----
    for u in units:
        a = carried_animal(u)
        if not a:
            continue
        if empty_past:
            tgt, _ = _nearest(u["pos"], empty_past)
            if u["pos"] == tgt:
                assigned[u["idx"]] = ["PLACE", a]
                empty_past.remove(tgt)
            else:
                assigned[u["idx"]] = _move_toward(u["pos"], tgt)
        elif unbuilt_spots:
            tgt, _ = _nearest(u["pos"], unbuilt_spots)
            if u["pos"] == tgt:
                assigned[u["idx"]] = ["BUILD_PASTURE"]
                unbuilt_spots.remove(tgt)
            else:
                assigned[u["idx"]] = _move_toward(u["pos"], tgt)
        else:
            assigned[u["idx"]] = ["PASS"]

    # ---- Pre-pass B: units carrying produce haul it to the shed when the
    # load is heavy or no urgent work is adjacent. ----
    for u in units:
        if u["idx"] in assigned:
            continue
        load = sum(v for k, v in u["inv"].items()
                   if v > 0 and k not in ("WHEAT", "FERTILIZER"))
        if load >= 5 or (load > 0 and ctx["shed_count"] >= CONFIG["shed_soft_cap"]):
            if _shed_dist(u["pos"]) == 0:
                assigned[u["idx"]] = ["DROP"]
            else:
                t, _ = _nearest(u["pos"], SHED_TILES)
                assigned[u["idx"]] = _move_toward(u["pos"], t)

    def job_sort(j):
        return j["tier"]
    jobs_sorted = sorted(jobs, key=job_sort)
    job_by_key = {j["key"]: j for j in jobs}

    def unit_action_for_job(u, j):
        pos = u["pos"]
        target = j["pos"]
        if target is None:
            return ["PASS"]
        if pos == tuple(target):
            return list(j["act"])
        return _move_toward(pos, target)

    sticky = MEM.setdefault("sticky", {})

    def take_job(u, j):
        assigned[u["idx"]] = unit_action_for_job(u, j)
        claimed.add(j["key"])
        sticky[(day, u["idx"])] = j["key"]

    # Pass 1: hard tiers (0-2): emergency feed, at-risk water, feed.
    resupply_cap = max(1, (ctx.get("unfed_total", 0) + 3) // 4)
    resupply_sent = 0
    quad_load = {}
    for j in jobs_sorted:
        if j["tier"] > 2:
            break
        if j["key"] in claimed:
            continue
        need = j.get("need")
        if need == "WHEAT":
            cands = [u for u in units if u["idx"] not in assigned
                     and carrying(u, "WHEAT") and not carrying_nonwheat(u)]
            if cands:
                u = min(cands, key=lambda u: _manhattan(u["pos"], j["pos"]))
                take_job(u, j)
            elif shed.get("WHEAT", 0) > 0 and resupply_sent < resupply_cap:
                # send nearest empty-handed unit to grab wheat (capped: one
                # pickup of 3-5 feeds several animals)
                cands = [u for u in units if u["idx"] not in assigned
                         and not carrying_nonwheat(u) and not carrying(u, "WHEAT")]
                if cands:
                    u = min(cands, key=lambda u: _shed_dist(u["pos"]))
                    grab = 5 if (u["farmer"] or u["idx"] <= 3) else 3
                    assigned[u["idx"]] = _pickup_or_move(u, "WHEAT", grab)
                    ctx["wheat_in_transit"] += grab
                    claimed.add(j["key"])
                    resupply_sent += 1
        else:
            cands = [u for u in units if u["idx"] not in assigned]
            if not cands:
                break
            if j["act"][0] == "WATER":
                # congestion-aware: spread watering crews across quadrants so
                # far corners don't dry out while everyone works near the shed
                def wscore(u):
                    q = _quad_of(j["pos"][0], j["pos"][1])
                    return _manhattan(u["pos"], j["pos"]) + 6 * quad_load.get(q, 0)
                u = min(cands, key=wscore)
                quad_load[_quad_of(j["pos"][0], j["pos"][1])] = \
                    quad_load.get(_quad_of(j["pos"][0], j["pos"][1]), 0) + 1
            else:
                u = min(cands, key=lambda u: _manhattan(u["pos"], j["pos"]))
            take_job(u, j)

    # ---- Pre-pass 0: opportunistic on-tile actions (the free wins),
    # ROLE-GATED so crop workers walk straight through the animal corridor
    # instead of stopping for every chore (the bug that starved planting).
    final_rush = day >= 28
    for u in units:
        a = _shed_drop_action(u, ctx, farm)
        if a:
            assigned[u["idx"]] = a
            continue
        if final_rush:
            inv = u["inv"]
            if any(k not in ("WHEAT", "COW", "SHEEP", "GOOSE") and v > 0
                   for k, v in inv.items()):
                t, _ = _nearest(u["pos"], SHED_TILES)
                assigned[u["idx"]] = _move_toward(u["pos"], t)
                continue
        # instant planting: a worker standing on ANY empty tile plants it
        # right now (kills sticky tunnel-vision across the fields)
        t_here = _tile(farm, u["pos"][0], u["pos"][1])
        if (t_here is None and u["idx"] not in tenders and day <= 25
                and hour <= 18 and not carried_animal(u)):
            urgent = ctx.get("water_urgent_tiles") or []
            near_urgent = any(_manhattan(u["pos"], w) <= 3 for w in urgent)
            # governor: stop planting if urgent watering is piling up
            over_planted = ctx.get("urgent_water_count", 0) >= max(6, n_units)
            if over_planted:
                pass
            elif not (urgent and near_urgent):
                crop = _choose_plant(u["pos"], day, seeds, farm)
                if crop and seed_budget.get(crop, 0) > 0:
                    seed_budget[crop] -= 1
                    assigned[u["idx"]] = ["PLANT", crop]
                    claimed.add(("plant",) + u["pos"])
                    continue
        a = _on_tile_action(u, farm, obs, ctx)
        if not a:
            continue
        is_tender = u["idx"] in tenders
        act = a[0]
        animal_acts = ("FEED", "CARE", "COLLECT_FERTILIZER", "PLACE")
        if act in animal_acts and not is_tender and not emergency_feed:
            continue  # workers never stop for animal chores
        if act == "HARVEST":
            # animal harvest is tender work; crop harvest is worker work
            t = _tile(farm, u["pos"][0], u["pos"][1])
            if isinstance(t, dict) and t.get("animal") and not is_tender:
                continue
        assigned[u["idx"]] = a
        x, y = u["pos"]
        for j in jobs:
            if j["pos"] == (x, y):
                claimed.add(j["key"])
                break

    # ---- Sticky targets: a unit keeps walking to the same job until it is
    # done or invalidated (kills the A<->B oscillation that wastes turns).
    for u in units:
        if u["idx"] in assigned:
            continue
        sk = (day, u["idx"])
        prev = sticky.get(sk)
        j = job_by_key.get(prev) if prev else None
        if j is None or j["key"] in claimed:
            sticky.pop(sk, None)
            continue
        # Only a feed EMERGENCY breaks a commitment. Routine survival work
        # (watering) is covered on-tile opportunistically as units pass, so
        # we never churn commitments — that made planters re-target every
        # turn and never reach their plot.
        if emergency_feed and j["tier"] > 0:
            sticky.pop(sk, None)
            continue
        need = j.get("need")
        if need == "WHEAT" and not carrying(u, "WHEAT"):
            sticky.pop(sk, None)
            continue
        if need == "FERTILIZER" and not carrying(u, "FERTILIZER"):
            sticky.pop(sk, None)
            continue
        if j["act"][0] == "PLANT":
            crop = j.get("seed")
            if seed_budget.get(crop, 0) <= 0:
                sticky.pop(sk, None)
                continue
            seed_budget[crop] -= 1
        take_job(u, j)

    # ---- Role split (the top bots' labor division, kept flexible):
    # farmer + first 2 hands are TENDERS for the animal corridor; the rest
    # are CROP WORKERS that fill and water the lanes. Overflow crosses over.
    fill_boost = ctx.get("crop_count", 0) < 36 and day <= 25

    # Pass 2: CLASS-BASED assignment. Tenders take the animal corridor
    # (feed overflow, care, collect, animal harvest, build, place); workers
    # take the crop lanes (harvest, weed, fertilize, PLANT). Each class
    # overflows to the other only when its own queue is empty. This is the
    # labor division the $140k bots run, with a job board instead of routes.
    pickup_animal_jobs = 0
    # planting push, throttled by watering backlog (no planting into a
    # watering crisis — that is how crops weed out)
    _uw = ctx.get("urgent_water_count", 0)
    if _uw >= max(5, n_units - 3):
        _plant_bump = 0
    elif ctx.get("crop_count", 0) < 26 and day <= 25:
        _plant_bump = 3
    else:
        _plant_bump = 2 if fill_boost else 0
    jobs_p2 = sorted(jobs_sorted,
                     key=lambda j: (j["tier"] - (_plant_bump
                                                 if j["act"][0] == "PLANT" else 0)))
    animal_q = [j for j in jobs_p2 if j.get("cls") == "animal" and j["tier"] >= 3]
    crop_q = [j for j in jobs_p2 if j.get("cls") == "crop" and j["tier"] >= 3]
    other_q = [j for j in jobs_p2 if j.get("cls") not in ("animal", "crop")
               and j["tier"] >= 3 and not j.get("pickup_animal")]
    tender_ids = tenders

    def assign_from(queue, preferred, fallback):
        nonlocal pickup_animal_jobs
        for j in queue:
            if j["key"] in claimed:
                continue
            free = [u for u in units if u["idx"] not in assigned]
            if not free:
                return
            if j["act"][0] == "PLANT":
                crop = j.get("seed")
                if seed_budget.get(crop, 0) <= 0:
                    continue
            if j.get("pickup_animal"):
                if pickup_animal_jobs >= 2:
                    continue
                pickup_animal_jobs += 1
                cands = [u for u in free if u["idx"] in preferred] or free
                u = min(cands, key=lambda u: _shed_dist(u["pos"]))
                if _shed_dist(u["pos"]) == 0:
                    kind = next((k for k in ("COW", "SHEEP", "GOOSE")
                                 if shed.get(k, 0) > 0), None)
                    assigned[u["idx"]] = ["PICKUP", kind, 1] if kind else ["PASS"]
                else:
                    t, _ = _nearest(u["pos"], SHED_TILES)
                    assigned[u["idx"]] = _move_toward(u["pos"], t)
                claimed.add(j["key"])
                continue
            pref = [u for u in free if u["idx"] in preferred]
            pool = pref or [u for u in free if u["idx"] in fallback] or free

            def score(u):
                d = _manhattan(u["pos"], j["pos"])
                if carrying_nonwheat(u) and j["act"][0] not in ("HARVEST",):
                    d += 6
                return d
            u = min(pool, key=score)
            if not pref and score(u) >= 16 and j["tier"] >= 4:
                continue  # don't cross the farm for routine chores
            if j["act"][0] == "PLANT":
                seed_budget[j.get("seed")] -= 1
            take_job(u, j)

    # 1) house waiting animals, 2) tenders sweep the animal corridor,
    # 3) everyone left sweeps their CROP LANE — serpentine routes, working
    #    every tile they stand on (the live-winners' 58-waterings/day trick).
    worker_ids = set(u["idx"] for u in units) - tender_ids
    place_q = [j for j in jobs_p2 if j.get("pickup_animal")]
    assign_from(place_q, tender_ids, set())
    assign_from(animal_q, tender_ids, set())
    assign_from(crop_q, worker_ids, set())
    leftover_crop = [j for j in jobs_p2 if j["tier"] >= 3
                     and j["key"] not in claimed and j.get("cls") == "crop"]
    leftover_animal = [j for j in jobs_p2 if j["tier"] >= 3
                       and j["key"] not in claimed and j.get("cls") == "animal"]
    assign_from(leftover_crop, worker_ids, tender_ids)
    assign_from(leftover_animal, tender_ids, worker_ids)
    assign_from(other_q, set(u["idx"] for u in units), set())

    # Pass 3: logistics for units with no job.
    for u in units:
        if u["idx"] in assigned:
            continue
        inv = u["inv"]
        carry = [(k, v) for k, v in inv.items() if v > 0]
        if carry and any(k != "WHEAT" for k, v in carry):
            if _shed_dist(u["pos"]) == 0:
                assigned[u["idx"]] = ["DROP"]
            else:
                t, _ = _nearest(u["pos"], SHED_TILES)
                assigned[u["idx"]] = _move_toward(u["pos"], t)
            continue
        if emergency_feed and shed.get("WHEAT", 0) > 0 and not carry:
            assigned[u["idx"]] = _pickup_or_move(u, "WHEAT", 4)
            continue
        assigned[u["idx"]] = ["PASS"]

    # Track fertilizer actually spent (FERTILIZE actions issued this turn)
    for idx, a in assigned.items():
        if a and a[0] == "FERTILIZE":
            MEM["fert_spent_on_melons"] += 1

    farmer_act = assigned.get(0, ["PASS"])
    hand_acts = [assigned.get(i + 1, ["PASS"]) for i in range(len(farm.get("hands") or []))]
    return farmer_act, hand_acts


def _pickup_or_move(u, item, n):
    if _shed_dist(u["pos"]) == 0:
        return ["PICKUP", item, n]
    t, _ = min(((s, _manhattan(u["pos"], s)) for s in SHED_TILES), key=lambda x: x[1])
    return _move_toward(u["pos"], t)


def _nearest(pos, pts):
    best, bd = None, 10 ** 9
    for p in pts:
        d = _manhattan(pos, p)
        if d < bd:
            best, bd = p, d
    return best, bd


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

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
            oc = 0
            for row in opp.get("tiles", []):
                for t in row:
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        oc += 1
            MEM["opp_crops"] = oc
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
