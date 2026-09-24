"""
Kaggriculture v5.8z — trimmed-side 2-hand route test.

Design goals:
  - No idle animal/barn routine. This version is crop-first.
  - Hire a big crew from turn 0, assign workers to sectors, and route them on different lanes.
  - Buy land only early enough to use it; never buy a late quadrant that cannot pay back.
  - Seed scheduler buys just-in-time: enough seed for empty plots + soon-to-empty harvest slots,
    but stops before endgame so seed bags do not remain dead cash at round 720.
  - Crop timing is explicit: fast crops keep cash flowing while slow crops mature.
  - All actions are LISTS, never bare strings.
  - __file__ guarded for Kaggle exec() loader.
"""

DEFAULT_DNA = {
    "target_hires": 8,
    "buy_land": 3,
    "land_reserve": 0,
    "max_land_buy_day": 20,
    "dump_turn": 690,
    "field_util_early": 96,
    "field_util_mid": 90,
    "field_util_late": 80,
    "melon_danger_opp": 6,
    "melon_crash_price": 185,
    "seed_buffer_early": 10,
    "seed_buffer_mid": 3,
    "use_brain": 1,
    "wheat_sell": 25,
    "carrot_sell": 32,
    "tomato_sell": 60,
    "strawberry_sell": 120,
    "melon_sell": 230,
    "fertilizer_sell": 105,
    "max_wheat_seed_bank": 6,
    "weed_panic": 999,
}


def _load_dna():
    import json, os
    dna = dict(DEFAULT_DNA)
    candidates = []
    try:
        candidates.append(os.path.join(os.path.dirname(__file__), "dna.json"))
    except Exception:
        pass
    candidates += ["Agent/dna.json", "dna.json"]
    for p in candidates:
        try:
            if os.path.exists(p):
                with open(p, "r") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    dna.update(data)
                break
        except Exception:
            pass
    return dna

DNA = _load_dna()
_BRAIN = None
_BRAIN_LOADED = False
_BRAIN_OK = False
_MEMORY = {"last_step": -1, "last_prices": {}, "price_dir": {}}
_ACTIVE_QUADS = ["NW"]

CROPS = {
    "WHEAT":      {"seed": 10,  "first": 2,  "maxday": 4,  "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first": 2,  "maxday": 3,  "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first": 8,  "maxday": 8,  "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "maxday": 10, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first": 10, "maxday": 12, "max_yield": 6, "ongoing": False},
}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
LAND_PRICES = [1000, 2000, 4000]
# Forced expansion schedule by game day: NE, SW, SE. If we have the cash, buy.
LAND_DUE_DAYS = [2, 6, 11]
# Last planting day that can reasonably mature/harvest/drop/sell by step 720.
LAST_PLANT_DAY = {"MELON": 16, "STRAWBERRY": 14, "TOMATO": 20, "WHEAT": 24, "CARROT": 25}


def _load_brain():
    global _BRAIN, _BRAIN_LOADED, _BRAIN_OK
    if _BRAIN_LOADED:
        return _BRAIN, _BRAIN_OK
    _BRAIN_LOADED = True
    if not DNA.get("use_brain", 1):
        return None, False
    import os, pickle
    candidates = []
    try:
        candidates.append(os.path.join(os.path.dirname(__file__), "HI_Market_Brain.pkl"))
    except Exception:
        pass
    candidates += ["HI_Market_Brain.pkl", "Agent/HI_Market_Brain.pkl"]
    for p in candidates:
        try:
            if os.path.exists(p):
                with open(p, "rb") as f:
                    _BRAIN = pickle.load(f)
                _BRAIN_OK = True
                return _BRAIN, True
        except Exception:
            pass
    return None, False


def brain_sell(day, hour, price, qty):
    brain, ok = _load_brain()
    if not ok or not brain:
        return None
    try:
        import numpy as np
        return int(brain.predict(np.array([[day, hour, price, qty]], dtype="float32"))[0]) == 1
    except Exception:
        return None


def update_memory(step, prices):
    if step < _MEMORY.get("last_step", -1):
        _MEMORY["last_prices"] = {}
        _MEMORY["price_dir"] = {}
    last = _MEMORY.get("last_prices", {}) or {}
    dirs = {}
    for k, v in (prices or {}).items():
        dirs[k] = v - last.get(k, v)
    _MEMORY["last_prices"] = dict(prices or {})
    _MEMORY["price_dir"] = dirs
    _MEMORY["last_step"] = step


def safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default


def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def _move_candidates(pos, target, idx):
    """Monotonic lane routing: workers choose different axis order, but never
    step away/backtrack just to make a fancy route. This stops the visible
    same-round backtracking while still reducing worker trains.
    """
    x, y = pos; tx, ty = target
    horiz = []
    vert = []
    if x < tx: horiz.append((["EAST"], (x + 1, y)))
    elif x > tx: horiz.append((["WEST"], (x - 1, y)))
    if y < ty: vert.append((["SOUTH"], (x, y + 1)))
    elif y > ty: vert.append((["NORTH"], (x, y - 1)))
    return (horiz + vert) if idx % 2 == 0 else (vert + horiz)


def route_step(pos, target, idx, board_size, reserved_next, tiles=None):
    if pos == target:
        return ["PASS"]

    def passable(nxt):
        nx, ny = nxt
        if not (0 <= nx < board_size and 0 <= ny < board_size):
            return False
        # Movement into locked land is allowed by the engine, but it wastes turns.
        # Treat LOCKED as a wall so workers do not wander into unopened quadrants.
        try:
            if tiles is not None and tiles[ny][nx] == "LOCKED":
                return False
        except Exception:
            pass
        return True

    for action, nxt in _move_candidates(pos, target, idx):
        if not passable(nxt):
            continue
        if nxt in reserved_next:
            continue
        reserved_next.add(nxt)
        return action

    # If both useful direct lanes are reserved, still move. Overlap is legal in
    # the engine, and passing here caused workers to idle on shed/locked tiles.
    for action, nxt in _move_candidates(pos, target, idx):
        if passable(nxt):
            reserved_next.add(nxt)
            return action
    return ["PASS"]


def step_toward(pos, target):
    # Legacy wrapper for any old call sites.
    return route_step(pos, target, 0, 10, set(), None)


def shed_tiles(board_size):
    h = board_size // 2
    return [(h-1, h-1), (h, h-1), (h-1, h), (h, h)]


def is_shed_tile(pos, board_size):
    return tuple(pos) in set(shed_tiles(board_size))


def scan_farm(farm, day):
    tiles = farm.get("tiles", []) or []
    info = {
        "empty": [], "weeds": [], "plants": [], "harvestable": [], "unwatered": [],
        "active": {c: 0 for c in CROPS}, "mature_soon": {c: 0 for c in CROPS},
        "animals": [], "structures": []
    }
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if t is None:
                if not is_trimmed_side_column((x, y), len(tiles)):
                    info["empty"].append((x, y))
            elif t == "LOCKED":
                continue
            elif isinstance(t, dict):
                kind = t.get("kind")
                if kind == "WEED":
                    if not is_trimmed_side_column((x, y), len(tiles)):
                        info["weeds"].append((x, y))
                elif kind == "PLANT":
                    crop = t.get("crop")
                    if crop in CROPS:
                        cd = CROPS[crop]
                        age = day - t.get("planted_day", day)
                        info["active"][crop] += 1
                        info["plants"].append((x, y, crop, age, t))
                        if t.get("yield_units", 0) > 0 and age >= cd["first"]:
                            # Only target crops when a worker can actually harvest profitably now.
                            # Before this, hands walked to wheat/carrot too early and waited there.
                            ready_now = (not cd["ongoing"] and age >= cd["maxday"]) or (cd["ongoing"] and t.get("yield_units", 0) >= 2)
                            if ready_now:
                                info["harvestable"].append((x, y, crop, age, t))
                        if not cd["ongoing"] and age >= cd["maxday"] - 1:
                            info["mature_soon"][crop] += 1
                        if not t.get("watered_today", False):
                            info["unwatered"].append((x, y, crop, age, t))
                elif kind in ("COOP", "PASTURE"):
                    info["structures"].append((x, y, kind, t))
                    if "animal" in t:
                        info["animals"].append((x, y, t.get("animal"), t))
    return info, len(tiles)



