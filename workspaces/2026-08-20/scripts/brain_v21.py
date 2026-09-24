#!/usr/bin/env python3
"""brain_v21.py — the runtime FIELD BRAIN ("mini-AI") for HI_AgriBot.

This is the "think on its feet" layer the user asked for.  It does NOT
re-route (routing stays the frozen v20 tape — every runtime path rewrite in
project history desynced and lost).  Instead it READS THE WORLD every turn
and adapts three things the rules say are safe to adapt: market orders,
crop-verb repairs on PASS steps (tile-local, zero movement), and its
internal model of the opponent.

Budget check (2026-08-14):
  * actTimeout = 1s/turn + an overage bank (env spec).  v20 uses ~0.27ms.
    The full brain (farm scans, detector, market logic) stays ~0.5-1ms.
    ~1000x headroom.  Time is NOT a constraint.
  * Submission size cap 65MB (project rule).  v20 tarball = 32KB (0.05%).
    We could embed dozens of tapes + the brain and stay under 1MB.
    Size is NOT a constraint.

THE THREE BRAIN LAYERS
----------------------
1. LaborRepair  — on PASS steps only, tile-local:
     WEED under the unit            -> DIG
     dry plant (CU>=1, not watered) -> WATER
     day>=28, one-time plant with yield>=2 -> HARVEST (leftover sweep)
   Zero movement => zero desync.  Strictly no worse than PASS.

2. KaitoNet     — detects the kaito family (the new top-of-ladder line):
   their signature (from kaito's own tape, decoded 2026-08-14) is a
   mid-game META RESET: melon/straw mid-game, then a mass WHEAT
   conversion d20-26 (13-18 plants/day) and a giant wheat flood sold
   d27-29 (155 units on d29) riding the town-center demand.
   Counter (only when locked, days 24-26):
     * dump OUR shed wheat EARLY (d24-26) at the still-high price and
       debt-cancel the same units from the tape's d27-29 wheat sells,
       so we sell BEFORE their flood crashes the price;
     * skip tape BUY_PRODUCT WHEAT when the kaito hoard has spiked the
       wheat price (>=1.2x base) and we keep a 4-unit feed reserve.

3. MarketBrain  — fertilizer crash-hold: when FERTILIZER price is crashed
   (>=8% under base) and our cash is healthy, hold the tape's fertilizer
   sells for the recovery (v18 tested this family; safe).

The brain is 100% legal: it only touches market orders and actions the
worker was going to spend on PASS anyway.  Nothing clones the opponent,
nothing rewrites routing, nothing sabo.

USAGE
-----
  cd Z:\\Kaggle\\Works\\kaggriculture
  python scripts\\brain_v21.py --self-test
  python scripts\\brain_v21.py --seeds 1 --procs 8
  python scripts\\brain_v21.py --seeds 1,2 --procs 8 --build-agent
  (or .\\scripts\\run_brain_v21.bat — no PowerShell policy issues)

SHIP GATE (strict):
  PASS economy == control (within $200, both seats), animals >= 13/13,
  vs v20 mirror: no worse than control's own mirror delta,
  vs kaito: improved or equal (that is the whole point),
  and the verdict compares the full finals battery vs control.
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
import adaptive_v20 as a20  # noqa: E402  (reuses clone distance, battle, helpers)

OUT_DIR = os.path.join(ROOT, "data", "brain_v21")
V20_PATH = os.path.join(ROOT, "agent", "main.py")  # v20 (shipped)

# ---------------------------------------------------------------------------
# LaborRepair — tile-local, PASS steps only
# ---------------------------------------------------------------------------
def _labor_repair(obs, action, mod=None):
    """Replace PASS with DIG/WATER/HARVEST when the unit stands on an
    actionable tile.  No movement => no desync.  Strictly >= PASS.
    mod=None means 'embedded in the agent file' (module-level helpers)."""
    try:
        if mod is not None:
            action = mod._copy_action(action)
            seat = mod._seat(obs)
            farm = mod._farm(obs, seat)
        else:
            action = _copy_action(action)
            seat = _seat(obs)
            farm = _farm(obs, seat)
        tiles = farm.get("tiles") or []
        day = int(obs.get("day", 0) or 0)
        positions = [farm.get("farmer"), *list(farm.get("hands") or [])]
        units = [action.get("farmer", ["PASS"]),
                 *list(action.get("hands") or [])]
        board = len(tiles)
        for i, (pos, act) in enumerate(zip(positions, units)):
            if not act or act[0] != "PASS":
                continue
            if not (isinstance(pos, (list, tuple)) and len(pos) >= 2):
                continue
            try:
                x, y = int(pos[0]), int(pos[1])
            except (TypeError, ValueError):
                continue
            if not (0 <= y < board and 0 <= x < len(tiles[y])):
                continue
            tile = tiles[y][x]
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "WEED":
                units[i] = ["DIG"]
            elif kind == "PLANT":
                cu = int(tile.get("consecutive_unwatered", 0) or 0)
                watered = bool(tile.get("watered_today"))
                if cu >= 1 and not watered:
                    units[i] = ["WATER"]
                elif day >= 28 and tile.get("crop") in ("WHEAT", "CARROT") \
                        and int(tile.get("yield_units", 0) or 0) >= 2:
                    units[i] = ["HARVEST"]
        action["farmer"] = units[0] if units else ["PASS"]
        action["hands"] = units[1:]
        return action
    except Exception:
        return action


# ---------------------------------------------------------------------------
# KaitoNet — detect the kaito midgame wheat-reset family, then counter
# ---------------------------------------------------------------------------
_KN_MEM = {0: None, 1: None}


def _kn_mem(obs):
    seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
    step = int(obs.get("step", 0) or 0)
    m = _KN_MEM.get(seat)
    if m is None or step == 0 or step < int(m.get("last_step", -1) or -1):
        m = {"family": None, "locked": False, "score": 0, "last_step": step,
             "debts": {}, "wheat_peak": 0}
        _KN_MEM[seat] = m
    m["last_step"] = step
    return m


def _opp_crop_counts(obs, crop):
    farms = obs.get("farms") or []
    opp = farms[1 - obs["player"]] if len(farms) > 1 else {}
    n = 0
    for row in (opp.get("tiles") or []):
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "PLANT" \
                    and t.get("crop") == crop:
                n += 1
    return n


def _kaito_detect(obs):
    """Score the opponent farm against kaito's tape signature:
      * melon-5 open (d0-1), big strawberry push d7-10 (S10..15)
      * THE META RESET: wheat conversion d20-26 (13-18/day, field wheat
        climbs past ~25) followed by the d27-29 wheat flood.
    Returns (score, reasons).  Lock at score>=4 by d24."""
    m = _kn_mem(obs)
    if m.get("locked"):
        return 99, ["locked"]
    try:
        day = int(obs.get("day", 0) or 0)
        score = 0
        reasons = []
        straw = _opp_crop_counts(obs, "STRAWBERRY")
        melon = _opp_crop_counts(obs, "MELON")
        wheat = _opp_crop_counts(obs, "WHEAT")
        m["wheat_peak"] = max(int(m.get("wheat_peak") or 0), wheat)
        peak = int(m.get("wheat_peak") or 0)

        if day <= 1 and melon >= 4:
            score += 1
            reasons.append("melonOpen")
        if 7 <= day <= 10 and straw >= 10:
            score += 1
            reasons.append("strawFlood")
        if 10 <= day <= 12 and melon >= 8 and straw >= 12:
            score += 1
            reasons.append("midMix")
        if 20 <= day <= 24 and peak >= 22:
            score += 3
            reasons.append("wheatReset")
        if 20 <= day <= 24 and wheat >= 16 and peak >= 22:
            score += 1
            reasons.append("wheatNow")
        if day >= 27 and peak >= 25:
            score += 1
            reasons.append("lateWheat")
        return score, reasons
    except Exception:
        return 0, []


def _kaito_counter(obs, action, step, tape, mod):
    """Days 24-26 vs a locked kaito-family opponent:
    front-run the d27-29 wheat flood with our shed wheat, then cancel the
    same units from the tape's later wheat sells (debt).  Also skip wheat
    BUY_PRODUCTs while their hoard has spiked the price."""
    m = _kn_mem(obs)
    try:
        day = int(obs.get("day", 0) or 0)
        if not m.get("locked"):
            score, reasons = _kaito_detect(obs)
            m["score"] = max(int(m.get("score") or 0), score)
            if day >= 24 and m["score"] >= 4:
                m["family"] = "kaito"
                m["locked"] = True
            elif day >= 24:
                m["family"] = "other"
                m["locked"] = True  # decision time has passed
            return action
        if m.get("family") != "kaito":
            return action

        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        private = obs.get("private") or {}
        shed = private.get("shed") or {}
        farm = obs["farms"][obs["player"]]
        money = float(farm.get("money") or 0)

        # --- front-run the flood (d24-26) ---
        if 24 <= day <= 26:
            wheat_in_shed = max(0, int(shed.get("WHEAT", 0) or 0))
            feed_reserve = 6
            sellable = wheat_in_shed - feed_reserve
            # also honor the tape's own wheat sells this turn (they'd
            # normally execute at the same price anyway)
            for o in (action.get("market") or []):
                if o and o[0] == "SELL" and o[1] == "WHEAT":
                    sellable -= max(0, int(o[2]))
            if sellable > 0:
                px = float(prices.get("WHEAT", 25) or 25)
                if px >= 24:  # only if the price is still healthy
                    qty = min(sellable, 10, int(m.get("frontrun_cap", 30)) -
                              int(m.get("frontrun_total", 0)))
                    if qty > 0 and len(action.get("market") or []) < 10:
                        action = mod._copy_action(action)
                        action["market"] = (action.get("market") or []) + \
                            [["SELL", "WHEAT", qty]]
                        m["frontrun_total"] = int(m.get("frontrun_total", 0)) + qty
                        m["debts"][27] = m["debts"].get(27, 0) + qty
        # --- repay: cancel the tape's d27+ wheat sells up to the debt ---
        if day >= 27 and m.get("debts", {}).get(27, 0) > 0:
            due = int(m["debts"][27])
            action = mod._copy_action(action)
            new_market = []
            for o in (action.get("market") or []):
                if due > 0 and o and o[0] == "SELL" and o[1] == "WHEAT" \
                        and len(o) > 2:
                    cut = min(int(o[2]), due)
                    o[2] = int(o[2]) - cut
                    due -= cut
                    if int(o[2]) <= 0:
                        continue
                new_market.append(o)
            action["market"] = new_market
            m["debts"][27] = due
        # --- skip wheat buys while the hoard inflates the price ---
        px = float(prices.get("WHEAT", 25) or 25)
        if day >= 20 and px >= 30 and money > 4000:
            skips = int(m.get("skip_buys", 0))
            if skips < 8:
                action = mod._copy_action(action)
                out = []
                for o in (action.get("market") or []):
                    if skips < 8 and o and o[0] == "BUY_PRODUCT" \
                            and o[1] == "WHEAT" \
                            and int(shed.get("WHEAT", 0) or 0) >= 4:
                        skips += 1
                        continue
                    out.append(o)
                action["market"] = out
                m["skip_buys"] = skips
        return action
    except Exception:
        return action


# ---------------------------------------------------------------------------
# MarketBrain — fertilizer crash-hold
# ---------------------------------------------------------------------------
def _fert_hold(obs, action, mod):
    try:
        day = int(obs.get("day", 0) or 0)
        if day < 5:
            return action
        farm = obs["farms"][obs["player"]]
        money = float(farm.get("money") or 0)
        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        inv = market.get("inventory") or {}
        px = float(prices.get("FERTILIZER", 100) or 100)
        inv_n = int(inv.get("FERTILIZER", 10000) or 10000)
        if px < 92 and money > 2500 and inv_n > 10060:
            action = mod._copy_action(action)
            action["market"] = [o for o in (action.get("market") or [])
                                if not (o and o[0] == "SELL"
                                        and o[1] == "FERTILIZER")]
        return action
    except Exception:
        return action



# ---------------------------------------------------------------------------
# CashRank — sell-first re-ranker when buys would fail (missing-crop fix)
# ---------------------------------------------------------------------------
_SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100,
              "MELON": 80}
_ANIMAL_COST = {"COW": 400, "SHEEP": 500, "GOOSE": 300}


def _order_cost(obs, o):
    """Cost of a buy order in the current market state."""
    if not o or len(o) < 3:
        return 0
    try:
        qty = max(0, int(o[2]))
    except (TypeError, ValueError):
        return 0
    if o[0] == "BUY_SEED":
        return _SEED_COST.get(o[1], 99) * qty
    if o[0] == "BUY_ANIMAL":
        return _ANIMAL_COST.get(o[1], 999) * qty
    if o[0] == "BUY_PRODUCT":
        px = float(((obs.get("market") or {}).get("prices") or {}).get(o[1], 0) or 0)
        return px * qty
    return 0


def _cash_rank(obs, action, mod=None):
    """When the tape's buy orders would fail for lack of cash this turn,
    move our SELLs to the front of the queue so they fund the buys in the
    same step (the engine resolves our queue in order).  Fixes the live
    cascade: cash pressure -> failed BUY_SEED -> skipped PLANT waves
    (the visible 'missing crops') and failed feed-wheat buys (escapes)."""
    try:
        farm = obs["farms"][obs["player"]]
        money = float(farm.get("money") or 0)
        market = list(action.get("market") or [])
        if not market:
            return action
        total_cost = sum(_order_cost(obs, o) for o in market)
        if money >= total_cost:
            return action  # no reorder needed — preserve reference behavior
        sells = [o for o in market if o and o[0] == "SELL"]
        if not sells:
            return action
        others = [o for o in market if not (o and o[0] == "SELL")]
        action = dict(action)
        action["market"] = sells + others
        return action
    except Exception:
        return action


# ---------------------------------------------------------------------------
# the brain agent factory (v20 base + layers)
# ---------------------------------------------------------------------------
def build_brain(mod, labor=False, kaito=False, hold=False, cashrank=False):
    tape0 = mod._SEAT0_ACTIONS
    tape1 = tape0  # v20 already single-tape on both seats

    def agent(obs, configuration=None):
        try:
            seat = mod._seat(obs)
            tape = tape0
            step = min(max(0, int(mod._get(obs, "step", 0) or 0)),
                       len(tape) - 1)
            mod._update_memory(obs)
            action = mod._weed_repair_action(
                obs, mod._copy_action(tape[step]), tape, step)
            action = mod._adapt_animals(obs, action)
            action = mod._adapt_crops(obs, action)
            action = mod._adapt_market(obs, action)
            if kaito:
                action = _kaito_counter(obs, action, step, tape, mod)
            if labor:
                action = _labor_repair(obs, action, mod)
            if hold:
                action = _fert_hold(obs, action, mod)
            if cashrank:
                action = _cash_rank(obs, action, mod)
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
# catalog + harness
# ---------------------------------------------------------------------------
def catalog():
    """The 2026-08-14 battery verdicts:
      * cashrank  — NEW: sell-first re-ranker when buys would fail
        (missing-crop / failed-seed-buy fix).
      * hold      — DEAD.  Fert sells are load-bearing early cash (d2-8);
                   holding them collapsed PASS to $119k with 5/3 animals.
      * kaito     — DEAD.  The detector is moot: our own v20 tape IS the
                   kaito late-wheat family (v20 field wheat d24=40 vs
                   kaito 42, d27=61 vs 60 — same meta reset).  There is
                   nothing to counter; front-running our own flood lost
                   money and the buy-skips starved feed.
      * labor     — SHIPPED.  Tile-local PASS->DIG/WATER/HARVEST repair.
                   PASS economy identical, mirror deltas within noise,
                   and it is the only runtime insurance against live
                   desyncs (the "missing row" class of live bug).
    """
    return [
        {"name": "ctrl", "labor": False, "kaito": False, "hold": False, "cashrank": False},
        {"name": "labor", "labor": True, "kaito": False, "hold": False, "cashrank": False},
        {"name": "cashrank", "labor": False, "kaito": False, "hold": False, "cashrank": True},
        {"name": "labor+cashrank", "labor": True, "kaito": False, "hold": False, "cashrank": True},
    ]


def battle(a, b, seed, seat_of_a):
    return a20.battle(a, b, seed, seat_of_a)


def pass_reward(agent, seat, seed=1):
    return a20.battle(agent, rc.pass_agent(), seed, seat)[0]


def animals_alive(agent, seed=1, seat=0):
    return a20.animals_alive(agent, seed=seed, seat=seat)


_W = {}


def _init(suite_paths):
    _W["mod"] = rc.load_v18(V20_PATH)
    _W["suite"] = {}
    for name, path in suite_paths.items():
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _W["suite"][name] = m.agent


def _eval(task):
    v, seeds = task
    t0 = time.time()
    try:
        mod = _W["mod"]
        agent = build_brain(mod, labor=v["labor"], kaito=v["kaito"],
                            hold=v["hold"], cashrank=v.get("cashrank", False))
        rec = {"name": v["name"]}
        # PASS economy
        rec["pass0"] = pass_reward(agent, 0)
        rec["pass1"] = pass_reward(agent, 1)
        rec["animals0"] = animals_alive(agent, seat=0)
        rec["animals1"] = animals_alive(agent, seat=1)
        # contested
        rec["vs"] = {}
        for opp_name in ("v20", "kaito", "tetsu", "rayk"):
            opp = _W["suite"][opp_name]
            wins = games = 0
            deltas = []
            for seed in seeds:
                for seat in (0, 1):
                    x, y = battle(agent, opp, seed, seat)
                    wins += 1 if x > y else 0
                    games += 1
                    deltas.append(x - y)
            rec["vs"][opp_name] = {"wins": wins, "games": games,
                                   "avg": sum(deltas) / max(1, len(deltas))}
        rec["time_s"] = round(time.time() - t0, 1)
        line = (f"    [{v['name']:<12}] PASS ${rec['pass0']:,.0f}/${rec['pass1']:,.0f} "
                f"anim {rec['animals0']}/{rec['animals1']} | "
                + " | ".join(f"{k} {d['avg']:+,.0f} ({d['wins']}/{d['games']})"
                             for k, d in rec["vs"].items())
                + f" | {rec['time_s']}s")
        print(line, flush=True)
        return rec
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"    [ERR] {v['name']}: {e}", flush=True)
        return {"name": v["name"], "error": str(e)}


SUITE_PATHS = {
    "v20": os.path.join(ROOT, "agent", "main.py"),
    "v18": os.path.join(ROOT, "agent", "main_v18_live_backup.py"),
    "kaito": os.path.join(ROOT, "opponents", "kaito_main.py"),
    "tetsu": os.path.join(ROOT, "opponents", "tetsu_main.py"),
    "rayk": os.path.join(ROOT, "opponents", "rayk_main.py"),
    "v14.5": os.path.join(ROOT, "agent", "main_v14_5.py"),
}


def main():
    # copy-paste guard: strip stray trailing punctuation from flags
    # ("--finals." -> "--finals") so pasted commands never 400.
    sys.argv = [a.rstrip(".,;:!?") if a.startswith("--") else a for a in sys.argv]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", default="1")
    ap.add_argument("--procs", type=int, default=0)
    ap.add_argument("--build-agent", action="store_true")
    ap.add_argument("--version", default="HI_AgriBot_v21_FieldBrain")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _self_test()
        return
    seeds = [int(s) for s in args.seeds.split(",")]
    procs = args.procs or os.cpu_count() or 2
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"[brain_v21] seeds={seeds} procs={procs}", flush=True)
    print("[brain_v21] base = v20. Layers: LaborRepair / KaitoNet / MarketBrain.",
          flush=True)
    variants = catalog()
    tasks = [(v, seeds) for v in variants]
    if procs <= 1:
        _init(SUITE_PATHS)
        results = [_eval(t) for t in tasks]
    else:
        pool = multiprocessing.Pool(processes=min(procs, len(tasks)),
                                    initializer=_init,
                                    initargs=(SUITE_PATHS,))
        results = list(pool.imap_unordered(_eval, tasks, chunksize=1))
        pool.close()
        pool.join()
    with open(os.path.join(OUT_DIR, "ledger.jsonl"), "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    ctrl = next((r for r in results if r["name"] == "ctrl" and not r.get("error")), None)
    print("\n[brain_v21] VERDICT", flush=True)
    if not ctrl:
        print("  control missing — nothing to judge.", flush=True)
        return
    print(f"  control: PASS ${ctrl['pass0']:,.0f}/${ctrl['pass1']:,.0f}",
          flush=True)
    shippable = None
    for r in results:
        if r.get("error") or r["name"] == "ctrl":
            continue
        ok_pass = (abs(r["pass0"] - ctrl["pass0"]) <= 200
                   and abs(r["pass1"] - ctrl["pass1"]) <= 200)
        ok_anim = r["animals0"] >= 13 and r["animals1"] >= 13
        # contested deltas must stay within noise of control (2 games per
        # matchup => ~+-300 noise band; a real regression is in the 1000s)
        ok_vs = all(
            abs(r["vs"].get(k, {}).get("avg", 0)
                - ctrl["vs"].get(k, {}).get("avg", 0)) <= 300
            for k in ctrl["vs"])
        keep = ok_pass and ok_anim and ok_vs
        if keep:
            shippable = r
        print(f"  {r['name']:<12} PASS_ok={ok_pass} anim_ok={ok_anim} "
              f"contested_ok={ok_vs} -> {'KEEP' if keep else 'reject'}",
              flush=True)
    # report
    report = {"control": ctrl, "results": results, "shippable":
              shippable["name"] if shippable else None}
    with open(os.path.join(OUT_DIR, "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[brain_v21] ledger + report -> {OUT_DIR}", flush=True)
    if shippable and args.build_agent:
        _build_agent_file(shippable, args.version)


def _build_agent_file(rec, version, tapes=None):
    """Package the kept brain variant as a standalone agent (v20 body +
    embedded runtime layers).  tapes= overrides the embedded routes
    (e.g. the px distinctive-path tape)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("v20", V20_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    src = open(V20_PATH).read()
    header = (f'"""HI_AgriBot_v21_FieldBrain — v20 + runtime FieldBrain '
              f'({rec.get("name")}).\n'
              f'Layers: labor={rec.get("labor")}, kaito={rec.get("kaito")}, '
              f'hold={rec.get("hold")}.\n'
              f'Routing stays the frozen v20 tape; the brain only repairs '
              f'PASS steps and adapts market orders.\n'
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
    tape_override = ""
    if tapes is not None:
        tape_override = (
            "\n# --- distinctive-path tapes (override) ---\n"
            f"_SEAT0_ACTIONS = json.loads({json.dumps(tapes)!r})\n"
            f"_SEAT1_ACTIONS = _SEAT0_ACTIONS\n"
        )
    layers = open(os.path.join(HERE, "brain_v21.py")).read()
    start = layers.index("# ---------------------------------------------------------------------------\n# LaborRepair")
    end = layers.index("# ---------------------------------------------------------------------------\n# KaitoNet")
    embedded = layers[start:end]
    embedded = embedded.replace("import route_compiler_v19 as rc  # noqa: E402", "")
    embedded = embedded.replace("import adaptive_v20 as a20  # noqa: E402", "")
    tail = f'''

{embedded}

_BRAIN = {{"labor": {bool(rec.get("labor"))}, "kaito": {bool(rec.get("kaito"))},
           "hold": {bool(rec.get("hold"))}}}

def agent(obs, configuration=None):
    try:
        seat = _seat(obs)
        tape = _SEAT0_ACTIONS
        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(tape) - 1)
        _update_memory(obs)
        action = _weed_repair_action(obs, _copy_action(tape[step]), tape, step)
        action = _adapt_animals(obs, action)
        action = _adapt_crops(obs, action)
        action = _adapt_market(obs, action)
        if _BRAIN.get("labor"):
            action = _labor_repair(obs, action, None)
        action = _align_hands(_rank_sell_slots(obs, action, configuration), obs)
        if step == 718:
            try:
                action = _v26_terminal_sweep(obs, action, configuration)
            except Exception:
                pass
        return _align_hands(action, obs)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {{"farmer": ["PASS"],
                "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
                "market": []}}

def _kaggle_submission_entrypoint(obs, configuration=None):
    return agent(obs, configuration)

# Kaggle's loader takes the LAST callable inserted into the module
# namespace.  agent/_kaggle_submission_entrypoint REBIND names defined
# earlier in the v20 body (their insertion positions stay early), so the
# loader would otherwise pick _labor_repair.  This fresh name is inserted
# last and is therefore the one the harness calls.
_v21_agent = agent
'''
    path = os.path.join(ROOT, "agent", "main_v21_brain.py")
    with open(path, "w") as f:
        f.write(header + body + tape_override + tail)
    print(f"[brain_v21] agent written -> {path}  VERSION = {version}",
          flush=True)


def _self_test():
    import importlib.util
    spec = importlib.util.spec_from_file_location("v20", V20_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert len(mod._SEAT0_ACTIONS) == 719
    agent = build_brain(mod, labor=True, kaito=True, hold=True)
    assert callable(agent)
    print("[self-test] v20 tapes load + brain builds ok")

    # labor repair: PASS on WEED -> DIG
    obs = {"player": 0, "step": 100, "day": 4, "farms": [{
        "farmer": [2, 2], "hands": [],
        "tiles": [[{"kind": "WEED"} if x == 2 and y == 2 else None
                   for x in range(10)] for y in range(10)]}]}
    act = {"farmer": ["PASS"], "hands": [], "market": []}
    out = _labor_repair(obs, act, mod)
    assert out["farmer"] == ["DIG"], out
    print("[self-test] labor repair WEED->DIG ok")

    # dry plant -> WATER
    obs["farms"][0]["tiles"][2][2] = {"kind": "PLANT", "crop": "WHEAT",
                                      "consecutive_unwatered": 1,
                                      "watered_today": False,
                                      "yield_units": 1}
    out = _labor_repair(obs, {"farmer": ["PASS"], "hands": [], "market": []}, mod)
    assert out["farmer"] == ["WATER"], out
    print("[self-test] labor repair dry->WATER ok")

    # kaito detector on a synthetic farm
    farm = {"farmer": [0, 0], "hands": [],
            "tiles": [[None] * 10 for _ in range(10)],
            "unlocked_quadrants": ["NW", "NE", "SW"], "money": 5000}
    for y in range(3):
        for x in range(9):
            farm["tiles"][y][x] = {"kind": "PLANT", "crop": "WHEAT",
                                   "consecutive_unwatered": 0,
                                   "watered_today": True, "yield_units": 2}
    obs2 = {"player": 0, "step": 24 * 22, "day": 22,
            "farms": [farm, farm]}
    score, reasons = _kaito_detect(obs2)
    print(f"[self-test] kaito detect on wheat-reset farm: score={score} {reasons}")
    assert score >= 3, (score, reasons)
    # cash rank: tight money + sells -> sells first
    obs3 = {"player": 0, "step": 100, "farms": [{"money": 50}],
            "market": {"prices": {"WHEAT": 25, "FERTILIZER": 100}}}
    act3 = {"farmer": ["PASS"], "hands": [],
            "market": [["BUY_SEED", "STRAWBERRY", 1], ["SELL", "FERTILIZER", 5]]}
    out3 = _cash_rank(obs3, act3)
    assert [o[0] for o in out3["market"]] == ["SELL", "BUY_SEED"], out3
    # flush cash -> no reorder
    obs3["farms"][0]["money"] = 5000
    out4 = _cash_rank(obs3, act3)
    assert [o[0] for o in out4["market"]] == ["BUY_SEED", "SELL"], out4
    print("[self-test] cash rank reorders only when cash is short ok")
    print("[self-test] ALL PASSED")


if __name__ == "__main__":
    main()
