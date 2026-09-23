#!/usr/bin/env python3
"""weed_deaths.py -- WHY do crops turn into weeds?

The user watched v30 episodes and saw crops converting to weeds. There are
two completely different mechanisms and they need OPPOSITE fixes:

  DEATH  : PLANT tile -> WEED tile
           (consecutive_unwatered hit the crop's limit -> a care failure)
           Fix = water more, or harvest before it dies.
  SPREAD : empty/harvested tile -> WEED tile
           (random weed growth on bare ground - NOT a care failure)
           Fix = replant faster.

So we walk every tile at h23 each day and classify each transition instead
of guessing. Also reports whether a dead tile was carrying ripe units at
the time ('ripe deaths' = we failed to pick a harvestable crop - the worst
kind, that is pure lost revenue).

Usage: python3 war/weed_deaths.py [bot] [seed ...]   (default live20_18 42)
"""
import contextlib
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env  # noqa: E402


def run(path_a, path_b, seed):
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])
    return env


def classify(env):
    """Return (deaths_by_day, ripe_deaths_by_day, spread_by_day, harv_by_day)."""
    from collections import Counter
    deaths, ripe, spread, harv = {}, {}, {}, {}
    bycrop = Counter()
    age_at_death = Counter()
    produced = Counter()
    plantings = Counter()
    for d in range(30):
        deaths[d] = 0
        ripe[d] = 0
        spread[d] = 0
        harv[d] = 0
    prev = None
    plant_day = {}
    for st in env.steps:
        obs = (st[0] or {}).get("observation") or {}
        if "farms" not in obs:
            continue
        if int(obs.get("hour", -1)) != 23:
            continue
        day = int(obs.get("day", 0))
        farm = obs["farms"][0]
        cur = {}
        for y, row in enumerate(farm.get("tiles", [])):
            for x, t in enumerate(row):
                if not isinstance(t, dict):
                    cur[(x, y)] = ("EMPTY", 0, 0, "")
                    continue
                kind = t.get("kind")
                if kind == "PLANT":
                    cur[(x, y)] = ("PLANT",
                                   int(t.get("harvestable_units", 0) or 0),
                                   int(t.get("consecutive_unwatered", 0) or 0),
                                   t.get("crop", "?"))
                elif kind == "WEED":
                    cur[(x, y)] = ("WEED", 0, 0, "")
                else:
                    cur[(x, y)] = ("EMPTY", 0, 0, "")
        for k, (kind, un, cuw, crop) in cur.items():
            if kind == "PLANT" and k not in plant_day:
                plant_day[k] = day
        if prev is not None:
            for k, (kind, un, cuw, crop) in cur.items():
                if k not in prev:
                    continue
                pk, pun, pcuw, pcrop = prev[k]
                if pk != "PLANT" and kind == "PLANT":
                    plantings[crop] += 1
                if kind == "PLANT" and pk == "PLANT" and un > pun:
                    produced[crop] += (un - pun)
                if pk == kind:
                    continue
                if pk == "PLANT" and kind == "WEED":
                    deaths[day] += 1
                    bycrop[pcrop] += 1
                    age_at_death[min(29, day - plant_day.get(k, day))] += 1
                    if pun > 0:
                        ripe[day] += 1
                elif pk == "PLANT" and kind == "EMPTY":
                    harv[day] += 1
                elif pk == "EMPTY" and kind == "WEED":
                    spread[day] += 1
        prev = cur
    return deaths, ripe, spread, harv, bycrop, age_at_death, produced, plantings


def compact(d):
    return " ".join("d%d:%d" % (k, v) for k, v in sorted(d.items()) if v)


def main():
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_18"
    seeds = [int(x) for x in sys.argv[2:]] or [42]
    ensure_env()
    a = resolve(bot)
    for s in seeds:
        env = run(a, "random", s)
        (deaths, ripe, spread, harv, bycrop, age,
         produced, plantings) = classify(env)
        last = None
        for st in reversed(env.steps):
            obs = (st[0] or {}).get("observation") or {}
            if "farms" in obs:
                last = obs
                break
        money = float(last["farms"][0].get("money", 0)) if last else 0.0
        print("### seed %d -- %s   final $%s" % (s, bot, int(money)))
        print("   DEATHS  (PLANT->WEED)   total=%-4d  %s"
              % (sum(deaths.values()), compact(deaths)))
        print("     of which RIPE         total=%-4d  %s"
              % (sum(ripe.values()), compact(ripe)))
        print("   SPREAD  (bare->WEED)    total=%-4d  %s"
              % (sum(spread.values()), compact(spread)))
        print("   HARVEST (PLANT->bare)   total=%-4d  %s"
              % (sum(harv.values()), compact(harv)))
        print("   DEATHS BY CROP          %s"
              % "  ".join("%s:%d" % kv for kv in bycrop.most_common()))
        print("   DEATHS BY PLANT AGE     %s"
              % "  ".join("age%d:%d" % (k, v)
                          for k, v in sorted(age.items())))
        print("   YIELD: units set / plantings  (max 4 for STRB/MELON/TOMATO)")
        for c in sorted(plantings):
            n = plantings[c]
            u = produced.get(c, 0)
            print("      %-11s planted=%-4d units=%-5d  %.2f units/planting"
                  % (c, n, u, u / max(1, n)))
        print()


if __name__ == "__main__":
    main()