def reserve_coord(info, coord):
    x, y = coord
    try:
        info["empty"] = [p for p in info.get("empty", []) if p != coord]
        info["weeds"] = [p for p in info.get("weeds", []) if p != coord]
        info["harvestable"] = [h for h in info.get("harvestable", []) if not (h[0] == x and h[1] == y)]
        info["unwatered"] = [u for u in info.get("unwatered", []) if not (u[0] == x and u[1] == y)]
    except Exception:
        pass

def unlocked_usable_tiles(farm, info):
    n = 0
    for row in farm.get("tiles", []) or []:
        for t in row:
            if t != "LOCKED":
                n += 1
    # reserve structures and a little practical movement slack around shed
    return max(0, n - len(info.get("structures", [])))


def crop_value(crop, prices, day, opp_info=None):
    cd = CROPS[crop]
    if day > LAST_PLANT_DAY.get(crop, 99):
        return -10**9
    price = prices.get(crop, cd["seed"] * 2)
    val = cd["max_yield"] * price - cd["seed"]
    # cash-flow bonus for fast crops; long crops are good but cannot be everything.
    if crop == "CARROT": val *= 1.20
    if crop == "WHEAT": val *= 0.95
    if crop == "TOMATO" and day > 12: val *= 0.75
    if crop == "STRAWBERRY" and day > 8: val *= 0.70
    if crop == "MELON":
        opp_melon = ((opp_info or {}).get("active", {}) or {}).get("MELON", 0)
        if opp_melon >= int(DNA.get("melon_danger_opp", 6)) or prices.get("MELON", 250) <= int(DNA.get("melon_crash_price", 185)):
            val *= 0.35
        elif day <= 6 and price >= 235:
            val *= 1.15
    return val


def desired_mix(info, opp_info, prices, day, step, farm):
    targets = {c: 0 for c in CROPS}
    if step >= int(DNA.get("dump_turn", 690)):
        return targets
    usable = unlocked_usable_tiles(farm, info)
    if day <= 10:
        util = int(DNA.get("field_util_early", 92)) / 100.0
    elif day <= 22:
        # After SW/SE are bought, burn cash into crops instead of hoarding money.
        util = max(int(DNA.get("field_util_mid", 82)) / 100.0, 0.92)
    else:
        util = int(DNA.get("field_util_late", 80)) / 100.0
    desired_total = max(0, int(usable * util))
    # As cutoff approaches, do not ask for impossible plants.
    eligible = [c for c in CROPS if day <= LAST_PLANT_DAY[c]]
    if not eligible:
        return targets
    ranked = sorted(eligible, key=lambda c: crop_value(c, prices, day, opp_info), reverse=True)

    # Opening philosophy: cheap wheat ignition first, then melon layer.
    # Wheat is not the highest value, but it is cheap enough to fill more plots immediately
    # and starts the cash flywheel while melons mature.
    if day <= 1:
        # True ignition: mostly cheap fast crops. Melon is only a small starter layer.
        targets["WHEAT"] = int(desired_total * 0.62)
        targets["CARROT"] = int(desired_total * 0.26)
        if "MELON" in eligible: targets["MELON"] = int(desired_total * 0.10)
        if "TOMATO" in eligible: targets["TOMATO"] = max(0, desired_total - sum(targets.values()))
    elif day <= 5:
        # v5.4m: slightly more melon, without choking the wheat/carrot cash engine.
        if "MELON" in eligible: targets["MELON"] = int(desired_total * 0.32)
        targets["CARROT"] = int(desired_total * 0.32)
        targets["WHEAT"] = int(desired_total * 0.20)
        if "TOMATO" in eligible: targets["TOMATO"] = int(desired_total * 0.12)
        if "STRAWBERRY" in eligible: targets["STRAWBERRY"] = max(0, desired_total - sum(targets.values()))
    elif day <= 12:
        # v5.4m: melon pressure + carrot cash; no forced strawberry layer.
        if "MELON" in eligible: targets["MELON"] += int(desired_total * 0.30)
        targets["CARROT"] += int(desired_total * 0.32)
        targets["WHEAT"] += int(desired_total * 0.16)
        if "TOMATO" in eligible: targets["TOMATO"] += int(desired_total * 0.14)
        if "STRAWBERRY" in eligible: targets["STRAWBERRY"] += max(0, desired_total - sum(targets.values()))
    elif day <= 17:
        # Cash-burn expansion push: if SW/SE are open and we have money, turn outer rings into melon.
        if "MELON" in eligible: targets["MELON"] += int(desired_total * 0.46)
        if "TOMATO" in eligible: targets["TOMATO"] += int(desired_total * 0.22)
        if "STRAWBERRY" in eligible: targets["STRAWBERRY"] += int(desired_total * 0.10)
        targets["CARROT"] += int(desired_total * 0.14)
        targets["WHEAT"] += max(0, desired_total - sum(targets.values()))
    elif day <= 22:
        # Late final push: tomatoes in middle/outer-mid, fast crops only inside.
        if "TOMATO" in eligible: targets["TOMATO"] += int(desired_total * 0.45)
        if "CARROT" in eligible: targets["CARROT"] += int(desired_total * 0.35)
        if "WHEAT" in eligible: targets["WHEAT"] += max(0, desired_total - sum(targets.values()))
    else:
        # Final cash-flow: fast crops only, with enough time to clear.
        if "CARROT" in eligible:
            targets["CARROT"] = int(desired_total * 0.60)
        if "WHEAT" in eligible:
            targets["WHEAT"] = desired_total - sum(targets.values())

    # Do not demand crops past their cutoff.
    for c in list(targets):
        if day > LAST_PLANT_DAY[c]:
            targets[c] = 0
    return targets


def bullseye_ring(pos, board_size):
    x, y = pos
    h = board_size // 2
    centers = [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]
    return min(manhattan(pos, c) for c in centers)


def is_outer_plot(pos, board_size):
    x, y = pos
    edge_dist = min(x, y, board_size - 1 - x, board_size - 1 - y)
    return edge_dist <= 1 or bullseye_ring(pos, board_size) >= 4


def empty_plot_score(crop, target, board_size):
    if not crop:
        return 0
    r = bullseye_ring(target, board_size)
    x, y = target
    edge_dist = min(x, y, board_size - 1 - x, board_size - 1 - y)
    if crop == "WHEAT": ideal = 0
    elif crop == "CARROT": ideal = 1
    elif crop == "TOMATO": ideal = 3
    elif crop == "STRAWBERRY": ideal = 4
    else: ideal = 5
    score = abs(r - ideal) * 100
    if crop in ("MELON", "STRAWBERRY"):
        score -= max(0, 2 - edge_dist) * 60
    if crop in ("WHEAT", "CARROT") and edge_dist <= 1:
        score += 450
    return score


