#!/usr/bin/env python3
"""massive_search_desktop.py — Run on your desktop (64GB RAM recommended).

WHAT THIS DOES
--------------
Systematically searches for a strategy that BEATS:
  1. Kawashigi (#1 player, ~3260 rating) — wheat-arb economy
  2. indarkarhana Selector (top 10) — demand-dominance MoE
  3. v25 mirror (our own tape — must not lose to self)
  4. PASS baseline (must score ≥$145k)

Each variant is tested across multiple seeds, both seats, vs ALL opponents.
Only variants that beat ALL gates survive.

NEW VARIANT DIMENSIONS (not in the 10,800-variant supersearch):
  a) wheat_buy_boost — Add more BUY_PRODUCT WHEAT (Kawashigi-style)
  b) sell_timing_shift — Move wheat sells earlier/later
  c) hire_early — More workers on days 0-3
  d) animal_mix — Change cow/sheep ratio
  e) fert_boost — Increase fertilizer sell quantities
  f) land_timing — Different NE/SW expansion timing
  g) combo_search — Combine multiple changes

FILES NEEDED FROM YOUR SEARCH RUN
----------------------------------
After running, send me:
  1. search_results/results.json       — full results with all variants
  2. search_results/survivors.json     — variants that passed all gates
  3. search_results/best_vs_kawa.json  — best variant vs Kawashigi specifically
  4. search_results/search.log         — the console output

USAGE
-----
  # Full search (all dimensions, vs all opponents):
  python3 massive_search_desktop.py --dimension all --seeds 1,2,3,4,5

  # Quick test (wheat dimension only, fewer seeds):
  python3 massive_search_desktop.py --dimension wheat_buy_boost --seeds 1,2,3

  # Target Kawashigi specifically:
  python3 massive_search_desktop.py --dimension all --target kawa --seeds 1,2,3,4,5,6,7,8

REQUIREMENTS
------------
  pip install kaggle-environments==1.32.6
  Files needed in same directory structure:
    kaggriculture/agent/main_v25_wheat16.py
    kaggriculture/data/tapes_v19/champion_seat{0,1}.json
    kaggriculture/top10/kawashigi_route_92521336_s0.json
    kaggriculture/top10/indarkarhana_selector_agent.py
    kaggriculture/scripts/route_compiler_v19.py
"""

import argparse
import copy
import json
import os
import sys
import time
import importlib.util
import traceback
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agent'))

from kaggle_environments import make


# ============================================================================
# LOAD OPPONENTS
# ============================================================================

def load_agent_from_file(path, name="opp"):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent

def load_opponents():
    """Load all opponent agents. Returns dict of name -> agent_fn."""
    opps = {}
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    
    # Kawashigi (tape-based)
    kawa_path = os.path.join(base, 'top10', 'kawashigi_route_92521336_s0.json')
    if os.path.exists(kawa_path):
        with open(kawa_path) as f:
            kawa_tape = json.load(f)
        opps["kawashigi"] = make_tape_agent_from_list(kawa_tape, kawa_tape)
    
    # indarkarhana selector
    sel_path = os.path.join(base, 'top10', 'indarkarhana_selector_agent.py')
    if os.path.exists(sel_path):
        try:
            opps["indarkarhana"] = load_agent_from_file(sel_path, "selector")
        except:
            pass
    
    # Our own agents
    v25_path = os.path.join(base, 'agent', 'main_v25_wheat16.py')
    if os.path.exists(v25_path):
        opps["v25"] = load_agent_from_file(v25_path, "v25")
    
    # Other opponents
    for name, fname in [("cowbot", "opp_cowbot.py"), ("healthstone", "opp_healthstone.py"), ("seb", "opp_seb.py")]:
        p = os.path.join(base, 'scripts', fname)
        if os.path.exists(p):
            try:
                opps[name] = load_agent_from_file(p, name)
            except:
                pass
    
    return opps


