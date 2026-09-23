#!/usr/bin/env python3
"""labor_probe.py - where do the worker-hours actually go?

Runs a bot vs passbot and decomposes every unit-hour into:
  MOVE / PASS / productive op / shed logistics / market (farmer only)
plus per-day coverage telemetry (care, fert-collect, water deaths, weeds).

Usage: python3 war/labor_probe.py [bot] [seed ...]
"""
import io
import contextlib
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env  # noqa: E402


OPS = ("WATER", "HARVEST", "PLANT", "DIG", "FERTILIZE", "FEED", "CARE",
       "COLLECT_FERTILIZER", "BUILD_COOP", "BUILD_PASTURE", "PLACE",
       "PICKUP", "DROP")
TILE_OPS = ("WATER", "HARVEST", "PLANT", "DIG", "FERTILIZE", "FEED", "CARE",
            "COLLECT_FERTILIZER")


def run(path_a, path_b, seed):
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])
    return env


def analyse(env, verbose=True):
    steps = env.steps
    # unit trails: index -> list of (day, hour, pos)
    trails = defaultdict(list)
    cat = Counter()                     # global action category counts
    opcount = Counter()                 # productive op counts
    per_day = defaultdict(Counter)      # day -> counter
    # coverage
    care_done = Counter()               # day -> cares executed
    fert_avail = Counter()              # day -> animals with fert flag at h0
    fert_done = Counter()
    water_deaths = Counter()
    prev_weeds = Counter()

    last_day = -1
    day_h0 = {}
    for st in steps:
        obs = (st[0] or {}).get("observation") or {}
        if "farms" not in obs:
            continue
        day = int(obs.get("day", 0))
        hour = int(obs.get("hour", 0))
        act = (st[0] or {}).get("action") or {}
        farm = obs["farms"][0]
        tiles = farm.get("tiles", [])
        # grid of tiles
        grid = {}
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                grid[(x, y)] = t
        if hour == 0:
            day_h0[day] = grid
            fert_avail[day] = sum(
                1 for t in grid.values()
                if isinstance(t, dict) and t.get("animal")
                and t.get("fertilizer_available"))
            prev_weeds[day] = sum(
                1 for t in grid.values()
                if isinstance(t, dict) and t.get("kind") == "WEED")

        units = []
        fa = act.get("farmer")
        if isinstance(fa, list):
            units.append(fa)
        for h in (act.get("hands") or []):
            units.append(h)
        for ui, u in enumerate(units):
            op = u[0] if u else "PASS"
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                cat["MOVE"] += 1
                per_day[day]["MOVE"] += 1
            elif op == "PASS":
                cat["PASS"] += 1
                per_day[day]["PASS"] += 1
            elif op in ("PICKUP", "DROP"):
                cat["SHED"] += 1
                per_day[day]["SHED"] += 1
                opcount[op] += 1
            elif op in TILE_OPS:
                cat["OP"] += 1
                per_day[day]["OP"] += 1
                opcount[op] += 1
                if op == "CARE":
                    care_done[day] += 1
                if op == "COLLECT_FERTILIZER":
                    fert_done[day] += 1
            elif op in ("BUILD_COOP", "BUILD_PASTURE", "PLACE", "BUY_ANIMAL"):
                cat["OP"] += 1
                per_day[day]["OP"] += 1
                opcount[op] += 1
            else:
                cat["OTHER:" + str(op)] += 1
                per_day[day]["OTHER"] += 1
        per_day[day]["NUNITS"] = len(units)
        last_day = day

    # deaths: weed count increase per day (proxy)
    days = sorted(day_h0)
    for i, d in enumerate(days):
        if d + 1 in prev_weeds:
            delta = prev_weeds[d + 1] - prev_weeds[d]
            if delta > 0:
                water_deaths[d + 1] += delta

    if verbose:
        tot = sum(cat.values())
        print("=" * 62)
        print("LABOR DECOMPOSITION (player 0, all unit-hours)")
        print("=" * 62)
        for k in ("OP", "MOVE", "PASS", "SHED", "OTHER"):
            v = cat.get(k, 0)
            print("  %-6s %7d  %5.1f%%" % (k, v, 100.0 * v / max(1, tot)))
        print("  %-6s %7d" % ("TOTAL", tot))
        print()
        print("OPS BY TYPE")
        for k, v in opcount.most_common():
            print("  %-22s %6d" % (k, v))
        print()
        print("PER-DAY (units / OP / MOVE / PASS / SHED)")
        print("  day  n  op  move pass shed | care fertA fertD")
        for d in days:
            c = per_day[d]
            print("  %3d %3d %4d %5d %4d %4d | %4d %5d %5d" % (
                d, c["NUNITS"], c["OP"], c["MOVE"], c["PASS"], c["SHED"],
                care_done[d], fert_avail[d], fert_done[d]))
    return dict(cat=cat, ops=opcount, per_day=per_day,
                care=care_done, fert_avail=fert_avail, fert_done=fert_done,
                deaths=water_deaths)


def main():
    ensure_env()
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_10"
    seeds = [int(s) for s in sys.argv[2:]] or [42]
    pa = resolve(bot)
    pb = resolve("pass")
    agg = Counter()
    for s in seeds:
        env = run(pa, pb, s)
        r = analyse(env)
        print("\nseed %d final: $%s" % (s, env.state[0].reward))
        agg.update(r["cat"])
    if len(seeds) > 1:
        print("\nAGGREGATE over %d seeds" % len(seeds))
        tot = sum(agg.values())
        for k in ("OP", "MOVE", "PASS", "SHED", "OTHER"):
            print("  %-6s %7d  %5.1f%%" % (k, agg.get(k, 0),
                                           100.0 * agg.get(k, 0) / max(1, tot)))


if __name__ == "__main__":
    main()
