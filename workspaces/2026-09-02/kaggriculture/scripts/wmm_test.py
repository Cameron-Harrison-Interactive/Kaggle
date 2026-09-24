"""Activate the dormant wheat MarketMakerExpert and read its telemetry.

Builds a V46 variant with patched config, plays games, then extracts the
agent closure's telemetry (which gate blocked entries: edge/slot/capacity/
cash) plus game results.
"""
import sys, json, re, zlib, base64, importlib.util, subprocess
from importlib.machinery import SourceFileLoader

ROOT = '/home/user/kaggriculture'

BUILD = r'''
import sys, json, re, importlib.util
from importlib.machinery import SourceFileLoader
sys.path.insert(0, "/home/user/kaggressue/agent".replace("kaggressue", "kaggriculture"))
sys.path.insert(0, "/home/user/kaggressue".replace("kaggressue", "kaggriculture"))
sys.path.insert(0, "/home/user/kaggressue/scripts".replace("kaggressue", "kaggriculture"))
from sim import GameSim

patch = json.loads(sys.argv[1])
src = open("/home/user/kaggressue/topbots/main.py".replace("kaggressue", "kaggriculture")).read()
inject = {k: v for k, v in patch.items() if ("'" + k + "':") not in src}
for k, v in patch.items():
    if k in inject: continue
    src, n = re.subn(r"('" + k + r"': )([^,}]+)", lambda mm, v=v: mm.group(1) + repr(v), src, count=1)
    assert n == 1, f"patch {k} failed"
if inject:
    extra = "".join(", '" + k + "': " + repr(v) for k, v in inject.items())
    src = src.replace("'wheat_market_maker': True", "'wheat_market_maker': True" + extra, 1)
    if "'wheat_market_maker': True" not in src:
        src = src.replace("'wheat_market_maker': False", "'wheat_market_maker': True" + extra, 1)
open("/tmp/_wmm_variant.py", "w").write(src)

loader = SourceFileLoader("wmm", "/tmp/_wmm_variant.py")
spec = importlib.util.spec_from_loader("wmm", loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
agent = m.agent

def call(fn, o):
    try: return fn(o, None)
    except TypeError: return fn(o)

# fresh stock for mirror
for k in [k for k in list(sys.modules) if k.split(".")[0] in ("v19","v23","v24","v44","v48","scripts")]:
    del sys.modules[k]
loader2 = SourceFileLoader("wstock", "/home/user/kaggressue/topbots/main.py".replace("kaggressue", "kaggriculture"))
spec2 = importlib.util.spec_from_loader("wstock", loader2)
m2 = importlib.util.module_from_spec(spec2)
loader2.exec_module(m2)
stock = m2.agent

def game(fa, fb, seed):
    sim = GameSim(seed=seed)
    for _ in range(720):
        o0, o1 = sim.obs(0), sim.obs(1)
        sim.step(call(fa, o0), call(fb, o1))
    return sim.money(0), sim.money(1)

solo = [round(game(agent, lambda o, c=None: {"farmer": ["PASS"], "hands": [], "market": []}, s)[0]) for s in (1, 2)]
mir = [game(agent, stock, s) for s in (1, 2)]

# telemetry from agent closure
def find_in_closure(fn, pred, depth=0, seen=None):
    if seen is None: seen = set()
    if id(fn) in seen or depth > 6: return None
    seen.add(id(fn))
    cl = getattr(fn, "__closure__", None) or []
    for c in cl:
        try: v = c.cell_contents
        except Exception: continue
        if pred(v): return v
        if callable(v):
            r = find_in_closure(v, pred, depth + 1, seen)
            if r is not None: return r
    return None

makers = find_in_closure(m._V44_POLICY, lambda v: isinstance(v, dict) and "default" in v and hasattr(v.get("default"), "telemetry"))
tele = {}
if makers:
    for name, mk in makers.items():
        t = getattr(mk, "telemetry", None)
        if t: tele[name] = {k: t.get(k) for k in ("entries", "entry_units", "edge_blocks", "slot_blocks", "capacity_blocks", "cash_blocks", "mirror_entries")} 
outer = find_in_closure(m._V44_POLICY, lambda v: isinstance(v, dict) and "market_maker_changed_turns" in v) or {}
tele["outer_changed_turns"] = outer.get("market_maker_changed_turns")
print(json.dumps({"solo": solo, "mirror": [[round(a), round(b)] for a, b in mir], "tele": tele}))
'''

jobs = [
    ('W1 maker on (defaults)', {'wheat_market_maker': True}),
    ('W2 + profit gate 1.0', {'wheat_market_maker': True, 'wheat_minimum_profit': 1.0}),
    ('W3 + batch 60', {'wheat_market_maker': True, 'wheat_minimum_profit': 1.0, 'wheat_batch': 60}),
    ('W4 + start 72', {'wheat_market_maker': True, 'wheat_minimum_profit': 1.0, 'wheat_batch': 60, 'wheat_start_step': 72}),
    ('W5 W3+exposure', {'wheat_market_maker': True, 'wheat_minimum_profit': 1.0, 'wheat_batch': 60, 'exposure_preempt': True}),
]
for label, patch in jobs:
    r = subprocess.run([sys.executable, '-c', BUILD, json.dumps(patch)],
                       capture_output=True, text=True, timeout=600, cwd=ROOT)
    out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'ERR ' + r.stderr[-150:]
    print(f'{label:24} {out}', flush=True)
print('(stock reference: solo 176813/185745; mirror ~equal)')
