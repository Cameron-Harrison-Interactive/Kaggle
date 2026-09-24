"""Mirror-gate sweep vs a MAKER-EQUIPPED clone (the real top-of-ladder opponent).

Opponent = stock V46 + uniform wheat maker (profit 1.0 everywhere, batch 60)
= the 'W3' build from session 70 = what lucaskna/Yizuki effectively run.
Our v11.6 currently uses mirror gate 25.0 (disarms us vs clones).
"""
import json
import re
import subprocess
import sys

ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"

CHILD = r'''
import sys, json, re, importlib.util, zlib, base64
from importlib.machinery import SourceFileLoader
ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"
sys.path.insert(0, ROOT + "/agent"); sys.path.insert(0, ROOT); sys.path.insert(0; 0) if False else ROOT + "/scripts")
from sim import GameSim
'''.replace("(0; 0)", "")

CHILD = r'''
import sys, json, re, importlib.util
from importlib.machinery import SourceFileLoader
ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"
sys.path.insert(0, ROOT + "/agent"); sys.path.insert(0, ROOT + "/scripts")
from sim import GameSim

mirror_gate = float(sys.argv[1])

def build_variant(mirror_gate):
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

def build_aggressive_clone():
    # stock + uniform maker (no mirror gate split) = W3-uniform
    import zlib, base64
    loader = SourceFileLoader("aggbase", ROOT + "/topbots/main.py")
    spec = importlib.util.spec_from_loader("aggbase", loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    modules = dict(m._V44_MODULES)
    gf = modules["v44.gold_floor"]
    if "mirror_wheat_minimum_profit" not in gf:
        gf = gf.replace("mirror_minimum_expected_profit=float(config.wheat_minimum_profit)",
                        'mirror_minimum_expected_profit=float(getattr(config, "mirror_wheat_minimum_profit", config.wheat_minimum_profit))')
        gf = gf.replace("    wheat_market_maker: bool = False",
                        "    wheat_market_maker: bool = False\n    mirror_wheat_minimum_profit: float = 25.0")
        modules["v44.gold_floor"] = gf
    src = open(ROOT + "/topbots/main.py").read()
    src = re.sub(r"'wheat_market_maker': [^,}]+", "'wheat_market_maker': True", src, count=1)
    inject = ""
    for k, v in (("wheat_minimum_profit", 1.0), ("wheat_batch", 60), ("mirror_wheat_minimum_profit", 1.0)):
        if ("'" + k + "':") not in src:
            inject += ", '" + k + "': " + repr(v)
    if inject:
        src = src.replace("'terminal_rule': 'collision'", "'terminal_rule': 'collision'" + inject, 1)
    def blob(obj):
        return "(\n" + repr(base64.b85encode(zlib.compress(json.dumps(obj).encode())).decode()) + "\n)"
    endm = ')).decode("utf-8"))'
    i = src.index("_V44_MODULES = json.loads(zlib.decompress(base64.b85decode(")
    j = src.index(endm, i) + len(endm)
    src = src[:i] + "_V44_MODULES = json.loads(zlib.decompress(base64.b85decode(" + blob(modules) + ')).decode("utf-8"))' + src[j:]
    open("/tmp/_ar_clone.py", "w").write(src)

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

build_variant(mirror_gate)
build_aggressive_clone()
variant = fresh("/tmp/_ar_var.py", "varc")
clone = fresh("/tmp/_ar_clone.py", "cln")

d = []
w = 0
n = 0
for s in (1, 3, 4, 5, 19):
    for seat in (0, 1):
        sim = GameSim(seed=s)
        for _ in range(720):
            o0, o1 = sim.obs(0), sim.obs(1)
            if seat == 0:
                sim.step(call(variant, o0), call(clone, o1))
            else:
                sim.step(call(clone, o0), call(variant, o1))
        dd = sim.money(seat) - sim.money(1 - seat)
        d.append(round(dd))
        w += dd > 0
        n += 1
print(json.dumps({"w": w, "n": n, "avg": round(sum(d) / n), "per": d}))
'''

if __name__ == '__main__':
    for gate in (25.0, 12.0, 5.0, 1.0):
        r = subprocess.run([sys.executable, '-c', CHILD, str(gate)],
                           capture_output=True, text=True, timeout=900, cwd=ROOT)
        out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'ERR ' + r.stderr[-120:]
        print(f'mirror_gate={gate:5}: {out}', flush=True)
