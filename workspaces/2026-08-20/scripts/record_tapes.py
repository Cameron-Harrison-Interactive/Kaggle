#!/usr/bin/env python3
"""Record per-seed route tapes by running v18 against a pass opponent.

Each tape = the exact 719-step action sequence v18 plays on that seed/seat.
This recreates the lost route_v18_opt_seat{seat}_s{seed}.json library.

Usage:
  python3 scripts/record_tapes.py --seeds 1-20 [--out data/tapes]
"""
import argparse
import importlib.util
import json
import os
import sys
import time

from kaggle_environments import make

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AGENT = os.path.join(ROOT, "submit", "main.py")


def load_v18(path=AGENT):
    spec = importlib.util.spec_from_file_location("v18", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Disable runtime weed repair while recording so the tape is clean
    # (no DIG baked in; the runtime layer re-adds DIG per actual weeds).
    mod._weed_repair_action = lambda obs, action, actions, step: action
    return mod


def make_pass_agent():
    def agent(obs, configuration=None):
        farm = obs["farms"][obs["player"]]
        return {
            "market": [],
            "farmer": ["PASS"],
            "hands": [["PASS"]] * len(farm.get("hands") or []),
        }
    return agent


def record_seed(mod, seed):
    """Record both seats for one seed. Returns (seat0_tape, seat1_tape)."""
    pass_agent = make_pass_agent()
    tapes = {0: [], 1: []}

    # seat 0: v18 as player 0
    def rec0(obs, config):
        act = mod.agent(obs, config)
        tapes[0].append({
            "market": [list(o) for o in (act.get("market") or [])],
            "farmer": list(act.get("farmer") or ["PASS"]),
            "hands": [list(h) for h in (act.get("hands") or [])],
        })
        return act

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    env.run([rec0, pass_agent])
    r0 = env.steps[-1][0].reward or 0

    # seat 1: v18 as player 1
    def rec1(obs, config):
        act = mod.agent(obs, config)
        tapes[1].append({
            "market": [list(o) for o in (act.get("market") or [])],
            "farmer": list(act.get("farmer") or ["PASS"]),
            "hands": [list(h) for h in (act.get("hands") or [])],
        })
        return act

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    env.run([pass_agent, rec1])
    r1 = env.steps[-1][1].reward or 0
    return tapes[0], tapes[1], r0, r1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="1,2,3,4,5,6,7,8,9,10")
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "tapes"))
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]
    os.makedirs(args.out, exist_ok=True)

    mod = load_v18()
    print(f"recording seeds {seeds}...", flush=True)
    for seed in seeds:
        t0 = time.time()
        s0, s1, r0, r1 = record_seed(mod, seed)
        p0 = os.path.join(args.out, f"route_v18_opt_seat0_s{seed}.json")
        p1 = os.path.join(args.out, f"route_v18_opt_seat1_s{seed}.json")
        with open(p0, "w") as f:
            json.dump(s0, f)
        with open(p1, "w") as f:
            json.dump(s1, f)
        print(f"seed {seed}: seat0 {len(s0)} steps (${r0:,.0f}), seat1 {len(s1)} steps (${r1:,.0f}) [{time.time()-t0:.0f}s]", flush=True)


if __name__ == "__main__":
    main()
