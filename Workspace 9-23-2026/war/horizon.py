#!/usr/bin/env python3
"""horizon.py — the LONG-HORIZON season model for Kaggriculture.

WHY THIS EXISTS
---------------
Every bot in `war/` decides one day at a time: today's board in, today's
argmax out. But the game is *deterministic* — plant a strawberry on day p and
the engine WILL produce on p+10, p+12, p+14, p+16, no matter what. A 30-day
season is a solvable planning problem and we were never solving it. This
module is the model that lets the agent value an action by what it will
actually produce, on the day it will actually produce it, at the price the
market will actually pay.

Everything here mirrors the engine's own semantics, transcribed from
`intel/engine_kagg_1327.py` on 2026-09-15 (not from memory, not from the
playbook's summary). Stdlib only. No engine import, no I/O, no RNG.

THE FIVE FACTS THE WHOLE MODEL RESTS ON (engine-verified)
--------------------------------------------------------
1. NON-ONGOING crops (wheat/carrot/melon) accrue yield ONLY from a WATER op,
   and only while `window_start <= age <= max_yield_day` where
   `window_start = (max_yield_day + 1) // 2`. Each watering is +1, or +2 if
   the tile is fertilized that day, capped at `max_yield`.
     wheat  max_yield_day  4 -> window ages 2..4  -> 3 waterings -> 3u (6u fert)
     carrot max_yield_day  3 -> window ages 2..3  -> 2 waterings -> 2u (4u fert)
     melon  max_yield_day 12 -> window ages 6..12 -> 6 waterings -> 6u (6u fert)
2. ONGOING crops (strawberry/tomato) produce at END OF DAY when
   `(next_day - planted_day - first_yield_day) >= 0` and `% interval == 0`,
   capped at `max_yield` productions. The unit is +2 if the tile was BOTH
   watered and fertilized that day, else +1 — and +1 even if never watered.
   After the last production the tile starts rotting (yield -1 per 2 hours).
     strawberry: first 10, interval 2, max 4 -> productions at +10/12/14/16.
3. ANIMALS produce `(next_day - placed_day - first_yield_day) % interval == 0`,
   yielding `1 + pending_care_bonus`, capped at max_held. The bonus is +1 for
   every day the animal was BOTH cared and fed, banked and then consumed whole
   on the next FED production day. So daily care is worth:
     goose (interval 1) 1 -> 2 units/production   (x2)
     cow   (interval 2) 1 -> 3 units/production   (x3)
     sheep (interval 3) 1 -> 4 units/production   (x4)
   Production happens even unfed; feeding buys survival (escape at
   consecutive_unfed >= 2) and unlocks the care bonus.
4. PRICE is a deterministic function of market inventory (I0 = 10000):
   scarcity above base below I0, glut below base above it, floored at $1.
   Every unit we SELL pushes price down; town consumption pulls it back.
5. LABOR is the real constraint: measured (war/walk_probe.py) at 45% of all
   worker-hours spent walking, 1.56 moves per productive op. A plan is only
   worth what the crew can actually execute.
"""

import math

TOTAL_DAYS = 30
TURNS_PER_DAY = 24
PRICE_FLOOR = 1
MARKET_I0 = 10000

# ---------------------------------------------------------------- tables
# Verbatim from intel/engine_kagg_1327.py.

CROPS = {
    "WHEAT":      {"seed": 10,  "first_yield_day": 2,  "max_yield_day": 4,
                   "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first_yield_day": 2,  "max_yield_day": 3,
                   "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first_yield_day": 8,  "max_yield_day": 8,
                   "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10,
                   "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first_yield_day": 10, "max_yield_day": 12,
                   "interval": 0, "max_yield": 6, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4,
              "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8,
              "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6,
              "interval": 3, "max_held": 6, "product": "WOOL"},
}

