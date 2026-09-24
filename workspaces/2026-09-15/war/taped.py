#!/usr/bin/env python3
"""taped.py - replays a taped elite route as a local sparring bot.

Usage (as a bot file in watch.py/h2h.py/solo.py):
    python3 solo.py war/taped.py 42            # the tape's solo score
    python3 h2h.py war/astra_live20_8.py war/taped.py 0,1,2

The route file is selected by the TAPED_ROUTE env var (default 0) and
must sit next to this file as elite_route{N}.json. LOCAL SPARRING ONLY
- file I/O, not submittable (and never meant to be: this is the public
Apache-2.0 Seven-Turn-Rescue tape, used to measure the elite gap).
"""
import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
    else "/home/user/war"
_N = os.environ.get("TAPED_ROUTE", "0")
with open(os.path.join(_DIR, f"elite_route{_N}.json")) as _f:
    ROUTE = json.load(_f)


def agent(obs, configuration=None):
    step = int(obs.get("step", 0)) if isinstance(obs, dict) else 0
    # obs may carry step under "step"; fall back to day/hour arithmetic
    if "step" not in obs:
        step = int(obs.get("day", 0)) * 24 + int(obs.get("hour", 0))
    turn = ROUTE[step] if 0 <= step < len(ROUTE) else {}
    a = turn if isinstance(turn, dict) else {}
    farmer = a.get("farmer") or ["PASS"]
    hands = a.get("hands") or []
    market = a.get("market") or []
    # hands: list of action-lists (one per hand, in order)
    return {"farmer": farmer if isinstance(farmer, list) else [farmer],
            "hands": [h if isinstance(h, list) else [h] for h in hands],
            "market": market}


kaggle_entry_agent = agent
