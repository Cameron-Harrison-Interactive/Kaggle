"""Repro escape on the ACTUAL ladder seeds from the 7 escape games, engine 1.32.7."""
import sys
import importlib.util
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


# ladder seeds from escape games (from earlier pulls: 1159596537 known; others unknown
# — but the tape is deterministic vs PASS, so any seed works IF the trigger is seed-
# independent... it isn't (only 6% of games). So sweep seeds + opponents broadly.)
ours = fresh(ROOT + "/topbots/v117_FINAL.py", "o")
stock = fresh(ROOT + "/topbots/main.py", "st")

esc = 0
games = 0
for s in list(range(9, 30)) + [1159596537]:
    for opp_fn, tag in ((stock, 'stock'),):
        for seat in (0, 1):
            sim = GameSim(seed=s)
            cow21 = None
            gone = None
            for step in range(720):
                o0, o1 = sim.obs(0), sim.obs(1)
                if seat == 0:
                    a0, a1 = call(ours, o0), call(opp_fn, o1)
                else:
                    a0, a1 = call(opp_fn, o0), call(ours, o1)
                farm_obs = o0['farms'][0] if seat == 0 else o1['farms'][1]
                day = step // 24
                t = farm_obs['tiles'][1][2]
                if isinstance(t, dict) and t.get('animal') == 'COW' and cow21 is None and not t.get('fed_today') and day >= 5:
                    cow21 = day  # first unfed sighting
                if isinstance(t, dict) and t.get('animal') is None:
                    pass
                if cow21 is not None and gone is None and not (isinstance(t, dict) and t.get('animal')):
                    gone = day
                sim.step(a0, a1)
            games += 1
            if gone is not None:
                esc += 1
                print(f'seed {s} seat {seat} vs {tag}: cow21 unfed first at D{cow21}, gone D{gone}')
print(f'escapes: {esc}/{games} (engine 1.32.7, seeds 9-29 + ladder seed)')
