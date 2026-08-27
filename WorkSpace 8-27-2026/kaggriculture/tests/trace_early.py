"""Trace hours 0..3 days worth to find where money vanishes."""
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
last_money = 3000.0
for step in range(24 * 8):
    obs = sim.obs(0)
    b_pre = Board(obs)
    a0 = custom_agent(obs)
    a1 = PASS(sim.obs(1))
    sim.step(a0, a1)
    b_post = Board(sim.obs(0))
    delta = b_post.money - last_money
    if abs(delta) > 5 or a0["market"]:
        print(f"D{b_pre.day}H{b_pre.hour:>2}: ${b_post.money:>6,.0f} ({delta:+6.0f}) mkt={a0['market']}")
    last_money = b_post.money
