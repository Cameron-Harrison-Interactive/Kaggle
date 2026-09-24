import importlib.util
spec = importlib.util.spec_from_file_location("agent", "/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py")
agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_mod)
agent = agent_mod.agent
from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
steps = env.reset()

def check_positions(obs, configuration=None):
    step = obs.get("step")
    if step in [716, 717, 718]:
        farm = obs.get("farms", [{}])[obs.get("player", 0)]
        farmer = farm.get("farmer", [])
        hands = farm.get("hands", [])
        shed_access = [(4,4), (5,4), (4,5), (5,5)]
        
        def is_shed_access(pos):
            try:
                return (int(pos[0]), int(pos[1])) in shed_access
            except:
                return False
        
        print(f"\nStep {step} seat {obs.get('player')}:")
        print(f"  Farmer at: {farmer} (shed: {is_shed_access(farmer)})")
        for i, h in enumerate(hands):
            print(f"  Hand {i} at: {h} (shed: {is_shed_access(h)})")
        
        shed = obs.get("private", {}).get("shed", {})
        nz = {k: v for k, v in shed.items() if v > 0}
        if nz:
            print(f"  Shed: {nz}")
        
        prices = obs.get("market", {}).get("prices", {})
        print(f"  FERTILIZER price: ${prices.get('FERTILIZER', 0)}")
    
    return agent(obs, configuration)

env.run([check_positions, check_positions])