def layer_adjustment(crop, pos, board_size):
    if pos is None:
        return 0
    r = bullseye_ring(pos, board_size)
    x, y = pos
    edge_dist = min(x, y, board_size - 1 - x, board_size - 1 - y)
    if crop == "WHEAT":
        adj = 2500 - 900 * abs(r - 0)
        if r >= 4 or edge_dist <= 1: adj -= 5000
    elif crop == "CARROT":
        adj = 2400 - 750 * abs(r - 1)
        if r >= 5 or edge_dist <= 1: adj -= 4200
    elif crop == "TOMATO":
        adj = 1900 - 550 * abs(r - 3)
        if r <= 1: adj -= 1800
    elif crop == "STRAWBERRY":
        adj = 1700 - 450 * abs(r - 4)
        if edge_dist <= 1: adj += 700
        if r <= 2: adj -= 2200
    else:
        adj = 2600 - 500 * abs(r - 5)
        if edge_dist <= 1: adj += 1200
        if r <= 2: adj -= 3500
    return adj


def is_trimmed_side_column(pos, board_size):
    """Ignore the leftmost and rightmost vertical columns of each quadrant.

    User idea: remove the outermost left-side 5 squares and right-side 5
    squares per quadrant so 2 workers can cover the remaining crop zone faster.
    For a 5x5 quadrant, this leaves the 3 middle columns = 15 usable crop tiles.
    """
    if pos is None:
        return False
    x, y = pos
    h = board_size // 2
    lx = x - h if x >= h else x
    return lx == 0 or lx == h - 1


def crop_allowed_on_plot(crop, pos, board_size):
    """Strict bullseye crop zoning.

    Inner rings are high-maintenance crops. Outer rings are long crops.
    This intentionally prevents wheat/carrot from leaking to the outside edges.
    """
    if pos is None:
        return True
    r = bullseye_ring(pos, board_size)
    x, y = pos
    edge_dist = min(x, y, board_size - 1 - x, board_size - 1 - y)
    # Very outer edge/corners: no wheat/carrot, period.
    if edge_dist <= 1 or r >= 5:
        return crop in ("MELON", "STRAWBERRY", "TOMATO")
    # Inner bullseye: fast maintenance crops.
    if r <= 1:
        return crop in ("WHEAT", "CARROT")
    # Middle ring: carrot/tomato bridge.
    if r <= 3:
        return crop in ("CARROT", "TOMATO", "WHEAT")
    # Outer-middle: tomato/long crops.
    return crop in ("TOMATO", "STRAWBERRY", "MELON")


def any_allowed_seed(seeds, day, pos, board_size):
    for crop in CROPS:
        if seeds.get(crop, 0) > 0 and day <= LAST_PLANT_DAY[crop] and crop_allowed_on_plot(crop, pos, board_size):
            return True
    return False


def best_crop_for_empty_slot(pos, prices, day, opp_info, board_size):
    # What seed should we buy for this empty slot's bullseye zone?
    # Once SW/SE are open-ish and we are in the last big-money window, outer ring
    # slots should become MELON unless it is too late. This prevents the bot from
    # continuing tiny wheat/carrot cycles while holding thousands in cash.
    if is_outer_plot(pos, board_size) and 12 <= day <= LAST_PLANT_DAY["MELON"] and crop_allowed_on_plot("MELON", pos, board_size):
        return "MELON"
    best = None
    best_score = -10**9
    for crop in CROPS:
        if day > LAST_PLANT_DAY[crop]:
            continue
        if not crop_allowed_on_plot(crop, pos, board_size):
            continue
        score = crop_value(crop, prices, day, opp_info) + layer_adjustment(crop, pos, board_size)
        if score > best_score:
            best_score = score
            best = crop
    return best


def preferred_crop_for_empty(active, targets, seeds, prices, day, opp_info=None):
    """Best desired crop for routing toward empty plots when no exact seed/plot is chosen yet."""
    best = None
    best_score = -10**9
    for crop in CROPS:
        if day > LAST_PLANT_DAY[crop]:
            continue
        deficit = targets.get(crop, 0) - active.get(crop, 0)
        score = crop_value(crop, prices, day, opp_info) + max(0, deficit) * 1000
        if seeds.get(crop, 0) > 0:
            score += 250
        if score > best_score:
            best_score = score
            best = crop
    return best


def choose_any_seed_for_plot(seeds, prices, day, opp_info, pos, board_size):
    """Fallback planter for owned seed bags.

    If a worker is standing on empty dirt and we already paid for a seed, plant
    the best seed that is compatible with this bullseye zone. This function was
    accidentally removed in a revert, which made v4.4 no-op via the safety except.
    """
    best = None
    best_score = -10**9
    for crop in CROPS:
        if seeds.get(crop, 0) <= 0 or day > LAST_PLANT_DAY[crop]:
            continue
        if not crop_allowed_on_plot(crop, pos, board_size):
            continue
        score = crop_value(crop, prices, day, opp_info) + layer_adjustment(crop, pos, board_size)
        if score > best_score:
            best_score = score
            best = crop
    if best is None:
        # Last resort: empty dirt is also bad. If no zone-compatible seed exists,
        # plant the best available seed rather than leaving a worker idle.
        for crop in CROPS:
            if seeds.get(crop, 0) <= 0 or day > LAST_PLANT_DAY[crop]:
                continue
            score = crop_value(crop, prices, day, opp_info)
            if score > best_score:
                best_score = score
                best = crop
    return best


def choose_crop_to_plant(active, targets, seeds, prices, day, opp_info=None, pos=None, board_size=10):
    best = None; best_score = -10**9
    strict_has_option = any_allowed_seed(seeds, day, pos, board_size) if pos is not None else False
    for crop in CROPS:
        if seeds.get(crop, 0) <= 0 or day > LAST_PLANT_DAY[crop]:
            continue
        # Strict zoning: if this plot has an allowed seed available, never choose a wrong-zone crop.
        # This stops wheat/carrot from going to the outside edges.
        if pos is not None and strict_has_option and not crop_allowed_on_plot(crop, pos, board_size):
            continue
        # If outer edge has no long seed, do NOT plant wheat/carrot just to fill it.
        if pos is not None and not crop_allowed_on_plot(crop, pos, board_size):
            continue
        deficit = targets.get(crop, 0) - active.get(crop, 0)
        score = crop_value(crop, prices, day, opp_info) + max(0, deficit) * 1000
        if deficit <= 0:
            score -= 500
        score += layer_adjustment(crop, pos, board_size)
        if score > best_score:
            best_score = score; best = crop
    return best if best_score > -10**8 else None



def _quad_sector(q, board_size):
    h = board_size // 2
    if q == "NW": return (0, h-1, 0, h-1)
    if q == "NE": return (h, board_size-1, 0, h-1)
    if q == "SW": return (0, h-1, h, board_size-1)
    return (h, board_size-1, h, board_size-1)


