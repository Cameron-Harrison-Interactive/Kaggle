import json, base64, zlib
from kaggle_environments import make
import sys

DATA = '/home/user/kaggriculture/V18 - Adapt-2-Survive/data'

# Load the current agent code as a module
import importlib.util
spec = importlib.util.spec_from_file_location("agent", "/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py")
agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_mod)

# But we need to modify the tapes. Let's do this differently:
# Create a wrapper that swaps tapes

def create_agent_with_tapes(seat0_tape, seat1_tape):
    """Create a new agent function with specified tapes."""
    # Import the base module's functions
    _market_price = agent_mod._market_price
    _is_sell = agent_mod._is_sell
    _impact_score = agent_mod._impact_score
    _demand_per_day = agent_mod._demand_per_day
    _order_score = agent_mod._order_score
    _rank_sell_slots = agent_mod._rank_sell_slots
    _get = agent_mod._get
    _seat = agent_mod._seat
    _farm = agent_mod._farm
    _copy_action = agent_mod._copy_action
    _align_hands = agent_mod._align_hands
    _shape = agent_mod._shape
    _WEED_STATE = agent_mod._WEED_STATE
    _WEED_REPLAY_STEPS = agent_mod._WEED_REPLAY_STEPS
    _tile_at = agent_mod._tile_at
    _trace_actor_action = agent_mod._trace_actor_action
    _weed_repair_action = agent_mod._weed_repair_action
    _MEM = agent_mod._MEM
    _new_mem = agent_mod._new_mem
    _mem_for = agent_mod._mem_for
    _count_crop = agent_mod._count_crop
    _count_animal = agent_mod._count_animal
    _opp_farm = agent_mod._opp_farm
    _update_memory = agent_mod._update_memory
    _adapt_crops = agent_mod._adapt_crops
    _adapt_animals = agent_mod._adapt_animals
    _shed_access_tiles = agent_mod._shed_access_tiles
    _is_shed_adjacent = agent_mod._is_shed_adjacent
    _v26_terminal_sweep = agent_mod._v26_terminal_sweep
    _MARKET_PARAMS = agent_mod._MARKET_PARAMS
    _regime = agent_mod._regime
    
    _SEAT0 = seat0_tape
    _SEAT1 = seat1_tape
    
    def agent(obs, configuration=None):
        step = int(_get(obs, "step", 0) or 0)
        
        # Weeds
        try:
            actions = _SEAT1 if _seat(obs) == 1 else _SEAT0
            step_idx = min(max(0, int(_get(obs, "step", 0) or 0)), len(actions) - 1)
            action = _copy_action(actions[step_idx])
            action = _weed_repair_action(obs, action, actions, step)
        except:
            farm = _farm(obs, _seat(obs))
            action = {"farmer": ["PASS"], 
                      "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])], 
                      "market": []}
        
        action = _adapt_crops(obs, action)
        action = _adapt_animals(obs, action)
        
        if step == 718:
            try:
                return _v26_terminal_sweep(obs, action, configuration)
            except:
                pass
        
        return action
    
    return agent

# Test on seeds 1-3
test_seeds = [1, 2, 3]

# Load tapes
def load_tape(seed, seat):
    if seat == 0:
        fn = f'{DATA}/route_v18_opt_seat0_s{seed}.json'
    else:
        fn = f'{DATA}/route_v18_opt_seat1_s{seed}.json'
    try:
        with open(fn) as f:
            return json.load(f)
    except:
        return None

print("Loading tapes...", flush=True)
tapes_s0 = {s: load_tape(s, 0) for s in range(1, 21)}
tapes_s1 = {s: load_tape(s, 1) for s in range(1, 21)}
print(f"Loaded seat0: {len([t for t in tapes_s0.values() if t])} tapes", flush=True)
print(f"Loaded seat1: {len([t for t in tapes_s1.values() if t])} tapes", flush=True)

# Current baseline
print("\n=== Baseline (s0=1, s1=5) ===", flush=True)
agent_base = create_agent_with_tapes(tapes_s0[1], tapes_s1[5])
total = 0
for seed in test_seeds:
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    steps = env.reset()
    env.run([agent_base, agent_base])
    score = env.steps[-1][0].reward + env.steps[-1][1].reward
    total += score
    print(f"  Seed {seed}: ${score:,.0f}", flush=True)
print(f"  Total: ${total:,.0f}", flush=True)

# Test seed 16 (best scoring)
print("\n=== Test s0=16, s1=5 ===", flush=True)
if tapes_s0.get(16) and tapes_s1.get(5):
    agent16 = create_agent_with_tapes(tapes_s0[16], tapes_s1[5])
    total = 0
    for seed in test_seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        steps = env.reset()
        env.run([agent16, agent16])
        score = env.steps[-1][0].reward + env.steps[-1][1].reward
        total += score
        print(f"  Seed {seed}: ${score:,.0f}", flush=True)
    print(f"  Total: ${total:,.0f} (delta: ${total - 505948:+,.0f})", flush=True)

# Test seed 15
print("\n=== Test s0=15, s1=5 ===", flush=True)
if tapes_s0.get(15) and tapes_s1.get(5):
    agent15 = create_agent_with_tapes(tapes_s0[15], tapes_s1[5])
    total = 0
    for seed in test_seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        steps = env.reset()
        env.run([agent15, agent15])
        score = env.steps[-1][0].reward + env.steps[-1][1].reward
        total += score
        print(f"  Seed {seed}: ${score:,.0f}", flush=True)
    print(f"  Total: ${total:,.0f} (delta: ${total - 505948:+,.0f})", flush=True)

# Test seed 13
print("\n=== Test s0=13, s1=5 ===", flush=True)
if tapes_s0.get(13) and tapes_s1.get(5):
    agent13 = create_agent_with_tapes(tapes_s0[13], tapes_s1[5])
    total = 0
    for seed in test_seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        steps = env.reset()
        env.run([agent13, agent13])
        score = env.steps[-1][0].reward + env.steps[-1][1].reward
        total += score
        print(f"  Seed {seed}: ${score:,.0f}", flush=True)
    print(f"  Total: ${total:,.0f} (delta: ${total - 505948:+,.0f})", flush=True)
