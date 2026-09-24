#!/usr/bin/env python3
"""Recover an old checkpoint (top 50 only) into a full population checkpoint.
Preserves all evaluated variants and best-ever record.
Fills remaining slots with fresh random variants.

USAGE:
  python3 scripts/recover_checkpoint.py --input evo_massive/state.json --output evo_massive/state_recovered.json --population 200
"""

import argparse, json, copy, os, sys, random
from datetime import datetime

# Hardcoded parameter ranges (matches evo_search_massive.py)
PARAM_RANGES = {
    "opening_cows": (0, 14),
    "opening_sheep": (0, 14),
    "opening_wheat_seeds": (0, 20),
    "opening_melon_seeds": (0, 15),
    "opening_straw_seeds": (0, 20),
    "opening_carrot_seeds": (0, 15),
    "opening_tomato_seeds": (0, 10),
    "opening_wheat_buy": (0, 50),
    "opening_fertilizer_buy": (0, 20),
    "ne_land_day": (-1, 15),
    "sw_land_day": (-1, 15),
    "se_land_day": (-1, 20),
    "daily_hires": (2, 16),
    "hire_strategy": (0, 2),
    "wheat_sell_focus_day": (-1, 28),
    "straw_sell_timing": (0, 2),
    "melon_sell_timing": (0, 2),
    "fertilizer_sell_timing": (0, 2),
    "care_priority": (0, 3),
    "fert_collection": (0, 3),
    "fert_use_strategy": (0, 4),
    "path_style": (0, 4),
    "water_cadence": (0, 3),
    "worker_zones": (0, 4),
    "se_quad_workers": (0, 4),
}

def random_params():
    return {k: random.randint(lo, hi) for k, (lo, hi) in PARAM_RANGES.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Old checkpoint file (top 50)")
    parser.add_argument("--output", required=True, help="New recovered checkpoint file")
    parser.add_argument("--population", type=int, default=200, help="Target population size")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: {args.input} not found")
        sys.exit(1)

    with open(args.input) as f:
        old = json.load(f)

    saved_pop = old.get("population", [])
    n_saved = len(saved_pop)
    shortfall = args.population - n_saved

    print(f"Old checkpoint: {n_saved} variants")
    print(f"Target population: {args.population}")
    print(f"Adding {shortfall} fresh random variants")

    # Validate saved variants have all required params
    required_keys = set(PARAM_RANGES.keys())
    valid_saved = []
    for ind in saved_pop:
        params = ind.get("params", {})
        # Fill in any missing params with random values
        for key in required_keys:
            if key not in params:
                lo, hi = PARAM_RANGES[key]
                params[key] = random.randint(lo, hi)
        valid_saved.append({
            "params": params,
            "fitness": None,  # Reset - will re-evaluate
            "results": None,
        })

    # Generate fresh random variants
    new_random = []
    for _ in range(shortfall):
        new_random.append({
            "params": random_params(),
            "fitness": None,
            "results": None,
        })

    recovered_pop = valid_saved + new_random

    # Build new checkpoint
    new_ckpt = {
        "generation": old.get("generation", 0),
        "population": recovered_pop,
        "best_ever": old.get("best_ever", {"fitness": -999999, "params": None, "results": None, "generation": 0}),
        "no_improvement": 0,  # Reset since we're adding new variants
        "recovered_from": args.input,
        "recovered_at": datetime.now().isoformat(),
    }

    tmp = args.output + ".tmp"
    with open(tmp, 'w') as f:
        json.dump(new_ckpt, f, indent=2)
    os.replace(tmp, args.output)

    print(f"\nRECOVERED!")
    print(f"  Saved variants: {n_saved} (fitness reset for re-evaluation)")
    print(f"  New random variants: {shortfall}")
    print(f"  Total population: {len(recovered_pop)}")
    print(f"  Best ever preserved: fitness={new_ckpt['best_ever']['fitness']:.1f}")
    print(f"  Generation: {new_ckpt['generation']}")
    print(f"\n  Output: {args.output}")
    print(f"\nTo resume:")
    print(f"  python3 scripts/evo_search_massive.py --resume {args.output}")


if __name__ == "__main__":
    main()
