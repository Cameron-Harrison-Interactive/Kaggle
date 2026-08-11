#!/usr/bin/env python3
"""Local test harness for the Kaggriculture agent.

Runs our bot against an opponent, replays the full episode, and audits:
  * final money
  * animal escapes (animals disappearing from the farm)
  * crops lost to weeds (plants becoming weeds without harvest)
  * peak/average crop fill
  * fertilizer produced vs sold
  * shed leftovers at turn 720 (dead inventory)

Usage:
  python3 scripts/run_local.py <our_agent.py> [opponent] [seed]
  opponent: 'starter' | 'random' | 'pass' | path to a .py
"""
import json
import sys
import time

from kaggle_environments import make


def audit(env):
    steps = env.steps
    res = {"animal_escapes": 0, "weed_outs": 0, "fert_produced": 0,
           "fert_sold": 0, "peak_crops": 0, "crop_days": [], "final_shed": {},
           "weeds_end": 0, "animals_end": 0, "hires": 0}
    prev_animals = {}
    prev_plants = set()
    for si, step in enumerate(steps):
        st = step[0]
        obs = st.get("observation", {}) or {}
        act = st.get("action", {}) or {}
        farms = obs.get("farms") or []
        if not farms:
            continue
        farm = farms[0]
        # animals
        cur = {}
        crops = 0
        weeds = 0
        for y, row in enumerate(farm.get("tiles", [])):
            for x, t in enumerate(row):
                if isinstance(t, dict):
                    if t.get("animal"):
                        cur[(x, y)] = t["animal"]
                    if t.get("kind") == "PLANT":
                        crops += 1
                    elif t.get("kind") == "WEED":
                        weeds += 1
        # escapes: animals that vanished without being sold (no animal sells exist)
        for pos, a in prev_animals.items():
            if pos not in cur:
                res["animal_escapes"] += 1
        prev_animals = cur
        # weed-outs: plant tiles that became weed tiles
        cur_plants = set()
        for y, row in enumerate(farm.get("tiles", [])):
            for x, t in enumerate(row):
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    cur_plants.add((x, y))
        for pos in prev_plants:
            t = farm["tiles"][pos[1]][pos[0]] if pos[1] < len(farm["tiles"]) else None
            if isinstance(t, dict) and t.get("kind") == "WEED":
                res["weed_outs"] += 1
        prev_plants = cur_plants
        res["peak_crops"] = max(res["peak_crops"], crops)
        res["crop_days"].append(crops)
        res["weeds_end"] = weeds
        res["animals_end"] = len(cur)
        # fertilizer accounting
        if isinstance(act, dict):
            for o in act.get("market", []) or []:
                if o and o[0] == "SELL" and o[1] == "FERTILIZER":
                    res["fert_sold"] += o[2]
                if o and o[0] == "HIRE":
                    res["hires"] += 1
        priv = obs.get("private", {}) or {}
        res["final_shed"] = priv.get("shed", {}) or {}
    res["avg_crops"] = sum(res["crop_days"]) / max(1, len(res["crop_days"]))
    return res


def main():
    our = sys.argv[1] if len(sys.argv) > 1 else "agent/main.py"
    opp = sys.argv[2] if len(sys.argv) > 2 else "starter"
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    t0 = time.time()
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([our, opp])
    dt = time.time() - t0
    final = env.steps[-1]
    p0 = final[0].reward if final[0].reward is not None else 0
    p1 = final[1].reward if final[1].reward is not None else 0
    res = audit(env)
    print(f"== {our} vs {opp} (seed {seed}) in {dt:.1f}s")
    print(f"   US ${p0:,.0f}   OPP ${p1:,.0f}   {'WIN' if p0 > p1 else 'LOSS' if p0 < p1 else 'TIE'}")
    print(f"   animal escapes : {res['animal_escapes']}   weed-outs: {res['weed_outs']}")
    print(f"   crops peak/avg : {res['peak_crops']} / {res['avg_crops']:.1f}   weeds_end: {res['weeds_end']}   animals_end: {res['animals_end']}")
    print(f"   fertilizer     : sold {res['fert_sold']}")
    print(f"   hires total    : {res['hires']}")
    shed = {k: v for k, v in res["final_shed"].items() if v}
    print(f"   shed leftovers : {shed if shed else 'EMPTY (good)'}")
    # dump replay for deeper analysis
    try:
        rp = env.toJSON()
        with open("data/last_local_replay.json", "w") as f:
            json.dump(rp, f)
    except Exception as e:
        print("   (replay dump skipped:", e, ")")
    return p0, p1, res


if __name__ == "__main__":
    main()
