"""Validate clone_batch=25 (v11.6 candidate) vs v11.5 base: solo + mirror + BT."""
import json
import re
import subprocess
import sys

ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"

CHILD_SOLO = r'''
import sys, json, re, importlib.util
from importlib.machinery import SourceFileLoader
ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"
sys.path.insert(0, ROOT + "/agent"); sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/scripts")
from sim import GameSim
src = open(ROOT + "/topbots/v115_FINAL_w9ytL.py").read()
src, n = re.subn(r"('clone_maximum_batch': )([^,}]+)", r"\g<1>25", src, count=1)
assert n == 1
open("/tmp/_v116.py", "w").write(src)
loader = SourceFileLoader("v116", "/tmp/_v116.py")
spec = importlib.util.spec_from_loader("v116", loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
def call(fn, o):
    try: return fn(o, None)
    except TypeError: return fn(o)
out = []
for seed in (1, 2, 3):
    sim = GameSim(seed=seed)
    for _ in range(720):
        o0, o1 = sim.obs(0), sim.obs(1)
        a = call(m.agent, o0)
        sim.step(a, {"farmer": ["PASS"], "hands": [], "market": []})
    out.append(round(sim.money(0)))
print(json.dumps(out))
'''

CHILD_MIRROR = r'''
import sys, json, re, importlib.util
from importlib.machinery import SourceFileLoader
ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"
sys.path.insert(0, ROOT + "/agent"); sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/scripts")
from sim import GameSim
src = open(ROOT + "/topbots/v115_FINAL_w9ytL.py").read()
src, n = re.subn(r"('clone_maximum_batch': )([^,}]+)", r"\g<1>25", src, count=1)
assert n == 1
open("/tmp/_v116.py", "w").write(src)

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

variant = fresh("/tmp/_v116.py", "varc")
opp = fresh(sys.argv[1], "opp")
seeds = json.loads(sys.argv[2])
d = []
for s in seeds:
    a_ = 0.0
    b_ = 0.0
    for seat in (0, 1):
        sim = GameSim(seed=s)
        for _ in range(720):
            o0, o1 = sim.obs(0), sim.obs(1)
            if seat == 0:
                sim.step(call(variant, o0), call(opp, o1))
            else:
                sim.step(call(opp, o0), call(variant, o1))
        a_ += sim.money(seat)
        b_ += sim.money(1 - seat)
    d.append(round(a_ - b_))
print(json.dumps({"deltas": d, "avg": round(sum(d) / len(d))}))
'''

if __name__ == '__main__':
    r = subprocess.run([sys.executable, '-c', CHILD_SOLO], capture_output=True, text=True, timeout=600, cwd=ROOT)
    print('solo [1,2,3]:', r.stdout.strip() or r.stderr[-100:], '(refs 177616/186250/189765)', flush=True)
    r = subprocess.run([sys.executable, '-c', CHILD_MIRROR, ROOT + '/topbots/main.py', '[1,3,4,5,19,29,61,62]'],
                       capture_output=True, text=True, timeout=900, cwd=ROOT)
    print('mirror vs stock (8 seeds):', r.stdout.strip() or r.stderr[-100:], flush=True)
    r = subprocess.run([sys.executable, '-c', CHILD_MIRROR, ROOT + '/agent/breaking_tie.py', '[1,2,3,5,19]'],
                       capture_output=True, text=True, timeout=900, cwd=ROOT)
    print('vs BT (5 seeds):', r.stdout.strip() or r.stderr[-100:], '(v11.5 ref: 10/10, +9145)', flush=True)