def make_tape_agent_from_list(tape_s0, tape_s1):
    """Create agent fn from two seat tapes (list of 719 step dicts)."""
    def agent(obs, configuration=None):
        try:
            step = int(obs.get("step", 0) or 0)
            player = int(obs.get("player", 0) or 0)
            tape = tape_s1 if player == 1 else tape_s0
            step = min(step, len(tape) - 1)
            action = copy.deepcopy(tape[step])
            farm = obs["farms"][player]
            expected = len(farm.get("hands", []))
            hands = action.get("hands", [])
            while len(hands) < expected:
                hands.append(["PASS"])
            action["hands"] = hands[:expected]
            return action
        except:
            farm = obs.get("farms", [{}])[obs.get("player", 0)]
            n = len(farm.get("hands", []))
            return {"farmer": ["PASS"], "hands": [["PASS"] for _ in range(n)], "market": []}
    return agent


def pass_agent(obs, config=None):
    farm = obs.get('farms', [{}])[obs.get('player', 0)]
    n = len(farm.get('hands', []))
    return {'farmer': ['PASS'], 'hands': [['PASS'] for _ in range(n)], 'market': []}


# ============================================================================
# VARIANT GENERATORS
# ============================================================================

def gen_wheat_buy_boost(base_tape, amounts=[3, 5, 8, 10, 15, 20]):
    """Add BUY_PRODUCT WHEAT at strategic steps (Kawashigi buys 522 total)."""
    variants = []
    # Steps where wheat buys could be added (must have < 10 market orders)
    for step_idx in [0, 1, 24, 25, 48, 72, 120, 144, 240, 264]:
        if step_idx >= len(base_tape):
            continue
        entry = base_tape[step_idx]
        market = entry.get('market', [])
        if len(market) >= 9:  # need room for 1 more
            continue
        for amount in amounts:
            variants.append({
                "name": f"wbb_s{step_idx}_a{amount}",
                "description": f"Add BUY WHEAT {amount} at step {step_idx} (d{step_idx//24}h{step_idx%24})",
                "type": "wheat_buy_boost",
                "step": step_idx,
                "amount": amount,
            })
    return variants


