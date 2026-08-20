"""Massive Strategy Search for Kaggriculture.

Systematically explores fundamentally different farming strategies.
Each strategy is a parameterized agent that makes decisions each turn.
Tests across multiple seeds, both seats, vs multiple opponents.

Strategy families:
1. WheatArb — wheat arbitrage (like #1 Kawashigi): buy wheat low, sell high volume
2. SheepLord — heavy sheep, wool income, minimal cows
3. StrawBlitz — aggressive strawberry with different timing
4. GooseFarm — egg-focused, daily income
5. ConservativeCash — minimal animals, pure crop efficiency
6. BalancedPortfolio — diversified approach
7. QuadRush — early land expansion
"""

import json
import math
import sys
import os
import time
import random
from collections import defaultdict

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.price_predictor import (
    compute_price, predict_sell_price, predict_buy_price,
    market_state_summary, RESOURCES
)


# ============================================================================
# STRATEGY DEFINITIONS — each is a set of parameters that define an agent
# ============================================================================

STRATEGY_PROFILES = {
    # ---- Wheat Arbitrage variants (like #1 Kawashigi) ----
    "wheatarb_heavy": {
        "name": "WheatArb-Heavy",
        "opening": "wheat_heavy",
        "wheat_seeds_d0": 7,       # more wheat seeds
        "melon_seeds_d0": 2,       # fewer melons
        "sheep_d0": 2,             # fewer sheep
        "cow_d0": 1,               # minimal cows
        "wheat_buy_target": 50,    # buy lots of wheat
        "sell_threshold_ratio": 1.1,  # sell when 10% above base
        "buy_threshold_ratio": 0.95,  # buy when near base
        "quad_ne_day": 5,          # early NE buy
        "quad_sw_day": 9,          # early SW buy
        "hire_per_day": 6,         # heavy hiring
        "strawberry_plant": False, # no strawberries
        "focus": "wheat_volume",
    },
    "wheatarb_mod": {
        "name": "WheatArb-Mod",
        "opening": "wheat_mod",
        "wheat_seeds_d0": 5,
        "melon_seeds_d0": 4,
        "sheep_d0": 3,
        "cow_d0": 1,
        "wheat_buy_target": 30,
        "sell_threshold_ratio": 1.05,
        "buy_threshold_ratio": 0.98,
        "quad_ne_day": 6,
        "quad_sw_day": 10,
        "hire_per_day": 5,
        "strawberry_plant": True,
        "focus": "wheat_balance",
    },
    
    # ---- Sheep-heavy variants ----
    "sheep_heavy": {
        "name": "SheepLord-Heavy",
        "opening": "sheep_heavy",
        "wheat_seeds_d0": 4,
        "melon_seeds_d0": 3,
        "sheep_d0": 4,
        "cow_d0": 0,               # no cows!
        "wheat_buy_target": 20,    # need wheat for feed
        "sell_threshold_ratio": 1.0,
        "buy_threshold_ratio": 1.0,
        "quad_ne_day": 7,
        "quad_sw_day": 11,
        "hire_per_day": 4,
        "strawberry_plant": True,
        "focus": "wool_volume",
    },
    "sheep_balanced": {
        "name": "SheepLord-Bal",
        "opening": "sheep_bal",
        "wheat_seeds_d0": 5,
        "melon_seeds_d0": 3,
        "sheep_d0": 4,
        "cow_d0": 1,
        "wheat_buy_target": 25,
        "sell_threshold_ratio": 1.05,
        "buy_threshold_ratio": 1.0,
        "quad_ne_day": 7,
        "quad_sw_day": 10,
        "hire_per_day": 5,
        "strawberry_plant": True,
        "focus": "wool_milk_mix",
    },
    
    # ---- Strawberry blitz variants ----
    "straw_blitz": {
        "name": "StrawBlitz",
        "opening": "straw_blitz",
        "wheat_seeds_d0": 4,
        "melon_seeds_d0": 2,
        "sheep_d0": 2,
        "cow_d0": 1,
        "wheat_buy_target": 15,
        "sell_threshold_ratio": 1.0,
        "buy_threshold_ratio": 1.0,
        "quad_ne_day": 6,
        "quad_sw_day": 9,
        "hire_per_day": 6,
        "strawberry_plant": True,
        "straw_target": 40,        # lots of strawberries
        "straw_plant_days": [7, 8, 9, 10, 11],
        "focus": "strawberry_volume",
    },
    
    # ---- Conservative cash (minimal animals, pure crops) ----
    "conservative": {
        "name": "ConservCash",
        "opening": "conservative",
        "wheat_seeds_d0": 5,
        "melon_seeds_d0": 5,
        "sheep_d0": 2,
        "cow_d0": 1,
        "wheat_buy_target": 10,
        "sell_threshold_ratio": 1.0,
        "buy_threshold_ratio": 1.0,
        "quad_ne_day": 8,
        "quad_sw_day": 12,
        "hire_per_day": 4,
        "strawberry_plant": True,
        "focus": "efficiency",
    },
    
    # ---- Balanced portfolio ----
    "balanced": {
        "name": "BalancedPortfolio",
        "opening": "balanced",
        "wheat_seeds_d0": 5,
        "melon_seeds_d0": 4,
        "sheep_d0": 3,
        "cow_d0": 1,
        "wheat_buy_target": 15,
        "sell_threshold_ratio": 1.05,
        "buy_threshold_ratio": 1.0,
        "quad_ne_day": 7,
        "quad_sw_day": 10,
        "hire_per_day": 5,
        "strawberry_plant": True,
        "focus": "diversified",
    },
    
    # ---- Quad rush (early expansion) ----
    "quad_rush": {
        "name": "QuadRush",
        "opening": "quad_rush",
        "wheat_seeds_d0": 4,
        "melon_seeds_d0": 3,
        "sheep_d0": 2,
        "cow_d0": 1,
        "wheat_buy_target": 10,
        "sell_threshold_ratio": 1.0,
        "buy_threshold_ratio": 1.0,
        "quad_ne_day": 4,          # very early NE
        "quad_sw_day": 7,          # early SW
        "quad_se_day": 12,         # SE too
        "hire_per_day": 6,
        "strawberry_plant": True,
        "focus": "land_expansion",
    },
}


