import importlib.util, json, glob
from kaggle_environments import make
from kaggle_environments.core import environments
NAME = [k for k in environments if k.startswith("kagg") and "beginner" not in k][0]
WS = open("/tmp/ws").read().strip()

def load_router(name, forced=None):
    """Load the router; if forced={block: tape}, replace trees with forced leaves."""
    spec = importlib.util.spec_from_file_location(name, WS + "/topbots/tt_router_938.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    if forced:
        trees = []
        for b in range(5):
            t = forced.get(b)
            trees.append([[-1, -1, -1, (t if t is not None else mod._TREES[b][0][3]), -1]])
        mod._TREES = trees
    fn = getattr(mod, "kaggle_entry_agent", None) or mod.agent
    return lambda obs, config=None: fn(obs, config)

def load_fn(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    fn = getattr(mod, "kaggle_entry_agent", None) or getattr(mod, "agent")
    return lambda obs, config=None: fn(obs, config)

class Tape:
    def __init__(s, t): s.t = t; s.i = 0
    def __call__(s, obs, config=None):
        a = s.t[s.i] if s.i < len(s.t) else {"farmer": [], "hands": [], "market": []}
        s.i += 1; return a

def load_tape_agent(rec):
    t = Tape(rec["tape"])
    return t

OPPONENTS = {
    "router": lambda: load_router("opp_router"),
    "v16":    lambda: load_fn(WS + "/topbots/tetsu_r5_v16_premium.py", "opp_v16"),
    "hamburger": lambda: load_fn(WS + "/topbots/poolsrc/hamburger.py", "opp_hb"),
}
# tape opponents (strong forks + elites) - load from workspace tapes
for f, key in ((WS + "/analysis/loss_tapes/106047657.json", "JOSHNA"),):
    OPPONENTS[key] = (lambda rec: (lambda: load_tape_agent(rec)))(json.load(open(f)))
for f in sorted(glob.glob(WS + "/analysis/elite_tapes/keiz_*.json"))[:1]:
    OPPONENTS["keiz-tape"] = (lambda rec: (lambda: load_tape_agent(rec)))(json.load(open(f)))
for f in sorted(glob.glob(WS + "/analysis/elite_tapes/Crop_Dusta_*.json"))[:1]:
    OPPONENTS["CD-tape"] = (lambda rec: (lambda: load_tape_agent(rec)))(json.load(open(f)))

CONDITIONS = {"baseline": None}
for tape in range(5):
    CONDITIONS[f"lock{tape}"] = {1: tape, 2: tape, 3: tape, 4: tape}

SEEDS = [201, 202, 203, 204]
import sys
only = sys.argv[1] if len(sys.argv) > 1 else None
results = []
for cond, forced in CONDITIONS.items():
    if only and cond != only: continue
    for oname, mk in OPPONENTS.items():
        wins = losses = ties = 0; marg = 0
        for seed in SEEDS:
            us = load_router(f"us_{cond}_{oname}_{seed}", forced)
            opp = mk()
            s = seed % 2
            pair = [None, None]; pair[s] = us; pair[1 - s] = opp
            env = make(NAME, configuration={"episodeSteps": 720, "seed": seed})
            env.run(pair)
            a = env.steps[-1][s]["reward"] or 0
            b = env.steps[-1][1 - s]["reward"] or 0
            if a > b: wins += 1
            elif b > a: losses += 1
            else: ties += 1
            marg += a - b
        rec = {"cond": cond, "opp": oname, "W": wins, "L": losses, "T": ties, "margin": marg}
        results.append(rec)
        print(f"{cond:8s} vs {oname:10s}: {wins}W-{losses}L-{ties}T margin {marg:+9,.0f}", flush=True)
json.dump(results, open(f"/tmp/train_{only or 'all'}.json", "w"))
print("saved")
