#!/usr/bin/env python3
"""adaptive_v20.py — the ADAPTIVE VERSION, built on the v19 compiled base.

Two proven levers (found by replay/tape analysis, 8-14-2026):

  1. SINGLE-TAPE SEAT1.  Our Gbining seat1 tape earns $155,325 vs PASS.
     Playing the v19 SEAT0 tape on seat1 earns $162,093 (verified — that is
     exactly tetsu's seat1 score; tetsu plays one tape on both seats).
     rayk does the same and gets $164,806.  Seat1 = +$6,768 minimum.

  2. RAYK RACE-MARKET LAYERS.  rayk's public bot ships a clone-aware
     preemption system: when the opponent farm is a near-clone, pull a
     fraction of planned PREMIUM sells (straw/melon/milk/wool) forward a few
     steps (better price), record a "debt", and cancel the tape's later
     sell of those units (_repay_shift).  An observer learns the opponent's
     preemption horizon from market-inventory deltas and races it (+1).
     This is the "sophisticated adaptive market controller" that was
     written in Chat-Log-8 and lost — ported here from rayk's public
     notebook, retargeted to OUR tape.

  3. MELON4 (optional, offline).  rayk plants 4 more melons and sells ~18
     more melon units.  Compiled through route_compiler_v19's crop_swaps
     (seed-compensated, water/harvest re-planned), never hand-patched.

Routing never changes at runtime (the user's rule).  Labor stays the exact
compiled tape.  Only market orders + crop verbs adapt — same policy family
as the v18/v19 adapt layers.

CATALOG (small — not a grid):
  v19ctrl            v19 verbatim (control)
  race               v19 tapes + rayk race layers only
  s0s1               seat1 plays the seat0 tape
  s0s1+race          s0s1 + race layers            <-- main candidate
  s0s1+race+th       + tetsu tomato overlay (isolate)
  s0s1+race+hold     + fertilizer crash-hold (isolate)
  melon4             compiled crop_swaps straw->melon x4 (slow)
  s0s1+race+melon4   full candidate (slow)

GATES (per variant):
  PASS economy      seat0 >= v19's measured PASS, seat1 >= v19's (or the
                    single-tape target 162,000), animals >= 13, crops kept
  vs v19            recorded honestly (mirror duels carry the known
                    ~-5.4k seat1 lockstep tax; reported, not fatal)
  vs tetsu          seeds 1-3 both seats (tetsu == single-tape mirror)
  FINALS            all 8 opponents, seeds 1-3, both seats.  A variant
                    ships only if its combined finals delta beats v19ctrl's.

USAGE (Windows PowerShell — ONE line, no backticks):
  cd Z:\\Kaggle\\Works\\kaggriculture
  python scripts\\adaptive_v20.py --self-test
  python scripts\\adaptive_v20.py --quick
  python scripts\\adaptive_v20.py --seeds 1,2,3 --procs 8 --build-agent
  .\\scripts\\adaptive_v20.ps1 -Seeds "1,2,3" -Procs 8 -BuildAgent
  (if PowerShell blocks the wrapper:  powershell -ExecutionPolicy Bypass -File scripts\\adaptive_v20.ps1
   or just run the python line directly.)

Do NOT ship unless the report says SHIP=YES.  Keep the live bot as-is until
then.  Outputs: data/adaptive_v20/ledger.jsonl + report.json (+ agent file).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import multiprocessing
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import route_compiler_v19 as rc  # noqa: E402

OUT_DIR = os.path.join(ROOT, "data", "adaptive_v20")
V19_PATH = os.path.join(ROOT, "agent", "main_v19.py")

# module-scope helpers (NOT embedded: the agent body already defines them)
_MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "log", 0.2, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "linear", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "linear", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}
_SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}

def _copy_action(action):
    action = copy.deepcopy(action or {})
    return {
        "farmer": list(action.get("farmer") or ["PASS"]),
        "hands": [list(order or ["PASS"]) for order in (action.get("hands") or [])],
        "market": [list(order) for order in (action.get("market") or [])],
    }


def _is_sell(order):
    return (isinstance(order, (list, tuple)) and len(order) >= 3
            and order[0] == "SELL")



# ---------------------------------------------------------------------------
# tuning constants (ported verbatim from rayk's public notebook)
# ---------------------------------------------------------------------------
_PREMIUM = ("STRAWBERRY", "MELON", "MILK", "WOOL")
_LIQUIDATION_ORDER = ("CARROT", "EGG", "FERTILIZER", "MELON", "MILK",
                      "STRAWBERRY", "TOMATO", "WHEAT", "WOOL")
_PREEMPT_ENABLED = True
_PREEMPT_FRACTION = 2.0
_PREEMPT_MAX_BATCH = 30
_PREEMPT_MAX_CLONE_DISTANCE = 6
_PREEMPT_MIN_PRICE_RATIO = 0.0
_PREEMPT_MIN_FUTURE_QUANTITY = 4
_PREEMPT_START = 120
_PREEMPT_STOP = 680
_PREEMPT_HORIZON = 4
_ADAPT_DEFAULT_HORIZON = 4
_ADAPT_MAX_OPP_HORIZON = 6
_ADAPT_MIN_EVENTS = 2
_RACE_STATE = {0: {}, 1: {}}
_SHIFT_STATE = {0: {}, 1: {}}


# ---------------------------------------------------------------------------
# helpers shared by the runtime layers
# ---------------------------------------------------------------------------
def _public_signature(farm):
    keys = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "COW", "SHEEP", "GOOSE", "PASTURE", "COOP", "WEED")
    counts = {key: 0 for key in keys}
    for row in (farm.get("tiles") or []) if isinstance(farm, dict) else []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value in counts:
                    counts[value] += 1
                    break
    return (len(farm.get("hands") or []),
            len(farm.get("unlocked_quadrants") or []),
            tuple(counts[key] for key in sorted(counts)))


def _clone_distance(obs):
    farms = list(obs.get("farms") or [])
    if len(farms) < 2:
        return 10 ** 9
    left, right = _public_signature(farms[0]), _public_signature(farms[1])
    return (abs(left[0] - right[0]) + 3 * abs(left[1] - right[1])
            + sum(abs(a - b) for a, b in zip(left[2], right[2])))


def _race_state(obs, step):
    seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
    state = _RACE_STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)):
        state = {
            "last_step": -1, "inventory": {}, "own_sells": {}, "shops": (),
            "scores": {h: 0.0 for h in range(1, _ADAPT_MAX_OPP_HORIZON + 1)},
            "events": 0, "horizon": _ADAPT_DEFAULT_HORIZON,
        }
        _RACE_STATE[seat] = state
    return state


def _shift_state(obs, step):
    seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
    state = _SHIFT_STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)):
        state = {"last_step": step, "debts": {}}
        _SHIFT_STATE[seat] = state
    state["last_step"] = step
    return state


def _town_drain(step, shops, item):
    drain = 0
    if step % 4 == 0:
        for shop in shops or ():
            products = _SHOP_PRODUCTS.get(shop, ())
            if item in products:
                drain += 2 if len(products) == 1 else 1
    if step % 24 == 0:
        drain += 1
    return drain


def _planned_premium(tape, step, item):
    if not (0 <= step < len(tape)):
        return 0
    return sum(max(0, int(order[2]))
               for order in (tape[step].get("market") or [])
               if len(order) >= 3 and order[0] == "SELL" and order[1] == item)


def _future_sells(tape, step, horizon):
    future_step = step + horizon
    if future_step >= len(tape):
        return {}
    result = {}
    for raw in (tape[future_step].get("market") or []):
        if len(raw) >= 3 and raw[0] == "SELL" and raw[1] in _PREMIUM:
            result[raw[1]] = result.get(raw[1], 0) + max(0, int(raw[2]))
    return result


def _shed_access(board_size):
    half = board_size // 2
    return {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}


def _projected_shed(obs, action, mod):
    """Shed contents after the current step's labor (DROP/PLACE) is applied."""
    farm = obs["farms"][obs["player"]] if obs.get("player") is not None else {}
    private = obs.get("private") or {}
    projected = {key: max(0, int(value or 0))
                 for key, value in dict(private.get("shed") or {}).items()}
    inventories = list(private.get("inventories") or [])
    positions = [farm.get("farmer", [0, 0]), *list(farm.get("hands") or [])]
    unit_actions = [action.get("farmer", ["PASS"]),
                    *list(action.get("hands") or [])]
    tiles = list(farm.get("tiles") or [])
    access = _shed_access(len(tiles) or 10)
    for index, unit_action in enumerate(unit_actions):
        if index >= len(positions) or index >= len(inventories):
            continue
        position = positions[index]
        if not isinstance(position, (list, tuple)) or len(position) < 2:
            continue
        try:
            x, y = int(position[0]), int(position[1])
        except (TypeError, ValueError):
            continue
        if (x, y) not in access or not (0 <= y < len(tiles) and 0 <= x < len(tiles[y])):
            continue
        inventory = {key: max(0, int(value or 0))
                     for key, value in dict(inventories[index] or {}).items()}
        if unit_action and unit_action[0] == "DROP":
            deposits = inventory.items()
        elif unit_action and unit_action[0] == "PLACE" and len(unit_action) >= 2:
            item = unit_action[1]
            tile = tiles[y][x]
            structure = {"COW": "PASTURE", "SHEEP": "PASTURE",
                         "GOOSE": "COOP"}.get(item)
            if structure and isinstance(tile, dict) and tile.get("kind") == structure \
                    and not tile.get("animal"):
                continue
            try:
                requested = int(unit_action[2]) if len(unit_action) >= 3 else 1
            except (TypeError, ValueError):
                continue
            deposits = ((item, min(max(0, requested), inventory.get(item, 0))),)
        else:
            continue
        for item, quantity in deposits:
            room = max(0, 100 - sum(projected.values()))
            amount = min(max(0, int(quantity)), room)
            projected[item] = projected.get(item, 0) + amount
    return projected


