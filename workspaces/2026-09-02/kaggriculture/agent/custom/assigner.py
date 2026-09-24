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


REGION_BONUS = 0           # tested multiple times; infrastructure kept
REGION_HOME_PENALTY = 0

# Task stickiness: reward a unit for taking a task whose required items it
# already carries (avoids the "hand picks up fert, task disappears, hand
# wanders to water" bug).
CARRY_MATCH_BONUS = 5000   # bigger than any distance-based tiebreaker


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

    # ---- ROLE-POOL ASSIGNMENT ---------------------------------------------
    # Split tasks into groups; reserve a MINIMUM number of hands for each
    # group so PLANT/WATER don't starve behind FEED/CARE. This is the fix
    # for "35 empty tiles at end of game".
    #
    # Groups:
    #   ANIMAL: FEED, CARE, HARVEST_ANIMAL, COLLECT_FERTILIZER, PLACE
    #   FIELD:  WATER, PLANT, FERTILIZE, HARVEST, DIG, BUILD
    #   OTHER:  DROP (fills wherever)
    ANIMAL_KINDS = {"FEED", "CARE", "HARVEST_ANIMAL", "COLLECT_FERTILIZER", "PLACE"}
    FIELD_KINDS = {"WATER", "PLANT", "FERTILIZE", "HARVEST", "DIG", "BUILD"}

    animal_tasks = [t for t in tasks if t.kind in ANIMAL_KINDS]
    field_tasks  = [t for t in tasks if t.kind in FIELD_KINDS]
    other_tasks  = [t for t in tasks if t.kind not in ANIMAL_KINDS and t.kind not in FIELD_KINDS]

    # Reservation policy:
    # - If we have >= 8 hands, reserve at least 2 for FIELD work.
    # - Never reserve more field-hands than there are field tasks.
    # - ANIMAL still gets priority if starvation is imminent (pri >= 95).
    # Reservation disabled: reserved=1 lost -$8k solo & -$26k H2H,
    # reserved=2 lost -$16k solo. Kept infrastructure for future use.
    reserved_field = 0

    assignment = {}
    remaining_tasks = list(tasks)
    remaining_units = list(range(n_units))

    unit_pos  = {i: board.units[i] for i in remaining_units}
    unit_inv  = {i: board.unit_inv(i) for i in remaining_units}
    unit_home = {i: _home_quad_for_unit(i, board.unlocked) for i in remaining_units}

    # --- PHASE 1: emergency animal FEED at pri >= 95 (starvation) --------
    urgent_animal = [t for t in remaining_tasks
                     if t.kind == "FEED" and t.priority >= 95]
    for t in urgent_animal:
        best_u = None
        best_score = -1e18
        for u in remaining_units:
            d = _detour_cost(unit_pos[u], unit_inv[u], t)
            carry_match = 0
            if t.required_items and all(unit_inv[u].get(k, 0) >= n
                                         for k, n in t.required_items.items()):
                carry_match = CARRY_MATCH_BONUS
            score = t.priority * 1000 - d + carry_match
            if score > best_score:
                best_score = score
                best_u = u
        if best_u is not None:
            assignment[best_u] = t
            remaining_units.remove(best_u)
            remaining_tasks.remove(t)

    # --- PHASE 2: reserved FIELD hands (2 dedicated planters) -------------
    reserved_ct = 0
    field_pool = [t for t in remaining_tasks if t.kind in FIELD_KINDS]
    while reserved_ct < reserved_field and field_pool and remaining_units:
        best_score = -1e18
        best_pair = None
        for u in remaining_units:
            for t in field_pool:
                d = _detour_cost(unit_pos[u], unit_inv[u], t)
                carry_match = 0
                if t.required_items and all(unit_inv[u].get(k, 0) >= n
                                             for k, n in t.required_items.items()):
                    carry_match = CARRY_MATCH_BONUS
                # BOOST field tasks so a PLANT-pri-40 beats CARE-pri-65
                # within this dedicated pool.
                score = (t.priority + 40) * 1000 - d + carry_match + _region_bias(unit_home[u], t)
                if score > best_score:
                    best_score = score
                    best_pair = (u, t)
        if best_pair is None:
            break
        u, t = best_pair
        assignment[u] = t
        remaining_units.remove(u)
        remaining_tasks.remove(t)
        field_pool = [x for x in remaining_tasks if x.kind in FIELD_KINDS]
        reserved_ct += 1

    # --- PHASE 3: greedy on remaining tasks/units (baseline behavior) -----
    while remaining_tasks and remaining_units:
        best_score = -1e18
        best_pair = None
        for u in remaining_units:
            for t in remaining_tasks:
                d = _detour_cost(unit_pos[u], unit_inv[u], t)
                carry_match = 0
                if t.required_items:
                    if all(unit_inv[u].get(item, 0) >= n
                           for item, n in t.required_items.items()):
                        carry_match = CARRY_MATCH_BONUS
                score = t.priority * 1000 - d + _region_bias(unit_home[u], t) + carry_match
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
