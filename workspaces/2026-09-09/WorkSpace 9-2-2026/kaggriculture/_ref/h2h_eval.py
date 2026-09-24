"""h2h_eval.py — evaluate a tape module vs a reference opponent (both seats).
Usage: python3 _ref/h2h_eval.py <bot.py> <opp.py> [seeds...]"""
import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim

def load(path, name="m"):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def call(fn, obs):
    try:
        return fn(obs, None)
    except TypeError:
        return fn(obs)

def h2h(ma, mb, seeds):
    wa = wb = 0; ta = tb = 0.0
    for s in seeds:
        for seat_a in (0, 1):
            sim = GameSim(seed=s)
            for _ in range(720):
                o0, o1 = sim.obs(0), sim.obs(1)
                a0 = call(ma.agent if seat_a == 0 else mb.agent, o0)
                a1 = call(mb.agent if seat_a == 0 else ma.agent, o1)
                sim.step(a0, a1)
            mma, mmb = sim.money(seat_a), sim.money(1 - seat_a)
            ta += mma; tb += mmb
            if mma > mmb: wa += 1
            else: wb += 1
    n = len(seeds) * 2
    return wa, wb, ta / n, tb / n

if __name__ == "__main__":
    bot = load(sys.argv[1], "bot")
    opp = load(sys.argv[2], "opp")
    seeds = [int(x) for x in sys.argv[3:]] or [1, 2, 3, 4, 5, 6]
    w, l, a, b = h2h(bot, opp, seeds)
    print(f"{w}-{l}  bot_avg={a:,.0f}  opp_avg={b:,.0f}")
