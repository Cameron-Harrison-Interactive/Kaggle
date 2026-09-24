#!/usr/bin/env python3
"""Blueprint Player — Reference agent for the route compiler.

Takes a blueprint (what to buy, what to plant where, etc.) and plays it
dumbly — just walks toward targets and executes actions. Doesn't need
optimal paths; the route compiler fixes movement.

BLUEPRINT FORMAT:
{
    "opening": {
        "cows": 1, "sheep": 4,
        "wheat_seeds": 5, "melon_seeds": 5, "straw_seeds": 0,
        "carrot_seeds": 0, "wheat_buy": 5,
        "hires": 4
    },
    "land": {"ne_day": 6, "sw_day": 10, "se_day": -1},
    "plant_layout": {
        # tile -> crop to plant on the FIRST visit
        "NE": {"WHEAT": 15, "MELON": 5, "STRAWBERRY": 5},
        "SW": {"WHEAT": 15, "MELON": 5, "STRAWBERRY": 5},
        "SE": {},
        "NW": {"WHEAT": 5}
    },
    "daily_hires": 5,
    "strategy": "balanced"  # or "wheat_heavy", "animal_heavy", etc.
}
"""

import json
import math
import os
from collections import deque
from kaggle_environments import make

# Board constants
BOARD = 10
HALF = BOARD // 2
SHED_TILES = {(HALF-1, HALF-1), (HALF, HALF-1), (HALF-1, HALF), (HALF, HALF)}

# Quadrant tile sets
QUADS = {
    "NW": [(y, x) for y in range(0, 5) for x in range(0, 5)],
    "NE": [(y, x) for y in range(0, 5) for x in range(5, 10)],
    "SW": [(y, x) for y in range(5, 10) for x in range(0, 5)],
    "SE": [(y, x) for y in range(5, 10) for x in range(5, 10)],
}

# Quad unlock costs and order
LAND_ORDER = ["NE", "SW", "SE"]
LAND_COSTS = {"NE": 1000, "SW": 2000, "SE": 4000}


def bfs_distance(start, goal):
    """BFS distance on 10x10 board. Locked tiles are passable."""
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


def step_toward(pos, goal):
    """Return first step direction from pos toward goal."""
    if pos == goal:
        return None
    px, py = pos
    gx, gy = goal
    dx = gx - px
    dy = gy - py
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    else:
        return "SOUTH" if dy > 0 else "NORTH"


def is_shed_adjacent(pos):
    px, py = pos
    return (py, px) in SHED_TILES


def find_nearest(position, targets):
    """Find nearest target tile from position."""
    if not targets:
        return None, 999
    best = None
    best_d = 999
    for t in targets:
        d = bfs_distance(position, t)
        if d < best_d:
            best_d = d
            best = t
    return best, best_d


# ============================================================================
# THE BLUEPRINT PLAYER
# ============================================================================

