"""Decision Agent — built from scratch, no tape DNA.

Makes fresh decisions every turn based on board state and evolvable parameters.
"""

import math
from collections import deque

BOARD = 10
HALF = BOARD // 2
SHED_TILES = {(HALF-1, HALF-1), (HALF, HALF-1), (HALF-1, HALF), (HALF, HALF)}

# Crop economics (base price, seed cost, max yield)
CROPS = {
    "WHEAT":      {"price": 25,  "seed": 10, "max_yield": 4,  "days_to_max": 4},
    "CARROT":     {"price": 35,  "seed": 20, "max_yield": 3,  "days_to_max": 3},
    "TOMATO":     {"price": 60,  "seed": 50, "max_yield": 4,  "days_to_max": 11, "ongoing": True},
    "STRAWBERRY": {"price": 120, "seed": 100,"max_yield": 4,  "days_to_max": 16, "ongoing": True},
    "MELON":      {"price": 250, "seed": 80, "max_yield": 6,  "days_to_max": 10},
}

ANIMALS = {
    "COW":   {"price": 400, "product": "MILK",  "product_price": 160, "interval": 2},
    "SHEEP": {"price": 500, "product": "WOOL",  "product_price": 200, "interval": 3},
    "GOOSE": {"price": 300, "product": "EGG",   "product_price": 50,  "interval": 1},
}

QUADS = {
    "NW": [(y, x) for y in range(0, 5) for x in range(0, 5)],
    "NE": [(y, x) for y in range(0, 5) for x in range(5, 10)],
    "SW": [(y, x) for y in range(5, 10) for x in range(0, 5)],
    "SE": [(y, x) for y in range(5, 10) for x in range(5, 10)],
}


def bfs_dist(start, goal):
    if start == goal:
        return 0
    sx, sy = start
    gx, gy = goal
    seen = {start}
    q = deque([(sx, sy, 0)])
    while q:
        x, y, d = q.popleft()
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < BOARD and 0 <= ny < BOARD and (nx,ny) not in seen:
                if (nx,ny) == (gx,gy):
                    return d + 1
                seen.add((nx,ny))
                q.append((nx,ny,d+1))
    return 999


def move_toward(pos, goal):
    if pos == goal:
        return "PASS"
    px, py = pos
    gx, gy = goal
    dx = gx - px
    dy = gy - py
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST" if dx < 0 else "PASS"
    else:
        return "SOUTH" if dy > 0 else "NORTH" if dy < 0 else "PASS"


def is_shed_adj(pos):
    return (pos[1], pos[0]) in SHED_TILES


# Default parameters — a balanced starting strategy
DEFAULT_PARAMS = {
    # Crop planting weights (relative priority for empty tiles)
    "crop_wheat": 0.5,
    "crop_melon": 0.2,
    "crop_straw": 0.2,
    "crop_carrot": 0.1,
    "crop_tomato": 0.0,
    
    # Animal targets
    "target_cows": 6,
    "target_sheep": 4,
    "target_geese": 0,
    
    # Land timing (-1 = never)
    "ne_land_day": 6,
    "sw_land_day": 10,
    "se_land_day": -1,
    
    # Workers
    "daily_hires": 5,
    
    # Behavior
    "water_aggression": 1,    # 0=lazy, 1=normal, 2=aggressive
    "fertilizer_use": 1,      # 0=sell all, 1=premium crops only, 2=all crops
    "care_animals": 1,        # 0=skip, 1=do it
    "collect_fert": 1,        # 0=skip, 1=do it
    
    # Market timing
    "sell_wheat_day": 20,     # start bulk wheat sales
    "sell_premium_day": 15,   # start selling premium goods
    "wheat_buy_extra": 10,    # extra wheat to buy for feed
}


