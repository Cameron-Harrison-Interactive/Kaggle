"""Route generator: run the counter-meta planner offline, record the action
tape + telemetry for the optimizer loop.

Usage: python3 scripts/route_gen.py [--out data/counter_route_v1.json]
"""
import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from kaggle_environments import make  # noqa: E402


def load_planner(path, name="planner"):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PASS_AGENT = """
def agent(observation, configuration):
    return {"market": [], "farmer": ["PASS"], "hands": [["PASS"]] * len(observation["farms"][observation["player"]].get("hands") or [])}
"""


def scan(farm):
    plants = weeds = pastures = animals = unfed = 0
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict):
                if "animal" in t:
                    animals += 1
                    if not t.get("fed_today"):
                        unfed += 1
                elif t.get("kind") == "PLANT":
                    plants += 1
                elif t.get("kind") == "WEED":
                    weeds += 1
                elif t.get("kind") == "PASTURE":
                    pastures += 1
    return plants, weeds, pastures, animals, unfed


def generate(seed=1, planner_path=None, out_path=None, report_path=None):
    planner_path = planner_path or os.path.join(HERE, "counter_meta.py")
    out_path = out_path or os.path.join(HERE, "..", "data", "counter_route.json")
    report_path = report_path or out_path.replace(".json", "_report.json")
    planner = load_planner(planner_path)

    tape = []
    telemetry = {"days": [], "events": []}

    with open(os.path.join(HERE, "_pass_agent.py"), "w") as f:
        f.write(PASS_AGENT)

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})

    prev = {"seeds": None, "shed": None, "money": None}

    def recording_agent(obs, config):
        act = planner.agent(obs, config)
        # record tape entry
        tape.append({
            "market": [list(o) for o in (act.get("market") or [])],
            "farmer": list(act.get("farmer") or ["PASS"]),
            "hands": [list(h) for h in (act.get("hands") or [])],
        })
        # telemetry at end of each day
        if obs.get("hour") == 23:
            p = obs["player"]
            farm = obs["farms"][p]
            priv = obs["private"]
            plants, weeds, pastures, animals, unfed = scan(farm)
            telemetry["days"].append({
                "day": obs["day"],
                "money": farm["money"],
                "hands": len(farm.get("hands") or []),
                "plants": plants, "weeds": weeds, "pastures": pastures,
                "animals": animals, "unfed": unfed,
                "shed_wheat": priv["shed"].get("WHEAT", 0),
                "seeds_wheat": priv["seeds"].get("WHEAT", 0),
                "quads": len(farm.get("unlocked_quadrants") or []),
            })
        return act

    env.run([recording_agent, os.path.join(HERE, "_pass_agent.py")])
    reward = env.steps[-1][0].reward or 0

    # audit-style postprocessing
    weed_outs = escapes = 0
    try:
        from run_local import audit
        r = audit(env)
        weed_outs = r["weed_outs"]
        escapes = r["animal_escapes"]
    except Exception:
        pass

    report = {
        "seed": seed,
        "reward": reward,
        "weed_outs": weed_outs,
        "escapes": escapes,
        "turns": len(tape),
        "days": telemetry["days"],
    }

    with open(out_path, "w") as f:
        json.dump(tape, f)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=1)

    print(f"route recorded: {len(tape)} turns -> {out_path}")
    print(f"reward: ${reward:,.0f} | weed_outs: {weed_outs} | escapes: {escapes}")
    return tape, report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--planner", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    generate(seed=args.seed, planner_path=args.planner, out_path=args.out,
             report_path=(args.out.replace(".json", "_report.json") if args.out else None))
