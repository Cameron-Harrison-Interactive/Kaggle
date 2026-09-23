#!/usr/bin/env python3
"""gate.py - solo gate runner over the canonical seed set.

Usage: python3 war/gate.py <bot> [seed ...]
       python3 war/gate.py live20_10 live20_12     (compare side by side)
"""
import io
import contextlib
import os
import sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

GATE = [42, 5, 101, 202, 303, 777]
BASE = {42: 94426, 5: 97952, 101: 101359, 202: 95515, 303: 108729,
        777: 89381}


def _one(args):
    path_a, path_b, seed = args
    import importlib
    watch = importlib.import_module("watch")
    env = watch.run_match.__wrapped__ if False else None
    import kaggle_environments as ke
    env = ke.make(watch.env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])
    return seed, float(env.state[0].reward)


def resolve(spec):
    from watch import resolve as _r
    return _r(spec)


def run_bot(bot, seeds, workers=2):
    pa = resolve(bot)
    pb = resolve("pass")
    jobs = [(pa, pb, s) for s in seeds]
    out = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for seed, val in ex.map(_one, jobs):
            out[seed] = val
    return out


def main():
    from watch import ensure_env
    ensure_env()
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    seeds = GATE
    bots = []
    for a in args:
        if a.isdigit():
            continue
        bots.append(a)
    nums = [int(a) for a in args if a.isdigit()]
    if nums:
        seeds = nums
    results = {}
    for b in bots:
        results[b] = run_bot(b, seeds)
    hdr = "  %-16s" % "bot" + "".join("%9s" % ("s%d" % s) for s in seeds) + "%11s" % "AVG"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for b in bots:
        r = results[b]
        vals = [r[s] for s in seeds]
        avg = sum(vals) / len(vals)
        line = "  %-16s" % b + "".join("%9.0f" % v for v in vals) + "%11.0f" % avg
        if len(bots) > 1:
            d = avg - sum(results[bots[0]][s] for s in seeds) / len(seeds)
            if b != bots[0]:
                line += "   %+8.0f" % d
        print(line)
    if len(bots) > 1 and set(seeds) == set(GATE):
        print("\n  delta vs %s (baseline v29):" % bots[0])
        for b in bots[1:]:
            for s in seeds:
                print("    s%-5d %+8.0f" % (s, results[b][s] - results[bots[0]][s]))


if __name__ == "__main__":
    main()