MARKET_PARAMS = {
    "WHEAT":      {"base": 25,  "I0": MARKET_I0, "T": 400, "below_func": "sqrt",
                   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base": 35,  "I0": MARKET_I0, "T": 450, "below_func": "hinge",
                   "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base": 60,  "I0": MARKET_I0, "T": 200, "below_func": "hinge",
                   "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": MARKET_I0, "T": 100, "below_func": "sqrt",
                   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": MARKET_I0, "T": 300, "below_func": "log",
                   "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base": 50,  "I0": MARKET_I0, "T": 332, "below_func": "hinge",
                   "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": MARKET_I0, "T": 122, "below_func": "sqrt",
                   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": MARKET_I0, "T": 105, "below_func": "log",
                   "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": MARKET_I0, "T": 200, "below_func": "linear",
                   "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

HINGE_GAIN = 1.0   # engine: HINGE_GAIN; f(T) == 1 by construction

LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = [1000, 2000, 4000]
FIB = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987)

# Measured labour constants (war/walk_probe.py, v29 seed 42).
MOVES_PER_OP = 1.56          # walking tax
HOURS_PER_OP = 1.0 + MOVES_PER_OP
OPS_PER_WORKER_DAY = TURNS_PER_DAY / HOURS_PER_OP   # ~9.2 real ops/worker/day


# ---------------------------------------------------------------- pricing
def shape(func, x, T=None):
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "log10":
        return math.log10(1.0 + x)
    if func == "hinge":
        if not T or T <= 0:
            return x
        u = x / T
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x


def market_price(item, inventory):
    """Exact engine price for `item` at market inventory `inventory`."""
    p = MARKET_PARAMS[item]
    base, I0, T = p["base"], p["I0"], p["T"]
    if inventory < I0:
        amp = p["below_target"] * base / shape(p["below_func"], T, T)
        price = base + amp * shape(p["below_func"], I0 - inventory, T)
    else:
        amp = p["above_target"] * base / shape(p["above_func"], T, T)
        price = base - amp * shape(p["above_func"], inventory - I0, T)
    return max(PRICE_FLOOR, int(round(price)))


def sale_revenue(item, inventory, qty):
    """Revenue for selling `qty` units one at a time into `inventory`.

    The engine executes a SELL order unit by unit and each unit raises
    inventory (and so lowers the price) before the next one is priced. This
    is the whole reason 'sell pacing >= farm output' is doctrine.
    """
    inv, total = inventory, 0.0
    for _ in range(int(qty)):
        px = market_price(item, inv)
        total += px
        if px > PRICE_FLOOR:
            inv += 1
    return total


# ------------------------------------------------------------- calendars
def crop_water_window(crop):
    """(first_age, last_age) on which a WATER op still adds yield."""
    cd = CROPS[crop]
    if cd["ongoing"]:
        return None
    return ((cd["max_yield_day"] + 1) // 2, cd["max_yield_day"])


def crop_plan(crop, planted_day, fertilize=False, last_day=TOTAL_DAYS - 1):
    """Full deterministic schedule for one tile planted with `crop`.

    Two day-lists, and the difference between them is the single most
    expensive off-by-one in this game:

      tick_days    – the days the engine actually ADDS yield, at end of day.
                     A WATER (and FERTILIZE) must land on THIS day for the
                     +2 bonus on ongoing crops.
      harvest_days – the days the units can be picked up (= tick day + 1).

    Engine: `_new_plant` seeds non-ongoing crops with yield_units = 1 (base
    unit at plant time); everything after that comes from watering.
    """
    cd = CROPS[crop]
    first_pick = planted_day + cd["first_yield_day"]

    if not cd["ongoing"]:
        ws, we = crop_water_window(crop)
        water_days = [planted_day + a for a in range(ws, we + 1)]
        water_days = [d for d in water_days if d <= last_day]
        per = 2 if fertilize else 1
        # base unit at planting + `per` per watering in the window
        units = min(cd["max_yield"], 1 + len(water_days) * per)
        if first_pick > last_day:
            units = 0
        harvest_day = min(max(first_pick, planted_day + cd["max_yield_day"]),
                          last_day)
        rot_day = planted_day + cd["max_yield_day"] + 1
        ops = 1 + len(water_days) + (1 if units else 0)
        if fertilize:
            ops += 1
        return {"crop": crop, "planted": planted_day, "ongoing": False,
                "water_days": water_days, "tick_days": water_days,
                "prod_days": [harvest_day] if units else [],
                "harvest_days": [harvest_day] if units else [],
                "units": units, "harvest_day": harvest_day,
                "rot_day": rot_day, "ops": ops}

    # ongoing: yield lands at END of day `current_day` when
    # (current_day + 1 - planted - first_yield_day) % interval == 0
    tick_days, k = [], 0
    while True:
        d = planted_day + cd["first_yield_day"] - 1 + k * cd["interval"]
        if d > last_day or k >= cd["max_yield"]:
            break
        tick_days.append(d)
        k += 1
    if not tick_days:
        return {"crop": crop, "planted": planted_day, "ongoing": True,
                "water_days": [], "tick_days": [], "prod_days": [],
                "harvest_days": [], "units": 0, "harvest_day": planted_day,
                "rot_day": planted_day, "ops": 1}
    harvest_days = [d + 1 for d in tick_days if d + 1 <= last_day]
    # +1 unwatered, +2 watered AND fertilized, capped at max_yield productions
    per = 2 if fertilize else 1
    units = min(cd["max_yield"] * per, len(tick_days) * per)
    if not harvest_days:
        units = 0
    ops = 1 + len(tick_days) + (1 if fertilize else 0) + max(1, len(harvest_days))
    return {"crop": crop, "planted": planted_day, "ongoing": True,
            "water_days": tick_days, "tick_days": tick_days,
            "prod_days": harvest_days, "harvest_days": harvest_days,
            "units": units, "harvest_day": min(tick_days[-1] + 1, last_day),
            "rot_day": tick_days[-1] + 2, "ops": ops}


def animal_productions(kind, placed_day, last_day=TOTAL_DAYS - 1):
    """Days the product can be HARVESTED.

    The engine adds yield at end of day `placed + first - 1 + k*interval`, so
    the unit is collectable the following morning (placed + first + k*interval).
    """
    a = ANIMALS[kind]
    out = []
    k = 0
    while True:
        d = placed_day + a["first_yield_day"] + k * a["interval"]
        if d > last_day:
            break
        out.append(d)
        k += 1
    return out


def animal_tick_days(kind, placed_day, last_day=TOTAL_DAYS - 1):
    """End-of-day on which the animal's yield_units actually increase."""
    a = ANIMALS[kind]
    out = []
    k = 0
    while True:
        d = placed_day + a["first_yield_day"] - 1 + k * a["interval"]
        if d > last_day:
            break
        out.append(d)
        k += 1
    return out


def animal_units(kind, placed_day, care=True, last_day=TOTAL_DAYS - 1):
    """Total product units over the animal's remaining life.

    With daily care the bonus is +1 per cared+fed day, consumed whole at the
    next fed production: cow 1->3, sheep 1->4, goose 1->2 per production.
    Capped by max_held (product left sitting on the tile is lost production).
    """
    a = ANIMALS[kind]
    prods = animal_productions(kind, placed_day, last_day)
    if not prods:
        return 0
    interval = a["interval"]
    cap = a["max_held"]
    if care:
        per = min(cap, 1 + interval)      # banked `interval` cared days
    else:
        per = 1
    # the first production has had no time to bank a bonus
    units = 1 if prods else 0
    for _ in prods[1:]:
        units += per
    return units


def animal_ops(kind, placed_day, care=True, last_day=TOTAL_DAYS - 1):
    """Labour ops the animal demands over its remaining life."""
    days = max(0, last_day - placed_day + 1)
    n_prod = len(animal_productions(kind, placed_day, last_day))
    ops = days                      # feed (or survival-feed every other day)
    if care:
        ops += days                 # care
    ops += days                     # collect fertilizer (1/day, always available)
    ops += n_prod                   # harvest the product
    ops += 2                        # pickup + build + place
    return ops


# ------------------------------------------------------------- valuation
def npv_crop(crop, planted_day, price_of, fertilize=False,
             last_day=TOTAL_DAYS - 1, fert_cost=0.0):
    """Expected revenue (net of seed + fertilizer) for one tile."""
    pl = crop_plan(crop, planted_day, fertilize, last_day)
    if not pl["prod_days"] or pl["units"] <= 0:
        return {"gross": 0.0, "net": -CROPS[crop]["seed"], "units": 0,
                "ops": 0, "per_op": 0.0, "plan": pl}
    # revenue lands on the harvest day (non-ongoing) or spread over production
    if pl["ongoing"]:
        per = max(1.0, pl["units"] / max(1, len(pl["prod_days"])))
        gross = sum(price_of(crop, d) * per for d in pl["prod_days"])
    else:
        gross = price_of(crop, pl["harvest_day"]) * pl["units"]
    net = gross - CROPS[crop]["seed"] - (fert_cost if fertilize else 0.0)
    return {"gross": gross, "net": net, "units": pl["units"],
            "ops": pl["ops"], "per_op": net / max(1.0, pl["ops"]),
            "plan": pl}


def npv_animal(kind, placed_day, price_of, care=True, feed_price=25.0,
               last_day=TOTAL_DAYS - 1):
    """Expected revenue net of purchase + feed for one animal."""
    a = ANIMALS[kind]
    prods = animal_productions(kind, placed_day, last_day)
    if not prods:
        return {"gross": 0.0, "net": -a["cost"], "units": 0, "per_op": 0.0}
    units = animal_units(kind, placed_day, care, last_day)
    per = units / max(1, len(prods))
    gross = sum(price_of(a["product"], d) * per for d in prods)
    days = last_day - placed_day + 1
    feed = feed_price * days
    net = gross - a["cost"] - feed
    return {"gross": gross, "net": net, "units": units,
            "ops": animal_ops(kind, placed_day, care, last_day),
            "per_op": net / max(1.0, animal_ops(kind, placed_day, care,
                                                last_day))}


def crew_wage(n_hands):
    """Daily wage for `n_hands` (FIB-priced, n-th hire costs fib(n))."""
    return sum(FIB[i] for i in range(min(n_hands, len(FIB))))


def labor_capacity(n_workers):
    """Productive ops the crew can execute in one day (walking included)."""
    return n_workers * OPS_PER_WORKER_DAY


# ------------------------------------------------------------ self-test
if __name__ == "__main__":
    print("=" * 66)
    print("horizon.py — long-horizon season model (engine-verified 09-15)")
    print("=" * 66)

    print("\n1. CROP CALENDARS (planted day 0, unfertilized)")
    print("   %-11s %-26s %5s %5s  %s" % ("crop", "water window (ages)",
                                          "units", "ops", "production days"))
    for c in ("WHEAT", "CARROT", "MELON", "STRAWBERRY", "TOMATO"):
        pl = crop_plan(c, 0)
        w = crop_water_window(c)
        wstr = "ages %d-%d" % w if w else "production days"
        print("   %-11s %-26s %5d %5d  %s" % (
            c, wstr, pl["units"], pl["ops"], pl["prod_days"]))

    print("\n2. STRAWBERRY TICK SCHEDULE (the factory)")
    for p in (0, 2, 8, 13):
        pl = crop_plan("STRAWBERRY", p)
        uf = pl["units"]
        plf = crop_plan("STRAWBERRY", p, fertilize=True)
        print("   planted d%-2d -> ticks %s  units %d (watered) / %d (watered+fert)"
              % (p, pl["prod_days"], uf, plf["units"]))

    print("\n3. ANIMAL CARE PRIZE (units per production, capped by max_held)")
    for k in ("GOOSE", "COW", "SHEEP"):
        a = ANIMALS[k]
        u0 = animal_units(k, 0, care=False)
        u1 = animal_units(k, 0, care=True)
        print("   %-6s interval %d  no-care %2d u  daily-care %2d u   = x%.1f"
              % (k, a["interval"], u0, u1, (u1 / max(1, u0))))

    print("\n4. PRICE CLIFFS (revenue for dumping N units at once, I0=10000)")
    print("   %-11s %8s %8s %8s %8s" % ("item", "10u", "25u", "50u", "100u"))
    for it in ("WHEAT", "STRAWBERRY", "MELON", "MILK", "WOOL", "FERTILIZER"):
        row = [sale_revenue(it, MARKET_I0, n) for n in (10, 25, 50, 100)]
        print("   %-11s %8.0f %8.0f %8.0f %8.0f" % (it, *row))

    print("\n5. LABOUR BUDGET")
    print("   measured: 1.56 moves per productive op -> %.1f real ops/worker/day"
          % OPS_PER_WORKER_DAY)
    for n in (8, 10, 12, 14):
        print("   crew %2d -> %5.1f ops/day, wage $%d/day"
              % (n, labor_capacity(n), crew_wage(n - 1)))

    print("\n6. WHY THE LAST PLANT DATES ARE WHAT THEY ARE")
    for c in ("MELON", "STRAWBERRY", "WHEAT"):
        best = None
        for d in range(TOTAL_DAYS):
            pl = crop_plan(c, d)
            if pl["units"] > 0:
                best = d
        print("   last plantable %s: d%d (units would be %d)"
              % (c, best, crop_plan(c, best)["units"]))


# ---------------------------------------------------------- season plan
def price_flat(item, day, inventory=MARKET_I0):
    """Baseline price path: today's quoted price held flat.

    Replace with a projected path (own supply + town drain + opponent) once
    the market model is wired in. Deliberately the simplest thing that can
    drive the planner so the calendar logic is testable in isolation.
    """
    return market_price(item, inventory)


def best_crop_for(day, price_of=price_flat, last_day=TOTAL_DAYS - 1,
                  labor_constrained=True, fert_cost=0.0):
    """What to plant on `day`, ranked by value.

    labor_constrained ranks by value PER LABOUR OP (the real binding
    constraint — measured 9.4 ops/worker/day) rather than per tile.
    """
    rows = []
    for c in CROPS:
        for fert in (False, True):
            v = npv_crop(c, day, price_of, fert, last_day, fert_cost)
            if v["units"] <= 0:
                continue
            key = v["per_op"] if labor_constrained else v["net"]
            rows.append((key, c, fert, v))
    rows.sort(key=lambda r: -r[0])
    return rows


def season_plan(start_day=0, price_of=price_flat, last_day=TOTAL_DAYS - 1):
    """Model-optimal planting schedule for every day of the season."""
    sched = {}
    for d in range(start_day, last_day + 1):
        rows = best_crop_for(d, price_of, last_day)
        sched[d] = rows[0] if rows else None
    return sched


if __name__ == "__main__" and "--plan" in __import__("sys").argv:
    import sys
    print("\n" + "=" * 66)
    print("7. MODEL-OPTIMAL PLANTING SCHEDULE (flat base prices, per labour op)")
    print("=" * 66)
    print("   %-5s %-12s %-6s %7s %6s %7s  %s"
          % ("day", "crop", "fert", "net$", "units", "$/op", "runners-up"))
    sched = season_plan()
    prev = None
    for d in range(0, TOTAL_DAYS):
        r = sched.get(d)
        if r is None:
            print("   %-5d %-12s %-6s %7s %6s %7s" % (d, "-", "", 0, 0, 0))
            continue
        key, c, fert, v = r
        alts = ", ".join("%s%s" % (rc[0][:4], "+f" if rf else "")
                         for _k, rc, rf, _v in best_crop_for(d)[1:3])
        mark = "" if prev == (c, fert) else "  <-- switch"
        print("   %-5d %-12s %-6s %7.0f %6d %7.1f  %s%s"
              % (d, c, "+fert" if fert else "", v["net"], v["units"],
                 v["per_op"], alts, mark))
        prev = (c, fert)


# =====================================================================
#  MARKET WAR — the shared-market differential model
# =====================================================================
# The user's doctrine, made arithmetic:
#
#   "crash the market or keep it low so the opponent cannot gain more to
#    win over us... match their outputs and sell first... push our main
#    target to what they do NOT have."
#
# The market inventory is SHARED (engine-verified). So a unit we sell does
# two things at once:
#     + earns us its price
#     - lowers the price of EVERY unit they sell afterwards
# Maximising our own gold is therefore the wrong objective. The objective
# is the DIFFERENTIAL:  (our revenue) - (their revenue).
#
# This section computes, per item and per day:
#     us_gain      what +1 unit/day of our supply earns us
#     them_loss    what it costs THEM (denial)
#     differential us_gain - them_loss   <-- the number that wins episodes
# Ranked per labour op, that is the war-optimal allocation: push volume
# into what THEY depend on, harvest what they do not.

def _sell_units(item, inv, qty):
    """Sell `qty` units one at a time. Returns (revenue, new_inventory)."""
    rev, i = 0.0, inv
    for _ in range(int(qty)):
        px = market_price(item, i)
        rev += px
        if px > PRICE_FLOOR:
            i += 1
    return rev, i


def simulate_item(item, our_units, their_units, drain=0.0,
                  inv0=MARKET_I0, days=TOTAL_DAYS, we_sell_first=True):
    """Day-by-day shared-market walk for one item.

    our_units / their_units : {day: units sold that day}
    drain                   : units/day removed by town consumption
    we_sell_first           : True if our market orders land before theirs
                              that day (the 'first-seller' race)
    Returns dict with revenues and the realised price path.
    """
    inv = inv0
    our_rev = their_rev = 0.0
    prices = []
    for d in range(days):
        q_us = float(our_units.get(d, 0))
        q_them = float(their_units.get(d, 0))
        if we_sell_first:
            r, inv = _sell_units(item, inv, q_us)
            our_rev += r
            r, inv = _sell_units(item, inv, q_them)
            their_rev += r
        else:
            r, inv = _sell_units(item, inv, q_them)
            their_rev += r
            r, inv = _sell_units(item, inv, q_us)
            our_rev += r
        inv -= drain                      # town consumption pulls it back
        prices.append(market_price(item, inv))
    return {"our_rev": our_rev, "their_rev": their_rev,
            "differential": our_rev - their_rev, "prices": prices,
            "end_inv": inv}


def _flat(units_per_day, start_day=0, days=TOTAL_DAYS):
    return {d: units_per_day for d in range(start_day, days)}


def marginal_war_value(item, our_upd, their_upd, drain=0.0,
                       extra_upd=1.0, days=TOTAL_DAYS, inv0=MARKET_I0,
                       ops_per_day=1.0, we_sell_first=True):
    """Value of adding `extra_upd` units/day of OUR supply to this item.

    Decomposed into what it earns us, what it denies them, and the
    differential (the only thing the leaderboard counts, via W/L).
    """
    base = simulate_item(item, _flat(our_upd, 0, days),
                         _flat(their_upd, 0, days), drain, inv0, days,
                         we_sell_first)
    plus = simulate_item(item, _flat(our_upd + extra_upd, 0, days),
                         _flat(their_upd, 0, days), drain, inv0, days,
                         we_sell_first)
    us_gain = plus["our_rev"] - base["our_rev"]
    them_delta = plus["their_rev"] - base["their_rev"]
    denial = -them_delta
    return {"item": item, "us_gain": us_gain, "denial": denial,
            "differential": us_gain + denial,
            "diff_per_op": (us_gain + denial) / max(1e-9, ops_per_day),
            "their_upd": their_upd, "our_upd": our_upd,
            "end_price_base": base["prices"][-1],
            "end_price_plus": plus["prices"][-1]}


# Town consumption, from the ladder replay analysis (playbook R51):
# shops unlock every 3 days and drain hard; milk 19-25/day by d9-d24,
# wool 13-37/day from d15. Everything else is gentler.
TOWN_DRAIN = {
    "WHEAT": 6.0, "CARROT": 4.0, "TOMATO": 2.0, "STRAWBERRY": 7.0,
    "MELON": 1.0, "EGG": 7.0, "MILK": 22.0, "WOOL": 22.0, "FERTILIZER": 3.0,
}

# A cow-heavy ladder winner (the class that beats us: Sutee 17 animals/$85k,
# Someswararao 15 cows, Ali Alghaithi 10 cows + 5 sheep) vs our balanced 6/6/6.
THEIR_PROFILE = {"MILK": 6.0, "WOOL": 3.0, "EGG": 4.0, "STRAWBERRY": 4.0,
                 "MELON": 2.0, "WHEAT": 6.0}
OUR_PROFILE   = {"MILK": 3.0, "WOOL": 2.0, "EGG": 4.0, "STRAWBERRY": 3.5,
                 "MELON": 2.0, "WHEAT": 6.0}
# rough labour cost of +1 unit/day of each stream, in ops/day
OPS_PER_UNIT  = {"MILK": 1.2, "WOOL": 1.0, "EGG": 0.7, "STRAWBERRY": 0.6,
                 "MELON": 0.5, "WHEAT": 0.3}


if __name__ == "__main__" and "--war" in __import__("sys").argv:
    print("\n" + "=" * 74)
    print("MARKET WAR — marginal value of +1 unit/day of OUR supply")
    print("=" * 74)
    print("opponent = cow-heavy ladder winner | drain = measured town consumption")
    print()
    print("  %-11s %7s %7s %8s %9s %9s  %s"
          % ("item", "us/day", "them/d", "us_gain", "denial", "DIFF/op", "verdict"))
    rows = []
    for it in ("MILK", "WOOL", "STRAWBERRY", "MELON", "EGG", "WHEAT"):
        r = marginal_war_value(it, OUR_PROFILE.get(it, 0.0),
                               THEIR_PROFILE.get(it, 0.0),
                               TOWN_DRAIN.get(it, 0.0),
                               ops_per_day=OPS_PER_UNIT[it])
        rows.append(r)
    rows.sort(key=lambda r: -r["diff_per_op"])
    for r in rows:
        it = r["item"]
        verdict = ("PUSH — they depend on it" if r["denial"] > r["us_gain"]
                   else "harvest quietly — we out-supply them")
        print("  %-11s %7.1f %7.1f %8.0f %9.0f %9.0f  %s"
              % (it, r["our_upd"], r["their_upd"], r["us_gain"],
                 r["denial"], r["diff_per_op"], verdict))

    print("\n  first-seller race (whoever's market order lands first that day):")
    for it in ("MILK", "STRAWBERRY"):
        a = marginal_war_value(it, OUR_PROFILE.get(it, 0.0),
                               THEIR_PROFILE.get(it, 0.0),
                               TOWN_DRAIN.get(it, 0.0),
                               ops_per_day=OPS_PER_UNIT[it],
                               we_sell_first=True)
        b = marginal_war_value(it, OUR_PROFILE.get(it, 0.0),
                               THEIR_PROFILE.get(it, 0.0),
                               TOWN_DRAIN.get(it, 0.0),
                               ops_per_day=OPS_PER_UNIT[it],
                               we_sell_first=False)
        print("    %-11s we-sell-first us_gain $%6.0f | they-sell-first us_gain $%6.0f"
              "  -> being first is worth $%.0f/unit/day"
              % (it, a["us_gain"], b["us_gain"], a["us_gain"] - b["us_gain"]))
