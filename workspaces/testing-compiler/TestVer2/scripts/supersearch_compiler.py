#!/usr/bin/env python3
"""supersearch_compiler.py — the SUPERSEARCH: brute-force variant search over
the compiled route, fighting EVERY one of our winner bots until it beats them
all without breaking a sweat.

It reuses the route_compiler_v19 engine (water-coverage recompile) and adds a
variant brute-forcer over:
  * crops     — swap PLANT types (carrot early-cash, extra strawberry,
                tomato hedge, more melon) with seed-buy compensation
  * animals   — fewer animals (drop late BUY_ANIMAL) / extra late cow
  * hires     — scale daily HIRE orders x0.8 / x1.0 / x1.2
  * sell days — shift SELLs earlier/later, split big batches (the
                'sell days amount' ledger is written for every variant)

For every combination the compiler builds BOTH seat tapes, then battles the
full opponent suite on multiple seeds x both seats. A variant is a champion
only if it beats EVERY opponent (win >= loss) with avg delta >= threshold
('no sweat'). Everything is logged to a ledger for review.

USAGE (PowerShell — one line, no backslashes):
  cd Z:\\Kaggle\\Works\\kaggriculture
  .\\scripts\\supersearch.ps1 -Seeds "1,2,3" -Opps all -Iterations 3 -Validate -BuildAgent

  # or plain python (Windows cmd / PowerShell):
  python scripts/supersearch_compiler.py --seats 0,1 --seeds 1,2,3 --opps all --iterations 3 --validate --build-agent

  --opps ours|all|v18 : ours = all our winner bots (v14.5,v15,v18,v18.5..v18.8)
                        all  = ours + top-player proxies (tetsu,kaito,rayk,seb,hs,cowbot,strawflood)
                        v18  = just v18 (fast single-seat sanity)
  --threshold N        : minimum avg delta ($) vs every opponent to count as
                         'beats no sweat' (default 200)
"""
import argparse
import copy
import importlib.util
import json
import os
import sys
import time

from kaggle_environments import make

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import route_compiler_v19 as rc  # noqa: E402

OUT_DIR = os.path.join(ROOT, "data", "supersearch")


# --------------------------------------------------------------------------
# opponent suite (every winner we have + top-player proxies)
# --------------------------------------------------------------------------
def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_suite():
    ours = {
        "v14.5": load_mod(os.path.join(ROOT, "agent", "main_v14_5.py"), "v145").agent,
        "v15": load_mod(os.path.join(ROOT, "agent", "main_v15_backup.py"), "v15").agent,
        "v18": load_mod(os.path.join(ROOT, "submit", "main.py"), "v18").agent,
        "v18.5mt": load_mod(os.path.join(ROOT, "submit", "main_multitape.py"), "v185").agent,
        "v18.6": load_mod(os.path.join(ROOT, "agent", "main_v18_6.py"), "v186").agent,
        "v18.7": load_mod(os.path.join(ROOT, "agent", "main_v18_7.py"), "v187").agent,
        "v18.8": load_mod(os.path.join(ROOT, "agent", "main_v18_8.py"), "v188").agent,
    }
    proxies = {
        "tetsu": load_mod(os.path.join(ROOT, "opponents", "tetsu_main.py"), "tetsu").agent,
        "kaito_TT": load_mod(os.path.join(ROOT, "opponents", "kaito_main.py"), "kaito").agent,
        "rayk": load_mod(os.path.join(ROOT, "opponents", "rayk_main.py"), "rayk").agent,
        "opp_seb": load_mod(os.path.join(ROOT, "scripts", "opp_seb.py"), "seb").agent,
        "opp_hs": load_mod(os.path.join(ROOT, "scripts", "opp_healthstone.py"), "hs").agent,
        "opp_cow": load_mod(os.path.join(ROOT, "scripts", "opp_cowbot.py"), "cow").agent,
    }
    # strawflood proxy tape agent
    try:
        v18mod = load_mod(os.path.join(ROOT, "submit", "main.py"), "v18mod")
        with open(os.path.join(ROOT, "data", "tapes_variants", "STRAWFLOOD32_seat0.json")) as f:
            sf0 = json.load(f)
        with open(os.path.join(ROOT, "data", "tapes_variants", "STRAWFLOOD32_seat1.json")) as f:
            sf1 = json.load(f)
        proxies["strawflood"] = rc.make_tape_agent(sf0, v18mod)
    except Exception as e:
        print(f"[suite] strawflood proxy skipped: {e}")
    return ours, proxies


