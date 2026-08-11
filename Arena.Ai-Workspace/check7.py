import importlib.util
spec = importlib.util.spec_from_file_location("agent", "/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py")
agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_mod)
from kaggle_environments import make

log = []

def my_agent(obs, configuration=None):
    step = obs.get("step")
    if step >= 716:
        farm = obs.get("farms", [{}])[obs.get("player", 0)]
        inventories = obs.get("private", {}).get("inventories", [])
        non_empty_inv = []
        for i, inv in enumerate(inventories):
            nz = {k: v for k, v in inv.items() if v > 0}
            if nz:
                non_empty_inv.append(f"unit{i}:{nz}")
        
        log.append(f"Step {step} seat {obs.get('player')}:\n"
                   f"  farmer={farm.get('farmer')} hands={farm.get('hands')}\n"
                   f"  inventories: {non_empty_inv}\n"
                   f"  shed: {obs.get('private', {}).get('shed')}\n"
                   f"  FERT_price={obs.get('market', {}).get('prices', {}).get('FERTILIZER')}\n"
                   f"  market_FERT_inv={obs.get('market', {}).get('inventory', {}).get('FERTILIZER')}\n"
                   f"  all_prices={dict((k,v) for k,v in obs.get('market', {}).get('prices', {}).items() if v < 100)}")
    return agent_mod.agent(obs, configuration)

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
steps = env.reset()
env.run([my_agent, my_agent])

with open('/tmp/debug.log', 'w') as f:
    for line in log:
        f.write(line + '\n')
print(f"Logged {len(log)} entries", flush=True)
