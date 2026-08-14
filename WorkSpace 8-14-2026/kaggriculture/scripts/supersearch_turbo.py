#!/usr/bin/env python3
"""supersearch_turbo.py — v20 SURGICAL route search.

The 8-13-26 10,800-variant cartesian run finished. Verdict: NOTHING beat
base ($167,978). Crop swaps, hire scaling, dropping animals, fill, early
plant, and full-route water recompiles all lost money or lost contested
games. The old champion name was a reconstruction bug — finalists were
compiled without their parameters, so every "finalist" was the base tape.

v20 does NOT rerun that dead grid. It:

  1. Starts every variant from the proven v18 tape (never from a broken combo).
  2. Searches REAL routing: splice-recompile individual odd days (the 52-vs-62
     crop gap), x-first / y-first / greedy path styles, idle PASS->WATER,
     leftover day-26 wheat harvest, cheap feed buffer / pickup stagger.
  3. Economy-gates FIRST (skip battles if seat0 drops >8%). Last run wasted
     thousands of matches on $0 tapes.
  4. Returns the FULL variant dict so finalists actually compile what won the gate.
  5. Resumes from ledger_turbo.jsonl after reboot (default). --fresh starts over
     but BACKS UP the old ledger first.
  6. Atomic cache writes (temp + replace) so a crash cannot corrupt JSON.
  7. Validates leftover plants + animals alive, prints every dim in PowerShell.

USAGE (PowerShell, ONE line — no backslash continuations):

  python scripts\\supersearch_turbo.py --seeds 1,2,3 --opps all --finalists 20 --procs 8 --build-agent

  .\\scripts\\turbo.ps1 -Seeds "1,2,3" -Opps all -Finalists 20 -Procs 8 -BuildAgent

First run after this upgrade, wipe the old cartesian cache:

  Remove-Item -Recurse -Force data\\supersearch\\cache, data\\supersearch\\cache_records -ErrorAction SilentlyContinue; python scripts\\supersearch_turbo.py --seeds 1,2,3 --opps all --finalists 20 --procs 8 --build-agent

Resume after a reboot (default — just run the same command):

  python scripts\\supersearch_turbo.py --seeds 1,2,3 --opps all --finalists 20 --procs 8 --build-agent
"""
import argparse
import hashlib
import importlib.util
import itertools
import json
import multiprocessing
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import route_compiler_v19 as rc  # noqa: E402

OUT_DIR = os.path.join(ROOT, "data", "supersearch")
CACHE_DIR = os.path.join(OUT_DIR, "cache")

SEATS = (0, 1)
BASE_REF = {0: 167978, 1: 155325}  # compiled-base reward vs PASS (seed 1)
KEEP_FRAC = 0.92  # reject if seat0 PASS reward drops more than 8%


# --------------------------------------------------------------------------
# variant grid
# --------------------------------------------------------------------------
def _nm(parts):
    return "+".join(p for p in parts if p)


def surgical_space():
    """~2,800 BASE-preserving variants. Dead dims from the 10,800 run are gone."""
    splices = [
        ("sp0", None),
        ("sp11", [11]),
        ("sp13", [13]),
        ("sp15", [15]),
        ("sp17", [17]),
        ("sp19", [19]),
        ("sp11.13", [11, 13]),
        ("sp13.15", [13, 15]),
        ("sp15.17", [15, 17]),
        ("sp17.19", [17, 19]),
        ("sp11.13.15", [11, 13, 15]),
        ("sp13.15.17", [13, 15, 17]),
        ("sp11.13.15.17", [11, 13, 15, 17]),
        ("spOdd10s", [11, 13, 15, 17, 19]),
        ("spOddAll", [11, 13, 15, 17, 19, 21, 23, 25, 27]),
    ]
    paths = [("pg", "greedy"), ("px", "xfirst"), ("py", "yfirst")]
    prios = [("wd", "distance"), ("wy", "young")]
    idles = [("i0", 0), ("i1", 1), ("i2", 2)]
    harvests = [("h0", 0), ("h1", 1), ("h2", 2)]
    feeds = [
        ("fd0", 0, False),
        ("fb5", 5, False),
        ("fst", 0, True),
        ("fb5st", 5, True),
    ]
    grid = []
    for sname, days in splices:
        path_opts = paths if days is not None else [("pg", "greedy")]
        prio_opts = prios if days is not None else [("wd", "distance")]
        for pname, pstyle in path_opts:
            for rname, prio in prio_opts:
                for iname, idle in idles:
                    for hname, hv in harvests:
                        for fname, buf, stag in feeds:
                            v = {
                                "path_style": pstyle,
                                "water_priority": prio,
                                "idle_water": idle,
                                "leftover_harvest": hv,
                                "feed_buffer": buf,
                                "feed_stagger": stag,
                            }
                            if days is not None:
                                v["splice_days"] = list(days)
                            v["name"] = _nm([sname, pname, rname, iname, hname, fname])
                            grid.append(v)
    return grid