# --------------------------------------------------------------------------
# variant space
# --------------------------------------------------------------------------
def variant_space():
    dims = {
        "crop": [
            {"name": "crop_base", "crop_swaps": []},
            {"name": "carrot2", "crop_swaps": [("WHEAT", "CARROT", 2)]},
            {"name": "carrot3", "crop_swaps": [("WHEAT", "CARROT", 3)]},
            {"name": "straw+8", "crop_swaps": [("WHEAT", "STRAWBERRY", 8)]},
            {"name": "straw+16", "crop_swaps": [("WHEAT", "STRAWBERRY", 16)]},
            {"name": "tomato6", "crop_swaps": [("WHEAT", "TOMATO", 6)]},
            {"name": "melon6", "crop_swaps": [("STRAWBERRY", "MELON", 6)]},
        ],
        "hires": [
            {"name": "hires0.8", "hires_mult": 0.8},
            {"name": "hires1.0", "hires_mult": 1.0},
            {"name": "hires1.2", "hires_mult": 1.2},
        ],
        "animals": [
            {"name": "anim13", "drop_animal_buys": 0},
            {"name": "anim12", "drop_animal_buys": 1},
            {"name": "anim11", "drop_animal_buys": 2},
            {"name": "anim10", "drop_animal_buys": 3},
            {"name": "extra_cow", "extra_cow": True},
        ],
        "sell": [
            {"name": "sell0", "sell_shift": 0},
            {"name": "sell-6", "sell_shift": -6},
            {"name": "sell+6", "sell_shift": 6},
            {"name": "sell+12", "sell_shift": 12},
            {"name": "sell_split", "sell_split": True},
        ],
        "water": [
            {"name": "w_daily_dist", "water_cadence": "daily", "water_priority": "distance"},
            {"name": "w_eod_dist", "water_cadence": "eod", "water_priority": "distance"},
            {"name": "w_switch_crop", "water_cadence": "switch", "water_priority": "crop",
             "water_switch_day": 14},
            {"name": "w_daily_crop", "water_cadence": "daily", "water_priority": "crop"},
            {"name": "w_eod_crop", "water_cadence": "eod", "water_priority": "crop"},
            {"name": "w_daily_young", "water_cadence": "daily", "water_priority": "young"},
            {"name": "w_switch_dist", "water_cadence": "switch", "water_priority": "distance",
             "water_switch_day": 10},
        ],
    }
    return dims


def merge_variants(*vs):
    out = {}
    for v in vs:
        out.update({k: val for k, val in v.items() if k != "name"})
    out["name"] = "+".join(v.get("name", "") for v in vs)
    return out


# --------------------------------------------------------------------------
# scoring vs the suite
# --------------------------------------------------------------------------
def score_pair(seat0_tape, seat1_tape, mod, suite, seeds, seats=(0, 1)):
    """Battle the tape pair vs every opponent. Returns {opp: {wins,games,avg}}."""
    agents = {
        0: rc.make_tape_agent(seat0_tape, mod),
        1: rc.make_tape_agent(seat1_tape, mod),
    }
    results = {}
    for name, opp in suite.items():
        wins = 0
        deltas = []
        games = 0
        for seed in seeds:
            for seat in seats:
                a = agents[seat]
                if seat == 0:
                    x, y = rc.battle(a, opp, seed, 0)
                else:
                    y, x = rc.battle(opp, a, seed, 1)
                wins += 1 if x > y else 0
                deltas.append(x - y)
                games += 1
        results[name] = {"wins": wins, "games": games,
                         "avg": sum(deltas) / games if games else 0.0,
                         "deltas": [round(d) for d in deltas]}
    return results


