#!/usr/bin/env python3
"""nw_census.py - NW-quad care / water / fert / bonus capture.

Usage: python3 war/nw_census.py [bot] [seed ...]
"""
import io
import contextlib
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env  # noqa: E402

ANIMALS = {
    "GOOSE": ("EGG", 4, 1, 4),
    "COW": ("MILK", 8, 2, 6),
    "SHEEP": ("WOOL", 6, 3, 6),
}


def quad(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


def run(path_a, path_b, seed):
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])
    return env


def analyse(env):
    steps = env.steps
    # day -> hour-23 snapshot of NW
    eod = {}
    ops = defaultdict(Counter)          # day -> op counts on NW tiles
    ops_all = Counter()
    care_eod = defaultdict(lambda: [0, 0])   # day -> [cared, total]
    feed_eod = defaultdict(lambda: [0, 0])
    bonus_eod = defaultdict(list)            # pending_care_bonus values
    water_eod = defaultdict(lambda: [0, 0])  # watered, plants
    fert_eod = defaultdict(lambda: [0, 0])   # fertilized plants, plants
    herd_eod = defaultdict(Counter)
    crops_eod = defaultdict(Counter)
    weeds_eod = Counter()
    dirt_eod = Counter()
    missed_water_dying = Counter()
    # animal production-day bonus capture
    bonus_on_prod = [0, 0]  # captured, possible
    # positions of units at each step to attribute ops to tiles
    last_pos = {}

    for st in steps:
        obs = (st[0] or {}).get("observation") or {}
        if "farms" not in obs:
            continue
        day = int(obs.get("day", 0))
        hour = int(obs.get("hour", 0))
        act = (st[0] or {}).get("action") or {}
        farm = obs["farms"][0]
        tiles = farm.get("tiles", [])
        farmer = tuple(farm.get("farmer") or (4, 4))
        hands = [tuple(p) for p in (farm.get("hands") or [])]
        units_pos = [farmer] + hands

        fa = act.get("farmer")
        unit_acts = []
        if isinstance(fa, list):
            unit_acts.append(fa)
        for h in (act.get("hands") or []):
            unit_acts.append(h)

        for ui, u in enumerate(unit_acts):
            op = u[0] if u else "PASS"
            pos = units_pos[ui] if ui < len(units_pos) else None
            if pos is None:
                continue
            if op in ("NORTH", "SOUTH", "EAST", "WEST", "PASS",
                      "PICKUP", "DROP"):
                continue
            if quad(pos[0], pos[1]) == "NW":
                ops[day][op] += 1
                ops_all[op] += 1

        if hour != 23:
            continue

        nw_an, nw_pl, nw_weed, nw_dirt = 0, 0, 0, 0
        cared = fed = 0
        watered = fertp = 0
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                if quad(x, y) != "NW":
                    continue
                if t is None:
                    nw_dirt += 1
                    continue
                if not isinstance(t, dict):
                    continue
                if t.get("kind") == "WEED":
                    nw_weed += 1
                    continue
                if t.get("kind") == "PLANT":
                    nw_pl += 1
                    crops_eod[day][t.get("crop")] += 1
                    if t.get("watered_today"):
                        watered += 1
                    if int(t.get("fertilized_until_day", -1)) >= day:
                        fertp += 1
                    if int(t.get("consecutive_unwatered", 0)) >= 1:
                        missed_water_dying[day] += 1
                elif t.get("animal"):
                    nw_an += 1
                    kind = t["animal"]
                    herd_eod[day][kind] += 1
                    if t.get("cared_today"):
                        cared += 1
                    if t.get("fed_today"):
                        fed += 1
                    bonus_eod[day].append(int(t.get("pending_care_bonus", 0) or 0))
                    # production day? next_day - placed - first % interval == 0
                    # at h23, daily refresh has NOT run yet (EOD is after h23)
                    # so pending_care_bonus here is yesterday's leftover;
                    # cared_today/fed_today are TODAY's flags about to convert.
                    prod, first, interval, cap = ANIMALS[kind][0], ANIMALS[kind][1], ANIMALS[kind][2], ANIMALS[kind][3]
                    placed = int(t.get("placed_day", 0))
                    next_day = day + 1
                    dsf = next_day - placed - first
                    if dsf >= 0 and dsf % interval == 0:
                        # tonight's refresh will consume pending (if fed) then
                        # add 1 if cared+fed today
                        bonus_on_prod[1] += 1
                        if t.get("fed_today") and int(t.get("pending_care_bonus", 0) or 0) > 0:
                            bonus_on_prod[0] += 1

        care_eod[day] = [cared, nw_an]
        feed_eod[day] = [fed, nw_an]
        water_eod[day] = [watered, nw_pl]
        fert_eod[day] = [fertp, nw_pl]
        weeds_eod[day] = nw_weed
        dirt_eod[day] = nw_dirt
        eod[day] = dict(an=nw_an, pl=nw_pl, weed=nw_weed, dirt=nw_dirt)

    return dict(eod=eod, ops=ops, ops_all=ops_all, care=care_eod,
                feed=feed_eod, bonus=bonus_eod, water=water_eod,
                fert=fert_eod, herd=herd_eod, crops=crops_eod,
                weeds=weeds_eod, dirt=dirt_eod, dying=missed_water_dying,
                bonus_on_prod=bonus_on_prod,
                reward=float(env.state[0].reward))