class DecisionAgent:
    def __init__(self, params=None, seat=0):
        self.params = params or dict(DEFAULT_PARAMS)
        self.seat = seat
        self.prev_day = -1
        self.planted_count = {}
        self.animal_count = 0
        self.land_bought = set()
        self.total_wheat_bought = 0

    def act(self, obs, config=None):
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        hour = step % 24
        player = int(obs.get("player", 0) or 0)
        opp = 1 - player

        farm = obs["farms"][player]
        opp_farm = obs["farms"][opp]
        tiles = farm.get("tiles", [])
        hands = farm.get("hands", [])
        money = float(farm.get("money", 0))
        unlocked = set(farm.get("unlocked_quadrants", []))
        farmer_pos = tuple(farm.get("farmer", [HALF-1, HALF-1]))

        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}
        seeds = private.get("seeds", {}) or {}
        inventories = private.get("inventories", []) or [{}]

        market_obs = obs.get("market", {})
        prices = market_obs.get("prices", {})
        inv = market_obs.get("inventory", {})

        # Reset daily state
        if day != self.prev_day:
            self.prev_day = day

        # Scan board
        board = self._scan_board(tiles, unlocked)

        # === MARKET ORDERS ===
        market = self._decide_market(day, hour, money, shed, seeds, unlocked, board)

        # === FARMER ACTION ===
        farmer_action = self._decide_worker_action(
            farmer_pos, board, shed, seeds, hands, day, hour, is_farmer=True
        )

        # === HAND ACTIONS ===
        hand_actions = []
        for i, hp in enumerate(hands):
            hand_pos = tuple(hp)
            action = self._decide_worker_action(
                hand_pos, board, shed, seeds, hands, day, hour, is_farmer=False
            )
            hand_actions.append(action)

        return {
            "farmer": farmer_action,
            "hands": hand_actions,
            "market": market[:10],
        }

    def _scan_board(self, tiles, unlocked):
        """Parse the board into structured data."""
        board = {
            "empty": [],
            "weeds": [],
            "plants": [],          # (y, x, crop, planted_day, yield_units, watered_today, consec_unwatered)
            "animals": [],         # (y, x, type, fed_today, cared_today, consec_unfed, fertilizer_available)
            "structures": [],      # (y, x, type, has_animal)
            "unlocked_quads": unlocked,
        }

        for y in range(BOARD):
            for x in range(BOARD):
                t = tiles[y][x] if y < len(tiles) and x < len(tiles[y]) else None
                if t is None:
                    quad = self._tile_quad(y, x)
                    if quad in unlocked:
                        board["empty"].append((y, x))
                elif t == "LOCKED":
                    pass
                elif isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "PLANT":
                        board["plants"].append({
                            "y": y, "x": x,
                            "crop": t.get("crop", "UNKNOWN"),
                            "planted_day": t.get("planted_day", 0),
                            "yield_units": t.get("yield_units", 0),
                            "watered_today": t.get("watered_today", False),
                            "consec_unwatered": t.get("consecutive_unwatered", 0),
                        })
                    elif kind == "WEED":
                        board["weeds"].append((y, x))
                    elif kind in ("COOP", "PASTURE"):
                        board["structures"].append({
                            "y": y, "x": x,
                            "type": kind,
                            "has_animal": t.get("animal") is not None,
                            "animal": t.get("animal"),
                            "fed_today": t.get("fed_today", False),
                            "cared_today": t.get("cared_today", False),
                            "consec_unfed": t.get("consecutive_unfed", 0),
                            "fertilizer_available": t.get("fertilizer_available", False),
                            "yield_units": t.get("yield_units", 0),
                        })
                        if t.get("animal"):
                            board["animals"].append(board["structures"][-1])

        return board

    def _tile_quad(self, y, x):
        if y < 5 and x < 5: return "NW"
        if y < 5 and x >= 5: return "NE"
        if y >= 5 and x < 5: return "SW"
        return "SE"

    def _decide_market(self, day, hour, money, shed, seeds, unlocked, board):
        """Decide market orders for this turn."""
        p = self.params
        market = []

        # Day 0: opening purchases
        if day == 0 and hour == 0:
            for _ in range(min(p["daily_hires"], 10)):
                market.append(["HIRE"])
            
            cows = min(p["target_cows"], 14)
            sheep = min(p["target_sheep"], 14)
            if cows > 0: market.append(["BUY_ANIMAL", "COW", cows])
            if sheep > 0: market.append(["BUY_ANIMAL", "SHEEP", sheep])
            
            # Seeds based on weights
            total_weight = sum(p.get(f"crop_{c}", 0) for c in ["wheat", "melon", "straw", "carrot", "tomato"])
            if total_weight > 0:
                seed_budget = 20  # total seeds to buy
                for crop_key, crop_name in [("wheat", "WHEAT"), ("melon", "MELON"), 
                                              ("straw", "STRAWBERRY"), ("carrot", "CARROT"),
                                              ("tomato", "TOMATO")]:
                    w = p.get(f"crop_{crop_key}", 0)
                    n = max(1, int(seed_budget * w / total_weight)) if w > 0 else 0
                    if n > 0 and len(market) < 10:
                        market.append(["BUY_SEED", crop_name, n])
            
            wb = p.get("wheat_buy_extra", 5)
            if wb > 0 and len(market) < 10:
                market.append(["BUY_PRODUCT", "WHEAT", wb])

        # Daily hires
        elif hour == 0 and day > 0:
            for _ in range(min(p["daily_hires"], 10)):
                market.append(["HIRE"])

        # Land purchases
        for quad, day_key in [("NE", "ne_land_day"), ("SW", "sw_land_day"), ("SE", "se_land_day")]:
            unlock_day = p.get(day_key, -1)
            if unlock_day >= 0 and day == unlock_day and hour == 0 and quad not in unlocked:
                if len(market) < 10:
                    market.append(["BUY_LAND"])

        # Buy wheat for feed if running low
        wheat_in_shed = int(shed.get("WHEAT", 0) or 0)
        n_animals = len(board["animals"])
        if wheat_in_shed < n_animals * 2 and money > 500 and hour == 1 and day > 2:
            if len(market) < 10:
                market.append(["BUY_PRODUCT", "WHEAT", min(5, 10 - len(market))])

        # Terminal liquidation
        if day >= 28:
            for item in ["STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "WHEAT", "FERTILIZER", "CARROT"]:
                qty = int(shed.get(item, 0) or 0)
                if qty > 0 and len(market) < 10:
                    market.append(["SELL", item, qty])

        return market

    def _decide_worker_action(self, pos, board, shed, seeds, hands, day, hour, is_farmer):
        """Decide what action this worker should take."""
        p = self.params

        # Priority 1: FEED unfed animals (critical)
        for animal in board["animals"]:
            if animal["consec_unfed"] >= 1 and int(shed.get("WHEAT", 0) or 0) > 0:
                tile = (animal["y"], animal["x"])
                a_pos = (animal["x"], animal["y"])
                dist = bfs_dist(pos, a_pos)
                if dist <= 2 and is_shed_adj(pos):
                    if dist == 0:
                        return ["FEED"]
                    else:
                        return [move_toward(pos, a_pos)]
                elif dist <= 1:
                    return [move_toward(pos, a_pos)]

        # Priority 2: WATER critically unwatered plants (consec >= 1)
        if p["water_aggression"] >= 1:
            for plant in board["plants"]:
                if plant["consec_unwatered"] >= 1:
                    tile_pos = (plant["x"], plant["y"])
                    dist = bfs_dist(pos, tile_pos)
                    if dist <= 1:
                        return ["WATER"]
                    elif dist <= 4:
                        return [move_toward(pos, tile_pos)]

        # Priority 3: HARVEST ripe crops
        for plant in board["plants"]:
            if plant["yield_units"] > 0:
                tile_pos = (plant["x"], plant["y"])
                dist = bfs_dist(pos, tile_pos)
                if dist <= 1:
                    return ["HARVEST"]
                elif dist <= 3:
                    return [move_toward(pos, tile_pos)]

        # Priority 4: CARE animals
        if p["care_animals"]:
            for animal in board["animals"]:
                if not animal["cared_today"]:
                    tile_pos = (animal["x"], animal["y"])
                    dist = bfs_dist(pos, tile_pos)
                    if dist <= 1:
                        return ["CARE"]
                    elif dist <= 2:
                        return [move_toward(pos, tile_pos)]

        # Priority 5: COLLECT FERTILIZER
        if p["collect_fert"]:
            for animal in board["animals"]:
                if animal["fertilizer_available"]:
                    tile_pos = (animal["x"], animal["y"])
                    dist = bfs_dist(pos, tile_pos)
                    if dist <= 1:
                        return ["COLLECT_FERTILIZER"]
                    elif dist <= 2:
                        return [move_toward(pos, tile_pos)]

        # Priority 6: PLACE animals from inventory
        farmer_inv = {}  # simplified
        for animal_type in ["COW", "SHEEP"]:
            for struct in board["structures"]:
                if not struct["has_animal"] and struct["type"] == ("PASTURE" if animal_type != "GOOSE" else "COOP"):
                    tile_pos = (struct["x"], struct["y"])
                    dist = bfs_dist(pos, tile_pos)
                    if dist <= 1:
                        # Would need inventory check here
                        pass
                    elif dist <= 2:
                        return [move_toward(pos, tile_pos)]

        # Priority 7: PLANT seeds on empty tiles
        crop_order = self._get_crop_priority()
        for crop in crop_order:
            seed_count = int(seeds.get(crop, 0) or 0)
            if seed_count > 0:
                # Find nearest empty tile in an unlocked quadrant
                for tile_y, tile_x in board["empty"]:
                    tile_pos = (tile_x, tile_y)
                    quad = self._tile_quad(tile_y, tile_x)
                    if quad in board["unlocked_quads"]:
                        dist = bfs_dist(pos, tile_pos)
                        if dist <= 1:
                            return ["PLANT", crop]
                        elif dist <= 5:
                            return [move_toward(pos, tile_pos)]
                        break  # only try nearest
                break  # only try one crop at a time

        # Priority 8: BUILD structures if needed
        cows_needed = p["target_cows"] - sum(1 for a in board["animals"] if a.get("animal") == "COW")
        sheep_needed = p["target_sheep"] - sum(1 for a in board["animals"] if a.get("animal") == "SHEEP")
        
        if cows_needed > 0:
            # Find empty tile near shed
            for tile_y, tile_x in board["empty"]:
                tile_pos = (tile_x, tile_y)
                if bfs_dist(pos, tile_pos) <= 3:
                    dist = bfs_dist(pos, tile_pos)
                    if dist <= 1:
                        return ["BUILD_PASTURE"]
                    else:
                        return [move_toward(pos, tile_pos)]
            break_point = True

        if sheep_needed > 0:
            for tile_y, tile_x in board["empty"]:
                tile_pos = (tile_x, tile_y)
                if bfs_dist(pos, tile_pos) <= 3:
                    dist = bfs_dist(pos, tile_pos)
                    if dist <= 1:
                        return ["BUILD_PASTURE"]
                    else:
                        return [move_toward(pos, tile_pos)]
                    break

        # Priority 9: WATER normal plants (preventative)
        if p["water_aggression"] >= 1:
            for plant in board["plants"]:
                if not plant["watered_today"] and plant["consec_unwatered"] == 0:
                    tile_pos = (plant["x"], plant["y"])
                    dist = bfs_dist(pos, tile_pos)
                    if dist <= 1:
                        return ["WATER"]
                    elif dist <= 3:
                        return [move_toward(pos, tile_pos)]

        # Priority 10: DIG weeds
        for wy, wx in board["weeds"]:
            tile_pos = (wx, wy)
            dist = bfs_dist(pos, tile_pos)
            if dist <= 1:
                return ["DIG"]
            elif dist <= 2:
                return [move_toward(pos, tile_pos)]

        # Fallback: PASS
        return ["PASS"]

    def _get_crop_priority(self):
        """Return crop list ordered by planting weight."""
        crops = []
        weights = [
            ("WHEAT", self.params.get("crop_wheat", 0.5)),
            ("MELON", self.params.get("crop_melon", 0.2)),
            ("STRAWBERRY", self.params.get("crop_straw", 0.2)),
            ("CARROT", self.params.get("crop_carrot", 0.1)),
            ("TOMATO", self.params.get("crop_tomato", 0.0)),
        ]
        weights.sort(key=lambda x: -x[1])
        return [c for c, w in weights if w > 0]


# ============================================================================
# Kaggle entry point
# ============================================================================

_params = None
_agents = {}

def agent(obs, configuration=None):
    global _params, _agents
    if _params is None:
        _params = dict(DEFAULT_PARAMS)
    seat = int(obs.get("player", 0) or 0)
    if seat not in _agents:
        _agents[seat] = DecisionAgent(_params, seat)
    return _agents[seat].act(obs, configuration)


def set_params(params):
    """Set parameters for the agent (called by search)."""
    global _params, _agents
    _params = params
    _agents = {}  # reset agents so new params take effect


if __name__ == "__main__":
    from kaggle_environments import make
    
    def pass_agent(obs, config=None):
        farm = obs.get("farms", [{}])[obs.get("player", 0)]
        n = len(farm.get("hands", []))
        return {"farmer": ["PASS"], "hands": [["PASS"] for _ in range(n)], "market": []}
    
    # Test with default params
    print("Testing Decision Agent vs PASS (seed 1)...")
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
    result = env.run([agent, pass_agent])
    final = result[-1]
    score = final[0]["observation"]["farms"][0]["money"]
    print(f"Default params: ${score:,.0f}")
    
    # Test with aggressive params
    set_params({
        **DEFAULT_PARAMS,
        "target_cows": 8,
        "target_sheep": 6,
        "daily_hires": 7,
        "crop_melon": 0.4,
        "crop_wheat": 0.3,
        "ne_land_day": 5,
        "sw_land_day": 9,
    })
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
    result = env.run([agent, pass_agent])
    final = result[-1]
    score = final[0]["observation"]["farms"][0]["money"]
    print(f"Aggressive params: ${score:,.0f}")