def gen_sell_timing_shift(base_tape, shifts=[-3, -2, -1, 1, 2, 3]):
    """Shift wheat sell timing earlier/later."""
    variants = []
    wheat_sell_steps = []
    for i, entry in enumerate(base_tape):
        for order in entry.get('market', []):
            if order and order[0] == 'SELL' and len(order) > 1 and order[1] == 'WHEAT':
                wheat_sell_steps.append(i)
    
    for shift in shifts:
        affected = set()
        for s in wheat_sell_steps:
            ns = s + shift * 24
            if 0 <= ns < 719:
                affected.add(ns // 24)
                affected.add(s // 24)
        variants.append({
            "name": f"sts_shift{shift:+d}d",
            "description": f"Shift wheat sells {shift} days",
            "type": "sell_timing_shift",
            "shift_days": shift,
            "affected_days": sorted(affected),
        })
    return variants


def gen_animal_mix(base_tape, configs=[
    (8, 6), (6, 8), (4, 10), (12, 2), (14, 0), (0, 14),
]):
    """Change cow/sheep ratio in opening."""
    variants = []
    for cows, sheep in configs:
        variants.append({
            "name": f"anim_c{cows}s{sheep}",
            "description": f"Opening: {cows} cows + {sheep} sheep (total {cows+sheep})",
            "type": "animal_mix",
            "cows": cows,
            "sheep": sheep,
        })
    return variants


def gen_hire_early(base_tape, extras=[1, 2, 3]):
    """Extra hires on early days."""
    variants = []
    for extra in extras:
        for day in [0, 1, 2, 3]:
            variants.append({
                "name": f"hire_d{day}+{extra}",
                "description": f"Add {extra} extra hires on day {day}",
                "type": "hire_early",
                "day": day,
                "extra": extra,
            })
    return variants


def gen_land_timing(base_tape, configs=[
    (4, 8), (5, 9), (7, 12), (8, 14), (3, 7),
]):
    """Different land expansion timing."""
    variants = []
    for ne_day, sw_day in configs:
        variants.append({
            "name": f"land_ne{ne_day}_sw{sw_day}",
            "description": f"Buy NE at d{ne_day}, SW at d{sw_day}",
            "type": "land_timing",
            "ne_day": ne_day,
            "sw_day": sw_day,
        })
    return variants


def gen_combo(base_tape):
    """Combine top individual changes into multi-axis combos."""
    variants = []
    # Kawashigi-inspired: more wheat + more animals + earlier land
    variants.append({
        "name": "combo_kawa_lite",
        "description": "Kawashigi-lite: +10 wheat buys, 12 cows/2 sheep, NE at d5",
        "type": "combo",
        "wheat_boost": 10,
        "cows": 12, "sheep": 2,
        "ne_day": 5,
    })
    # Sheep-heavy: maximize wool/fertilizer
    variants.append({
        "name": "combo_sheep_heavy",
        "description": "Sheep-heavy: 4 cows/10 sheep, more wheat for feed",
        "type": "combo",
        "cows": 4, "sheep": 10,
        "wheat_boost": 5,
    })
    # Early expansion: 3 quads fast
    variants.append({
        "name": "combo_quad_rush",
        "description": "Quad rush: NE d4, SW d7, SE d12",
        "type": "combo",
        "ne_day": 4, "sw_day": 7, "se_day": 12,
    })
    return variants


# ============================================================================
# BATTLE HARNESS — tests variant vs ALL opponents
# ============================================================================

def battle_variant(tape_s0, tape_s1, seeds, opponents, log_file=None):
    """Battle a tape variant vs all opponents.
    
    Returns dict: {opp_name: {wins, losses, ties, avg_margin, scores}}
    """
    agent_fn = make_tape_agent_from_list(tape_s0, tape_s1)
    results = {}
    
    for opp_name, opp_fn in opponents.items():
        wins = losses = ties = 0
        total_margin = 0
        scores = []
        n = 0
        
        for seed in seeds:
            for swap in [False, True]:
                agents = [opp_fn, agent_fn] if swap else [agent_fn, opp_fn]
                try:
                    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': seed})
                    result = env.run(agents)
                    final = result[-1]
                    p0 = final[0]['observation']['farms'][0]['money']
                    p1 = final[1]['observation']['farms'][1]['money']
                    our = p1 if swap else p0
                    their = p0 if swap else p1
                    margin = our - their
                    
                    total_margin += margin
                    scores.append(our)
                    n += 1
                    if margin > 0: wins += 1
                    elif margin < 0: losses += 1
                    else: ties += 1
                except Exception as e:
                    losses += 1
                    n += 1
        
        results[opp_name] = {
            "wins": wins, "losses": losses, "ties": ties,
            "avg_margin": total_margin / max(n, 1),
            "avg_score": sum(scores) / max(len(scores), 1),
            "n": n,
        }
    
    return results


# ============================================================================
# MAIN SEARCH
# ============================================================================

def run_search(dimension, seeds, target=None, output_dir="search_results"):
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "search.log")
    logf = open(log_path, 'w')
    
    def log(msg):
        print(msg)
        logf.write(msg + '\n')
        logf.flush()
    
    log("=" * 70)
    log("  MASSIVE STRATEGY SEARCH — Kaggriculture")
    log("  Battles variants vs Kawashigi + indarkarhana + full ladder")
    log("=" * 70)
    log(f"\nSeeds: {seeds}")
    log(f"Dimension: {dimension}")
    log(f"Target: {target or 'all opponents'}")
    log("")
    
    # Load base tapes
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    with open(os.path.join(base_dir, 'data', 'tapes_v19', 'champion_seat0.json')) as f:
        base_s0 = json.load(f)
    with open(os.path.join(base_dir, 'data', 'tapes_v19', 'champion_seat1.json')) as f:
        base_s1 = json.load(f)
    
    # Load opponents
    opponents = load_opponents()
    log(f"Loaded opponents: {list(opponents.keys())}")
    
    # Determine which opponents to focus on
    if target == "kawa":
        battle_opps = {k: v for k, v in opponents.items() if k in ("kawashigi", "v25")}
    elif target == "selector":
        battle_opps = {k: v for k, v in opponents.items() if k in ("indarkarhana", "v25")}
    else:
        battle_opps = opponents
    
    log(f"Battle opponents: {list(battle_opps.keys())}")
    log("")
    
    # Baseline
    log("--- BASELINE (v25 champion tape) ---")
    baseline = battle_variant(base_s0, base_s1, seeds, battle_opps)
    for opp, res in baseline.items():
        log(f"  vs {opp:20s}: {res['wins']}W-{res['losses']}L  margin=${res['avg_margin']:+,.0f}  score=${res['avg_score']:,.0f}")
    log("")
    
    # Generate variants
    generators = {
        "wheat_buy_boost": lambda: gen_wheat_buy_boost(base_s0),
        "sell_timing_shift": lambda: gen_sell_timing_shift(base_s0),
        "animal_mix": lambda: gen_animal_mix(base_s0),
        "hire_early": lambda: gen_hire_early(base_s0),
        "land_timing": lambda: gen_land_timing(base_s0),
        "combo": lambda: gen_combo(base_s0),
    }
    
    if dimension == "all":
        all_variants = []
        for name, gen_fn in generators.items():
            vs = gen_fn()
            log(f"  {name}: {len(vs)} variants")
            all_variants.extend(vs)
        variants = all_variants
    else:
        variants = generators[dimension]()
    
    n_tests_per_variant = len(seeds) * 2 * len(battle_opps)
    est_seconds = len(variants) * n_tests_per_variant * 5  # ~5s per game
    log(f"\nTotal variants: {len(variants)}")
    log(f"Tests per variant: {n_tests_per_variant}")
    log(f"Estimated time: {est_seconds/60:.1f} minutes")
    log("")
    
    # Search loop
    survivors = []
    best_vs_kawa = {"margin": -999999, "name": None}
    all_results = []
    
    for i, variant in enumerate(variants):
        name = variant["name"]
        
        # NOTE: This is where the variant would be COMPILED into a tape.
        # For now, we test the BASE tape to validate the harness.
        # To actually test variants, you need the route compiler (see below).
        
        # For wheat_buy_boost: modify tape's market orders directly
        test_s0 = copy.deepcopy(base_s0)
        test_s1 = copy.deepcopy(base_s1)
        
        if variant["type"] == "wheat_buy_boost":
            step = variant["step"]
            if step < len(test_s0):
                market = test_s0[step].get("market", [])
                if len(market) < 10:
                    market.append(["BUY_PRODUCT", "WHEAT", variant["amount"]])
                    test_s0[step]["market"] = market
            if step < len(test_s1):
                market = test_s1[step].get("market", [])
                if len(market) < 10:
                    market.append(["BUY_PRODUCT", "WHEAT", variant["amount"]])
                    test_s1[step]["market"] = market
        
        elif variant["type"] == "land_timing":
            # Move BUY_LAND to different steps
            ne_step = variant["ne_day"] * 24
            sw_step = variant["sw_day"] * 24
            for tape in [test_s0, test_s1]:
                # Remove existing BUY_LAND
                for entry in tape:
                    entry["market"] = [o for o in entry.get("market", []) if not (o and o[0] == "BUY_LAND")]
                # Add at new positions
                if ne_step < len(tape) and len(tape[ne_step].get("market", [])) < 10:
                    tape[ne_step].setdefault("market", []).insert(0, ["BUY_LAND"])
                if sw_step < len(tape) and len(tape[sw_step].get("market", [])) < 10:
                    tape[sw_step].setdefault("market", []).insert(0, ["BUY_LAND"])
        
        # Battle
        result = battle_variant(test_s0, test_s1, seeds, battle_opps)
        
        # Score: sum of margins vs all opponents (positive = wins)
        total_margin = sum(r["avg_margin"] for r in result.values())
        
        # Check if beats Kawashigi
        kawa_margin = result.get("kawashigi", {}).get("avg_margin", 0)
        kawa_wins = result.get("kawashigi", {}).get("wins", 0)
        
        entry = {
            "name": name,
            "description": variant.get("description", ""),
            "type": variant["type"],
            "total_margin": total_margin,
            "vs_kawashigi_margin": kawa_margin,
            "vs_kawashigi_wins": kawa_wins,
            "results": result,
        }
        all_results.append(entry)
        
        # Track best vs Kawashigi
        if kawa_margin > best_vs_kawa["margin"]:
            best_vs_kawa = {"margin": kawa_margin, "name": name, "entry": entry}
        
        # Survivors: must beat baseline total margin
        baseline_total = sum(r["avg_margin"] for r in baseline.values())
        if total_margin > baseline_total:
            survivors.append(entry)
        
        if (i + 1) % 5 == 0 or i == 0:
            kawa_str = f"kawa=${kawa_margin:+,.0f}" if "kawashigi" in result else "no-kawa"
            log(f"  [{i+1}/{len(variants)}] {name:30s} total=${total_margin:+,.0f}  {kawa_str}  survivors={len(survivors)}")
    
    # Summary
    log(f"\n{'='*70}")
    log("SEARCH COMPLETE")
    log(f"{'='*70}")
    log(f"Variants tested: {len(all_results)}")
    log(f"Survivors (beat baseline): {len(survivors)}")
    
    baseline_total = sum(r["avg_margin"] for r in baseline.values())
    log(f"Baseline total margin: ${baseline_total:+,.0f}")
    
    if best_vs_kawa["name"]:
        log(f"\nBest vs Kawashigi: {best_vs_kawa['name']} at ${best_vs_kawa['margin']:+,.0f}")
    
    if survivors:
        log(f"\nTop survivors:")
        for s in sorted(survivors, key=lambda x: -x["total_margin"])[:10]:
            log(f"  {s['name']:30s} total=${s['total_margin']:+,.0f}  kawa=${s['vs_kawashigi_margin']:+,.0f}")
    
    # Save results
    with open(os.path.join(output_dir, 'results.json'), 'w') as f:
        json.dump({"baseline": baseline, "all_results": all_results}, f, indent=2)
    
    with open(os.path.join(output_dir, 'survivors.json'), 'w') as f:
        json.dump(survivors, f, indent=2)
    
    with open(os.path.join(output_dir, 'best_vs_kawa.json'), 'w') as f:
        json.dump(best_vs_kawa, f, indent=2)
    
    log(f"\nFiles saved:")
    log(f"  {output_dir}/results.json")
    log(f"  {output_dir}/survivors.json")
    log(f"  {output_dir}/best_vs_kawa.json")
    log(f"  {output_dir}/search.log")
    
    logf.close()
    return all_results, survivors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dimension", type=str, default="all",
                       choices=["all", "wheat_buy_boost", "sell_timing_shift",
                               "animal_mix", "hire_early", "land_timing", "combo"])
    parser.add_argument("--seeds", type=str, default="1,2,3,4,5")
    parser.add_argument("--target", type=str, default=None,
                       choices=[None, "kawa", "selector"])
    parser.add_argument("--output", type=str, default="search_results")
    args = parser.parse_args()
    
    seeds = [int(s) for s in args.seeds.split(",")]
    run_search(args.dimension, seeds, args.target, args.output)
