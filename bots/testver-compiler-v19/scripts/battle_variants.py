#!/usr/bin/env python3
"""Battle v18 variants against v18 mirror. Reports W-L, money deltas,
crop counts at d12, weeds at d15, and final animals.

Usage: python3 scripts/battle_variants.py
"""
import importlib.util
import json
import os
import sys

from kaggle_environments import make

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_tape_agent(seat0_tape, seat1_tape, base_mod):
    """Build an agent function that uses custom tapes with v18's runtime."""
    def agent(obs, configuration=None):
        seat = base_mod._seat(obs)
        actions = seat1_tape if seat == 1 else seat0_tape
        step = min(max(0, int(base_mod._get(obs, "step", 0) or 0)), len(actions) - 1)
        try:
            base_mod._update_memory(obs)
            action = base_mod._weed_repair_action(obs, base_mod._copy_action(actions[step]), actions, step)
            action = base_mod._adapt_animals(obs, action)
            action = base_mod._adapt_crops(obs, action)
            action = base_mod._adapt_market(obs, action)
            return base_mod._align_hands(base_mod._rank_sell_slots(obs, action, configuration), obs)
        except Exception:
            farm = base_mod._farm(obs, base_mod._seat(obs))
            return {"farmer": ["PASS"],
                    "hands": [["PASS"]] * len(base_mod._get(farm, "hands", []) or []),
                    "market": []}
    return agent


def battle(agent_a, agent_b, seed, seat):
    """seat: 0 = a is p0, 1 = a is p1. Returns (a_score, b_score, a_stats, b_stats)"""
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    if seat == 0:
        env.run([agent_a, agent_b])
    else:
        env.run([agent_b, agent_a])
    final = env.steps[-1]
    a, b = (final[0].reward or 0, final[1].reward or 0) if seat == 0 else (final[1].reward or 0, final[0].reward or 0)
    stats = [{}, {}]
    for pi in (0, 1):
        s = stats[0] if (seat == 0 and pi == 0) or (seat == 1 and pi == 1) else stats[1]
        for step in env.steps:
            obs = step[pi].get("observation", {}) or {}
            farm = (obs.get("farms") or [{}, {}])[pi] or {}
            if step[pi].get("status") != "DONE" and len(env.steps) > 0:
                pass
        # sample d12 and d15
        for target in (288, 360):
            if target < len(env.steps):
                obs = env.steps[target][pi].get("observation", {}) or {}
                farm = (obs.get("farms") or [{}, {}])[pi] or {}
                crops = weeds = 0
                for row in farm.get("tiles") or []:
                    for t in row:
                        if isinstance(t, dict):
                            if t.get("kind") == "PLANT":
                                crops += 1
                            elif t.get("kind") == "WEED":
                                weeds += 1
                s[f"crops_d{target//24}"] = crops
                s[f"weeds_d{target//24}"] = weeds
        # final animals
        obs = env.steps[-1][pi].get("observation", {}) or {}
        farm = (obs.get("farms") or [{}, {}])[pi] or {}
        anims = 0
        for row in farm.get("tiles") or []:
            for t in row:
                if isinstance(t, dict) and t.get("animal"):
                    anims += 1
        s["animals_end"] = anims
    return a, b, stats[0], stats[1]


def main():
    v18 = load(os.path.join(ROOT, "submit", "main.py"), "v18")
    v187 = load(os.path.join(ROOT, "agent", "main_v18_7.py"), "v187")

    variants = {"v18.7_wateropt": v187.agent}

    # Carrot tape agents (seed1 tapes for both seats — same as base pair)
    base_mod = v18
    for count in (2, 3):
        s0 = os.path.join(ROOT, "data", "tapes_variants", f"CARROT{count}_seat0_s1.json")
        s1 = os.path.join(ROOT, "data", "tapes_variants", f"CARROT{count}_seat1_s1.json")
        if os.path.exists(s0) and os.path.exists(s1):
            with open(s0) as f:
                t0 = json.load(f)
            with open(s1) as f:
                t1 = json.load(f)
            variants[f"carrot{count}_tape"] = make_tape_agent(t0, t1, base_mod)

    seeds = [1, 2, 3]
    print(f"{'variant':<20} {'seat':<5} {'W-L':<6} {'avg_delta':>10} {'d12_crops':>12} {'d15_weeds':>12} {'anims_end':>10}")
    print("-" * 80)
    for name, agent_fn in variants.items():
        for seat in (0, 1):
            wins = 0
            deltas = []
            c12 = []
            w15 = []
            ae = []
            for seed in seeds:
                a, b, sa, sb = battle(agent_fn, v18.agent, seed, seat)
                wins += 1 if a > b else 0
                deltas.append(a - b)
                mine = sa if seat == 0 else sb
                c12.append(mine.get("crops_d12", -1))
                w15.append(mine.get("weeds_d15", -1))
                ae.append(mine.get("animals_end", -1))
            avg = sum(deltas) / len(deltas)
            print(f"{name:<20} {seat:<5} {wins}-{len(seeds)-wins:<4} {avg:>+10,.0f} {sum(c12)/len(c12):>12.1f} {sum(w15)/len(w15):>12.1f} {sum(ae)/len(ae):>10.1f}")


if __name__ == "__main__":
    main()
