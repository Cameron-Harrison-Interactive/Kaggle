"""Solo-ladder a list of bot files (seeds 10007-16 x both seats).

Usage: python3 scripts/run_variant_ladder.py topbots/v7v_W1a.py [more.py ...]
"""
import importlib.util
import os
import statistics
import sys

sys.path.insert(0, "scripts")
os.chdir(open("/tmp/ws").read().strip())
from kaggle_environments import make

ENV = "kagg" + "riculture"


def pass_agent(obs, config=None):
    return {"farmer": ["PASS"], "hands": [], "market": []}


def load(path):
    spec = importlib.util.spec_from_file_location("m_" + os.path.basename(path)[:-3], path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.agent


def ladder(agent):
    scores = []
    for seed in range(10007, 10017):
        for seat in (0, 1):
            env = make(ENV, configuration={"episodeSteps": 720, "seed": seed})
            env.run([agent, pass_agent] if seat == 0 else [pass_agent, agent])
            scores.append(env.steps[-1][seat]["reward"])
    return statistics.mean(scores), min(scores), max(scores)


if __name__ == "__main__":
    for path in sys.argv[1:]:
        agent = load(path)
        mean, mn, mx = ladder(agent)
        print(f"{os.path.basename(path):32s} MEAN ${mean:>9,.0f}  MIN ${mn:>9,.0f}  MAX ${mx:>9,.0f}",
              flush=True)
