"""Clone-preemption knob sweep on v11.5 base vs stock (mirror seeds)."""
import json
import re
import subprocess
import sys

ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"

CHILD = r'''
import sys, json, re, importlib.util
from importlib.machinery import SourceFileLoader
ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"
sys.path.insert(0, ROOT + "/agent"); sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/scripts")
from sim import GameSim

patch = json.loads(sys.argv[1])
src = open(ROOT + "/topbots/v115_FINAL_w9ytL.py").read()
for k, v in patch.items():
    src, n = re.subn(r"('" + k + r"': )([^,}]+)", lambda mm, v=v: mm.group(1) + repr(v), src, count=1)
    assert n == 1, "patch " + k + " failed"

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

open("/tmp/_pre_var.py", "w").write(src)
variant = fresh("/tmp/_pre_var.py", "varc")
stock = fresh(ROOT + "/topbots/main.py", "stockc")

mir = []
for s in (1, 3, 4, 5, 19):
    a_ = 0.0
    b_ = 0.0
    for seat in (0, 1):
        sim = GameSim(seed=s)
        for _ in range(720):
            o0, o1 = sim.obs(0), sim.obs(1)
            if seat == 0:
                sim.step(call(variant, o0), call(stock, o1))
            else:
                sim.step(call(stock, o0), call(variant, o1))
        a_ += sim.money(seat)
        b_ += sim.money(1 - seat)
    mir.append(round(a_ - b_))
print(json.dumps({"mirror": mir, "avg": round(sum(mir) / len(mir))}))
'''

JOBS = [
    ('baseline knobs', {}),
    ('batch 10->25', {'clone_maximum_batch': 25}),
    ('horizon 2->5', {'clone_preempt_horizon': 5}),
    ('active 160->80', {'clone_active_start': 80}),
    ('streak 24->10', {'clone_streak_required': 10}),
    ('all four', {'clone_maximum_batch': 25, 'clone_preempt_horizon': 5,
                  'clone_active_start': 80, 'clone_streak_required': 10}),
]

if __name__ == '__main__':
    for label, patch in JOBS:
        r = subprocess.run([sys.executable, '-c', CHILD, json.dumps(patch)],
                           capture_output=True, text=True, timeout=900, cwd=ROOT)
        out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'ERR ' + r.stderr[-100:]
        print(f'{label:22} {out}', flush=True)
    print('(W9ytL mirror refs vs stock: [+303,0,0,0,+404] avg +221)')