def cartesian_space():
    """OLD 10,800 grid — kept only for --mode cartesian. Proven dead."""
    return {
        "crop": [
            {"name": "crop0"},
            {"name": "carrot3", "crop_swaps": [("WHEAT", "CARROT", 3)]},
            {"name": "straw+8", "crop_swaps": [("WHEAT", "STRAWBERRY", 8)]},
            {"name": "melon6", "crop_swaps": [("STRAWBERRY", "MELON", 6)]},
        ],
        "hires": [
            {"name": "h1.0", "hires_mult": 1.0},
            {"name": "h0.8", "hires_mult": 0.8},
            {"name": "h1.2", "hires_mult": 1.2},
        ],
        "animals": [
            {"name": "a13"},
            {"name": "a12", "drop_animal_buys": 1},
            {"name": "a11", "drop_animal_buys": 2},
            {"name": "a10", "drop_animal_buys": 3},
            {"name": "acow", "extra_cow": True},
        ],
        "water": [
            {"name": "w_daily", "water_cadence": "daily"},
            {"name": "w_eod", "water_cadence": "eod"},
            {"name": "w_sw14", "water_cadence": "switch", "water_switch_day": 14},
            {"name": "w_crop", "water_priority": "crop"},
            {"name": "w_young", "water_priority": "young"},
        ],
        "fill": [
            {"name": "f0"},
            {"name": "f4", "plant_fill": 4},
            {"name": "f8", "plant_fill": 8},
        ],
        "early": [
            {"name": "e0"},
            {"name": "e4", "early_plant": 4},
            {"name": "e8", "early_plant": 8},
        ],
        "feed": [
            {"name": "fr0", "feed_repair": 0},
            {"name": "fr1", "feed_repair": 1},
            {"name": "fr2", "feed_repair": 2},
            {"name": "fr3", "feed_repair": 3},
        ],
    }


def merge(vs):
    out = {}
    for v in vs:
        out.update({k: val for k, val in v.items() if k != "name"})
    out["name"] = "+".join(v.get("name", "") for v in vs)
    return out


def build_grid(mode, dims_filter=None):
    if mode == "cartesian":
        space = cartesian_space()
        if dims_filter:
            space = {k: v for k, v in space.items() if k in dims_filter.split(",")}
        names, dims = zip(*space.items())
        grid = [merge(combo) for combo in itertools.product(*dims)]
    else:
        grid = surgical_space()
    seen, out = set(), []
    for v in grid:
        key = variant_key(v)
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


def variant_key(v):
    d = {k: val for k, val in v.items() if k != "name"}
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]


def describe(v):
    bits = []
    if v.get("splice_days") is not None:
        bits.append("splice:" + ",".join(str(d) for d in v["splice_days"]))
    else:
        bits.append("splice:off")
    bits.append("path:" + str(v.get("path_style", "greedy")))
    bits.append("prio:" + str(v.get("water_priority", "distance")))
    bits.append("idle:" + str(v.get("idle_water", 0)))
    bits.append("harvest:" + str(v.get("leftover_harvest", 0)))
    fb = int(v.get("feed_buffer") or 0)
    fs = bool(v.get("feed_stagger"))
    if fb and fs:
        bits.append(f"feed:buf{fb}+stagger")
    elif fb:
        bits.append(f"feed:buf{fb}")
    elif fs:
        bits.append("feed:stagger")
    else:
        bits.append("feed:off")
    if v.get("crop_swaps"):
        bits.append("crops")
    if v.get("hires_mult") and v.get("hires_mult") != 1.0:
        bits.append(f"hires:{v['hires_mult']}")
    if v.get("drop_animal_buys"):
        bits.append(f"animals:-{v['drop_animal_buys']}")
    if v.get("extra_cow"):
        bits.append("extra_cow")
    if v.get("plant_fill"):
        bits.append(f"fill:{v['plant_fill']}")
    if v.get("early_plant"):
        bits.append(f"early:{v['early_plant']}")
    if v.get("feed_repair"):
        bits.append(f"feed_repair:{v['feed_repair']}")
    if v.get("water_cadence"):
        bits.append(f"w:{v['water_cadence']}")
    return " ".join(bits)


