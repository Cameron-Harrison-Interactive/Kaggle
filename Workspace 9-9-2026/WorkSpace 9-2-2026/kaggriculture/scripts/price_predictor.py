"""Price Elasticity Predictor — models the market's price function.

Uses the known competition math to predict price impact of buys/sells.
This is the core of the adaptive system — knowing WHEN to sell/buy.
"""
import math

# Market params from the competition rules
RESOURCES = {
    "WHEAT":       {"base": 25,  "I0": 10000, "T": 400,  "below_func": "sqrt",  "below_target": 0.80, "above_func": "log",   "above_target": 0.20},
    "CARROT":      {"base": 35,  "I0": 10000, "T": 450,  "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt",  "above_target": 0.70},
    "TOMATO":      {"base": 60,  "I0": 10000, "T": 200,  "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt",  "above_target": 0.60},
    "STRAWBERRY":  {"base": 120, "I0": 10000, "T": 100,  "below_func": "sqrt",  "below_target": 0.70, "above_func": "linear","above_target": 1.60},
    "MELON":       {"base": 250, "I0": 10000, "T": 300,  "below_func": "log",   "below_target": 0.20, "above_func": "sq",    "above_target": 3.60},
    "EGG":         {"base": 50,  "I0": 10000, "T": 332,  "below_func": "hinge", "below_target": 0.40, "above_func": "log",   "above_target": 0.20},
    "MILK":        {"base": 160, "I0": 10000, "T": 122,  "below_func": "sqrt",  "below_target": 0.60, "above_func": "linear","above_target": 1.60},
    "WOOL":        {"base": 200, "I0": 10000, "T": 105,  "below_func": "log",   "below_target": 0.20, "above_func": "sq",    "above_target": 3.20},
    "FERTILIZER":  {"base": 100, "I0": 10000, "T": 200,  "below_func": "linear","below_target": 0.40, "above_func": "linear","above_target": 0.40},
}


def _shape_func(name, x):
    """Evaluate shape function f(x)."""
    if name == "linear":
        return x
    elif name == "sqrt":
        return math.sqrt(x)
    elif name == "sq":
        return x * x
    elif name == "log":
        return math.log(1 + x)
    elif name == "log10":
        return math.log10(1 + x)
    elif name == "hinge":
        # hinge depends on T - handled separately
        return x
    return x


def compute_price(resource, inventory):
    """Compute the sell price for a resource at given inventory level."""
    if resource not in RESOURCES:
        return 1
    p = RESOURCES[resource]
    base = p["base"]
    I0 = p["I0"]
    T = p["T"]
    
    diff = abs(inventory - I0)
    if diff < 0.001:
        return base
    
    if inventory < I0:
        # Scarcity -> price up
        func_name = p["below_func"]
        target = p["below_target"]
    else:
        # Glut -> price down
        func_name = p["above_func"]
        target = p["above_target"]
    
    if func_name == "hinge":
        u = diff / T
        f_val = u + 8 * max(0, u - 1) ** 2
        f_T = 1.0  # by construction
    else:
        f_val = _shape_func(func_name, diff)
        f_T = _shape_func(func_name, T)
    
    amp = target * base / f_T if f_T > 0 else 0
    sign = 1 if inventory < I0 else -1
    price = base + sign * amp * f_val
    
    return max(1, round(price))


def predict_sell_price(resource, current_inventory, units_to_sell):
    """Predict the average price received when selling N units.
    
    Units are sold one at a time, each adding 1 to inventory.
    Returns (avg_price, total_revenue, price_impact).
    """
    if units_to_sell <= 0:
        return 0, 0, 0
    
    prices = []
    inv = current_inventory
    for _ in range(units_to_sell):
        p = compute_price(resource, inv)
        prices.append(p)
        inv += 1  # selling adds to market inventory
    
    total = sum(prices)
    avg = total / len(prices)
    start_price = compute_price(resource, current_inventory)
    end_price = compute_price(resource, current_inventory + units_to_sell)
    impact = end_price - start_price
    
    return avg, total, impact


