"""
Kaggriculture v6.5 "Dairy Baron" — lane routing — animal-first economic engine.

Our own implementation, modeled on the decoded top-player meta:
  - 14 animals: 8 cows + 6 sheep on pastures in a compact corridor around
    the shed, spread across NW + NE + SW (never SE).
  - Land: NE day 7, SW day 11.
  - Day 0: hire 5, buy 2 cows + 2 sheep, 7 wheat seed + 12 melon seed, 5 wheat.
  - Animal ramp: +1 cow d3, +1 cow d5, +2 cow/+2 sheep d7, +2 cow d9, +2 sheep d11.
  - NO dedicated tender. Every hand carries 1-3 wheat and opportunistically FEEDs
    any unfed animal it walks past while routing between crop columns. This is
    exactly how the top bots keep 14 animals alive with one pass per day.
  - Farmer builds/places animals during the opening, then joins the crop/feed loop.
  - Sell milk, wool, fertilizer, melon, strawberry, surplus wheat daily.
  - Crop layout: checkerboard of wheat (feed) and melon in NW; strawberry in
    NE/SW after expansion.

No ML; rule-based autonomous agent.
"""

DEFAULT_DNA = {
    "version": "v6.1",
    "target_cows": 8,
    "target_sheep": 6,
    "buy_ne_day": 7,
    "buy_sw_day": 11,
    "hires_day0": 5,
    "hires_cap": 14,
    "wheat_seed_day0": 7,
    "melon_seed_day0": 12,
    "strawberry_seed_day7": 19,
    "melon_seed_restock_day11": 12,
    "strawberry_seed_restock_day11": 23,
    "milk_sell": 90,
    "wool_sell": 120,
    "fertilizer_sell": 40,
    "melon_sell": 140,
    "strawberry_sell": 80,
    "wheat_sell": 16,
    "feed_reserve": 20,
    "use_brain": 0,
}


def _load_dna():
    import json, os
    dna = dict(DEFAULT_DNA)
    here = os.getcwd()
    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        pass
    for p in [os.path.join(here, "dna_v6.json"), "Agent/dna_v6.json", "dna_v6.json"]:
        try:
            if os.path.exists(p):
                dna.update(json.load(open(p)))
                break
        except Exception:
            pass
    return dna


DNA = _load_dna()

# ---------------------------------------------------------------------------
# v6.6 strict lane routing (Nosiru's trial designs). Each worker follows an
# ordered route and only acts on its current tile; no diversion.
# ---------------------------------------------------------------------------
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
try:
    import routes as _R
except Exception:  # routes.py lives alongside; tolerate import quirks
    _R = None
TRIAL = _os.environ.get("KK_TRIAL", "trial01")

# Per-turn progress per worker: map (worker_key) -> index in its route.
_ROUTE_POS = {}

ANIMALS = {"COW", "SHEEP", "GOOSE"}
ANIMAL_STRUCT = {"COW": "PASTURE", "SHEEP": "PASTURE", "GOOSE": "COOP"}
ANIMAL_COST = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
CROP_FIRST_YIELD = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
QUAD_TILES = {
    "NW": [(x, y) for y in range(0, 5) for x in range(0, 5)],
    "NE": [(x, y) for y in range(0, 5) for x in range(5, 10)],
    "SW": [(x, y) for y in range(5, 10) for x in range(0, 5)],
    "SE": [(x, y) for y in range(5, 10) for x in range(5, 10)],
}

# Compact pasture corridor target positions (built in this order). Mirrors the
# top bots: NW first (4 animals around shed), then NE row 3/4, then SW row 5.
PASTURE_LAYOUT = [
    # Day 0: build 6 NW pastures in a tight 2x3 block around the shed
    # (rows 3-4, cols 2-4). All within 3 tiles of shed = feedable day 1.
    (3, 4), (4, 4), (3, 3), (4, 3), (2, 4), (2, 3),
    # NE expansion (rows 3-4, cols 5-7) after day 7.
    (5, 3), (6, 3), (5, 4), (6, 4), (7, 4), (7, 3),
    # SW (rows 5-6) after day 11.
    (3, 5), (4, 5), (5, 5), (2, 5),
]


# ---------------------------- utilities ------------------------------------
def tile(farm, x, y):
    try:
        return farm["tiles"][y][x]
    except Exception:
        return None


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def move_toward(pos, target):
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    if dx == 0 and dy == 0:
        return ["PASS"]
    if abs(dx) >= abs(dy):
        return ["EAST"] if dx > 0 else ["WEST"]
    return ["SOUTH"] if dy > 0 else ["NORTH"]


