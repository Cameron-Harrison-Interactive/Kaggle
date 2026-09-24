"""
sim.py — exact, fast game simulator for Kaggriculture.

Drives the OFFICIAL engine's own interpreter functions directly (imported from
kaggle_environments), so the rules are bit-for-bit identical to a real match —
no re-implementation, no transcription bugs. It is verified against the real
engine in `verify_sim()` (replay a real game, compare money/prices exactly).

Why this exists: the "full AI bot" needs to *look ahead* — "if I add this one
animal do I win or lose?", "if I skip watering this crop do I save 30 or lose
6?". Answering that requires cloning the current game state and simulating
candidate futures. This module is the foundation of that planner.

Speed: each step is a single interpreter call (no `make()`, no agent plumbing),
~30-60 microseconds/step, so rolling out a few days is essentially free.

Usage:
    sim = GameSim(seed=1)
    sim.step(player0_action_dict, player1_action_dict)   # advance one turn
    obs = sim.obs(player)                                # dict obs for an agent
    clone = sim.clone()                                  # branch off a copy

    # replay-verify against the real engine:
    verify_sim(seeds=[1, 2, 3])
"""

import copy
import sys

from kaggle_environments.utils import Struct
from kaggle_environments.envs.kaggriculture import kaggriculture as K


DEFAULT_CONFIG = {
    "episodeSteps": 720,
    "actTimeout": 1,
    "runTimeout": 1200,
    "boardSize": 10,
    "startingMoney": 3000,
    "maxMarketOrdersPerTurn": 10,
    "turnsPerDay": 24,
    "shedCapacity": 100,
    "weedSpawnChance": 0.005,
    "townShopUnlockInterval": 3,
    "townShopSellInterval": 4,
    "townCenterSellInterval": 24,
    "farmHandCostMult": 1,
    "marketParams": {},
}


class _Env:
    """Minimal stand-in for the kaggle_environments `env` object."""

    def __init__(self, configuration):
        self.configuration = Struct(**configuration)
        self.done = False
        self.info = {}


class _AgentState:
    """Minimal stand-in for one agent's slot in `state`."""

    def __init__(self):
        self.observation = Struct()
        self.action = {}
        self.status = "ACTIVE"
        self.reward = 0.0


def _empty_private(farm):
    """Private state for an opponent we can't see (shed/seeds unknown)."""
    shed = {item: 0 for item in K.PRODUCTS + list(K.ANIMALS)}
    seeds = {c: 0 for c in K.CROPS}
    n_units = 1 + len(farm.get("hands", []) or [])
    return {"shed": shed, "seeds": seeds, "inventories": [{} for _ in range(n_units)]}


