"""
Kaggriculture v6.1 "Dairy Baron" — animal-first economic engine.

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
    (4, 3), (5, 3), (3, 4), (4, 4),   # NW day 0: 2 sheep + 2 cow
    (2, 4), (5, 2), (6, 3), (6, 4),   # NE / NW as it opens (days 3-9 cows)
    (3, 5), (4, 5), (7, 4), (3, 3),   # SW / fill (sheep + cows)
    (5, 4), (2, 3),                   # remaining cows
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
        market.append(["BUY_PRODUCT", "WHEAT", 5])
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

    # ---- Seed restocks ----
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

    # ---- Buy wheat for feed (keep shed stocked so hands can PICKUP) ----
    animals_now = count_animals(farm)
    wheat = shed.get("WHEAT", 0)
    need = max(0, animals_now + 4 - wheat)
    if need > 0 and cash >= 1:
        market.append(["BUY_PRODUCT", "WHEAT", min(need, 10)])

    # ---- Surplus wheat sell (keep a LARGE buffer; selling feed wheat starves
    # animals under market pressure — winners hold 30-50 wheat) ----
    reserve = int(DNA["feed_reserve"]) + animals_now * 2
    if shed.get("WHEAT", 0) > reserve + 5:
        market.append(["SELL", "WHEAT", shed["WHEAT"] - reserve])

    return market[:10]


# ---------------------------- labor ----------------------------------------
def find_empty_pasture_spot(farm, pos):
    """Find the next corridor spot to build a pasture (empty tile, owned)."""
    for (x, y) in PASTURE_LAYOUT:
        t = tile(farm, x, y)
        if t is None and _quad_of(x, y) in unlocked(farm):
            return (x, y)
    # fallback: any empty owned tile near shed
    spots = [(x, y) for (x, y) in owned_tiles(farm) if tile(farm, x, y) is None]
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

    # ---- 4. On-tile crop actions ----
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

    # ---- 5. Building/placement duty (farmer + hand 0 while animals wait) ----
    if (is_farmer or (unit_idx == 1)) and day <= 12:
        animals_waiting = sum(shed.get(k, 0) for k in ("COW", "SHEEP", "GOOSE"))
        # Don't pull planters off crop work unless animals actually wait or we
        # still need pastures built.
        need_pastures = count_empty_pasture_targets(farm)
        if animals_waiting > 0 and carrying not in ANIMALS:
            if shed_adj(pos):
                for k in ("COW", "SHEEP", "GOOSE"):
                    if shed.get(k, 0) > 0:
                        return ["PICKUP", k, 1]
            t, _ = nearest(pos, SHED_TILES)
            return move_toward(pos, t)
        if is_farmer and need_pastures and here is None:
            spot = find_empty_pasture_spot(farm, pos)
            if spot == tuple(pos):
                return ["BUILD_PASTURE"]
            if spot:
                return move_toward(pos, spot)

    # ---- 6. If animals are unfed, ensure we carry wheat and route to them ----
    if any_unfed(farm):
        if carrying == "WHEAT":
            # Head to a distinct unclaimed unfed animal.
            targets = [
                (xx, yy) for (xx, yy) in owned_tiles(farm)
                if isinstance(tile(farm, xx, yy), dict)
                and tile(farm, xx, yy).get("animal")
                and not tile(farm, xx, yy).get("fed_today")
            ]
            tgt = _claim_target(pos, targets)
            if tgt:
                return move_toward(pos, tgt)
        elif shed.get("WHEAT", 0) > 0:
            if shed_adj(pos):
                return ["PICKUP", "WHEAT", 2]
            t, _ = nearest(pos, SHED_TILES)
            return move_toward(pos, t)
        # No wheat in shed — fall through to other work.

    # ---- 7. Navigate to work ----
    target = choose_target(pos, farm, private, obs, carrying, is_farmer)
    if target:
        return move_toward(pos, target)
    return ["PASS"]


def any_unfed(farm):
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("animal") and not t.get("fed_today"):
                return True
    return False


def choose_target(pos, farm, private, obs, carrying, is_farmer):
    """Pick the nearest important job. Priority:
    1. An unfed animal (if we carry wheat) — feed it.
    2. An animal with fertilizer/care/harvest due.
    3. A thirsty crop.
    4. A mature crop to harvest.
    5. An empty tile to plant.
    6. The shed (to restock wheat / drop goods).
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

    # If not carrying wheat but there are unfed animals, head to shed for wheat.
    if feed and carrying != "WHEAT":
        if any_unfed(farm):
            t, _ = nearest(pos, SHED_TILES)
            return t
    for bucket in (feed, ancare, water, harv, weeds, plant):
        if bucket:
            t, _ = nearest(pos, bucket)
            return t
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


def agent(obs):
    try:
        player = obs.get("player", 0)
        farms = obs.get("farms", []) or []
        if not farms or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        farm = farms[player]
        private = obs.get("private", {}) or {}

        # Reset per-turn coordination (target claiming).
        _TURN_STATE["claimed"] = set()

        market = plan_market(obs, farm, private)

        farmer_pos = tuple(farm.get("farmer", [4, 4]) or [4, 4])
        farmer_action = act_unit(farmer_pos, farm, private, obs, 0, is_farmer=True)

        hand_actions = []
        for i, hpos in enumerate(farm.get("hands") or []):
            hand_actions.append(act_unit(tuple(hpos), farm, private, obs, i + 1, is_farmer=False))

        return {
            "farmer": farmer_action or ["PASS"],
            "hands": hand_actions,
            "market": market[:10],
        }
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}
