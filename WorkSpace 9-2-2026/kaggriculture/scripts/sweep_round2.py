"""Round 2 knob sweep on v11.6 base: batch push, phase batch, terminal rule."""
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
src = open(ROOT + "/topbots/v116_FINAL.py").read()
for k, v in patch.items():
    src, n = re.subn(r"('" + k + r"': )([^,}]+)", lambda mm, v=v: mm.group(1) + repr(v), src, count=1)
    assert n == 1, "patch " + k + " failed"
open("/tmp/_r2_var.py", "w").write(src)

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

variant = fresh("/tmp/_r2_var.py", "varc")

# solo first (2 seeds)
solo = []
for seed in (1, 3):
    sim = GameSim(seed=seed)
    for _ in range(720):
        o0, o1 = sim.obs(0), sim.obs(1)
        a = call(variant, o0)
        sim.step(a, {"farmer": ["PASS"], "hands": [], "market": []})
    solo.append(round(sim.money(0)))

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
print(json.dumps({"solo": solo, "mirror": mir, "avg": round(sum(mir) / len(mir))}))
'''

JOBS = [
    ('v11.6 base (batch25)', {}),
    ('batch 40', {'clone_maximum_batch': 40}),
    ('batch 60', {'clone_maximum_batch': 60}),
    ('phase_batch 40', {'clone_phase_maximum_batch': 40}),
    ('detect 48->24', {'clone_detection_start': 24}),
    ('terminal value', {'terminal_rule': 'value'}),
]

if __name__ == '__main__':
    for label, patch in JOBS:
        r = subprocess.run([sys.executable, '-c', CHILD, json.dumps(patch)],
                           capture_output=True, text=True, timeout=900, cwd=ROOT)
        out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'ERR ' + r.stderr[-100:]
        print(f'{label:22} {out}', flush=True)
    print('(v11.6 refs: solo 177616/189765, mirror avg +970)')
