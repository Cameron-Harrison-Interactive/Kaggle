#!/usr/bin/env python3
"""v28_full.py — economy-variant search ON THE v25 TAPE via the route compiler.

v28-full: generate a wheat-machine economy variant using the compiler's
variant machinery, with hard gates (the user's "make sure we test it"):

  F (fast-path, proven movement, market/surgery only):
    leftover_harvest 1/3, sell_split, idle_water, combos
  R (recompile movement around new economy anchors):
    early_plant 4/6 (plant the late SW wheat at its first visit — the
    'missing row planted a month late' fix), plant_fill 2 (new wheat tiles
    on visited-but-empty ground), combos

Gates (all must pass for a variant to be considered):
  PASS (validate_tape, seeds 1-2 both seats): reward >= v25_base - 1000,
    animals_alive >= 12, missed_water <= base + 2.
  keepgate vs v25 (same wrapper, seeds 1-2 both seats): wins >= 5/8 AND
    avg delta >= +500.
Survivor battery: seed 3 PASS, contested v20/kaito (>=7/8 not worse than
v25 by >500), 3 recorded-replay spots (sum >= -1500).
"""
import argparse
import copy
import importlib.util
import json
import multiprocessing as mp
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "agent"))
sys.path.insert(0, os.path.join(ROOT, "opponents"))

import route_compiler_v19 as rc  # noqa: E402

from kaggle_environments import make  # noqa: E402

V25_PATH = os.path.join(ROOT, "agent", "main_v25_wheat16.py")
OUT = os.path.join(ROOT, "data", "v28full")
os.makedirs(OUT, exist_ok=True)
RESULTS_PATH = os.path.join(OUT, "results.jsonl")

VARIANTS = {
    "F_lh1":      {"leftover_harvest": 1},
    "F_lh3":      {"leftover_harvest": 3},
    "F_split":    {"sell_split": True},
    "F_lh1split": {"leftover_harvest": 1, "sell_split": True},
    "F_idle":     {"idle_water": 1},
    "R_early4":   {"early_plant": 4},
    "R_early6":   {"early_plant": 6},
    "R_early4lh": {"early_plant": 4, "leftover_harvest": 1},
    "R_fill2":    {"plant_fill": 2},
    "R_all":      {"early_plant": 4, "plant_fill": 2, "leftover_harvest": 1},
}

REPLAYS = {}
for eid in ("93065463", "93061726", "93059081"):
    p = os.path.join(ROOT, "data", "regression_v26", "opp_actions",
                     f"{eid}.json")
    if os.path.exists(p):
        d = json.load(open(p))
        REPLAYS[eid] = (d["actions"], d["our_seat"], d["opp_seat"], d["seed"])


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V25 = load_mod(V25_PATH, "v25mod")
V20 = load_mod(os.path.join(ROOT, "agent", "main.py"), "v20mod")
KAITO = load_mod(os.path.join(ROOT, "opponents", "kaito_main.py"), "kaitom")

V25_TAPE = V25._SEAT0_ACTIONS


class ReplayOpp:
    def __init__(self, acts):
        self.acts = acts
        self.i = -1

    def __call__(self, obs, configuration=None):
        self.i += 1
        return self.acts[min(self.i, len(self.acts) - 1)]


def count_escapes(out, seat):
    esc = 0
    prev = {}
    for st in out:
        farm = (st[seat].get("observation") or {}).get("farms") or [{}]
        tiles = (farm[0] if farm else {}).get("tiles") or []
        cur = {}
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                if isinstance(t, dict) and "animal" in t:
                    cur[(x, y)] = t["animal"]
        for pos in prev:
            if pos not in cur:
                esc += 1
        prev = cur
    return esc


