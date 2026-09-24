"""Market Warfare Engine — Real-time opponent tracking + price exploitation.

CORE CONCEPT:
  Watch what the opponent does → predict their moves → exploit price movements.
  
  If opponent dumps wheat → price crashes → we BUY low → wait for recovery → SELL high
  If opponent hoards animals → wheat demand spikes → we SELL wheat at premium
  If opponent floods strawberry → price collapses → we avoid strawberry, sell something else

OBSERVABLE DATA (from game rules):
  - Opponent's farm tiles (crops, animals, structures) — PUBLIC
  - Opponent's money — PUBLIC
  - Opponent's unlocked quadrants — PUBLIC
  - Market inventory + prices — SHARED (both see same)
  - Town shops — SHARED
  
NOT OBSERVABLE:
  - Opponent's shed inventory — PRIVATE
  - Opponent's worker actions — PRIVATE
  - Opponent's market orders — only see the RESULT (price/inventory change)

STRATEGY:
  1. Track opponent's crop/animal counts over time
  2. Predict when they'll harvest/sell (based on crop ages, animal placement)
  3. Front-run their sells (sell BEFORE they crash the price)
  4. Buy their crashes (when they dump, buy low from the market)
  5. Time our sells for peak prices (when town demand is highest)
"""

import math
import copy


# ============================================================================
# PRICE MODEL — exact competition math
# ============================================================================

MARKET_PARAMS = {
    "WHEAT":      (25,  10000, 400, "sqrt",  0.80, "log",    0.20),
    "CARROT":     (35,  10000, 450, "hinge", 1.00, "sqrt",   0.70),
    "TOMATO":     (60,  10000, 200, "hinge", 0.40, "sqrt",   0.60),
    "STRAWBERRY": (120, 10000, 100, "sqrt",  0.70, "linear", 1.60),
    "MELON":      (250, 10000, 300, "log",   0.20, "sq",     3.60),
    "EGG":        (50,  10000, 332, "hinge", 0.40, "log",    0.20),
    "MILK":       (160, 10000, 122, "sqrt",  0.60, "linear", 1.60),
    "WOOL":       (200, 10000, 105, "log",   0.20, "sq",     3.20),
    "FERTILIZER": (100, 10000, 200, "linear",0.40, "linear", 0.40),
}

def _shape(name, x):
    if name == "linear": return x
    if name == "sqrt": return math.sqrt(x)
    if name == "sq": return x * x
    if name == "log": return math.log(1 + x)
    return x

def price_at(resource, inventory):
    """Compute exact sell price for given inventory level."""
    if resource not in MARKET_PARAMS:
        return 1
    base, I0, T, b_func, b_tgt, a_func, a_tgt = MARKET_PARAMS[resource]
    diff = abs(inventory - I0)
    if diff < 0.5:
        return base
    if inventory < I0:
        func, target = b_func, b_tgt
    else:
        func, target = a_func, a_tgt
    if func == "hinge":
        u = diff / T
        f_val = u + 8 * max(0, u - 1) ** 2
        f_T = 1.0
    else:
        f_val = _shape(func, diff)
        f_T = _shape(func, T)
    amp = target * base / f_T if f_T > 0.001 else 0
    sign = 1 if inventory < I0 else -1
    return max(1, round(base + sign * amp * f_val))

def price_impact(resource, current_inv, units):
    """Predict total revenue from selling N units (one at a time)."""
    total = 0
    inv = current_inv
    for _ in range(units):
        total += price_at(resource, inv)
        inv += 1  # selling adds to market
    return total

def buy_cost(resource, current_inv, units):
    """Predict total cost of buying N units."""
    total = 0
    inv = current_inv
    for _ in range(units):
        inv -= 1  # buying removes from market
        total += price_at(resource, inv)
    return total


# ============================================================================
# OPPONENT TRACKER — watches opponent's farm state over time
# ============================================================================