def suite_summary(results):
    worst_avg = min(r["avg"] for r in results.values())
    total_w = sum(r["wins"] for r in results.values())
    total_g = sum(r["games"] for r in results.values())
    losses = sum(r["games"] - r["wins"] for r in results.values())
    return {"worst_opp_avg": worst_avg, "total_wins": total_w,
            "total_games": total_g, "losses": losses}


# --------------------------------------------------------------------------
# search
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seats", default="0,1")
    ap.add_argument("--seed", type=int, default=1, help="reference seed for compiling")
    ap.add_argument("--seeds", default="1,2", help="battle seeds")
    ap.add_argument("--iterations", type=int, default=1,
                    help="search passes over the variant grid (default 1; 3+ recommended)")
    ap.add_argument("--opps", default="v18", choices=["ours", "all", "v18"])
    ap.add_argument("--threshold", type=int, default=200,
                    help="min avg delta vs EVERY opponent to count as beating it")
    ap.add_argument("--validate", action="store_true", help="validate candidates vs PASS")
    ap.add_argument("--build-agent", action="store_true",
                    help="write agent/main_v19.py from the champion tapes")
    ap.add_argument("--version", default="HI_AgriBot_v19_SuperSearch")
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--dims", default=None,
                    help="comma list of dimensions to search (crop,hires,animals,sell); "
                         "default = all")
    args = ap.parse_args()

    seats = [int(s) for s in args.seats.split(",")]
    seeds = [int(s) for s in args.seeds.split(",")]
    os.makedirs(args.out, exist_ok=True)

    mod = rc.load_v18(os.path.join(ROOT, "submit", "main.py"))
    ours, proxies = build_suite()
    if args.opps == "v18":
        suite = {"v18": ours["v18"]}
    elif args.opps == "ours":
        suite = ours
    else:
        suite = dict(ours)
        suite.update(proxies)
    print(f"[ss] suite: {', '.join(suite)} ({len(suite)} opponents)", flush=True)

    dims = variant_space()
    if args.dims:
        dims = {k: v for k, v in dims.items() if k in args.dims.split(",")}
    dim_names = list(dims)

    # ledger
    ledger_path = os.path.join(args.out, "ledger.jsonl")
    if not os.path.exists(ledger_path):
        with open(ledger_path, "w") as f:
            f.write("")

    def log_variant(name, results, sells, reward, meta):
        with open(ledger_path, "a") as f:
            f.write(json.dumps({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "variant": name,
                "scores": {k: {"wins": v["wins"], "games": v["games"], "avg": round(v["avg"], 0)}
                           for k, v in results.items()},
                "summary": suite_summary(results),
                "sell_ledger": sells,
                "reward_p0": reward,
                "meta": meta,
            }) + "\n")

    # base (no variant) compile + score
    print("[ss] compiling BASE...", flush=True)
    base_tapes = {}
    base_rewards = {}
    for seat in seats:
        tape, report = rc.compile_seat(args.seed, seat, mod)
        base_tapes[seat] = tape
        base_rewards[seat] = report.get("ref_reward")
    base_results = score_pair(base_tapes[0], base_tapes[1], mod, suite, seeds)
    base_sum = suite_summary(base_results)
    print(f"[ss] BASE: worst_opp_avg {base_sum['worst_opp_avg']:+,.0f} "
          f"W {base_sum['total_wins']}/{base_sum['total_games']}", flush=True)
    log_variant("BASE", base_results,
                rc.sell_ledger(base_tapes[0]),
                base_rewards.get(0), {"reward_seat1": base_rewards.get(1)})

    # champion state
    champion = {"tapes": {s: base_tapes[s] for s in seats},
                "name": "BASE",
                "results": base_results,
                "sum": base_sum}

    # search grid: greedy beam over dimensions, `iterations` passes
    combo = {}
    for it in range(args.iterations):
        print(f"\n[ss] ====== pass {it + 1}/{args.iterations} ======", flush=True)
        improved = False
        for dim in dim_names:
            best_v, best_key = None, None
            for v in dims[dim]:
                variant = merge_variants(combo, v)
                name = variant["name"]
                print(f"[ss]   {dim}: trying {name} ...", flush=True)
                tapes = {}
                rewards = {}
                for seat in seats:
                    tape, report = rc.compile_seat(args.seed, seat, mod, variant=variant)
                    tapes[seat] = tape
                    rewards[seat] = report.get("ref_reward")
                if args.validate:
                    st = rc.validate_tape(tapes[seats[0]], args.seed, seats[0], mod)
                    print(f"[ss]     validate: ${st['reward']:,.0f} "
                          f"crops {st['max_crops']} weeds_d15 {st['weeds_d15']} "
                          f"missed_water {st.get('total_missed_water', '?')} "
                          f"(days {st.get('missed_water_days', {})})", flush=True)
                results = score_pair(tapes[0], tapes[1], mod, suite, seeds)
                s = suite_summary(results)
                print(f"[ss]     worst_avg {s['worst_opp_avg']:+,.0f} "
                      f"W {s['total_wins']}/{s['total_games']} "
                      f"losses {s['losses']}", flush=True)
                log_variant(name, results, rc.sell_ledger(tapes[0]), rewards.get(0),
                            {"reward_seat1": rewards.get(1)})
                # keep best on this dimension (better than current combo)
                if (best_key is None or s["worst_opp_avg"] > best_key):
                    best_key = s["worst_opp_avg"]
                    best_v = (v, tapes, results, s)   # keep the RAW dim variant
            if best_v is not None:
                # fold the best raw variant of this dim into the combo
                combo = merge_variants(combo, best_v[0])
                if (best_v[3]["worst_opp_avg"] > champion["sum"]["worst_opp_avg"]):
                    champion = {"tapes": best_v[1], "name": combo["name"],
                                "results": best_v[2], "sum": best_v[3]}
                    improved = True
                    print(f"[ss]   ** NEW CHAMPION {combo['name']}: "
                          f"worst_avg {best_v[3]['worst_opp_avg']:+,.0f}", flush=True)
                    for seat in seats:
                        with open(os.path.join(args.out, f"champion_seat{seat}.json"), "w") as f:
                            json.dump(champion["tapes"][seat], f)
        if not improved:
            print("[ss] no improvement this pass — stopping early", flush=True)
            break

    # final verification + report
    print("\n[ss] ====== FINAL CHAMPION ======", flush=True)
    print(f"[ss] {champion['name']}", flush=True)
    for k, v in champion["results"].items():
        print(f"  vs {k:<12} W {v['wins']}/{v['games']} avg {v['avg']:+,.0f}", flush=True)
    print(f"[ss] worst_opp_avg {champion['sum']['worst_opp_avg']:+,.0f} "
          f"losses {champion['sum']['losses']}", flush=True)
    print("[ss] sell ledger (seat0):", flush=True)
    for item, rec in sorted(rc.sell_ledger(champion["tapes"][0]).items()):
        print(f"  {item:<12} total {rec['total']:>4} first_d{rec['first_day']:>2} "
              f"last_d{rec['last_day']:>2} batches {rec['batches']:>2} "
              f"avg_batch {rec['avg_batch']}", flush=True)

    report = {
        "champion": champion["name"],
        "suite": list(suite),
        "seeds": seeds,
        "scores": {k: {"wins": v["wins"], "games": v["games"], "avg": round(v["avg"], 0)}
                   for k, v in champion["results"].items()},
        "summary": champion["sum"],
        "sell_ledger": rc.sell_ledger(champion["tapes"][0]),
        "beats_all_no_sweat": champion["sum"]["losses"] == 0
        and champion["sum"]["worst_opp_avg"] >= args.threshold,
    }
    with open(os.path.join(args.out, "champion_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(f"[ss] report -> {os.path.join(args.out, 'champion_report.json')}")
    print(f"[ss] beats all without a sweat: {report['beats_all_no_sweat']}")

    if args.build_agent:
        with open(os.path.join(ROOT, "submit", "main.py")) as f:
            src = f.read()
        new_src = rc.inject_tapes(src, champion["tapes"][0], champion["tapes"][1],
                                  args.version)
        out_path = os.path.join(ROOT, "agent", "main_v19.py")
        with open(out_path, "w") as f:
            f.write(new_src)
        import ast
        ast.parse(new_src)
        print(f"[ss] wrote {out_path} (VERSION={args.version})", flush=True)


if __name__ == "__main__":
    main()
