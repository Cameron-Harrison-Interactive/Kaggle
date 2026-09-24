#!/usr/bin/env python3
"""build_v28_wheatarb.py — v25 Wheat16 + the wheat-arbitrage scale-up (HIGH for v27/v28).

Transform (market-only; field choreography untouched):
  * d8-15: BUY_PRODUCT WHEAT quantities x MULT (dip buys; shed has ~50-80
    headroom there per the live traces).
  * d13/16/17/18 h0: SELL WHEAT quantities bumped to drain the extra stock
    at the mid-flood prices, proportional to the base sell sizes.
  * Everything else byte-identical. The engine clamps any overshoot, and
    the sell bumps are sized so the shed ends up with MORE wheat at d13
    than the original tape (feed-safe by construction).

VERSION = HI_AgriBot_v28_WheatArb; MULT overridable via env for the battery.
"""
import os
import re

SRC = "/home/user/kaggriculture/agent/main_v25_wheat16.py"
OUT = "/home/user/kaggriculture/agent/main_v28_wheatarb.py"

src = open(SRC).read()

layer = '''

# ---------------------------------------------------------------------------
# v28 WheatArb — scaled wheat dip-buys (d8-15) drained at the mid-flood sells
# ---------------------------------------------------------------------------
import os as _os
_V28_MULT = float(_os.environ.get("V28_MULT", "1.5"))

_V28_BUY_WINDOW = (8 * 24, 15 * 24 + 23)
_V28_SELL_STEPS = {13 * 24: 0.35, 16 * 24: 0.20, 17 * 24: 0.35,
                   18 * 24: 0.10}


def _v28_extra_bought(tape):
    """Sum of buy bumps across the window for the current MULT."""
    extra = 0.0
    for s in range(_V28_BUY_WINDOW[0], _V28_BUY_WINDOW[1] + 1):
        for o in (tape[s].get("market") or []):
            if o and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" and len(o) > 2:
                q = max(0, int(o[2]))
                extra += round(q * (_V28_MULT - 1.0))
    return int(extra)


def _v28_wheatarb(obs, action, step, tape, extra):
    try:
        if extra <= 0 or _V28_MULT <= 1.0:
            return action
        if _V28_BUY_WINDOW[0] <= step <= _V28_BUY_WINDOW[1]:
            market = list(action.get("market") or [])
            changed = False
            for o in market:
                if o and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" \\
                        and len(o) > 2:
                    q = max(0, int(o[2]))
                    o[2] = round(q * _V28_MULT)
                    changed = True
            if changed:
                action = dict(action)
                action["market"] = market
                return action
        if step in _V28_SELL_STEPS:
            w = _V28_SELL_STEPS[step]
            market = list(action.get("market") or [])
            changed = False
            for o in market:
                if o and o[0] == "SELL" and o[1] == "WHEAT" and len(o) > 2:
                    o[2] = max(0, int(o[2])) + int(round(extra * w))
                    changed = True
            if changed:
                action = dict(action)
                action["market"] = market
        return action
    except Exception:
        return action
'''

anchor = '_BRAIN = {"labor": True, "cashrank": True}'
assert src.count(anchor) == 1
src = src.replace(anchor, layer + "\n\n" + anchor)

# precompute extra once at module load (tape is immutable)
precompute = '''

# precompute the v28 bump (tape is immutable per process)
_V28_EXTRA = _v28_extra_bought(_SEAT0_ACTIONS)
'''
src = src.replace(anchor, precompute + "\n\n" + anchor)

old_pipe = '''def agent(obs, configuration=None):
    try:
        seat = _seat(obs)
        tape = _SEAT0_ACTIONS
        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(tape) - 1)
        _update_memory(obs)
        action = _weed_repair_action(obs, _copy_action(tape[step]), tape, step)'''
new_pipe = '''def agent(obs, configuration=None):
    try:
        seat = _seat(obs)
        tape = _SEAT0_ACTIONS
        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(tape) - 1)
        _update_memory(obs)
        action = _weed_repair_action(obs, _copy_action(tape[step]), tape, step)
        action = _v28_wheatarb(obs, action, step, tape, _V28_EXTRA)'''
assert src.count(old_pipe) == 1
src = src.replace(old_pipe, new_pipe)

src = src.replace("HI_AgriBot_v25_Wheat16", "HI_AgriBot_v28_WheatArb")
src = src.replace("_v25_agent = agent", "_v28_agent = agent")

open(OUT, "w").write(src)
print("wrote", OUT, len(src), "chars")