class OpponentTracker:
    """Track opponent's observable state and predict their moves."""
    
    def __init__(self):
        self.history = []  # list of snapshots
        self.predictions = {}
    
    def observe(self, obs, player):
        """Record opponent's current state."""
        opp = obs["farms"][1 - player]
        day = int(obs.get("day", 0) or 0)
        step = int(obs.get("step", 0) or 0)
        
        # Count crops and animals
        tiles = opp.get("tiles", [])
        board = len(tiles) if tiles else 10
        crops = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0}
        crop_ages = {"WHEAT": [], "CARROT": [], "TOMATO": [], "STRAWBERRY": [], "MELON": []}
        animals = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
        ripe_crops = 0  # crops ready to harvest
        unfed_animals = 0
        
        for y in range(board):
            for x in range(board):
                t = tiles[y][x] if y < len(tiles) and x < len(tiles[y]) else None
                if not isinstance(t, dict):
                    continue
                kind = t.get("kind")
                if kind == "PLANT":
                    crop = t.get("crop", "WHEAT")
                    crops[crop] = crops.get(crop, 0) + 1
                    age = day - t.get("planted_day", day)
                    crop_ages[crop].append(age)
                    if t.get("yield_units", 0) > 0:
                        ripe_crops += 1
                elif kind in ("COOP", "PASTURE"):
                    animal = t.get("animal")
                    if animal:
                        animals[animal] = animals.get(animal, 0) + 1
                        if not t.get("fed_today") and t.get("consecutive_unfed", 0) >= 1:
                            unfed_animals += 1
        
        money = float(opp.get("money", 0))
        quads = opp.get("unlocked_quadrants", [])
        n_hands = len(opp.get("hands", []))
        
        snapshot = {
            "step": step,
            "day": day,
            "crops": dict(crops),
            "crop_ages": dict(crop_ages),
            "animals": dict(animals),
            "ripe_crops": ripe_crops,
            "unfed_animals": unfed_animals,
            "money": money,
            "quads": list(quads),
            "n_hands": n_hands,
        }
        
        self.history.append(snapshot)
        return snapshot
    
    def predict_harvest_wave(self, resource):
        """Predict when opponent will harvest a crop (sell incoming)."""
        if len(self.history) < 2:
            return None
        
        latest = self.history[-1]
        ages = latest["crop_ages"].get(resource, [])
        if not ages:
            return None
        
        # One-time crops: harvest at max_yield_day
        # Wheat: max_yield_day=4, harvestable at age 2+
        # Melon: max_yield_day=10, harvestable at age 10
        # Carrot: max_yield_day=3, harvestable at age 2+
        # Ongoing: harvest periodically
        
        min_age = min(ages) if ages else 999
        max_age = max(ages) if ages else 0
        count = len(ages)
        
        if resource == "WHEAT":
            # Wheat ready at age 2 (first yield), peak at 4
            if min_age >= 2:
                return "IMMINENT"  # harvest any turn now
            elif min_age >= 1:
                return "TOMORROW"  # 1 day away
        elif resource == "MELON":
            if min_age >= 10:
                return "IMMINENT"
            elif min_age >= 8:
                return "SOON"  # 2 days away
        elif resource == "STRAWBERRY":
            # Ongoing: produces at ages 10, 12, 14, 16
            if min_age >= 10:
                return "IMMINENT"
        
        return "NOT_YET"
    
    def predict_sell_pressure(self, resource):
        """Predict how much the opponent will sell (and when)."""
        if len(self.history) < 2:
            return 0
        
        latest = self.history[-1]
        ripe = latest["ripe_crops"]
        crop_count = latest["crops"].get(resource, 0)
        
        if crop_count == 0:
            return 0
        
        harvest = self.predict_harvest_wave(resource)
        if harvest == "IMMINENT":
            return crop_count * 3  # ~3 units per crop at peak
        elif harvest == "TOMORROW":
            return crop_count * 2
        elif harvest == "SOON":
            return crop_count
        
        return 0
    
    def classify_strategy(self):
        """Classify opponent's strategy based on observed behavior."""
        if len(self.history) < 3:
            return "unknown"
        
        latest = self.history[-1]
        crops = latest["crops"]
        animals = latest["animals"]
        quads = latest["quads"]
        
        total_crops = sum(crops.values())
        total_animals = sum(animals.values())
        
        # Wheat-arb: heavy wheat + lots of animals (Kawashigi)
        if crops.get("WHEAT", 0) >= 20 and total_animals >= 8:
            return "wheat_arb"
        
        # Strawberry flood
        if crops.get("STRAWBERRY", 0) >= 20:
            return "straw_flood"
        
        # Melon-heavy (Build-A style)
        if crops.get("MELON", 0) >= 10 and animals.get("COW", 0) >= 4:
            return "buildA"
        
        # 4-quad (Seb style)
        if len(quads) >= 3 and len(self.history) > 0:
            early_quads = self.history[min(5, len(self.history)-1)]
            if len(early_quads.get("quads", [])) >= 2:
                return "seb"
        
        # Animal-heavy
        if total_animals >= 14:
            return "animal_heavy"
        
        # Default
        return "balanced"