def worker_sector(idx, board_size):
    """Assign exactly 2 hired hands per ACTIVE unlocked quadrant.

    NW only        -> hands 1-2 NW
    NW+NE          -> hands 1-2 NW, 3-4 NE
    NW+NE+SW       -> hands 1-2 NW, 3-4 NE, 5-6 SW
    all 4          -> hands 1-2 NW, 3-4 NE, 5-6 SW, 7-8 SE
    Main farmer is the roaming +1 helper.
    """
    if idx <= 0:
        return None
    quads = _ACTIVE_QUADS or ["NW"]
    q_index = ((idx - 1) // 2) % len(quads)
    return _quad_sector(quads[q_index], board_size)


def in_sector(pos, sector):
    if sector is None:
        return True
    x, y = pos
    x0, x1, y0, y1 = sector
    return x0 <= x <= x1 and y0 <= y <= y1


def sector_center(sector):
    x0, x1, y0, y1 = sector
    return ((x0 + x1) // 2, (y0 + y1) // 2)


def target_score(idx, pos, target, board_size, urgent=False):
    # Main farmer and urgent carrying tasks just go nearest. Hands prefer their own quadrant.
    dist = manhattan(pos, target)
    sector = worker_sector(idx, board_size)
    if sector is None or urgent:
        return (0, dist)
    if in_sector(target, sector):
        return (0, dist)
    # If no local work is left, allow cross-sector work, but make it less attractive.
    return (2 + (manhattan(target, sector_center(sector)) // 4), dist)

def quadrant_entry_coords(pos, board_size):
    """Normalize a target to local coordinates from that quadrant's shed-side corner."""
    x, y = pos
    h = board_size // 2
    east = x >= h
    south = y >= h
    lx = x - h if east else x
    ly = y - h if south else y
    if not east and not south:      # NW, enter from bottom-right
        return "NW", (h - 1 - lx), (h - 1 - ly), h
    if east and not south:          # NE, enter from bottom-left
        return "NE", lx, (h - 1 - ly), h
    if not east and south:          # SW, enter from top-right
        return "SW", (h - 1 - lx), ly, h
    return "SE", lx, ly, h          # SE, enter from top-left


def worker_active_quadrant(idx):
    if idx <= 0:
        return "NW"
    quads = _ACTIVE_QUADS or ["NW"]
    q_index = ((idx - 1) // 2) % len(quads)
    return quads[q_index]


def entry_to_global(q, ax, ay, board_size):
    """Inverse of quadrant_entry_coords: local route coords -> board coords."""
    h = board_size // 2
    if q == "NW":
        return (h - 1 - ax, h - 1 - ay)
    if q == "NE":
        return (h + ax, h - 1 - ay)
    if q == "SW":
        return (h - 1 - ax, h + ay)
    return (h + ax, h + ay)


def lane_local_path(lane, h):
    """Two strict adjacent routes over the 3 usable middle columns.

    Side columns (local ax 0 and ax h-1) are pass-through/non-work columns.
    lane 0 covers the near/middle columns; lane 1 covers the far-middle column.
    This reduces travel while keeping exact route order.
    """
    if h <= 2:
        return [(0, 0)]
    # usable local columns are 1..h-2
    if lane == 0:
        pts = [(0, 0)]  # entry pass-through
        # column 1 down
        for ay in range(0, h):
            pts.append((1, ay))
        # column 2 up if it exists
        if h - 2 >= 2:
            for ay in range(h - 1, -1, -1):
                pts.append((2, ay))
        return list(dict.fromkeys(pts))
    # lane 1: move through to far-middle column and sweep it
    col = max(1, h - 2)
    pts = [(0, 0)]
    for ax in range(1, col + 1):
        pts.append((ax, 0))
    for ay in range(1, h):
        pts.append((col, ay))
    return list(dict.fromkeys(pts))


def worker_route_path(idx, board_size):
    q = worker_active_quadrant(idx)
    lane = (idx - 1) % 2 if idx > 0 else 1
    h = board_size // 2
    return [entry_to_global(q, ax, ay, board_size) for ax, ay in lane_local_path(lane, h)]


def route_order_score(idx, pos, target, board_size):
    """How far ahead on this worker's exact path a target is.

    Low score = next on path. Targets off path are penalized heavily and only used
    if the assigned route has no work.
    """
    if idx <= 0:
        return manhattan(pos, target)
    path = worker_route_path(idx, board_size)
    if not path:
        return manhattan(pos, target)
    # nearest current position on route
    cur_i = min(range(len(path)), key=lambda i: manhattan(pos, path[i]))
    try:
        tgt_i = path.index(target)
    except ValueError:
        return 1000 + manhattan(pos, target)
    if tgt_i >= cur_i:
        return tgt_i - cur_i
    return (len(path) - cur_i) + tgt_i + 20  # wrap only after completing route


def lane_patrol_score(idx, pos, target, board_size, kind="empty"):
    if idx <= 0:
        return manhattan(pos, target)
    sector = worker_sector(idx, board_size)
    sector_penalty = 0 if (sector is None or in_sector(target, sector)) else 300
    return sector_penalty + route_order_score(idx, pos, target, board_size)


def route_lane_match(idx, target, board_size):
    """Physical route membership: pass-through + work cells."""
    if idx <= 0:
        return not is_trimmed_side_column(target, board_size)
    if is_trimmed_side_column(target, board_size):
        return False
    return target in set(worker_route_path(idx, board_size))


def route_work_match(idx, target, board_size):
    """For this test, every tile on the assigned path is a work tile.

    The drawn route itself is the work order. Workers do the task on whatever
    route tile they stand on, then continue the route.
    """
    if idx <= 0:
        return not is_trimmed_side_column(target, board_size)
    if is_trimmed_side_column(target, board_size):
        return False
    return target in set(worker_route_path(idx, board_size))


def route_owned_candidates(idx, candidates, board_size):
    """Strict route hierarchy: own exact path -> own quadrant -> global."""
    if idx <= 0 or not candidates:
        return candidates
    sector = worker_sector(idx, board_size)
    own_sector = [p for p in candidates if sector is not None and in_sector(p, sector)]
    own_work = [p for p in own_sector if route_work_match(idx, p, board_size)]
    if own_work:
        return own_work
    own_path = [p for p in own_sector if route_lane_match(idx, p, board_size)]
    if own_path:
        return own_path
    if own_sector:
        return own_sector
    return candidates


def patrol_route_step(pos, target, idx, board_size, reserved_next, tiles=None):
    """Move along the exact path instead of cutting directly across the field."""
    if idx <= 0 or target not in set(worker_route_path(idx, board_size)):
        return route_step(pos, target, idx, board_size, reserved_next, tiles)
    path = worker_route_path(idx, board_size)
    cur_i = min(range(len(path)), key=lambda i: manhattan(pos, path[i]))
    tgt_i = path.index(target)
    # If off the path, first rejoin nearest route tile.
    if pos != path[cur_i]:
        return route_step(pos, path[cur_i], idx, board_size, reserved_next, tiles)
    if cur_i == tgt_i:
        return ["PASS"]
    nxt_i = cur_i + 1 if cur_i < len(path) - 1 else 0
    # Don't wrap unless target is behind us; route_order_score gave wrap penalty.
    if tgt_i < cur_i and cur_i < len(path) - 1:
        nxt_i = cur_i + 1
    return route_step(pos, path[nxt_i], idx, board_size, reserved_next, tiles)


def lane_task_key(idx, pos, target, board_size, kind, crop_hint=None, urgent=False):
    base = target_score(idx, pos, target, board_size, urgent=urgent)
    dist = manhattan(pos, target)
    lane = lane_patrol_score(idx, pos, target, board_size, kind)
    if kind == "empty":
        layer = empty_plot_score(crop_hint, target, board_size) if crop_hint else 0
        # For this experiment, follow the drawn path first, crop-zone second.
        # Previous strict versions kept choosing crop-fit clusters and visually abandoned lanes.
        return (base[0], lane, layer, dist)
    if kind in ("water", "harvest"):
        # Still respect routes more, but keep urgent jobs practical.
        return (base[0], lane, min(dist, 3), dist)
    return (base[0], lane, dist)

def sector_candidates(idx, candidates, board_size):
    """Soft recovery version: do NOT lock workers to quadrants.

    Hard quadrant ownership tanked score because workers ignored useful work and the
    economy never reached SE.  We keep route/lane diversity elsewhere, but task
    choice is global with lookahead scoring.
    """
    return candidates


def lookahead_target_key(idx, pos, target, board_size, kind, crop_hint=None):
    """3-ish step lookahead scoring. Lower is better.

    Prioritize tasks that can be reached/actioned soon. Empty plots are valuable
    only if the worker can get there fast enough to plant instead of wandering.
    """
    dist = manhattan(pos, target)
    sector_penalty = target_score(idx, pos, target, board_size, urgent=(kind in ("harvest", "water", "drop")))[0]
    if kind == "water":
        # watering prevents crop death, but don't drag everyone cross-map
        return (0, min(dist, 3), sector_penalty, dist)
    if kind == "harvest":
        return (1, min(dist, 4), sector_penalty, dist)
    if kind == "empty":
        # empty plot only useful if close or excellent bullseye match
        layer = empty_plot_score(crop_hint, target, board_size) if crop_hint else 0
        return (2, dist // 3, layer, sector_penalty, dist)
    if kind == "weed":
        return (9, dist)
    return (5, sector_penalty, dist)



def path_tile_kind(coord, info, seeds, day, board_size):
    """Return whether a path tile has useful work available now."""
    x, y = coord
    # empty + seed means plantable work
    if coord in set(info.get("empty", [])):
        # Any seed that can be planted here, or fallback seed if zoning blocks everything.
        for crop in CROPS:
            if seeds.get(crop, 0) > 0 and day <= LAST_PLANT_DAY[crop]:
                return "empty"
    for u in info.get("unwatered", []):
        if u[0] == x and u[1] == y:
            return "water"
    for a in info.get("harvestable", []):
        if a[0] == x and a[1] == y:
            return "harvest"
    if coord in set(info.get("weeds", [])):
        return "weed"
    return None


def strict_patrol_action(idx, pos, tiles, info, seeds, prices, day, board_size, reserved_next, opp_info=None):
    """Force a worker to follow its route.

    It searches forward along the assigned path for the next tile that needs work.
    If no work exists on the route, it still moves to the next route tile instead
    of idling. This is intentionally stricter than priority targeting.
    """
    if idx <= 0:
        return None
    path = worker_route_path(idx, board_size)
    if not path:
        return None
    # Find nearest place on the route and continue forward from there.
    cur_i = min(range(len(path)), key=lambda i: manhattan(pos, path[i]))

    # If currently off the route, rejoin it first.
    if pos != path[cur_i]:
        return patrol_route_step(pos, path[cur_i], idx, board_size, reserved_next, tiles)

    # Search forward one full loop for a useful tile. Direct action on current tile
    # already happened above, so start with next tile.
    n = len(path)
    for step_ahead in range(1, n + 1):
        j = (cur_i + step_ahead) % n
        coord = path[j]
        # Only work the assigned lane. Other route tiles are pass-through so the
        # worker reaches the outside/route segment before planting inward.
        if not route_work_match(idx, coord, board_size):
            continue
        kind = path_tile_kind(coord, info, seeds, day, board_size)
        if kind is not None:
            reserve_coord(info, coord)
            return patrol_route_step(pos, coord, idx, board_size, reserved_next, tiles)

    # No work on the whole route: keep patrolling so the worker is positioned for next day/turn.
    nxt = path[(cur_i + 1) % n]
    return patrol_route_step(pos, nxt, idx, board_size, reserved_next, tiles)


def next_route_action(pos, idx, board_size, reserved_next, tiles):
    """Move exactly one step along this worker's assigned route.

    No target skipping. No chasing better tasks. If off-route, rejoin the nearest
    route tile, then continue route order.
    """
    if idx <= 0:
        return None
    path = worker_route_path(idx, board_size)
    if not path:
        return ["PASS"]
    if pos in path:
        i = path.index(pos)
        nxt = path[(i + 1) % len(path)]
    else:
        nxt = min(path, key=lambda p: manhattan(pos, p))
    if nxt == pos:
        return ["PASS"]
    return route_step(pos, nxt, idx, board_size, reserved_next, tiles)


def route_direct_action(idx, pos, tile, info, targets, seeds, prices, day, step, reserved, board_size, opp_info=None):
    """Action for a hired hand standing on its route.

    This is intentionally route-only: hands do work on their assigned route tile;
    otherwise they keep moving. This enforces the user's drawn path.
    """
    if idx <= 0:
        return None
    if not route_work_match(idx, pos, board_size):
        return None
    is_dump = step >= int(DNA.get("dump_turn", 690))
    x, y = pos
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop = tile.get("crop")
        cd = CROPS.get(crop, {})
        age = day - tile.get("planted_day", day)
        yld = tile.get("yield_units", 0)
        if yld > 0 and (is_dump or (not cd.get("ongoing", False) and age >= cd.get("maxday", 99)) or (cd.get("ongoing", False) and (yld >= 2 or day >= 20))):
            reserve_coord(info, pos)
            return ["HARVEST"]
        if not tile.get("watered_today", False) and not is_dump:
            reserve_coord(info, pos)
            return ["WATER"]
        if is_dump and step >= 700:
            reserve_coord(info, pos)
            return ["DIG"]
    elif tile is None and not is_dump:
        crop = choose_crop_to_plant(info["active"], targets, seeds, prices, day, opp_info, pos, board_size)
        if not crop:
            crop = choose_any_seed_for_plot(seeds, prices, day, opp_info, pos, board_size)
        if crop and reserved.get(crop, 0) < seeds.get(crop, 0):
            reserved[crop] = reserved.get(crop, 0) + 1
            info["active"][crop] = info["active"].get(crop, 0) + 1
            reserve_coord(info, pos)
            return ["PLANT", crop]
    elif isinstance(tile, dict) and tile.get("kind") == "WEED" and not is_dump:
        reserve_coord(info, pos)
        return ["DIG"]
    return None


def plan_unit(idx, pos, inv, tiles, info, targets, seeds, prices, day, step, reserved, reserved_next, stage_empty=False, stage_slots=None, opp_info=None):
    board_size = len(tiles)
    x, y = pos
    tile = tiles[y][x] if 0 <= y < board_size and 0 <= x < len(tiles[y]) else "LOCKED"
    is_dump = step >= int(DNA.get("dump_turn", 690))
    # Do NOT reserve the current tile. Hands often spawn stacked around the shed,
    # including on locked shed-access tiles. Reserving current positions traps them.

    # Hired hands should only work their assigned route/lane. They may pass through
    # other tiles without planting/watering so the outside-first path is preserved.
    # Main farmer remains a flexible sweeper.
    on_my_route = (idx <= 0) or route_work_match(idx, (x, y), board_size)

    # Drop harvested items ASAP so market can sell them.
    if inv and any(v > 0 for k, v in inv.items() if k in PRODUCTS):
        if is_shed_tile((x, y), board_size):
            return ["DROP"]

    # Hired hands follow their exact assigned route. They only act on the tile
    # under their feet if it belongs to their route; otherwise they move one step
    # along the route. This prevents priority logic from pulling them off-path.
    if idx > 0:
        direct = route_direct_action(idx, (x, y), tile, info, targets, seeds, prices, day, step, reserved, board_size, opp_info)
        if direct is not None:
            return direct
        route_move = next_route_action((x, y), idx, board_size, reserved_next, tiles)
        if route_move is not None:
            return route_move

    if on_my_route and isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop = tile.get("crop")
        cd = CROPS.get(crop, {})
        age = day - tile.get("planted_day", day)
        yld = tile.get("yield_units", 0)
        if yld > 0:
            # Non-ongoing wait for maxday unless cleanup; ongoing harvest at 2+ or cleanup.
            if is_dump or (not cd.get("ongoing", False) and age >= cd.get("maxday", 99)) or (cd.get("ongoing", False) and (yld >= 2 or day >= 20)):
                reserve_coord(info, (x, y))
                return ["HARVEST"]
        if not tile.get("watered_today", False) and not is_dump:
            reserve_coord(info, (x, y))
            return ["WATER"]
        if yld > 0 and is_dump and age >= cd.get("first", 99):
            reserve_coord(info, (x, y))
            return ["HARVEST"]
        if is_dump and step >= 700:
            # Final emergency only: immature plants are dead capital at 720.
            reserve_coord(info, (x, y))
            return ["DIG"]

    if on_my_route and tile is None and not is_dump:
        crop = choose_crop_to_plant(info["active"], targets, seeds, prices, day, opp_info, (x, y), board_size)
        if not crop:
            crop = choose_any_seed_for_plot(seeds, prices, day, opp_info, (x, y), board_size)
        if crop and reserved.get(crop, 0) < seeds.get(crop, 0):
            reserved[crop] = reserved.get(crop, 0) + 1
            info["active"][crop] = info["active"].get(crop, 0) + 1
            reserve_coord(info, (x, y))
            return ["PLANT", crop]

    if on_my_route and isinstance(tile, dict) and tile.get("kind") == "WEED" and not is_dump:
        reserve_coord(info, (x, y))
        return ["DIG"]

    # Hard route rule for hired hands: do not abandon the designed path.
    # If their route has no immediate work, they still patrol to the next tile.
    patrol = strict_patrol_action(idx, (x, y), tiles, info, seeds, prices, day, board_size, reserved_next, opp_info)
    if patrol is not None:
        return patrol

    # Movement task lists. We choose in priority bands so workers do not walk to
    # a far empty plot while a crop beside them is dying unwatered. Within each
    # band, hands prefer their assigned quadrant/sector.
    if inv and any(v > 0 for k, v in inv.items() if k in PRODUCTS):
        candidates = shed_tiles(board_size)
        target = min(candidates, key=lambda p: target_score(idx, (x, y), p, board_size, urgent=True))
        reserve_coord(info, target)
        return route_step((x, y), target, idx, board_size, reserved_next, tiles)

    # Strict route patrol movement.
    # Direct tile actions above still handle: plant on empty, water standing crop,
    # harvest standing crop, dig standing weed.  Movement should NOT chase global
    # priority jobs, because that pulled workers off their designed paths and left
    # route tiles unwatered.  Instead, each hand follows its own route/lane and
    # moves to the next useful tile on that route.
    if not is_dump:
        patrol_targets = []
        # Empty plots only matter if seeds exist / are being staged.
        empty_stage_ok = False
        wants_more = sum(targets.values()) > sum(info.get("active", {}).values())
        if choose_crop_to_plant(info["active"], targets, seeds, prices, day, opp_info, None, board_size):
            empty_stage_ok = True
        elif stage_empty and stage_slots is not None and stage_slots[0] > 0:
            empty_stage_ok = True
        elif wants_more and stage_empty and stage_slots is not None and stage_slots[0] > 0:
            empty_stage_ok = True
        if empty_stage_ok:
            empties = list(info.get("empty", []))
            if sum(seeds.values()) > 0:
                compat = [p for p in empties if any_allowed_seed(seeds, day, p, board_size)]
                if compat:
                    empties = compat
            for p in empties:
                crop_here = choose_any_seed_for_plot(seeds, prices, day, opp_info, p, board_size)
                crop_hint = crop_here if crop_here is not None else preferred_crop_for_empty(info["active"], targets, seeds, prices, day, opp_info)
                patrol_targets.append((p, "empty", crop_hint))

        # Route patrol includes crops needing water/harvest and weeds, but path position
        # decides which one the worker walks toward. When it arrives, direct action fires.
        for u in info.get("unwatered", []):
            patrol_targets.append(((u[0], u[1]), "water", None))
        for a in info.get("harvestable", []):
            patrol_targets.append(((a[0], a[1]), "harvest", None))
        for w in info.get("weeds", []):
            patrol_targets.append((w, "weed", None))

        if patrol_targets:
            coords = [p for p, kind, hint in patrol_targets]
            owned = route_owned_candidates(idx, coords, board_size)
            owned_set = set(owned)
            filtered = [(p, kind, hint) for p, kind, hint in patrol_targets if p in owned_set]
            if filtered:
                def patrol_key(item):
                    p, kind, hint = item
                    # Route lane first. Action kind is only a tiny tie-breaker so we do not
                    # abandon the route to chase water/harvest globally.
                    route = lane_patrol_score(idx, (x, y), p, board_size, kind)
                    action_tie = 0 if kind == "empty" else (1 if kind == "water" else (2 if kind == "harvest" else 3))
                    dist = manhattan((x, y), p)
                    layer = empty_plot_score(hint, p, board_size) if kind == "empty" and hint else 0
                    return (route, action_tie, layer, dist)
                target, kind, hint = min(filtered, key=patrol_key)
                if kind == "empty" and stage_slots is not None:
                    stage_slots[0] -= 1
                reserve_coord(info, target)
                return patrol_route_step((x, y), target, idx, board_size, reserved_next, tiles)
    else:
        # Cleanup mode: just go harvestable nearest-ish on route.
        cleanup_targets = [((a[0], a[1]), "harvest", None) for a in info.get("harvestable", [])]
        if cleanup_targets:
            target, kind, hint = min(cleanup_targets, key=lambda item: lane_patrol_score(idx, (x, y), item[0], board_size, item[1]))
            reserve_coord(info, target)
            return patrol_route_step((x, y), target, idx, board_size, reserved_next, tiles)

    return ["PASS"]



def quadrant_fill(farm, quadrant):
    """Return (filled_ratio, active, empty, weeds, usable) for a quadrant."""
    tiles = farm.get("tiles", []) or []
    if not tiles:
        return 0.0, 0, 0, 0, 0
    board_size = len(tiles)
    h = board_size // 2
    if quadrant == "NW": x0, x1, y0, y1 = 0, h - 1, 0, h - 1
    elif quadrant == "NE": x0, x1, y0, y1 = h, board_size - 1, 0, h - 1
    elif quadrant == "SW": x0, x1, y0, y1 = 0, h - 1, h, board_size - 1
    else: x0, x1, y0, y1 = h, board_size - 1, h, board_size - 1
    active = empty = weeds = usable = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            t = tiles[y][x]
            if t == "LOCKED" or is_trimmed_side_column((x, y), board_size):
                continue
            usable += 1
            if t is None:
                empty += 1
            elif isinstance(t, dict) and t.get("kind") == "PLANT":
                active += 1
            elif isinstance(t, dict) and t.get("kind") == "WEED":
                weeds += 1
    return (active / float(max(1, usable))), active, empty, weeds, usable


def expansion_readiness(farm, info, seeds):
    """Return whether current unlocked land is being used well enough to expand.

    This follows the user's rule: fill/maintain the current square first, then
    unlock the next quadrant.  Empty/weed-heavy current land means the crew is
    not ready for more acreage yet.
    """
    unlocked = 0
    tiles = farm.get("tiles", []) or []
    board_size = len(tiles) if tiles else 10
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if t != "LOCKED" and not is_trimmed_side_column((x, y), board_size):
                unlocked += 1
    structures = len(info.get("structures", []))
    usable = max(1, unlocked - structures)
    active = sum(info.get("active", {}).values())
    empty = len(info.get("empty", []))
    weeds = len(info.get("weeds", []))
    seed_total = sum(safe_int(v) for v in (seeds or {}).values())
    filled_ratio = active / float(usable)
    # Seeds about to be planted count a little, but empty ground is still the warning sign.
    potential_ratio = min(1.0, (active + min(seed_total, empty)) / float(usable))
    # Full-drive rule: don't buy another drive until this one is basically full.
    ready = (filled_ratio >= 0.82 and potential_ratio >= 0.92 and empty <= max(3, usable // 8) and weeds <= max(6, usable // 8))
    return ready, filled_ratio, potential_ratio, empty, weeds, usable


def next_land_need(farm, day):
    unlocked = farm.get("unlocked_quadrants", ["NW"]) or ["NW"]
    extra = max(0, len(unlocked) - 1)
    if extra >= min(3, int(DNA.get("buy_land", 3))):
        return None
    if day > int(DNA.get("max_land_buy_day", 20)):
        return None
    return extra, LAND_PRICES[extra], LAND_DUE_DAYS[extra]

def agent(obs):
    try:
        player = obs.get("player", 0)
        step = safe_int(obs.get("step", 0))
        day = safe_int(obs.get("day", step // 24))
        hour = safe_int(obs.get("hour", step % 24))
        farms = obs.get("farms", []) or []
        if not farms or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        my_farm = farms[player]
        opp_farm = farms[1-player] if len(farms) > 1 else None
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}
        seeds = private.get("seeds", {}) or {}
        inventories = private.get("inventories", [{}]) or [{}]
        prices = (obs.get("market", {}) or {}).get("prices", {}) or {}
        cash = float(my_farm.get("money", 0) or 0)
        tiles = my_farm.get("tiles", []) or []
        hands = my_farm.get("hands", []) or []
        farmer_pos = my_farm.get("farmer", [4, 4]) or [4, 4]

        update_memory(step, prices)
        my_info, board_size = scan_farm(my_farm, day)
        # Active quadrants drive 3-hands-per-quadrant lane assignment.
        global _ACTIVE_QUADS
        unlocked_order = ["NW", "NE", "SW", "SE"]
        current_unlocked = my_farm.get("unlocked_quadrants", ["NW"]) or ["NW"]
        _ACTIVE_QUADS = [q for q in unlocked_order if q in current_unlocked] or ["NW"]
        opp_info, _ = scan_farm(opp_farm, day) if opp_farm else ({"active": {}}, board_size)
        targets = desired_mix(my_info, opp_info, prices, day, step, my_farm)
        is_dump = step >= int(DNA.get("dump_turn", 690))

        reserved = {}
        # Planned next-step lane reservations. Do not pre-reserve current positions;
        # overlap is legal and pre-reserving trapped workers at spawn.
        reserved_next = set()
        # Stage workers on empty plots only when seed exists, and only as many
        # workers as seed bags available. This avoids workers camping empty dirt.
        seed_total_now = sum(safe_int(v) for v in seeds.values())
        stage_empty = (seed_total_now > 0)
        stage_slots = [max(seed_total_now, min(8, len(my_info.get("empty", []))) if seed_total_now > 0 else 0)]
        farmer_inv = inventories[0] if len(inventories) > 0 and isinstance(inventories[0], dict) else {}
        farmer_action = plan_unit(0, tuple(farmer_pos), farmer_inv, tiles, my_info, targets, seeds, prices, day, step, reserved, reserved_next, stage_empty, stage_slots, opp_info)
        hand_actions = []
        for i, hp in enumerate(hands):
            inv = inventories[i+1] if i+1 < len(inventories) and isinstance(inventories[i+1], dict) else {}
            hand_actions.append(plan_unit(i+1, tuple(hp), inv, tiles, my_info, targets, seeds, prices, day, step, reserved, reserved_next, stage_empty, stage_slots, opp_info))

        market = []
        # Sell harvested crops early enough to recycle cash. In cleanup sell everything.
        opp_melon_loaded = (opp_info.get("active", {}) or {}).get("MELON", 0) >= int(DNA.get("melon_danger_opp", 6))
        for item in PRODUCTS:
            qty = safe_int(shed.get(item, 0))
            if qty <= 0:
                continue
            # During normal play, leave market slots for mandatory hires and seeds.
            # In cleanup/dump mode, sell everything.
            if (not is_dump and len(market) >= 4) or (is_dump and len(market) >= 10):
                continue
            price = prices.get(item, 0)
            gate = int(DNA.get(item.lower() + "_sell", 99999))
            if item == "MELON" and opp_melon_loaded and price >= 215:
                gate = min(gate, 215)
            brain_vote = brain_sell(day, hour, price, qty)
            if is_dump or price >= gate or (brain_vote is True and price >= int(gate * 0.85)):
                market.append(["SELL", item, qty])

        # Staged expansion: fill and maintain the current unlocked square first.
        # Buying land early only helps if the current crew can keep existing plots full.
        land_need = next_land_need(my_farm, day)
        land_reserve_floor = 0
        if not is_dump and land_need and len(market) < 10:
            extra, land_price, due_day = land_need
            land_reserve_floor = land_price + int(DNA.get("land_reserve", 0))
            ready_expand, filled_ratio, potential_ratio, empty_count, weed_count, usable_now = expansion_readiness(my_farm, my_info, seeds)
            # NE is allowed once the first square is mostly full; SW requires the full-field gate.
            # SE is special: if SW is only half-used, buying SE is dead money. In the 24.9k run,
            # SE was bought at ~455 and only got ~5 crops, so block late SE unless SW is truly full.
            first_extra = (extra == 0 and day >= 2 and filled_ratio >= 0.82 and potential_ratio >= 0.90)
            staged_ready = ready_expand and day >= due_day
            if extra == 2:
                sw_fill, sw_active, sw_empty, sw_weeds, sw_usable = quadrant_fill(my_farm, "SW")
                se_allowed = (day <= 15 and sw_fill >= 0.78 and sw_empty <= max(4, sw_usable // 5))
                staged_ready = staged_ready and se_allowed
            if cash >= land_price and (first_extra or staged_ready):
                market.append(["BUY_LAND"]); cash -= land_price
                land_reserve_floor = 0

        # Mandatory quadrant crews BEFORE seed ordering.
        # Sells intentionally leave slots for this block; otherwise a sell burst can
        # consume all 10 market slots and cause no workers / day-4 weedouts.
        if not is_dump and hour <= 20 and len(market) < 10:
            unlocked = my_farm.get("unlocked_quadrants", ["NW"]) or ["NW"]
            pending_land = any(isinstance(o, list) and o and o[0] == "BUY_LAND" for o in market)
            managed_quadrants = min(4, len(unlocked) + (1 if pending_land else 0))
            # Exactly 2 hired hands per active/pending quadrant. Main farmer is the +1 floater.
            desired_hands_pre = min(int(DNA.get("target_hires", 8)), 2 * managed_quadrants)
            # Leave market slots for seed/sell orders. Hire cost is tiny, so don't require $70.
            while len(hands) + sum(1 for o in market if o == ["HIRE"]) < desired_hands_pre and len(market) < 8 and cash > 5:
                market.append(["HIRE"]); cash -= 2

        # Just-in-time seed scheduler after sell/land reserve. Empty plots with no seed were causing
        # 20+ turn idle gaps, so seed orders get first claim on market slots after selling.
        if not is_dump:
            active = my_info["active"]
            total_seed = sum(safe_int(v) for v in seeds.values())
            plant_requests = sum(1 for a in [farmer_action] + hand_actions if isinstance(a, list) and a and a[0] == "PLANT")
            empty_now = len(my_info.get("empty", []))
            soon_empty = sum(1 for x, y, c, age, t in my_info.get("harvestable", []) if not CROPS.get(c, {}).get("ongoing", False))
            target_hires = int(DNA.get("target_hires", 8))
            intended_workers = 1 + max(len(hands), min(target_hires, len(hands) + 5))
            buffer = int(DNA.get("seed_buffer_early", 6)) if day <= 8 else int(DNA.get("seed_buffer_mid", 3)) if day <= 16 else 0
            practical_need = min(empty_now + soon_empty, intended_workers * 2 + soon_empty + buffer)
            seed_budget = max(0, practical_need - total_seed + plant_requests)
            all_land_open = len(my_farm.get("unlocked_quadrants", ["NW"]) or ["NW"]) >= 4
            # Once land is open and cash is sitting around, stop hoarding and flood empty zones.
            ready_for_more, fr_now, pr_now, ec_now, wc_now, usable_now2 = expansion_readiness(my_farm, my_info, seeds)
            # If current acreage is not full, seed every empty slot before thinking about more land.
            if cash >= 400 and ec_now > 0 and day <= 22:
                seed_budget = max(seed_budget, min(60, empty_now + soon_empty - total_seed + plant_requests))
            if all_land_open and cash >= 1500 and 12 <= day <= 22:
                seed_budget = max(seed_budget, min(70, empty_now + soon_empty - total_seed + plant_requests))
            if day <= 3:
                seed_budget = max(seed_budget, min(24, empty_now + soon_empty - total_seed + plant_requests))
            if day >= 23:
                seed_budget = min(seed_budget, max(0, intended_workers + soon_empty - total_seed))

            deficits = {}
            zone_empty_need = {c: 0 for c in CROPS}
            # Critical: buy seeds for the plots that are actually empty in each bullseye zone.
            # This prevents the bot from owning only wheat/carrot while outer slots wait empty.
            for p in my_info.get("empty", []):
                c = best_crop_for_empty_slot(p, prices, day, opp_info, board_size)
                if c:
                    zone_empty_need[c] += 1
            outer_empty_count = sum(1 for p in my_info.get("empty", []) if is_outer_plot(p, board_size))
            for crop in CROPS:
                # In the all-land cash-burn window, allow melon buying until its true last plant day.
                if crop == "MELON" and all_land_open and cash >= 1200 and day <= LAST_PLANT_DAY["MELON"]:
                    stop_buy_day = LAST_PLANT_DAY[crop] + 1
                else:
                    stop_buy_day = LAST_PLANT_DAY[crop] - (2 if crop in ("MELON", "STRAWBERRY", "TOMATO") else 1)
                if day >= stop_buy_day:
                    deficits[crop] = 0
                else:
                    target_need = max(0, targets.get(crop, 0) - active.get(crop, 0) - seeds.get(crop, 0))
                    slot_need = max(0, zone_empty_need.get(crop, 0) - seeds.get(crop, 0))
                    deficits[crop] = max(target_need, slot_need)
            if all_land_open and cash >= 1200 and 12 <= day <= LAST_PLANT_DAY["MELON"]:
                # Hard override: buy enough MELON to fill outer ring empties.
                deficits["MELON"] = max(deficits.get("MELON", 0), max(0, outer_empty_count - seeds.get("MELON", 0)))
                # During melon surge, do not waste cash on additional wheat bank.
                deficits["WHEAT"] = min(deficits.get("WHEAT", 0), 2)
                deficits["CARROT"] = min(deficits.get("CARROT", 0), 4)

            # Seed-bank discipline. Wheat is cheap, so the bot was over-buying it and
            # ending with 35 bags. Keep only a small rolling bank and stop late wheat buys.
            if seeds.get("WHEAT", 0) >= int(DNA.get("max_wheat_seed_bank", 6)) or day >= 20:
                deficits["WHEAT"] = 0
            if seeds.get("CARROT", 0) >= 10 or day >= 22:
                deficits["CARROT"] = 0

            if day <= 1:
                order = ["WHEAT", "CARROT", "MELON", "TOMATO", "STRAWBERRY"]
            elif all_land_open and cash >= 1200 and 12 <= day <= LAST_PLANT_DAY["MELON"]:
                # Once SW/SE are open and cash is sitting around, burn money into outer value,
                # not more wheat seed bank.
                order = ["MELON", "TOMATO", "STRAWBERRY", "CARROT", "WHEAT"]
            elif day <= 12:
                order = ["CARROT", "MELON", "WHEAT", "TOMATO", "STRAWBERRY"]
            elif day <= 17:
                order = ["CARROT", "WHEAT", "MELON", "TOMATO", "STRAWBERRY"]
            else:
                order = sorted(CROPS.keys(), key=lambda c: (-deficits.get(c, 0), -crop_value(c, prices, day, opp_info)))
            for crop in order:
                if len(market) >= 10 or seed_budget <= 0:
                    break
                cap = 30
                if crop == "MELON" and all_land_open and cash >= 1200 and 12 <= day <= LAST_PLANT_DAY["MELON"]:
                    cap = 40
                elif crop == "MELON" and day <= 3:
                    cap = 4
                elif crop == "MELON" and day <= 10:
                    cap = 10
                elif crop == "MELON" and day <= 13:
                    cap = 8
                elif crop == "WHEAT":
                    cap = 18 if day <= 3 else (6 if day <= 12 else 3)
                elif crop == "CARROT":
                    cap = 18 if day <= 3 else 8
                n = min(seed_budget, deficits.get(crop, 0), cap)
                if n <= 0:
                    continue
                cost = CROPS[crop]["seed"] * n
                reserve = 40 if day <= 22 else 160
                if land_reserve_floor and day >= (land_need[2] - 1 if land_need else 99):
                    # Hard-save for due land. Do not let seed buying repeatedly delay SW/SE.
                    reserve = max(reserve, land_reserve_floor)
                # If there are zero seeds and empty plots, buy enough to keep the crew busy.
                # Only clamp small when land is due and we are saving for it.
                if total_seed <= 0 and empty_now > 0 and day <= 16:
                    if land_reserve_floor and day >= (land_need[2] - 1 if land_need else 99):
                        n = min(n, 4)
                    cost = CROPS[crop]["seed"] * n
                    reserve = min(reserve, 120)
                if cash >= cost + reserve:
                    market.append(["BUY_SEED", crop, n])
                    cash -= cost
                    seed_budget -= n


        return {"farmer": farmer_action, "hands": hand_actions, "market": market[:10]}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}