def merge_variants(a, b):
    """Combine two surgical winners (union of days, max of flags)."""
    out = {}
    sa = set(a.get("splice_days") or [])
    sb = set(b.get("splice_days") or [])
    if sa or sb:
        out["splice_days"] = sorted(sa | sb)
    # prefer the first variant's path/prio (it ranked higher)
    out["path_style"] = a.get("path_style") or b.get("path_style") or "greedy"
    out["water_priority"] = a.get("water_priority") or b.get("water_priority") or "distance"
    out["idle_water"] = max(int(a.get("idle_water") or 0), int(b.get("idle_water") or 0))
    out["leftover_harvest"] = max(int(a.get("leftover_harvest") or 0),
                                  int(b.get("leftover_harvest") or 0))
    out["feed_buffer"] = max(int(a.get("feed_buffer") or 0), int(b.get("feed_buffer") or 0))
    out["feed_stagger"] = bool(a.get("feed_stagger") or b.get("feed_stagger"))
    sname = "sp" + ".".join(str(d) for d in out.get("splice_days", [])) if out.get("splice_days") else "sp0"
    out["name"] = _nm([
        sname,
        "p" + out["path_style"][:1],
        "w" + out["water_priority"][:1],
        f"i{out['idle_water']}",
        f"h{out['leftover_harvest']}",
        ("fb" + str(out["feed_buffer"]) + ("st" if out["feed_stagger"] else "")) if (out["feed_buffer"] or out["feed_stagger"]) else "fd0",
        "combo",
    ])
    return out


# --------------------------------------------------------------------------
# worker
# --------------------------------------------------------------------------
_W = {}


def _init(mod_path, cache_dir, opp_paths):
    _W["mod"] = rc.load_v18(mod_path)
    _W["cache"] = cache_dir
    _W["opps"] = {}
    for name, path in opp_paths.items():
        if not os.path.exists(path):
            print(f"[warn] opponent {name} missing ({path}) — skipped", flush=True)
            continue
        try:
            _W["opps"][name] = load_mod(path, name)
        except Exception as e:
            print(f"[warn] opponent {name} failed to load: {e} — skipped", flush=True)


def _compile_variant(v, seed, seats):
    key = variant_key(v)
    path = os.path.join(_W["cache"], f"{key}.json")
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
            tapes = {int(k): val for k, val in data["tapes"].items()}
            return tapes, data.get("reward0"), data.get("reward1")
        except Exception:
            try:
                os.remove(path)
            except Exception:
                pass
    mod = _W["mod"]
    tapes, r0, r1 = {}, None, None
    for seat in seats:
        tape, report = rc.compile_seat(seed, seat, mod, variant=v)
        tapes[seat] = tape
        if seat == 0:
            r0 = report.get("ref_reward")
        else:
            r1 = report.get("ref_reward")
    rc.atomic_write_json(path, {
        "tapes": {str(s): tapes[s] for s in tapes},
        "reward0": r0, "reward1": r1, "name": v.get("name"),
    })
    return tapes, r0, r1


def _fail_result(v, err, t0):
    print(f"    [{v.get('name', '?'):<28}] ERROR {type(err).__name__}: {err}", flush=True)
    return {
        "name": v.get("name", "?"), "key": variant_key(v), "variant": v,
        "gate_avg": -1e9, "gate_wins": 0, "gate_games": 0, "gate_by_opp": {},
        "reward_p0": 0, "max_crops": 0, "weeds_d15": 0, "missed_water": 0,
        "leftover_plants": 0, "leftover_units": 0, "animals_alive": 0,
        "keep": False, "time_s": round(time.time() - t0, 1), "error": str(err),
    }


def _gate_variant(task):
    v, seed, seats, gate_names, gate_seeds = task
    t0 = time.time()
    try:
        return _gate_variant_inner(v, seed, seats, gate_names, gate_seeds, t0)
    except Exception as e:
        return _fail_result(v, e, t0)


