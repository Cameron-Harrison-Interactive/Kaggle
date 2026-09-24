#!/usr/bin/env python3
"""MASSIVE EVOLUTIONARY SEARCH - True Meta Discovery

This is NOT v25 optimization. This is discovering NEW strategies from scratch.

APPROACH:
- 1000+ random variants per generation (not 16 seeds)
- Full parameter space exploration (every crop/timing/route combo possible)
- Test against ALL 6 opponents from generation 1 (no easy mode)
- Fitness = win_rate + margin across all opponents
- High mutation rate (50% full random reset) for maximum diversity
- Novelty bonus: reward strategies that are different from each other

This will find strategies we haven't even thought of.
"""

import argparse, copy, json, os, sys, time, random, importlib.util, signal
import multiprocessing as mp
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agent'))
from kaggle_environments import make

# ============================================================================
# FULL PARAMETER SPACE - Everything is variable
# ============================================================================

PARAM_RANGES = {
    # Opening buys (0 = don't buy, max = buy a lot)
    "opening_cows": (0, 14),
    "opening_sheep": (0, 14),
    "opening_wheat_seeds": (0, 20),
    "opening_melon_seeds": (0, 15),
    "opening_straw_seeds": (0, 20),
    "opening_carrot_seeds": (0, 15),
    "opening_tomato_seeds": (0, 10),
    "opening_wheat_buy": (0, 50),  # Kawashigi buys 522, we explore 0-50
    "opening_fertilizer_buy": (0, 20),
    
    # Land timing (-1 = never buy)
    "ne_land_day": (-1, 15),
    "sw_land_day": (-1, 15),
    "se_land_day": (-1, 20),
    
    # Worker management
    "daily_hires": (2, 16),  # 2-16 workers per day
    "hire_strategy": (0, 2),  # 0=constant, 1=ramp up, 2=ramp down
    
    # Market timing
    "wheat_sell_focus_day": (-1, 28),  # -1 = no focus, spread evenly
    "straw_sell_timing": (0, 2),  # 0=early, 1=mid, 2=late
    "melon_sell_timing": (0, 2),
    "fertilizer_sell_timing": (0, 2),
    
    # Resource management
    "care_priority": (0, 3),  # 0=skip, 1=normal, 2=high, 3=max
    "fert_collection": (0, 3),
    "fert_use_strategy": (0, 4),  # 0=sell all, 1=wheat only, 2=premium, 3=all crops, 4=strategic
    
    # Route optimization
    "path_style": (0, 4),  # 0=greedy, 1=serpentine, 2=center-out, 3=perimeter, 4=dynamic
    "water_cadence": (0, 3),  # 0=every day, 1=every other, 2=skip-2, 3=adaptive
    "worker_zones": (0, 4),  # 0=all roam, 1=NE/SW, 2=4-way, 3=animal/crop, 4=dynamic
    "se_quad_workers": (0, 4),  # 0-4 workers dedicated to SE if unlocked
}

def random_params():
    """Generate completely random parameters - true exploration."""
    return {k: random.randint(lo, hi) for k, (lo, hi) in PARAM_RANGES.items()}

def mutate_params(parent):
    """High mutation rate with full random resets for diversity."""
    child = dict(parent)
    for key in PARAM_RANGES:
        lo, hi = PARAM_RANGES[key]
        if random.random() < 0.5:  # 50% mutation rate
            if random.random() < 0.4:  # 40% chance of full random reset
                child[key] = random.randint(lo, hi)
            else:  # 60% chance of moderate change
                child[key] = max(lo, min(hi, child[key] + random.randint(-5, 5)))
    return child

def crossover_params(p1, p2):
    """Uniform crossover - each param independently chosen."""
    return {k: (p1[k] if random.random() < 0.5 else p2[k]) for k in PARAM_RANGES}


# ============================================================================
# TAPE BUILDER - Full parameter support
# ============================================================================