def play_agents(agents, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": seed})
    out = env.run(agents)
    last = out[-1]
    return (last[0].get("reward"), last[1].get("reward"),
            count_escapes(out, 0), count_escapes(out, 1))


def replay_game(variant_agent, our_seat, opp_seat, seed, opp_acts):
    agents = [None, None]
    agents[our_seat] = variant_agent
    agents[opp_seat] = ReplayOpp(opp_acts)
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": int(seed)})
    out = env.run(agents)
    return out[-1][our_seat].get("reward")


def base_pass(seed, seat):
    """cached v25-tape PASS stats (precomputed in main; fork-inherited)."""
    return BASE_PASS[(seed, seat)]


def _compute_base_pass():
    return {(seed, seat): rc.validate_tape(V25_TAPE, seed, seat, V25)
            for seed in (1, 2, 3) for seat in (0, 1)}


BASE_PASS = None


def run_variant(name):
    spec = VARIANTS[name]
    t0, rep0 = rc.compile_seat(1, 0, V25, variant=spec)
    t1, rep1 = rc.compile_seat(1, 1, V25, variant=spec)
    tapes = {0: t0, 1: t1}
    res = {"name": name, "recompiled": rep0.get("recompiled") or rep1.get("recompiled")}
    # PASS gates seeds 1-2 both seats
    pass_ok = True
    for seed in (1, 2):
        for seat in (0, 1):
            st = rc.validate_tape(tapes[seat], seed, seat, V25)
            b = base_pass(seed, seat)
            res[f"pass_{seed}_{seat}"] = {
                "reward": st["reward"], "base": b["reward"],
                "animals": st["animals_alive"], "missed": st["total_missed_water"],
                "base_missed": b["total_missed_water"],
            }
            if (st["reward"] < b["reward"] - 1000
                    or st["animals_alive"] < 12
                    or st["total_missed_water"] > b["total_missed_water"] + 2):
                pass_ok = False
    res["pass_ok"] = pass_ok
    # keepgate vs v25 raw tape (identical wrapper)
    va = rc.make_tape_agent(tapes[0], V25)
    va1 = rc.make_tape_agent(tapes[1], V25)
    base_a = rc.make_tape_agent(V25_TAPE, V25)
    wins = total = 0
    for seed in (1, 2):
        for seat in (0, 1):
            variant = va if seat == 0 else va1
            a, b = rc.battle(variant, base_a, seed, seat)
            wins += 1 if a > b else 0
            total += a - b
    res["keepgate"] = {"wins": wins, "games": 8, "avg": total / 8}
    res["keep_ok"] = wins >= 5 and total / 8 >= 500
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(res) + "\n")
    return res