def _gate_variant_inner(v, seed, seats, gate_names, gate_seeds, t0):
    tapes, r0, r1 = _compile_variant(v, seed, seats)
    mod = _W["mod"]
    st = rc.validate_tape(tapes[0], gate_seeds[0], 0, mod)
    keep = st["reward"] >= KEEP_FRAC * BASE_REF.get(0, 160000)
    gate_total = 0.0
    gate_wins = 0
    gate_games = 0
    by_opp = {}
    if keep:
        agents = {s: rc.make_tape_agent(tapes[s], mod) for s in seats}
        gate_opps = [(n, _W["opps"][n]) for n in gate_names if n in _W["opps"]]
        for name, opp in gate_opps:
            od = 0.0
            ow = 0
            og = 0
            for gs in gate_seeds:
                for seat in seats:
                    a = agents[seat]
                    if seat == 0:
                        x, y = rc.battle(a, opp, gs, 0)
                    else:
                        y, x = rc.battle(opp, a, gs, 1)
                    od += x - y
                    ow += 1 if x > y else 0
                    og += 1
            by_opp[name] = {"avg": od / max(1, og), "wins": ow, "games": og}
            gate_total += od
            gate_wins += ow
            gate_games += og
    gate_avg = gate_total / max(1, gate_games) if gate_games else -1e9
    opp_bits = " ".join(
        f"{n} {d['avg']:+.0f} {d['wins']}/{d['games']}" for n, d in by_opp.items()
    ) or "skipped"
    print(
        f"    [{v.get('name', '?'):<28}] {describe(v)}\n"
        f"         seat0 ${st['reward']:,.0f} crops={st['max_crops']} weeds={st['weeds_d15']} "
        f"left={st.get('leftover_plants', '?')}u{st.get('leftover_units', '?')} "
        f"animals={st.get('animals_alive', '?')} missW={st.get('total_missed_water', 0)} | "
        f"gate {gate_avg:+.0f} W {gate_wins}/{gate_games} ({opp_bits}) | "
        f"{time.time() - t0:.1f}s",
        flush=True,
    )
    return {
        "name": v["name"], "key": variant_key(v),
        "variant": v,
        "gate_avg": gate_avg,
        "gate_wins": gate_wins, "gate_games": gate_games,
        "gate_by_opp": by_opp,
        "reward_p0": st["reward"], "max_crops": st["max_crops"],
        "weeds_d15": st["weeds_d15"],
        "missed_water": st.get("total_missed_water", 0),
        "leftover_plants": st.get("leftover_plants", 0),
        "leftover_units": st.get("leftover_units", 0),
        "animals_alive": st.get("animals_alive", 0),
        "keep": keep, "time_s": round(time.time() - t0, 1),
    }


def _score_finalist(task):
    v, seed, seats, suite_names, suite_seeds = task
    try:
        return _score_finalist_inner(v, seed, seats, suite_names, suite_seeds)
    except Exception as e:
        print(f"    [FINAL {v.get('name', '?'):<24}] ERROR {type(e).__name__}: {e}", flush=True)
        return {
            "name": v.get("name", "?"), "key": variant_key(v), "variant": v,
            "results": {}, "sell_ledger": {},
            "reward_p0": 0, "reward_p1": 0, "max_crops": 0,
            "weeds_d15": 0, "missed_water": 0,
            "leftover_plants": 0, "leftover_units": 0, "animals_alive": 0,
            "error": str(e),
        }


