import sys, json, importlib.util
from importlib.machinery import SourceFileLoader

ROOT = "/home/user"
sys.path.insert(0, ROOT + "/kaggriculture/agent")
sys.path.insert(0, ROOT + "/kaggriculture")
sys.path.insert(0, ROOT + "/kaggriculture/scripts")

from sim import GameSim
import breaking_tie as BT

loader = SourceFileLoader("var", sys.argv[1])
spec = importlib.util.spec_from_loader("var", loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)


def call(fn, o):
    try:
        return fn(o, None)
    except TypeError:
        return fn(o)


d = 0
w = 0
n = 0
per = []
for seed in (1, 2, 3, 5, 19):
    for seat in (0, 1):
        sim = GameSim(seed=seed)
        for _ in range(720):
            o0, o1 = sim.obs(0), sim.obs(1)
            if seat == 0:
                sim.step(call(m.agent, o0), call(BT.agent, o1))
            else:
                sim.step(call(BT.agent, o0), call(m.agent, o1))
        dd = sim.money(seat) - sim.money(1 - seat)
        d += dd
        w += dd > 0
        n += 1
        per.append(int(dd))
print(json.dumps({"w": w, "n": n, "avg": round(d / n), "per": per}))