def predict_buy_price(resource, current_inventory, units_to_buy):
    """Predict the average cost when buying N units.
    
    Units are bought one at a time, each removing 1 from inventory.
    Note: buy price uses post-buy inventory.
    Returns (avg_cost, total_cost, price_impact).
    """
    if units_to_buy <= 0:
        return 0, 0, 0
    
    costs = []
    inv = current_inventory
    for _ in range(units_to_buy):
        inv -= 1  # buying removes from market
        p = compute_price(resource, inv)
        costs.append(p)
    
    total = sum(costs)
    avg = total / len(costs)
    start_price = compute_price(resource, current_inventory)
    end_price = compute_price(resource, current_inventory - units_to_buy)
    impact = end_price - start_price
    
    return avg, total, impact


def optimal_sell_timing(resource, current_inventory, units_available, 
                        daily_production=0, days_remaining=30, current_day=0):
    """Recommend when to sell for maximum revenue.
    
    Models: daily production adds to inventory, town consumption removes.
    Returns recommended sell schedule.
    """
    p = RESOURCES.get(resource, {})
    base = p.get("base", 25)
    current_price = compute_price(resource, current_inventory)
    
    # Price is above base? Sell now.
    if current_price > base * 1.2:
        return "SELL_NOW", f"Price ${current_price} is 20%+ above base ${base}"
    
    # Price is below base? Hold if we have time.
    if current_price < base * 0.8 and days_remaining - current_day > 5:
        return "HOLD", f"Price ${current_price} is below 80% of base ${base}, wait for recovery"
    
    # Near floor? Desperate sell.
    if current_price <= 2:
        return "DESPERATE_SELL", f"Price at floor ${current_price}, sell everything"
    
    # Default: sell in batches
    return "BATCH_SELL", f"Price ${current_price} near base ${base}, sell in batches"


def market_state_summary(obs):
    """Analyze current market state for the voting system."""
    market = obs.get("market", {})
    inv = market.get("inventory", {})
    prices = market.get("prices", {})
    
    summary = {}
    for resource in RESOURCES:
        current_inv = inv.get(resource, 10000)
        current_price = prices.get(resource, RESOURCES[resource]["base"])
        base_price = RESOURCES[resource]["base"]
        
        price_ratio = current_price / base_price if base_price > 0 else 1
        inv_delta = current_inv - 10000  # deviation from I0
        
        # Sell urgency: high price = sell now, low price = hold
        if price_ratio > 1.3:
            urgency = "SELL_HIGH"
        elif price_ratio > 1.0:
            urgency = "SELL_NORMAL"
        elif price_ratio > 0.7:
            urgency = "HOLD"
        else:
            urgency = "SELL_FLOOR"
        
        summary[resource] = {
            "inventory": current_inv,
            "price": current_price,
            "base": base_price,
            "price_ratio": price_ratio,
            "inv_delta": inv_delta,
            "urgency": urgency,
        }
    
    return summary


if __name__ == "__main__":
    # Quick demo
    print("Price predictions:")
    for resource in ["WHEAT", "STRAWBERRY", "MILK", "WOOL"]:
        for inv in [9500, 9800, 10000, 10200, 10500]:
            p = compute_price(resource, inv)
            print(f"  {resource:12s} inv={inv:>6d} → price=${p:>4d}")
        print()
    
    print("Sell 20 wheat at inv=9800:")
    avg, total, impact = predict_sell_price("WHEAT", 9800, 20)
    print(f"  Avg: ${avg:.1f}, Total: ${total}, Impact: ${impact:+d}")
    
    print("\nSell 20 wheat at inv=10200:")
    avg, total, impact = predict_sell_price("WHEAT", 10200, 20)
    print(f"  Avg: ${avg:.1f}, Total: ${total}, Impact: ${impact:+d}")
