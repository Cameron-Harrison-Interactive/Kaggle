"""
pathing.py — cheap Manhattan pathing on the 10x10 board.

The board has no impassable tiles for MOVEMENT — every tile is reachable
by walking through anything (locked or unlocked). Movement onto a LOCKED
tile is legal; only tile OPERATIONS are blocked there. So distance is
plain Manhattan. We keep this module tiny; if a future map obstacle
appears we can swap in BFS without touching callers.
"""

from .board import BOARD_SIZE


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def step_toward(src, dst):
    """Return one of NORTH/SOUTH/EAST/WEST that gets us closer, or None if arrived."""
    sx, sy = src
    dx, dy = dst
    if (sx, sy) == (dx, dy):
        return None
    # Prefer moving on the axis with the larger delta first (arbitrary but
    # deterministic; keeps hands moving in a consistent pattern).
    ax = dx - sx
    ay = dy - sy
    if abs(ax) >= abs(ay):
        if ax > 0 and sx + 1 < BOARD_SIZE:
            return "EAST"
        if ax < 0 and sx - 1 >= 0:
            return "WEST"
        if ay > 0 and sy + 1 < BOARD_SIZE:
            return "SOUTH"
        if ay < 0 and sy - 1 >= 0:
            return "NORTH"
    else:
        if ay > 0 and sy + 1 < BOARD_SIZE:
            return "SOUTH"
        if ay < 0 and sy - 1 >= 0:
            return "NORTH"
        if ax > 0 and sx + 1 < BOARD_SIZE:
            return "EAST"
        if ax < 0 and sx - 1 >= 0:
            return "WEST"
    return None


def apply_step(src, direction):
    x, y = src
    if direction == "NORTH": return (x, y - 1)
    if direction == "SOUTH": return (x, y + 1)
    if direction == "EAST":  return (x + 1, y)
    if direction == "WEST":  return (x - 1, y)
    return (x, y)


def nearest(src, targets):
    """Return (target, distance) for the closest coord in `targets`, or (None, inf)."""
    if not targets:
        return None, float("inf")
    best = None
    best_d = float("inf")
    for t in targets:
        d = manhattan(src, t)
        if d < best_d:
            best_d = d
            best = t
    return best, best_d
