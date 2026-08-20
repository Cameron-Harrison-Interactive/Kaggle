#!/usr/bin/env python3
"""v28_quads.py — SE-quadrant flood variants with the same hard gates.

Variants (compiler-driven, splice d0-19 so the opening+feeding is
byte-identical; only d20-29 movement is rebuilt around the SE wheat):
  Q_24 : unlock SE at d12h01 (BUY_LAND $4k), plant 24 wheat tiles d20-22,
         harvest d26, daily water.
  Q_12 : same with 12 tiles.

Gates: PASS seeds 1-2 both seats (reward >= v25_base − 1500, animals >= 12,
       missed <= base + 2) + keepgate vs v25 (wins >= 5/8, avg >= +500).
Survivor battery: seed 3 PASS both seats, contested v20/kaito seeds 1-2,
self-mirror.
"""
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
OUT = os.path.join(ROOT, "data", "v28quads")
os.makedirs(OUT, exist_ok=True)
RESULTS_PATH = os.path.join(OUT, "results.jsonl")

VARIANTS = {
    "Q_24": {"se_flood": 24, "extra_buy_land": [289]},
    "Q_12": {"se_flood": 12, "extra_buy_land": [289]},
}


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V25 = load_mod(V25_PATH, "v25mod")
V20 = load_mod(os.path.join(ROOT, "agent", "main.py"), "v20mod")
KAITO = load_mod(os.path.join(ROOT, "opponents", "kaito_main.py"), "kaitom")

V25_TAPE = V25._SEAT0_ACTIONS


class Idle:
    def __call__(self, obs, configuration=None):
        return {}


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


def base_pass(seed, seat):
    return BASE_PASS[(seed, seat)]


def _compute_base_pass():
    return {(seed, seat): rc.validate_tape(V25_TAPE, seed, seat, V25)
            for seed in (1, 2, 3) for seat in (0, 1)}


BASE_PASS = None


def run_variant(name):
    spec = VARIANTS[name]
    t0, rep0 = rc.compile_seat(1, 0, V25, variant=dict(spec))
    t1, rep1 = rc.compile_seat(1, 1, V25, variant=dict(spec))
    tapes = {0: t0, 1: t1}
    res = {"name": name}
    pass_ok = True
    for seed in (1, 2):
        for seat in (0, 1):
            st = rc.validate_tape(tapes[seat], seed, seat, V25)
            b = base_pass(seed, seat)
            res[f"pass_{seed}_{seat}"] = {
                "reward": st["reward"], "base": b["reward"],
                "animals": st["animals_alive"],
                "missed": st["total_missed_water"],
                "base_missed": b["total_missed_water"],
            }
            if (st["reward"] < b["reward"] - 1500
                    or st["animals_alive"] < 12
                    or st["total_missed_water"] > b["total_missed_water"] + 2):
                pass_ok = False
    res["pass_ok"] = pass_ok
    va = rc.make_tape_agent(t0, V25)
    va1 = rc.make_tape_agent(t1, V25)
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


def survivor_battery(name):
    spec = VARIANTS[name]
    t0, _ = rc.compile_seat(1, 0, V25, variant=dict(spec))
    t1, _ = rc.compile_seat(1, 1, V25, variant=dict(spec))
    va = rc.make_tape_agent(t0, V25)
    va1 = rc.make_tape_agent(t1, V25)
    base_a = rc.make_tape_agent(V25_TAPE, V25)
    res = {"name": name}
    ok = True
    for seat in (0, 1):
        tape = t0 if seat == 0 else t1
        st = rc.validate_tape(tape, 3, seat, V25)
        b = base_pass(3, seat)
        res[f"pass3_{seat}"] = {"reward": st["reward"], "base": b["reward"]}
        if st["reward"] < b["reward"] - 1500 or st["animals_alive"] < 12:
            ok = False
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
    env = make("kaggriculture", configuration={"episodeSteps": 720,
                                               "seed": 1})
    out = env.run([va, va1])
    last = out[-1]
    res["mirror"] = [last[0].get("reward"), last[1].get("reward")]
    res["survivor"] = ok and res["contested_ok"]
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(res) + "\n")
    return res


def main():
    global BASE_PASS
    BASE_PASS = _compute_base_pass()
    print("base PASS (v25):", flush=True)
    for seed in (1, 2, 3):
        b0, b1 = BASE_PASS[(seed, 0)], BASE_PASS[(seed, 1)]
        print(f"  seed {seed}: s0 {b0['reward']:,.0f} s1 {b1['reward']:,.0f} "
              f"missed {b0['total_missed_water']}/{b1['total_missed_water']} "
              f"animals {b0['animals_alive']}/{b1['animals_alive']}",
              flush=True)
    if os.path.exists(RESULTS_PATH):
        os.remove(RESULTS_PATH)
    if os.path.exists(rc.RECORD_CACHE_DIR):
        shutil.rmtree(rc.RECORD_CACHE_DIR)
    print("record cache wiped; search starts", flush=True)
    with mp.Pool(2) as pool:
        for res in pool.imap_unordered(run_variant, list(VARIANTS),
                                       chunksize=1):
            kg = res["keepgate"]
            print(f"  {res['name']}: pass_ok={res['pass_ok']} "
                  f"keep {kg['wins']}/8 avg {kg['avg']:+9,.0f} "
                  f"keep_ok={res['keep_ok']}", flush=True)
    rows = [json.loads(l) for l in open(RESULTS_PATH)]
    passing = [r for r in rows if r.get("pass_ok") and r.get("keep_ok")]
    print(f"survivors: {[r['name'] for r in passing]}", flush=True)
    for name in [r["name"] for r in passing]:
        res = survivor_battery(name)
        print(f"  {name} survivor battery: survivor={res.get('survivor')} "
              f"mirror={res.get('mirror')}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
