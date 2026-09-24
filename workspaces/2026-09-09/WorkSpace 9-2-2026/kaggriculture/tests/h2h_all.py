"""H2H vs all top opponents (6 seeds × 2 seats each)."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "agent"))

from sim import GameSim
from agent.custom import agent as custom
import breaking_tie as BT
import v41_kaito as V41
import moon
import soil
import amey
import multiroute


OPPS = {
    "BT": BT.agent,
    "V41": V41.agent,
    "moon": moon.agent,
    "soil": soil.agent,
    "amey": amey.agent,
    "multiroute": multiroute.agent,
}


def call(mod_fn, obs, cfg=None):
    try: return mod_fn(obs, cfg)
    except TypeError: return mod_fn(obs)


def run_game(seed, custom_seat, opp_agent):
    sim = GameSim(seed=seed)
    for _ in range(720):
        obs0 = sim.obs(0)
        obs1 = sim.obs(1)
        if custom_seat == 0:
            a0 = call(custom, obs0); a1 = call(opp_agent, obs1)
        else:
            a0 = call(opp_agent, obs0); a1 = call(custom, obs1)
        sim.step(a0, a1)
    return sim.money(custom_seat), sim.money(1 - custom_seat)


if __name__ == "__main__":
    seeds = [1, 2, 3, 4, 5, 6]
    all_summary = []
    for name, opp in OPPS.items():
        wins = 0; delta_total = 0
        for seed in seeds:
            for seat in [0, 1]:
                c, o = run_game(seed, seat, opp)
                if c > o: wins += 1
                delta_total += c - o
        n = len(seeds) * 2
        avg = delta_total / n
        all_summary.append((name, wins, n, avg))
        print(f"vs {name:>12}: wins {wins:>2}/{n}   avg delta ${avg:+,.0f}")
    print()
    print("Summary:")
    for name, w, n, d in all_summary:
        pct = 100 * w / n
        print(f"  {name:>12}: {w:>2}/{n} ({pct:>4.0f}%)  delta ${d:+,.0f}")
