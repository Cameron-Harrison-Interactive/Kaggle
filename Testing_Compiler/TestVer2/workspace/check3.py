import importlib.util
spec = importlib.util.spec_from_file_location("agent", "/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py")
agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_mod)
agent = agent_mod.agent
from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
steps = env.reset()

print("Starting...", flush=True)

def debug_agent(obs, configuration=None):
    step = obs.get("step")
    if step >= 715:
        print(f"Step {step} seat {obs.get('player')}:", flush=True)
        farm = obs.get("farms", [{}])[obs.get("player", 0)]
        print(f"  Farmer pos: {farm.get('farmer')}", flush=True)
        print(f"  Hands pos: {farm.get('hands')}", flush=True)
        shed = obs.get("private", {}).get("shed", {})
        nz = {k: v for k, v in shed.items() if v > 0}
        print(f"  Shed: {nz}", flush=True)
        prices = obs.get("market", {}).get("prices", {})
        print(f"  FERT price: {prices.get('FERTILIZER')}", flush=True)
    
    try:
        result = agent(obs, configuration)
        if step >= 715:
            print(f"  Action: {result}", flush=True)
        return result
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}

env.run([debug_agent, debug_agent])
print("Done!", flush=True)
