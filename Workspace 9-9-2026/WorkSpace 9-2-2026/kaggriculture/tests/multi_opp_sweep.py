"""Multi-opp sweep — evaluate a change against BT, V41, moon, soil."""
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


def call(fn, obs, cfg=None):
    try: return fn(obs, cfg)
    except TypeError: return fn(obs)


def h2h_delta(opp_agent, seeds=(1,2,3,4)):
    delta = 0
    for seed in seeds:
        for seat in [0,1]:
            sim = GameSim(seed=seed)
            for _ in range(720):
                obs0 = sim.obs(0); obs1 = sim.obs(1)
                if seat == 0:
                    a0 = call(custom, obs0); a1 = call(opp_agent, obs1)
                else:
                    a0 = call(opp_agent, obs0); a1 = call(custom, obs1)
                sim.step(a0, a1)
            delta += sim.money(seat) - sim.money(1-seat)
    return delta / (len(seeds) * 2)


def solo(n=5):
    total = 0
    for seed in range(1, n+1):
        sim = GameSim(seed=seed)
        for _ in range(720):
            sim.step(custom(sim.obs(0)), {})
        total += sim.money(0)
    return total / n


if __name__ == "__main__":
    s = solo(5)
    bt = h2h_delta(BT.agent)
    v41 = h2h_delta(V41.agent)
    m = h2h_delta(moon.agent)
    so = h2h_delta(soil.agent)
    avg = (bt + v41 + m + so) / 4
    print(f"SOLO(5): ${s:.0f}")
    print(f"BT:   ${bt:+,.0f}")
    print(f"V41:  ${v41:+,.0f}")
    print(f"moon: ${m:+,.0f}")
    print(f"soil: ${so:+,.0f}")
    print(f"avg:  ${avg:+,.0f}")
