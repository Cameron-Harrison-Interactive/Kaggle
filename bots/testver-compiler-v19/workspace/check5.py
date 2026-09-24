import importlib.util
spec = importlib.util.spec_from_file_location("agent", "/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py")
agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_mod)
from kaggle_environments import make

call_count = [0]

def my_agent(obs, configuration=None):
    call_count[0] += 1
    step = obs.get("step")
    if call_count[0] <= 5 or step >= 710:
        print(f"Call #{call_count[0]}: step={step} seat={obs.get('player')}", flush=True)
    return agent_mod.agent(obs, configuration)

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
steps = env.reset()
print(f"Reset done, starting run...", flush=True)
env.run([my_agent, my_agent])
print(f"\nTotal calls: {call_count[0]}", flush=True)

# Final score
final = env.steps[-1]
score = final[0].reward + final[1].reward
print(f"Score: ${score:,.0f}", flush=True)
