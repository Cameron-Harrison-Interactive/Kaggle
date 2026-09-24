#!/usr/bin/env python3
"""wheatfix.py — adopt Álvaro's proven live opening (episode 92975821).

The live loss (v20 vs Álvaro Benítez, $70,321 vs $103,475) decomposes to:
  1. Their d0h0 queue opens with BUY_PRODUCT WHEAT 14 (front of queue).
     That (a) reserves 5 wheat for feeding all 5 animals (ours buys 5 at
     the END of the queue with only ~$110 left -> lands 3 at the inflated
     price) and (b) inflates the wheat price for our 5-unit buy.
  2. Their d0h1 sells 9 wheat back (~$250) which funds the seed orders
     their d0h0 cash couldn't cover (M3 + W1) AND keeps the 5 feed units.
  3. One of OUR sheep (placed late d0, unfed d0 because we had 3 wheat for
     5 animals) reaches consecutive_unfed=2 on d1 (no wheat exists d1) ->
     escapes.  With 3 sheep, our d10h1 WOOL16 sell (~$3,120) fails while
     theirs succeeds -> their d10 seed wave (M+S) funds, ours dies at $54
     with 3 melon seeds -> 12 failed plants -> 46 vs 62 crops forever.

Fixes (stacked):
  A. wheat_open  — replace our d0h0/d0h1 market queues with theirs.
  B. nocow       — the (7,4) cow relocation (previous session's v22 fix).
  C. alvaro_mkt  — graft their ENTIRE 720-turn market-order schedule onto
                   our tape (labor stays ours).  Keep-gated.

Gates: PASS (seed 1 + live seed 1441928087) >= base-500, escapes == 0,
d10-d12 crops >= 58 on the live-seed contested test, contested deltas
(v20/tetsu/kaito/rayk) within tolerance of control.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import multiprocessing
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import route_compiler_v19 as rc  # noqa: E402
import adaptive_v20 as a20  # noqa: E402
import nocow_fix as nf  # noqa: E402

OUT_DIR = os.path.join(ROOT, "data", "wheatfix")
V20_PATH = os.path.join(ROOT, "agent", "main.py")
LIVE_SEED = 1441928087
BASE_PASS0 = 167978
CTRL_VS = {"v20": -414, "tetsu": -413, "rayk": 14388, "kaito": 17538}

REPLAY_PATH = os.path.join(ROOT, "episode-92975821-replay.json")


# ---------------------------------------------------------------------------
# A: wheat opening
# ---------------------------------------------------------------------------
def apply_wheat_open(tape):
    out = copy.deepcopy(tape)
    out[0]["market"] = [
        ["BUY_PRODUCT", "WHEAT", 14],
        ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
        ["BUY_ANIMAL", "COW", 1],
        ["BUY_ANIMAL", "SHEEP", 4],
        ["BUY_SEED", "MELON", 5],
        ["BUY_SEED", "WHEAT", 5],
    ]
    out[1]["market"] = [
        ["SELL", "WHEAT", 9],
        ["BUY_SEED", "MELON", 3],
        ["BUY_SEED", "WHEAT", 1],
    ]
    return out


# ---------------------------------------------------------------------------
# C: full alvaro market graft
# ---------------------------------------------------------------------------
_ALVARO_MKT = None


def _load_alvaro_market():
    global _ALVARO_MKT
    if _ALVARO_MKT is not None:
        return _ALVARO_MKT
    replay = json.load(open(REPLAY_PATH))
    steps = replay["steps"]
    mkt = []
    for t in range(720):
        # replay steps[t+1].action == turn-t action (steps[0] is pre-state)
        act = (steps[t + 1][1].get("action") or {}) if t + 1 < len(steps) else {}
        orders = [list(o) for o in (act.get("market") or [])]
        mkt.append(orders)
    _ALVARO_MKT = mkt
    return mkt


def apply_alvaro_market(tape):
    mkt = _load_alvaro_market()
    out = copy.deepcopy(tape)
    for t in range(720):
        if t < len(out):
            out[t]["market"] = copy.deepcopy(mkt[min(t, len(mkt) - 1)])
    return out


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------
_W = {}


def _init():
    spec = importlib.util.spec_from_file_location("v20", V20_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _W["mod"] = mod
    _W["mod_p"] = rc.load_v18(V20_PATH)
    suite = {}
    for name, path in (("v20", V20_PATH),
                       ("tetsu", os.path.join(ROOT, "opponents/tetsu_main.py")),
                       ("rayk", os.path.join(ROOT, "opponents/rayk_main.py")),
                       ("kaito", os.path.join(ROOT, "opponents/kaito_main.py"))):
        s = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
        suite[name] = m.agent
    _W["suite"] = suite


def _taped_agent(mod, tape):
    def agent(obs, configuration=None):
        try:
            step = min(max(0, int(mod._get(obs, "step", 0) or 0)), len(tape) - 1)
            mod._update_memory(obs)
            action = mod._weed_repair_action(obs, mod._copy_action(tape[step]), tape, step)
            action = mod._adapt_animals(obs, action)
            action = mod._adapt_crops(obs, action)
            action = mod._adapt_market(obs, action)
            action = mod._align_hands(mod._rank_sell_slots(obs, action, configuration), obs)
            if step == 718 and hasattr(mod, "_v26_terminal_sweep"):
                try:
                    action = mod._v26_terminal_sweep(obs, action, configuration)
                except Exception:
                    pass
            return mod._align_hands(action, obs)
        except Exception:
            farm = mod._farm(obs, mod._seat(obs))
            return {"farmer": ["PASS"],
                    "hands": [["PASS"] for _ in (mod._get(farm, "hands", []) or [])],
                    "market": []}
    return agent


def _audit(agent, opp, seed, seat=0):
    """money/crops/escapes/failed-plants audit of one game."""
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    if seat == 0:
        env.run([agent, opp])
    else:
        env.run([opp, agent])
    crops_by_day, escapes, fails = [], 0, 0
    prev = {}
    for si in range(720):
        obs = env.steps[si][seat].get("observation", {}) or {}
        farm = (obs.get("farms") or [{}])[seat]
        cur = {(x, y): t["animal"] for y, row in enumerate(farm.get("tiles") or [])
               for x, t in enumerate(row) if isinstance(t, dict) and t.get("animal")}
        for pos in list(prev):
            if pos not in cur:
                escapes += 1
        prev = cur
        if si % 24 == 0:
            crops_by_day.append(sum(1 for row in farm.get("tiles") or []
                                    for t in row if isinstance(t, dict) and t.get("kind") == "PLANT"))
        act = env.steps[si][seat].get("action") or {}
        seeds = dict((obs.get("private") or {}).get("seeds") or {})
        for k in ("farmer", "hands"):
            units = [act.get(k)] if k == "farmer" else (act.get("hands") or [])
            for u in units:
                if u and u[0] == "PLANT" and len(u) > 1 and seeds.get(u[1], 0) <= 0:
                    fails += 1
    return {"reward": env.steps[-1][seat].reward or 0,
            "escapes": escapes, "fails": fails, "max_crops": max(crops_by_day),
            "crops_d10": crops_by_day[10] if len(crops_by_day) > 10 else 0,
            "crops_d11": crops_by_day[11] if len(crops_by_day) > 11 else 0,
            "crops_d12": crops_by_day[12] if len(crops_by_day) > 12 else 0}


def _build_tape(name):
    mod = _W["mod_p"]
    tape, plants, anchors, day_starts, hires, visits, ref = rc.get_record(1, 0, mod, {})
    _, oh, _ = rc.record_reference(1, 0, mod, {})
    if name in ("wheat_open", "stack"):
        tape = apply_wheat_open(tape)
    if name in ("alvaro_mkt", "stack"):
        tape = apply_alvaro_market(tape)
    if name in ("nocow", "stack"):
        tape, rep = nf.apply_nocow(tape, oh)
    return tape


def _eval(task):
    name, seeds = task
    t0 = time.time()
    try:
        tape = _build_tape(name)
        agent = _taped_agent(_W["mod"], tape)
        rec = {"name": name}
        # PASS on seed 1 + live seed
        for label, seed in (("s1", 1), ("live", LIVE_SEED)):
            a = _audit(agent, rc.pass_agent(), seed, 0)
            rec[f"pass_{label}"] = a
        # contested on the LIVE seed + seeds 1-2
        rec["vs"] = {}
        for opp_name, opp in _W["suite"].items():
            wins = games = 0
            deltas = []
            for seed in seeds:
                for seat in (0, 1):
                    x, y = a20.battle(agent, opp, seed, seat)
                    wins += 1 if x > y else 0
                    games += 1
                    deltas.append(x - y)
            rec["vs"][opp_name] = {"wins": wins, "games": games,
                                   "avg": sum(deltas) / max(1, len(deltas))}
        # the money metric: live-seed mirror crop counts
        m = _audit(agent, _W["suite"]["v20"], LIVE_SEED, 0)
        rec["live_mirror"] = m
        rec["time_s"] = round(time.time() - t0, 1)
        print(f"    [{name:10s}] PASS s1 ${rec['pass_s1']['reward']:,.0f} (esc {rec['pass_s1']['escapes']}, "
              f"fails {rec['pass_s1']['fails']}, crops d10-12 "
              f"{rec['pass_s1']['crops_d10']}/{rec['pass_s1']['crops_d11']}/{rec['pass_s1']['crops_d12']}) | "
              f"PASS live ${rec['pass_live']['reward']:,.0f} (esc {rec['pass_live']['escapes']}) | "
              + " | ".join(f"{k} {d['avg']:+,.0f}" for k, d in rec["vs"].items())
              + f" | liveMirror crops d10-12 {m['crops_d10']}/{m['crops_d11']}/{m['crops_d12']} "
                f"${m['reward']:,.0f} | {rec['time_s']}s", flush=True)
        return rec
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"    [ERR] {name}: {e}", flush=True)
        return {"name": name, "error": str(e)}


def main():
    # copy-paste guard: strip stray trailing punctuation from flags
    # ("--finals." -> "--finals") so pasted commands never 400.
    sys.argv = [a.rstrip(".,;:!?") if a.startswith("--") else a for a in sys.argv]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", default="1,2")
    ap.add_argument("--procs", type=int, default=0)
    ap.add_argument("--build-agent", action="store_true")
    ap.add_argument("--version", default="HI_AgriBot_v24_WheatGuard")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _init()
        mod = _W["mod_p"]
        tape, plants, anchors, day_starts, hires, visits, ref = rc.get_record(1, 0, mod, {})
        t1 = apply_wheat_open(tape)
        assert t1[0]["market"][0] == ["BUY_PRODUCT", "WHEAT", 14], t1[0]
        assert t1[1]["market"][0] == ["SELL", "WHEAT", 9], t1[1]
        print("[self-test] wheat_open orders ok")
        mkt = _load_alvaro_market()
        assert len(mkt) == 720 and any(len(o) for o in mkt)
        print(f"[self-test] alvaro market loaded: 720 turns, "
              f"{sum(1 for o in mkt if o)} non-empty")
        print("[self-test] ALL PASSED")
        return
    seeds = [int(s) for s in args.seeds.split(",")]
    procs = args.procs or os.cpu_count() or 2
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"[wheatfix] seeds={seeds} procs={procs}", flush=True)
    print("[wheatfix] control v20: PASS s1 $167,978 (esc 1, 24 fails), "
          "live-seed mirror crops 61", flush=True)
    tasks = [(n, seeds) for n in ("wheat_open", "nocow", "stack", "alvaro_mkt")]
    if procs <= 1:
        _init()
        results = [_eval(t) for t in tasks]
    else:
        pool = multiprocessing.Pool(processes=min(procs, len(tasks)), initializer=_init)
        results = list(pool.imap_unordered(_eval, tasks, chunksize=1))
        pool.close()
        pool.join()
    with open(os.path.join(OUT_DIR, "ledger.jsonl"), "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print("\n[wheatfix] VERDICT", flush=True)
    for r in results:
        if r.get("error"):
            print(f"  {r['name']}: ERROR {r['error']}", flush=True)
            continue
        p1 = r["pass_s1"]; pl = r["pass_live"]
        ok_pass = p1["reward"] >= BASE_PASS0 - 500
        ok_esc = p1["escapes"] == 0 and pl["escapes"] == 0
        ok_crops = r["live_mirror"]["crops_d12"] >= 58
        ok_vs = all(abs(r["vs"].get(k, {}).get("avg", 0) - CTRL_VS[k]) <= 600
                    for k in CTRL_VS)
        verdict = "SHIP" if ok_pass and ok_esc and ok_crops and ok_vs else "no"
        print(f"  {r['name']:10s}: PASS ${p1['reward']:,.0f} esc={p1['escapes']} "
              f"live-mirror-crops-d12={r['live_mirror']['crops_d12']} "
              f"pass={ok_pass} esc={ok_esc} crops={ok_crops} vs={ok_vs} -> {verdict}",
              flush=True)
        r["verdict"] = verdict
    ship = [r for r in results if r.get("verdict") == "SHIP"]
    json.dump({"results": results, "shippable": ship[0]["name"] if ship else None},
              open(os.path.join(OUT_DIR, "report.json"), "w"), indent=2)
    print(f"[wheatfix] report -> {OUT_DIR}", flush=True)
    if ship and args.build_agent:
        name = ship[0]["name"]
        _init()
        tape = _build_tape(name)
        _build_agent_file(tape, args.version, name)


def _build_agent_file(tape, version, tag):
    src = open(V20_PATH).read()
    header = (f'"""HI_AgriBot_v24_WheatGuard — v20 + {tag} '
              f'(Álvaro wheat opening / no-escape fixes).\n'
              f'"""\n\nVERSION = {json.dumps(version)}\n')
    lines = src.splitlines(keepends=True)
    out = []
    skip_doc = False
    for line in lines:
        if line.startswith('"""') and not skip_doc:
            skip_doc = True
            continue
        if skip_doc:
            if '"""' in line:
                skip_doc = False
            continue
        if line.startswith("VERSION = "):
            continue
        out.append(line)
    body = "".join(out)
    override = ("\n# --- fixed tapes (override) ---\n"
                f"_SEAT0_ACTIONS = json.loads({json.dumps(tape)!r})\n"
                f"_SEAT1_ACTIONS = _SEAT0_ACTIONS\n"
                f"_v24_agent = agent\n")
    path = os.path.join(ROOT, "agent", "main_v24_wheatguard.py")
    with open(path, "w") as f:
        f.write(header + body + override)
    print(f"[wheatfix] agent written -> {path}  VERSION = {version}", flush=True)


if __name__ == "__main__":
    main()
