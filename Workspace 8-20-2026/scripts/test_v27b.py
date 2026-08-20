#!/usr/bin/env python3
"""test_v27b.py — trimmed decision battery for v27 (mp.Pool(2), JSONL save).

A. Variant sweep: YARN seeds {6, 8, 19} x both seats x 5 variants vs LOW.
B. Zero-diff check: non-YARN seeds {1, 2, 9} x both seats (must equal v25).
C. Contested: YARN seeds {6, 8} x {v20, kaito} x both seats x {v27, v25}.
D. Self-mirror on seed 6.
"""
import importlib.util
import json
import multiprocessing as mp
import os
import sys

sys.path.insert(0, "/home/user/kaggriculture/agent")
sys.path.insert(0, "/home/user/kaggriculture/opponents")
from kaggle_environments import make

OUT = "/home/user/kaggriculture/data/v27_battery_b.jsonl"


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V25 = load_mod("/home/user/kaggriculture/agent/main_v25_wheat16.py", "v25m")
V27 = load_mod("/home/user/kaggriculture/agent/main_v27_selector.py", "v27m")
V20 = load_mod("/home/user/kaggriculture/agent/main.py", "v20m")
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


def job_a(args):
    seed, seat, variant = args
    v27 = load_mod("/home/user/kaggriculture/agent/main_v27_selector.py",
                   f"v27_{variant}_{seed}_{seat}")
    v27._V27_WOOL_VARIANT = variant
    low, _, _, _ = one_game(seed, seat, V25.agent, Idle())
    us, them, shops, esc = one_game(seed, seat, v27.agent, Idle())
    row = {"t": "A", "seed": seed, "seat": seat, "variant": variant,
           "low": low, "us": us, "shops": shops, "esc": esc}
    with open(OUT, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def job_b(args):
    seed, seat = args
    us, them, shops, esc = one_game(seed, seat, V27.agent, Idle())
    low, _, _, _ = one_game(seed, seat, V25.agent, Idle())
    row = {"t": "B", "seed": seed, "seat": seat, "low": low, "us": us,
           "shops": shops, "esc": esc, "diff": us - low}
    with open(OUT, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def job_c(args):
    seed, name, seat, which = args
    opp = V20.agent if name == "v20" else KAITO.agent
    agent = V27.agent if which == "v27" else V25.agent
    us, them, _, esc = one_game(seed, seat, agent, opp)
    row = {"t": "C", "seed": seed, "name": name, "seat": seat,
           "which": which, "us": us, "them": them, "esc": esc}
    with open(OUT, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def dispatch(job):
    kind, args = job[0], job[1]
    return {"A": job_a, "B": job_b, "C": job_c}[kind](args)


def main():
    if os.path.exists(OUT):
        os.remove(OUT)
    jobs = []
    jobs += [("A", (s, seat, v)) for s in (6, 8, 19) for seat in (0, 1)
             for v in VARIANTS]
    jobs += [("B", (s, seat)) for s in (1, 2, 9) for seat in (0, 1)]
    jobs += [("C", (s, n, seat, w)) for s in (6, 8) for n in ("v20", "kaito")
             for seat in (0, 1) for w in ("v27", "v25")]
    print(f"{len(jobs)} jobs", flush=True)
    with mp.Pool(2) as pool:
        for i, row in enumerate(pool.imap_unordered(dispatch, jobs,
                                                    chunksize=1)):
            if row["t"] == "A":
                print(f"[{i+1}] A seed {row['seed']} seat {row['seat']} "
                      f"{row['variant']:9s}: {row['us']:7,.0f} "
                      f"(d {row['us'] - row['low']:+8,.0f}) esc={row['esc']}",
                      flush=True)
            elif row["t"] == "B":
                print(f"[{i+1}] B seed {row['seed']} seat {row['seat']}: "
                      f"diff={row['diff']:+,.0f} (must be 0)", flush=True)
            else:
                print(f"[{i+1}] C seed {row['seed']} {row['name']} seat "
                      f"{row['seat']} {row['which']}: {row['us']:,.0f} vs "
                      f"{row['them']:,.0f}", flush=True)

    # aggregate A
    rows = [json.loads(l) for l in open(OUT)]
    a = [r for r in rows if r["t"] == "A"]
    print("\n=== A: variant mean delta (YARN seeds, both seats) ===", flush=True)
    for v in VARIANTS:
        ds = [r["us"] - r["low"] for r in a if r["variant"] == v]
        print(f"  {v:9s}: n={len(ds)} mean={sum(ds)/len(ds):+9,.0f} "
              f"deltas={[f'{d:+,.0f}' for d in ds]}", flush=True)
    # mirror
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": 6})
    out = env.run([V27.agent, V27.agent])
    last = out[-1]
    print(f"\nmirror seed 6: {last[0].get('reward'):,.0f} vs "
          f"{last[1].get('reward'):,.0f}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
