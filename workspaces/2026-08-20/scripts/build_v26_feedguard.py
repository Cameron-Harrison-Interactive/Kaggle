#!/usr/bin/env python3
"""build_v26_feedguard.py — v25 Wheat16 + two hole fixes learned from the v24 live losses.

Fix A (opening clamp immunity — the "one missing seed" root cause):
  d0h0 queue tail: [..., BUY_SEED MELON 5, BUY_SEED WHEAT 5]
                -> [..., BUY_SEED WHEAT 6, BUY_SEED MELON 5]
  Wheat seeds now land BEFORE melon seeds and have +1 slack, so a first-mover
  opponent who inflates our d0h0 wheat-product buy can no longer clamp our
  wheat seed purchase -> the 5th wheat PLANT always lands -> no missing tile.

Fix B (feed-reserve guard — the cow-escape hole):
  Runtime layer: on days <= 13, if shed wheat <= current animal count, drop
  SELL WHEAT orders entirely (the shed is the feed buffer; FEED pulls from
  shed-adjacent PICKUPs). Healthy games are untouched (shed >> animals);
  crunch games keep feed wheat instead of selling it for ~60 coins, saving
  cows worth 400 each + milk income.

Output: agent/main_v26_feedguard.py, VERSION = HI_AgriBot_v26_FeedGuard.
"""
import base64
import json
import re
import zlib

SRC = "/home/user/kaggriculture/agent/main_v25_wheat16.py"
OUT = "/home/user/kaggriculture/agent/main_v26_feedguard.py"

src = open(SRC).read()

# ---------------------------------------------------------------------------
# Fix A: edit step 0 of the tape (both the b85 blob and the fallback literal)
# ---------------------------------------------------------------------------
old_orders = [["BUY_SEED", "MELON", 5], ["BUY_SEED", "WHEAT", 5]]
new_orders = [["BUY_SEED", "WHEAT", 6], ["BUY_SEED", "MELON", 5]]

# 1) b85 blob at module level (lines ~16-141)
m = re.search(r"base64\.b85decode\(\n(.*?)\n\s*\)\)\)", src, re.S)
if not m:
    raise SystemExit("b85 tape blob not found")
b85 = "".join(re.findall(r"'([^']*)'", m.group(1)))
tape = json.loads(zlib.decompress(base64.b85decode(b85)))
step0 = tape[0]["market"]
assert old_orders[0] in step0 and old_orders[1] in step0, f"unexpected d0 orders: {step0}"
step0.remove(old_orders[0]); step0.remove(old_orders[1])
step0.extend(new_orders)
new_b85 = base64.b85encode(zlib.compress(json.dumps(tape).encode())).decode()
src = src.replace(m.group(1), "\n(\n" + "\n".join(
    "    '%s'" % new_b85[i:i+100] for i in range(0, len(new_b85), 100)) + "\n")

# 2) fallback literal (the operative reassignment near the end)
old_lit = r'"market": [["BUY_PRODUCT", "WHEAT", 16], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_ANIMAL", "COW", 1], ["BUY_ANIMAL", "SHEEP", 4], ["BUY_SEED", "MELON", 5], ["BUY_SEED", "WHEAT", 5]]'
new_lit = r'"market": [["BUY_PRODUCT", "WHEAT", 16], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_ANIMAL", "COW", 1], ["BUY_ANIMAL", "SHEEP", 4], ["BUY_SEED", "WHEAT", 6], ["BUY_SEED", "MELON", 5]]'
assert src.count(old_lit) == 1, f"fallback literal count = {src.count(old_lit)}"
src = src.replace(old_lit, new_lit)

# ---------------------------------------------------------------------------
# Fix B: feed-reserve guard layer
# ---------------------------------------------------------------------------
guard_fn = '''

# ---------------------------------------------------------------------------
# FeedReserve — v26: never sell the feed buffer (cow-escape hole fix).
# The shed is the feed buffer: FEED pulls wheat via shed-adjacent PICKUPs.
# On days <= 13, if shed wheat is at/below the animal count, drop SELL WHEAT
# orders (the ~60-120 coins forgone beats 4 escaped cows worth 400+ each).
# Healthy games are byte-identical (shed wheat >> animals).
# ---------------------------------------------------------------------------
_FEED_RESERVE_LAST_DAY = 13


def _count_live_animals(obs, seat):
    try:
        farm = _farm(obs, seat)
        tiles = _get(farm, "tiles", []) or []
        n = 0
        for row in tiles:
            for t in row:
                if isinstance(t, dict) and "animal" in t:
                    n += 1
        shed = _get(_get(obs, "private", {}) or {}, "shed", {}) or {}
        for kind in ("COW", "SHEEP", "GOOSE"):
            n += int(_get(shed, kind, 0) or 0)
        return n
    except Exception:
        return 0


def _feed_reserve(obs, action):
    try:
        day = int(_get(obs, "day",
                       int(_get(obs, "step", 0) or 0) // 24) or 0)
        if day > _FEED_RESERVE_LAST_DAY:
            return action
        n_anim = _count_live_animals(obs, _seat(obs))
        if n_anim <= 0:
            return action
        shed = _get(_get(obs, "private", {}) or {}, "shed", {}) or {}
        shed_w = int(_get(shed, "WHEAT", 0) or 0)
        if shed_w > n_anim:
            return action
        market = list(action.get("market") or [])
        if not any(o and o[0] == "SELL" and o[1] == "WHEAT" for o in market):
            return action
        action = dict(action)
        action["market"] = [
            o for o in market
            if not (o and o[0] == "SELL" and o[1] == "WHEAT")
        ]
        return action
    except Exception:
        return action
'''

anchor = '_BRAIN = {"labor": True, "cashrank": True}'
assert src.count(anchor) == 1
src = src.replace(anchor, guard_fn + "\n\n" + anchor)

# wire into the pipeline: after cashrank, before labor
old_pipe = '''        if _BRAIN.get("cashrank"):
            action = _cash_rank(obs, action)
        if _BRAIN.get("labor"):'''
new_pipe = '''        if _BRAIN.get("cashrank"):
            action = _cash_rank(obs, action)
        action = _feed_reserve(obs, action)
        if _BRAIN.get("labor"):'''
assert src.count(old_pipe) == 1
src = src.replace(old_pipe, new_pipe)

# ---------------------------------------------------------------------------
# Version + fresh tail callable (loader-safe)
# ---------------------------------------------------------------------------
src = src.replace("HI_AgriBot_v25_Wheat16", "HI_AgriBot_v26_FeedGuard")
src = src.replace("_v25_agent = agent", "_v26_agent = agent")

open(OUT, "w").write(src)
print("wrote", OUT, len(src), "chars")