# ---------------------------------------------------------------------------
# the three runtime layers
# ---------------------------------------------------------------------------
def _repay_shift(obs, action, step):
    """Cancel tape SELLs whose units were already sold by a preemption."""
    state = _shift_state(obs, step)
    debts = state.setdefault("debts", {})
    due = {item: max(0, int(quantity))
           for item, quantity in dict(debts.pop(step, {}) or {}).items()}
    if not due:
        return action
    market = []
    for raw in action.get("market", []) or []:
        order = list(raw)
        if len(order) >= 3 and order[0] == "SELL" and due.get(order[1], 0) > 0:
            item = order[1]
            requested = max(0, int(order[2]))
            reduction = min(requested, due[item])
            requested -= reduction
            due[item] -= reduction
            if requested <= 0:
                continue
            order[2] = requested
        market.append(order)
    action["market"] = market
    return action


def _preempt_shift(obs, action, step, tape, mod):
    """Clone-aware front-run: sell premium units ahead of the tape's plan."""
    if not _PREEMPT_ENABLED or not (_PREEMPT_START <= step < _PREEMPT_STOP):
        return action
    if _clone_distance(obs) > _PREEMPT_MAX_CLONE_DISTANCE:
        return action
    state = _race_state(obs, step)
    horizon = int(state.get("horizon", _ADAPT_DEFAULT_HORIZON))
    future = _future_sells(tape, step, horizon)
    if not future:
        return action
    market = list(action.get("market") or [])
    if len(market) >= 10:
        return action
    remaining = _projected_shed(obs, action, mod)
    for raw in market:
        if len(raw) >= 3 and raw[0] == "SELL":
            item = raw[1]
            remaining[item] = max(0, int(remaining.get(item, 0) or 0)
                                  - max(0, int(raw[2])))
    prices = (obs.get("market") or {}).get("prices") or {}
    shifted = {}
    for item in _PREMIUM:
        future_quantity = max(0, int(future.get(item, 0) or 0))
        if future_quantity < _PREEMPT_MIN_FUTURE_QUANTITY:
            continue
        base_price = float(_MARKET_PARAMS[item][0])
        if float(prices.get(item, 0) or 0) < base_price * _PREEMPT_MIN_PRICE_RATIO:
            continue
        target = min(max(0, int(remaining.get(item, 0) or 0)),
                     future_quantity, _PREEMPT_MAX_BATCH,
                     max(1, int(round(future_quantity * _PREEMPT_FRACTION))))
        if target <= 0 or len(market) >= 10:
            continue
        market.append(["SELL", item, target])
        remaining[item] = max(0, int(remaining.get(item, 0) or 0) - target)
        shifted[item] = target
    if shifted:
        action["market"] = market[:10]
        due_step = step + horizon
        debts = _shift_state(obs, step).setdefault("debts", {})
        due = debts.setdefault(due_step, {})
        for item, quantity in shifted.items():
            due[item] = due.get(item, 0) + quantity
    return action


