"""
Strict lane routes for v6.6, designed from Nosiru's Trial-01/02/03 diagrams.

Board is 10x10, split into four 5x5 quadrants. Each quadrant is entered from
its shed-side corner, so routes are FLIPPED per quadrant via local coordinates
(ax, ay) where:
  NW: local (0,0) = board (4,4) shed corner; ax grows LEFT, ay grows UP
  NE: local (0,0) = board (5,4); ax grows RIGHT, ay grows UP
  SW: local (0,0) = board (4,5); ax grows LEFT, ay grows DOWN
  SE: local (0,0) = board (5,5); ax grows RIGHT, ay grows DOWN
So a route expressed in local coords can be reused in any quadrant by mapping
through `to_global`.

Rule: each worker follows ONE route in order, one tile per turn. At each tile
it performs whatever action the tile needs (water/harvest/plant/dig, OR feed
an animal on a grass/pasture tile). Only when the tile needs nothing does it
move to the next route point. Workers do NOT divert to other jobs until they
reach the end of their route, then they repeat.

ANIMAL PLACEMENT: animals live on the route so crop workers feed them as they
pass (this is the key insight from the diagrams — no separate tender).
"""

BOARD = 10
H = BOARD // 2  # 5

# Quadrant entry corners (shed side) in global coords, and axis directions.
# (origin_x, origin_y, dx, dy)
QUAD_ORIGIN = {
    "NW": (H - 1, H - 1, -1, -1),
    "NE": (H,     H - 1, +1, -1),
    "SW": (H - 1, H,     -1, +1),
    "SE": (H,     H,     +1, +1),
}


def to_global(quad, local_pts):
    """Map a list of local (ax, ay) route points to global board coords."""
    ox, oy, dx, dy = QUAD_ORIGIN[quad]
    return [(ox + dx * ax, oy + dy * ay) for (ax, ay) in local_pts]


# --------------------------------------------------------------------------
# Animal layout (local coords). The red L-route must pass every animal tile.
# Cows on the far column (ax=4, ay=0..3), sheep on the bottom-ish row
# (ay=4, ax=0..3), exactly like Trial-01/02.
# --------------------------------------------------------------------------
ANIMALS = {
    "NW": {
        "cows":   [(4, 0), (4, 1), (4, 2), (4, 3)],   # rightmost column
        "sheep":  [(0, 4), (1, 4), (2, 4), (3, 4)],   # bottom row
    },
}


def animal_positions(quad):
    a = ANIMALS["NW"]
    return to_global(quad, a["cows"]), to_global(quad, a["sheep"])


# --------------------------------------------------------------------------
# TRIAL 01: 3 workers per quadrant
#   red  = L-route: up cow column, across sheep row (ANIMALS)
#   black = outer crop border (left col + top row + right-of-animal)
#   blue  = middle S-curve covering remaining crop tiles
# --------------------------------------------------------------------------
def trial01_routes():
    red = [(4, 0), (4, 1), (4, 2), (4, 3), (4, 4),
           (3, 4), (2, 4), (1, 4), (0, 4)]
    black = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
             (1, 0), (2, 0), (3, 0)]
    blue = [(1, 1), (2, 1), (3, 1),
            (3, 2), (2, 2), (1, 2),
            (1, 3), (2, 3), (3, 3)]
    return {"red": red, "black": black, "blue": blue}


# --------------------------------------------------------------------------
# TRIAL 02: 2 workers per quadrant (plus red animal L)
#   red  = same animal L-route
#   black = zig-zag over the LEFT two columns of crops
#   blue  = zig-zag over the MIDDLE two columns of crops
# Column 4 is the cow column (handled by red).
# --------------------------------------------------------------------------
def trial02_routes():
    red = [(4, 0), (4, 1), (4, 2), (4, 3), (4, 4),
           (3, 4), (2, 4), (1, 4), (0, 4)]
    # black: columns 0-1, boustrophedon from entry
    black = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
             (1, 4), (1, 3), (1, 2), (1, 1), (1, 0)]
    # blue: columns 2-3
    blue = [(2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
            (3, 4), (3, 3), (3, 2), (3, 1), (3, 0)]
    return {"red": red, "black": black, "blue": blue}


# --------------------------------------------------------------------------
# TRIAL 03: 2 workers per quadrant, animals in CENTER (2x3 block).
#   cows/sheep sit at local (1..3, 2..3) center band.
#   black & red are S-curves that weave THROUGH the animals so they get fed
#   as the workers pass. (Trial-03 diagram: animals in middle, two S routes.)
# --------------------------------------------------------------------------
ANIMALS_03 = {
    "cows":  [(1, 2), (3, 2), (1, 3), (3, 3)],
    "sheep": [(2, 2), (2, 3)],
}


def trial03_routes():
    # black S: col0 down, col1 up (passes animals at (1,2),(1,3)), col2 down
    black = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
             (1, 4), (1, 3), (1, 2), (1, 1), (1, 0),
             (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)]
    # red S: col3 up from entry (passes (3,2),(3,3)), col4 up
    red = [(4, 4), (4, 3), (4, 2), (4, 1), (4, 0),
           (3, 0), (3, 1), (3, 2), (3, 3), (3, 4)]
    return {"black": black, "red": red}


TRIALS = {
    "trial01": (trial01_routes, 3),
    "trial02": (trial02_routes, 3),
    "trial03": (trial03_routes, 2),
}


def get_routes(trial):
    fn, n = TRIALS[trial]
    return fn(), n


def all_worker_routes(trial, active_quads):
    """Return list of (route_points_global) for every worker across all active
    quadrants. Workers are assigned round-robin: first N workers are the N
    routes in quadrant order."""
    routes_local, n_per = get_routes(trial)
    names = list(routes_local.keys())
    result = []
    for q in active_quads:
        for nm in names:
            result.append(to_global(q, routes_local[nm]))
    return result, names