# ============================================================================
# DECISION-BASED AGENT — makes choices each turn from game state
# ============================================================================

class FarmState:
    """Track internal state for the decision agent."""
    def __init__(self):
        self.memory = {}
        self.turn_count = 0
        self.total_wheat_bought = 0
        self.total_wheat_sold = 0
        self.sell_queue = []  # planned sells
        self.last_water_day = {}  # tile -> day
        self.strategy = None
    
    def update(self, obs):
        self.turn_count += 1


def make_decision_agent(strategy_name):
    """Create an agent function for a given strategy profile."""
    profile = STRATEGY_PROFILES[strategy_name]
    state = {"init": False, "mem": {}, "plan": {}}
    
    def agent(obs, configuration=None):
        try:
            step = int(obs.get("step", 0) or 0)
            day = step // 24
            hour = step % 24
            farm = obs["farms"][obs.get("player", 0)]
            opp_farm = obs["farms"][1 - obs.get("player", 0)]
            market = obs.get("market", {})
            prices = market.get("prices", {})
            inv = market.get("inventory", {})
            private = obs.get("private", {})
            shed = private.get("shed", {})
            seeds = private.get("seeds", {})
            tiles = farm.get("tiles", [])
            money = farm.get("money", 0)
            hands_list = farm.get("hands", [])
            n_hands = len(hands_list)
            quads = farm.get("unlocked_quadrants", [])
            hires_today = farm.get("hires_today", 0)
            
            board_size = len(tiles) if tiles else 10
            half = board_size // 2
            
            # Initialize memory
            if not state["init"]:
                state["init"] = True
                state["mem"] = {
                    "wheat_bought": 0,
                    "wheat_sold": 0,
                    "straw_sold": 0,
                    "day_plans": {},
                    "priority": profile.get("focus", "balanced"),
                }
            
            mem = state["mem"]
            farmer_pos = farm.get("farmer", [half-1, half-1])
            
            # ---- MARKET ORDERS ----
            market_orders = []
            
            # Day 0 opening
            if day == 0 and hour == 0:
                # Hire workers
                for _ in range(min(profile["hire_per_day"], 10)):
                    market_orders.append(["HIRE"])
                
                # Buy animals
                for _ in range(profile["sheep_d0"]):
                    market_orders.append(["BUY_ANIMAL", "SHEEP", 1])
                for _ in range(profile["cow_d0"]):
                    market_orders.append(["BUY_ANIMAL", "COW", 1])
                
                # Buy seeds
                market_orders.append(["BUY_SEED", "WHEAT", profile["wheat_seeds_d0"]])
                market_orders.append(["BUY_SEED", "MELON", profile["melon_seeds_d0"]])
                
                # Buy wheat for feed
                market_orders.append(["BUY_PRODUCT", "WHEAT", 5])
                
                return {
                    "farmer": ["PASS"],
                    "hands": [["PASS"] for _ in range(n_hands)],
                    "market": market_orders[:10],
                }
            
            # Daily hire
            if hour == 0 and day >= 1:
                daily_hires = min(profile["hire_per_day"], 8)
                for _ in range(daily_hires):
                    market_orders.append(["HIRE"])
            
            # Wheat buying (arbitrage strategy)
            wheat_target = profile.get("wheat_buy_target", 15)
            wheat_price = prices.get("WHEAT", 25)
            if mem["wheat_bought"] < wheat_target and wheat_price <= 30 and money > 2000:
                buy_qty = min(5, wheat_target - mem["wheat_bought"])
                if buy_qty > 0 and hour == 1:
                    market_orders.append(["BUY_PRODUCT", "WHEAT", buy_qty])
                    mem["wheat_bought"] += buy_qty
            
            # Smart selling — use price predictor
            wheat_inv = inv.get("WHEAT", 10000)
            shed_wheat = shed.get("WHEAT", 0)
            if shed_wheat > 0 and hour >= 1:
                current_wheat_price = prices.get("WHEAT", 25)
                base_wheat = 25
                threshold = base_wheat * profile.get("sell_threshold_ratio", 1.0)
                
                if current_wheat_price >= threshold or day >= 25:
                    sell_qty = min(shed_wheat, 20)
                    market_orders.append(["SELL", "WHEAT", sell_qty])
            
            # Sell milk/wool/eggs when shed has them
            for item in ["MILK", "WOOL", "EGG", "STRAWBERRY", "MELON"]:
                item_qty = shed.get(item, 0)
                if item_qty > 0 and hour >= 1:
                    item_price = prices.get(item, RESOURCES.get(item, {}).get("base", 50))
                    base_price = RESOURCES.get(item, {}).get("base", 50)
                    threshold = base_price * profile.get("sell_threshold_ratio", 1.0)
                    
                    if item_price >= threshold * 0.9 or day >= 25:
                        sell_qty = min(item_qty, 15)
                        market_orders.append(["SELL", item, sell_qty])
            
            # Sell fertilizer
            fert = shed.get("FERTILIZER", 0)
            if fert > 0 and hour >= 1:
                market_orders.append(["SELL", "FERTILIZER", min(fert, 5)])
            
            # Land expansion
            if "NE" not in quads and day >= profile.get("quad_ne_day", 7) and money > 3000 and hour == 0:
                market_orders.insert(0, ["BUY_LAND"])
            if "NE" in quads and "SW" not in quads and day >= profile.get("quad_sw_day", 10) and money > 5000 and hour == 0:
                market_orders.insert(0, ["BUY_LAND"])
            
            # Strawberry planting
            if profile.get("strawberry_plant") and profile.get("straw_target", 0) > 0:
                straw_days = profile.get("straw_plant_days", [8, 9, 10])
                if day in straw_days and hour == 0 and seeds.get("STRAWBERRY", 0) == 0 and money > 1500:
                    market_orders.append(["BUY_SEED", "STRAWBERRY", 6])
            
            # ---- FARMER ACTION ----
            farmer_action = ["PASS"]
            hand_actions = [["PASS"] for _ in range(n_hands)]
            
            # Get tile state for decisions
            plant_tiles = []  # (y, x, tile_dict)
            weed_tiles = []
            empty_tiles = []
            animal_structures = []  # (y, x, tile_dict)
            
            for y in range(board_size):
                for x in range(board_size):
                    if y < len(tiles) and x < len(tiles[y]):
                        t = tiles[y][x]
                    else:
                        continue
                    if t is None:
                        empty_tiles.append((y, x))
                    elif t == "LOCKED":
                        continue
                    elif isinstance(t, dict):
                        if t.get("kind") == "PLANT":
                            plant_tiles.append((y, x, t))
                        elif t.get("kind") == "WEED":
                            weed_tiles.append((y, x))
                        elif t.get("kind") in ("COOP", "PASTURE"):
                            animal_structures.append((y, x, t))
            
            # Priority 1: Feed animals (prevent escapes)
            unfed_animals = [(y, x, t) for y, x, t in animal_structures 
                           if t.get("animal") and not t.get("fed_today") 
                           and t.get("consecutive_unfed", 0) >= 1]
            
            if unfed_animals and shed.get("WHEAT", 0) > 0:
                # Find closest unfed animal to farmer
                best = None
                best_dist = 999
                for y, x, t in unfed_animals:
                    dist = abs(y - farmer_pos[1]) + abs(x - farmer_pos[0])
                    if dist < best_dist:
                        best_dist = dist
                        best = (y, x, t)
                
                if best and best_dist <= 1:
                    farmer_action = ["FEED"]
                elif best and best_dist <= 6:
                    # Move toward it
                    dy = best[0] - farmer_pos[1]
                    dx = best[1] - farmer_pos[0]
                    if abs(dx) >= abs(dy):
                        farmer_action = ["EAST"] if dx > 0 else ["WEST"] if dx < 0 else ["PASS"]
                    else:
                        farmer_action = ["SOUTH"] if dy > 0 else ["NORTH"] if dy < 0 else ["PASS"]
            
            # Priority 2: Water unwatered plants
            if farmer_action == ["PASS"]:
                unwatered = [(y, x, t) for y, x, t in plant_tiles 
                           if not t.get("watered_today") 
                           and t.get("consecutive_unwatered", 0) >= 1]
                if unwatered:
                    best = None
                    best_dist = 999
                    for y, x, t in unwatered:
                        dist = abs(y - farmer_pos[1]) + abs(x - farmer_pos[0])
                        if dist < best_dist:
                            best_dist = dist
                            best = (y, x)
                    
                    if best and best_dist <= 1:
                        farmer_action = ["WATER"]
                    elif best and best_dist <= 5:
                        dy = best[0] - farmer_pos[1]
                        dx = best[1] - farmer_pos[0]
                        if abs(dx) >= abs(dy):
                            farmer_action = ["EAST"] if dx > 0 else ["WEST"] if dx < 0 else ["PASS"]
                        else:
                            farmer_action = ["SOUTH"] if dy > 0 else ["NORTH"] if dy < 0 else ["PASS"]
            
            # Priority 3: Harvest ripe crops
            if farmer_action == ["PASS"]:
                harvestable = [(y, x, t) for y, x, t in plant_tiles 
                             if t.get("yield_units", 0) > 0]
                if harvestable:
                    best = None
                    best_dist = 999
                    for y, x, t in harvestable:
                        dist = abs(y - farmer_pos[1]) + abs(x - farmer_pos[0])
                        if dist < best_dist:
                            best_dist = dist
                            best = (y, x)
                    if best and best_dist <= 1:
                        farmer_action = ["HARVEST"]
                    elif best and best_dist <= 4:
                        dy = best[0] - farmer_pos[1]
                        dx = best[1] - farmer_pos[0]
                        if abs(dx) >= abs(dy):
                            farmer_action = ["EAST"] if dx > 0 else ["WEST"] if dx < 0 else ["PASS"]
                        else:
                            farmer_action = ["SOUTH"] if dy > 0 else ["NORTH"] if dy < 0 else ["PASS"]
            
            # Priority 4: Care for animals
            if farmer_action == ["PASS"]:
                uncareed = [(y, x, t) for y, x, t in animal_structures 
                          if t.get("animal") and not t.get("cared_today")]
                if uncareed:
                    best = min(uncareed, key=lambda a: abs(a[0]-farmer_pos[1]) + abs(a[1]-farmer_pos[0]))
                    dist = abs(best[0] - farmer_pos[1]) + abs(best[1] - farmer_pos[0])
                    if dist <= 1:
                        farmer_action = ["CARE"]
                    elif dist <= 4:
                        dy = best[0] - farmer_pos[1]
                        dx = best[1] - farmer_pos[0]
                        if abs(dx) >= abs(dy):
                            farmer_action = ["EAST"] if dx > 0 else ["WEST"] if dx < 0 else ["PASS"]
                        else:
                            farmer_action = ["SOUTH"] if dy > 0 else ["NORTH"] if dy < 0 else ["PASS"]
            
            # Priority 5: Collect fertilizer
            if farmer_action == ["PASS"]:
                fert_animals = [(y, x, t) for y, x, t in animal_structures 
                              if t.get("animal") and t.get("fertilizer_available")]
                if fert_animals:
                    best = min(fert_animals, key=lambda a: abs(a[0]-farmer_pos[1]) + abs(a[1]-farmer_pos[0]))
                    dist = abs(best[0] - farmer_pos[1]) + abs(best[1] - farmer_pos[0])
                    if dist <= 1:
                        farmer_action = ["COLLECT_FERTILIZER"]
                    elif dist <= 3:
                        dy = best[0] - farmer_pos[1]
                        dx = best[1] - farmer_pos[0]
                        if abs(dx) >= abs(dy):
                            farmer_action = ["EAST"] if dx > 0 else ["WEST"] if dx < 0 else ["PASS"]
                        else:
                            farmer_action = ["SOUTH"] if dy > 0 else ["NORTH"] if dy < 0 else ["PASS"]
            
            # Priority 6: Plant seeds
            if farmer_action == ["PASS"] and empty_tiles:
                can_plant = []
                for crop_type in ["WHEAT", "MELON", "STRAWBERRY", "CARROT"]:
                    if seeds.get(crop_type, 0) > 0:
                        can_plant.append(crop_type)
                if can_plant:
                    # Find an empty tile near farmer
                    best_tile = min(empty_tiles, 
                                  key=lambda t: abs(t[0]-farmer_pos[1]) + abs(t[1]-farmer_pos[0]))
                    dist = abs(best_tile[0] - farmer_pos[1]) + abs(best_tile[1] - farmer_pos[0])
                    if dist <= 1:
                        farmer_action = ["PLANT", can_plant[0]]
                    elif dist <= 3:
                        dy = best_tile[0] - farmer_pos[1]
                        dx = best_tile[1] - farmer_pos[0]
                        if abs(dx) >= abs(dy):
                            farmer_action = ["EAST"] if dx > 0 else ["WEST"] if dx < 0 else ["PASS"]
                        else:
                            farmer_action = ["SOUTH"] if dy > 0 else ["NORTH"] if dy < 0 else ["PASS"]
            
            # Priority 7: Build structures
            if farmer_action == ["PASS"] and day <= 8:
                # Place animals if we have them in inventory
                inv_data = private.get("inventories", [{}])
                farmer_inv = inv_data[0] if inv_data else {}
                for animal_type in ["COW", "SHEEP", "GOOSE"]:
                    if farmer_inv.get(animal_type, 0) > 0:
                        # Find empty structure
                        empty_struct = [(y, x, t) for y, x, t in animal_structures
                                      if t.get("animal") is None and t.get("kind") in ("COOP", "PASTURE")]
                        if empty_struct:
                            best = min(empty_struct, key=lambda a: abs(a[0]-farmer_pos[1]) + abs(a[1]-farmer_pos[0]))
                            dist = abs(best[0] - farmer_pos[1]) + abs(best[1] - farmer_pos[0])
                            if dist <= 1:
                                farmer_action = ["PLACE", animal_type, 1]
                                break
                            elif dist <= 3:
                                dy = best[0] - farmer_pos[1]
                                dx = best[1] - farmer_pos[0]
                                if abs(dx) >= abs(dy):
                                    farmer_action = ["EAST"] if dx > 0 else ["WEST"] if dx < 0 else ["PASS"]
                                else:
                                    farmer_action = ["SOUTH"] if dy > 0 else ["NORTH"] if dy < 0 else ["PASS"]
                                break
            
            # Priority 8: Build pasture/coop
            if farmer_action == ["PASS"] and day <= 5 and empty_tiles:
                n_pastures = sum(1 for _,_,t in animal_structures if t.get("kind") == "PASTURE")
                n_coops = sum(1 for _,_,t in animal_structures if t.get("kind") == "COOP")
                if n_pastures < profile.get("cow_d0", 0) + profile.get("sheep_d0", 0) + 2:
                    # Build near shed
                    center_tiles = [(half-1, half-1), (half, half-1), (half-1, half), (half, half)]
                    for cy, cx in center_tiles:
                        if (cy, cx) in [(t[0], t[1]) for t in empty_tiles]:
                            farmer_action = ["BUILD_PASTURE"]
                            break
            
            # Hands: assign to watering, feeding, harvesting
            for i in range(n_hands):
                hand_pos = hands_list[i] if i < len(hands_list) else [half-1, half-1]
                hand_inv = private.get("inventories", [{}]*(n_hands+1))
                
                # Feed animals if close
                if unfed_animals and shed.get("WHEAT", 0) > len(unfed_animals):
                    for ay, ax, at in unfed_animals:
                        dist = abs(ay - hand_pos[1]) + abs(ax - hand_pos[0])
                        if dist <= 1:
                            hand_actions[i] = ["FEED"]
                            break
                        elif dist <= 3 and hand_actions[i] == ["PASS"]:
                            dy = ay - hand_pos[1]
                            dx = ax - hand_pos[0]
                            if abs(dx) >= abs(dy):
                                hand_actions[i] = ["EAST"] if dx > 0 else ["WEST"]
                            else:
                                hand_actions[i] = ["SOUTH"] if dy > 0 else ["NORTH"]
                
                # Water plants
                if hand_actions[i] == ["PASS"]:
                    for py, px, pt in plant_tiles:
                        if not pt.get("watered_today") and pt.get("consecutive_unwatered", 0) >= 1:
                            dist = abs(py - hand_pos[1]) + abs(px - hand_pos[0])
                            if dist <= 1:
                                hand_actions[i] = ["WATER"]
                                break
                            elif dist <= 4:
                                dy = py - hand_pos[1]
                                dx = px - hand_pos[0]
                                if abs(dx) >= abs(dy):
                                    hand_actions[i] = ["EAST"] if dx > 0 else ["WEST"]
                                else:
                                    hand_actions[i] = ["SOUTH"] if dy > 0 else ["NORTH"]
                                break
                
                # Harvest
                if hand_actions[i] == ["PASS"]:
                    for py, px, pt in plant_tiles:
                        if pt.get("yield_units", 0) > 0:
                            dist = abs(py - hand_pos[1]) + abs(px - hand_pos[0])
                            if dist <= 1:
                                hand_actions[i] = ["HARVEST"]
                                break
                            elif dist <= 3:
                                dy = py - hand_pos[1]
                                dx = px - hand_pos[0]
                                if abs(dx) >= abs(dy):
                                    hand_actions[i] = ["EAST"] if dx > 0 else ["WEST"]
                                else:
                                    hand_actions[i] = ["SOUTH"] if dy > 0 else ["NORTH"]
                                break
                
                # Plant
                if hand_actions[i] == ["PASS"] and can_plant if 'can_plant' in dir() else False:
                    for et_y, et_x in empty_tiles:
                        dist = abs(et_y - hand_pos[1]) + abs(et_x - hand_pos[0])
                        if dist <= 1:
                            hand_actions[i] = ["PLANT", can_plant[0]]
                            break
                        elif dist <= 2:
                            dy = et_y - hand_pos[1]
                            dx = et_x - hand_pos[0]
                            if abs(dx) >= abs(dy):
                                hand_actions[i] = ["EAST"] if dx > 0 else ["WEST"]
                            else:
                                hand_actions[i] = ["SOUTH"] if dy > 0 else ["NORTH"]
                            break
                
                # Dig weeds
                if hand_actions[i] == ["PASS"] and weed_tiles:
                    for wy, wx in weed_tiles:
                        dist = abs(wy - hand_pos[1]) + abs(wx - hand_pos[0])
                        if dist <= 1:
                            hand_actions[i] = ["DIG"]
                            break
                        elif dist <= 2:
                            dy = wy - hand_pos[1]
                            dx = wx - hand_pos[0]
                            if abs(dx) >= abs(dy):
                                hand_actions[i] = ["EAST"] if dx > 0 else ["WEST"]
                            else:
                                hand_actions[i] = ["SOUTH"] if dy > 0 else ["NORTH"]
                            break
            
            # Drop inventory at shed (end of day will auto-drop, but PLACE helps)
            # Actually the end-of-day auto-drop handles this
            
            return {
                "farmer": farmer_action,
                "hands": hand_actions,
                "market": market_orders[:10],
            }
        except Exception as e:
            # Safe fallback
            farm = obs.get("farms", [{}])[obs.get("player", 0)]
            n_hands = len(farm.get("hands", []))
            return {
                "farmer": ["PASS"],
                "hands": [["PASS"] for _ in range(n_hands)],
                "market": [],
            }
    
    return agent


