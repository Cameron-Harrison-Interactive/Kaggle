#!/usr/bin/env python3
"""weed_deaths2.py -- FIXED crop-death attribution.

The first version of this probe had a real bug: it recorded plant_day the
first time a tile ever held a PLANT and never reset it, so a strawberry
sown on d16 onto a tile that had grown wheat in week 1 was scored as
"age 21" instead of "age 5". That silently hid the exact failure the user
watched happen ("d16 strawberries dead by d21").

This version:
  * resets plant_day whenever a tile stops holding a plant, so AGE is the
    age of the CURRENT plant, not of the tile's first ever crop;
  * uses a HARD, observation-free loss bound instead of relying on
    harvestable_units: a plant that dies before its first-yield day cannot
    possibly have produced anything. first_yield = WHEAT/CARROT 2,
    TOMATO 8, MELON/STRAWBERRY 10. Those are TOTAL LOSSES - seed money,
    the tile for N days, and a dig before it can be replanted.
  * prints, for every dead strawberry, the (planted, died) pair so the
    d16 -> d21 pattern is directly visible.

Usage: python3 war/weed_deaths2.py [bot] [seed ...]
"""
import contextlib
import io
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env  # noqa: E402

# engine-verified first yield days (see war/horizon.py)
FIRST_YIELD = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "MELON": 10,
               "STRAWBERRY": 10}


def run(path_a, path_b, seed):
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])
    return env


def snap(farm):
    cur = {}
    for y, row in enumerate(farm.get("tiles", [])):
        for x, t in enumerate(row):
            if not isinstance(t, dict):
                continue
            kind = t.get("kind")
            if kind == "PLANT":
                cur[(x, y)] = t.get("crop", "?")
            elif kind == "WEED":
                cur[(x, y)] = "WEED"
    return cur


def classify(env):
    """Return counters describing every crop death in one episode."""
    bycrop = Counter()
    lost = Counter()          # died before first yield -> total loss
    ok_age = Counter()        # died at/after first yield
    ages = Counter()
    strb_pairs = Counter()    # (planted, died) for strawberries
    quads = Counter()         # (quadrant, crop) for every death
    lost_quads = Counter()    # (quadrant, crop) for total-loss deaths
    plant_day = {}
    prev = None
    for st in env.steps:
        obs = (st[0] or {}).get("observation") or {}
        if "farms" not in obs:
            continue
        if int(obs.get("hour", -1)) != 23:
            continue
        day = int(obs.get("day", 0))
        cur = snap(obs["farms"][0])

        # 1) DEATH DETECTION FIRST - while plant_day still holds the clock
        #    for the plant that was alive yesterday.
        if prev is not None:
            for k, crop in cur.items():
                if crop != "WEED":
                    continue
                if prev.get(k) in (None, "WEED"):
                    continue          # bare ground or an old weed: SPREAD
                if k not in plant_day:
                    continue
                pd, pcrop = plant_day[k]
                age = day - pd
                bycrop[pcrop] += 1
                ages[age] += 1
                fy = FIRST_YIELD.get(pcrop, 10)
                if age < fy:
                    lost[pcrop] += 1
                else:
                    ok_age[pcrop] += 1
                q = ("N" if k[1] < 5 else "S") + ("W" if k[0] < 5 else "E")
                quads[(q, pcrop)] += 1
                if age < fy:
                    lost_quads[(q, pcrop)] += 1
                if pcrop == "STRAWBERRY":
                    strb_pairs[(pd, day)] += 1
                del plant_day[k]

        # 2) THEN refresh the clock. AGE is the age of the CURRENT plant:
        #    forget any tile that is not currently holding a plant, so a
        #    replant re-starts the clock instead of inheriting the tile's
        #    first-ever crop.
        for k in list(plant_day):
            if cur.get(k) in (None, "WEED"):
                del plant_day[k]
        for k, crop in cur.items():
            if crop == "WEED":
                continue
            if k not in plant_day:
                plant_day[k] = (day, crop)

        prev = cur
    return bycrop, lost, ok_age, ages, strb_pairs, quads, lost_quads


def main():
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_18"
    seeds = [int(x) for x in sys.argv[2:]] or [42]
    ensure_env()
    path = resolve(bot)
    tot = Counter()
    tot_lost = Counter()
    all_ages = Counter()
    all_pairs = Counter()
    all_quads = Counter()
    all_lost_quads = Counter()
    for s in seeds:
        env = run(path, "random", s)
        (bycrop, lost, ok_age, ages, pairs,
         quads, lost_quads) = classify(env)
        tot.update(bycrop)
        tot_lost.update(lost)
        all_ages.update(ages)
        all_pairs.update(pairs)
        all_quads.update(quads)
        all_lost_quads.update(lost_quads)
        n_lost = sum(lost.values())
        print("### seed %-4d deaths=%-3d  TOTAL-LOSS(<first yield)=%-3d  %s"
              % (s, sum(bycrop.values()), n_lost,
                 " ".join("%s:%d" % kv for kv in bycrop.most_common())))
        if n_lost:
            print("        lost: %s"
                  % "  ".join("%s:%d" % kv for kv in lost.most_common()))
    print()
    print("=== %s over %d seeds ===" % (bot, len(seeds)))
    print("  deaths by crop          %s"
          % "  ".join("%s:%d" % kv for kv in tot.most_common()))
    print("  TOTAL LOSS (age<yield)  %d   %s"
          % (sum(tot_lost.values()),
             "  ".join("%s:%d" % kv for kv in tot_lost.most_common())))
    print("  deaths by TRUE age      %s"
          % "  ".join("a%d:%d" % kv for kv in sorted(all_ages.items())))
    print("  ALL deaths by quadrant   %s"
          % "  ".join("%s:%d" % (k[0] + "/" + k[1], v)
                      for k, v in sorted(all_quads.items())))
    print("  TOTAL-LOSS by quadrant   %s"
          % "  ".join("%s:%d" % (k[0] + "/" + k[1], v)
                      for k, v in sorted(all_lost_quads.items())))
    if all_pairs:
        print("  STRAWBERRY (planted->died):")
        for (pd, dd), n in sorted(all_pairs.items()):
            flag = "  <-- NEVER YIELDED (died at age %d)" % (dd - pd) \
                if (dd - pd) < FIRST_YIELD["STRAWBERRY"] else ""
            print("      planted d%-3d died d%-3d  age %-3d x%d%s"
                  % (pd, dd, dd - pd, n, flag))


if __name__ == "__main__":
    main()
