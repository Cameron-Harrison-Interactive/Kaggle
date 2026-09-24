import importlib.util
spec = importlib.util.spec_from_file_location("agent", "/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py")
agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_mod)
from kaggle_environments import make

log = []

def my_agent(obs, configuration=None):
    step = obs.get("step")
    if step >= 715:
        farm = obs.get("farms", [{}])[obs.get("player", 0)]
        farmer = farm.get("farmer", [])
        hands = farm.get("hands", [])
        shed = obs.get("private", {}).get("shed", {})
        prices = obs.get("market", {}).get("prices", {})
        log.append(f"Step {step} seat {obs.get('player')}: farmer={farmer} hands={hands} shed={shed} FERT_price={prices.get('FERTILIZER')}")
    return agent_mod.agent(obs, configuration)

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
steps = env.reset()
env.run([my_agent, my_agent])

with open('/tmp/debug.log', 'w') as f:
    for line in log:
        f.write(line + '\n')

print(f"Logged {len(log)} entries to /tmp/debug.log", flush=True)