def _score_finalist_inner(v, seed, seats, suite_names, suite_seeds):
    suite = {n: _W["opps"][n] for n in suite_names if n in _W["opps"]}
    tapes, r0, r1 = _compile_variant(v, seed, seats)
    mod = _W["mod"]
    agents = {s: rc.make_tape_agent(tapes[s], mod) for s in seats}
    results = {}
    for name, opp in suite.items():
        wins = 0
        deltas = []
        games = 0
        for s in suite_seeds:
            for seat in seats:
                a = agents[seat]
                if seat == 0:
                    x, y = rc.battle(a, opp, s, 0)
                else:
                    y, x = rc.battle(opp, a, s, 1)
                wins += 1 if x > y else 0
                deltas.append(x - y)
                games += 1
        results[name] = {"wins": wins, "games": games,
                         "avg": sum(deltas) / games if games else 0.0}
    st0 = rc.validate_tape(tapes[0], suite_seeds[0], 0, mod)
    st1 = rc.validate_tape(tapes[1], suite_seeds[0], 1, mod) if 1 in tapes else {}
    print(
        f"    [FINAL {v.get('name', '?'):<24}] seat0 ${st0['reward']:,.0f} "
        f"seat1 ${st1.get('reward', 0):,.0f} left={st0.get('leftover_plants', 0)} "
        f"animals={st0.get('animals_alive', 0)} | "
        + " ".join(f"{n} {d['avg']:+.0f} {d['wins']}/{d['games']}"
                   for n, d in results.items()),
        flush=True,
    )
    return {
        "name": v["name"], "key": variant_key(v), "variant": v,
        "results": results, "sell_ledger": rc.sell_ledger(tapes[0]),
        "reward_p0": st0["reward"], "reward_p1": st1.get("reward"),
        "max_crops": st0["max_crops"],
        "weeds_d15": st0["weeds_d15"],
        "missed_water": st0.get("total_missed_water", 0),
        "leftover_plants": st0.get("leftover_plants", 0),
        "leftover_units": st0.get("leftover_units", 0),
        "animals_alive": st0.get("animals_alive", 0),
    }


