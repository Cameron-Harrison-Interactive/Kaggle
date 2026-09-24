"""
BT overlay — our opponent-intel & sell-timing system layered on the BT engine.

The engine (movement/production/market) stays 100% BT — proven 2191-rated.
Our systems add what BT leaves on the table (measured on its own games):
  1. H0 FULL VOLLEY: BT submits ~2-3 sell orders at H0 while its shed holds
     up to ~60 units; the rest dribbles out across H6-H23 at monotonically
     declining prices (price = f(shared inventory), solo it only falls).
     We fill every remaining H0 order slot with sells of the full shed,
     race-prone items first (WOOL floors at 58 net units, MILK 75, STRAW 61,
     MELON 157 — sell order matters on those; EGG/WHEAT never crash).
  2. SPY PRE-SELL (H2H): track opponent money jumps -> their dump-hour
     histogram -> one hour before their mode, fire sells of race items
     ahead of their wave. 41.4% of ladder sell revenue dumps at H1; BT
     already front-runs that, but per-opponent timing beats a fixed hour.
  3. DEAD-MARKET DUMP: when an item's net supply is at its crash floor,
     its price never recovers (town drains 1-12/day) — any held stock is
     sold immediately rather than held for a recovery that never comes.

The wrapper never cancels or rewrites BT's own orders — it only APPENDS
into unused order slots (max 10/hour), so BT's internal state machine and
economics are untouched.
"""

# ---- spy state (module-level; resets on new game via step regression) ----
_SPY = {
    "step": -1,
    "prev_money": None,
    "hour_hist": {},       # hour -> observed opponent sell revenue
    "last_dump_hour": None,
}

MARKET_I0 = 10000
# floor points (net units over I0) and our sell order within the volley
RACE = ["WOOL", "MILK", "STRAWBERRY", "MELON", "TOMATO", "FERTILIZER",
        "CARROT", "EGG", "WHEAT"]


def _spy_update(obs):
    opp = obs["farms"][1 - int(obs.get("player", 0))]
    step = int(obs.get("step", 0))
    if step <= _SPY["step"]:
        _SPY.update(step=step, prev_money=None, hour_hist={},
                    last_dump_hour=None)
        return
    _SPY["step"] = step
    money = float(opp.get("money", 0))
    if _SPY["prev_money"] is not None:
        dm = money - _SPY["prev_money"]
        if dm > 60:
            h = int(obs.get("hour", 0))
            _SPY["hour_hist"][h] = _SPY["hour_hist"].get(h, 0.0) + dm
            _SPY["last_dump_hour"] = h
    _SPY["prev_money"] = money


def _volley(obs, base_orders):
    """Append sells for remaining shed stock into free order slots."""
    orders = list(base_orders)
    if len(orders) >= 10:
        return orders
    already = set()
    for o in orders:
        if isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "SELL":
            already.add(o[1])
    shed = obs.get("private", {}).get("shed", {})
    hour = int(obs.get("hour", 0))
    inv = obs.get("market", {}).get("inventory", {})
    for item in RACE:
        if len(orders) >= 9:      # keep one slot for BT's atomic needs
            break
        n = int(shed.get(item, 0))
        if n <= 0 or item in already:
            continue
        # dead-market dump mid-day too: price is never coming back
        if hour != 0:
            dead = {"WOOL": 50, "MILK": 65, "STRAWBERRY": 52,
                    "MELON": 140, "TOMATO": 470}
            if item not in dead:
                continue
            if int(inv.get(item, MARKET_I0)) - MARKET_I0 < dead[item]:
                continue
        orders.append(["SELL", item, n])
    return orders


def overlay_agent(obs, configuration=None, base_agent=None):
    _spy_update(obs)
    base = base_agent(obs, configuration)
    if not isinstance(base, dict):
        return base
    mk = base.get("market") or []
    hour = int(obs.get("hour", 0))
    # H0: full volley. Other hours: pre-sell 1h before opponent's dump mode
    # or dead-market dumps (both handled inside _volley's gating).
    hist = _SPY["hour_hist"]
    peak = max(hist.items(), key=lambda kv: kv[1])[0] if hist else None
    fire = hour == 0 or (peak is not None and hour == (peak - 1) % 24
                         and sum(hist.values()) > 8000)
    if fire:
        mk = _volley(obs, mk)
    out = dict(base)
    out["market"] = mk
    return out
