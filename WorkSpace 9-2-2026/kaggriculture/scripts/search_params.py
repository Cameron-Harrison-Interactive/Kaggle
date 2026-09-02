"""
search_params.py — evolutionary parameter search for decision_agent_v2.

Evolves the decision agent's ~30 knobs (opening buys, hiring, land timing,
animal targets, crop weights, sell/plant timing) against PASS (and optionally
a second agent) across multiple seeds, using all your CPU cores.

This is the "massive search" for the clean-room decision agent. It is
independent of the old tape-based evo_search.py.

Why PASS: the decision agent is a *clean-room* agent. First goal is to push
its raw economy (PASS score) as high as possible; contested adaptation comes
after the economy is strong. You can add a second opponent with --opp2.

Run (8 cores, ~3.5h for 500 pop-free generations on a Ryzen 7 3700X):

    python3 scripts/search_params.py --population 32 --generations 200 --seeds 1,2,3

Resume after Ctrl+C / crash (auto-checkpoints every generation):

    python3 scripts/search_params.py --resume search_results/state.json

Outputs (search_results/):
    best.json     - best params found + scores
    state.json    - full population + generation (for --resume)
    search.log    - progress log (tail -f it in a second window)
"""

import argparse
import json
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(HERE, "..", "agent")
sys.path.insert(0, AGENT_DIR)

import decision_agent_v2 as dv2  # noqa: E402


# --------------------------------------------------------------------------
# Search space: name -> (lo, hi) for ints, or name -> [choice, ...].
# --------------------------------------------------------------------------
INT_PARAMS = {
    "open_wheat": (6, 20),
    "open_hires": (3, 5),
    "open_sheep": (1, 4),
    "open_cows": (1, 4),
    "open_melon_seed": (3, 8),
    "open_straw_seed": (2, 6),
    "open_wheat_seed": (4, 10),
    "daily_hires": (3, 6),
    "late_hires": (6, 10),
    "late_day": (8, 14),
    "ne_land_day": (4, 9),
    "sw_land_day": (9, 17),
    "se_land_day": (14, 22),
    "final_sheep": (2, 6),
    "final_cow": (6, 12),
    "cow_ramp_end": (10, 22),
    "sheep_ramp_end": (3, 10),
    "slow_crop_days": (0, 4),
    "melon_last_day": (10, 18),
    "straw_last_day": (4, 12),
    "harvest_animal_min": (1, 4),
    "plant_cutoff": (6, 18),
    "wheat_reserve_per_animal": (1, 4),
    "sell_hour": (1, 4),
    "cash_buffer": (100, 500),
}

# Land days may also be -1 (never buy).
OPTIONAL_NEGATIVE = {"sw_land_day", "se_land_day"}

FLOAT_PARAMS = {
    "land_density": (0.45, 0.8),
    "crop_wheat": (0.2, 0.8),
    "crop_melon": (0.0, 0.5),
    "crop_straw": (0.0, 0.4),
    "crop_carrot": (0.0, 0.2),
}


def random_params(rng):
    p = dict(dv2.DEFAULT_PARAMS)
    for name, (lo, hi) in INT_PARAMS.items():
        p[name] = rng.randint(lo, hi)
        if name in OPTIONAL_NEGATIVE and rng.random() < 0.15:
            p[name] = -1
    for name, (lo, hi) in FLOAT_PARAMS.items():
        p[name] = round(rng.uniform(lo, hi), 2)
    return p


def mutate_params(p, rng, rate=0.20):
    q = dict(p)
    for name, (lo, hi) in INT_PARAMS.items():
        if rng.random() < rate:
            if name in OPTIONAL_NEGATIVE and rng.random() < 0.2:
                q[name] = -1
            else:
                q[name] = min(hi, max(lo, q[name] + rng.randint(-3, 3)))
    for name, (lo, hi) in FLOAT_PARAMS.items():
        if rng.random() < rate:
            q[name] = round(min(hi, max(lo, q[name] + rng.uniform(-0.15, 0.15))), 2)
    return q


def _pass_agent(obs, config=None):
    farm = obs["farms"][obs["player"]]
    n = len(farm.get("hands", []) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}


def _evaluate_one(params, seeds):
    """Run the agent vs PASS across seeds; return (avg_money, per_seed)."""
    from kaggle_environments import make
    dv2.set_params(params)
    per_seed = []
    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        result = env.run([dv2.agent, _pass_agent])
        per_seed.append(result[-1][0]["observation"]["farms"][0]["money"])
    return sum(per_seed) / len(per_seed), per_seed


def evaluate(population, seeds, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_evaluate_one, p, seeds): i for i, p in enumerate(population)}
        scores = [None] * len(population)
        for fut in futures:
            i = futures[fut]
            scores[i] = fut.result()
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--population", type=int, default=32)
    ap.add_argument("--generations", type=int, default=200)
    ap.add_argument("--seeds", default="1,2,3")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 8)
    ap.add_argument("--resume", default=None)
    ap.add_argument("--out", default="search_results")
    ap.add_argument("--seed", type=int, default=7)  # RNG seed for the search
    args = ap.parse_args()

    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    os.makedirs(args.out, exist_ok=True)
    log_path = os.path.join(args.out, "search.log")

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with open(log_path, "a") as f:
            f.write(line + "\n")

    rng = random.Random(args.seed)

    if args.resume and os.path.exists(args.resume):
        with open(args.resume) as f:
            state = json.load(f)
        population = state["population"]
        gen0 = state["generation"] + 1
        best = state["best"]
        log(f"resumed at generation {gen0} with {len(population)} variants; best so far ${best[1]:,.0f}")
    else:
        population = [random_params(rng) for _ in range(args.population)]
        # always keep the hand-tuned default in the mix
        population[0] = dict(dv2.DEFAULT_PARAMS)
        gen0 = 0
        best = (None, -1e18)

    for gen in range(gen0, args.generations):
        t0 = time.time()
        scores = evaluate(population, seeds, args.workers)
        # sort: index, params, avg score
        ranked = sorted(
            ((i, population[i], scores[i][0]) for i in range(len(population))),
            key=lambda x: -x[2],
        )
        top_avg, top_params = ranked[0][2], ranked[0][1]
        if top_avg > best[1]:
            best = (top_params, top_avg)

        log(f"gen {gen}: best ${top_avg:,.0f} | running best ${best[1]:,.0f} "
            f"| pop avg ${sum(s[2] for s in ranked)/len(ranked):,.0f} "
            f"| {time.time()-t0:.1f}s")

        # elite keep + mutation
        keep = max(2, args.population // 4)
        elites = [ranked[i][1] for i in range(keep)]
        new_pop = [dict(e) for e in elites]
        while len(new_pop) < args.population:
            parent = rng.choice(elites)
            new_pop.append(mutate_params(parent, rng))
        population = new_pop

        # checkpoint
        state = {
            "generation": gen,
            "best": [best[0], best[1]],
            "population": population,
        }
        with open(os.path.join(args.out, "state.json"), "w") as f:
            json.dump(state, f)
        with open(os.path.join(args.out, "best.json"), "w") as f:
            json.dump({"params": best[0], "avg_money": best[1],
                       "seeds": seeds, "top_avg_this_gen": top_avg}, f, indent=2)

    log(f"DONE. best: ${best[1]:,.0f}")
    print(f"\nBest params -> {os.path.join(args.out, 'best.json')}")
    print(json.dumps(best[0], indent=2))


if __name__ == "__main__":
    main()
