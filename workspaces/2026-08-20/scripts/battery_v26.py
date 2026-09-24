#!/usr/bin/env python3
"""battery_v26.py — PASS gates (seeds 1-3, both seats) + head-to-head ladder
for HI_AgriBot_v26_FeedGuard. Run after the regression suite.

Gates:
  PASS: 0 escapes both seats, seeds 1-3; not worse than v25's PASS.
  H2H seed 1: vs v24 (w14), v25 (w16 self-ish), v20, tetsu, rayk, kaito.
  Self-mirror must be ~0.
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


V26 = load_mod("/home/user/kaggriculture/agent/main_v26_feedguard.py", "v26m")
V25 = load_mod("/home/user/kaggriculture/agent/main_v25_wheat16.py", "v25m")
V24 = load_mod("/home/user/kaggriculture/agent/main_v24_wheatguard.py", "v24m")
V20 = load_mod("/home/user/kaggriculture/agent/main.py", "v20m")
TETSU = load_mod("/home/user/kaggriculture/opponents/tetsu_main.py", "tetsum")
RAYK = load_mod("/home/user/kaggriculture/opponents/rayk_main.py", "raykm")
KAITO = load_mod("/home/user/kaggriculture/opponents/kaito_main.py", "kaitom")


class Idle:
    def __call__(self, obs, configuration=None):
        return {}


def count_escapes(out, seat):
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
    return esc


def play(agents, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": seed})
    out = env.run(agents)
    last = out[-1]
    return (last[0].get("reward"), last[1].get("reward"),
            count_escapes(out, 0), count_escapes(out, 1))


print("=== PASS gates (seeds 1-3, both seats) ===", flush=True)
for seed in (1, 2, 3):
    for seat in (0, 1):
        agents = [Idle(), Idle()]
        agents[seat] = V26.agent
        r0, r1, e0, e1 = play(agents, seed)
        us = r0 if seat == 0 else r1
        esc = e0 if seat == 0 else e1
        print(f"  seed {seed} seat {seat}: us={us:,.0f} escapes={esc}",
              flush=True)

print("=== H2H seed 1 (v26 vs ladder, both seats) ===", flush=True)
ladder = [("v24-w14", V24.agent), ("v25-w16", V25.agent), ("v20", V20.agent),
          ("tetsu", TETSU.agent), ("rayk", RAYK.agent), ("kaito", KAITO.agent),
          ("v26-mirror", V26.agent)]
for name, opp in ladder:
    for seat in (0, 1):
        agents = [opp, V26.agent] if seat == 0 else [V26.agent, opp]
        r0, r1, e0, e1 = play(agents, 1)
        delta = (r0 - r1) if seat == 0 else (r1 - r0)
        esc_us = e0 if seat == 0 else e1
        print(f"  vs {name:12s} seat{seat}: delta={delta:+9,.0f} "
              f"(us {r0 if seat==0 else r1:,.0f} / them {r1 if seat==0 else r0:,.0f}) "
              f"esc_us={esc_us}", flush=True)
print("done", flush=True)
