"""Test forward-search wrapper on top of custom agent."""
import sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))

from sim import GameSim
from agent.custom import agent as custom_agent
from agent.custom.search import choose_extra_order
from agent.custom.board import Board


SEARCH_DAYS = {5, 10, 15, 20}
SEARCH_HOUR = 1

CANDIDATES_BY_DAY = {
    5:  [("none", []), ("melon_seed_2", [["BUY_SEED", "MELON", 2]]),
         ("wheat_seed_5", [["BUY_SEED", "WHEAT", 5]])],
    10: [("none", []), ("straw_seed_2", [["BUY_SEED", "STRAWBERRY", 2]]),
         ("sell_wheat_20", [["SELL", "WHEAT", 20]])],
    15: [("none", []), ("sell_fert_10", [["SELL", "FERTILIZER", 10]]),
         ("sell_straw_all", [["SELL", "STRAWBERRY", 20]])],
    20: [("none", []), ("sell_melon_5", [["SELL", "MELON", 5]]),
         ("buy_wheat_prod_10", [["BUY_PRODUCT", "WHEAT", 10]])],
}


def searching_agent_factory():
    picks = {}
    def act(obs, cfg=None):
        b = Board(obs)
        if b.day in SEARCH_DAYS and b.hour == SEARCH_HOUR:
            sim = GameSim.from_obs(obs)
            cands = CANDIDATES_BY_DAY.get(b.day, [("none", [])])
            # roll to end
            steps_to_end = 720 - int(obs.get("step", 0))
            best_label, best_extra, best_m = choose_extra_order(
                sim, custom_agent, cands, horizon=steps_to_end)
            picks.setdefault(b.day, []).append(best_label)
            base = custom_agent(obs, cfg)
            if best_extra:
                base["market"] = (base.get("market", []) + list(best_extra))[:10]
            return base
        return custom_agent(obs, cfg)
    return act, picks


if __name__ == "__main__":
    total_base = 0
    total_search = 0
    for seed in [1, 2, 3, 4, 5]:
        sim = GameSim(seed=seed)
        for _ in range(720):
            sim.step(custom_agent(sim.obs(0)), {})
        base_m = sim.money(0)

        agent, picks = searching_agent_factory()
        t = time.perf_counter()
        sim2 = GameSim(seed=seed)
        for _ in range(720):
            sim2.step(agent(sim2.obs(0)), {})
        search_m = sim2.money(0)
        dt = time.perf_counter() - t
        print(f"seed {seed}: base=${base_m:.0f}  search=${search_m:.0f}  delta={search_m-base_m:+.0f}  ({dt:.1f}s)  picks={picks}")
        total_base += base_m
        total_search += search_m
    print(f"\nAVG base=${total_base/5:.0f}  AVG search=${total_search/5:.0f}  delta={((total_search-total_base)/5):+.0f}")
