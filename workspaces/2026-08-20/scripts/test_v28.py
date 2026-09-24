#!/usr/bin/env python3
"""test_v28.py — battery for HI_AgriBot_v28_WheatArb.

A. PASS seeds 1-3, both seats, MULT in {1.0, 1.25, 1.5, 1.75, 2.0} + escapes.
B. Contested seeds 1-2 vs v20/kaito both seats, MULT 1.5 vs v25.
C. Replay spots: 3 recorded v24-loss opponents (Debmalya replay etc.) vs
   MULT 1.5 and v25.
D. Self-mirror seed 1.
"""
import importlib.util
import json
import multiprocessing as mp
import os
import sys

sys.path.insert(0, "/home/user/kaggriculture/agent")
sys.path.insert(0, "/home/user/kaggriculture/opponents")
from kaggle_environments import make

OUT = "/home/user/kaggriculture/data/v28_battery.jsonl"


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V25 = load_mod("/home/user/kaggriculture/agent/main_v25_wheat16.py", "v25m")
V20 = load_mod("/home/user/kaggriculture/agent/main.py", "v20m")
KAITO = load_mod("/home/user/kaggriculture/opponents/kaito_main.py", "kaitom")
MULTS = [1.0, 1.25, 1.5, 1.75, 2.0]

REPLAYS = {}
for eid in ("93065463", "93061726", "93059081"):
    p = f"/home/user/kaggriculture/data/regression_v26/opp_actions/{eid}.json"
    if os.path.exists(p):
        d = json.load(open(p))
        REPLAYS[eid] = (d["actions"], d["our_seat"], d["opp_seat"], d["seed"])


class Idle:
    def __call__(self, obs, configuration=None):
        return {}


class ReplayOpp:
    def __init__(self, acts):
        self.acts = acts
        self.i = -1

    def __call__(self, obs, configuration=None):
        self.i += 1
        return self.acts[min(self.i, len(self.acts) - 1)]


def one_game(seed, seat, agent, opponent):
    agents = [Idle(), Idle()]
    agents[seat] = agent
    agents[1 - seat] = opponent
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": seed})
    out = env.run(agents)
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
    return us, them, esc


def job_a(args):
    seed, seat, mult = args
    v28 = load_mod("/home/user/kaggriculture/agent/main_v28_wheatarb.py",
                   f"v28_{mult}_{seed}_{seat}")
    v28._V28_MULT = float(mult)
    us, them, esc = one_game(seed, seat, v28.agent, Idle())
    row = {"t": "A", "seed": seed, "seat": seat, "mult": mult,
           "us": us, "esc": esc}
    with open(OUT, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def job_b(args):
    seed, name, seat = args
    opp = V20.agent if name == "v20" else KAITO.agent
    v28 = load_mod("/home/user/kaggriculture/agent/main_v28_wheatarb.py",
                   f"v28b_{seed}_{name}_{seat}")
    v28._V28_MULT = 1.5
    u28, t28, e28 = one_game(seed, seat, v28.agent, opp)
    u25, t25, e25 = one_game(seed, seat, V25.agent, opp)
    row = {"t": "B", "seed": seed, "name": name, "seat": seat,
           "v28": [u28, t28, e28], "v25": [u25, t25, e25]}
    with open(OUT, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def job_c(args):
    eid = args
    acts, our_seat, opp_seat, seed = REPLAYS[eid]
    agents = [None, None]
    agents[our_seat] = load_mod("/home/user/kaggriculture/agent/"
                                "main_v28_wheatarb.py",
                                f"v28c_{eid}").agent
    agents[opp_seat] = ReplayOpp(acts)
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": int(seed)})
    out = env.run(agents)
    last = out[-1]
    u28 = last[our_seat].get("reward")
    agents[our_seat] = V25.agent
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": int(seed)})
    out = env.run(agents)
    last = out[-1]
    u25 = last[our_seat].get("reward")
    row = {"t": "C", "eid": eid, "v28": u28, "v25": u25}
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
    jobs += [("A", (s, seat, m)) for s in (1, 2, 3) for seat in (0, 1)
             for m in MULTS]
    jobs += [("B", (s, n, seat)) for s in (1, 2) for n in ("v20", "kaito")
             for seat in (0, 1)]
    jobs += [("C", eid) for eid in REPLAYS]
    print(f"{len(jobs)} jobs", flush=True)
    with mp.Pool(2) as pool:
        for i, row in enumerate(pool.imap_unordered(dispatch, jobs,
                                                    chunksize=1)):
            if row["t"] == "A":
                print(f"[{i+1}] A seed {row['seed']} seat {row['seat']} "
                      f"mult {row['mult']}: {row['us']:,.0f} esc={row['esc']}",
                      flush=True)
            elif row["t"] == "B":
                d = (row["v28"][0] - row["v28"][1]) - (row["v25"][0] - row["v25"][1])
                print(f"[{i+1}] B seed {row['seed']} {row['name']} seat "
                      f"{row['seat']}: d28={d:+9,.0f} "
                      f"(v28 {row['v28'][0]:,.0f}/{row['v28'][1]:,.0f} | "
                      f"v25 {row['v25'][0]:,.0f}/{row['v25'][1]:,.0f}) "
                      f"esc={row['v28'][2]}", flush=True)
            else:
                print(f"[{i+1}] C replay {row['eid']}: v28 {row['v28']:,.0f} "
                      f"vs v25 {row['v25']:,.0f} "
                      f"(d {row['v28'] - row['v25']:+,.0f})", flush=True)

    rows = [json.loads(l) for l in open(OUT)]
    a = [r for r in rows if r["t"] == "A"]
    print("\n=== A: PASS per mult (mean over 6 games) ===", flush=True)
    v25base = {}
    for s in (1, 2, 3):
        for seat in (0, 1):
            us, them, esc = one_game(s, seat, V25.agent, Idle())
            v25base[(s, seat)] = us
    for m in MULTS:
        ds = [r["us"] - v25base[(r["seed"], r["seat"])] for r in a
              if r["mult"] == m]
        escs = sum(r["esc"] for r in a if r["mult"] == m)
        print(f"  mult {m}: mean={sum(ds)/len(ds):+9,.0f} esc_total={escs} "
              f"deltas={[f'{d:+,.0f}' for d in ds]}", flush=True)

    print("\n=== mirror seed 1 (mult 1.5) ===", flush=True)
    v28 = load_mod("/home/user/kaggriculture/agent/main_v28_wheatarb.py",
                   "v28m_final")
    v28._V28_MULT = 1.5
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": 1})
    out = env.run([v28.agent, v28.agent])
    last = out[-1]
    print(f"  {last[0].get('reward'):,.0f} vs {last[1].get('reward'):,.0f}",
          flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
