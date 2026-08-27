"""Head-to-head battle tests for main.py (in-memory GameSim, fast).

Opponents:
  * v25 tape   : agent/main_v25_wheat16.py  (_SEAT0_ACTIONS replay)
  * archetypes : mirror / cowbot / sheepbot / goosebot / cropbot
                 (built on decision_agent_v2 params, like battle_contested.py)

Usage:
  python3 scripts/battle_main.py [seed list] [opponent ...]
  (default: seeds 1 2 3, all opponents)
"""
import sys, os, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "agent"))

from sim import GameSim
import main as M
import decision_agent_v2 as v2


def pass_agent(obs, cfg=None):
    farm = obs["farms"][obs["player"]]
    n = len(farm.get("hands", []) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}


class TapeAgent:
    """Replay the fixed v25 tape (seat-0 actions) verbatim."""
    def __init__(self, actions):
        self.actions = actions
        self.step = 0
    def __call__(self, obs):
        if self.step < len(self.actions):
            t = self.actions[self.step]
            self.step += 1
            n = len(obs["farms"][obs["player"]].get("hands", []) or [])
            hands = list(t.get("hands") or [])
            while len(hands) < n:
                hands.append(["PASS"])
            return {"market": list(t.get("market") or []),
                    "farmer": t.get("farmer") or ["PASS"],
                    "hands": hands[:n]}
        return {"farmer": ["PASS"], "hands": [], "market": []}


def load_tape():
    src = open(os.path.join(ROOT, "agent", "main_v25_wheat16.py")).read()
    m = re.search(r"_SEAT0_ACTIONS = json.loads\(\'(.*?)\'\)", src, re.S)
    return json.loads(m.group(1))


def v2_agent(mod, params):
    cls = mod.CounterAgent if hasattr(mod, "CounterAgent") else mod.DecisionAgent
    inst = cls(params, seat=0)
    return lambda obs, config=None: inst.act(obs, config)


ARCHETYPES = {
    "mirror":   dict(v2.DEFAULT_PARAMS),
    "cowbot":   {**dict(v2.DEFAULT_PARAMS), "final_cow": 14, "final_sheep": 0,
                 "target_sheep": 0, "open_sheep": 0},
    "sheepbot": {**dict(v2.DEFAULT_PARAMS), "final_cow": 2, "final_sheep": 12,
                 "open_cows": 2, "open_sheep": 3},
    "goosebot": {**dict(v2.DEFAULT_PARAMS), "final_cow": 4, "final_sheep": 2,
                 "target_goose": 3, "final_goose": 10},
    "cropbot":  {**dict(v2.DEFAULT_PARAMS), "final_cow": 4, "final_sheep": 2,
                 "open_cows": 1, "open_sheep": 1},
}


def battle(opp_agent, seed):
    """Run main.py (seat 0) vs opp (seat 1); return (ours, opp)."""
    M.set_params(dict(M.DEFAULT_PARAMS))
    sim = GameSim(seed=seed)
    sim.run(M.agent, opp_agent)
    return sim.money(0), sim.money(1)


def battle_swap(opp_agent, seed):
    """Run opp (seat 0) vs main.py (seat 1); return (ours, opp)."""
    M.set_params(dict(M.DEFAULT_PARAMS))
    sim = GameSim(seed=seed)
    sim.run(opp_agent, M.agent)
    return sim.money(1), sim.money(0)


def main():
    seeds = [int(s) for s in (sys.argv[1:] or [])] or [1, 2, 3]
    tape = load_tape()
    opps = {"tape_v25": lambda: TapeAgent(tape)}
    for name, params in ARCHETYPES.items():
        opps[name] = lambda params=params: v2_agent(v2, params)

    for name, make_opp in opps.items():
        w = l = t = 0
        margins = []
        for seed in seeds:
            for swap in (False, True):
                opp = make_opp()
                if swap:
                    ours, oppm = battle_swap(opp, seed)
                else:
                    ours, oppm = battle(opp, seed)
                margin = ours - oppm
                margins.append(margin)
                if margin > 0.5:
                    w += 1
                elif margin < -0.5:
                    l += 1
                else:
                    t += 1
        avg = sum(margins) / len(margins)
        print(f"{name:10s}: {w}W {l}L {t}T   avg margin {avg:+,.0f}   "
              f"(seeds {seeds}, both seats)")


if __name__ == "__main__":
    main()
