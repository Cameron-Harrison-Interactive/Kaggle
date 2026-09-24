"""Reproduce the (2,1) cow escape locally: v11.6/v11.7 vs stock and vs
maker-clone, tracking tile (2,1) daily + wheat shed at D5-D6 feed hours."""
import sys
import json
import re
import importlib.util
import zlib
import base64
from importlib.machinery import SourceFileLoader

ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"
sys.path.insert(0, ROOT + "/agent")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/scripts")

from sim import GameSim


def load(path, name):
    loader = SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m.agent


def call(fn, o):
    try:
        return fn(o, None)
    except TypeError:
        return fn(o)


def fresh(path, name):
    for k in [k for k in list(sys.modules) if k.split(".")[0] in ("v19", "v23", "v24", "v44", "v48", "scripts")]:
        del sys.modules[k]
    return load(path, name)


def build_clone():
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
    open("/tmp/_esc_clone.py", "w").write(src)


def run_pair(ours, theirs, seeds, label):
    esc = 0
    details = []
    for s in seeds:
        for seat in (0, 1):
            sim = GameSim(seed=s)
            cow21 = None
            gone = None
            wheat_low = []
            for step in range(720):
                o0, o1 = sim.obs(0), sim.obs(1)
                a0 = call(ours, o0) if seat == 0 else call(theirs, o0)
                a1 = call(theirs, o1) if seat == 0 else call(ours, o1)
                farm_obs = o0['farms'][0] if seat == 0 else o1['farms'][1]
                day = step // 24
                t = farm_obs['tiles'][1][2] if len(farm_obs['tiles']) > 1 else None
                if isinstance(t, dict) and t.get('animal') == 'COW' and cow21 is None:
                    cow21 = day
                if cow21 is not None and gone is None and not (isinstance(t, dict) and t.get('animal') == 'COW') and day > cow21:
                    gone = day
                if day in (5, 6):
                    shed = (o0 if seat == 0 else o1)['private']['shed']
                    wheat_low.append((step, shed.get('WHEAT', 0)))
                sim.step(a0, a1)
            if gone is not None:
                esc += 1
                zero_w = [w for (_, w) in wheat_low if w == 0]
                details.append((s, seat, f'placedD{cow21} goneD{gone} zeroWheatHours={len(zero_w)}/48'))
    print(f'{label}: escapes {esc}/{len(seeds) * 2} games')
    for d in details:
        print('   ', d)


ours117 = fresh(ROOT + "/topbots/v117_FINAL.py", "o117")
stock = fresh(ROOT + "/topbots/main.py", "st")
build_clone()
clone = fresh("/tmp/_esc_clone.py", "cl")

run_pair(ours117, stock, list(range(1, 9)), 'v11.7 vs stock seeds 1-8')
run_pair(ours117, clone, list(range(1, 9)), 'v11.7 vs maker-clone seeds 1-8')
