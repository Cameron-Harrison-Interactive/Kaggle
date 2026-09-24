#!/usr/bin/env python3
"""nocow_fix.py — eliminate the d22 (7,4) cow escape (found 2026-08-14).

Mechanism (traced in the v20 seat0 tape vs PASS):
  * the (7,4) pasture is built d8h12 and a cow placed d8h13;
  * the tender feeds/cares it daily through d19 (milk harvested d16/18/20);
  * the d20 late-wheat wave re-routes the tender -> cow unfed d20+d21 ->
    ESCAPES end of d21 (visible d22h0).  Every game.  -$400 + optics.

Fix A "nocow" (surgical, no recompile):
  * REMOVE the d8h12 BUILD_PASTURE on (7,4): the d8h13 PLACE fails, the cow
    rides the worker's inventory to the end-of-day shed drop;
  * the d21 construction wave (tape builds (7,3) and (3,0) pastures and
    feeds both!) picks the shed cow up and places it FED;
  * SKIP the d18h1 BUY_ANIMAL COW 1 so no cow strands in the shed;
  * net: 9 cows all alive and tended, no escape, no stranded cow.
    Cost: the d16-20 (7,4) milk (~3 harvests). Gain: $400 + d21+ milk
    from the relocated cow + zero escapes.

Fix B "feed74" (compiler): inject FEED-only anchors at (7,4) on d21,23,
25,27 for the reference tender (route_compiler_v19.inject_feed_anchors).

Gate: PASS seat0 >= base-400, animals >= 13, escapes == 0, contested
(v20/tetsu/kaito/rayk, seeds 1-2 both seats) within $300 avg of control.
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

OUT_DIR = os.path.join(ROOT, "data", "nocow")
V20_PATH = os.path.join(ROOT, "agent", "main.py")
BASE_PASS0 = 167978
CTRL_VS = {"v20": -414, "tetsu": -413, "rayk": 14388, "kaito": 17538}


# ---------------------------------------------------------------------------
# fix A: surgical pasture-skip + cow-buy-skip
# ---------------------------------------------------------------------------
def apply_nocow(tape, obs_history):
    """Remove the (7,4) BUILD_PASTURE (d8h12) and the d18h1 COW buy."""
    out = copy.deepcopy(tape)
    # find the exact step/unit of the (7,4) pasture build from the reference
    build_step = build_unit = None
    for s, e in enumerate(out):
        if s // 24 != 8:
            continue
        units = [(0, e.get("farmer"))] + [(i + 1, h) for i, h in enumerate(e.get("hands") or [])]
        for wid, a in units:
            if a and a[0] == "BUILD_PASTURE":
                # where does the reference put this worker at step s?
                obs = obs_history[min(s, len(obs_history) - 1)]
                farm = (obs.get("farms") or [{}])[0]
                pos = [farm.get("farmer"), *list(farm.get("hands") or [])]
                p = pos[wid] if wid < len(pos) else None
                if p and list(p[:2]) == [7, 4]:
                    build_step, build_unit = s, wid
    if build_step is None:
        # fallback: the build at d8h12 whose NEXT step places a cow
        for s, e in enumerate(out):
            if s // 24 == 8:
                units = [(0, e.get("farmer"))] + [(i + 1, h) for i, h in enumerate(e.get("hands") or [])]
                for wid, a in units:
                    if a and a[0] == "BUILD_PASTURE":
                        nxt = out[s + 1] if s + 1 < len(out) else {}
                        nunits = [(0, nxt.get("farmer"))] + [(i + 1, h) for i, h in enumerate(nxt.get("hands") or [])]
                        for nwid, na in nunits:
                            if nwid == wid and na and na[0] == "PLACE" and len(na) > 1 and na[1] == "COW":
                                build_step, build_unit = s, wid
    if build_step is None:
        return out, {"error": "no (7,4) pasture build found"}
    e = out[build_step]
    if build_unit == 0:
        e["farmer"] = ["PASS"]
    else:
        e["hands"][build_unit - 1] = ["PASS"]
    # skip the d18h1 cow buy
    skipped = 0
    for s, e2 in enumerate(out):
        if s // 24 == 18:
            for o in (e2.get("market") or []):
                if skipped < 1 and o and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    o[0] = "SKIP"
                    skipped += 1
    out = [{**e2, "market": [o for o in (e2.get("market") or []) if o and o[0] != "SKIP"]}
           for e2 in out]
    return out, {"build_step": build_step, "build_unit": build_unit,
                 "cow_buys_skipped": skipped}


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------
_W = {}


def _init():
    m = importlib.util.spec_from_file_location("v20", V20_PATH)
    mod = importlib.util.module_from_spec(m)
    m.loader.exec_module(mod)
    _W["mod"] = mod
    _W["mod_patched"] = rc.load_v18(V20_PATH)
    suite = {}
    for name, path in (("v20", V20_PATH),
                       ("tetsu", os.path.join(ROOT, "opponents/tetsu_main.py")),
                       ("rayk", os.path.join(ROOT, "opponents/rayk_main.py")),
                       ("kaito", os.path.join(ROOT, "opponents/kaito_main.py"))):
        s = importlib.util.spec_from_file_location(name, path)
        mm = importlib.util.module_from_spec(s)
        s.loader.exec_module(mm)
        suite[name] = mm.agent
    _W["suite"] = suite


def _count_escapes(agent, seed=1, seat=0):
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    if seat == 0:
        env.run([agent, rc.pass_agent()])
    else:
        env.run([rc.pass_agent(), agent])
    anim, escapes = {}, 0
    for si in range(720):
        obs = env.steps[si][seat].get("observation", {}) or {}
        farm = (obs.get("farms") or [{}])[seat]
        cur = {}
        for y, row in enumerate(farm.get("tiles") or []):
            for x, t in enumerate(row):
                if isinstance(t, dict) and t.get("animal"):
                    cur[(x, y)] = t["animal"]
        for pos in list(anim):
            if pos not in cur:
                escapes += 1
        anim = cur
    return escapes


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


def _eval(task):
    name, seeds = task
    t0 = time.time()
    try:
        mod = _W["mod_patched"]
        tape, plants, anchors, day_starts, hires, visits, ref_reward = \
            rc.get_record(1, 0, mod, {})
        _, obs_history, _ = rc.record_reference(1, 0, mod, {})
        if name == "nocow":
            tape, rep = apply_nocow(tape, obs_history)
        elif name == "feed74":
            tape, rep = rc.compile_seat(1, 0, mod,
                                        variant={"feed74_days": [21, 23, 25, 27]})
        else:
            rep = {}
        agent = _taped_agent(_W["mod"], tape)
        rec = {"name": name, "patch": rep}
        st0 = rc.validate_tape(tape, 1, 0, mod)
        st1 = rc.validate_tape(tape, 1, 1, mod)
        rec["pass0"] = st0["reward"]
        rec["pass1"] = st1["reward"]
        rec["animals0"] = st0.get("animals_alive")
        rec["animals1"] = st1.get("animals_alive")
        rec["escapes"] = _count_escapes(agent)
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
        rec["time_s"] = round(time.time() - t0, 1)
        print(f"    [{name}] PASS ${rec['pass0']:,.0f}/${rec['pass1']:,.0f} "
              f"anim {rec['animals0']}/{rec['animals1']} escapes={rec['escapes']} | "
              + " | ".join(f"{k} {d['avg']:+,.0f} ({d['wins']}/{d['games']})"
                           for k, d in rec["vs"].items())
              + f" | {rec['time_s']}s", flush=True)
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
    ap.add_argument("--version", default="HI_AgriBot_v22_NoEscapes")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _init()
        mod = _W["mod_patched"]
        tape, plants, anchors, day_starts, hires, visits, ref = rc.get_record(1, 0, mod, {})
        _, oh, _ = rc.record_reference(1, 0, mod, {})
        t2, rep = apply_nocow(tape, oh)
        assert "error" not in rep, rep
        # no more BUILD_PASTURE at (7,4)
        for s, e in enumerate(t2):
            units = [(0, e.get("farmer"))] + [(i+1, h) for i, h in enumerate(e.get("hands") or [])]
            for wid, a in units:
                if a and a[0] == "BUILD_PASTURE":
                    obs = oh[min(s, len(oh)-1)]
                    farm = (obs.get("farms") or [{}])[0]
                    pos = [farm.get("farmer"), *list(farm.get("hands") or [])]
                    p = pos[wid] if wid < len(pos) else None
                    assert not (p and list(p[:2]) == [7, 4]), f"still builds (7,4) at s{s}"
        print("[self-test] nocow: (7,4) pasture build removed")
        # d18 cow buy removed
        n18 = sum(1 for s, e in enumerate(t2) if s // 24 == 18
                  for o in (e.get("market") or [])
                  if o and o[0] == "BUY_ANIMAL" and o[1] == "COW")
        assert n18 == 0, n18
        print("[self-test] nocow: d18 cow buy removed")
        print("[self-test] ALL PASSED")
        return
    seeds = [int(s) for s in args.seeds.split(",")]
    procs = args.procs or os.cpu_count() or 2
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"[nocow] seeds={seeds} procs={procs}", flush=True)
    print(f"[nocow] control (v20): PASS ${BASE_PASS0:,.0f}  "
          f"vs v20 {CTRL_VS['v20']:+.0f} tetsu {CTRL_VS['tetsu']:+.0f} "
          f"rayk {CTRL_VS['rayk']:+.0f} kaito {CTRL_VS['kaito']:+.0f}  escapes=1",
          flush=True)
    tasks = [("nocow", seeds), ("feed74", seeds)]
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
    print("\n[nocow] VERDICT", flush=True)
    for r in results:
        if r.get("error"):
            print(f"  {r['name']}: ERROR {r['error']}", flush=True)
            continue
        ok_pass = r["pass0"] >= BASE_PASS0 - 400 and r["pass1"] >= 162093 - 400
        ok_anim = r["animals0"] >= 13 and r["animals1"] >= 13
        ok_esc = r["escapes"] == 0
        ok_vs = all(abs(r["vs"].get(k, {}).get("avg", 0) - CTRL_VS[k]) <= 300
                    for k in CTRL_VS)
        verdict = "SHIP" if ok_pass and ok_anim and ok_esc and ok_vs else "no"
        print(f"  {r['name']}: PASS {r['pass0']:,.0f}/{r['pass1']:,.0f} "
              f"anim {r['animals0']}/{r['animals1']} escapes={r['escapes']} "
              f"-> {verdict}", flush=True)
        r["verdict"] = verdict
    ship = [r for r in results if r.get("verdict") == "SHIP"]
    json.dump({"results": results, "shippable": ship[0]["name"] if ship else None},
              open(os.path.join(OUT_DIR, "report.json"), "w"), indent=2)
    print(f"[nocow] report -> {OUT_DIR}", flush=True)
    if ship and args.build_agent:
        r = ship[0]
        mod = _W["mod_patched"]
        tape, plants, anchors, day_starts, hires, visits, ref = rc.get_record(1, 0, mod, {})
        if r["name"] == "nocow":
            _, oh, _ = rc.record_reference(1, 0, mod, {})
            tape, rep = apply_nocow(tape, oh)
        else:
            tape, rep = rc.compile_seat(1, 0, mod, variant={"feed74_days": [21, 23, 25, 27]})
        _build_agent_file(tape, args.version, r["name"])


def _build_agent_file(tape, version, tag):
    src = open(V20_PATH).read()
    header = (f'"""HI_AgriBot_v22_NoEscapes — v20 + {tag} fix '
              f'(no more (7,4) cow escape).\n'
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
                f"_v22_agent = agent\n")
    path = os.path.join(ROOT, "agent", "main_v22_noescapes.py")
    with open(path, "w") as f:
        f.write(header + body + override)
    print(f"[nocow] agent written -> {path}  VERSION = {version}", flush=True)


if __name__ == "__main__":
    main()
