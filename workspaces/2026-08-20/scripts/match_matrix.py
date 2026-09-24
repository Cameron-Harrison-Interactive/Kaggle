#!/usr/bin/env python3
"""Head-to-head match matrix: v18 vs top-player agents.

Usage:
  python3 scripts/match_matrix.py [--seeds 1-5] [--quick]
Runs each matchup on both seat orders and reports W/L + coin deltas.
"""
import argparse
import importlib.util
import sys
import time

from kaggle_environments import make

HERE = "/home/user/kaggriculture"


def load_agent(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def run_match(agent_a, agent_b, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    env.run([agent_a, agent_b])
    final = env.steps[-1]
    return final[0].reward or 0, final[1].reward or 0, final[0].status, final[1].status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="1,2,3,4,5")
    ap.add_argument("--quick", action="store_true", help="seed 1 only, both seats")
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]
    if args.quick:
        seeds = [1]

    ours = load_agent(f"{HERE}/agent/main.py", "v20")
    opponents = {
        "v18": f"{HERE}/agent/main_v18_live_backup.py",
        "v14.5_keepgate": f"{HERE}/agent/main_v14_5.py",
        "v15_backup": f"{HERE}/agent/main_v15_backup.py",
        "kaito_THUNDER#1": f"{HERE}/opponents/kaito_main.py",
        "rayk_main": f"{HERE}/opponents/rayk_main.py",
        "tetsu_main": f"{HERE}/opponents/tetsu_main.py",
        "opp_seb": f"{HERE}/scripts/opp_seb.py",
        "opp_healthstone": f"{HERE}/scripts/opp_healthstone.py",
        "opp_cowbot": f"{HERE}/scripts/opp_cowbot.py",
    }

    # Load all opponents first (fail fast)
    loaded = {}
    for name, path in opponents.items():
        try:
            loaded[name] = load_agent(path, name.replace("#", "").replace(".", "_"))
            print(f"loaded: {name}", flush=True)
        except Exception as e:
            print(f"FAILED to load {name}: {e}", flush=True)

    print(f"\n=== v18 vs opponents, seeds {seeds} ===", flush=True)
    header = f"{'opponent':<22} {'seat':<5} {'seeds':<5} {'W-L-T':<7} {'our_avg':>10} {'opp_avg':>10} {'avg_delta':>10} {'time':>6}"
    print(header, flush=True)
    print("-" * len(header), flush=True)

    summary = []
    for name, opp_agent in loaded.items():
        for seat in [0, 1]:
            wins = losses = ties = 0
            our_scores = []
            opp_scores = []
            t0 = time.time()
            for seed in seeds:
                try:
                    if seat == 0:
                        a, b, sa, sb = run_match(ours, opp_agent, seed)
                    else:
                        b, a, sb, sa = run_match(opp_agent, ours, seed)
                except Exception as e:
                    print(f"  {name} seat{seat} seed{seed} ERROR: {e}", flush=True)
                    continue
                # status may be "DONE" or error; treat reward 0 + error as loss
                if a > b:
                    wins += 1
                elif b > a:
                    losses += 1
                else:
                    ties += 1
                our_scores.append(a)
                opp_scores.append(b)
            dt = time.time() - t0
            if our_scores:
                our_avg = sum(our_scores) / len(our_scores)
                opp_avg = sum(opp_scores) / len(opp_scores)
                wlt = f"{wins}-{losses}-{ties}"
                print(f"{name:<22} {seat:<5} {len(seeds):<5} {wlt:<7} {our_avg:>10,.0f} {opp_avg:>10,.0f} {our_avg-opp_avg:>+10,.0f} {dt:>5.0f}s", flush=True)
                summary.append((name, seat, wins, losses, ties, our_avg, opp_avg))

    print("\n=== combined (both seats) ===", flush=True)
    from collections import defaultdict
    comb = defaultdict(lambda: [0, 0, 0, [], []])
    for name, seat, w, l, t, oa, oa2 in summary:
        c = comb[name]
        c[0] += w
        c[1] += l
        c[2] += t
        c[3].append(oa)
        c[4].append(oa2)
    for name, (w, l, t, our_list, opp_list) in sorted(comb.items(), key=lambda kv: -(kv[1][0] - kv[1][1])):
        all_our = sum(our_list) / max(1, len(our_list))
        all_opp = sum(opp_list) / max(1, len(opp_list))
        print(f"{name:<22} W-L-T {w}-{l}-{t}  our_avg ${all_our:,.0f}  opp_avg ${all_opp:,.0f}  delta ${all_our-all_opp:+,.0f}", flush=True)


if __name__ == "__main__":
    main()