def report(r, seed):
    print("=" * 72)
    print("NW CENSUS  seed %d  final $%.0f" % (seed, r["reward"]))
    print("=" * 72)
    print("  day  an  fed  care  |  pl  wat fert dying weed dirt | herd            crops")
    days = sorted(r["eod"])
    tot_an = tot_fed = tot_care = 0
    tot_pl = tot_wat = tot_fert = 0
    for d in days:
        c, n = r["care"][d]
        f, _ = r["feed"][d]
        w, p = r["water"][d]
        ft, _ = r["fert"][d]
        tot_an += n
        tot_fed += f
        tot_care += c
        tot_pl += p
        tot_wat += w
        tot_fert += ft
        herd = "".join("%s%d" % (k[0], v) for k, v in sorted(r["herd"][d].items())) or "-"
        crops = "".join("%s%d" % (k[0], v) for k, v in sorted(r["crops"][d].items())) or "-"
        print("  %3d %3d %4d %5d  | %3d %4d %4d %5d %4d %4d | %-15s %s" % (
            d, n, f, c, p, w, ft, r["dying"][d], r["weeds"][d], r["dirt"][d],
            herd, crops))
    print()
    print("  CARE coverage:  %d / %d animal-days  %.1f%%" % (
        tot_care, tot_an, 100.0 * tot_care / max(1, tot_an)))
    print("  FEED coverage:  %d / %d animal-days  %.1f%%" % (
        tot_fed, tot_an, 100.0 * tot_fed / max(1, tot_an)))
    print("  WATER coverage: %d / %d plant-days   %.1f%%  (watered_today at h23)" % (
        tot_wat, tot_pl, 100.0 * tot_wat / max(1, tot_pl)))
    print("  FERT standing:  %d / %d plant-days   %.1f%%" % (
        tot_fert, tot_pl, 100.0 * tot_fert / max(1, tot_pl)))
    cap, poss = r["bonus_on_prod"]
    print("  CARE BONUS on production days: %d / %d  %.1f%%  (fed AND pending>0 at h23)" % (
        cap, poss, 100.0 * cap / max(1, poss)))
    print()
    print("  NW TILE OPS (season)")
    for k, v in r["ops_all"].most_common():
        print("    %-22s %5d" % (k, v))
    print()
    # pending bonus histogram
    hist = Counter()
    for d, vals in r["bonus"].items():
        for v in vals:
            hist[v] += 1
    print("  pending_care_bonus histogram (h23, all NW animals all days):")
    for k in sorted(hist):
        print("    bonus=%d  %4d" % (k, hist[k]))


def main():
    ensure_env()
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_18"
    seeds = [int(s) for s in sys.argv[2:]] or [42]
    pa = resolve(bot)
    pb = resolve("pass")
    for s in seeds:
        env = run(pa, pb, s)
        r = analyse(env)
        report(r, s)


if __name__ == "__main__":
    main()
