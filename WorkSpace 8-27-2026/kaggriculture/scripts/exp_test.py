"""Sweep wheat-maker knobs on the W9 asymmetric base. One subprocess per variant."""
import json
import subprocess
import sys

CHILD = r'''
import sys, json, re, importlib.util, zlib, base64
from importlib.machinery import SourceFileLoader

BASE = "/home/user/kaggriculture"
sys.path.insert(0, BASE + "/agent")
sys.path.insert(0, BASE)
sys.path.insert(0, BASE + "/scripts")

from sim import GameSim
import breaking_tie as BT

patch = json.loads(sys.argv[1])

loader = SourceFileLoader("basemod", BASE + "/topbots/main.py")
spec = importlib.util.spec_from_loader("basemod", loader)
bm = importlib.util.module_from_spec(spec)
loader.exec_module(bm)

modules = dict(bm._V44_MODULES)
gf = modules["v44.gold_floor"]
if "mirror_wheat_minimum_profit" not in gf:
    gf = gf.replace(
        "mirror_minimum_expected_profit=float(config.wheat_minimum_profit)",
        'mirror_minimum_expected_profit=float(getattr(config, "mirror_wheat_minimum_profit", config.wheat_minimum_profit))',
    )
    gf = gf.replace(
        "    wheat_market_maker: bool = False",
        "    wheat_market_maker: bool = False\n    mirror_wheat_minimum_profit: float = 25.0",
    )
    modules["v44.gold_floor"] = gf

src = open(BASE + "/topbots/main.py").read()
cfg = {"wheat_market_maker": True, "wheat_minimum_profit": 1.0, "wheat_batch": 60}
cfg.update(patch)
src = re.sub(r"'wheat_market_maker': [^,}]+", "'wheat_market_maker': True", src, count=1)
inject = "".join(", '" + k + "': " + repr(v) for k, v in cfg.items() if ("'" + k + "':") not in src)
if inject:
    src = src.replace("'terminal_rule': 'collision'", "'terminal_rule': 'collision'" + inject, 1)


def blob(obj):
    b85 = base64.b85encode(zlib.compress(json.dumps(obj).encode())).decode()
    return "(\n" + repr(b85) + "\n)"


endm = ')).decode("utf-8"))'
i = src.index("_V44_MODULES = json.loads(zlib.decompress(base64.b85decode(")
j = src.index(endm, i) + len(endm)
src = src[:i] + "_V44_MODULES = json.loads(zlib.decompress(base64.b85decode(" + blob(modules) + endm + src[j:]
open("/tmp/_sw_var.py", "w").write(src)

for k in [k for k in list(sys.modules) if k.split(".")[0] in ("v19", "v23", "v24", "v44", "v48", "scripts", "basemod")]:
    del sys.modules[k]

ld = SourceFileLoader("varmod", "/tmp/_sw_var.py")
sp = importlib.util.spec_from_loader("varmod", ld)
m = importlib.util.module_from_spec(sp)
ld.exec_module(m)
var = m.agent

ld2 = SourceFileLoader("stmod", BASE + "/topbots/main.py")
sp2 = importlib.util.spec_from_loader("stmod", ld2)
m2 = importlib.util.module_from_spec(sp2)
ld2.exec_module(m2)
stock = m2.agent


def call(fn, o):
    try:
        return fn(o, None)
    except TypeError:
        return fn(o)


solo = []
for s in (3, 4, 5):
    sim = GameSim(seed=s)
    for _ in range(720):
        o0, o1 = sim.obs(0), sim.obs(1)
        sim.step(call(var, o0), {"farmer": ["PASS"], "hands": [], "market": []})
    solo.append(round(sim.money(0)))

mir = []
for s in (3, 4, 19, 29, 5):
    a_ = 0.0
    b_ = 0.0
    for seat in (0, 1):
        sim = GameSim(seed=s)
        for _ in range(720):
            o0, o1 = sim.obs(0), sim.obs(1)
            if seat == 0:
                sim.step(call(var, o0), call(stock, o1))
            else:
                sim.step(call(stock, o0), call(var, o1))
        a_ += sim.money(seat)
        b_ += sim.money(1 - seat)
    mir.append(round(a_ - b_))

bt = []
for s in (1, 2, 19):
    a_ = 0.0
    b_ = 0.0
    for seat in (0, 1):
        sim = GameSim(seed=s)
        for _ in range(720):
            o0, o1 = sim.obs(0), sim.obs(1)
            if seat == 0:
                sim.step(call(var, o0), call(BT.agent, o1))
            else:
                sim.step(call(BT.agent, o0), call(var, o1))
        a_ += sim.money(seat)
        b_ += sim.money(1 - seat)
    bt.append(round(a_ - b_))

print(json.dumps({"solo": solo, "mirror": mir, "bt": bt}))
'''

VARIANTS = [
    ('W9+exposure(0.80)', {'exposure_preempt': True}),
    ('W9+exposure(0.60)', {'exposure_preempt': True, 'exposure_minimum_price_ratio': 0.60}),
    ('W9+exposure(0.45)', {'exposure_preempt': True, 'exposure_minimum_price_ratio': 0.45}),
]

if __name__ == '__main__':
    for label, patch in VARIANTS:
        r = subprocess.run([sys.executable, '-c', CHILD, json.dumps(patch)],
                           capture_output=True, text=True, timeout=900,
                           cwd='/home/user/kaggriculture')
        out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'ERR ' + r.stderr[-120:]
        print(f'{label:26} {out}', flush=True)
    print('(stock solo: 188863/152001/165520 | W9 mirror: [+303,0,0,0,+404] | W9 BT(1,2,3,5,19): +9145)')
