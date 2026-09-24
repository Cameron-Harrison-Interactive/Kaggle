#!/usr/bin/env python3
"""build_v27_selector.py — v25 Wheat16 + the shop-keyed route selector.

Selector (public state only, no seed/opponent-private knowledge):
  * steps 0-167: both routes identical (shared opening, like the top-10 MoE).
  * step 168: read town.unlocked_shops. If YARN_STORE is visible and the
    opening is not the ICE_CREAM_SHOP -> YARN_STORE dominated pair, switch
    to the HIGH tape; else stay LOW (byte-identical to v25 otherwise).
  * HIGH = v25 tape + market-only wool-sell alignment for YARN boards
    (variant chosen by the battery: merge312 | shift311 | shift313 | drop).

VERSION = HI_AgriBot_v27_ShopSelector
"""
import base64
import json
import re
import zlib

SRC = "/home/user/kaggriculture/agent/main_v25_wheat16.py"
OUT = "/home/user/kaggriculture/agent/main_v27_selector.py"

src = open(SRC).read()

# ---------------------------------------------------------------------------
# HIGH tape: patched copy of the tape. Market-only edits.
# ---------------------------------------------------------------------------
layer = '''

# ---------------------------------------------------------------------------
# v27 ShopSelector — public shop-sequence route choice (step 168)
# ---------------------------------------------------------------------------
_SHOP_STATE = {0: {"mode": None, "last": -1}, 1: {"mode": None, "last": -1}}


def _v27_high_market(step, market):
    """HIGH route market edits (wool sells aligned to the YARN demand tick).
    The town consumes at steps % 4 == 0 AFTER the market resolves, so the
    tape's tick-step wool sells already ride the spike; the one off-phase
    sell is d12h22 (step 310, phase 2). Variant:
      merge312: move the wool-12 sell to d13h0 (step 312), merged with the
                existing wool-4 sell -> one SELL WOOL 16 order.
      shift311: move the wool-12 sell to step 311 (phase 3).
      shift313: move the wool-12 sell to step 313 (phase 1, post-tick).
      drop:     drop the wool-12 sell (it lands in the terminal sweep).
    """
    variant = _V27_WOOL_VARIANT
    if variant == "base":
        return market
    if step == 310:
        if variant == "shift311":
            return []
        if variant == "shift313":
            return []
        if variant == "drop":
            return []
        if variant == "merge312":
            return []
        return market
    if step == 311 and variant == "shift311":
        return [o for o in market] + [["SELL", "WOOL", 12]]
    if step == 312 and variant == "merge312":
        out = []
        for o in market:
            if o and o[0] == "SELL" and o[1] == "WOOL":
                out.append(["SELL", "WOOL", 16])
            else:
                out.append(o)
        return out
    if step == 313 and variant == "shift313":
        return [o for o in market] + [["SELL", "WOOL", 12]]
    return market


def _v27_shop_mode(obs, step):
    """Decide once, at step 168, from the public shop list."""
    seat = _seat(obs)
    st = _SHOP_STATE[seat]
    if step < st.get("last", -1) or (st["mode"] is None and step == 0):
        st = {"mode": None, "last": -1}
        _SHOP_STATE[seat] = st
    if st["mode"] is None and step >= 168:
        town = _get(obs, "town", {}) or {}
        shops = list(_get(town, "unlocked_shops", []) or [])
        dominated = (
            len(shops) >= 2
            and shops[0] == "ICE_CREAM_SHOP"
            and shops[1] == "YARN_STORE"
        )
        st["mode"] = (
            "high" if "YARN_STORE" in shops and not dominated else "low"
        )
    st["last"] = step
    return st["mode"] or "low"
'''

anchor = '_BRAIN = {"labor": True, "cashrank": True}'
assert src.count(anchor) == 1
src = src.replace(anchor, layer + "\n\n" + anchor)

# wire into agent(): pick tape by mode, then patch HIGH market
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
        base_action = _copy_action(tape[step])
        if _v27_shop_mode(obs, step) == "high":
            base_action["market"] = _v27_high_market(
                step, base_action.get("market") or []
            )
        action = _weed_repair_action(obs, base_action, tape, step)'''
assert src.count(old_pipe) == 1
src = src.replace(old_pipe, new_pipe)

# variant knob (runtime-overridable for the battery; ship default merge312)
src += '''

# battery knob: os.environ["V27_WOOL_VARIANT"] overrides the shipped default
import os as _os
_V27_WOOL_VARIANT = _os.environ.get("V27_WOOL_VARIANT", "merge312")
'''

# version + fresh tail
src = src.replace("HI_AgriBot_v25_Wheat16", "HI_AgriBot_v27_ShopSelector")
src = src.replace("_v25_agent = agent", "_v27_agent = agent")

open(OUT, "w").write(src)
print("wrote", OUT, len(src), "chars")
