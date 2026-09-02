"""Complete the gate matrix: v11.6 with varying mirror gates vs MAKER-LESS stock."""
import json
import re
import subprocess
import sys

ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"

CHILD = r'''
import sys, json, re, importlib.util
from importlib.machinery import SourceFileLoader
ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"
sys.path.insert(0, ROOT + "/agent"); sys.path.insert(0, ROOT + "/scripts")
from sim import GameSim

mirror_gate = float(sys.argv[1])
src = open(ROOT + "/topbots/v116_FINAL.py").read()
if "'mirror_wheat_minimum_profit':" in src:
    src, n = re.subn(r"('mirror_wheat_minimum_profit': )([^,}]+)",
                     lambda m: m.group(1) + repr(mirror_gate), src, count=1)
    assert n == 1
else:
    src, n = re.subn(r"('terminal_rule': 'collision')",
                     r"\g<1>, 'mirror_wheat_minimum_profit': " + repr(mirror_gate), src, count=1)
    assert n == 1
open("/tmp/_ar_var.py", "w").write(src)

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

variant = fresh("/tmp/_ar_var.py", "varc")
stock = fresh(ROOT + "/topbots/main.py", "st")

d = []
w = 0
for s in (1, 3, 4, 5, 19):
    for seat in (0, 1):
        sim = GameSim(seed=s)
        for _ in range(720):
            o0, o1 = sim.obs(0), sim.obs(1)
            if seat == 0:
                sim.step(call(variant, o0), call(stock, o1))
            else:
                sim.step(call(stock, o0), call(variant, o1))
        dd = sim.money(seat) - sim.money(1 - seat)
        d.append(round(dd))
        w += dd > 0
print(json.dumps({"w": w, "n": len(d), "avg": round(sum(d) / len(d)), "per": d}))
'''

if __name__ == '__main__':
    for gate in (25.0, 12.0, 5.0, 1.0):
        r = subprocess.run([sys.executable, '-c', CHILD, str(gate)],
                           capture_output=True, text=True, timeout=900, cwd=ROOT)
        out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'ERR ' + r.stderr[-120:]
        print(f'gate={gate:5} vs stock: {out}', flush=True)
