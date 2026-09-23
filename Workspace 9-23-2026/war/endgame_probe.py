#!/usr/bin/env python3
"""endgame_probe.py - what is still sitting on the farm at the final whistle.

Score = farm money at step 719. Anything in the shed, in a worker's pocket or
in the seed pouch at the horn is $0. This prints the last week day by day
(buys vs plants vs standing vs weeds) and then the exact final contents.

Usage: python3 war/endgame_probe.py [bot] [seed ...]
"""
import io
import contextlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env  # noqa: E402

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")


def run(path_a, path_b, seed):
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])
    return env


def analyse(env, seed, verbose=True):
    steps = env.steps
    obs_by_step = []
    for st in steps:
        obs = (st[0] or {}).get("observation") or {}
        if "farms" in obs:
            obs_by_step.append(obs)
    last = obs_by_step[-1]
    prev_seed_pouch = None
    rows = []
    for obs in obs_by_step:
        day = int(obs.get("day", 0))
        hour = int(obs.get("hour", 0))
        if hour != 23:
            continue
        priv = obs.get("private") or {}
        pouch = priv.get("seeds") or {}
        shed = priv.get("shed") or {}
        farm = obs["farms"][0]
        grid = {}
        for y, row in enumerate(farm.get("tiles", [])):
            for x, t in enumerate(row):
                grid[(x, y)] = t
        plants = sum(1 for t in grid.values()
                     if isinstance(t, dict) and t.get("kind") == "PLANT")
        weeds = sum(1 for t in grid.values()
                    if isinstance(t, dict) and t.get("kind") == "WEED")
        rows.append({
            "day": day, "pouch": dict(pouch), "shed": dict(shed),
            "plants": plants, "weeds": weeds,
            "money": float(farm.get("money", 0)),
        })

    if verbose:
        print("\n### seed %d  final $%s" % (seed, env.state[0].reward))
        print("  LAST WEEK, at h23 (end of day):")
        print("  %4s %6s %6s %7s  %-34s %s"
              % ("day", "plants", "weeds", "money", "seed pouch", "shed (non-zero)"))
        for r in rows[-8:]:
            pouch = {k: int(v) for k, v in r["pouch"].items() if int(v or 0) > 0}
            shed = {k: int(v) for k, v in r["shed"].items() if int(v or 0) > 0}
            print("  %4d %6d %6d %7.0f  %-34s %s"
                  % (r["day"], r["plants"], r["weeds"], r["money"],
                     pouch or "-", shed or "-"))

        priv = last.get("private") or {}
        print("\n  AT THE FINAL WHISTLE (d%s h%s):"
              % (last.get("day"), last.get("hour")))
        pouch = {k: int(v) for k, v in (priv.get("seeds") or {}).items()
                 if int(v or 0) > 0}
        shed = {k: int(v) for k, v in (priv.get("shed") or {}).items()
                if int(v or 0) > 0}
        invs = priv.get("inventories") or []
        carried = {}
        for inv in invs:
            for k, v in (inv or {}).items():
                if int(v or 0) > 0:
                    carried[k] = carried.get(k, 0) + int(v)
        seed_cost = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50,
                     "STRAWBERRY": 100, "MELON": 80}
        anim_cost = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
        base_px = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
                   "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200,
                   "FERTILIZER": 100}
        print("    seed pouch : %s" % (pouch or "-"))
        print("    shed       : %s" % (shed or "-"))
        print("    on workers : %s" % (carried or "-"))
        wasted = sum(seed_cost.get(k, 0) * v for k, v in pouch.items())
        wasted += sum(anim_cost.get(k, 0) * v
                      for k, v in list(shed.items()) + list(carried.items())
                      if k in anim_cost)
        wasted += sum(base_px.get(k, 0) * v
                      for k, v in list(shed.items()) + list(carried.items())
                      if k in base_px)
        print("    >>> CASH BURNED ON UNSOLD/UNPLANTED STOCK: ~$%d" % wasted)
    return rows


def main():
    ensure_env()
    bot = sys.argv[1] if len(sys.argv) > 1 else "submit/v30_champion.py"
    seeds = [int(s) for s in sys.argv[2:]] or [42]
    pa, pb = resolve(bot), resolve("pass")
    for s in seeds:
        analyse(run(pa, pb, s), s)


if __name__ == "__main__":
    main()