class GameSim:
    def __init__(self, seed=1, configuration=None):
        cfg = dict(DEFAULT_CONFIG)
        if configuration:
            cfg.update(configuration)
        self.configuration = cfg
        self.env = _Env(cfg)
        self.env.info["seed"] = int(seed)
        self.state = [_AgentState(), _AgentState()]
        K._initialize(self.state, self.env)
        self.step_index = 0

    # --------------------------------------------------------------- step
    def step(self, action0, action1):
        # The interpreter reads obs0.step for town consumption / end-of-day /
        # plant-decay timing; the real framework maintains it outside the
        # interpreter, so the sim must too.
        self.state[0].observation.step = self.step_index
        self.state[1].observation.step = self.step_index
        self.state[0].action = action0 or {}
        self.state[1].action = action1 or {}
        K.interpreter(self.state, self.env)
        self.step_index += 1
        return self

    def run(self, agent0, agent1, steps=None):
        """Run with callable agents; each gets a plain-dict obs, returns an action dict."""
        steps = steps if steps is not None else self.configuration["episodeSteps"]
        for _ in range(steps):
            a0 = agent0(self.obs(0)) if agent0 else {}
            a1 = agent1(self.obs(1)) if agent1 else {}
            self.step(a0, a1)
        return self

    # -------------------------------------------------------------- state
    def obs(self, player):
        """Build the observation dict the real engine would hand an agent."""
        o = self.state[0].observation
        return {
            "player": player,
            "day": o.day,
            "hour": o.hour,
            "step": self.step_index,
            "farms": o.farms,
            "market": o.market,
            "town": o.town,
            "private": self.state[player].observation.private,
            "remainingOverageTime": 60.0,
        }

    def money(self, player):
        return float(self.state[0].observation.farms[player]["money"])

    def prices(self):
        return dict(self.state[0].observation.market["prices"])

    def done(self):
        return self.state[0].status == "DONE"

    def clone(self):
        return copy.deepcopy(self)

    def total_steps(self):
        return self.configuration["episodeSteps"]

    # --------------------------------------------------------- reconstruct
    @classmethod
    def from_obs(cls, obs, seed=0):
        """Reconstruct a live GameSim from an agent observation.

        Farms/market/town are deep-copied from the observation (public, exact).
        The acting player's private state (shed/seeds/inventories) is copied;
        the opponent's private state is unknown, so it is approximated as empty
        (only matters if the opponent acts inside a rollout).

        `seed` is fabricated in live play (the real seed is scrubbed from
        observations), so future weed spawns / shop unlocks are approximate —
        but they are IDENTICAL across every cloned option, so *relative*
        what-if comparisons (deltas) are reliable.
        """
        sim = cls.__new__(cls)
        sim.configuration = dict(DEFAULT_CONFIG)
        sim.env = _Env(sim.configuration)
        sim.env.info["seed"] = int(seed)
        sim.state = [_AgentState(), _AgentState()]

        farms = copy.deepcopy(obs["farms"])
        market = copy.deepcopy(obs["market"])
        town = copy.deepcopy(obs["town"])
        day = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)
        step = int(obs.get("step", 0) or 0)
        player = int(obs.get("player", 0) or 0)

        for i in range(2):
            o = sim.state[i].observation
            o.player = i
            o.farms = farms
            o.market = market
            o.town = town
            o.day = day
            o.hour = hour
            o.step = step

        sim.state[player].observation.private = copy.deepcopy(obs["private"])
        sim.state[1 - player].observation.private = _empty_private(farms[1 - player])
        sim.step_index = step
        return sim


def verify_sim(seeds=(1, 2, 3), quiet=False):
    """Replay real-engine games through GameSim and assert exact agreement.

    Returns True if every seed matches on final money and on daily prices.
    """
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agent"))
    from kaggle_environments import make

    all_ok = True
    for seed in seeds:
        rec0, rec1 = [], []

        def a0(obs, config=None):
            rec0.append(sim_action_for_replay(obs))
            return rec0[-1]

        def a1(obs, config=None):
            rec1.append(sim_action_for_replay(obs))
            return rec1[-1]

        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        result = env.run([a0, a1])
        real_m0 = result[-1][0]["observation"]["farms"][0]["money"]
        real_m1 = result[-1][1]["observation"]["farms"][1]["money"]

        sim = GameSim(seed=seed)
        n = min(len(rec0), len(rec1), 720)
        for i in range(n):
            sim.step(rec0[i], rec1[i])
        sim_m0 = sim.money(0)
        sim_m1 = sim.money(1)

        ok_money = abs(sim_m0 - real_m0) < 0.5 and abs(sim_m1 - real_m1) < 0.5

        # spot-check market prices at day boundaries
        ok_prices = True
        for day in (5, 10, 15, 20, 25):
            step = day * 24
            if step < len(result):
                real_prices = result[step][0]["observation"]["market"]["prices"]
            else:
                continue
            s = GameSim(seed=seed)
            for i in range(min(step, n)):
                s.step(rec0[i], rec1[i])
            sim_prices = s.prices()
            if real_prices != sim_prices:
                ok_prices = False
                break

        if not quiet:
            print(f"seed {seed}: real ${real_m0:,.0f}/${real_m1:,.0f}  "
                  f"sim ${sim_m0:,.0f}/${sim_m1:,.0f}  "
                  f"money_match={ok_money}  prices_match={ok_prices}")
        all_ok = all_ok and ok_money and ok_prices
    return all_ok


def sim_action_for_replay(obs):
    """The reference behaviour used to generate replay games.

    Uses decision_agent_v2 so the replays are realistic; its exact action
    sequence is recorded and replayed through GameSim.
    """
    from decision_agent_v2 import agent as dv2_agent
    return dv2_agent(obs)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    sys.path.insert(0, "agent")
    ok = verify_sim()
    print("VERIFY:", "PASS" if ok else "FAIL")