class BlueprintPlayer:
    def __init__(self, blueprint, seat=0):
        self.bp = blueprint
        self.seat = seat
        self.state = {
            "turn": 0,
            "day": 0,
            "hour": 0,
            "farmer_pos": (HALF-1, HALF-1),  # starts at shed
            "hands_pos": {},
            "planted_tiles": set(),
            "watered_today": set(),
            "fed_animals": set(),
            "animals_placed": 0,
            "land_unlocked": {"NW": True},
            "pending_land": {},
            "tasks": [],
            "hand_goals": {},  # worker_id -> (target_tile, action)
        }
        self._build_task_list()

    def _build_task_list(self):
        """Pre-compute all anchors from the blueprint."""
        bp = self.bp
        opening = bp.get("opening", {})
        land = bp.get("land", {})
        layout = bp.get("plant_layout", {})
        daily_hires = bp.get("daily_hires", 5)
        
        tasks = []
        
        # Land unlock tasks
        for quad in LAND_ORDER:
            day = land.get(f"{quad.lower()}_day", -1)
            if day >= 0:
                tasks.append({
                    "type": "BUY_LAND",
                    "day": day,
                    "priority": 0,
                    "quad": quad,
                })
        
        # Plant tasks for each quadrant
        for quad, crops in layout.items():
            quad_day = land.get(f"{quad.lower()}_day", -1)
            if quad != "NW" and quad_day < 0:
                continue  # quad locked, skip
            
            tiles = QUADS.get(quad, [])
            crop_list = []
            for crop, count in crops.items():
                crop_list.extend([crop] * count)
            
            for i, tile in enumerate(tiles):
                if i < len(crop_list):
                    crop = crop_list[i]
                    # Plant in first 3 days of quad being available
                    plant_day = quad_day if quad_day >= 0 else 0
                    plant_day = min(plant_day + (i // 10), 15)
                    tasks.append({
                        "type": "PLANT",
                        "day": plant_day,
                        "tile": tile,
                        "crop": crop,
                        "priority": 1,
                    })
        
        # Sort by day then priority
        tasks.sort(key=lambda t: (t["day"], t.get("priority", 9)))
        self.state["tasks"] = tasks
        self.state["daily_hires"] = daily_hires

    def act(self, obs, config=None):
        """Main action function — called every turn."""
        try:
            return self._act_inner(obs, config)
        except Exception as e:
            import traceback
            step = int(obs.get("step", 0) or 0)
            print(f"!!! CRASH at step {step}: {e}")
            traceback.print_exc()
            farm = obs.get("farms", [{}])[obs.get("player", 0)]
            n = len(farm.get("hands", []))
            return {"farmer": ["PASS"], "hands": [["PASS"]]*n, "market": []}

    def _act_inner(self, obs, config=None):
        """Actual logic — wrapped in try/except by act()."""
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        hour = step % 24
        player = int(obs.get("player", 0) or 0)
        
        farm = obs["farms"][player]
        tiles = farm.get("tiles", [])
        hands = farm.get("hands", [])
        money = float(farm.get("money", 0))
        unlocked = farm.get("unlocked_quadrants", [])
        
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}
        seeds = private.get("seeds", {}) or {}
        inventories = private.get("inventories", []) or [{}]
        
        market_obs = obs.get("market", {})
        prices = market_obs.get("prices", {})
        inv = market_obs.get("inventory", {})
        
        # Update state
        self.state["turn"] = step
        self.state["day"] = day
        self.state["hour"] = hour
        self.state["land_unlocked"] = {q: True for q in unlocked}
        
        # Farmer position
        fp = farm.get("farmer", [HALF-1, HALF-1])
        self.state["farmer_pos"] = (fp[0], fp[1])
        
        # Hand positions
        for i, hp in enumerate(hands):
            self.state["hands_pos"][i] = (hp[0], hp[1])
        
        # === MARKET ORDERS ===
        market = []
        
        # Day 0: opening buys
        if step == 0:
            opening = self.bp.get("opening", {})
            for _ in range(opening.get("hires", 4)):
                if len(market) < 10:
                    market.append(["HIRE"])
            cows = opening.get("cows", 0)
            sheep = opening.get("sheep", 0)
            if cows > 0 and len(market) < 10:
                market.append(["BUY_ANIMAL", "COW", cows])
            if sheep > 0 and len(market) < 10:
                market.append(["BUY_ANIMAL", "SHEEP", sheep])
            ws = opening.get("wheat_seeds", 5)
            ms = opening.get("melon_seeds", 5)
            ss = opening.get("straw_seeds", 0)
            cs = opening.get("carrot_seeds", 0)
            if ws > 0 and len(market) < 10: market.append(["BUY_SEED", "WHEAT", ws])
            if ms > 0 and len(market) < 10: market.append(["BUY_SEED", "MELON", ms])
            if ss > 0 and len(market) < 10: market.append(["BUY_SEED", "STRAWBERRY", ss])
            if cs > 0 and len(market) < 10: market.append(["BUY_SEED", "CARROT", cs])
            wb = opening.get("wheat_buy", 5)
            if wb > 0 and len(market) < 10: market.append(["BUY_PRODUCT", "WHEAT", wb])
        
        # Daily hires (at h0 of each day after day 0)
        elif hour == 0 and day > 0:
            n_hires = self.state.get("daily_hires", 5)
            for _ in range(n_hires):
                if len(market) < 10:
                    market.append(["HIRE"])
        
        # Land purchases
        for task in self.state["tasks"]:
            if task["type"] == "BUY_LAND" and task["day"] == day and hour == 0:
                quad = task["quad"]
                if quad not in self.state["land_unlocked"] and len(market) < 10:
                    market.append(["BUY_LAND"])
        
        # Sell everything at game end
        if day >= 28 and hour >= 2:
            for item in ["WHEAT", "STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "FERTILIZER", "CARROT"]:
                qty = int(shed.get(item, 0) or 0)
                if qty > 0 and len(market) < 10:
                    market.append(["SELL", item, qty])
        
        # === FARMER ACTION ===
        farmer_action = ["PASS"]
        hand_actions = [["PASS"] for _ in range(len(hands))]
        
        # Priority 1: FEED unfed animals
        unfed_animals = []
        for y in range(BOARD):
            for x in range(BOARD):
                t = tiles[y][x] if y < len(tiles) and x < len(tiles[y]) else None
                if isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE"):
                    if t.get("animal") and not t.get("fed_today") and t.get("consecutive_unfed", 0) >= 1:
                        unfed_animals.append((y, x))
        
        if unfed_animals and int(shed.get("WHEAT", 0) or 0) > 0:
            # Find nearest unfed animal
            best, dist = find_nearest(self.state["farmer_pos"], [(t[1], t[0]) for t in unfed_animals])
            if best:
                if dist <= 1 and is_shed_adjacent(self.state["farmer_pos"]):
                    farmer_action = ["FEED"]
                elif dist <= 2 and is_shed_adjacent(self.state["farmer_pos"]):
                    farmer_action = ["FEED"]
                else:
                    farmer_action = [step_toward(self.state["farmer_pos"], best) or "PASS"]
        
        # Priority 2: WATER unwatered crops
        if farmer_action == ["PASS"]:
            unwatered = []
            for y in range(BOARD):
                for x in range(BOARD):
                    t = tiles[y][x] if y < len(tiles) and x < len(tiles[y]) else None
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        if not t.get("watered_today") and t.get("consecutive_unwatered", 0) >= 1:
                            unwatered.append((y, x))
            
            if unwatered:
                best, dist = find_nearest(self.state["farmer_pos"], [(t[1], t[0]) for t in unwatered])
                if best:
                    if dist <= 1:
                        farmer_action = ["WATER"]
                    else:
                        farmer_action = [step_toward(self.state["farmer_pos"], best) or "PASS"]
        
        # Priority 3: HARVEST ripe crops
        if farmer_action == ["PASS"]:
            ripe = []
            for y in range(BOARD):
                for x in range(BOARD):
                    t = tiles[y][x] if y < len(tiles) and x < len(tiles[y]) else None
                    if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("yield_units", 0) > 0:
                        ripe.append((y, x))
            
            if ripe:
                best, dist = find_nearest(self.state["farmer_pos"], [(t[1], t[0]) for t in ripe])
                if best:
                    if dist <= 1:
                        farmer_action = ["HARVEST"]
                    else:
                        farmer_action = [step_toward(self.state["farmer_pos"], best) or "PASS"]
        
        # Priority 4: CARE animals
        if farmer_action == ["PASS"]:
            uncare = []
            for y in range(BOARD):
                for x in range(BOARD):
                    t = tiles[y][x] if y < len(tiles) and x < len(tiles[y]) else None
                    if isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE"):
                        if t.get("animal") and not t.get("cared_today"):
                            uncare.append((y, x))
            
            if uncare:
                best, dist = find_nearest(self.state["farmer_pos"], [(t[1], t[0]) for t in uncare])
                if best:
                    if dist <= 1:
                        farmer_action = ["CARE"]
                    else:
                        farmer_action = [step_toward(self.state["farmer_pos"], best) or "PASS"]
        
        # Priority 5: COLLECT FERTILIZER
        if farmer_action == ["PASS"]:
            fert_ready = []
            for y in range(BOARD):
                for x in range(BOARD):
                    t = tiles[y][x] if y < len(tiles) and x < len(tiles[y]) else None
                    if isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE"):
                        if t.get("animal") and t.get("fertilizer_available"):
                            fert_ready.append((y, x))
            
            if fert_ready:
                best, dist = find_nearest(self.state["farmer_pos"], [(t[1], t[0]) for t in fert_ready])
                if best:
                    if dist <= 1:
                        farmer_action = ["COLLECT_FERTILIZER"]
                    else:
                        farmer_action = [step_toward(self.state["farmer_pos"], best) or "PASS"]
        
        # Priority 6: PLANT seeds (walk to empty tiles and plant)
        if farmer_action == ["PASS"]:
            # Find pending plant tasks for today
            today_plants = [t for t in self.state["tasks"] 
                          if t["type"] == "PLANT" and t["day"] <= day 
                          and t["tile"] not in self.state["planted_tiles"]]
            
            if today_plants:
                task = today_plants[0]
                tile = task["tile"]
                tile_pos = (tile[1], tile[0])  # convert to (x, y)
                crop = task["crop"]
                
                # Check we have seeds
                seed_type = crop if crop != "STRAWBERRY" else "STRAWBERRY"
                seed_count = int(seeds.get(seed_type, 0) or 0)
                
                # DEBUG
                if step < 30:
                    print(f"  [DEBUG s{step}] PLANT check: crop={crop} tile={tile} "
                          f"seeds={seed_count} farmer_pos={self.state['farmer_pos']} "
                          f"tile_pos={tile_pos} dist={bfs_distance(self.state['farmer_pos'], tile_pos)} "
                          f"planted_so_far={len(self.state['planted_tiles'])}")
                
                if seed_count > 0:
                    dist = bfs_distance(self.state["farmer_pos"], tile_pos)
                    if dist <= 1:
                        farmer_action = ["PLANT", crop]
                        self.state["planted_tiles"].add(tile)
                    else:
                        farmer_action = [step_toward(self.state["farmer_pos"], tile_pos) or "PASS"]
                elif step < 30:
                    print(f"  [DEBUG s{step}] NO SEEDS for {crop}! seeds dict: {dict(seeds)}")
        
        # Priority 7: PLACE animals
        if farmer_action == ["PASS"]:
            farmer_inv = inventories[0] if inventories else {}
            for animal_type in ["COW", "SHEEP"]:
                if int(farmer_inv.get(animal_type, 0) or 0) > 0:
                    # Find empty structure
                    for y in range(BOARD):
                        for x in range(BOARD):
                            t = tiles[y][x] if y < len(tiles) and x < len(tiles[y]) else None
                            if isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and not t.get("animal"):
                                tile_pos = (x, y)
                                dist = bfs_distance(self.state["farmer_pos"], tile_pos)
                                if dist <= 1:
                                    farmer_action = ["PLACE", animal_type, 1]
                                else:
                                    farmer_action = [step_toward(self.state["farmer_pos"], tile_pos) or "PASS"]
                                break
                        if farmer_action != ["PASS"]:
                            break
                    if farmer_action != ["PASS"]:
                        break
        
        # === HAND ACTIONS ===
        # Workers do the same priorities as farmer but spread across tiles
        for hi in range(len(hands)):
            hand_pos = self.state["hands_pos"].get(hi, (HALF-1, HALF-1))
            
            # FEED unfed animals near this hand
            fed = False
            for ay, ax in unfed_animals:
                d = bfs_distance(hand_pos, (ax, ay))
                if d <= 2 and is_shed_adjacent(hand_pos) and int(shed.get("WHEAT", 0) or 0) > 0:
                    if d <= 1:
                        hand_actions[hi] = ["FEED"]
                    else:
                        hand_actions[hi] = [step_toward(hand_pos, (ax, ay)) or "PASS"]
                    fed = True
                    break
            if fed:
                continue
            
            # WATER unwatered crops
            watered = False
            for uy, ux in unwatered:
                d = bfs_distance(hand_pos, (ux, uy))
                if d <= 3:
                    if d <= 1:
                        hand_actions[hi] = ["WATER"]
                    else:
                        hand_actions[hi] = [step_toward(hand_pos, (ux, uy)) or "PASS"]
                    watered = True
                    break
            if watered:
                continue
            
            # HARVEST ripe
            harvested = False
            for ry, rx in ripe:
                d = bfs_distance(hand_pos, (rx, ry))
                if d <= 3:
                    if d <= 1:
                        hand_actions[hi] = ["HARVEST"]
                    else:
                        hand_actions[hi] = [step_toward(hand_pos, (rx, ry)) or "PASS"]
                    harvested = True
                    break
            if harvested:
                continue
            
            # CARE animals
            cared = False
            for cy, cx in uncare:
                d = bfs_distance(hand_pos, (cx, cy))
                if d <= 2:
                    if d <= 1:
                        hand_actions[hi] = ["CARE"]
                    else:
                        hand_actions[hi] = [step_toward(hand_pos, (cx, cy)) or "PASS"]
                    cared = True
                    break
            if cared:
                continue
        
        return {
            "farmer": farmer_action,
            "hands": hand_actions,
            "market": market[:10],
        }


# ============================================================================
# MAIN — play a blueprint vs PASS to generate a reference tape
# ============================================================================

def play_blueprint(blueprint, seed=1, seat=0):
    """Play a blueprint vs PASS and return (tape, obs_history, reward)."""
    player = BlueprintPlayer(blueprint, seat)
    
    tape = []
    obs_history = []
    
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    
    def record_and_play(obs, config=None):
        act = player.act(obs, config)
        tape.append({
            "market": [list(o) for o in act.get("market", [])],
            "farmer": list(act.get("farmer", ["PASS"])),
            "hands": [list(h) for h in act.get("hands", [])],
        })
        return act
    
    pass_agent_fn = lambda obs, config=None: {
        "market": [],
        "farmer": ["PASS"],
        "hands": [["PASS"]] * len(obs["farms"][obs["player"]].get("hands", [])),
    }
    
    if seat == 0:
        env.run([record_and_play, pass_agent_fn])
        reward = env.steps[-1][0].get("reward", 0) or 0
    else:
        env.run([pass_agent_fn, record_and_play])
        reward = env.steps[-1][1].get("reward", 0) or 0
    
    for step_data in env.steps:
        obs = step_data[seat].get("observation", {}) or {}
        obs_history.append(obs)
    
    return tape, obs_history, reward


if __name__ == "__main__":
    # Test blueprint
    test_bp = {
        "opening": {
            "cows": 1, "sheep": 4,
            "wheat_seeds": 5, "melon_seeds": 5,
            "straw_seeds": 0, "carrot_seeds": 0,
            "wheat_buy": 5, "hires": 4
        },
        "land": {"ne_day": 6, "sw_day": 10, "se_day": -1},
        "plant_layout": {
            "NW": {"WHEAT": 10, "MELON": 5},
            "NE": {"WHEAT": 15, "MELON": 5, "STRAWBERRY": 5},
            "SW": {"WHEAT": 15, "MELON": 5, "STRAWBERRY": 5},
            "SE": {},
        },
        "daily_hires": 5,
    }
    
    print("Playing blueprint vs PASS (seed 1)...")
    tape, obs_history, reward = play_blueprint(test_bp, seed=1, seat=0)
    print(f"Reward: ${reward:,.0f}")
    print(f"Tape length: {len(tape)} steps")
    
    # Save
    os.makedirs("data/blueprints", exist_ok=True)
    with open("data/blueprints/test_tape.json", "w") as f:
        json.dump(tape, f)
    print("Saved to data/blueprints/test_tape.json")
    
    # Debug: show first 20 steps
    print("\n--- First 20 steps ---")
    for i, step in enumerate(tape[:20]):
        mkt = ', '.join([' '.join(str(x) for x in o) for o in step.get('market', [])])
        farmer = step.get('farmer', ['PASS'])
        n_hands = len(step.get('hands', []))
        print(f"  s{i:3d}: farmer={farmer[0]:15s} hands={n_hands} market=[{mkt[:60]}]")
