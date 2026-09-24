"""V46 config sweep: mirror vs stock V46 + guard vs BT.

Each variant patches one config knob in the exposed _V44_CONFIG dict,
then plays 4 seeds x 2 seats vs stock V46 (mirror margin = ladder Elo in
this family-heavy meta) and 2 seeds x 2 seats vs BT (guard the anti-BT
edge). One subprocess per variant (packaged payloads collide in
sys.modules otherwise).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V46_SRC = os.path.join(ROOT, 'topbots', 'main.py')

CHILD = r'''
import sys, json, re, importlib.util
from importlib.machinery import SourceFileLoader
sys.path.insert(0, '/home/user/kaggriculture/agent')
sys.path.insert(0, '/home/user/kaggriculture')
sys.path.insert(0, '/home/user/kaggressue' if False else '/home/user/kaggriculture/scripts')
from sim import GameSim
import breaking_tie as BT

patch = json.loads(sys.argv[1])
src = open('/home/user/kaggriculture/topbots/main.py').read()
if patch:
    for k, v in patch.items():
        # replace '"k": <old>' inside the _V44_CONFIG dict literal
        pat = re.compile(r"('" + k + r"': )([^,}]+)")
        src, n = pat.subn(lambda mm: mm.group(1) + repr(v), src, count=1)
        if n != 1:
            print(json.dumps({'error': f'patch {k} failed'})); sys.exit(0)

def load(name, code):
    loader = SourceFileLoader(name, '/tmp/_sweep_' + name + '.py')
    open(loader.path, 'w').write(code)
    spec = importlib.util.spec_from_loader(name, loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m.agent

def call(fn, obs):
    try: return fn(obs, None)
    except TypeError: return fn(obs)

variant = load('variant', src)
stock = load('stock', open('/home/user/kaggriculture/topbots/main.py').read())

def h2h(fa, fb, seeds):
    d = 0; wins = 0; n = 0
    for seed in seeds:
        for seat in (0, 1):
            sim = GameSim(seed=seed)
            for _ in range(720):
                o0, o1 = sim.obs(0), sim.obs(1)
                if seat == 0:
                    sim.step(call(fa, o0), call(fb, o1))
                else:
                    sim.step(call(fb, o0), call(fa, o1))
            v = sim.money(seat); o = sim.money(1 - seat)
            d += v - o; wins += v > o; n += 1
    return wins, n, d / n

mw, mn, md = h2h(variant, stock, (1, 2, 3, 4))
bw, bn, bd = h2h(variant, BT.agent, (1, 2))
print(json.dumps({'mirror': [mw, mn, round(md)], 'vsBT': [bw, bn, round(bd)]}))
'''


def run_variant(label, patch):
    r = subprocess.run([sys.executable, '-c', CHILD, json.dumps(patch)],
                       capture_output=True, text=True, timeout=900,
                       cwd=ROOT)
    out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else '{}'
    try:
        res = json.loads(out)
    except Exception:
        res = {'error': r.stderr[-120:]}
    print(f'{label:44} mirror={res.get("mirror")} vsBT={res.get("vsBT")} {res.get("error", "")}', flush=True)


VARIANTS = [
    ('stock baseline (sanity)', {}),
    ('exposure_preempt=True', {'exposure_preempt': True}),
    ('wheat_market_maker=True', {'wheat_market_maker': True}),
    ('bakery_capital_maximum_geese=4', {'bakery_capital_maximum_geese': 4}),
    ('yarn_third_start=180', {'yarn_third_start': 180}),
    ('clone_detection_start=24', {'clone_detection_start': 24}),
    ('clone_streak_required=12', {'clone_streak_required': 12}),
    ('aligned_reorder=False', {'aligned_reorder': False}),
]

if __name__ == '__main__':
    for label, patch in VARIANTS:
        run_variant(label, patch)
