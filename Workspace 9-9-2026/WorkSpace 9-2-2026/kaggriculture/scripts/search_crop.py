"""Grid-search the crop-engine knobs against PASS (in-memory sim)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import GameSim
import main as M
from collections import defaultdict


def pass_agent(obs, cfg=None):
    farm = obs["farms"][obs["player"]]
    n = len(farm.get("hands", []) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}


def run(seed, mod):
    M.set_params({**dict(M.DEFAULT_PARAMS), **mod})
    sim = GameSim(seed=seed)
    units = defaultdict(int)
    def us(obs):
        act = M.agent(obs)
        for o in act.get("market", []):
            if o[0] == "SELL":
                units[o[1]] += o[2]
        return act
    sim.run(us, pass_agent)
    return sim.money(0), units


CONFIGS = {
    "base(no crops fix)": dict(day0_plan=False, survival_water=False, hire_reserve=250,
                               seed_floor_straw=200, seed_floor_melon=250),
    "surv only": dict(day0_plan=False, survival_water=True, hire_reserve=250,
                      seed_floor_straw=200, seed_floor_melon=250),
    "surv+hire50": dict(day0_plan=False, survival_water=True, hire_reserve=50,
                        seed_floor_straw=200, seed_floor_melon=250),
    "surv+hire50+floor100": dict(day0_plan=False, survival_water=True, hire_reserve=50,
                                 seed_floor_straw=100, seed_floor_melon=150),
    "surv+hire50+floor300": dict(day0_plan=False, survival_water=True, hire_reserve=50,
                                 seed_floor_straw=300, seed_floor_melon=350),
    "surv+hire50+day0": dict(day0_plan=True, survival_water=True, hire_reserve=50,
                             seed_floor_straw=200, seed_floor_melon=250),
}

if __name__ == "__main__":
    seeds = [int(s) for s in sys.argv[1:]] or [1, 3, 6, 7]
    names = list(CONFIGS)
    print(f"{'config':28s} " + " ".join(f"{'s'+str(s):>9s}" for s in seeds) + "   AVG")
    for name in names:
        row = []
        for seed in seeds:
            m, u = run(seed, CONFIGS[name])
            row.append(m)
        avg = sum(row) / len(row)
        cells = " ".join(f"{m:>9,.0f}" for m in row)
        print(f"{name:28s} {cells}   {avg:>9,.0f}")