# ============================================================================
# MARKET STRATEGIST — decides what to buy/sell and when
# ============================================================================

class MarketStrategist:
    """Makes real-time market decisions based on opponent tracking + price model."""
    
    def __init__(self):
        self.tracker = OpponentTracker()
        self.portfolio = {"bought": {}, "sold": {}}  # track our trades
        self.price_history = {}  # resource -> list of (step, price)
    
    def observe(self, obs, player):
        """Update all tracking."""
        snap = self.tracker.observe(obs, player)
        
        # Track prices
        market = obs.get("market", {})
        prices = market.get("prices", {})
        step = int(obs.get("step", 0) or 0)
        for resource, price in prices.items():
            if resource not in self.price_history:
                self.price_history[resource] = []
            self.price_history[resource].append((step, price))
        
        return snap
    
    def decide_market_orders(self, obs, player, tape_market_orders, memory=None):
        """Generate market orders using live market intelligence.
        
        CONSERVATIVE APPROACH:
        - NEVER remove the tape's planned orders (they're proven optimal)
        - Only BOOST existing sell quantities when we know it's safe
        - Only ADD new orders when there's CLEAR room and opportunity
        - Opponent-specific counters only when classification is CONFIRMED
        """
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        market = obs.get("market", {})
        inv = market.get("inventory", {})
        prices = market.get("prices", {})
        private = obs.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})
        farm = obs["farms"][player]
        money = float(farm.get("money", 0))
        
        # CRITICAL: Start with tape's EXACT orders — never remove them
        orders = [list(o) for o in (tape_market_orders or [])]
        
        # Get opponent classification (passed in from agent)
        memory = memory or {}
        opp_strategy = self.tracker.classify_strategy()
        
        # === BOOST 1: Sell more fertilizer when we have it ===
        fert_in_shed = int(shed.get("FERTILIZER", 0) or 0)
        if fert_in_shed > 3 and day >= 2:
            for i, o in enumerate(orders):
                if o and o[0] == "SELL" and len(o) > 1 and o[1] == "FERTILIZER":
                    old_qty = int(o[2]) if len(o) > 2 else 1
                    if fert_in_shed > old_qty:
                        orders[i] = ["SELL", "FERTILIZER", fert_in_shed]
                    break
        
        # === BOOST 2: Terminal sell boost (d27+) ===
        if day >= 27:
            for item in ["STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "CARROT", "TOMATO"]:
                qty = int(shed.get(item, 0) or 0)
                if qty <= 0:
                    continue
                for i, o in enumerate(orders):
                    if o and o[0] == "SELL" and len(o) > 1 and o[1] == item:
                        old_qty = int(o[2]) if len(o) > 2 else 1
                        if qty > old_qty:
                            orders[i] = ["SELL", item, qty]
                        break
        
        # === OPPONENT-SPECIFIC COUNTERS (only when classification locked) ===
        if memory.get("locked") and day >= 8:
            mode = memory.get("mode", "default")
            
            if mode == "anti_wheat_arb" and shed.get("WHEAT", 0) > 10:
                wheat_price = prices.get("WHEAT", 25)
                if wheat_price >= 30:
                    for i, o in enumerate(orders):
                        if o and o[0] == "SELL" and len(o) > 1 and o[1] == "WHEAT":
                            old_qty = int(o[2]) if len(o) > 2 else 1
                            orders[i] = ["SELL", "WHEAT", min(int(shed.get("WHEAT", 0)), old_qty + 8)]
                            break
        
        return orders[:10]
