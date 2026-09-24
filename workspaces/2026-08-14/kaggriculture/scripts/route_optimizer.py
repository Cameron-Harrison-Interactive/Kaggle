#!/usr/bin/env python3
"""Route Optimizer — the local route scanner you asked for.

Finds the best route by:
  1. Recording the base tape (v18 vs PASS) — labor actions are seed-invariant,
     so one recording generalizes to all seeds.
  2. Telemetry pass: walk games and find every idle PASS where a worker is
     standing on a dry crop (CU>=1) -> patch to WATER, or on an empty tile
     that the route revisits -> patch to PLANT (timing-safe: worker never
     moves, so the 719-step choreography is preserved).
  3. Greedy + beam search over patch sets, testing each candidate tape vs
     opponents (v18 mirror, Build-A proxy, tetsu) on multiple seeds.
  4. Saves the best tape + a report.

Usage:
  python3 scripts/route_optimizer.py --rounds 5 --seeds 1,2,3 \
      --opp v18 --out data/tapes_opt/route_opt_seat0.json

  --opp v18|builda|tetsu|all   (which opponent to train against)

Run on your local machine for a big search (each match ~7s):
  python3 scripts/route_optimizer.py --rounds 20 --seeds 1,2,3,4,5 --seat 0 --opp all
  python3 scripts/route_optimizer.py --rounds 20 --seeds 1,2,3,4,5 --seat 1 --opp all

Caveat: only TIMING-SAFE patches are tried (PASS -> WATER / PASS -> PLANT).
Full coverage (the 62-vs-52-crops gap vs mirror clones) needs MOVE-level
recompilation, which desyncs the tape and has failed keep-gate every time it
was tried (see COVERAGE_ANALYSIS.md). The optimizer will report honestly if
no safe patch improves the score.
"""
import argparse
import importlib.util
import json
import os
import random
import sys
import time
from collections import defaultdict

from kaggle_environments import make

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

BASE_TAPE_SEED = 1


