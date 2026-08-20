#!/usr/bin/env python3
"""prize_v27.py — measure the route-switch prize.

Probe: on seeds where YARN_STORE is visible by day 7, does a wool-heavy
economy (Kawashigi's full public route, decoded — VALIDATION INSTRUMENT
ONLY, never submitted) beat our v25? And does v25 win the non-YARN seeds?
If yes, a selector between two economies we own is worth building.
"""
import importlib.util
import json
import sys

sys.path.insert(0, "/home/user/kaggriculture/agent")
from kaggle_environments import make


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V25 = load_mod("/home/user/kaggriculture/agent/main_v25_wheat16.py", "v25m")
KAW = json.load(open("/home/user/top10/kawashigi_route_92521336_s0.json"))


class KawFull:
    def __call__(self, obs, configuration=None):
        step = min(max(0, int(obs.get("step", 0) or 0)), len(KAW) - 1)
        a = KAW[step]
        return {"farmer": a.get("farmer") or ["PASS"],
                "hands": a.get("hands") or [],
                "market": a.get("market") or []}


class Idle:
    def __call__(self, obs, configuration=None):
        return {}


def one_game(seed, seat, agent):
    agents = [Idle(), Idle()]
    agents[seat] = agent
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": seed})
    out = env.run(agents)
    town = (((out[168][seat].get("observation") or {}).get("town") or {})
            .get("unlocked_shops") or [])
    return out[-1][seat].get("reward"), list(town)


def main():
    kaw = KawFull()
    print("prize probe: full-Kawashigi route vs our v25, by trigger state",
          flush=True)
    print(f"{'seed':>4} {'seat':>4} {'shops':>32} {'v25':>9} {'KAW':>9} {'delta':>9}",
          flush=True)
    yarn_deltas = []
    non_deltas = []
    for s in range(1, 17):
        for seat in (0, 1):
            low, shops = one_game(s, seat, V25.agent)
            k, shops2 = one_game(s, seat, kaw)
            trig = "YARN" if "YARN_STORE" in shops else "other"
            d = k - low
            print(f"{s:>4} {seat:>4} {str(shops):>32} {low:>9,.0f} "
                  f"{k:>9,.0f} {d:+9,.0f}", flush=True)
            (yarn_deltas if trig == "YARN" else non_deltas).append(d)
    print(f"\nYARN blocks: n={len(yarn_deltas)} "
          f"mean={sum(yarn_deltas)/max(1, len(yarn_deltas)):+,.0f}", flush=True)
    print(f"other blocks: n={len(non_deltas)} "
          f"mean={sum(non_deltas)/max(1, len(non_deltas)):+,.0f}", flush=True)


if __name__ == "__main__":
    main()