def nearest(pos, targets):
    best, bd = None, 10**9
    for t in targets:
        d = manhattan(pos, t)
        if d < bd:
            best, bd = t, d
    return best, bd


def shed_adj(pos):
    return tuple(pos) in set(SHED_TILES)


def unlocked(farm):
    return set(farm.get("unlocked_quadrants") or ["NW"])


def owned_tiles(farm):
    for q in unlocked(farm):
        for p in QUAD_TILES[q]:
            yield p


def count_animals(farm):
    return sum(
        1 for row in farm["tiles"] for t in row
        if isinstance(t, dict) and t.get("animal") in ANIMALS
    )


def count_kind(farm, kind):
    return sum(
        1 for row in farm["tiles"] for t in row
        if isinstance(t, dict) and t.get("animal") == kind
    )


def inv_get(private, item, idx):
    invs = private.get("inventories", []) or []
    if idx < len(invs):
        return (invs[idx] or {}).get(item, 0)
    return 0


def inv_carrying(private, idx):
    invs = private.get("inventories", []) or []
    if idx < len(invs):
        for k, v in (invs[idx] or {}).items():
            if v:
                return k, v
    return None, 0



# ---------------------------- v6.5 crop-lane routing ----------------------
# Borrowed from v5.8z5f's proven coverage: 2 hands per unlocked quadrant,
# each sweeping two columns. This gives 40-55 crops vs v6.3's 7-10.

def _active_quads(farm):
    """Quads in unlock order."""
    u = unlocked(farm)
    return [q for q in ("NW", "NE", "SW", "SE") if q in u]


def _quad_sector(q, board_size=10):
    h = board_size // 2
    if q == "NW": return (0, h - 1, 0, h - 1)
    if q == "NE": return (h, board_size - 1, 0, h - 1)
    if q == "SW": return (0, h - 1, h, board_size - 1)
    return (h, board_size - 1, h, board_size - 1)


