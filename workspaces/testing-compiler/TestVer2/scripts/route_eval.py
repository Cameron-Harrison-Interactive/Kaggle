"""Route evaluator: replay a recorded tape in the engine, audit it, and
compare against opponents. Part of the counter-meta optimizer loop.

Usage: python3 scripts/route_eval.py [route.json] [--vs /tmp/v23_bare.py]
"""
import argparse
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from kaggle_environments import make  # noqa: E402
from run_local import audit  # noqa: E402

WRAPPER = '''
import json
_ROUTE = json.load(open(__ROUTE_PATH__))
_STEP = 0
def agent(observation, configuration):
    global _STEP
    if _STEP < len(_ROUTE):
        t = _ROUTE[_STEP]
        _STEP += 1
        n_hands = len(observation["farms"][observation["player"]].get("hands") or [])
        hands = list(t.get("hands") or [])
        while len(hands) < n_hands:
            hands.append(["PASS"])
        return {"market": t.get("market") or [], "farmer": t.get("farmer") or ["PASS"],
                "hands": hands[:n_hands]}
    return {"market": [], "farmer": ["PASS"],
            "hands": [["PASS"]] * len(observation["farms"][observation["player"]].get("hands") or [])}
'''


def make_wrapper(route_path):
    wrapper_path = os.path.join(HERE, "_tape_wrapper.py")
    with open(wrapper_path, "w") as f:
        f.write(WRAPPER.replace("__ROUTE_PATH__", repr(os.path.abspath(route_path))))
    return wrapper_path


def eval_route(route_path, seeds=(1, 2, 3), opponent=None):
    wrapper = make_wrapper(route_path)
    results = []
    for seed in seeds:
        agents = [wrapper, opponent or "starter"]
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run(agents)
        r = audit(env)
        p0 = env.steps[-1][0].reward or 0
        p1 = env.steps[-1][1].reward or 0
        results.append({
            "seed": seed, "us": p0, "opp": p1,
            "escapes": r["animal_escapes"], "weed_outs": r["weed_outs"],
            "animals_end": r["animals_end"], "peak_crops": r["peak_crops"],
            "avg_crops": round(r["avg_crops"], 1), "fert_sold": r["fert_sold"],
            "hires": r["hires"],
        })
    return results


def print_results(label, results):
    us = [r["us"] for r in results]
    opp = [r["opp"] for r in results]
    print(f"=== {label} ===")
    for r in results:
        verdict = ""
        if r["opp"] > 0:
            verdict = "WIN" if r["us"] > r["opp"] else ("tie" if r["us"] == r["opp"] else "LOSS")
        print(f"  seed {r['seed']}: us ${r['us']:,.0f} vs opp ${r['opp']:,.0f} {verdict} "
              f"| esc={r['escapes']} weeds={r['weed_outs']} anim={r['animals_end']} "
              f"peak={r['peak_crops']} avg={r['avg_crops']} fert={r['fert_sold']}")
    print(f"  MEAN: us ${statistics.mean(us):,.0f}" +
          (f" | margin ${statistics.mean(us) - statistics.mean(opp):+,.0f}" if opp[0] > 0 else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("route", nargs="?",
                    default=os.path.join(HERE, "..", "data", "counter_route.json"))
    ap.add_argument("--vs", default=None, help="opponent agent path (default: starter)")
    ap.add_argument("--seeds", default="1,2,3")
    args = ap.parse_args()
    seeds = tuple(int(x) for x in args.seeds.split(","))
    results = eval_route(args.route, seeds=seeds, opponent=args.vs)
    print_results(os.path.basename(args.route) +
                  (f" vs {os.path.basename(args.vs)}" if args.vs else " vs starter"),
                  results)
