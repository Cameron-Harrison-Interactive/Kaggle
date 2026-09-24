"""
executor.py — turns an ASSIGNED (unit, task) into ONE primitive engine action.

This is where the routing bugs traditionally live: pickup/carry/walk/execute
sequencing. We centralize the rule:

    A unit's turn boils down to ONE of:
      1) If it's not on the target tile -> STEP toward target (respecting
         detour to shed if it needs to PICKUP required_items first).
      2) If it's on the target tile AND has required_items -> terminal action.
      3) If it's on the target tile but is missing required_items ->
         it should never have been routed here (assigner failed). Fallback: DROP.

    A unit that has EXCESS carry (>= drop_threshold) should first DROP at shed
    before its next task pickup. We treat that as a separate short-circuit
    task called "AutoDrop" attached before any long walk to a distant target.

Pickup is expressed as a MICRO-DETOUR: if the unit needs WHEAT to FEED but has
none, we first route it to the nearest shed-access tile and emit a PICKUP,
then next turn route it to the animal. This function returns the immediate
action; the surrounding loop just calls it again next turn — no persistent
"I'm on a multi-step mission" state needed.
"""

from .board import SHED_TILES, SHED_SET
from .pathing import step_toward, nearest, manhattan


def is_on_shed_tile(pos):
    return tuple(pos) in SHED_SET


def action_for_unit(unit_idx, pos, task, board):
    """Return the engine action list for this unit this turn.

    Returns ["PASS"] if there's genuinely nothing productive to do.
    """
    if task is None:
        return _idle_action(unit_idx, pos, board)

    target = task.target
    unit_inv = board.unit_inv(unit_idx)

    # 1) Check required items — if missing, detour to shed for PICKUP.
    missing = {}
    for item, n in task.required_items.items():
        held = unit_inv.get(item, 0)
        if held < n:
            missing[item] = n - held

    if missing:
        return _pickup_detour(pos, missing, board)

    # 2) On the target tile? execute.
    if tuple(pos) == tuple(target):
        return task.terminal_action(unit_idx, board)

    # 3) Otherwise walk toward the target.
    direction = step_toward(pos, target)
    if direction is None:
        return task.terminal_action(unit_idx, board)
    return [direction]


def _pickup_detour(pos, missing, board):
    """Walk to nearest shed-access tile, then PICKUP the first missing item.

    We pick ONE item per turn (engine supports one op per unit per turn).
    Grab a modest bundle (>=n needed, capped by what's in shed & shed access).
    """
    # Pick the item to fetch — largest need first.
    item, n_need = max(missing.items(), key=lambda kv: kv[1])

    # If shed has none of this item, we can't do anything — PASS so we don't
    # spin against the wall.
    have_in_shed = board.shed.get(item, 0)
    if have_in_shed <= 0:
        return ["PASS"]

    # Are we already on a shed-access tile?
    if is_on_shed_tile(pos):
        from .board import ANIMALS
        # Animals: pick up exactly ONE (each PLACE consumes 1 tile).
        # Consumables (WHEAT, FERTILIZER): grab a modest batch for reuse.
        if item in ANIMALS:
            take = 1
        else:
            take = min(max(n_need, 3), have_in_shed)
        return ["PICKUP", item, take]

    # Walk toward the closest shed-access tile.
    target, _ = nearest(pos, SHED_TILES)
    direction = step_toward(pos, target)
    if direction is None:
        # Already there but is_on_shed_tile said no? Shouldn't happen; PASS.
        return ["PASS"]
    return [direction]


def _idle_action(unit_idx, pos, board):
    """Unit has no task. If carrying anything, take it to the shed."""
    unit_inv = board.unit_inv(unit_idx)
    if any(v > 0 for v in unit_inv.values()):
        if is_on_shed_tile(pos):
            return ["DROP"]
        target, _ = nearest(pos, SHED_TILES)
        direction = step_toward(pos, target)
        return [direction] if direction else ["DROP"]
    return ["PASS"]
