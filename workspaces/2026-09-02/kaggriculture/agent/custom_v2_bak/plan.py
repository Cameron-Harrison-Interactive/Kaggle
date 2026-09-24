"""
plan.py — WHERE things go on the board (build layout) and WHAT to plant/place.

Deliberately KEPT SEPARATE from the reactive task generator. This is the
long-horizon layout: "structure X belongs at tile (x,y)". Tasks then fire
naturally against the layout: if the tile is empty and the plan says
PASTURE, generate a BuildTask; if the pasture is empty and the plan says
SHEEP and we own a sheep, generate a PlaceAnimalTask; etc.

The layout is FIXED per-quad (per-quad determinism keeps our fields packed),
but WHEN we execute the layout is state-driven (we don't build a pasture
until we can afford the sheep to fill it).
"""

from .board import BOARD_SIZE, quadrant, SHED_SET, ANIMALS, CROPS

# ------------------------------------------------------------
# Per-quadrant tile roles.
#   "CROP" -> plant our current crop of choice
#   "PASTURE" / "COOP" -> structure + animal
#   "SKIP" -> leave empty (walkway, or too close to shed)
# ------------------------------------------------------------

# NW quad tiles: y in 0..4, x in 0..4. (4,4) is a shed-access tile — keep OPEN.
# Layout (row, col) — 5x5 grid:
#   rows 0-2 = crop field (15 tiles wheat)
#   row 3    = pastures (5 tiles)  -> sheep + cows
#   row 4    = coops (5 tiles)     -> geese, BUT (4,4) is shed access -> SKIP
NW_LAYOUT = {}
for y in range(5):
    for x in range(5):
        if (x, y) in SHED_SET:
            NW_LAYOUT[(x, y)] = "SKIP"
        elif y <= 2:
            NW_LAYOUT[(x, y)] = "CROP"
        elif y == 3:
            NW_LAYOUT[(x, y)] = "PASTURE"
        else:  # y == 4
            NW_LAYOUT[(x, y)] = "COOP"

# NE (y 0..4, x 5..9): rows 0-2 crop, row 3 pasture, row 4 coop.
# Shed access (5,4) is in NE — leave open.
NE_LAYOUT = {}
for y in range(5):
    for x in range(5, 10):
        if (x, y) in SHED_SET:
            NE_LAYOUT[(x, y)] = "SKIP"
        elif y <= 2:
            NE_LAYOUT[(x, y)] = "CROP"
        elif y == 3:
            NE_LAYOUT[(x, y)] = "PASTURE"
        else:
            NE_LAYOUT[(x, y)] = "COOP"

# SW (y 5..9, x 0..4): all crop (later: ongoing crops for strawberry)
SW_LAYOUT = {}
for y in range(5, 10):
    for x in range(5):
        if (x, y) in SHED_SET:
            SW_LAYOUT[(x, y)] = "SKIP"
        else:
            SW_LAYOUT[(x, y)] = "CROP"

# SE (y 5..9, x 5..9): all crop
SE_LAYOUT = {}
for y in range(5, 10):
    for x in range(5, 10):
        if (x, y) in SHED_SET:
            SE_LAYOUT[(x, y)] = "SKIP"
        else:
            SE_LAYOUT[(x, y)] = "CROP"

QUAD_LAYOUT = {"NW": NW_LAYOUT, "NE": NE_LAYOUT, "SW": SW_LAYOUT, "SE": SE_LAYOUT}


def full_layout():
    """Merged {(x,y): role} for every board tile."""
    out = {}
    for lay in QUAD_LAYOUT.values():
        out.update(lay)
    return out


# ------------------------------------------------------------
# Animal preference per structure slot.
# We fill pastures with SHEEP first (best net vs cost given wool prices),
# then COW. Coops with GOOSE.
# We fill DETERMINISTICALLY by tile order so subsequent turns are stable:
# pastures NW row 3 left-to-right get sheep first, then remaining pastures
# get cows.
# ------------------------------------------------------------

def desired_animal_for(x, y, existing_counts, targets=None):
    """existing_counts: {'SHEEP': n, 'COW': n, 'GOOSE': n}.
    targets: {'SHEEP': N, 'COW': N, 'GOOSE': N}. Falls back to DEFAULT_TARGETS."""
    t = targets or DEFAULT_TARGETS
    lay = full_layout().get((x, y))
    if lay == "COOP":
        if existing_counts.get("GOOSE", 0) < t["GOOSE"]:
            return "GOOSE"
        return None
    if lay == "PASTURE":
        if existing_counts.get("SHEEP", 0) < t["SHEEP"]:
            return "SHEEP"
        if existing_counts.get("COW", 0) < t["COW"]:
            return "COW"
        return None
    return None


# fallback if caller didn't pass explicit targets
DEFAULT_TARGETS = {"SHEEP": 3, "COW": 2, "GOOSE": 3}


# ------------------------------------------------------------
# Planting policy per role tile
# ------------------------------------------------------------

def desired_crop_for(x, y):
    """Which crop belongs on this tile if it's empty and marked CROP.
    Wheat is our staple: feeds animals AND produces sellable surplus.
    Later versions may split some tiles to STRAWBERRY (highest ROI ongoing)."""
    return "WHEAT"
