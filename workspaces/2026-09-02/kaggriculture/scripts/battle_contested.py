"""
battle_contested.py — head-to-head margin testing for the counter layer.

The win condition is MARGIN vs a live opponent, not solo gold. This script
pits our agent (v4 counter) against opponent archetypes and reports
wins/losses/ties and the average money margin per game — the "beat them by
20 extra gold" metric.

Archetypes (built from v2 with different params — the "clones with
modifications" you see on the ladder):
    mirror   : identical economy to ours (10 cows / 4 sheep)
    cowbot   : 14 cows, 0 sheep  (floods milk)
    sheepbot : 2 cows, 12 sheep  (floods wool)
    goosebot : 4 cows, 2 sheep, 10 geese (floods eggs)

For each matchup it also runs v2 (no counter) as the CONTROL, so you can see
exactly how much the counter layer adds on top of the plain economy.

Run:
    python3 scripts/battle_contested.py [seeds] [agent]

    agent = v4 (default) | v2 | v3
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(HERE, "..", "agent")
sys.path.insert(0, AGENT_DIR)

from kaggle_environments import make  # noqa: E402
import decision_agent_v2 as v2  # noqa: E402
import decision_agent_v4 as v4  # noqa: E402


def make_agent(mod, params):
    """Build a seat-agnostic agent from a module's agent class."""
    cls = mod.CounterAgent if hasattr(mod, "CounterAgent") else mod.DecisionAgent
    inst = cls(params, seat=0)
    return lambda obs, config=None: inst.act(obs, config)


ARCHETYPES = {
    "mirror":   dict(v2.DEFAULT_PARAMS),
    "cowbot":   {**dict(v2.DEFAULT_PARAMS), "final_cow": 14, "final_sheep": 0,
                 "target_sheep": 0, "open_sheep": 0},
    "sheepbot": {**dict(v2.DEFAULT_PARAMS), "final_cow": 2, "final_sheep": 12,
                 "open_cows": 2, "open_sheep": 3},
    "goosebot": {**dict(v2.DEFAULT_PARAMS), "final_cow": 4, "final_sheep": 2,
                 "target_goose": 3, "final_goose": 10, "open_geese": 2},
}


def battle(agent_a, agent_b, seed, seat_swap=False):
    if seat_swap:
        agent_a, agent_b = agent_b, agent_a
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    result = env.run([agent_a, agent_b])
    return (result[-1][0]["observation"]["farms"][0]["money"],
            result[-1][1]["observation"]["farms"][1]["money"])


def run_matchup(our_agent, opp_agent, seeds):
    """Return (W, L, T, avg_margin_ours_minus_opp, games)."""
    w = l = t = 0
    margins = []
    for seed in seeds:
        for seat in (0, 1):
            p0, p1 = battle(our_agent, opp_agent, seed, seat_swap=(seat == 1))
            ours = p0 if seat == 0 else p1
            opp = p1 if seat == 0 else p0
            margin = ours - opp
            margins.append(margin)
            if margin > 0.5:
                w += 1
            elif margin < -0.5:
                l += 1
            else:
                t += 1
    return w, l, t, sum(margins) / len(margins), margins


def main():
    seeds = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [1, 2, 3]
    agent_name = sys.argv[2] if len(sys.argv) > 2 else "v4"

    mod = {"v2": v2, "v4": v4}[agent_name]
    params = mod.V4_DEFAULT_PARAMS if hasattr(mod, "V4_DEFAULT_PARAMS") else mod.DEFAULT_PARAMS
    our = make_agent(mod, dict(params))

    print(f"{'='*66}")
    print(f"  {agent_name.upper()} vs opponent archetypes | seeds {seeds}")
    print(f"{'='*66}")
    for name, opp_params in ARCHETYPES.items():
        opp = make_agent(v2, dict(opp_params))
        w, l, t, avg, margins = run_matchup(our, opp, seeds)
        print(f"  vs {name:<10} {w}W-{l}L-{t}T   avg margin {avg:+,.0f}   "
              f"({', '.join(f'{m:+,.0f}' for m in margins)})")

    # control: v2 (no counter) vs the same archetypes, for comparison
    print(f"\n  --- control: v2 (no counter) vs same archetypes ---")
    v2_agent = make_agent(v2, dict(v2.DEFAULT_PARAMS))
    for name, opp_params in ARCHETYPES.items():
        opp = make_agent(v2, dict(opp_params))
        w, l, t, avg, margins = run_matchup(v2_agent, opp, seeds)
        print(f"  vs {name:<10} {w}W-{l}L-{t}T   avg margin {avg:+,.0f}   "
              f"({', '.join(f'{m:+,.0f}' for m in margins)})")


if __name__ == "__main__":
    main()
