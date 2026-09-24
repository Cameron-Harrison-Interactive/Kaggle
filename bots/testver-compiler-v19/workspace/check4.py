import importlib.util
spec = importlib.util.spec_from_file_location("agent", "/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py")
agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_mod)
from kaggle_environments import make

print("Module loaded", flush=True)

def my_agent(obs, configuration=None):
    step = obs.get("step")
    if step >= 715:
        print(f"\nStep {step} seat {obs.get('player')}:", flush=True)
        farm = obs.get("farms", [{}])[obs.get("player", 0)]
        farmer = farm.get("farmer", [])
        hands = farm.get("hands", [])
        shed_access = [(4,4), (5,4), (4,5), (5,5)]
        def is_shed(p):
            try: return (int(p[0]), int(p[1])) in shed_access
            except: return False
        print(f"  Farmer: {farmer} shed={is_shed(farmer)}", flush=True)
        for i, h in enumerate(hands):
            print(f"  Hand{i}: {h} shed={is_shed(h)}", flush=True)
        shed = obs.get("private", {}).get("shed", {})
        nz = {k: v for k, v in shed.items() if v > 0}
        print(f"  Shed: {nz}", flush=True)
        prices = obs.get("market", {}).get("prices", {})
        print(f"  FERT price: {prices.get('FERTILIZER')}", flush=True)
        print(f"  Market FERT inv: {obs.get('market', {}).get('inventory', {}).get('FERTILIZER')}", flush=True)
    
    return agent_mod.agent(obs, configuration)

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
steps = env.reset()
env.run([my_agent, my_agent])
print("\nDone!", flush=True)
