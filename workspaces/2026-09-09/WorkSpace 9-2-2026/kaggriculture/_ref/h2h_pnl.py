"""h2h_pnl.py — H2H matchup with executed-P&L decomposition per player.

Monkeypatches the engine's _commit_unit/_do_hire to log every executed
market commit (revenue/cost by item, per player), then runs both seats.

Usage: python3 _ref/h2h_pnl.py <bot.py> <opp.py> [seeds...]
"""
import sys, os, importlib.util
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim  # noqa: E402
import kaggle_environments.envs.kaggriculture.kaggriculture as K  # noqa: E402

_orig_commit = K._commit_unit
_orig_hire = K._do_hire
# farm object identity -> player index (farms are stable objects across the game)
_FARM_ID = {}
LOG = []


def _register(sim):
    _FARM_ID.clear()
    LOG.clear()
    for i in range(2):
        _FARM_ID[id(sim.state[0].observation.farms[i])] = i


def _commit(op, item, price, farm, private, market, shed_capacity=100):
    ok = _orig_commit(op, item, price, farm, private, market, shed_capacity)
    if ok:
        p = _FARM_ID.get(id(farm), -1)
        if op == "SELL":
            LOG.append((p, "rev", item, price))
        else:
            LOG.append((p, "cost", item, price))
    return ok


def _hire(farm, private, board_size, mult=K.FARM_HAND_COST_MULT):
    before = farm["money"]
    _orig_hire(farm, private, board_size, mult)
    p = _FARM_ID.get(id(farm), -1)
    LOG.append((p, "cost", "HIRE", before - farm["money"]))


K._commit_unit = _commit
K._do_hire = _hire


def load(path, name="m"):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def call(fn, obs):
    try:
        return fn(obs, None)
    except TypeError:
        return fn(obs)


def h2h_pnl(ma, mb, seeds):
    from collections import defaultdict
    pnl = [defaultdict(Counter), defaultdict(Counter)]
    finals = [0.0, 0.0]
    n_games = 0
    for s in seeds:
        for seat_a in (0, 1):
            sim = GameSim(seed=s)
            _register(sim)
            for _ in range(720):
                o0, o1 = sim.obs(0), sim.obs(1)
                a0 = call(ma.agent if seat_a == 0 else mb.agent, o0)
                a1 = call(mb.agent if seat_a == 0 else ma.agent, o1)
                sim.step(a0, a1)
            # money attribution: player i in sim vs bot identity
            bot_seat = seat_a
            finals[0] += sim.money(bot_seat)
            finals[1] += sim.money(1 - bot_seat)
            n_games += 1
            for p, kind, item, price in LOG:
                who = 0 if p == bot_seat else 1
                pnl[who][kind][item] += price
    K._commit_unit = _orig_commit
    K._do_hire = _orig_hire
    return finals[0] / n_games, finals[1] / n_games, pnl


if __name__ == "__main__":
    bot = load(sys.argv[1], "bot")
    opp = load(sys.argv[2], "opp")
    seeds = [int(x) for x in sys.argv[3:]] or [1, 2, 3, 4, 5, 6]
    fa, fb, pnl = h2h_pnl(bot, opp, seeds)
    print(f"bot_avg={fa:,.0f}  opp_avg={fb:,.0f}  margin={fa-fb:+,.0f}")
    for who, name in ((0, "BOT "), (1, "OPP ")):
        rev = pnl[who]["rev"]
        cost = pnl[who]["cost"]
        print(f"\n{name} revenue ({sum(rev.values()):,.0f}): " +
              ", ".join(f"{k}={v:,.0f}" for k, v in sorted(rev.items(), key=lambda kv: -kv[1])))
        print(f"{name} costs   ({sum(cost.values()):,.0f}): " +
              ", ".join(f"{k}={v:,.0f}" for k, v in sorted(cost.items(), key=lambda kv: -kv[1])))