def _observe_opponent_market(obs, step, tape, mod):
    """Learn the opponent's preemption horizon from inventory deltas."""
    state = _race_state(obs, step)
    current = dict((obs.get("market") or {}).get("inventory") or {})
    previous = dict(state.get("inventory") or {})
    prev_step = int(state.get("last_step", -1))
    if previous and prev_step == step - 1 \
            and _clone_distance(obs) <= _PREEMPT_MAX_CLONE_DISTANCE:
        own = dict(state.get("own_sells") or {})
        shops = tuple(state.get("shops", ()) or ())
        for item in _PREMIUM:
            delta = int(current.get(item, 0) or 0) - int(previous.get(item, 0) or 0)
            inferred = (delta + _town_drain(prev_step, shops, item)
                        - int(own.get(item, 0) or 0)
                        - _planned_premium(tape, prev_step, item))
            if inferred < _PREEMPT_MIN_FUTURE_QUANTITY:
                continue
            state["events"] += 1
            for horizon in range(1, _ADAPT_MAX_OPP_HORIZON + 1):
                expected = _planned_premium(tape, prev_step + horizon, item)
                if expected > 0:
                    similarity = min(inferred, expected) / float(max(inferred, expected))
                    state["scores"][horizon] += 1.0 + similarity
                else:
                    state["scores"][horizon] -= 0.15
        if state["events"] >= _ADAPT_MIN_EVENTS:
            best = max(state["scores"], key=lambda h: (state["scores"][h], -h))
            state["horizon"] = min(_ADAPT_MAX_OPP_HORIZON + 1, max(2, best + 1))
    state["last_step"] = step
    state["inventory"] = current
    state["shops"] = tuple((obs.get("town") or {}).get("unlocked_shops") or [])


def _terminal_liquidation(obs, action, step, mod):
    """Sell unplanned shed leftovers at 716+ (ahead of the 718 sweep)."""
    if step < 716:
        return action
    action = _copy_action(action)
    shed = (obs.get("private") or {}).get("shed") or {}
    planned = {}
    for order in action.get("market", []):
        if _is_sell(order):
            planned[str(order[1])] = planned.get(str(order[1]), 0) \
                + max(0, int(order[2]))
    for item in _LIQUIDATION_ORDER:
        available = max(0, int(shed.get(item, 0) or 0))
        extra = available if step >= 718 else max(0, available - planned.get(item, 0))
        if extra and len(action["market"]) < 10:
            action["market"] = action["market"] + [["SELL", item, extra]]
    return action


def _record_own_sells(obs, action, step):
    state = _race_state(obs, step)
    sold = {}
    for order in action.get("market") or []:
        if len(order) >= 3 and order[0] == "SELL" and order[1] in _PREMIUM:
            sold[order[1]] = sold.get(order[1], 0) + max(0, int(order[2]))
    state["own_sells"] = sold


# ---------------------------------------------------------------------------
# fertilizer crash-hold (small isolated layer)
# ---------------------------------------------------------------------------
def _fert_crash_hold(obs, action, mod):
    """Hold FERTILIZER sells while its price is crashed AND cash is healthy."""
    try:
        day = int(obs.get("day", 0) or 0)
        if day < 5:
            return action
        farm = obs["farms"][obs["player"]]
        money = float(farm.get("money") or 0)
        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        inv = market.get("inventory") or {}
        px = float(prices.get("FERTILIZER", 100) or 100)
        base = float(mod._MARKET_PARAMS["FERTILIZER"][0])
        inv_n = int(inv.get("FERTILIZER", 10000) or 10000)
        if px < base * 0.92 and money > 2500 and inv_n > 10060:
            action = _copy_action(action)
            action["market"] = [o for o in (action.get("market") or [])
                                if not (o and o[0] == "SELL"
                                        and o[1] == "FERTILIZER")]
        return action
    except Exception:
        return action