def load_v18(path):
    spec = importlib.util.spec_from_file_location("v18", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._weed_repair_action = lambda obs, action, actions, step: action
    return mod


def record_base(seed, seat):
    """Record v18 vs PASS for one seat."""
    mod = load_v18(os.path.join(ROOT, "submit", "main.py"))
    pass_agent = lambda obs, c: {"market": [], "farmer": ["PASS"],
                                 "hands": [["PASS"]] * len(obs["farms"][obs["player"]].get("hands") or [])}
    tape = []

    def rec(obs, config):
        act = mod.agent(obs, config)
        tape.append({"market": [list(o) for o in (act.get("market") or [])],
                     "farmer": list(act.get("farmer") or ["PASS"]),
                     "hands": [list(h) for h in (act.get("hands") or [])]})
        return act

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    if seat == 0:
        env.run([rec, pass_agent])
    else:
        env.run([pass_agent, rec])
    return tape


def telemetry(seed, seat, mod):
    """Walk the game and record (step, worker, pos, tile-state) + PASS candidates."""
    pass_agent = lambda obs, c: {"market": [], "farmer": ["PASS"],
                                 "hands": [["PASS"]] * len(obs["farms"][obs["player"]].get("hands") or [])}
    candidates_w = []   # (step, worker_idx, x, y, cu) PASS on dry crop
    candidates_p = []   # (step, worker_idx, x, y) PASS on empty tile
    visits = defaultdict(list)  # (x,y) -> [step,...] worker stood here
    tiles_seen = {}

    def rec(obs, config):
        step = int(obs.get("step", 0) or 0)
        act = mod.agent(obs, config)
        farm = obs["farms"][seat]
        tiles = farm.get("tiles") or []
        positions = [farm.get("farmer"), *list(farm.get("hands") or [])]
        unit_actions = [act.get("farmer"), *list(act.get("hands") or [])]
        for wi, (pos, ua) in enumerate(zip(positions, unit_actions)):
            if not pos:
                continue
            try:
                x, y = int(pos[0]), int(pos[1])
            except Exception:
                continue
            visits[(x, y)].append(step)
            op = ua[0] if isinstance(ua, list) and ua else "PASS"
            if op != "PASS":
                continue
            try:
                tile = tiles[y][x]
            except Exception:
                continue
            if tile is None:
                candidates_p.append((step, wi, x, y))
            elif isinstance(tile, dict) and tile.get("kind") == "PLANT":
                cu = tile.get("consecutive_unwatered", 0)
                if not tile.get("watered_today") and cu >= 1:
                    candidates_w.append((step, wi, x, y, cu))
        return act

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    if seat == 0:
        env.run([rec, pass_agent])
    else:
        env.run([pass_agent, rec])
    return candidates_w, candidates_p, visits


def make_tape_agent(tape, mod):
    def agent(obs, configuration=None):
        seat = mod._seat(obs)
        actions = tape
        step = min(max(0, int(mod._get(obs, "step", 0) or 0)), len(actions) - 1)
        try:
            mod._update_memory(obs)
            action = mod._weed_repair_action(obs, mod._copy_action(actions[step]), actions, step)
            action = mod._adapt_animals(obs, action)
            action = mod._adapt_crops(obs, action)
            action = mod._adapt_market(obs, action)
            return mod._align_hands(mod._rank_sell_slots(obs, action, configuration), obs)
        except Exception:
            farm = mod._farm(obs, mod._seat(obs))
            return {"farmer": ["PASS"],
                    "hands": [["PASS"]] * len(mod._get(farm, "hands", []) or []),
                    "market": []}
    return agent


def load_opp(name):
    if name == "v18":
        mod = load_v18(os.path.join(ROOT, "submit", "main.py"))
        return mod.agent
    if name == "builda":
        spec = importlib.util.spec_from_file_location("opp", os.path.join(ROOT, "scripts", "opp_seb.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.agent
    if name == "tetsu":
        spec = importlib.util.spec_from_file_location("opp", os.path.join(ROOT, "opponents", "tetsu_main.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.agent
    raise ValueError(name)


def battle(agent_a, agent_b, seed, seat):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    if seat == 0:
        env.run([agent_a, agent_b])
        return env.steps[-1][0].reward or 0, env.steps[-1][1].reward or 0
    else:
        env.run([agent_b, agent_a])
        return env.steps[-1][1].reward or 0, env.steps[-1][0].reward or 0


def score_tape(tape, mod, opp_agent, seeds, seats):
    agent = make_tape_agent(tape, mod)
    total = 0
    for seed in seeds:
        for seat in seats:
            a, b = battle(agent, opp_agent, seed, seat)
            total += a - b
    return total


def apply_patch(tape, step, worker, new_action):
    t = json.loads(json.dumps(tape))
    if worker == "farmer":
        t[step]["farmer"] = list(new_action)
    else:
        hands = t[step].get("hands") or []
        while len(hands) <= worker:
            hands.append(["PASS"])
        hands[worker] = list(new_action)
        t[step]["hands"] = hands
    return t


def ensure_seeds(tape, crop, n):
    """Add a BUY_SEED order for crop at step 0 market if room."""
    t = json.loads(json.dumps(tape))
    mkt = t[0].get("market") or []
    if len(mkt) < 10:
        mkt = [list(o) for o in mkt] + [["BUY_SEED", crop, n]]
        t[0]["market"] = mkt[:10]
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--seeds", default="1,2,3")
    ap.add_argument("--seat", type=int, default=0)
    ap.add_argument("--opp", default="v18", choices=["v18", "builda", "tetsu", "all"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]
    seat = args.seat
    out = args.out or os.path.join(ROOT, "data", "tapes_opt", f"route_opt_seat{seat}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    mod = load_v18(os.path.join(ROOT, "submit", "main.py"))
    print(f"[opt] recording base tape seat{seat} seed{BASE_TAPE_SEED}...", flush=True)
    base = record_base(BASE_TAPE_SEED, seat)
    print(f"[opt] base tape {len(base)} steps", flush=True)

    print(f"[opt] telemetry pass (seed {BASE_TAPE_SEED})...", flush=True)
    cw, cp, visits = telemetry(BASE_TAPE_SEED, seat, mod)
    print(f"[opt] PASS-on-dry candidates: {len(cw)}, PASS-on-empty: {len(cp)}", flush=True)

    # Filter plant candidates: tile must be revisited within 3 days (<=72 steps)
    # by SOME worker, so the tape's own water schedule can cover it.
    plant_cands = []
    for step, wi, x, y in cp:
        future = [s for s in visits.get((x, y), []) if step < s <= step + 72]
        if future:
            plant_cands.append((step, wi, x, y, future[0]))
    print(f"[opt] plant candidates with future revisit: {len(plant_cands)}", flush=True)

    # Opponent(s)
    opps = [args.opp] if args.opp != "all" else ["v18", "builda", "tetsu"]
    opp_agents = {name: load_opp(name) for name in opps}

    def full_score(tape):
        s = 0.0
        for name, oa in opp_agents.items():
            w = 1.0 if name == "v18" else 0.5
            s += w * score_tape(tape, mod, oa, seeds, [0, 1])
        return s

    # Baseline
    base_score = full_score(base)
    print(f"[opt] base score: {base_score:+,.0f}", flush=True)

    # Water patches: all safe (standing on dry crop, worker doesn't move)
    w_patch = []
    for step, wi, x, y, cu in cw:
        w_patch.append((step, wi, ["WATER"]))
    tape_w = apply_patch(base, *w_patch[0]) if w_patch else base
    for p in w_patch[1:]:
        tape_w = apply_patch(tape_w, *p)
    if w_patch:
        w_score = full_score(tape_w)
        print(f"[opt] +all water patches ({len(w_patch)}): {w_score:+,.0f}", flush=True)
    else:
        w_score = base_score

    # Beam search over plant patches (each adds a crop)
    beam = [(base, base_score)]
    if plant_cands:
        # prune: only plant WHEAT (feed-safe) on tiles visited >=3 times
        pruned = []
        for step, wi, x, y, fut in plant_cands:
            n_visits = len([s for s in visits.get((x, y), []) if step <= s <= step + 144])
            if n_visits >= 3:
                pruned.append((step, wi, x, y))
        print(f"[opt] plant candidates surviving visit>=3 filter: {len(pruned)}", flush=True)
        best_tape, best_score = base, base_score
        improved = True
        round_i = 0
        while improved and round_i < args.rounds:
            improved = False
            round_i += 1
            # try adding each candidate to current best
            for step, wi, x, y in pruned:
                cand = apply_patch(best_tape, step, wi, ["PLANT", "WHEAT"])
                cand = ensure_seeds(cand, "WHEAT", 1)
                s = full_score(cand)
                if s > best_score + 200:
                    best_tape, best_score = cand, s
                    improved = True
                    print(f"[opt] round{round_i}: +PLANT at step{step} w{wi} ({x},{y}) -> {s:+,.0f}", flush=True)
                    break
        if best_score > base_score:
            beam = [(best_tape, best_score)]

    best_tape, best_score = max(beam + ([(tape_w, w_score)] if w_patch else []), key=lambda x: x[1])
    print(f"[opt] best score: {best_score:+,.0f} (base {base_score:+,.0f})", flush=True)

    with open(out, "w") as f:
        json.dump(best_tape, f)
    print(f"[opt] saved {out} ({os.path.getsize(out):,} bytes)", flush=True)

    report = {
        "seat": seat, "base_score": base_score, "best_score": best_score,
        "n_water_patches": len(w_patch), "n_plant_patches": len(pruned) if plant_cands else 0,
        "out": out,
    }
    with open(out.replace(".json", "_report.json"), "w") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
