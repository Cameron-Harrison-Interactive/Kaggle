"""
assigner.py — matches units to tasks.

Greedy priority-first with distance tiebreak, plus REGION-AFFINITY bias so
work spreads across the whole farm instead of piling up near the shed.

Score for (unit, task):
    score = 1000 * task.priority - detour_cost(unit, task) + region_bonus

region_bonus rewards a unit for taking tasks in its assigned "home" quadrant.
Hands are assigned homes deterministically by index modulo unlocked quads,
so every quadrant gets covered as we hire more bodies.
"""

from .board import SHED_TILES, SHED_SET, quadrant, BOARD_SIZE
from .pathing import manhattan, nearest


REGION_BONUS = 0           # disabled — was reducing throughput; keep round-robin
                           # infrastructure for future experiments
REGION_HOME_PENALTY = 0


def _home_quad_for_unit(unit_idx, unlocked_quads):
    """Assign hands to quadrants with a bias: keep MOST hands in NW/NE (where
    animals + shed access live) and only push OVERFLOW hands to SW/SE. This
    prevents an SE-home hand from walking 12+ steps to feed a NW animal while
    still ensuring SE gets planted eventually.

    Layout (for 10 hands + farmer):
      farmer -> NW
      hands 1,2,3 -> NW (core field + animals)
      hands 4,5   -> NE
      hands 6,7   -> SW  (only if unlocked; else NW)
      hands 8,9   -> SE  (only if unlocked; else NE)
      hands 10+   -> round-robin through unlocked
    """
    if unit_idx == 0:
        return "NW"
    unlocked = set(unlocked_quads) if unlocked_quads else {"NW"}
    # Priority list mapping hand index -> preferred quad
    preferred = ["NW", "NW", "NW", "NE", "NE", "SW", "SW", "SE", "SE"]
    if unit_idx - 1 < len(preferred):
        q = preferred[unit_idx - 1]
        if q in unlocked:
            return q
        # Fallback: next-best unlocked quad
    # Round-robin fallback (any extra hands)
    order = ["NW", "NE", "SW", "SE"]
    order = [q for q in order if q in unlocked] or ["NW"]
    return order[(unit_idx - 1) % len(order)]


def _detour_cost(unit_pos, unit_inv, task):
    """Steps from unit to task including a possible shed detour for required items."""
    missing = False
    for item, n in task.required_items.items():
        if unit_inv.get(item, 0) < n:
            missing = True
            break
    if not missing:
        return manhattan(unit_pos, task.target)
    shed_tile, d_to_shed = nearest(unit_pos, SHED_TILES)
    return d_to_shed + 1 + manhattan(shed_tile, task.target)


def _region_bias(unit_home, task):
    """Positive bonus if task is in unit's home quad, small penalty otherwise.

    Only applied to WATER and PLANT tasks — the routine field work that
    piles up locally and causes SE to never be planted. HARVEST, FEED,
    BUILD, PLACE, FERTILIZE, DIG, DROP all remain region-agnostic so
    scarce work (an escaped animal to feed, a place to fill) still finds
    the closest available hand regardless of quadrant.
    """
    if task.kind not in ("WATER", "PLANT"):
        return 0
    q = quadrant(task.target[0], task.target[1])
    if q == unit_home:
        return REGION_BONUS
    return -REGION_HOME_PENALTY


def assign(board, tasks, taboo=None):
    n_units = len(board.units)
    if not tasks:
        return {i: None for i in range(n_units)}

    # De-dup by (target, kind)
    seen = {}
    for t in tasks:
        key = (t.target, t.kind)
        if key not in seen or t.priority > seen[key].priority:
            seen[key] = t
    tasks = list(seen.values())

    assignment = {}
    remaining_tasks = list(tasks)
    remaining_units = list(range(n_units))

    unit_pos = {i: board.units[i] for i in remaining_units}
    unit_inv = {i: board.unit_inv(i) for i in remaining_units}
    unit_home = {i: _home_quad_for_unit(i, board.unlocked) for i in remaining_units}

    while remaining_tasks and remaining_units:
        best_score = -1e18
        best_pair = None
        for u in remaining_units:
            for t in remaining_tasks:
                d = _detour_cost(unit_pos[u], unit_inv[u], t)
                score = t.priority * 1000 - d + _region_bias(unit_home[u], t)
                if score > best_score:
                    best_score = score
                    best_pair = (u, t)
        if best_pair is None:
            break
        u, t = best_pair
        assignment[u] = t
        remaining_units.remove(u)
        remaining_tasks.remove(t)

    for u in remaining_units:
        assignment[u] = None
    return assignment
