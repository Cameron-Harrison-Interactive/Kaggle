"""v11.6 vs the full local field: moon, soil, v41, amey, multiroute."""
import json
import subprocess
import sys

ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"

CHILD = r'''
import sys, json, importlib.util
from importlib.machinery import SourceFileLoader
ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"
sys.path.insert(0, ROOT + "/agent"); sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/scripts")
from sim import GameSim

def load(path, name):
    loader = SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m.agent

def call(fn, o):
    try: return fn(o, None)
    except TypeError: return fn(o)

def fresh(path, name):
    for k in [k for k in list(sys.modules) if k.split(".")[0] in ("v19","v23","v24","v44","v48","scripts")]:
        del sys.modules[k]
    return load(path, name)

variant = fresh(ROOT + "/topbots/v116_FINAL.py", "varc")
opp = fresh(sys.argv[1], "opp")
d = 0
w = 0
n = 0
for seed in (1, 2, 19, 29):
    for seat in (0, 1):
        sim = GameSim(seed=seed)
        for _ in range(720):
            o0, o1 = sim.obs(0), sim.obs(1)
            if seat == 0:
                sim.step(call(variant, o0), call(opp, o1))
            else:
                sim.step(call(opp, o0), call(variant, o1))
        dd = sim.money(seat) - sim.money(1 - seat)
        d += dd
        w += dd > 0
        n += 1
print(json.dumps({"w": w, "n": n, "avg": round(d / n)}))
'''

OPPS = [
    ('BT', ROOT + '/agent/breaking_tie.py'),
    ('moon', ROOT + '/agent/moon.py'),
    ('soil', ROOT + '/agent/soil.py'),
    ('amey', ROOT + '/agent/amey.py'),
    ('v41', ROOT + '/agent/v41_kaito.py'),
    ('multiroute', ROOT + '/agent/multiroute.py'),
]

if __name__ == '__main__':
    for label, path in OPPS:
        r = subprocess.run([sys.executable, '-c', CHILD, path],
                           capture_output=True, text=True, timeout=900, cwd=ROOT)
        out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'ERR ' + r.stderr[-100:]
        print(f'v11.6 vs {label:11} {out}', flush=True)
