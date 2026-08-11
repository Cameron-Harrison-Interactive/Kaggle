import importlib.util
spec = importlib.util.spec_from_file_location("agent", "/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py")
agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_mod)
agent = agent_mod.agent
from kaggle_environments import make
import sys

# Test seeds 1-20
results = []
for seed in range(1, 21):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    steps = env.reset()
    env.run([agent, agent])
    final = env.steps[-1]
    score = final[0].reward + final[1].reward
    results.append((seed, score))
    print(f"Seed {seed:2d}: ${score:,.0f}", flush=True)

# Sort by score
results.sort(key=lambda x: -x[1])
print("\n=== Top 5 seeds ===")
for seed, score in results[:5]:
    print(f"Seed {seed}: ${score:,.0f}")

print(f"\nAverage: ${sum(s for _,s in results)/len(results):,.0f}")
print(f"Best: ${results[0][1]:,.0f} (seed {results[0][0]})")
print(f"Worst: ${results[-1][1]:,.0f} (seed {results[-1][0]})")
