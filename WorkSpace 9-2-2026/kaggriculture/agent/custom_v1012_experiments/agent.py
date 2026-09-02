"""
agent.py — v1 top-level agent. Wheat field + small herd in NW quad.

Milestone target: solo $30-50k with animals live through full 30 days,
zero escapes, zero errors.
"""

from .board import Board, BOARD_SIZE, CROPS, SHED_TILES
from .tasks import (generate_tasks, generate_planting_tasks,
                    generate_build_and_place_tasks, DropTask)
from .assigner import assign
from .executor import action_for_unit
from .economy import plan_market_orders
from .spy import SPY, shop_drain
from . import plan as farm_plan
from .pathing import nearest

try:    # package mode
    from .plan import set_market_ctx
except ImportError:   # built main.py: import lines stripped; inlined def used
    pass


# v5: fill all pasture/coop slots (10P + 8C = 18 animals)
V1_CFG = {
    "field_size_target": 78,
    "hires_target":      12,
    "sheep_target":      5,   # 5+5=10 pastures (max)
    "cow_target":        5,
    "goose_target":      5,   # S61: -1 goose (was 6). Sweep: +$4k solo,
                              # -$1.3k H2H avg (noise). User: "we can lower
                              # 1 Animal that should be enough to cover".
    "buy_land":          True,
    "skip_se":           True,   # BT-style: skip the $4000 SE quad
    "skip_sw":           False,  # 2-quad tested worse: $75k vs $82k
}

DROP_CARRY_THRESHOLD = 6         # force drop if carrying >= this


def _forced_drop_task(board, unit_idx):
    inv = board.unit_inv(unit_idx)
    if sum(inv.values()) >= DROP_CARRY_THRESHOLD:
        st, _ = nearest(board.units[unit_idx], SHED_TILES)
        return DropTask(st, priority=200)
    return None


def _adaptive_herd(drain, day):
    """S62: herd sized by structure slots; shop drain tunes only the RATIO.

    Corrected economics (fert included): fert is $40-100/animal/DAY no
    matter what shops spawn (town never consumes fert; it floors at 494
    cumulative units — with ~17 animals we barely reach that cap). So every
    animal is worth its slot even when its product floors: ~$17/visit of
    fert on top of product value. Solo-tested day-pacing and drain-sized
    herds were both NEGATIVE (-$3k to -$5k); filling structures won.
    Shops tune only:
      - sheep vs cows: wool floors at 58 net units with 0 YARN_STOREs
        (BT sold exactly 59 on a zero-yarn seed) -> favor cows then;
      - geese: egg price is log-shaped (never crashes) -> fill coops
        when any egg shop exists, else 5.
    """
    yarn = drain.get("WOOL", 1) >= 13
    if yarn:
        sheep, cows = 5, 5
    else:
        sheep, cows = 3, 7
    geese = 8 if drain.get("EGG", 1) >= 13 else 5
    return sheep, cows, geese


def agent(obs, configuration=None):
    b = Board(obs)

    # Live opponent intelligence: money-jump sell detection, dump-hour
    # histogram, production forecast from their tiles, market pressure.
    # Powers the pre-sell counters in plan_market_orders.
    SPY.update(obs, b)

    # S62: town-drain-adaptive build. The seed's shop RNG decides which
    # items pay (visible live in obs.town.unlocked_shops).
    drain = shop_drain(obs.get("town"))
    set_market_ctx(drain.get("STRAWBERRY", 1), b.day)
    s_t, c_t, g_t = _adaptive_herd(drain, b.day)
    herd = {"SHEEP": s_t, "COW": c_t, "GOOSE": g_t}
    V1_CFG["sheep_target"] = s_t
    V1_CFG["cow_target"] = c_t
    V1_CFG["goose_target"] = g_t

    herd = {"SHEEP": V1_CFG["sheep_target"],
            "COW":   V1_CFG["cow_target"],
            "GOOSE": V1_CFG["goose_target"]}

    tasks = []
    tasks.extend(generate_tasks(b))
    tasks.extend(generate_planting_tasks(b))
    tasks.extend(generate_build_and_place_tasks(b, herd_targets=herd))

    forced = {}
    for u in range(len(b.units)):
        t = _forced_drop_task(b, u)
        if t is not None:
            forced[u] = t

    assignment = assign(b, tasks)
    for u, t in forced.items():
        assignment[u] = t

    # IDLE-DROP: hands with no task but carrying any inventory should return
    # to shed and drop, so the shed fills up faster and market SELL orders
    # actually commit. Without this, hands can walk PASS/pace-in-place for
    # 12+ hours holding wool/egg/milk until end-of-day drop, blocking sales.
    for u in range(len(b.units)):
        if assignment.get(u) is None:
            inv = b.unit_inv(u)
            if sum(inv.values()) > 0:
                st, _ = nearest(b.units[u], SHED_TILES)
                assignment[u] = DropTask(st, priority=10)

    farmer_act = action_for_unit(0, b.units[0], assignment.get(0), b)
    hand_acts = []
    for i in range(1, len(b.units)):
        hand_acts.append(action_for_unit(i, b.units[i], assignment.get(i), b))

    market = plan_market_orders(b, V1_CFG, spy=SPY)

    return {"farmer": farmer_act, "hands": hand_acts, "market": market}
