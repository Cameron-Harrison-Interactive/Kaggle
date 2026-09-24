"""Probe our bot's crop-planting behavior day by day vs PASS (seed 1)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from sim import GameSim
import main as M

def pass_agent(obs, cfg=None):
    farm = obs["farms"][obs["player"]]
    n = len(farm.get("hands", []) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}

def run(seed):
    M.set_params(dict(M.DEFAULT_PARAMS))
    sim = GameSim(seed=seed)
    # instrument: wrap our agent to log
    state = {"day": 0, "planted": [], "buys": []}
    prev_tiles = None
    prev_seeds = None
    prev_hands = None

    def us(obs):
        nonlocal prev_tiles, prev_seeds, prev_hands
        day = obs["day"]
        if day != state["day"]:
            state["day"] = day
            state["planted"].append([])
        farm = obs["farms"][obs["player"]]
        # count hands
        hands = len(farm.get("hands", []) or [])
        # plants on board
        tiles = farm["tiles"]
        plants = {}
        for row in tiles:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    c = t.get("crop")
                    plants[c] = plants.get(c, 0) + 1
        # track planting deltas
        if prev_tiles is not None:
            new = {}
            for row_i in range(10):
                for col in range(10):
                    t = tiles[row_i][col]
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        c = t["crop"]
                        p0 = prev_tiles[row_i][col]
                        is_new = not (isinstance(p0, dict) and p0.get("kind") == "PLANT")
                        if is_new:
                            new[c] = new.get(c, 0) + 1
            if new:
                state["planted"][-1].append(new)
        prev_tiles = [row[:] for row in tiles]
        prev_hands = hands
        act = M.agent(obs)
        return act

    sim.run(us, pass_agent)
    money = sim.money(0)
    return money, state

if __name__ == "__main__":
    money, state = run(1)
    print(f"seed 1 final money: ${money:,.0f}")
    print("\nper-day plantings (dict crop->count per turn where a new plant appeared):")
    for d, plist in enumerate(state["planted"]):
        if plist:
            agg = {}
            for p in plist:
                for c, n in p.items():
                    agg[c] = agg.get(c, 0) + n
            print(f"  day {d}: {agg}")
