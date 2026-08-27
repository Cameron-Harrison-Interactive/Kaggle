"""Quick H2H test: custom bot vs breaking_tie, N seeds × 2 seats."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "agent"))

from sim import GameSim
from agent.custom import agent as custom
import breaking_tie as BT


def call(mod_fn, obs, cfg=None):
    try:
        return mod_fn(obs, cfg)
    except TypeError:
        return mod_fn(obs)


def run_game(seed, custom_seat, opp_agent):
    """custom is at custom_seat; opp at 1-custom_seat. Return (custom_money, opp_money)."""
    sim = GameSim(seed=seed)
    for _ in range(720):
        obs0 = sim.obs(0)
        obs1 = sim.obs(1)
        if custom_seat == 0:
            a0 = call(custom, obs0)
            a1 = call(opp_agent, obs1)
        else:
            a0 = call(opp_agent, obs0)
            a1 = call(custom, obs1)
        sim.step(a0, a1)
    return sim.money(custom_seat), sim.money(1 - custom_seat)


if __name__ == "__main__":
    seeds = [1, 2, 3, 4, 5, 6]
    opp = BT.agent
    wins = 0
    delta_total = 0
    for seed in seeds:
        for seat in [0, 1]:
            c, o = run_game(seed, seat, opp)
            delta = c - o
            delta_total += delta
            if c > o:
                wins += 1
            print(f"seed {seed} seat {seat}: custom=${c:>7,.0f}  BT=${o:>7,.0f}  delta={delta:+.0f}")
    n = len(seeds) * 2
    print(f"\nWINS: {wins}/{n}   avg delta: ${delta_total/n:+,.0f}")