# --------------------------------------------------------------------------
# suite
# --------------------------------------------------------------------------
def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def _load_done(ledger_path):
    done = {}
    if not os.path.exists(ledger_path):
        return done
    with open(ledger_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("key"):
                done[r["key"]] = r
    return done


def _backup(path):
    if not os.path.exists(path):
        return None
    stamp = time.strftime("%Y%m%d_%H%M%S")
    root, ext = os.path.splitext(path)
    dst = f"{root}_{stamp}{ext}"
    try:
        import shutil
        shutil.copy2(path, dst)
        return dst
    except Exception:
        return None


def _write_progress(path, text):
    try:
        with open(path, "w") as f:
            f.write(text)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", default="1,2", help="finalist battle seeds")
    ap.add_argument("--gate-seeds", default="1", help="fast-gate seeds")
    ap.add_argument("--opps", default="ours", choices=["v18", "ours", "all"])
    ap.add_argument("--dims", default=None, help="cartesian-only: crop,hires,animals,water,fill,early,feed")
    ap.add_argument("--mode", default="surgical", choices=["surgical", "cartesian"],
                    help="surgical = v20 BASE-preserving route search (default). cartesian = dead 10800 grid.")
    ap.add_argument("--procs", type=int, default=0, help="workers (0 = all cores). Use 8 on a 3700X.")
    ap.add_argument("--finalists", type=int, default=20, help="top-K gate scores to full-battle")
    ap.add_argument("--threshold", type=int, default=200)
    ap.add_argument("--build-agent", action="store_true")
    ap.add_argument("--version", default="HI_AgriBot_v20_Surgical")
    ap.add_argument("--limit", type=int, default=0, help="cap grid size (testing)")
    ap.add_argument("--resume", action="store_true", default=True,
                    help="skip variants already in ledger_turbo.jsonl (default ON)")
    ap.add_argument("--fresh", action="store_true",
                    help="ignore existing ledger (backs it up first) and start over")
    ap.add_argument("--no-combine", action="store_true",
                    help="skip the pairwise-combine phase after the gate")
    args = ap.parse_args()
    if args.fresh:
        args.resume = False

    seats = list(SEATS)
    seeds = [int(s) for s in args.seeds.split(",")]
    gate_seeds = [int(s) for s in args.gate_seeds.split(",")]
    procs = args.procs or os.cpu_count() or 4
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    mod_path = os.path.join(ROOT, "submit", "main.py")
    grid = build_grid(args.mode, args.dims)
    if args.limit:
        grid = grid[:args.limit]
    print(f"[turbo v20] mode={args.mode} grid={len(grid)} procs={procs} "
          f"opps={args.opps} gate_seeds={gate_seeds} resume={args.resume}",
          flush=True)
    print("[turbo v20] dead dims EXCLUDED (10,800-run proof): crop swaps, "
          "hire scale, drop animals, fill, early plant, sell, full-route recompile",
          flush=True)
    print("[turbo v20] searching: odd-day splice routes + path style + idle WATER "
          "+ leftover harvest + cheap feed buffer/stagger",
          flush=True)

    all_opp_paths = {
        "v14.5": os.path.join(ROOT, "agent", "main_v14_5.py"),
        "v15": os.path.join(ROOT, "agent", "main_v15_backup.py"),
        "v18": os.path.join(ROOT, "submit", "main.py"),
        "v18.5mt": os.path.join(ROOT, "submit", "main_multitape.py"),
        "v18.6": os.path.join(ROOT, "agent", "main_v18_6.py"),
        "v18.7": os.path.join(ROOT, "agent", "main_v18_7.py"),
        "v18.8": os.path.join(ROOT, "agent", "main_v18_8.py"),
        "tetsu": os.path.join(ROOT, "opponents", "tetsu_main.py"),
        "kaito": os.path.join(ROOT, "opponents", "kaito_main.py"),
        "rayk": os.path.join(ROOT, "opponents", "rayk_main.py"),
        "opp_seb": os.path.join(ROOT, "scripts", "opp_seb.py"),
        "opp_hs": os.path.join(ROOT, "scripts", "opp_healthstone.py"),
        "opp_cow": os.path.join(ROOT, "scripts", "opp_cowbot.py"),
    }
    all_opp_paths = {n: p for n, p in all_opp_paths.items() if os.path.exists(p)}
    # gate the two that actually matter: our own tape, and the weak matchup
    gate_names = [n for n in ("v18", "tetsu") if n in all_opp_paths]
    if "v18" not in gate_names and "v14.5" in all_opp_paths:
        gate_names = ["v14.5"] + gate_names
    print(f"[turbo v20] gate opponents: {gate_names}", flush=True)

    ledger_path = os.path.join(OUT_DIR, "ledger_turbo.jsonl")
    progress_path = os.path.join(OUT_DIR, "PROGRESS.txt")
    champ_path = os.path.join(OUT_DIR, "champion_report_turbo.json")

    done = {}
    if args.resume:
        done = _load_done(ledger_path)
        print(f"[turbo v20] resume: {len(done)} variants already in ledger", flush=True)
    else:
        bak = _backup(ledger_path)
        if bak:
            print(f"[turbo v20] backed up old ledger -> {bak}", flush=True)
        with open(ledger_path, "w") as f:
            pass

    pending = [v for v in grid if variant_key(v) not in done]
    print(f"[turbo v20] to-run: {len(pending)} / {len(grid)}", flush=True)

    # Pre-warm the shared base record ONCE in the main process so 8 Windows
    # workers do not race os.replace on rec_*_seat0.json (WinError 5).
    print("[turbo v20] pre-warming base records (both seats, once)...", flush=True)
    try:
        warm_mod = rc.load_v18(mod_path)
        for seat in seats:
            rc.get_record(1, seat, warm_mod, {})
        print("[turbo v20] base records ready", flush=True)
    except Exception as e:
        print(f"[turbo v20] pre-warm failed ({e}) — workers will record themselves",
              flush=True)

    t_start = time.time()
    results = list(done.values())
    best_gate_avg = max((r.get("gate_avg", -1e9) for r in results if r.get("keep")), default=-1e9)

    def _ingest(r, i_done, i_total):
        results.append(r)
        with open(ledger_path, "a") as f:
            f.write(json.dumps(r) + "\n")
        if r.get("keep") and r.get("gate_avg", -1e9) > ingest_state[0]:
            ingest_state[0] = r["gate_avg"]
            print(f"    [★ NEW LEADER ★] {r['name']} | Gate {r['gate_avg']:+.0f} | "
                  f"W {r['gate_wins']}/{r['gate_games']} | ${r['reward_p0']:,.0f} | "
                  f"crops {r['max_crops']} left {r.get('leftover_plants', '?')} "
                  f"animals {r.get('animals_alive', '?')}",
                  flush=True)
            try:
                rc.atomic_write_json(champ_path, {
                    "interim_best": r["name"], "variant": r.get("variant"),
                    "gate_avg": r["gate_avg"], "reward_p0": r.get("reward_p0"),
                    "max_crops": r.get("max_crops"),
                    "leftover_plants": r.get("leftover_plants"),
                    "animals_alive": r.get("animals_alive"),
                    "weeds_d15": r.get("weeds_d15"),
                    "missed_water": r.get("missed_water"),
                    "gate_by_opp": r.get("gate_by_opp"),
                })
            except Exception:
                pass
        if i_done % 10 == 0 or i_done == i_total:
            el = time.time() - t_start
            rate = i_done / max(0.001, el) * 3600
            eta = el / max(1, i_done) * (i_total - i_done) / 60
            print(f"[turbo v20] {i_done}/{i_total} done | {rate:,.0f}/hr | ETA {eta:.0f} min | "
                  f"leader gate {ingest_state[0]:+.0f}",
                  flush=True)
            _write_progress(progress_path, (
                f"v20 {i_done}/{i_total}  rate={rate:.0f}/hr  ETA={eta:.0f}min\n"
                f"leader_gate={ingest_state[0]:+.0f}\n"
                f"last={r.get('name')} keep={r.get('keep')} "
                f"rew={r.get('reward_p0')} gate={r.get('gate_avg')}\n"
            ))

    ingest_state = [best_gate_avg]

    if pending:
        pool = multiprocessing.Pool(processes=procs, initializer=_init,
                                    initargs=(mod_path, CACHE_DIR, all_opp_paths))
        tasks = [(v, 1, seats, gate_names, gate_seeds) for v in pending]
        already = len(results)
        for i, r in enumerate(pool.imap_unordered(_gate_variant, tasks, chunksize=1)):
            _ingest(r, already + i + 1, already + len(tasks))
        pool.close()
        pool.join()

    # ---------- combine phase: pairwise merge of improving operators ----------
    kept = [r for r in results if r.get("keep") and r.get("variant")]
    kept.sort(key=lambda r: -r.get("gate_avg", -1e9))
    print(f"[turbo v20] gate done in {(time.time() - t_start) / 60:.1f} min | "
          f"{len(kept)}/{len(results)} passed economy",
          flush=True)

    if not args.no_combine and args.mode == "surgical":
        base_gate = next((r["gate_avg"] for r in results
                          if r.get("name", "").startswith("sp0+") and r.get("keep")), 0.0)
        improvers = [r for r in kept if r.get("gate_avg", -1e9) > base_gate + 1][:12]
        if len(improvers) >= 2:
            combos = []
            seen_k = {variant_key(r["variant"]) for r in results if r.get("variant")}
            for i in range(len(improvers)):
                for j in range(i + 1, len(improvers)):
                    cv = merge_variants(improvers[i]["variant"], improvers[j]["variant"])
                    ck = variant_key(cv)
                    if ck not in seen_k:
                        seen_k.add(ck)
                        combos.append(cv)
            print(f"[turbo v20] combining {len(improvers)} improvers -> {len(combos)} new variants",
                  flush=True)
            if combos:
                pool = multiprocessing.Pool(processes=procs, initializer=_init,
                                            initargs=(mod_path, CACHE_DIR, all_opp_paths))
                tasks = [(v, 1, seats, gate_names, gate_seeds) for v in combos]
                already = len(results)
                for i, r in enumerate(pool.imap_unordered(_gate_variant, tasks, chunksize=1)):
                    _ingest(r, already + i + 1, already + len(tasks))
                pool.close()
                pool.join()
                kept = [r for r in results if r.get("keep") and r.get("variant")]
                kept.sort(key=lambda r: -r.get("gate_avg", -1e9))

    finalists = kept[:args.finalists]
    if not finalists:
        print("[turbo v20] no variant passed the gate — champion stays BASE / v18", flush=True)
        return

    if args.opps == "v18":
        suite_names = [n for n in ("v18",) if n in all_opp_paths]
    elif args.opps == "ours":
        suite_names = [n for n in ("v14.5", "v15", "v18", "v18.5mt", "v18.6", "v18.7", "v18.8")
                       if n in all_opp_paths]
    else:
        suite_names = list(all_opp_paths)
    print(f"[turbo v20] full-battling {len(finalists)} finalists vs "
          f"{len(suite_names)} opponents on seeds {seeds}...",
          flush=True)
    print("[turbo v20] finalists:", flush=True)
    for r in finalists:
        print(f"    {r['name']:<28} gate {r.get('gate_avg', 0):+.0f} "
              f"${r.get('reward_p0', 0):,.0f} left={r.get('leftover_plants', '?')} "
              f"animals={r.get('animals_alive', '?')}",
              flush=True)

    t2 = time.time()
    pool = multiprocessing.Pool(processes=procs, initializer=_init,
                                initargs=(mod_path, CACHE_DIR, all_opp_paths))
    # CRITICAL: pass the original variant dict, not a reconstructed stub
    ftasks = [(r["variant"], 1, seats, suite_names, seeds) for r in finalists]
    fresults = list(pool.imap_unordered(_score_finalist, ftasks))
    pool.close()
    pool.join()
    print(f"[turbo v20] finalist battles done in {(time.time() - t2) / 60:.1f} min", flush=True)

    def worst(r):
        vals = [x["avg"] for x in r["results"].values()]
        return min(vals) if vals else -1e9

    def losses(r):
        return sum(x["games"] - x["wins"] for x in r["results"].values())

    def v18_avg(r):
        return (r["results"].get("v18") or {}).get("avg", -1e9)

    # never crown something that loses to v18 worse than "about even"
    viable = [r for r in fresults if v18_avg(r) >= -500] or fresults
    champ = max(viable, key=lambda r: (worst(r), v18_avg(r), r.get("reward_p0", 0)))
    beats = losses(champ) == 0 and worst(champ) >= args.threshold

    print("\n[turbo v20] ====== CHAMPION ======", flush=True)
    print(f"  {champ['name']} | worst_avg {worst(champ):+,.0f} | losses {losses(champ)} | "
          f"reward ${champ['reward_p0']:,.0f} seat1 ${champ.get('reward_p1') or 0:,.0f} "
          f"crops {champ['max_crops']} left {champ.get('leftover_plants', 0)} "
          f"animals {champ.get('animals_alive', 0)} missed_water {champ['missed_water']}",
          flush=True)
    print(f"  dims: {describe(champ.get('variant') or {})}", flush=True)
    for k, val in sorted(champ["results"].items()):
        print(f"  vs {k:<12} W {val['wins']}/{val['games']} avg {val['avg']:+,.0f}", flush=True)
    print(f"[turbo v20] beats all no-sweat: {beats}", flush=True)
    print("[turbo v20] sell ledger (seat0):", flush=True)
    for item, rec in sorted((champ.get("sell_ledger") or {}).items()):
        print(f"  {item:<12} total {rec['total']:>4} first_d{rec['first_day']:>2} "
              f"last_d{rec['last_day']:>2} batches {rec['batches']:>2} "
              f"avg_batch {rec['avg_batch']}", flush=True)

    _W["mod"] = rc.load_v18(mod_path)
    _W["cache"] = CACHE_DIR
    champ_v = champ.get("variant") or {"name": champ["name"]}
    tapes, r0, r1 = _compile_variant(champ_v, 1, seats)
    for seat in seats:
        rc.atomic_write_json(os.path.join(OUT_DIR, f"champion_seat{seat}.json"), tapes[seat])
    report = {
        "champion": champ["name"], "variant": champ_v,
        "beats_all_no_sweat": beats,
        "scores": {k: {"wins": val["wins"], "games": val["games"], "avg": round(val["avg"], 0)}
                   for k, val in champ["results"].items()},
        "worst_avg": worst(champ), "losses": losses(champ),
        "sell_ledger": champ.get("sell_ledger"),
        "reward_p0": champ["reward_p0"], "reward_p1": champ.get("reward_p1"),
        "max_crops": champ["max_crops"],
        "missed_water": champ["missed_water"],
        "leftover_plants": champ.get("leftover_plants"),
        "leftover_units": champ.get("leftover_units"),
        "animals_alive": champ.get("animals_alive"),
        "grid_size": len(grid), "finalists": len(finalists),
        "mode": args.mode,
        "variants_per_hour": round(len(results) / max(0.001, (time.time() - t_start) / 3600)),
    }
    rc.atomic_write_json(champ_path, report)
    print(f"[turbo v20] report -> {champ_path}", flush=True)

    if args.build_agent:
        with open(os.path.join(ROOT, "submit", "main.py")) as f:
            src = f.read()
        new_src = rc.inject_tapes(src, tapes[0], tapes[1], args.version)
        out_path = os.path.join(ROOT, "agent", "main_v19.py")
        with open(out_path, "w") as f:
            f.write(new_src)
        import ast
        ast.parse(new_src)
        print(f"[turbo v20] wrote {out_path} (VERSION={args.version})", flush=True)


if __name__ == "__main__":
    main()
