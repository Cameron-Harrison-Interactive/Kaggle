"""
test_v0_solo.py — smoke test the v0 custom bot against PASS.

Prints per-day money trace so we can see the field cycle.
Success target: $30k+ solo (v0 goal: prove routing works, not to compete yet).
"""

import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from sim import GameSim
from agent.custom import agent as custom_agent


def PASS(obs, cfg=None):
    n_hands = len(obs["farms"][obs["player"]].get("hands", []) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * n_hands, "market": []}


def run_solo(seed, n_steps=720, trace=True):
    sim = GameSim(seed=seed)
    day_money = {}
    errors = []
    for step in range(n_steps):
        try:
            a0 = custom_agent(sim.obs(0))
        except Exception as e:
            errors.append(f"step {step}: {type(e).__name__}: {e}")
            a0 = {"farmer": ["PASS"], "hands": [], "market": []}
        a1 = PASS(sim.obs(1))
        sim.step(a0, a1)
        d = sim.state[0].observation.day
        if d not in day_money:
            day_money[d] = sim.money(0)
    final = sim.money(0)
    if trace:
        print(f"seed={seed} final=${final:,.0f}")
        for d in sorted(day_money):
            print(f"  D{d:>2}: ${day_money[d]:>9,.0f}")
        if errors:
            print(f"  ERRORS: {len(errors)}")
            for e in errors[:5]:
                print(f"    {e}")
    return final, errors


if __name__ == "__main__":
    total = 0
    for seed in [1, 2, 3]:
        f, errs = run_solo(seed, trace=(seed == 1))
        total += f
        if errs:
            print(f"seed {seed}: {len(errs)} errors, final ${f:,.0f}")
        elif seed != 1:
            print(f"seed {seed}: ${f:,.0f}")
    print(f"\nAVG over 3 seeds: ${total/3:,.0f}")
