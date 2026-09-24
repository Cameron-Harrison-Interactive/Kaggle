"""Process-isolated game runner: one (version, opponent, seed, seat) game
per python process, so engine module state can never leak between games.

Usage: run_isolated.py <version> <opponent> <seed> <seat>
  version: v119 | v1110 | v46
  opponent: v119 | v1110 | v46 | k2900 | moon | soil | bt | pass | ghost:<eid>:<oppseat>
Prints: final cash for our version (seat) and the opponent.
"""
import json, sys, os, importlib.util

WS = "/home/user/WorkSpace 8-27-2026/kaggriculture"
sys.path.insert(0, os.path.join(WS, "scripts"))
sys.path.insert(0, os.path.join(WS, "agent"))
from sim import GameSim
from importlib.machinery import SourceFileLoader

VERSIONS = {
    "v119": os.path.join(WS, "main.py"),
    "v1110": os.path.join(WS, "topbots/v1110_feedrescue.py"),
    "v46": os.path.join(WS, "topbots/main.py"),
    "k2900": os.path.join(WS, "agent/v41_kaito.py"),
    "moon": os.path.join(WS, "agent/moon.py"),
    "soil": os.path.join(WS, "agent/soil.py"),
    "bt": os.path.join(WS, "agent/breaking_tie.py"),
}

def load(path, name):
    before = dict(sys.modules)
    loader = SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    # purge modules this file registered (v44.*, scripts.*, v23.*, v24.*) so
    # the next engine load gets fresh copies — the agent closures keep their
    # own module instances alive.
    for k in list(sys.modules):
        if k not in before:
            del sys.modules[k]
    return m.agent

def call(fn, obs):
    try:
        return fn(obs, None)
    except TypeError:
        return fn(obs)

def make_pass():
    def pass_agent(obs):
        farm = (obs.get("farms") or [{}])[obs.get("player", 0)]
        n = len(farm.get("hands") or [])
        return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}
    return pass_agent

def make_ghost(eid, opp_seat):
    d = json.load(open(f"/tmp/eps2/episode-{eid}-replay.json"))
    steps = d['steps']
    tape = [steps[i][opp_seat]['action'] or {} for i in range(len(steps))]
    class G:
        def __call__(self, obs):
            s = int(obs.get("step", 0))
            farm = (obs.get("farms") or [{}])[obs.get("player", 0)]
            n = len(farm.get("hands") or [])
            if not (0 <= s < len(tape)):
                return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}
            a = tape[s]
            h = list(a.get("hands") or [])
            while len(h) < n:
                h.append(["PASS"])
            h = h[:n]
            return {"farmer": list(a.get("farmer") or ["PASS"]), "hands": h,
                    "market": list(a.get("market") or [])}
    return G()

def main():
    version, opponent, seed, seat = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    fn = load(VERSIONS[version], "agent_" + version)
    if opponent == "pass":
        opp = make_pass()
    elif opponent.startswith("ghost:"):
        parts = opponent.split(":")
        opp = make_ghost(parts[1], int(parts[2]))
    else:
        opp = load(VERSIONS[opponent], "opp_" + opponent)
    sim = GameSim(seed=seed)
    known = {}
    escapes = []
    for si in range(720):
        o0, o1 = sim.obs(0), sim.obs(1)
        if seat == 0:
            a0, a1 = call(fn, o0), call(opp, o1)
        else:
            a0, a1 = call(opp, o0), call(fn, o1)
        sim.step(a0, a1)
        o = sim.obs(seat)
        farm = o['farms'][seat]
        now = {}
        for y, row in enumerate(farm['tiles']):
            for x, t in enumerate(row):
                if isinstance(t, dict) and t.get('animal'):
                    now[(x, y)] = t['animal']
        for pos in list(known):
            if pos not in now:
                known.pop(pos)
                escapes.append(si // 24)
        for pos in now:
            known.setdefault(pos, True)
    o = sim.obs(seat)
    shed = {k: v for k, v in (o['private']['shed'] or {}).items() if v}
    animals = {}
    for row in o['farms'][seat]['tiles']:
        for t in row:
            if isinstance(t, dict) and t.get('animal'):
                animals[t['animal']] = animals.get(t['animal'], 0) + 1
    o1 = sim.obs(1 - seat)
    print(json.dumps({"cash": sim.money(seat), "opp_cash": sim.money(1 - seat),
                      "herd": animals, "shed": shed, "escapes": escapes}))

if __name__ == "__main__":
    main()
