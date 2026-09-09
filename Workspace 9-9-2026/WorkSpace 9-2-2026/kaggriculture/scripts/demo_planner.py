"""
demo_planner.py — show the "full AI bot" thinking layer in action.

1. Plays a real game to day 8.
2. Prints the daily-capacity report (can we keep up? would an extra animal
   or extra crops overload the crew?).
3. Runs the what-if evaluator: simulates several candidate decisions a few
   days forward (opponent behaviour frozen) and shows the dollar tradeoff of
   each — the "miss one crop to save 30 vs add one to miss 6" reasoning.

Run:  python3 scripts/demo_planner.py [seed]
"""

import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "agent"))

from sim import GameSim
import decision_agent_v2 as dv2
import planner

DEFAULT_DAYS_IN = 8
DEFAULT_DAYS_OUT = 6


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    days_in = DEFAULT_DAYS_IN
    days_out = DEFAULT_DAYS_OUT

    dv2.set_params(dict(dv2.DEFAULT_PARAMS))
    agent = lambda obs: dv2.agent(obs)  # noqa: E731

    # --- play a real game to `days_in` (self-play shadow as the opponent) ---
    sim = GameSim(seed=seed)
    sim.run(agent, agent, steps=days_in * 24)
    print(f"=== Played to day {days_in} (seed {seed}) ===")
    print(f"    our money ${sim.money(0):,.0f} | opponent ${sim.money(1):,.0f}")

    # --- never-miss capacity report ---
    p = dict(dv2.DEFAULT_PARAMS)
    day_now = days_in
    expected_hires = p["daily_hires"] if day_now < p["late_day"] else p["late_hires"]
    print(f"\n=== Capacity check (day {day_now}, planning +{expected_hires} hires) ===")
    planner.print_capacity(sim.obs(0), player=0, expected_hires=expected_hires)

    # --- what-if lookahead ---
    # Note: options that replicate what the agent already plans (e.g. "buy a
    # cow" on a day its ramp already buys one) come back ~0 — the tool is
    # correctly reporting "no change". The informative rows are the *marginal*
    # decisions the agent wouldn't otherwise make.
    print(f"\n=== What-if lookahead ({days_out} days, opponent frozen) ===")
    options = [
        ("extra 1 SHEEP (d8)", planner.option_buy_animal("SHEEP", 1, day=days_in)),
        ("extra 1 COW (d8)", planner.option_buy_animal("COW", 1, day=days_in)),
        ("extra 2 hands (d8)", planner.option_extra_hires(2, days=(days_in,))),
        ("extra 2 hands (d8,d9)", planner.option_extra_hires(2, days=(days_in, days_in + 1))),
        ("unlock next quadrant (d8)", planner.option_buy_land(day=days_in)),
        ("+8 wheat feed stock (d8)", planner.option_buy_wheat(8, day=days_in)),
    ]
    results = planner.what_if(sim, days_out, options, agent0=agent)

    best = max(results, key=lambda r: r[1])
    print(f"\n   BEST: {best[0]}  (${best[1]:,.0f})")


if __name__ == "__main__":
    main()
