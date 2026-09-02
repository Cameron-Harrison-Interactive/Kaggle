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
from .pathing import nearest


# v5: fill all pasture/coop slots (10P + 8C = 18 animals)
V1_CFG = {
    "field_size_target": 78,
    "hires_target":      12,
    "sheep_target":      5,   # 5+5=10 pastures (max)
    "cow_target":        5,
    "goose_target":      6,
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


def agent(obs, configuration=None):
    b = Board(obs)

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

    farmer_act = action_for_unit(0, b.units[0], assignment.get(0), b)
    hand_acts = []
    for i in range(1, len(b.units)):
        hand_acts.append(action_for_unit(i, b.units[i], assignment.get(i), b))

    market = plan_market_orders(b, V1_CFG)

    return {"farmer": farmer_act, "hands": hand_acts, "market": market}