def worker_quadrant(idx, farm):
    """Hands 1-2 are animal tenders. Hands 3+ are crop workers: 2 per
    active quadrant, lane = (idx-3) % 2."""
    if idx <= 2:
        return None
    quads = _active_quads(farm)
    if not quads:
        return "NW"
    return quads[((idx - 3) // 2) % len(quads)]


def _lane_local_path(lane, h):
    """Two strict routes over a quadrant's 4 usable columns.
    lane 0 = shed-side cols 0-1; lane 1 = outer cols 2-3. Far/fence col ignored."""
    if h <= 2:
        return [(0, 0)]
    max_work_col = h - 2
    if lane == 0:
        pts = [(0, ay) for ay in range(h)]
        if max_work_col >= 1:
            pts += [(1, ay) for ay in range(h - 1, -1, -1)]
        return pts
    c1 = min(2, max_work_col)
    c2 = max_work_col
    pts = [(ax, 0) for ax in range(c1 + 1)]
    pts += [(c1, ay) for ay in range(1, h)]
    if c2 > c1:
        pts.append((c2, h - 1))
        pts += [(c2, ay) for ay in range(h - 2, -1, -1)]
    return list(dict.fromkeys(pts))


def _local_to_global(q, lx, ly, board_size=10):
    h = board_size // 2
    if q == "NW": return (h - 1 - lx, h - 1 - ly)
    if q == "NE": return (h + lx, h - 1 - ly)
    if q == "SW": return (h - 1 - lx, h + ly)
    return (h + lx, h + ly)


def worker_route(idx, farm, board_size=10):
    """Ordered list of global tiles this hand patrols (planters only)."""
    q = worker_quadrant(idx, farm)
    if q is None:
        return []
    lane = (idx - 3) % 2
    h = board_size // 2
    return [_local_to_global(q, lx, ly, board_size) for lx, ly in _lane_local_path(lane, h)]


def route_order(idx, pos, target, farm, board_size=10):
    """How far along the hand's route target is (low = next). Off-route penalized."""
    if idx <= 0:
        return manhattan(pos, target)
    path = worker_route(idx, farm, board_size)
    if not path:
        return manhattan(pos, target)
    cur_i = min(range(len(path)), key=lambda i: manhattan(pos, path[i]))
    try:
        tgt_i = path.index(tuple(target))
    except ValueError:
        return 1000 + manhattan(pos, target)
    if tgt_i >= cur_i:
        return tgt_i - cur_i
    return (len(path) - cur_i) + tgt_i + 20


def in_worker_quad(idx, target, farm, board_size=10):
    if idx <= 2:
        return True
    q = worker_quadrant(idx, farm)
    sector = _quad_sector(q, board_size)
    if sector is None:
        return True
    x0, x1, y0, y1 = sector
    return x0 <= target[0] <= x1 and y0 <= target[1] <= y1



# ---------------------------- market ---------------------------------------
def plan_market(obs, farm, private):
    market = []
    day = obs.get("day", 0)
    hour = obs.get("hour", 0)
    cash = float(farm.get("money", 0))
    seeds = private.get("seeds", {}) or {}
    shed = private.get("shed", {}) or {}
    prices = (obs.get("market", {}) or {}).get("prices", {}) or {}

    # Hour 0 is observation/setup; the first real action is hour 1. Do nothing
    # at hour 0 (the top bots PASS here; hiring at hour 0 wastes the budget
    # before the opening orders).
    if hour == 0 and day == 0:
        return []

    if day == 0 and hour == 1:
        for _ in range(int(DNA["hires_day0"])):
            market.append(["HIRE"])
        market.append(["BUY_ANIMAL", "SHEEP", 2])
        market.append(["BUY_ANIMAL", "COW", 2])
        if seeds.get("WHEAT", 0) < 7:
            market.append(["BUY_SEED", "WHEAT", 7])
        if seeds.get("MELON", 0) < 12:
            market.append(["BUY_SEED", "MELON", 12])
        market.append(["BUY_PRODUCT", "WHEAT", 12])
        return market

    # ---- SELL first (cash in) ----
    def sell(item, gate):
        n = shed.get(item, 0)
        if n <= 0:
            return
        p = prices.get(item, 0) or 0
        if day >= 28 or p >= gate:
            market.append(["SELL", item, n])

    sell("MILK", int(DNA["milk_sell"]))
    sell("WOOL", int(DNA["wool_sell"]))
    sell("MELON", int(DNA["melon_sell"]))
    sell("STRAWBERRY", int(DNA["strawberry_sell"]))
    if shed.get("FERTILIZER", 0) > 2:
        market.append(["SELL", "FERTILIZER", shed["FERTILIZER"] - 2])

    # ---- Land (highest priority capital expense) ----
    if day == int(DNA["buy_ne_day"]) and "NE" not in unlocked(farm) and cash >= 1000:
        market.append(["BUY_LAND"])
        cash -= 1000
    if day == int(DNA["buy_sw_day"]) and "SW" not in unlocked(farm) and cash >= 2000:
        market.append(["BUY_LAND"])
        cash -= 2000

    # ---- Hires (at least 2/day; keep expansion days hiring) ----
    fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]
    hands = len(farm.get("hands") or [])
    hires_today = farm.get("hires_today", 0) or 0
    already = sum(1 for m in market if m and m[0] == "HIRE")
    committed = hires_today + already
    want = int(DNA["hires_cap"])
    cost = sum(fib[hires_today + k] for k in range(already))
    added = 0
    while hands + committed + added < want and (committed + added) < len(fib):
        c = fib[committed + added]
        if cost + c > cash:
            break
        cost += c
        market.append(["HIRE"])
        added += 1

    # ---- Animals on schedule (after land + hires so they don't starve them,
    #      but only if budget remains) ----
    cows = count_kind(farm, "COW") + shed.get("COW", 0)
    sheep = count_kind(farm, "SHEEP") + shed.get("SHEEP", 0)
    tmap = {"COW": int(DNA["target_cows"]), "SHEEP": int(DNA["target_sheep"])}
    hmap = {"COW": cows, "SHEEP": sheep}

    def schedule_buy(kind, qty, dc):
        nonlocal cash
        if day != dc:
            return
        want_qty = max(0, min(qty, tmap[kind] - hmap[kind]))
        if want_qty > 0 and cash >= ANIMAL_COST[kind] * want_qty + 20:
            market.append(["BUY_ANIMAL", kind, want_qty])
            cash -= ANIMAL_COST[kind] * want_qty

    schedule_buy("COW", 1, 3)
    schedule_buy("COW", 1, 5)
    schedule_buy("COW", 2, 7)
    schedule_buy("SHEEP", 2, 7)
    schedule_buy("COW", 2, 9)
    schedule_buy("SHEEP", 2, 11)

    # ---- Seed restocks (hour 1 ONLY — otherwise it re-buys every hour
    # and burns cash on hundreds of unused seeds) ----
    if hour == 1:
        if day == 7 and seeds.get("STRAWBERRY", 0) < int(DNA["strawberry_seed_day7"]):
            n = int(DNA["strawberry_seed_day7"]) - seeds.get("STRAWBERRY", 0)
            market.append(["BUY_SEED", "STRAWBERRY", n])
        if day == 11:
            mw = int(DNA["melon_seed_restock_day11"])
            sw = int(DNA["strawberry_seed_restock_day11"])
            if seeds.get("MELON", 0) < mw:
                market.append(["BUY_SEED", "MELON", mw - seeds.get("MELON", 0)])
            if seeds.get("STRAWBERRY", 0) < sw:
                market.append(["BUY_SEED", "STRAWBERRY", sw - seeds.get("STRAWBERRY", 0)])
        if day in (4, 8, 12, 16, 20, 24, 28):
            if seeds.get("WHEAT", 0) < 7:
                market.append(["BUY_SEED", "WHEAT", 7 - seeds.get("WHEAT", 0)])

    # ---- Buy wheat for feed. Buy a chunk at hour 1; top up later only
    # when animals are actually unfed (so expansion days don't starve). ----
    animals_now = count_animals(farm)
    wheat = shed.get("WHEAT", 0)
    need = max(0, animals_now + 6 - wheat)
    if hour == 1 and need > 0 and cash >= 1:
        market.append(["BUY_PRODUCT", "WHEAT", min(need, 14)])
    elif any_unfed(farm) and wheat < animals_now and cash >= 1:
        market.append(["BUY_PRODUCT", "WHEAT", min(need, 6)])

    # ---- Surplus wheat sell (keep a LARGE buffer; selling feed wheat starves
    # animals under market pressure — winners hold 30-50 wheat) ----
    reserve = int(DNA["feed_reserve"]) + animals_now * 2
    if shed.get("WHEAT", 0) > reserve + 5:
        market.append(["SELL", "WHEAT", shed["WHEAT"] - reserve])

    return market[:10]


# ---------------------------- labor ----------------------------------------
def find_empty_pasture_spot(farm, pos, allow_fallback=True):
    """Find the next corridor spot to build. Uses PASTURE_LAYOUT; only
    falls back to a <=3-tile empty tile if allow_fallback (never on day 0,
    where a far pasture causes an animal to starve)."""
    for (x, y) in PASTURE_LAYOUT:
        t = tile(farm, x, y)
        if t is None and _quad_of(x, y) in unlocked(farm):
            return (x, y)
    if not allow_fallback:
        return None
    spots = [(x, y) for (x, y) in owned_tiles(farm)
             if tile(farm, x, y) is None
             and min(manhattan((x, y), s) for s in SHED_TILES) <= 3]
    if spots:
        spots.sort(key=lambda p: (min(manhattan(p, s) for s in SHED_TILES), manhattan(p, pos)))
        return spots[0]
    return None


def count_empty_pasture_targets(farm):
    """How many corridor pasture spots still need to be built."""
    n = 0
    for (x, y) in PASTURE_LAYOUT:
        if _quad_of(x, y) in unlocked(farm):
            t = tile(farm, x, y)
            if t is None:
                n += 1
    return n


def find_empty_pasture_for_animal(farm):
    """Find an empty existing pasture to place an animal on, nearest shed."""
    spots = []
    for (x, y) in owned_tiles(farm):
        t = tile(farm, x, y)
        if isinstance(t, dict) and t.get("kind") == "PASTURE" and "animal" not in t:
            spots.append((x, y))
    spots.sort(key=lambda p: (min(manhattan(p, s) for s in SHED_TILES), p))
    return spots[0] if spots else None


def _quad_of(x, y):
    if x < 5 and y < 5:
        return "NW"
    if x >= 5 and y < 5:
        return "NE"
    if x < 5 and y >= 5:
        return "SW"
    return "SE"


def act_unit(pos, farm, private, obs, unit_idx, is_farmer):
    """One action for any unit. The top bots use opportunistic feeding: every
    hand carries wheat and feeds animals it crosses while doing crop work."""
    day = obs.get("day", 0)
    x, y = pos
    here = tile(farm, x, y)
    carrying, qty = inv_carrying(private, unit_idx)
    seeds = private.get("seeds", {}) or {}
    shed = private.get("shed", {}) or {}

    # ---- 0. If carrying an animal (farmer/hand during opening), place it ----
    if carrying in ANIMALS and qty > 0:
        struct = ANIMAL_STRUCT[carrying]
        if isinstance(here, dict) and here.get("kind") == struct and "animal" not in here:
            return ["PLACE", carrying]
        if here is None:
            return ["BUILD_PASTURE"] if struct == "PASTURE" else ["BUILD_COOP"]
        spot = find_empty_pasture_for_animal(farm) or find_empty_pasture_spot(farm, pos)
        return move_toward(pos, spot) if spot else ["PASS"]

    # ---- 1. Drop any non-wheat product at shed (so it can sell) ----
    if carrying and carrying != "WHEAT" and carrying not in ANIMALS and qty > 0:
        if shed_adj(pos):
            return ["DROP"]
        t, _ = nearest(pos, SHED_TILES)
        return move_toward(pos, t)

    # ---- 2. FEED is the top on-animal priority (prevents escapes) ----
    if (isinstance(here, dict) and here.get("animal")
            and not here.get("fed_today") and carrying == "WHEAT"):
        return ["FEED"]

    # ---- 3. On-tile animal care ----
    if isinstance(here, dict) and here.get("animal"):
        if here.get("fertilizer_available"):
            return ["COLLECT_FERTILIZER"]
        if not here.get("cared_today"):
            return ["CARE"]
        if here.get("yield_units", 0) > 0:
            return ["HARVEST"]

    # ---- 4. On-tile crop actions. Farmer is a dedicated tender and never
    # crops. Planters only act within their assigned quadrant lane. Planters
    # also feed opportunistically (handled in section 2). ----
    planter = (not is_farmer) and unit_idx >= 3
    in_my_quad = (not planter) or in_worker_quad(unit_idx, (x, y), farm)
    if in_my_quad:
        if isinstance(here, dict) and here.get("kind") == "PLANT":
            if not here.get("watered_today"):
                return ["WATER"]
            if here.get("yield_units", 0) > 0:
                age = day - here.get("planted_day", day)
                if age >= CROP_FIRST_YIELD.get(here.get("crop"), 2):
                    return ["HARVEST"]
        if isinstance(here, dict) and here.get("kind") == "WEED":
            return ["DIG"]
        if here is None and day < 26:
            crop = choose_crop(x, y, day, seeds, farm)
            if crop:
                return ["PLANT", crop]

    # ---- 5. Building/placement (farmer + hand0 build/places animals) ----
    if day <= 12 and (is_farmer or unit_idx == 1):
        animals_waiting = sum(shed.get(k, 0) for k in ("COW", "SHEEP", "GOOSE"))
        empty_past = find_empty_pasture_for_animal(farm)
        # If animals wait but no empty pasture exists, build one.
        if animals_waiting > 0 and empty_past is None and here is None:
            spot = find_empty_pasture_spot(farm, pos)
            if spot == tuple(pos):
                return ["BUILD_PASTURE"]
            if spot:
                return move_toward(pos, spot)
        if animals_waiting > 0 and carrying not in ANIMALS:
            if shed_adj(pos):
                for k in ("COW", "SHEEP", "GOOSE"):
                    if shed.get(k, 0) > 0:
                        return ["PICKUP", k, 1]
            t, _ = nearest(pos, SHED_TILES)
            return move_toward(pos, t)
        # Proactively build planned corridor pastures (farmer).
        if is_farmer and here is None:
            spot = find_empty_pasture_spot(farm, pos)
            if spot == tuple(pos):
                return ["BUILD_PASTURE"]
            if spot:
                return move_toward(pos, spot)

    # ---- 6. Tenders (farmer idx 0 + hands 1-2) always route to unfed
    # animals and carry a big stack of wheat (5) so they make fewer shed
    # trips. Planters (idx 3+) only divert when they ALREADY carry wheat
    # AND there are more unfed animals than the 3 tenders can handle this
    # pass — this keeps crop workers filling their lanes instead of all
    # abandoning crops (the v6.5 fill bug). ----
    if any_unfed(farm):
        n_unfed = sum(1 for (xx, yy) in owned_tiles(farm)
                      if isinstance(tile(farm, xx, yy), dict)
                      and tile(farm, xx, yy).get("animal")
                      and not tile(farm, xx, yy).get("fed_today"))
        is_tender = (unit_idx <= 2)
        # Planter helps only if already holding wheat and animals are backed up.
        planter_helps = (unit_idx >= 3 and carrying == "WHEAT" and n_unfed >= 4)
        if carrying == "WHEAT" and (is_tender or planter_helps):
            targets = [
                (xx, yy) for (xx, yy) in owned_tiles(farm)
                if isinstance(tile(farm, xx, yy), dict)
                and tile(farm, xx, yy).get("animal")
                and not tile(farm, xx, yy).get("fed_today")
            ]
            tgt = _claim_target(pos, targets)
            if tgt:
                return move_toward(pos, tgt)
        elif is_tender and shed.get("WHEAT", 0) > 0:
            if shed_adj(pos):
                # Tenders carry 5 wheat to minimize trips back to the shed.
                return ["PICKUP", "WHEAT", 5]
            t, _ = nearest(pos, SHED_TILES)
            return move_toward(pos, t)
        # Otherwise fall through to crop work (fill those plots!).

    # ---- 7. Navigate to work ----
    target = choose_target(pos, farm, private, obs, carrying, is_farmer, unit_idx)
    if target:
        return move_toward(pos, target)
    return ["PASS"]


def any_unfed(farm):
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("animal") and not t.get("fed_today"):
                return True
    return False


def choose_target(pos, farm, private, obs, carrying, is_farmer, hand_idx=0):
    """v6.5: route-aware target picker.

    For farmer/tender (hand_idx 0): pick nearest job (animals first).
    For planters (hand_idx >= 1): prefer jobs on their assigned quadrant lane,
    scored by route order so they sweep columns instead of all converging.
    """
    day = obs.get("day", 0)
    seeds = private.get("seeds", {}) or {}

    feed, ancare, water, harv, weeds, plant = [], [], [], [], [], []
    for (x, y) in owned_tiles(farm):
        t = tile(farm, x, y)
        if isinstance(t, dict):
            if t.get("animal"):
                if not t.get("fed_today") and carrying == "WHEAT":
                    feed.append((x, y))
                elif t.get("fertilizer_available") or not t.get("cared_today") or t.get("yield_units", 0) > 0:
                    ancare.append((x, y))
            elif t.get("kind") == "PLANT":
                if not t.get("watered_today"):
                    water.append((x, y))
                elif t.get("yield_units", 0) > 0 and (day - t.get("planted_day", day)) >= CROP_FIRST_YIELD.get(t.get("crop"), 2):
                    harv.append((x, y))
        elif t is not None and t.get("kind") == "WEED":
            weeds.append((x, y))
        elif t is None and day < 26 and any(seeds.get(c, 0) > 0 for c in ("WHEAT", "MELON", "STRAWBERRY")):
            plant.append((x, y))

    # Tender/farmer: nearest job, animals first.
    if hand_idx <= 2 or is_farmer:
        if feed and carrying != "WHEAT" and any_unfed(farm):
            t, _ = nearest(pos, SHED_TILES)
            return t
        for bucket in (feed, ancare, water, harv, weeds, plant):
            if bucket:
                t, _ = nearest(pos, bucket)
                return t
        return None

    # Planter: route-aware. Score each candidate by (in-quad bonus, route order).
    def score(cand):
        in_q = in_worker_quad(hand_idx, cand, farm)
        ro = route_order(hand_idx, pos, cand, farm)
        # Off-quadrant jobs heavily penalized but allowed if quad is empty.
        return (0 if in_q else 500) + ro

    if feed and carrying != "WHEAT" and any_unfed(farm):
        t, _ = nearest(pos, SHED_TILES)
        return t
    # When animals are fed/cared for, clear weeds before watering so tiles
    # can be replanted. If there are unfed animals, water first (crops die fast).
    if any_unfed(farm):
        order = (feed, ancare, water, harv, weeds, plant)
    else:
        order = (feed, ancare, harv, weeds, water, plant)
    for bucket in order:
        if bucket:
            cand = min(bucket, key=lambda c: score(c))
            if score(cand) < 800:
                return cand
    return None


def choose_crop(x, y, day, seeds, farm):
    if day >= 25:
        return None
    # Wheat near shed (feed crop).
    d = min(manhattan((x, y), s) for s in SHED_TILES)
    if d <= 1 and seeds.get("WHEAT", 0) > 0:
        return "WHEAT"
    if day <= 12 and seeds.get("MELON", 0) > 0:
        return "MELON"
    if day >= 7 and seeds.get("STRAWBERRY", 0) > 0 and d <= 5:
        return "STRAWBERRY"
    if seeds.get("WHEAT", 0) > 0:
        return "WHEAT"
    if seeds.get("MELON", 0) > 0:
        return "MELON"
    if seeds.get("STRAWBERRY", 0) > 0:
        return "STRAWBERRY"
    return None


# ---------------------------- main -----------------------------------------
_TURN_STATE = {"claimed": set()}


def _claim_target(pos, candidates):
    """Pick the nearest candidate not already claimed by another unit this turn."""
    claimed = _TURN_STATE["claimed"]
    avail = [c for c in candidates if c not in claimed] or list(candidates)
    if not avail:
        return None
    avail.sort(key=lambda c: manhattan(pos, c))
    choice = avail[0]
    claimed.add(choice)
    return choice



def _route_for_unit(unit_idx, farm):
    """Return this unit's ordered global route (or None if unassigned)."""
    if _R is None:
        return None
    active = [q for q in ("NW", "NE", "SW", "SE") if q in unlocked(farm)]
    if not active:
        active = ["NW"]
    all_routes, _ = _R.all_worker_routes(TRIAL, active)
    if not all_routes:
        return None
    return all_routes[unit_idx % len(all_routes)]


def _act_on_tile(pos, farm, private, obs, carrying, qty, unit_idx, is_farmer, seeds, day):
    """Perform the action needed on the current tile (if any); else None."""
    x, y = pos
    here = tile(farm, x, y)

    # Carrying an animal to place: place on an empty pasture here.
    if carrying in ANIMALS and qty > 0:
        if isinstance(here, dict) and here.get("kind") == "PASTURE" and "animal" not in here:
            return ["PLACE", carrying]
        # Need a pasture; if this tile is empty and on the animal route, build.
        if here is None and is_farmer:
            return ["BUILD_PASTURE"]

    # Drop a carried non-feed product at the shed.
    if carrying and carrying != "WHEAT" and carrying not in ANIMALS and qty > 0:
        if shed_adj(pos):
            return ["DROP"]

    # Animal on this tile: FEED (if wheat), then collect/care/harvest.
    if isinstance(here, dict) and here.get("animal"):
        if not here.get("fed_today") and carrying == "WHEAT":
            return ["FEED"]
        if here.get("fertilizer_available"):
            return ["COLLECT_FERTILIZER"]
        if not here.get("cared_today"):
            return ["CARE"]
        if here.get("yield_units", 0) > 0:
            return ["HARVEST"]

    # Crop on this tile: water, harvest.
    if isinstance(here, dict) and here.get("kind") == "PLANT":
        if not here.get("watered_today"):
            return ["WATER"]
        if here.get("yield_units", 0) > 0:
            age = day - here.get("planted_day", day)
            if age >= CROP_FIRST_YIELD.get(here.get("crop"), 2):
                return ["HARVEST"]

    # Weed: clear it.
    if isinstance(here, dict) and here.get("kind") == "WEED":
        return ["DIG"]

    # Empty: plant if we have seed and the route expects a crop here.
    if here is None and day < 26:
        # Don't plant on the animal L-corridor (grass stays for pasture path).
        on_animal_route = _is_animal_tile(pos, farm)
        if not on_animal_route:
            crop = choose_crop(x, y, day, seeds, farm)
            if crop:
                return ["PLANT", crop]
    return None


def _is_animal_tile(pos, farm):
    """True if this position is on a red animal L-route in its quadrant."""
    if _R is None:
        return False
    x, y = pos
    for q in ("NW", "NE", "SW", "SE"):
        if q not in unlocked(farm):
            continue
        routes, names = _R.all_worker_routes(TRIAL, [q])
        if not routes:
            continue
        # The "red" route is the first route per quadrant (animal L).
        red = routes[0]
        if tuple(pos) in [tuple(p) for p in red]:
            return True
    return False


def _next_route_step(unit_idx, pos, farm):
    """Advance this unit's route index to the next tile that still needs
    work; return the next target position (or pos if route finished)."""
    route = _route_for_unit(unit_idx, farm)
    if not route:
        return None
    key = unit_idx
    i = _ROUTE_POS.get(key, 0) % len(route)
    # If we're at the current target, advance.
    if tuple(pos) == tuple(route[i]):
        i = (i + 1) % len(route)
    _ROUTE_POS[key] = i
    return route[i]


def agent(obs):
    try:
        player = obs.get("player", 0)
        farms = obs.get("farms", []) or []
        if not farms or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        farm = farms[player]
        private = obs.get("private", {}) or {}
        day = obs.get("day", 0)
        seeds = private.get("seeds", {}) or {}

        # Reset per-turn coordination.
        _TURN_STATE["claimed"] = set()

        market = plan_market(obs, farm, private)

        farmer_pos = tuple(farm.get("farmer", [4, 4]) or [4, 4])

        # ---- v6.6 strict routes ----
        # The farmer places animals/builds pastures early; after the opening
        # it joins route 0. Hands follow their assigned strict routes.
        def unit_action(pos, unit_idx, is_farmer):
            carrying, qty = inv_carrying(private, unit_idx)
            # 1. Opening build/place (farmer + hand0 on day 0-12).
            if day <= 12 and (is_farmer or unit_idx == 1):
                a = _opening_build_place(pos, farm, private, obs, unit_idx,
                                         is_farmer, carrying)
                if a:
                    return a
            # 2. Grab wheat at shed if empty-handed and route needs feed.
            if carrying != "WHEAT" and shed.get("WHEAT", 0) > 0 and _route_has_animals(unit_idx, farm):
                if shed_adj(pos):
                    return ["PICKUP", "WHEAT", 5]
                t, _ = nearest(pos, SHED_TILES)
                return move_toward(pos, t)
            # 3. Strict route: act on current tile if it needs something.
            a = _act_on_tile(pos, farm, private, obs, carrying, qty,
                              unit_idx, is_farmer, seeds, day)
            if a:
                return a
            # 4. Tile is clear — advance to the next route point.
            nxt = _next_route_step(unit_idx, pos, farm)
            if nxt and tuple(nxt) != tuple(pos):
                return move_toward(pos, nxt)
            return ["PASS"]

        shed = private.get("shed", {}) or {}
        farmer_action = unit_action(farmer_pos, 0, True)
        hand_actions = []
        for i, hpos in enumerate(farm.get("hands") or []):
            hand_actions.append(unit_action(tuple(hpos), i + 1, False))

        return {
            "farmer": farmer_action or ["PASS"],
            "hands": hand_actions,
            "market": market[:10],
        }
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}


