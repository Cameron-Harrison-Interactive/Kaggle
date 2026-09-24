#!/usr/bin/env python3
"""supersearch_turbo.py — BRUTE-FORCE variant search at thousands/hour.

Design for SPEED (your PC, not the sandbox):
  * FULL CARTESIAN GRID: crop x hires x animals x sell x water x fill x early
    (~thousands of combos, the 'security code' search).
  * CACHE: every compiled variant is keyed by sha1 and saved to disk, so
    re-runs and later passes are instant.
  * POST-ONLY FAST PATH: sell shifts/splits and carrot swaps don't touch
    labor -> applied to the cached base tape in milliseconds (no recompile).
  * FAST GATE: every variant first fights only 2 opponents on 1 seed
    (~15s). Only the top-K finalists get the full winner suite. This is what
    makes thousands/hour possible.
  * MULTIPROCESSING: one worker per core (--procs, default = all cores).
    Each worker loads the engine once and processes variants independently.
  * LEDGER: every variant logged (gate score + sell ledger + missed-water
    audit) to data/supersearch/ledger.jsonl for your review.

USAGE (PowerShell, one line):
  cd Z:\\Kaggle\\Works\\kaggriculture
  python scripts\\supersearch_turbo.py --seeds 1,2,3 --opps all --finalists 20 --build-agent
  python scripts\\supersearch_turbo.py --dims sell,water --procs 16 --finalists 10   # quick focus

  .\\scripts\\turbo.ps1 -Seeds "1,2,3" -Opps all -Finalists 20 -BuildAgent   # wrapper

The champion must beat EVERY opponent with 0 losses and avg delta >=
threshold (--threshold, default 200) before it is accepted.
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


# --------------------------------------------------------------------------
# variant grid (cartesian)
# --------------------------------------------------------------------------
def variant_space():
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
        # sell dimension REMOVED entirely: sell_shift and sell_split both
        # break the shed-capacity choreography (verified $5.5k/$47/$1.4k/$0
        # vs $168k base). Sell timing is already optimal in the tape +
        # terminal sweep. The search fights over the levers that work:
        # crops, hires, animals, water/routing, fill, early.
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


def build_grid(dims_filter=None):
    space = variant_space()
    if dims_filter:
        space = {k: v for k, v in space.items() if k in dims_filter.split(",")}
    names, dims = zip(*space.items())
    grid = []
    for combo in itertools.product(*dims):
        v = merge(combo)
        grid.append(v)
    # dedupe by effective params
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


def is_noop(v):
    """True if the variant changes nothing vs BASE."""
    return (
        (v.get("hires_mult") or 1.0) == 1.0
        and not v.get("drop_animal_buys")
        and not v.get("extra_cow")
        and not v.get("sell_shift")
        and not v.get("sell_split")
        and not v.get("plant_fill")
        and not v.get("early_plant")
        and not v.get("crop_swaps")
        and v.get("water_cadence", "daily") in (None, "daily")
        and v.get("water_priority", "distance") in (None, "distance")
    )


def _labor_changed(v):
    """True if any labor-affecting key actually differs from BASE."""
    if (v.get("hires_mult") or 1.0) != 1.0:
        return True
    if v.get("drop_animal_buys"):
        return True
    if v.get("extra_cow"):
        return True
    if v.get("water_cadence") not in (None, "daily"):
        return True
    if v.get("water_priority") not in (None, "distance"):
        return True
    if v.get("water_switch_day"):
        return True
    if v.get("plant_fill"):
        return True
    if v.get("early_plant"):
        return True
    return False


def is_post_only(v):
    """No labor changes -> can be applied to the cached base tape (free)."""
    if _labor_changed(v):
        return False
    for (frm, to, n) in v.get("crop_swaps", []):
        if to != "CARROT":
            return False  # only carrot matures early enough to post-apply
    return True


# --------------------------------------------------------------------------
# worker (top-level for pickling)
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
    """Compile (or load from cache) both seat tapes for a variant.
    Returns (tapes{seat: tape}, reward_seat0, reward_seat1)."""
    key = variant_key(v)
    path = os.path.join(_W["cache"], f"{key}.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        tapes = {int(k): v for k, v in data["tapes"].items()}
        return tapes, data.get("reward0"), data.get("reward1")
    mod = _W["mod"]
    tapes, r0, r1 = {}, None, None
    for seat in seats:
        tape, report = rc.compile_seat(seed, seat, mod, variant=v)
        tapes[seat] = tape
        if seat == 0:
            r0 = report.get("ref_reward")
        else:
            r1 = report.get("ref_reward")
    with open(path, "w") as f:
        json.dump({"tapes": {str(s): tapes[s] for s in tapes},
                   "reward0": r0, "reward1": r1}, f)
    return tapes, r0, r1


def _gate_variant(task):
    """Compile + fast gate vs the gate opponents on gate seeds.
    Returns a dict for the ledger + finalist pool."""
    v, seed, seats, gate_names, gate_seeds = task
    gate_opps = [(n, _W["opps"][n]) for n in gate_names]
    t0 = time.time()
    if is_post_only(v):
        # post-apply to cached base (fast path)
        tapes = {}
        for seat in seats:
            base = _compile_variant({}, seed, seats)[0]
            tapes[seat] = rc.apply_sell_mutations(base[seat], v)
            tapes[seat] = rc.apply_extra_cow(tapes[seat], v)
            # carrot swap post-process
            for (frm, to, n) in v.get("crop_swaps", []):
                if to == "CARROT":
                    tapes[seat] = _post_carrot(tapes[seat], frm, n)
        r0 = r1 = None
    else:
        tapes, r0, r1 = _compile_variant(v, seed, seats)
    mod = _W["mod"]
    agents = {s: rc.make_tape_agent(tapes[s], mod) for s in seats}
    # gate score: sum of deltas vs each gate opp on gate seeds (both seats)
    gate_total = 0.0
    gate_wins = 0
    gate_games = 0
    for name, opp in gate_opps:
        for gs in gate_seeds:
            for seat in seats:
                a = agents[seat]
                if seat == 0:
                    x, y = rc.battle(a, opp, gs, 0)
                else:
                    y, x = rc.battle(opp, a, gs, 1)
                gate_total += x - y
                gate_wins += 1 if x > y else 0
                gate_games += 1
    # quick economy sanity vs PASS (1 seat, 1 seed)
    st = rc.validate_tape(tapes[0], gate_seeds[0], 0, mod)
    keep = st["reward"] >= 0.55 * BASE_REF.get(0, 160000)
    # VERBOSE: show the variant being tested + which dims it touches
    dims = []
    if v.get("water_cadence") or v.get("water_priority"):
        dims.append("routing")
    if v.get("plant_fill"):
        dims.append(f"fill{v['plant_fill']}")
    if v.get("early_plant"):
        dims.append(f"early{v['early_plant']}")
    if v.get("crop_swaps"):
        dims.append("crops")
    if v.get("hires_mult"):
        dims.append(f"hires{v['hires_mult']}")
    if v.get("drop_animal_buys"):
        dims.append(f"animals-{v['drop_animal_buys']}")
    if v.get("extra_cow"):
        dims.append("extra_cow")
    if v.get("sell_shift"):
        dims.append(f"sell{v['sell_shift']:+d}")
    if v.get("sell_split"):
        dims.append("sell_split")
    print(f"    [{v['name']}] ({', '.join(dims) or 'base'}) "
          f"gate_avg {gate_total/max(1,gate_games):+8,.0f} "
          f"W {gate_wins}/{gate_games} reward ${st['reward']:,.0f} "
          f"crops {st['max_crops']} weeds_d15 {st['weeds_d15']} "
          f"missed_water {st.get('total_missed_water', 0)}", flush=True)
    return {
        "name": v["name"], "key": variant_key(v),
        "gate_avg": gate_total / max(1, gate_games),
        "gate_wins": gate_wins, "gate_games": gate_games,
        "reward_p0": st["reward"], "max_crops": st["max_crops"],
        "weeds_d15": st["weeds_d15"], "missed_water": st.get("total_missed_water", 0),
        "keep": keep, "time_s": round(time.time() - t0, 1),
    }


def _post_carrot(tape, frm, n):
    import copy
    t = copy.deepcopy(tape)
    swapped = 0
    for e in t:
        for key in ("farmer", "hands"):
            acts = e.get(key)
            if not isinstance(acts, list):
                continue
            for i, a in enumerate(acts):
                if (isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT"
                        and a[1] == frm and swapped < n):
                    acts[i] = ["PLANT", "CARROT"]
                    swapped += 1
    # seed: convert first n WHEAT seed buys to CARROT
    left = n
    for e in t:
        mkt = e.get("market") or []
        for o in mkt:
            if left > 0 and o and o[0] == "BUY_SEED" and o[1] == "WHEAT":
                o[2] = max(0, int(o[2]) - 1)
                mkt.append(["BUY_SEED", "CARROT", 1])
                left -= 1
        if left == 0:
            break
    return t


def _score_finalist(task):
    """Full suite battle for a finalist. Returns full results dict."""
    v, seed, seats, suite_names, suite_seeds = task
    suite = {n: _W["opps"][n] for n in suite_names}
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
    st = rc.validate_tape(tapes[0], suite_seeds[0], 0, mod)
    return {
        "name": v["name"], "key": variant_key(v),
        "results": results, "sell_ledger": rc.sell_ledger(tapes[0]),
        "reward_p0": st["reward"], "max_crops": st["max_crops"],
        "weeds_d15": st["weeds_d15"], "missed_water": st.get("total_missed_water", 0),
    }


# --------------------------------------------------------------------------
# suite builders
# --------------------------------------------------------------------------
def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def build_suite(kind):
    ours = {
        "v14.5": load_mod(os.path.join(ROOT, "agent", "main_v14_5.py"), "v145"),
        "v15": load_mod(os.path.join(ROOT, "agent", "main_v15_backup.py"), "v15"),
        "v18": load_mod(os.path.join(ROOT, "submit", "main.py"), "v18"),
        "v18.5mt": load_mod(os.path.join(ROOT, "submit", "main_multitape.py"), "v185"),
        "v18.6": load_mod(os.path.join(ROOT, "agent", "main_v18_6.py"), "v186"),
        "v18.7": load_mod(os.path.join(ROOT, "agent", "main_v18_7.py"), "v187"),
        "v18.8": load_mod(os.path.join(ROOT, "agent", "main_v18_8.py"), "v188"),
    }
    if kind == "v18":
        return {"v18": ours["v18"]}
    if kind == "ours":
        return ours
    proxies = {
        "tetsu": load_mod(os.path.join(ROOT, "opponents", "tetsu_main.py"), "tetsu"),
        "kaito": load_mod(os.path.join(ROOT, "opponents", "kaito_main.py"), "kaito"),
        "rayk": load_mod(os.path.join(ROOT, "opponents", "rayk_main.py"), "rayk"),
        "opp_seb": load_mod(os.path.join(ROOT, "scripts", "opp_seb.py"), "seb"),
        "opp_hs": load_mod(os.path.join(ROOT, "scripts", "opp_healthstone.py"), "hs"),
        "opp_cow": load_mod(os.path.join(ROOT, "scripts", "opp_cowbot.py"), "cow"),
    }
    v18m = load_mod(os.path.join(ROOT, "submit", "main.py"), "v18m")
    for seat in SEATS:
        p = os.path.join(ROOT, "data", "tapes_variants", f"STRAWFLOOD32_seat{seat}.json")
        if os.path.exists(p):
            with open(p) as f:
                proxies[f"strawflood{seat}"] = rc.make_tape_agent(json.load(f), v18m)
    suite = dict(ours)
    suite.update(proxies)
    return suite


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", default="1,2", help="finalist battle seeds")
    ap.add_argument("--gate-seeds", default="1", help="fast-gate seeds")
    ap.add_argument("--opps", default="ours", choices=["v18", "ours", "all"])
    ap.add_argument("--dims", default=None, help="crop,hires,animals,sell,water,fill,early")
    ap.add_argument("--procs", type=int, default=0, help="workers (0 = all cores)")
    ap.add_argument("--finalists", type=int, default=20, help="top-K gate scores to full-battle")
    ap.add_argument("--threshold", type=int, default=200)
    ap.add_argument("--build-agent", action="store_true")
    ap.add_argument("--version", default="HI_AgriBot_v19_SuperSearch")
    ap.add_argument("--limit", type=int, default=0, help="cap grid size (testing)")
    args = ap.parse_args()

    seats = list(SEATS)
    seeds = [int(s) for s in args.seeds.split(",")]
    gate_seeds = [int(s) for s in args.gate_seeds.split(",")]
    procs = args.procs or os.cpu_count() or 4
    os.makedirs(CACHE_DIR, exist_ok=True)

    mod_path = os.path.join(ROOT, "submit", "main.py")
    grid = build_grid(args.dims)
    if args.limit:
        grid = grid[:args.limit]
    print(f"[turbo] grid: {len(grid)} variants | procs: {procs} | "
          f"opps: {args.opps} | gate seeds: {gate_seeds}", flush=True)

    # gate opponents: always v18 + v14.5 (cheap, decisive)
    gate_names = ["v18", "v14.5"]

    # pickle-safe: workers load every opponent from path inside _init
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

    # keep only opponent files that exist (fresh-folder safe)
    all_opp_paths = {n: p for n, p in all_opp_paths.items() if os.path.exists(p)}
    missing = [n for n in ("v18", "v14.5") if n not in all_opp_paths]
    if missing:
        print(f"[warn] gate opponents missing: {missing} — add them or the run "
              f"will have nothing to fight", flush=True)
    gate_names = [n for n in gate_names if n in all_opp_paths]

    t_start = time.time()
    pool = multiprocessing.Pool(processes=procs, initializer=_init,
                                initargs=(mod_path, CACHE_DIR, all_opp_paths))
    tasks = [(v, 1, seats, gate_names, gate_seeds) for v in grid]
    results = []
    for i, r in enumerate(pool.imap_unordered(_gate_variant, tasks, chunksize=2)):
        results.append(r)
        if (i + 1) % 25 == 0 or i + 1 == len(tasks):
            el = time.time() - t_start
            rate = (i + 1) / el * 3600
            print(f"[turbo] {i + 1}/{len(tasks)} done | {rate:,.0f} variants/hr | "
                  f"ETA {el / (i + 1) * (len(tasks) - i - 1) / 60:.0f} min", flush=True)
    pool.close()
    pool.join()

    # ledger
    ledger_path = os.path.join(OUT_DIR, "ledger_turbo.jsonl")
    with open(ledger_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    kept = [r for r in results if r["keep"]]
    kept.sort(key=lambda r: -r["gate_avg"])
    print(f"[turbo] gate done in {(time.time()-t_start)/60:.1f} min | "
          f"{len(kept)}/{len(results)} passed economy sanity", flush=True)

    finalists = kept[:args.finalists]
    if not finalists:
        print("[turbo] no variant passed the gate — champion stays BASE", flush=True)
        return

    if args.opps == "v18":
        suite_names = ["v18"]
    elif args.opps == "ours":
        suite_names = ["v14.5", "v15", "v18", "v18.5mt", "v18.6", "v18.7", "v18.8"]
    else:
        suite_names = list(all_opp_paths)
    print(f"[turbo] full-battling {len(finalists)} finalists vs "
          f"{len(suite_names)} opponents on seeds {seeds}...", flush=True)
    t2 = time.time()
    pool = multiprocessing.Pool(processes=procs, initializer=_init,
                                initargs=(mod_path, CACHE_DIR, all_opp_paths))
    ftasks = [(v, 1, seats, suite_names, seeds) for v in
              [{"name": r["name"], **{k: val for k, val in r.items()
                                       if k in ("crop_swaps", "hires_mult", "drop_animal_buys",
                                                "extra_cow", "sell_shift", "sell_split",
                                                "water_cadence", "water_priority",
                                                "water_switch_day", "plant_fill",
                                                "early_plant")}} for r in finalists]]
    fresults = list(pool.imap_unordered(_score_finalist, ftasks))
    pool.close()
    pool.join()
    print(f"[turbo] finalist battles done in {(time.time()-t2)/60:.1f} min", flush=True)

    # champion: losses==0 vs every opp and worst_avg >= threshold
    def worst(r):
        return min(x["avg"] for x in r["results"].values())

    def losses(r):
        return sum(x["games"] - x["wins"] for x in r["results"].values())

    champ = max(fresults, key=lambda r: worst(r))
    beats = losses(champ) == 0 and worst(champ) >= args.threshold

    print("\n[turbo] ====== CHAMPION ======", flush=True)
    print(f"  {champ['name']} | worst_avg {worst(champ):+,.0f} | losses {losses(champ)} | "
          f"reward ${champ['reward_p0']:,.0f} crops {champ['max_crops']} "
          f"missed_water {champ['missed_water']}", flush=True)
    for k, v in sorted(champ["results"].items()):
        print(f"  vs {k:<12} W {v['wins']}/{v['games']} avg {v['avg']:+,.0f}", flush=True)
    print(f"[turbo] beats all no-sweat: {beats}", flush=True)
    print("[turbo] sell ledger (seat0):", flush=True)
    for item, rec in sorted(champ["sell_ledger"].items()):
        print(f"  {item:<12} total {rec['total']:>4} first_d{rec['first_day']:>2} "
              f"last_d{rec['last_day']:>2} batches {rec['batches']:>2} "
              f"avg_batch {rec['avg_batch']}", flush=True)

    # save champion tapes (main process: init _W first)
    _W["mod"] = rc.load_v18(mod_path)
    _W["cache"] = CACHE_DIR
    tapes, r0, r1 = _compile_variant(
        {"name": champ["name"], **{k: val for k, val in champ.items()
                                    if k in ("crop_swaps", "hires_mult", "drop_animal_buys",
                                             "extra_cow", "sell_shift", "sell_split",
                                             "water_cadence", "water_priority",
                                             "water_switch_day", "plant_fill", "early_plant")}},
        1, seats)
    for seat in seats:
        with open(os.path.join(OUT_DIR, f"champion_seat{seat}.json"), "w") as f:
            json.dump(tapes[seat], f)
    report = {
        "champion": champ["name"], "beats_all_no_sweat": beats,
        "scores": {k: {"wins": v["wins"], "games": v["games"], "avg": round(v["avg"], 0)}
                   for k, v in champ["results"].items()},
        "worst_avg": worst(champ), "losses": losses(champ),
        "sell_ledger": champ["sell_ledger"],
        "reward_p0": champ["reward_p0"], "max_crops": champ["max_crops"],
        "missed_water": champ["missed_water"],
        "grid_size": len(grid), "finalists": len(finalists),
        "variants_per_hour": round(len(grid) / max(0.001, (time.time() - t_start) / 3600)),
    }
    with open(os.path.join(OUT_DIR, "champion_report_turbo.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(f"[turbo] report -> {os.path.join(OUT_DIR, 'champion_report_turbo.json')}")

    if args.build_agent:
        with open(os.path.join(ROOT, "submit", "main.py")) as f:
            src = f.read()
        new_src = rc.inject_tapes(src, tapes[0], tapes[1], args.version)
        out_path = os.path.join(ROOT, "agent", "main_v19.py")
        with open(out_path, "w") as f:
            f.write(new_src)
        import ast
        ast.parse(new_src)
        print(f"[turbo] wrote {out_path} (VERSION={args.version})", flush=True)


if __name__ == "__main__":
    main()