def create_agent_file(strategy_name, output_path):
    """Generate a standalone agent file for a strategy."""
    profile = STRATEGY_PROFILES[strategy_name]
    
    code = f'''"""Kaggriculture agent — {profile["name"]} strategy.

Auto-generated by massive_search.py
Strategy focus: {profile["focus"]}
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
from scripts.massive_search import make_decision_agent

_agent_fn = make_decision_agent("{strategy_name}")

def agent(obs, configuration=None):
    return _agent_fn(obs, configuration)
'''
    with open(output_path, "w") as f:
        f.write(code)
    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Massive Strategy Search")
    parser.add_argument("--strategy", type=str, default="all",
                       help="Strategy name or 'all'")
    parser.add_argument("--seeds", type=str, default="1,2,3,4,5",
                       help="Comma-separated seed list")
    parser.add_argument("--vs", type=str, default="self",
                       help="Opponent agent path or 'self'")
    args = parser.parse_args()
    
    from battle_harness import run_battery, print_results
    
    seeds = [int(s) for s in args.seeds.split(",")]
    
    strategies = [args.strategy] if args.strategy != "all" else list(STRATEGY_PROFILES.keys())
    
    for strat in strategies:
        print(f"\n{'#'*60}")
        print(f"  Testing strategy: {STRATEGY_PROFILES[strat]['name']}")
        print(f"{'#'*60}")
        
        # Create temp agent file
        agent_path = f"/tmp/agent_{strat}.py"
        create_agent_file(strat, agent_path)
        
        if args.vs == "self":
            results = run_battery(agent_path, agent_path, seeds=seeds,
                                label=STRATEGY_PROFILES[strat]["name"])
        else:
            results = run_battery(agent_path, args.vs, seeds=seeds,
                                label=STRATEGY_PROFILES[strat]["name"])
        
        print_results(results)
