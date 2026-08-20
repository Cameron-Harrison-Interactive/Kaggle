#!/usr/bin/env python3
"""test_v27.py — validation battery for HI_AgriBot_v27_ShopSelector (sequential).

Phase 1: classify seeds 1..24 by trigger state at step 168 (v25-LOW vs idle,
         both seats) + LOW baseline rewards.
Phase 2: on YARN-triggered seeds, A/B the HIGH wool-sell variants vs LOW.
Phase 3: non-YARN zero-diff check + contested spot checks + self-mirror.
"""
import importlib.util
import json
import sys

sys.path.insert(0, "/home/user/kaggriculture/agent")
sys.path.insert(0, "/home/user/kaggriculture/opponents")
from kaggle_environments import make


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V25 = load_mod("/home/user/kaggriculture/agent/main_v25_wheat16.py", "v25m")
V27 = load_mod("/home/user/kaggriculture/agent/main_v27_selector.py", "v27m")
V20 = load_mod("/home/user/kaggriculture/agent/main.py", "v20m")
TETSU = load_mod("/home/user/kaggriculture/opponents/tetsu_main.py", "tetsum")
RAYK = load_mod("/home/user/kaggriculture/opponents/rayk_main.py", "raykm")
KAITO = load_mod("/home/user/kaggriculture/opponents/kaito_main.py", "kaitom")

VARIANTS = ["base", "merge312", "shift311", "shift313", "drop"]


class Idle:
    def __call__(self, obs, configuration=None):
        return {}


def one_game(seed, seat, agent, opponent):
    agents = [Idle(), Idle()]
    agents[seat] = agent
    agents[1 - seat] = opponent
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": seed})
    out = env.run(agents)
    town = (((out[168][seat].get("observation") or {}).get("town") or {})
            .get("unlocked_shops") or [])
    last = out[-1]
    us = last[seat].get("reward")
    them = last[1 - seat].get("reward")
    esc = 0
    prev = {}
    for st in out:
        farm = (st[seat].get("observation") or {}).get("farms") or [{}]
        tiles = (farm[0] if farm else {}).get("tiles") or []
        cur = {}
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                if isinstance(t, dict) and "animal" in t:
                    cur[(x, y)] = t["animal"]
        for pos in prev:
            if pos not in cur:
                esc += 1
        prev = cur
    return us, them, list(town), esc


def main():
    seeds = range(1, 25)
    rows = []
    print("=== Phase 1: classify 24 seeds (v25-LOW vs idle, both seats) ===",
          flush=True)
    for s in seeds:
        for seat in (0, 1):
            us, them, shops, esc = one_game(s, seat, V25.agent, Idle())
            rows.append((s, seat, us, them, shops, esc))
            print(f"  seed {s:2d} seat{seat}: {us:7,.0f} esc={esc} shops={shops}",
                  flush=True)
    yarn_seeds = sorted({r[0] for r in rows if "YARN_STORE" in r[4]})
    nonyarn = sorted({r[0] for r in rows if "YARN_STORE" not in r[4]})
    print(f"YARN seeds: {yarn_seeds}", flush=True)
    print(f"non-YARN: {nonyarn}", flush=True)
    json.dump(rows, open("/home/user/kaggriculture/data/v27_phase1.json", "w"))

    print("\n=== Phase 2: HIGH variants on YARN seeds (both seats) ===",
          flush=True)
    results = {}
    for variant in VARIANTS:
        V27._V27_WOOL_VARIANT = variant
        for s in yarn_seeds:
            for seat in (0, 1):
                us, them, shops, esc = one_game(s, seat, V27.agent, Idle())
                results[(s, seat, variant)] = us
                low = [r[2] for r in rows if r[0] == s and r[1] == seat][0]
                print(f"  {variant:9s} seed {s:2d} seat{seat}: {us:7,.0f} "
                      f"(d {us - low:+8,.0f}) esc={esc}", flush=True)
    json.dump({f"{k[0]}_{k[1]}_{k[2]}": v for k, v in results.items()},
              open("/home/user/kaggriculture/data/v27_phase2.json", "w"))

    print("\n=== Per-variant mean delta vs LOW (YARN seeds, both seats) ===",
          flush=True)
    for variant in VARIANTS:
        deltas = [results[(s, seat, variant)]
                  - [r[2] for r in rows if r[0] == s and r[1] == seat][0]
                  for s in yarn_seeds for seat in (0, 1)]
        print(f"  {variant:9s}: n={len(deltas)} mean={sum(deltas)/len(deltas):+9,.0f} "
              f"deltas={[f'{d:+,.0f}' for d in deltas]}", flush=True)

    # pick the best variant (mean)
    best = max(VARIANTS,
               key=lambda v: sum(results[(s, seat, v)]
                                 - [r[2] for r in rows
                                    if r[0] == s and r[1] == seat][0]
                                 for s in yarn_seeds for seat in (0, 1))
               / (2 * len(yarn_seeds)))
    print(f"\nBEST VARIANT by mean delta: {best}", flush=True)
    V27._V27_WOOL_VARIANT = best

    print("\n=== Phase 3a: non-YARN zero-diff check (must be 0) ===", flush=True)
    zd = 0
    for s in nonyarn[:5]:
        for seat in (0, 1):
            us, them, shops, esc = one_game(s, seat, V27.agent, Idle())
            low = [r[2] for r in rows if r[0] == s and r[1] == seat][0]
            if us != low:
                zd += 1
                print(f"  DIFF seed {s} seat {seat}: v27 {us:,.0f} vs v25 {low:,.0f}",
                      flush=True)
    print(f"  non-YARN diffs: {zd}", flush=True)

    print("\n=== Phase 3b: contested spot checks (YARN seeds) ===", flush=True)
    for s in yarn_seeds[:3]:
        for name, opp in (("v20", V20.agent), ("kaito", KAITO.agent)):
            for seat in (0, 1):
                u27, t27, _, e27 = one_game(s, seat, V27.agent, opp)
                u25, t25, _, e25 = one_game(s, seat, V25.agent, opp)
                d = (u27 - t27) - (u25 - t25)
                print(f"  seed {s} {name:6s} seat{seat}: d27={d:+8,.0f} "
                      f"(v27 {u27:,.0f}/{t27:,.0f} | v25 {u25:,.0f}/{t25:,.0f}) "
                      f"esc={e27}", flush=True)

    print("\n=== Phase 3c: self-mirror (YARN seed) ===", flush=True)
    s = yarn_seeds[0]
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": s})
    out = env.run([V27.agent, V27.agent])
    last = out[-1]
    print(f"  mirror seed {s}: {last[0].get('reward'):,.0f} vs "
          f"{last[1].get('reward'):,.0f}", flush=True)

    print("\ndone", flush=True)


if __name__ == "__main__":
    main()
