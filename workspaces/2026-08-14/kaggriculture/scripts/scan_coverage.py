#!/usr/bin/env python3
"""Coverage scanner: replay v18 vs PASS and find where the tape has idle
PASS steps near empty tiles (potential plant slots) and dry crops
(potential water slots), so the route optimizer knows what to patch.

Usage: python3 scripts/scan_coverage.py --seed 1 [--seat 0]
"""
import argparse
import importlib.util
import json
import os
from collections import defaultdict

from kaggle_environments import make

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_v18(path):
    spec = importlib.util.spec_from_file_location("v18", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._weed_repair_action = lambda obs, action, actions, step: action
    return mod


def scan(seed, seat):
    mod = load_v18(os.path.join(ROOT, "submit", "main.py"))
    pass_agent = lambda obs, c: {"market": [], "farmer": ["PASS"],
                                 "hands": [["PASS"]] * len(obs["farms"][obs["player"]].get("hands") or [])}
    tape = []
    day_events = defaultdict(lambda: {"pass_on_empty": 0, "pass_on_dry": 0,
                                      "water": 0, "plant": 0, "harvest": 0,
                                      "dry_at_dayend": 0, "empty_at_dayend": 0})

    def rec(obs, config):
        step = int(obs.get("step", 0) or 0)
        day = int(obs.get("day", 0) or 0)
        act = mod.agent(obs, config)
        farm = obs["farms"][seat if seat is not None else obs["player"]]
        tiles = farm.get("tiles") or []
        # count idle-on-empty / idle-on-dry actions this turn
        positions = [farm.get("farmer"), *list(farm.get("hands") or [])]
        unit_actions = [act.get("farmer"), *list(act.get("hands") or [])]
        for pos, ua in zip(positions, unit_actions):
            if not ua:
                continue
            op = ua[0] if isinstance(ua, list) else ua
            if op != "PASS":
                continue
            try:
                x, y = int(pos[0]), int(pos[1])
                tile = tiles[y][x]
            except Exception:
                continue
            if tile is None:
                day_events[day]["pass_on_empty"] += 1
            elif isinstance(tile, dict) and tile.get("kind") == "PLANT":
                if not tile.get("watered_today") and tile.get("consecutive_unwatered", 0) >= 1:
                    day_events[day]["pass_on_dry"] += 1
        for k in ("farmer", "hands"):
            for a in (act.get(k) or []):
                if isinstance(a, list) and a:
                    if a[0] in ("WATER", "PLANT", "HARVEST"):
                        day_events[day][a[0].lower()] += 1
        # end-of-day counts
        if obs.get("hour") == 23:
            dry = empty = 0
            for row in tiles:
                for t in row:
                    if t is None:
                        empty += 1
                    elif isinstance(t, dict) and t.get("kind") == "PLANT":
                        if not t.get("watered_today") and t.get("consecutive_unwatered", 0) >= 1:
                            dry += 1
            day_events[day]["dry_at_dayend"] = dry
            day_events[day]["empty_at_dayend"] = empty
        tape.append({"market": [list(o) for o in (act.get("market") or [])],
                     "farmer": list(act.get("farmer") or ["PASS"]),
                     "hands": [list(h) for h in (act.get("hands") or [])]})
        return act

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    if seat == 0:
        env.run([rec, pass_agent])
    else:
        env.run([pass_agent, rec])

    print(f"=== coverage scan seed {seed} seat {seat} (vs PASS) ===")
    print(f"{'day':>3} {'passEmpty':>9} {'passDry':>7} {'WATER':>5} {'PLANT':>5} {'HARV':>5} {'dryEOD':>6} {'emptyEOD':>8}")
    for d in sorted(day_events):
        e = day_events[d]
        print(f"{d:>3} {e['pass_on_empty']:>9} {e['pass_on_dry']:>7} {e['water']:>5} {e['plant']:>5} {e['harvest']:>5} {e['dry_at_dayend']:>6} {e['empty_at_dayend']:>8}")
    return tape


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--seat", type=int, default=0)
    args = ap.parse_args()
    scan(args.seed, args.seat)