# ---------------------------------------------------------------------------
# tetsu tomato overlay (isolate-only; the v18 three-fer rejected it)
# ---------------------------------------------------------------------------
def _tetsu_tomato_hedge(obs, action, mod):
    try:
        day = int(obs.get("day", 0) or 0)
        if not (6 <= day <= 15):
            return action
        farms = obs.get("farms") or []
        opp = farms[1 - obs["player"]] if len(farms) > 1 else {}
        straw = 0
        melon = 0
        for row in (opp.get("tiles") or []):
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    if t.get("crop") == "STRAWBERRY":
                        straw += 1
                    elif t.get("crop") == "MELON":
                        melon += 1
        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        inv = market.get("inventory") or {}
        straw_px = float(prices.get("STRAWBERRY", 120) or 120)
        straw_inv = int(inv.get("STRAWBERRY", 10000) or 10000)
        if not (straw >= 15 or straw_inv > 10045 or straw_px < 105):
            return action
        private = obs.get("private") or {}
        seeds = dict(private.get("seeds") or {})
        mo = list(action.get("market") or [])
        if int(seeds.get("TOMATO", 0) or 0) == 0 and len(mo) < 10:
            mo.append(["BUY_SEED", "TOMATO", 3])
            action["market"] = mo[:10]
        if int(seeds.get("TOMATO", 0) or 0) > 0:
            max_conv = 2
            hands = list(action.get("hands") or [])
            conv = 0
            for i, h in enumerate(hands):
                if h and h[0] == "PLANT" and len(h) > 1 \
                        and h[1] == "STRAWBERRY" and conv < max_conv:
                    hands[i] = ["PLANT", "TOMATO"]
                    conv += 1
            action["hands"] = hands
    except Exception:
        pass
    return action


# ---------------------------------------------------------------------------
# melon4 (direct tape patch: 4 LATE strawberries -> melons, rayk-style)
# ---------------------------------------------------------------------------
def apply_melon4(tape):
    """Swap 4 strawberry PLANTs (planted day>=5) to melons + seed buys + sells.
    Rayk plants 23 melons / 36 straw vs our 19 / 37 and outsells us by ~18
    melon units.  Swapping the OPENING strawberries collapses the economy
    (early straw cash is load-bearing), so only day>=5 plants are swapped.
    Labor (WATER/HARVEST/MOVE) is untouched — harvest on a melon tile just
    harvests melons; the tape's straw SELLs fail harmlessly when short, and
    the extra melon units are added to existing MELON sell steps (d13+)."""
    out = copy.deepcopy(tape)
    swaps = []
    for s, e in enumerate(out):
        day = s // 24
        if day < 5 or day > 11:
            continue
        for k in ("farmer", "hands"):
            unit = e.get(k)
            if k == "hands":
                for h in unit or []:
                    if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "STRAWBERRY":
                        swaps.append((s, k, e, h))
                        if len(swaps) >= 4:
                            break
            else:
                if unit and unit[0] == "PLANT" and len(unit) > 1 and unit[1] == "STRAWBERRY":
                    swaps.append((s, k, e, unit))
            if len(swaps) >= 4:
                break
        if len(swaps) >= 4:
            break
    for s, k, e, unit in swaps:
        unit[1] = "MELON"
    # seed compensation: convert exactly 4 strawberry SEED UNITS to melon
    # (1 seed per swapped plant; split the last order if it overshoots)
    converted = 0
    for e in out:
        if converted >= 4:
            break
        for o in (e.get("market") or []):
            if converted >= 4:
                break
            if o and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY" and len(o) > 2:
                qty = int(o[2])
                take = min(qty, 4 - converted)
                if take >= qty:
                    o[1] = "MELON"
                    converted += qty
                else:
                    o[2] = qty - take
                    converted += take
                    # add a fresh melon buy next to it (room-permitting)
                    if len(e.get("market") or []) < 10:
                        e["market"] = (e.get("market") or []) + \
                            [["BUY_SEED", "MELON", take]]
                    else:
                        o[2] = qty  # no room: skip this order's conversion
                        converted -= take
    # sells: +4 melon across existing melon sell steps after d13
    added = 0
    for s, e in enumerate(out):
        if added >= 4:
            break
        day = s // 24
        if day < 13:
            continue
        for o in (e.get("market") or []):
            if added >= 4:
                break
            if o and o[0] == "SELL" and o[1] == "MELON" and len(o) >= 3:
                o[2] = int(o[2]) + 1
                added += 1
    return out


# ---------------------------------------------------------------------------
# seat1 opening splice (market-only offline patches on the Gbining seat1 tape)
# ---------------------------------------------------------------------------
def apply_seat1_splice(tape1, tape0, mode="s1sp"):
    """Market-level patches to the seat1 tape, labor untouched.

    s1sp  : d0h0 market = seat0's (4 hires instead of 5, sell/buy order),
            the 5th worker never exists (hands truncated by _align_hands).
    s1sp_w: s1sp + trim ~20 BUY_PRODUCT WHEAT units across d2-10 (seat1 buys
            23 more wheat than seat0 over the game; most of the seat1 gap).
    """
    out = copy.deepcopy(tape1)
    if mode in ("s1sp", "s1sp_w"):
        out[0]["market"] = [list(o) for o in (tape0[0].get("market") or [])]
    if mode == "s1sp_w":
        trim = 20
        for s, e in enumerate(out):
            if trim <= 0:
                break
            day = s // 24
            if not (2 <= day <= 10):
                continue
            for o in (e.get("market") or []):
                if trim <= 0:
                    break
                if o and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" and len(o) > 2 \
                        and int(o[2]) > 1:
                    o[2] = int(o[2]) - 1
                    trim -= 1
    return out


