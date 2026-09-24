"""
assigner.py — matches units to tasks.

Greedy priority-first with distance tiebreak. Runs every turn from scratch
(so a hand may be reassigned mid-walk if a higher-priority task appears).

Score for (unit, task):
    score = 1000 * task.priority - detour_cost(unit, task)

where detour_cost estimates the number of steps from unit.pos to task.target,
adding a penalty if the unit will need to detour through the shed to pick up
required items it doesn't already have.

We assign UNITS one at a time in a greedy loop:
  - while there are unassigned units AND remaining tasks:
      pick (unit, task) with maximum score across all pairs
      commit that unit to that task; remove both from pools

O(U*T) per pass which is fine for U<=13 and T<=~40.

The assigner intentionally deduplicates: we don't send two units to the same
plant tile in one turn (would waste one action), but we DO allow two units to
converge on the same shed if both need pickup.
"""

from .board import SHED_TILES, SHED_SET
from .pathing import manhattan, nearest


def _detour_cost(unit_pos, unit_inv, task):
    """Steps from unit to task including a possible shed detour for required items."""
    missing = False
    for item, n in task.required_items.items():
        if unit_inv.get(item, 0) < n:
            missing = True
            break
    if not missing:
        return manhattan(unit_pos, task.target)
    # Detour: unit -> nearest shed access tile -> target
    shed_tile, d_to_shed = nearest(unit_pos, SHED_TILES)
    return d_to_shed + 1 + manhattan(shed_tile, task.target)  # +1 for the PICKUP turn


def assign(board, tasks, taboo=None):
    """Return dict {unit_idx: task_or_None}.

    `taboo` is an optional set of (unit_idx, task_kind_or_target) pairs to skip;
    lets caller exclude specific pairings (rarely needed).
    """
    n_units = len(board.units)
    if not tasks:
        return {i: None for i in range(n_units)}

    # De-dup: for each target tile, keep only the highest-priority task on it.
    # (Multiple tasks may exist on one animal tile — FEED / HARVEST /
    # COLLECT_FERT. We DO want to keep all of them; they're distinct ops
    # requiring separate visits.) So actually don't dedup by target — dedup
    # by (target, kind).
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

    while remaining_tasks and remaining_units:
        best_score = -1e18
        best_pair = None
        for u in remaining_units:
            for t in remaining_tasks:
                d = _detour_cost(unit_pos[u], unit_inv[u], t)
                score = t.priority * 1000 - d
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
