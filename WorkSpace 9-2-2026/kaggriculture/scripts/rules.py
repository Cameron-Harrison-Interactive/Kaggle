"""
rules.py — the exact Kaggriculture rules, as one importable module the bot can
PLAN with (the "extra income days" on crops, fertilizer timing, etc.).

Every table here is transcribed from the official engine
(kaggle_environments/envs/kaggriculture/kaggriculture.py) and cross-checked
against it (sim.verify_sim re-plays real games through the engine itself).

The "extra income days" mechanics, precisely:

* ONE-TIME crops (wheat/carrot/melon) have a watering BONUS WINDOW:
    window_start = ceil(max_yield_day / 2) .. max_yield_day.
  Each day you water INSIDE the window adds +1 yield unit (+2 if fertilized).
  Watering before the window only keeps the plant alive; watering inside the
  window is where the yield actually comes from. The plant is born with
  yield_units=1.

* FERTILIZER doubles the bonus for 3 days (the day you fertilize, +1, +2):
  - wheat  : 4 -> 6 units (net vs selling the fertilizer: roughly break-even)
  - carrot : 3 -> 4 units
  - melon  : hits its 6-unit cap at age 8 instead of 10 -> harvest 2 DAYS
             EARLIER, same units. That's free extra income via faster cycles.
  - strawberry : doubles each scheduled production (4 x 1 -> 4 x 2 = 8 units).
             Net +~$380/tile after the fertilizer's sell value.
  - tomato : doubles each scheduled production (4 x 1 -> 8), but tomato price
             gluts, so it's marginal.

* ONGOING crops (tomato/strawberry) produce on a fixed schedule: first yield
  at first_yield_day, then every `interval` days, up to max_yield productions.
  Fertilized AND watered on a production day doubles that production.

* ANIMALS: feed daily with wheat; CARE banks a bonus paid on the next
  production; product accumulates up to max_held; 1 fertilizer/animal/day.
"""

import math

