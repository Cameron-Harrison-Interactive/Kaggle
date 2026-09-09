"""eval_tape.py — fast in-process solo evaluation of any tape/agent module.
Usage: python3 _ref/eval_tape.py <bot.py> [seeds...]
"""
import sys, os, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim

def load(path, name="botmod"):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def call(fn, obs):
    try:
        return fn(obs, None)
    except TypeError:
        return fn(obs)

def solo(path, seeds):
    m = load(path)
    out = []
    for s in seeds:
        sim = GameSim(seed=s)
        a1 = {"farmer": ["PASS"], "hands": [], "market": []}
        for _ in range(720):
            out_obs = sim.obs(0)
            a0 = call(m.agent, out_obs)
            sim.step(a0, a1)
        out.append(sim.money(0))
    return out

if __name__ == "__main__":
    path = sys.argv[1]
    seeds = [int(x) for x in sys.argv[2:]] or list(range(1, 9))
    res = solo(path, seeds)
    for s, r in zip(seeds, res):
        print(f"seed {s}: {r:,.0f}")
    print(f"avg: {sum(res)/len(res):,.0f}")
