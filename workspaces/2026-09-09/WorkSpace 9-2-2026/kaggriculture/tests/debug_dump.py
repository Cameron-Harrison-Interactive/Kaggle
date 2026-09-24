"""Dump state MID-DAY (after H1 hires) so we can see actual hand count."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))

from sim import GameSim
from agent.custom import agent as custom_agent
from agent.custom.board import Board


def PASS(obs, cfg=None):
    n_hands = len(obs["farms"][obs["player"]].get("hands", []) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * n_hands, "market": []}


sim = GameSim(seed=1)
last_actions = {}
for step in range(200):
    obs = sim.obs(0)
    a0 = custom_agent(obs)
    a1 = PASS(sim.obs(1))
    sim.step(a0, a1)
    d = sim.state[0].observation.day
    h = sim.state[0].observation.hour
    b = Board(sim.obs(0))
    if h in {2, 6, 12, 18, 23} and d in {0, 1, 2, 3, 5, 8}:
        n_plants = len(b.plants())
        n_hands = len(b.hands)
        wheat_shed = b.shed.get("WHEAT", 0)
        # yields
        yields = [b.tile(x, y)["yield_units"] for (x, y) in b.plants()]
        print(f"D{d}H{h:>2}: ${b.money:>7,.0f}  plants={n_plants}(yields={yields})  hands={n_hands}  "
              f"shed_wheat={wheat_shed}")
        print(f"      farmer_act={a0['farmer']}  hand_acts={a0['hands']}")
        # unit positions
        for i, u in enumerate(b.units):
            inv = b.unit_inv(i)
            print(f"      u{i}@{u} inv={dict(inv)}")