# ---- crop / animal / market tables (verbatim from the engine) --------------
CROPS = {
    "WHEAT":      {"seed": 10,  "first": 2,  "max_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first": 2,  "max_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first": 8,  "max_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "max_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first": 10, "max_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "struct": "COOP",    "first": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "struct": "PASTURE", "first": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "struct": "PASTURE", "first": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER"]

MARKET_I0 = 10000
PRICE_FLOOR = 1

MARKET = {
    "WHEAT":      {"base": 25,  "T": 400, "below": "sqrt",   "bt": 0.80, "above": "log",   "at": 0.20},
    "CARROT":     {"base": 35,  "T": 450, "below": "log",    "bt": 0.20, "above": "sqrt",  "at": 0.70},
    "TOMATO":     {"base": 60,  "T": 200, "below": "linear", "bt": 0.40, "above": "sqrt",  "at": 0.60},
    "STRAWBERRY": {"base": 120, "T": 100, "below": "sqrt",   "bt": 0.70, "above": "linear","at": 1.60},
    "MELON":      {"base": 250, "T": 300, "below": "log",    "bt": 0.20, "above": "sq",    "at": 3.60},
    "EGG":        {"base": 50,  "T": 332, "below": "linear", "bt": 0.40, "above": "log",   "at": 0.20},
    "MILK":       {"base": 160, "T": 122, "below": "sqrt",   "bt": 0.60, "above": "linear","at": 1.60},
    "WOOL":       {"base": 200, "T": 105, "below": "log",    "bt": 0.20, "above": "sq",    "at": 3.20},
    "FERTILIZER": {"base": 100, "T": 200, "below": "linear", "bt": 0.40, "above": "linear","at": 0.40},
}

# ---- exact price function --------------------------------------------------
def _shape(name, x):
    x = max(0.0, x)
    if name == "linear": return x
    if name == "sq":     return x * x
    if name == "sqrt":   return math.sqrt(x)
    if name == "log":    return math.log(1.0 + x)
    if name == "log10":  return math.log10(1.0 + x)
    return x


def price(item, inventory, params=None):
    """Exact sell price at a given market inventory (matches the engine)."""
    p = (params or MARKET)[item]
    base, T = p["base"], p["T"]
    if inventory < MARKET_I0:
        f, target = p["below"], p["bt"]
        amp = target * base / _shape(f, T)
        price = base + amp * _shape(f, MARKET_I0 - inventory)
    else:
        f, target = p["above"], p["at"]
        amp = target * base / _shape(f, T)
        price = base - amp * _shape(f, inventory - MARKET_I0)
    return max(PRICE_FLOOR, int(round(price)))


# ---- crop scheduling (the "extra income days") -----------------------------
def bonus_window(crop):
    """(start_age, end_age) inclusive watering-bonus window for a one-time
    crop, or None for ongoing crops."""
    cd = CROPS[crop]
    if cd["ongoing"]:
        return None
    start = (cd["max_day"] + 1) // 2
    return start, cd["max_day"]


def plan_crop(crop, plant_day, fertilize_days=()):
    """Full dated schedule for ONE tile of `crop` planted on `plant_day`.

    Returns dict:
        water_days     : days the tile must be watered (inclusive)
        harvest_day    : earliest day we can harvest at (near-)max yield
        yield_units    : units harvested on that day
        ongoing_days   : for ongoing crops, the days each production lands
        fertilize_days : recommended fertilizer days (what you passed in)
    """
    cd = CROPS[crop]
    if not cd["ongoing"]:
        ws, we = bonus_window(crop)
        water_days = list(range(plant_day, plant_day + cd["max_day"] + 1))
        # FERTILIZE on day F doubles the bonus for F, F+1, F+2.
        doubled = set()
        for f in fertilize_days:
            doubled |= {f, f + 1, f + 2}
        yield_u = 1
        harvest_day = None
        for age in range(0, cd["max_day"] + 1):
            day = plant_day + age
            if ws <= age <= we:
                yield_u += 2 if day in doubled else 1
            if harvest_day is None and age >= cd["first"] and yield_u >= cd["max_yield"]:
                harvest_day = day
        if harvest_day is None:
            harvest_day = plant_day + cd["max_day"]
        return {
            "water_days": water_days,
            "harvest_day": harvest_day,
            "yield_units": min(cd["max_yield"], yield_u),
            "ongoing_days": [],
        }
    # ongoing: scheduled productions
    prod_days = [plant_day + cd["first"] + k * cd["interval"]
                 for k in range(cd["max_yield"])]
    return {
        "water_days": list(range(plant_day, plant_day + cd["first"] + (cd["max_yield"] - 1) * cd["interval"] + 1)),
        "harvest_day": None,          # harvests repeat on prod_days
        "yield_units": cd["max_yield"] * (2 if all(d in fertilize_days for d in prod_days) else 1),
        "ongoing_days": prod_days,
    }


def harvest_value(crop, units, inventory=10000):
    """Dollar value of `units` of a crop sold one at a time into `inventory`."""
    total = 0
    inv = inventory
    for _ in range(units):
        total += price(crop, inv)
        inv += 1
    return total


def fertilizer_net(crop, plant_day, inventory=10000):
    """Net value of fertilizing one tile of `crop` optimally, after deducting
    the fertilizer's own sell value (i.e. its opportunity cost)."""
    cd = CROPS[crop]
    if crop not in CROPS or cd["ongoing"] is False and crop not in ("WHEAT", "MELON"):
        pass
    fert_sell = price("FERTILIZER", inventory)

    if crop == "WHEAT":
        # one fertilizer on day window-start: 4 -> 6 units
        gain = harvest_value("WHEAT", 2, inventory)
        return gain - fert_sell
    if crop == "MELON":
        # No gain: harvest is blocked before first_yield_day=10, and daily
        # watering already hits the 6-unit cap by age 10. Fertilizer is
        # better sold than spent here.
        return -fert_sell
    if crop == "STRAWBERRY":
        # two fertilizers double all 4 productions: +4 units
        gain = harvest_value("STRAWBERRY", 4, inventory)
        return gain - 2 * fert_sell
    if crop == "TOMATO":
        gain = harvest_value("TOMATO", 4, inventory)
        return gain - 2 * fert_sell
    return 0


if __name__ == "__main__":
    print("Price sanity (should match the engine README table):")
    for item in PRODUCTS:
        print(f"  {item:<12} base={price(item, 10000):>4}  -T={price(item, 10000-MARKET[item]['T']):>4}  +T={price(item, 10000+MARKET[item]['T']):>4}")

    print("\nCrop schedules (planted day 0):")
    for crop in ("WHEAT", "MELON", "STRAWBERRY", "TOMATO", "CARROT"):
        s = plan_crop(crop, 0)
        bw = bonus_window(crop)
        print(f"  {crop:<12} window={bw}  water={s['water_days'][0]}..{s['water_days'][-1]}  "
              f"harvest={s['harvest_day']}  units={s['yield_units']}  prod_days={s['ongoing_days']}")

    print("\nFertilizer net value (base prices):")
    for crop in ("WHEAT", "STRAWBERRY", "TOMATO", "MELON"):
        print(f"  {crop:<12} net ${fertilizer_net(crop, 0):+.0f}")

    print("\nKey 'extra income' facts:")
    print("  * melon fertilizer = $0 gain (harvest locked to age 10, cap already hit)")
    print("  * strawberry fertilizer = the big one (+4 units, ~+$268/tile)")
    print("  * wheat fertilizer = loss (sell the fertilizer instead)")
    print("  * strawberry production days (planted d0):", plan_crop("STRAWBERRY", 0)["ongoing_days"])