def build_tape_from_params(params, base_tape):
    """Build a tape from any parameter combination."""
    tape = copy.deepcopy(base_tape)
    
    # === Day 0 market ===
    new_d0 = []
    hires = params.get("daily_hires", 6)
    hire_strategy = params.get("hire_strategy", 0)
    
    for _ in range(min(hires, 10)):
        new_d0.append(["HIRE"])
    
    cows = params.get("opening_cows", 2)
    sheep = params.get("opening_sheep", 2)
    if cows > 0: new_d0.append(["BUY_ANIMAL", "COW", cows])
    if sheep > 0: new_d0.append(["BUY_ANIMAL", "SHEEP", sheep])
    
    ws = params.get("opening_wheat_seeds", 5)
    ms = params.get("opening_melon_seeds", 3)
    ss = params.get("opening_straw_seeds", 0)
    cs = params.get("opening_carrot_seeds", 0)
    ts = params.get("opening_tomato_seeds", 0)
    
    if ws > 0 and len(new_d0) < 10: new_d0.append(["BUY_SEED", "WHEAT", ws])
    if ms > 0 and len(new_d0) < 10: new_d0.append(["BUY_SEED", "MELON", ms])
    if ss > 0 and len(new_d0) < 10: new_d0.append(["BUY_SEED", "STRAWBERRY", ss])
    if cs > 0 and len(new_d0) < 10: new_d0.append(["BUY_SEED", "CARROT", cs])
    if ts > 0 and len(new_d0) < 10: new_d0.append(["BUY_SEED", "TOMATO", ts])
    
    wb = params.get("opening_wheat_buy", 10)
    fb = params.get("opening_fertilizer_buy", 0)
    
    if wb > 0 and len(new_d0) < 10: new_d0.append(["BUY_PRODUCT", "WHEAT", wb])
    if fb > 0 and len(new_d0) < 10: new_d0.append(["BUY_PRODUCT", "FERTILIZER", fb])
    
    tape[0]["market"] = new_d0[:10]
    
    # === Land timing ===
    ne_day = params.get("ne_land_day", 5)
    sw_day = params.get("sw_land_day", 9)
    se_day = params.get("se_land_day", -1)
    
    existing_land = []
    for i, entry in enumerate(tape):
        for o in entry.get("market", []):
            if o and o[0] == "BUY_LAND": existing_land.append(i); break
    
    target_land_days = []
    if ne_day >= 0: target_land_days.append(ne_day)
    if sw_day >= 0: target_land_days.append(sw_day)
    if se_day >= 0: target_land_days.append(se_day)
    
    land_changed = any(idx < len(existing_land) and existing_land[idx]//24 != td or idx >= len(existing_land) for idx, td in enumerate(target_land_days))
    
    if land_changed:
        for entry in tape:
            entry["market"] = [o for o in entry.get("market", []) if not (o and o[0] == "BUY_LAND")]
        for d in target_land_days:
            step = d * 24
            if step < len(tape) and len(tape[step].get("market", [])) < 10:
                tape[step].setdefault("market", []).insert(0, ["BUY_LAND"])
    
    # === Crop swapping based on seed ratios ===
    total_seeds = ws + ms + ss + cs + ts
    if total_seeds > 0:
        # Count current plants
        plant_counts = {"WHEAT": 0, "MELON": 0, "STRAWBERRY": 0, "CARROT": 0, "TOMATO": 0}
        plant_actions = []
        
        for step_idx, entry in enumerate(tape):
            farmer_action = entry.get("farmer", ["PASS"])
            if farmer_action and farmer_action[0] == "PLANT" and len(farmer_action) > 1:
                crop = farmer_action[1]
                if crop in plant_counts:
                    plant_counts[crop] += 1
                    plant_actions.append((step_idx, "farmer", crop))
            
            for hand_idx, hand_action in enumerate(entry.get("hands", [])):
                if hand_action and hand_action[0] == "PLANT" and len(hand_action) > 1:
                    crop = hand_action[1]
                    if crop in plant_counts:
                        plant_counts[crop] += 1
                        plant_actions.append((step_idx, f"hand_{hand_idx}", crop))
        
        # Calculate target distribution
        total_plants = sum(plant_counts.values())
        target_dist = {
            "WHEAT": int(total_plants * ws / total_seeds),
            "MELON": int(total_plants * ms / total_seeds),
            "STRAWBERRY": int(total_plants * ss / total_seeds),
            "CARROT": int(total_plants * cs / total_seeds),
            "TOMATO": int(total_plants * ts / total_seeds),
        }
        
        # Build swap list
        swaps = []
        for crop in ["WHEAT", "MELON", "STRAWBERRY", "CARROT", "TOMATO"]:
            excess = plant_counts[crop] - target_dist[crop]
            if excess > 0:
                # Find crops that need more
                for target_crop in ["CARROT", "STRAWBERRY", "TOMATO", "MELON", "WHEAT"]:
                    deficit = target_dist[target_crop] - plant_counts[target_crop]
                    if deficit > 0:
                        swap_count = min(excess, deficit)
                        swaps.extend([(crop, target_crop)] * swap_count)
                        excess -= swap_count
                        if excess <= 0: break
        
        # Apply swaps
        swap_idx = 0
        for step_idx, actor, old_crop in plant_actions:
            if swap_idx >= len(swaps): break
            from_crop, to_crop = swaps[swap_idx]
            if old_crop == from_crop:
                if actor == "farmer":
                    tape[step_idx]["farmer"] = ["PLANT", to_crop]
                elif actor.startswith("hand_"):
                    hand_idx = int(actor.split("_")[1])
                    tape[step_idx]["hands"][hand_idx] = ["PLANT", to_crop]
                swap_idx += 1
    
    # === Animal routing - convert PASS to CARE for extra animals ===
    total_animals = cows + sheep
    base_animals = 5
    if total_animals > base_animals:
        extra_actions = (total_animals - base_animals) * 3
        action_count = 0
        for step_idx in range(48, len(tape)):
            entry = tape[step_idx]
            for hand_idx, action in enumerate(entry.get("hands", [])):
                if action and action[0] == "PASS" and action_count < extra_actions:
                    entry["hands"][hand_idx] = ["CARE"]
                    action_count += 1
            if action_count >= extra_actions: break
    
    return tape, tape


# ============================================================================
# PARALLEL BATTLE WORKER
# ============================================================================

def _make_tape_agent(tape_s0, tape_s1):
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
            while len(hands) < expected: hands.append(["PASS"])
            action["hands"] = hands[:expected]
            return action
        except:
            farm = obs.get("farms", [{}])[obs.get("player", 0)]
            n = len(farm.get("hands", []))
            return {"farmer":["PASS"],"hands":[["PASS"] for _ in range(n)],"market":[]}
    return agent

def _load_opponents():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    opps = {}
    
    for name, path in [
        ("kawashigi", "top10/kawashigi_route_92521336_s0.json"),
        ("indarkarhana", "top10/indarkarhana_selector_agent.py"),
        ("v25_mirror", "agent/main_v25_wheat16.py"),
        ("cowbot", "scripts/opp_cowbot.py"),
        ("healthstone", "scripts/opp_healthstone.py"),
        ("seb", "scripts/opp_seb.py"),
    ]:
        full_path = os.path.join(base, path)
        if not os.path.exists(full_path): continue
        
        if path.endswith('.json'):
            with open(full_path) as f: tape = json.load(f)
            opps[name] = _make_tape_agent(tape, tape)
        else:
            spec = importlib.util.spec_from_file_location(name, full_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            opps[name] = mod.agent
    
    return opps

def evaluate_variant(task):
    params, base_tape_path, seeds = task
    
    with open(base_tape_path) as f:
        base_tape = json.load(f)
    
    tape_s0, tape_s1 = build_tape_from_params(params, base_tape)
    agent_fn = _make_tape_agent(tape_s0, tape_s1)
    opponents = _load_opponents()
    
    results = {}
    total_wins = total_games = 0
    total_margin = 0
    
    for opp_name, opp_fn in opponents.items():
        wins = losses = ties = 0
        opp_margin = 0
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
                    opp_margin += margin
                    total_margin += margin
                    n += 1
                    total_games += 1
                    if margin > 0: wins += 1; total_wins += 1
                    elif margin < 0: losses += 1
                    else: ties += 1
                except:
                    losses += 1; n += 1; total_games += 1
        
        results[opp_name] = {
            "wins": wins, "losses": losses, "ties": ties,
            "win_rate": wins / max(n, 1),
            "avg_margin": opp_margin / max(n, 1),
        }
    
    return {
        "per_opponent": results,
        "overall_win_rate": total_wins / max(total_games, 1),
        "avg_margin": total_margin / max(total_games, 1),
        "total_wins": total_wins,
        "total_games": total_games,
    }


# ============================================================================
# CHECKPOINT
# ============================================================================

_state = {"generation": 0, "population": [], "best_ever": {"fitness": -999999, "params": None, "results": None}, "no_improvement": 0, "_shutdown": False}

def save_checkpoint(output_dir):
    path = os.path.join(output_dir, "state.json")
    data = {
        "generation": _state["generation"],
        "population": sorted(_state["population"], key=lambda x: -(x["fitness"] or -999999)),
        "best_ever": _state["best_ever"],
        "no_improvement": _state["no_improvement"],
        "saved_at": datetime.now().isoformat(),
    }
    tmp = path + ".tmp"
    with open(tmp, 'w') as f: json.dump(data, f, indent=2)
    os.replace(tmp, path)

def load_checkpoint(path):
    with open(path) as f: return json.load(f)


# ============================================================================
# MAIN - MASSIVE EVOLUTION
# ============================================================================

def run_massive_search(generations, population_size, seeds, output_dir="evo_massive", resume_from=None, n_workers=None):
    os.makedirs(output_dir, exist_ok=True)
    
    if n_workers is None:
        n_workers = min(mp.cpu_count(), 8)
    
    log_path = os.path.join(output_dir, "search.log")
    logf = open(log_path, 'a' if resume_from else 'w')
    
    def log(msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        logf.write(line + '\n')
        logf.flush()
    
    def graceful_shutdown(sig=None, frame=None):
        log("\n!!! Ctrl+C received - finishing current chunk then saving checkpoint !!!")
        _state["_shutdown"] = True
    
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    log("=" * 70)
    log("  MASSIVE EVOLUTIONARY SEARCH - True Meta Discovery")
    log(f"  Population: {population_size} | Generations: {generations}")
    log(f"  Seeds: {seeds} | Workers: {n_workers}")
    log(f"  Testing against ALL 6 opponents from gen 1")
    log(f"  Full parameter space: {len(PARAM_RANGES)} dimensions")
    log("=" * 70)
    
    base_tape_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'tapes_v19', 'champion_seat0.json')
    
    # Init or resume
    if resume_from and os.path.exists(resume_from):
        ckpt = load_checkpoint(resume_from)
        _state.update({k: ckpt[k] for k in ["generation", "population", "best_ever", "no_improvement"]})
        _state["_shutdown"] = False
        # If loaded population is smaller than expected, fill with random variants
        if len(_state["population"]) < population_size:
            shortfall = population_size - len(_state["population"])
            log(f"Checkpoint has {len(_state['population'])} variants, adding {shortfall} random")
            for _ in range(shortfall):
                _state["population"].append({"params": random_params(), "fitness": None, "results": None})
        # Reset fitness to None so all get re-evaluated with current opponents
        for ind in _state["population"]:
            ind["fitness"] = None
            ind["results"] = None
        log(f"RESUMED gen {_state['generation']} | Best: fitness={_state['best_ever']['fitness']:.1f}")
    else:
        _state["population"] = []
        _state["best_ever"] = {"fitness": -999999, "params": None, "results": None, "generation": 0}
        
        # Start with completely random population (no v25 bias)
        for i in range(population_size):
            _state["population"].append({
                "params": random_params(),
                "fitness": None,
                "results": None
            })
        
        log(f"Starting with {population_size} random variants")
    
    pool = mp.Pool(processes=n_workers)
    
    try:
        for gen in range(_state["generation"], generations):
            gen_start = time.time()
            log(f"\n{'='*50}\nGENERATION {gen+1}/{generations}\n{'='*50}")
            
            tasks = []
            task_indices = []
            for i, ind in enumerate(_state["population"]):
                if ind["fitness"] is None:
                    tasks.append((ind["params"], base_tape_path, seeds))
                    task_indices.append(i)
            
            if tasks:
                # Process in small chunks so Ctrl+C works on Windows
                results_list = []
                chunk_size = max(1, n_workers)
                for chunk_start in range(0, len(tasks), chunk_size):
                    chunk = tasks[chunk_start:chunk_start + chunk_size]
                    chunk_results = pool.map(evaluate_variant, chunk)
                    results_list.extend(chunk_results)
                    # Check if shutdown was requested
                    if _state.get("_shutdown"):
                        log("\n!!! SHUTDOWN REQUESTED - saving checkpoint !!!")
                        save_checkpoint(output_dir)
                        log(f"Resume: --resume {os.path.join(output_dir, 'state.json')}")
                        logf.close()
                        pool.close()
                        pool.join()
                        return
                
                for idx, battle_results in zip(task_indices, results_list):
                    ind = _state["population"][idx]
                    ind["results"] = battle_results
                    
                    # Fitness: win rate + margin + novelty
                    win_rate = battle_results["overall_win_rate"]
                    avg_margin = battle_results["avg_margin"]
                    
                    # Novelty bonus: reward high variance in params (different from average)
                    novelty = 0
                    for key in PARAM_RANGES:
                        lo, hi = PARAM_RANGES[key]
                        val = ind["params"][key]
                        # Reward extreme values (different from middle)
                        mid = (lo + hi) / 2
                        novelty += abs(val - mid) / (hi - lo)
                    novelty = novelty / len(PARAM_RANGES)  # 0-1
                    
                    fitness = win_rate * 1000 + avg_margin / 100 + novelty * 200
                    
                    ind["fitness"] = fitness
                    
                    if fitness > _state["best_ever"]["fitness"]:
                        _state["best_ever"] = {
                            "fitness": fitness,
                            "params": ind["params"],
                            "results": battle_results,
                            "generation": gen+1,
                            "index": idx,
                            "novelty": novelty
                        }
                        _state["no_improvement"] = 0
                        
                        with open(os.path.join(output_dir, "best.json"), 'w') as f:
                            json.dump(_state["best_ever"], f, indent=2)
                        
                        tape_s0, tape_s1 = build_tape_from_params(ind["params"], json.load(open(base_tape_path)))
                        with open(os.path.join(output_dir, "champion_tape_s0.json"), 'w') as f: json.dump(tape_s0, f)
                        with open(os.path.join(output_dir, "champion_tape_s1.json"), 'w') as f: json.dump(tape_s1, f)
                        
                        log(f"  *** NEW BEST! Gen {gen+1} fitness={fitness:.1f} novelty={novelty:.2f}")
                        for opp, res in battle_results["per_opponent"].items():
                            log(f"      vs {opp:15s}: {res['wins']}W-{res['losses']}L ${res['avg_margin']:+,.0f}")
                    else:
                        _state["no_improvement"] += 1
            
            gen_time = time.time() - gen_start
            best_f = max(x['fitness'] or -999 for x in _state["population"])
            log(f"  Gen {gen+1} done in {gen_time:.0f}s | Best: {best_f:.1f} | Stuck: {_state['no_improvement']}")
            
            # Selection: top 20% + random 20% for diversity
            _state["population"].sort(key=lambda x: -(x["fitness"] or -999999))
            top_20 = _state["population"][:population_size // 5]
            random_20 = random.sample(_state["population"][population_size // 5:], population_size // 5)
            survivors = top_20 + random_20
            
            new_pop = [copy.deepcopy(survivors[0])]  # elitism
            
            while len(new_pop) < population_size:
                if len(survivors) >= 2 and random.random() < 0.7:
                    p1 = random.choice(survivors[:len(survivors)//2])
                    p2 = random.choice(survivors)
                    child = crossover_params(p1["params"], p2["params"])
                else:
                    child = random_params()  # 30% completely random
                
                new_pop.append({"params": mutate_params(child), "fitness": None, "results": None})
            
            _state["population"] = new_pop
            _state["generation"] = gen + 1
            save_checkpoint(output_dir)
            
            # Check for true champion (beats all opponents 70%+)
            if _state["best_ever"]["results"]:
                all_decent = all(r["win_rate"] >= 0.7 for r in _state["best_ever"]["results"]["per_opponent"].values())
                if all_decent:
                    log(f"\n{'!'*60}\nTRUE CHAMPION! Beats all opponents 70%+\n{'!'*60}")
                    log(f"Params: {json.dumps(_state['best_ever']['params'], indent=2)}")
                    save_checkpoint(output_dir)
                    break
            
            if _state["no_improvement"] > population_size * 50:
                log(f"\nNo improvement for {_state['no_improvement']}. Done.")
                break
    
    finally:
        pool.close()
        pool.join()
    
    log(f"\n{'='*70}\nSEARCH COMPLETE\n{'='*70}")
    log(f"Best: fitness={_state['best_ever']['fitness']:.1f}")
    if "novelty" in _state["best_ever"]:
        log(f"Novelty: {_state['best_ever']['novelty']:.2f}")
    log(f"Params: {json.dumps(_state['best_ever']['params'], indent=2)}")
    if _state["best_ever"]["results"]:
        for opp, res in _state["best_ever"]["results"]["per_opponent"].items():
            log(f"  vs {opp:15s}: WR={res['win_rate']:.0%} ${res['avg_margin']:+,.0f}")
    logf.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generations", type=int, default=1000)
    parser.add_argument("--population", type=int, default=1000)
    parser.add_argument("--seeds", type=str, default="1,2,3")
    parser.add_argument("--output", type=str, default="evo_massive")
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()
    
    seeds = [int(s) for s in args.seeds.split(",")]
    run_massive_search(args.generations, args.population, seeds, args.output, args.resume, args.workers)
