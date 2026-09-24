#!/usr/bin/env python3
"""Test v18.8 (crash dump) vs v18 mirror, straw-flood proxy, and tetsu."""
import importlib.util
import json
import os

from kaggle_environments import make

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_tape_agent(tape, mod):
    def agent(obs, configuration=None):
        seat = mod._seat(obs)
        actions = tape
        step = min(max(0, int(mod._get(obs, "step", 0) or 0)), len(actions) - 1)
        try:
            mod._update_memory(obs)
            action = mod._weed_repair_action(obs, mod._copy_action(actions[step]), actions, step)
            action = mod._adapt_animals(obs, action)
            action = mod._adapt_crops(obs, action)
            action = mod._adapt_market(obs, action)
            return mod._align_hands(mod._rank_sell_slots(obs, action, configuration), obs)
        except Exception:
            farm = mod._farm(obs, mod._seat(obs))
            return {"farmer": ["PASS"],
                    "hands": [["PASS"]] * len(mod._get(farm, "hands", []) or []),
                    "market": []}
    return agent


def battle(a, b, seed, seat):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    if seat == 0:
        env.run([a, b])
        return env.steps[-1][0].reward or 0, env.steps[-1][1].reward or 0
    env.run([b, a])
    return env.steps[-1][1].reward or 0, env.steps[-1][0].reward or 0


def main():
    v18 = load(os.path.join(ROOT, "submit", "main.py"), "v18")
    v188 = load(os.path.join(ROOT, "agent", "main_v18_8.py"), "v188")
    tetsu = load(os.path.join(ROOT, "opponents", "tetsu_main.py"), "tetsu")

    with open(os.path.join(ROOT, "data", "tapes_variants", "STRAWFLOOD_seat0.json")) as f:
        sf0 = json.load(f)
    with open(os.path.join(ROOT, "data", "tapes_variants", "STRAWFLOOD_seat1.json")) as f:
        sf1 = json.load(f)
    strawflood = make_tape_agent(sf0, v18)

    cases = [
        ("v18.8 vs v18 MIRROR (keep-gate)", v188.agent, v18.agent, [1, 2, 3, 4, 5]),
        ("v18.8 vs STRAWFLOOD proxy", v188.agent, strawflood, [1, 2, 3]),
        ("v18.8 vs TETSU", v188.agent, tetsu.agent, [1, 2, 3]),
        ("v18 (base) vs STRAWFLOOD", v18.agent, strawflood, [1, 2, 3]),
    ]
    for label, a, b, seeds in cases:
        wins = 0
        deltas = []
        for seed in seeds:
            for seat in (0, 1):
                x, y = battle(a, b, seed, seat)
                wins += 1 if x > y else 0
                deltas.append(x - y)
        print(f"{label:<36} W-L {wins}-{len(seeds)*2-wins}  avg_delta {sum(deltas)/len(deltas):+,.0f}  {[f'{d:+,.0f}' for d in deltas]}")


if __name__ == "__main__":
    main()