def survivor_battery(name, spec):
    t0, _ = rc.compile_seat(1, 0, V25, variant=spec)
    t1, _ = rc.compile_seat(1, 1, V25, variant=spec)
    va = rc.make_tape_agent(t0, V25)
    va1 = rc.make_tape_agent(t1, V25)
    base_a = rc.make_tape_agent(V25_TAPE, V25)
    res = {"name": name}
    # seed 3 PASS both seats
    ok = True
    for seat in (0, 1):
        tape = t0 if seat == 0 else t1
        st = rc.validate_tape(tape, 3, seat, V25)
        b = base_pass(3, seat)
        res[f"pass3_{seat}"] = {"reward": st["reward"], "base": b["reward"]}
        if st["reward"] < b["reward"] - 1000 or st["animals_alive"] < 12:
            ok = False
    # contested
    worse = 0
    for opp_name, opp_mod in (("v20", V20), ("kaito", KAITO)):
        for seed in (1, 2):
            for seat in (0, 1):
                variant = va if seat == 0 else va1
                agents_v = [None, None]
                agents_v[seat] = variant
                agents_v[1 - seat] = opp_mod.agent
                v_r, o_r, v_e, _ = play_agents(agents_v, seed)
                agents_b = [None, None]
                agents_b[seat] = base_a
                agents_b[1 - seat] = opp_mod.agent
                b_r, o2_r, b_e, _ = play_agents(agents_b, seed)
                dv = v_r - o_r
                db = b_r - o2_r
                res[f"c_{opp_name}_{seed}_{seat}"] = {
                    "var": [v_r, o_r, v_e], "base": [b_r, o2_r, b_e],
                    "delta": dv - db,
                }
                if dv < db - 500:
                    worse += 1
    res["contested_ok"] = worse <= 1
    # replay spots
    total_r = 0
    for eid, (acts, our_seat, opp_seat, seed) in REPLAYS.items():
        rv = replay_game(va if our_seat == 0 else va1, our_seat, opp_seat,
                         seed, acts)
        rb = replay_game(base_a, our_seat, opp_seat, seed, acts)
        res[f"r_{eid}"] = {"var": rv, "base": rb}
        total_r += rv - rb
    res["replay_ok"] = total_r >= -1500
    res["survivor"] = ok and res["contested_ok"] and res["replay_ok"]
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(res) + "\n")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wipe-cache", action="store_true",
                    help="delete the compiler record cache first")
    ap.add_argument("--survivors", action="store_true",
                    help="run the survivor battery for passing variants")
    args = ap.parse_args()

    if args.wipe_cache and os.path.exists(rc.RECORD_CACHE_DIR):
        shutil.rmtree(rc.RECORD_CACHE_DIR)
        print("record cache wiped", flush=True)

    if os.path.exists(RESULTS_PATH) and not args.survivors:
        os.remove(RESULTS_PATH)

    global BASE_PASS
    BASE_PASS = _compute_base_pass()

    if not args.survivors:
        print("=== v28-full variant search on the v25 tape ===", flush=True)
        print("base PASS (v25 tape):", flush=True)
        for seed in (1, 2, 3):
            b0, b1 = BASE_PASS[(seed, 0)], BASE_PASS[(seed, 1)]
            print(f"  seed {seed}: "
                  f"s0 {b0['reward']:,.0f} "
                  f"s1 {b1['reward']:,.0f} "
                  f"(missed {b0['total_missed_water']}/"
                  f"{b1['total_missed_water']}, "
                  f"animals {b0['animals_alive']}/"
                  f"{b1['animals_alive']})", flush=True)
        with mp.Pool(2) as pool:
            for res in pool.imap_unordered(run_variant,
                                           list(VARIANTS), chunksize=1):
                kg = res["keepgate"]
                print(f"  {res['name']:12s} recompile={res['recompiled']} "
                      f"pass_ok={res['pass_ok']} "
                      f"keep {kg['wins']}/8 avg {kg['avg']:+9,.0f} "
                      f"keep_ok={res['keep_ok']}", flush=True)
        rows = [json.loads(l) for l in open(RESULTS_PATH)]
        passing = [r for r in rows if r.get("pass_ok") and r.get("keep_ok")]
        print(f"\n=== {len(passing)} survivors: {[r['name'] for r in passing]}",
              flush=True)
        json.dump(rows, open(os.path.join(OUT, "search.json"), "w"), indent=1)
    else:
        rows = [json.loads(l) for l in open(RESULTS_PATH)]
        passing = [r for r in rows if r.get("pass_ok") and r.get("keep_ok")]
        print(f"survivor battery for {len(passing)} variants", flush=True)
        for name in [r["name"] for r in passing]:
            res = survivor_battery(name, VARIANTS[name])
            print(f"  {name}: survivor={res.get('survivor')} "
                  f"contested_worse={sum(1 for k in res if k.startswith('c_') and res[k]['delta'] < -500)} "
                  f"replay_total={sum(res.get(k, {}).get('var', 0) - res.get(k, {}).get('base', 0) for k in res if k.startswith('r_')):+,.0f}",
                  flush=True)
        final = [json.loads(l) for l in open(RESULTS_PATH)
                 if json.loads(l).get("survivor") is True and json.loads(l).get("keep_ok")]
        print(f"\n=== FINAL SURVIVORS: {[r['name'] for r in final]}", flush=True)


if __name__ == "__main__":
    main()