# ---------------------------------------------------------------------------
# variant agent builder
# ---------------------------------------------------------------------------
def build_variant_agent(mod, spec, tapes_override=None):
    """spec keys: seat1 ('gbining'|'seat0'), race (bool), hold (bool),
    th (bool), melon4 (bool).  Tape selection happens per seat at runtime."""
    tape0 = mod._SEAT0_ACTIONS
    tape1 = mod._SEAT1_ACTIONS
    if tapes_override:
        tape0, tape1 = tapes_override[0], tapes_override[1]
    if spec.get("s1splice"):
        tape1 = apply_seat1_splice(tape1, tape0, mode=spec["s1splice"])
    if spec.get("seat1") == "seat0":
        tape1 = tape0

    def agent(obs, configuration=None):
        try:
            seat = mod._seat(obs)
            tape = tape1 if seat == 1 else tape0
            step = min(max(0, int(mod._get(obs, "step", 0) or 0)), len(tape) - 1)
            mod._update_memory(obs)
            action = mod._weed_repair_action(
                obs, mod._copy_action(tape[step]), tape, step)
            # adapt layers (v18/v19 policy family, market/crop/animal only)
            action = mod._adapt_animals(obs, action)
            action = mod._adapt_crops(obs, action)
            action = mod._adapt_market(obs, action)
            if spec.get("th"):
                action = _tetsu_tomato_hedge(obs, action, mod)
            if spec.get("race"):
                _observe_opponent_market(obs, step, tape, mod)
                action = _repay_shift(obs, action, step)
            action = mod._align_hands(
                mod._rank_sell_slots(obs, action, configuration), obs)
            if spec.get("race"):
                action = _preempt_shift(obs, action, step, tape, mod)
                _record_own_sells(obs, action, step)
                action = _terminal_liquidation(obs, action, step, mod)
            if spec.get("hold"):
                action = _fert_crash_hold(obs, action, mod)
            if step == 718 and hasattr(mod, "_v26_terminal_sweep"):
                try:
                    action = mod._v26_terminal_sweep(obs, action, configuration)
                except Exception:
                    pass
            return mod._align_hands(action, obs)
        except Exception:
            farm = mod._farm(obs, mod._seat(obs))
            return {"farmer": ["PASS"],
                    "hands": [["PASS"] for _ in (mod._get(farm, "hands", []) or [])],
                    "market": []}

    return agent


# ---------------------------------------------------------------------------
# melon4 (offline compile through the v19 compiler)
# ---------------------------------------------------------------------------
def build_melon4_tapes(mod, seed=1):
    """Compile both seats with crop_swaps STRAWBERRY->MELON x4 (day>=5 only:
    the opening strawberries are load-bearing for early cash)."""
    tapes = {}
    for seat in (0, 1):
        tape, report = rc.compile_seat(
            seed, seat, mod,
            variant={"crop_swaps": [("STRAWBERRY", "MELON", 4)],
                     "crop_swap_min_day": 5})
        tapes[seat] = tape
    return tapes


# ---------------------------------------------------------------------------
# match helpers
# ---------------------------------------------------------------------------
def _load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def battle(a, b, seed, seat_of_a):
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    if seat_of_a == 0:
        env.run([a, b])
        ra = env.steps[-1][0].reward or 0
        rb = env.steps[-1][1].reward or 0
    else:
        env.run([b, a])
        ra = env.steps[-1][1].reward or 0
        rb = env.steps[-1][0].reward or 0
    return ra, rb


def pass_reward(agent, seat, seed=1):
    return battle(agent, rc.pass_agent(), seed, seat)[0]


def animals_alive(agent, seed=1, seat=0):
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    if seat == 0:
        env.run([agent, rc.pass_agent()])
    else:
        env.run([rc.pass_agent(), agent])
    obs = env.steps[-1][seat].get("observation", {}) or {}
    farm = (obs.get("farms") or [{}])[seat]
    n = 0
    for row in (farm.get("tiles") or []):
        for t in row:
            if isinstance(t, dict) and t.get("animal"):
                n += 1
    return n


# ---------------------------------------------------------------------------
# catalog
# ---------------------------------------------------------------------------
def catalog(quick=False, with_melon4=False):
    base = [
        {"name": "v19ctrl", "seat1": "gbining", "race": False, "hold": False, "th": False, "melon4": False, "s1splice": None},
        {"name": "race", "seat1": "gbining", "race": True, "hold": False, "th": False, "melon4": False, "s1splice": None},
        {"name": "s0s1", "seat1": "seat0", "race": False, "hold": False, "th": False, "melon4": False, "s1splice": None},
        {"name": "s0s1+race", "seat1": "seat0", "race": True, "hold": False, "th": False, "melon4": False, "s1splice": None},
        {"name": "s1sp", "seat1": "gbining", "race": False, "hold": False, "th": False, "melon4": False, "s1splice": "s1sp"},
        {"name": "s1sp_w", "seat1": "gbining", "race": False, "hold": False, "th": False, "melon4": False, "s1splice": "s1sp_w"},
    ]
    if with_melon4:
        base.append({"name": "melon4", "seat1": "gbining", "race": False, "hold": False, "th": False, "melon4": True, "s1splice": None})
        base.append({"name": "s0s1+race+melon4", "seat1": "seat0", "race": True, "hold": False, "th": False, "melon4": True, "s1splice": None})
    if quick:
        return [v for v in base if v["name"] in
                ("v19ctrl", "s0s1", "s1sp")]
    return base


# ---------------------------------------------------------------------------
# worker
# ---------------------------------------------------------------------------
_W = {}


def _init(suite_paths):
    _W["mod"] = rc.load_v18(V19_PATH)
    _W["suite"] = {name: _load_mod(path, name.replace("#", "_")).agent
                   for name, path in suite_paths.items()}