def _route_has_animals(unit_idx, farm):
    route = _route_for_unit(unit_idx, farm)
    if not route or _R is None:
        return False
    rset = set(tuple(p) for p in route)
    for (x, y) in rset:
        t = tile(farm, x, y)
        if isinstance(t, dict) and t.get("animal"):
            return True
    return False


def _opening_build_place(pos, farm, private, obs, unit_idx, is_farmer, carrying):
    """Day 0-12: farmer builds the red-route pastures (in order); all units
    place waiting animals onto empty pastures. Then strict routing takes over."""
    day = obs.get("day", 0)
    shed = private.get("shed", {}) or {}
    here = tile(farm, *pos)
    animals_waiting = sum(shed.get(k, 0) for k in ("COW", "SHEEP", "GOOSE"))

    # Build: farmer standing on an unbuilt red-route tile builds a pasture.
    if is_farmer and here is None and _is_animal_tile(pos, farm):
        return ["BUILD_PASTURE"]

    # Place a carried animal on the nearest empty pasture.
    if carrying in ANIMALS:
        spot = find_empty_pasture_for_animal(farm)
        if spot == tuple(pos):
            return ["PLACE", carrying]
        if spot:
            return move_toward(pos, spot)
        # No empty pasture: if farmer, go build the next red-route tile.
        if is_farmer:
            for (x, y) in _planned_animal_pastures(farm):
                if tile(farm, x, y) is None:
                    if (x, y) == tuple(pos):
                        return ["BUILD_PASTURE"]
                    return move_toward(pos, (x, y))

    # Pick up a waiting animal from the shed (farmer + hand0).
    if animals_waiting > 0 and carrying not in ANIMALS and (is_farmer or unit_idx == 1):
        if shed_adj(pos):
            for k in ("COW", "SHEEP", "GOOSE"):
                if shed.get(k, 0) > 0:
                    return ["PICKUP", k, 1]
        t, _ = nearest(pos, SHED_TILES)
        return move_toward(pos, t)

    # Farmer: proactively walk to & build the next unbuilt red-route pasture.
    if is_farmer:
        for (x, y) in _planned_animal_pastures(farm):
            if tile(farm, x, y) is None:
                if (x, y) == tuple(pos):
                    return ["BUILD_PASTURE"]
                return move_toward(pos, (x, y))
    return None


def _planned_animal_pastures(farm):
    """All red-route animal positions across active quads (build order)."""
    if _R is None:
        return []
    out = []
    for q in ("NW", "NE", "SW", "SE"):
        if q not in unlocked(farm):
            continue
        routes, _ = _R.all_worker_routes(TRIAL, [q])
        if routes:
            for p in routes[0]:
                out.append(tuple(p))
    return out
