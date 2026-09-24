"""v52: TT-router engine (taped elite routes) + war seller overlay.
Bench build: imports tt_router.py from the same directory.
The overlay replaces the tape's SELL orders with war sells (first-seller,
full dump, spy-gated wheat flood, endgame horn dump) while preserving every
non-SELL order (hires/seeds/animals/land) — those fund the engine. The
tape's unit actions are untouched. Feed reserve protects the tape's
PICKUP-WHEAT feeding loop.
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import tt_router as _tt

WAR_ITEMS = ("MELON", "STRAWBERRY", "MILK", "WOOL", "EGG", "CARROT", "TOMATO")

def agent(obs, config=None):
    base = _tt.agent(obs, config)
    p = int(obs["player"])
    day = int(obs.get("day", 0))
    farms = obs.get("farms", [])
    priv = obs.get("private", {}) or {}
    shed = priv.get("shed", {}) or {}

    # ---- spy: enemy wheat commitment ----
    my_w = en_w = en_an = 0
    n_an = 0
    for i, fm in enumerate(farms):
        if not isinstance(fm, dict):
            continue
        w = a = 0
        for row in fm.get("tiles", []):
            for t in row:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT" and t.get("crop") == "WHEAT":
                        w += 1
                    elif "animal" in t:
                        a += 1
        if i == p:
            my_w, n_an = w, a
        else:
            en_w, en_an = w, a

    keep_w = 0
    if day < 28:
        keep_w = max(6, n_an * 2)          # tape feeds from the shed daily
    else:
        keep_w = n_an if day < 29 else 0   # d28 feed still buys d29 output

    orders = []
    for o in base.get("market", []):
        if isinstance(o, list) and o and o[0] == "SELL":
            continue                        # replace tape sells with war sells
        orders.append(list(o))
        if len(orders) >= 10:
            break

    def room():
        return 10 - len(orders)

    # war sells fill the remaining slots (tape's hires/buys keep priority —
    # orders beyond 10 are dropped by the engine, and hires fund everything)
    if day >= 29:
        # horn: dump absolutely everything
        for it in ("MELON", "STRAWBERRY", "MILK", "WOOL", "EGG", "CARROT",
                   "TOMATO", "FERTILIZER", "WHEAT"):
            if room() <= 0:
                break
            if it == "WHEAT":
                n = shed.get(it, 0)
            else:
                n = 10 ** 6
            if n > 0:
                orders.append(["SELL", it, n])
    else:
        for it in WAR_ITEMS:
            if room() <= 0:
                break
            orders.append(["SELL", it, 10 ** 6])   # mega: drains shed, aborts empty
        fert_keep = 6
        if shed.get("FERTILIZER", 0) > fert_keep and room() > 0:
            orders.append(["SELL", "FERTILIZER", shed["FERTILIZER"] - fert_keep])
        # wheat flood only vs wheat-heavy enemies; never touch the feed reserve
        if en_w >= 10 and en_w >= 1.2 * max(1, my_w) and room() > 0:
            n = shed.get("WHEAT", 0) - keep_w
            if n > 0:
                orders.append(["SELL", "WHEAT", n])

    return {"farmer": base.get("farmer", ["PASS"]),
            "hands": base.get("hands", []),
            "market": orders[:10]}
