#!/usr/bin/env python3
"""melon4_surgical.py — the rayk +$3.4k edge: 4 late strawberries -> melons.

SURGICAL tape patch on the v20 route (no recompile, no seed-window guessing):

  * swap 4 strawberry PLANTs (window d5-11, latest first) to MELON — same
    tile, same worker, same step.  The compiled water schedule already
    covers the tile daily, and the tape's age-10 HARVEST collects the full
    6 melon units;
  * insert one BUY_SEED MELON 1 at a step strictly BEFORE each swap
    (labor runs before market within a step, so same-step buys are too
    late for the plant; the search walks back up to 12 steps for a market
    slot with room);
  * bump later melon SELL orders +1 each (n*6 total) so the new supply
    moves at the tape's own melon price window (d10-22);
  * NOTHING else changes — labor, routing, animals, wheat schedule intact.

Why it should work: melon = one-time 6 units @ $250 base vs strawberry =
4 ongoing yields @ ~$100.  rayk's tape is our lineage with exactly this
swap (23 melon / 36 straw plants vs our 19 / 37, +18 melon units sold) and
they sit at $173,479 seat0 PASS vs our $167,978.

SHIP GATE: PASS both seats >= base + 500, animals >= 13/13, and contested
(seeds 1-2, both seats) no worse than the known v20 control numbers by
more than $300 avg per opponent.
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
import brain_v21 as b21  # noqa: E402  (reuses build_variant-style harness + labor layer)

OUT_DIR = os.path.join(ROOT, "data", "melon4")
V20_PATH = os.path.join(ROOT, "agent", "main.py")

# known v20 control numbers (measured in the brain_v21 battery, seeds 1-2):
CTRL = {
    "pass0": 167978, "pass1": 162093,
    "vs": {
        "v20": {"avg": -414}, "tetsu": {"avg": -413},
        "rayk": {"avg": 14388}, "kaito": {"avg": 17538},
    },
}


# ---------------------------------------------------------------------------
# the patch
# ---------------------------------------------------------------------------
def apply_melon4(tape, n=4, day_lo=5, day_hi=11, latest_first=True,
                 seed_lookback=12, sell_bump=None):
    """Returns (patched_tape, report)."""
    out = copy.deepcopy(tape)
    # 1) locate strawberry plants in the window
    swaps = []
    for s, e in enumerate(out):
        day = s // 24
        if not (day_lo <= day <= day_hi):
            continue
        for k in ("farmer", "hands"):
            units = [e.get(k)] if k == "farmer" else (e.get("hands") or [])
            for u in units:
                if u and u[0] == "PLANT" and len(u) > 1 and u[1] == "STRAWBERRY":
                    swaps.append((s, k, e, u))
    swaps.sort(key=lambda x: x[0], reverse=latest_first)
    swaps = swaps[:n]
    if len(swaps) < n:
        return None, {"error": f"only {len(swaps)} strawberry plants in d{day_lo}-{day_hi}"}

    # 2) seed buys strictly before each swap, then flip the verb
    done = []
    for s, k, e, u in swaps:
        placed = None
        for t in range(s - 1, max(-1, s - 1 - seed_lookback), -1):
            if t < 0:
                break
            mkt = out[t].get("market") or []
            if len(mkt) < 10:
                out[t]["market"] = mkt + [["BUY_SEED", "MELON", 1]]
                placed = t
                break
        if placed is not None:
            u[1] = "MELON"
            done.append((s, placed))

    # 3) bump melon sells from the earliest swap's harvest day (age 10) on.
    # Melon sell orders run d10-22 in the tape; +1 per order spreads the
    # extra 24 units across the tape's own price window.  Orders overshoot
    # the shed harmlessly (the engine sells min(shed, qty)).
    if not done:
        return None, {"error": "no seed slots found for any swap"}
    first_swap_day = min(s // 24 for s, _ in done)
    bump = sell_bump if sell_bump is not None else n * 6
    bumped = 0
    for s, e in enumerate(out):
        if bumped >= bump:
            break
        if s // 24 < first_swap_day + 10:
            continue
        for o in (e.get("market") or []):
            if bumped >= bump:
                break
            if o and o[0] == "SELL" and o[1] == "MELON" and len(o) > 2:
                o[2] = int(o[2]) + 1
                bumped += 1
    # fallback: new melon sell orders at d20+ steps with market room
    for s, e in enumerate(out):
        if bumped >= bump:
            break
        if s // 24 < first_swap_day + 10:
            continue
        if len(e.get("market") or []) < 10:
            qty = min(6, bump - bumped)
            e["market"] = (e.get("market") or []) + [["SELL", "MELON", qty]]
            bumped += qty
    return out, {
        "swaps": [(s, s // 24, placed) for s, placed in done],
        "first_swap_day": first_swap_day,
        "sell_bumps": bumped,
    }


def build_m4_agent(mod, tape):
    """Full v20 runtime layers on top of the patched tape."""
    def agent(obs, configuration=None):
        try:
            step = min(max(0, int(mod._get(obs, "step", 0) or 0)), len(tape) - 1)
            mod._update_memory(obs)
            action = mod._weed_repair_action(obs, mod._copy_action(tape[step]), tape, step)
            action = mod._adapt_animals(obs, action)
            action = mod._adapt_crops(obs, action)
            action = mod._adapt_market(obs, action)
            action = mod._align_hands(
                mod._rank_sell_slots(obs, action, configuration), obs)
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


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------
_W = {}


def _init():
    _W["mod"] = rc.load_v18(V20_PATH)
    _W["mod_raw"] = importlib.util.spec_from_file_location("v20", V20_PATH)
    m = importlib.util.module_from_spec(_W["mod_raw"])
    _W["mod_raw"].loader.exec_module(m)
    _W["mod_raw"] = m
    _W["suite"] = {
        "v20": m.agent,
        "tetsu": _load("opponents/tetsu_main.py", "tetsu").agent,
        "rayk": _load("opponents/rayk_main.py", "rayk").agent,
        "kaito": _load("opponents/kaito_main.py", "kaito").agent,
    }


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _eval(task):
    v, seeds = task
    t0 = time.time()
    try:
        mod = _W["mod"]
        tape, rep = apply_melon4(mod._SEAT0_ACTIONS,
                                 n=v["n"], day_lo=v["day_lo"], day_hi=v["day_hi"])
        if tape is None:
            return {"name": v["name"], "error": rep.get("error")}
        rec = {"name": v["name"], "patch": rep}
        st0 = rc.validate_tape(tape, 1, 0, mod)
        st1 = rc.validate_tape(tape, 1, 1, mod)
        rec["pass0"] = st0["reward"]
        rec["pass1"] = st1["reward"]
        rec["animals0"] = st0.get("animals_alive")
        rec["animals1"] = st1.get("animals_alive")
        rec["weeds_d15"] = st0.get("weeds_d15")
        agent = build_m4_agent(_W["mod_raw"], tape)
        rec["vs"] = {}
        for name, opp in _W["suite"].items():
            wins = games = 0
            deltas = []
            for seed in seeds:
                for seat in (0, 1):
                    x, y = a20.battle(agent, opp, seed, seat)
                    wins += 1 if x > y else 0
                    games += 1
                    deltas.append(x - y)
            rec["vs"][name] = {"wins": wins, "games": games,
                               "avg": sum(deltas) / max(1, len(deltas))}
        rec["time_s"] = round(time.time() - t0, 1)
        print(f"    [{v['name']}] PASS ${rec['pass0']:,.0f}/${rec['pass1']:,.0f} "
              f"anim {rec['animals0']}/{rec['animals1']} weeds_d15={rec['weeds_d15']} | "
              + " | ".join(f"{k} {d['avg']:+,.0f} ({d['wins']}/{d['games']})"
                           for k, d in rec["vs"].items())
              + f" | {rec['time_s']}s", flush=True)
        return rec
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"    [ERR] {v['name']}: {e}", flush=True)
        return {"name": v["name"], "error": str(e)}


def catalog():
    return [
        {"name": "m4_late", "n": 4, "day_lo": 5, "day_hi": 11},
        {"name": "m4_mid", "n": 4, "day_lo": 5, "day_hi": 9},
        {"name": "m4_2", "n": 2, "day_lo": 8, "day_hi": 11},
    ]


def _self_test():
    mod = _load("agent/main.py", "v20")
    tape, rep = apply_melon4(mod._SEAT0_ACTIONS)
    assert tape is not None, rep
    base = mod._SEAT0_ACTIONS

    def plant_counter(t):
        import collections
        c = collections.Counter()
        for e in t:
            for k in ("farmer", "hands"):
                units = [e.get(k)] if k == "farmer" else (e.get("hands") or [])
                for u in units:
                    if u and u[0] == "PLANT" and len(u) > 1:
                        c[u[1]] += 1
        return c
    pb, pp = plant_counter(base), plant_counter(tape)
    assert pp["MELON"] - pb["MELON"] == 4, (pb, pp)
    assert pb["STRAWBERRY"] - pp["STRAWBERRY"] == 4
    print(f"[self-test] plant delta ok  {dict(pp)}")

    def melon_seed_buys(t):
        n = 0
        for e in t:
            for o in (e.get("market") or []):
                if o and o[0] == "BUY_SEED" and o[1] == "MELON":
                    n += int(o[2])
        return n
    sb, sp = melon_seed_buys(base), melon_seed_buys(tape)
    assert sp - sb == 4, (sb, sp)
    print(f"[self-test] melon seed buys +{sp - sb} ok")

    def melon_sells(t):
        n = 0
        for e in t:
            for o in (e.get("market") or []):
                if o and o[0] == "SELL" and o[1] == "MELON":
                    n += int(o[2])
        return n
    xb, xp = melon_sells(base), melon_sells(tape)
    assert xp - xb == 24, (xb, xp)
    print(f"[self-test] melon sells +{xp - xb} ok")

    # labor unchanged outside the 4 plant verbs + seed/sell market lines
    lab_diff = 0
    for s in range(719):
        for k in ("farmer", "hands"):
            a = [base[s].get(k)] if k == "farmer" else (base[s].get("hands") or [])
            b = [tape[s].get(k)] if k == "farmer" else (tape[s].get("hands") or [])
            for ua, ub in zip(a, b):
                if ua != ub and not (ua and ub and ua[0] == "PLANT"
                                     and ua[1] == "STRAWBERRY" and ub[1] == "MELON"):
                    lab_diff += 1
    assert lab_diff == 0, lab_diff
    print("[self-test] labor intact outside the 4 swaps ok")
    print("[self-test] ALL PASSED")


def main():
    # copy-paste guard: strip stray trailing punctuation from flags
    # ("--finals." -> "--finals") so pasted commands never 400.
    sys.argv = [a.rstrip(".,;:!?") if a.startswith("--") else a for a in sys.argv]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", default="1,2")
    ap.add_argument("--procs", type=int, default=0)
    ap.add_argument("--build-agent", action="store_true")
    ap.add_argument("--version", default="HI_AgriBot_v22_MelonMeta")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _self_test()
        return
    seeds = [int(s) for s in args.seeds.split(",")]
    procs = args.procs or os.cpu_count() or 2
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"[melon4] seeds={seeds} procs={procs}", flush=True)
    print("[melon4] control numbers (v20, seeds 1-2): PASS $167,978/$162,093, "
          f"vs v20 {CTRL['vs']['v20']['avg']:+.0f}, tetsu {CTRL['vs']['tetsu']['avg']:+.0f}, "
          f"rayk {CTRL['vs']['rayk']['avg']:+.0f}, kaito {CTRL['vs']['kaito']['avg']:+.0f}",
          flush=True)
    variants = catalog()
    tasks = [(v, seeds) for v in variants]
    if procs <= 1:
        _init()
        results = [_eval(t) for t in tasks]
    else:
        pool = multiprocessing.Pool(processes=min(procs, len(tasks)),
                                    initializer=_init)
        results = list(pool.imap_unordered(_eval, tasks, chunksize=1))
        pool.close()
        pool.join()
    with open(os.path.join(OUT_DIR, "ledger.jsonl"), "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    print("\n[melon4] VERDICT", flush=True)
    for r in results:
        if r.get("error"):
            print(f"  {r['name']}: ERROR {r['error']}", flush=True)
            continue
        ok_pass = (r["pass0"] >= CTRL["pass0"] + 500
                   and r["pass1"] >= CTRL["pass1"] + 500)
        ok_anim = r["animals0"] >= 13 and r["animals1"] >= 13
        ok_vs = all(abs(r["vs"].get(k, {}).get("avg", 0) - CTRL["vs"][k]["avg"]) <= 300
                    for k in CTRL["vs"])
        verdict = "SHIP" if ok_pass and ok_anim and ok_vs else "no"
        print(f"  {r['name']}: pass_delta s0 {r['pass0']-CTRL['pass0']:+,.0f} "
              f"s1 {r['pass1']-CTRL['pass1']:+,.0f}  anim_ok={ok_anim} "
              f"contested_ok={ok_vs} -> {verdict}", flush=True)
        r["verdict"] = verdict

    ship = [r for r in results if r.get("verdict") == "SHIP"]
    report = {"control": CTRL, "results": results,
              "shippable": ship[0]["name"] if ship else None}
    with open(os.path.join(OUT_DIR, "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[melon4] ledger + report -> {OUT_DIR}", flush=True)
    if ship and args.build_agent:
        r = ship[0]
        mod = _W["mod_raw"]
        tape, rep = apply_melon4(mod._SEAT0_ACTIONS,
                                 n=r.get("n", 4), day_lo=r.get("day_lo", 5),
                                 day_hi=r.get("day_hi", 11))
        _build_agent_file(tape, args.version)


def _build_agent_file(tape, version):
    src = open(V20_PATH).read()
    import re
    header = (f'"""HI_AgriBot_v22_MelonMeta — v20 + melon4-surgical '
              f'(4 late strawberries -> melons, rayk economy edge).\n'
              f'"""\n\nVERSION = {json.dumps(version)}\n')
    # drop docstring + VERSION
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
    override = ("\n# --- melon4 tapes (override) ---\n"
                f"_SEAT0_ACTIONS = json.loads({json.dumps(tape)!r})\n"
                f"_SEAT1_ACTIONS = _SEAT0_ACTIONS\n")
    path = os.path.join(ROOT, "agent", "main_v22_melon4.py")
    with open(path, "w") as f:
        f.write(header + body + override)
    print(f"[melon4] agent written -> {path}  VERSION = {version}", flush=True)


if __name__ == "__main__":
    main()