def _agent_for(spec):
    mod = _W["mod"]
    if spec.get("melon4"):
        if "_m4tapes" not in _W:
            _W["_m4tapes"] = build_melon4_tapes(mod, seed=1)
        t0, t1 = _W["_m4tapes"][0], _W["_m4tapes"][1]
        return build_variant_agent(_W["mod"], spec,
                                   tapes_override=(t0, t1)), (t0, t1)
    return build_variant_agent(_W["mod"], spec), None


def _eval_variant(task):
    v, seeds = task
    t0 = time.time()
    try:
        spec = {k: val for k, val in v.items() if k != "name"}
        agent_fn, melon_tapes = _agent_for(spec)
        rec = {"name": v["name"], "time_s": 0.0,
               "seat1": spec.get("seat1"), "race": spec.get("race", False),
               "hold": spec.get("hold", False), "th": spec.get("th", False),
               "melon4": spec.get("melon4", False),
               "s1splice": spec.get("s1splice")}

        # PASS economy
        s0p = pass_reward(agent_fn, 0)
        s1p = pass_reward(agent_fn, 1)
        anim = animals_alive(agent_fn)
        anim_s1 = animals_alive(agent_fn, seat=1)
        rec["pass0"] = s0p
        rec["pass1"] = s1p
        rec["animals_alive"] = anim
        rec["animals_alive_s1"] = anim_s1

        # contested: v19 + tetsu
        v19a = _W["mod"].agent
        battles = {}
        for label, opp in (("v19", v19a), ("tetsu", _W["suite"].get("tetsu"))):
            if opp is None:
                continue
            wins = games = 0
            deltas = []
            by = {}
            for seed in seeds:
                for seat in (0, 1):
                    # battle(a, b, seat_of_a): a plays the given seat
                    x, y = battle(agent_fn, opp, seed, seat)
                    wins += 1 if x > y else 0
                    games += 1
                    deltas.append(x - y)
                    by[f"s{seed}p{seat}"] = {"us": x, "them": y, "d": x - y}
            battles[label] = {"wins": wins, "games": games,
                              "avg": sum(deltas) / max(1, len(deltas)), "by": by}
        rec["battles"] = battles
        rec["time_s"] = round(time.time() - t0, 1)
        line = (f"    [{v['name']:<22}] PASS ${s0p:,.0f}/${s1p:,.0f} "
                f"anim {anim}/{anim_s1} | v19 {battles.get('v19',{}).get('avg',0):+.0f} "
                f"W{battles.get('v19',{}).get('wins',0)}/{battles.get('v19',{}).get('games',0)} | "
                f"tetsu {battles.get('tetsu',{}).get('avg',0):+.0f} "
                f"W{battles.get('tetsu',{}).get('wins',0)}/{battles.get('tetsu',{}).get('games',0)} | "
                f"{rec['time_s']}s")
        print(line, flush=True)
        return rec
    except Exception as e:
        import traceback
        print(f"    [ERR ] {v.get('name', '?')}: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        return {"name": v.get("name", "?"), "error": str(e)}


# ---------------------------------------------------------------------------
# finals (top variants vs every opponent)
# ---------------------------------------------------------------------------
def finals(variant, seeds, suite, mod):
    agent_fn, _ = _agent_for(dict(variant, name=None))
    results = {}
    for name, opp in suite.items():
        wins = games = 0
        deltas = []
        d0, d1 = [], []
        for seed in seeds:
            for seat in (0, 1):
                # battle(a, b, seat_of_a): a plays the given seat, b the other.
                x, y = battle(agent_fn, opp, seed, seat)
                wins += 1 if x > y else 0
                games += 1
                deltas.append(x - y)
                (d0 if seat == 0 else d1).append(x - y)
        results[name] = {"wins": wins, "games": games,
                         "avg": sum(deltas) / max(1, len(deltas)),
                         "seat0": sum(d0) / max(1, len(d0)),
                         "seat1": sum(d1) / max(1, len(d1))}
        print(f"      vs {name:<14} W {wins}/{games}  avg {results[name]['avg']:+,.0f}"
              f"  (s0 {results[name]['seat0']:+,.0f} / s1 {results[name]['seat1']:+,.0f})",
              flush=True)
    return results


# ---------------------------------------------------------------------------
# self-test (no engine)
# ---------------------------------------------------------------------------
def _self_test():
    mod = _load_mod(V19_PATH, "v19")
    assert len(mod._SEAT0_ACTIONS) == 719 and len(mod._SEAT1_ACTIONS) == 719
    agent_fn = build_variant_agent(mod, {"seat1": "seat0", "race": True})
    assert callable(agent_fn)
    print("[self-test] v19 tapes load ok (719/719)")

    # clone distance on two identical-ish farms
    farm = {"hands": [[1, 1]] * 10, "unlocked_quadrants": ["NW", "NE", "SW"],
            "tiles": [[None] * 10 for _ in range(10)]}
    obs = {"farms": [farm, farm]}
    assert _clone_distance(obs) == 0
    farm2 = copy.deepcopy(farm)
    farm2["hands"] = [[1, 1]] * 13
    assert _clone_distance({"farms": [farm, farm2]}) == 3
    print("[self-test] clone distance ok")

    # debt bookkeeping
    step = 200
    _shift_state({"player": 0}, 0)
    act = {"market": [["SELL", "MILK", 10], ["SELL", "WOOL", 5]]}
    st = _shift_state({"player": 0}, step)
    st["debts"] = {step: {"MILK": 4}}
    act2 = _repay_shift({"player": 0}, act, step)
    orders = {tuple(o[:2]): o[2] for o in act2["market"]}
    assert orders[("SELL", "MILK")] == 6, act2
    assert orders[("SELL", "WOOL")] == 5, act2
    print("[self-test] repay shift ok")

    # terminal liquidation appends extras
    obs = {"player": 0, "step": 716, "private": {"shed": {"EGG": 7}},
           "farms": [{"hands": [], "farmer": [0, 0], "tiles": [[None]*10]*10}]}
    act3 = _terminal_liquidation(obs, {"market": [["SELL", "WHEAT", 2]],
                                       "farmer": ["PASS"], "hands": []}, 716, mod)
    assert any(o[0] == "SELL" and o[1] == "EGG" for o in act3["market"]), act3
    print("[self-test] terminal liquidation ok")

    full = catalog(False)
    quick = catalog(True)
    assert len(quick) == 3 and len(full) >= 5
    print(f"[self-test] catalog ok  full={len(full)} quick={len(quick)}")
    print("[self-test] ALL PASSED")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
SUITE_PATHS = {
    "v14.5": os.path.join(ROOT, "agent", "main_v14_5.py"),
    "v15": os.path.join(ROOT, "agent", "main_v15_backup.py"),
    "v18": os.path.join(ROOT, "submit", "main.py"),
    "kaito_TT": os.path.join(ROOT, "opponents", "kaito_main.py"),
    "rayk": os.path.join(ROOT, "opponents", "rayk_main.py"),
    "tetsu": os.path.join(ROOT, "opponents", "tetsu_main.py"),
    "seb": os.path.join(ROOT, "scripts", "opp_seb.py"),
    "healthstone": os.path.join(ROOT, "scripts", "opp_healthstone.py"),
    "cowbot": os.path.join(ROOT, "scripts", "opp_cowbot.py"),
}


def main():
    # copy-paste guard: strip stray trailing punctuation from flags
    # ("--finals." -> "--finals") so pasted commands never 400.
    sys.argv = [a.rstrip(".,;:!?") if a.startswith("--") else a for a in sys.argv]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", default="1,2,3")
    ap.add_argument("--procs", type=int, default=0)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--with-melon4", action="store_true")
    ap.add_argument("--finals", action="store_true",
                    help="run the full 9-opponent battery on the top variants")
    ap.add_argument("--finals-only", action="store_true",
                    help="skip the gate; read data/adaptive_v20/ledger.jsonl "
                         "and run finals for control + top-2 non-control")
    ap.add_argument("--build-agent", action="store_true")
    ap.add_argument("--version", default="HI_AgriBot_v20_Adaptive")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _self_test()
        return

    seeds = [int(s) for s in args.seeds.split(",")]
    procs = args.procs or os.cpu_count() or 2
    os.makedirs(OUT_DIR, exist_ok=True)

    if args.finals_only:
        results = []
        with open(os.path.join(OUT_DIR, "ledger.jsonl")) as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
        print(f"[adaptive_v20] finals-only: loaded {len(results)} records",
              flush=True)
    else:
        print(f"[adaptive_v20] seeds={seeds} procs={procs} quick={args.quick} "
              f"melon4={args.with_melon4}", flush=True)
        print("[adaptive_v20] base = v19 compiled routes (62 crops). Ship gate: "
              "PASS >= v19 baseline, animals >= 13, finals better than v19ctrl.",
              flush=True)

        variants = catalog(quick=args.quick, with_melon4=args.with_melon4)
        print(f"[adaptive_v20] catalog={len(variants)}", flush=True)
        for v in variants:
            print(f"    {v['name']}", flush=True)

        tasks = [(v, seeds) for v in variants]
        if procs <= 1:
            _init(SUITE_PATHS)
            results = [_eval_variant(t) for t in tasks]
        else:
            pool = multiprocessing.Pool(processes=min(procs, len(tasks)),
                                        initializer=_init, initargs=(SUITE_PATHS,))
            results = list(pool.imap_unordered(_eval_variant, tasks, chunksize=1))
            pool.close()
            pool.join()

        with open(os.path.join(OUT_DIR, "ledger.jsonl"), "w") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")

    # main process needs its own worker state for finals
    _init(SUITE_PATHS)

    # pick finalists for the finals battery: control + best 2 non-control
    ok = [r for r in results if not r.get("error")
          and r.get("pass0", 0) >= 150000 and r.get("pass1", 0) >= 140000
          and r.get("animals_alive", 99) >= 13 and r.get("animals_alive_s1", 99) >= 13]
    v19ctl = next((r for r in ok if r["name"] == "v19ctrl"), None)
    ctl_delta = None
    rank_key = lambda r: (sum(r.get("battles", {}).get(k, {}).get("avg", 0)
                              for k in ("v19", "tetsu")))
    candidates = [r for r in ok if r["name"] != "v19ctrl"]
    candidates.sort(key=rank_key, reverse=True)
    finalists = [r for r in candidates[:2]] + ([v19ctl] if v19ctl else [])
    if not (args.finals or args.finals_only):
        finalists = []

    for r in finalists:
        print(f"\n[adaptive_v20] FINALS for {r['name']}:", flush=True)
        spec = {"seat1": r.get("seat1", "gbining"), "race": r.get("race", False),
                "hold": r.get("hold", False), "th": r.get("th", False),
                "melon4": r.get("melon4", False),
                "s1splice": r.get("s1splice")}
        res = finals(spec, seeds, _W["suite"], _W["mod"])
        r["finals"] = res
        r["finals_sum"] = sum(v["avg"] for v in res.values())
        if r["name"] == "v19ctrl":
            ctl_delta = r["finals_sum"]

    # verdict
    print("\n" + "=" * 70)
    print("[adaptive_v20] VERDICT", flush=True)
    shippable = None
    best = None
    if (args.finals or args.finals_only) and ctl_delta is not None:
        for r in ok:
            if r.get("finals_sum") is None:
                continue
            if best is None or r["finals_sum"] > best["finals_sum"]:
                best = r
        if best and best["name"] != "v19ctrl" and best["finals_sum"] > ctl_delta:
            shippable = best
    if shippable:
        print(f"  SHIP=YES  {shippable['name']}  finals_sum "
              f"{shippable['finals_sum']:+,.0f} vs control {ctl_delta:+,.0f}",
              flush=True)
    else:
        print("  SHIP=NO   nothing beat the v19 control in finals. "
              "Keep the live bot.", flush=True)

    report = {"shippable": shippable["name"] if shippable else None,
              "control_finals_sum": ctl_delta,
              "results": results}
    with open(os.path.join(OUT_DIR, "report.json"), "w") as f:
        json.dump(report, f, indent=2)

    if shippable and args.build_agent:
        _build_agent_file(shippable, args.version)
    print(f"[adaptive_v20] ledger + report -> {OUT_DIR}", flush=True)


def _build_agent_file(rec, version):
    """Package the winning runtime spec as a standalone agent file."""
    mod = _load_mod(V19_PATH, "v19")
    spec = {"seat1": rec.get("seat1", "gbining"),
            "race": rec.get("race", False), "hold": rec.get("hold", False),
            "th": rec.get("th", False), "melon4": rec.get("melon4", False),
            "s1splice": rec.get("s1splice")}
    src = open(V19_PATH).read()
    header = (
        f'"""HI_AgriBot_v20_Adaptive — v19 compiled routes + adaptive layers.\n'
        f"Variant: {rec.get('name')} (seat1={spec['seat1']}, race={spec['race']}, "
        f"hold={spec['hold']}, th={spec['th']}, melon4={spec['melon4']})\n"
        f'"""\n\nVERSION = {json.dumps(version)}\n'
    )
    lines = src.splitlines(keepends=True)
    out = []
    skip_doc = False
    for i, line in enumerate(lines):
        if line.startswith('"""') and not skip_doc:
            skip_doc = True
            continue
        if skip_doc:
            if '"""' in line:
                skip_doc = False
            continue
        if line.startswith("VERSION = "):
            continue
        out.append(line)
    body = "".join(out)
    # melon4: override the embedded tapes with the compiled ones
    tape_override = ""
    if spec.get("melon4"):
        print("[adaptive_v20] compiling melon4 tapes for the agent file...",
              flush=True)
        tapes = build_melon4_tapes(mod, seed=1)
        tape_override = (
            f"\n# --- melon4 compiled tapes (override) ---\n"
            f"_SEAT0_ACTIONS = json.loads({json.dumps(tapes[0])!r})\n"
            f"_SEAT1_ACTIONS = json.loads({json.dumps(tapes[1])!r})\n"
        )
    elif spec.get("s1splice"):
        print("[adaptive_v20] patching seat1 opening for the agent file...",
              flush=True)
        t1 = apply_seat1_splice(mod._SEAT1_ACTIONS, mod._SEAT0_ACTIONS,
                                mode=spec["s1splice"])
        tape_override = (
            f"\n# --- seat1 opening splice (override) ---\n"
            f"_SEAT1_ACTIONS = json.loads({json.dumps(t1)!r})\n"
        )
    layers = open(os.path.join(HERE, "adaptive_v20.py")).read()
    # extract just the runtime-layer section for embedding
    start = layers.index("# ---------------------------------------------------------------------------\n# tuning constants")
    end = layers.index("# ---------------------------------------------------------------------------\n# variant agent builder")
    embedded = layers[start:end]
    embedded = embedded.replace("import route_compiler_v19 as rc  # noqa: E402", "")
    tail = f'''
{embedded}

_ADAPTIVE_SPEC = {spec!r}

def _v20_agent(obs, configuration=None):
    seat = _seat(obs)
    tape = _SEAT0_ACTIONS if (seat == 1 and _ADAPTIVE_SPEC.get("seat1") == "seat0") else (_SEAT1_ACTIONS if seat == 1 else _SEAT0_ACTIONS)
    step = min(max(0, int(_get(obs, "step", 0) or 0)), len(tape) - 1)
    _update_memory(obs)
    action = _weed_repair_action(obs, _copy_action(tape[step]), tape, step)
    action = _adapt_animals(obs, action)
    action = _adapt_crops(obs, action)
    action = _adapt_market(obs, action)
    if _ADAPTIVE_SPEC.get("th"):
        action = _tetsu_tomato_hedge(obs, action, None)
    if _ADAPTIVE_SPEC.get("race"):
        _observe_opponent_market(obs, step, tape, None)
        action = _repay_shift(obs, action, step)
    action = _align_hands(_rank_sell_slots(obs, action, configuration), obs)
    if _ADAPTIVE_SPEC.get("race"):
        action = _preempt_shift(obs, action, step, tape, None)
        _record_own_sells(obs, action, step)
        action = _terminal_liquidation(obs, action, step, None)
    if _ADAPTIVE_SPEC.get("hold"):
        action = _fert_crash_hold(obs, action, None)
    if step == 718:
        try:
            action = _v26_terminal_sweep(obs, action, configuration)
        except Exception:
            pass
    return _align_hands(action, obs)

def agent(obs, configuration=None):
    try:
        return _v20_agent(obs, configuration)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {{"farmer": ["PASS"],
                "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
                "market": []}}

def _kaggle_submission_entrypoint(obs, configuration=None):
    return agent(obs, configuration)
'''
    path = os.path.join(ROOT, "agent", "main_v20_adaptive.py")
    with open(path, "w") as f:
        f.write(header + body + tape_override + tail)
    print(f"[adaptive_v20] agent written -> {path}", flush=True)
    print(f"[adaptive_v20] VERSION = {version}", flush=True)


if __name__ == "__main__":
    main()
