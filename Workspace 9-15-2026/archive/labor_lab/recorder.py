#!/usr/bin/env python3
"""Labor-trace recorder: run an agent solo (vs PASS) on a seed, log every step's
actions + positions + compact farm state. Output feeds labor_optimizer.py.
Usage: python3 recorder.py <agent.py> <seed> <out.json>"""
import importlib.util, json, sys
from kaggle_environments import make
from kaggle_environments.core import environments

NAME = [k for k in environments if k.startswith("kagg") and "beginner" not in k][0]

def load(p):
    spec = importlib.util.spec_from_file_location("m", p)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.agent

def record(agent_path, seed, out_path):
    A = load(agent_path)
    class Pass:
        def __call__(s, obs, config=None): return {"farmer": ["PASS"], "hands": [], "market": []}
    trace = []
    def wrap(obs, config=None):
        act = A(obs, config)
        p = int(obs["player"]); farm = obs["farms"][p]
        tiles = []
        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                if t is None: tiles.append([x, y, 0])
                elif isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PLANT": tiles.append([x, y, 1, t["crop"], t.get("yield_units", 0), int(t.get("watered_today", False)), t.get("consecutive_unwatered", 0)])
                    elif "animal" in t: tiles.append([x, y, 2, t["animal"], t.get("yield_units", 0), int(t.get("fed_today", False)), int(t.get("cared_today", False))])
                    elif k == "COOP": tiles.append([x, y, 3])
                    elif k == "PASTURE": tiles.append([x, y, 4])
                    elif k == "WEED": tiles.append([x, y, 5])
        trace.append({"step": int(obs.get("step", 0)),
                      "act": {"farmer": act.get("farmer"), "hands": [list(h) for h in act.get("hands", [])]},
                      "market": act.get("market", []),
                      "pos": {"farmer": tuple(farm["farmer"]), "hands": [tuple(h) for h in farm["hands"]]},
                      "money": farm["money"], "tiles": tiles,
                      "shed": dict((obs.get("private", {}) or {}).get("shed", {}))})
        return act
    env = make(NAME, configuration={"episodeSteps": 720, "seed": seed})
    env.run([wrap, Pass()])
    final = env.steps[-1][0]["observation"]["farms"][0]["money"]
    json.dump({"seed": seed, "final": final, "trace": trace}, open(out_path, "w"))
    return final

if __name__ == "__main__":
    print(f"final ${record(sys.argv[1], int(sys.argv[2]), sys.argv[3]):,.0f}")
