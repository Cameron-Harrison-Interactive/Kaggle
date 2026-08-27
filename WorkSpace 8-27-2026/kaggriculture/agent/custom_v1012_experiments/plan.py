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

# NE (y 0..4, x 5..9): row 0 MELON (unlocks D0, plant D1, harvest D13,
# replant harvest D25 — 2 cycles × 6 units × ~$250 = huge cash boost),
# row 1 STRAWBERRY (full 4 productions from D11), row 2 CROP,
# row 3 PASTURE, row 4 COOP.
NE_LAYOUT = {}
for y in range(5):
    for x in range(5, 10):
        if (x, y) in SHED_SET:
            NE_LAYOUT[(x, y)] = "SKIP"
        elif y == 0:
            NE_LAYOUT[(x, y)] = "MELON"
        elif y == 1:
            NE_LAYOUT[(x, y)] = "STRAW"
        elif y == 2:
            NE_LAYOUT[(x, y)] = "CROP"
        elif y == 3:
            NE_LAYOUT[(x, y)] = "PASTURE"
        else:
            NE_LAYOUT[(x, y)] = "COOP"

# SW (y 5..9, x 0..4): row 5 STRAWBERRY, row 6 MELON, rows 7,8,9 CROP (wheat)
SW_LAYOUT = {}
for y in range(5, 10):
    for x in range(5):
        if (x, y) in SHED_SET:
            SW_LAYOUT[(x, y)] = "SKIP"
        elif y == 5:
            SW_LAYOUT[(x, y)] = "STRAW"
        elif y == 6:
            SW_LAYOUT[(x, y)] = "MELON"
        else:
            SW_LAYOUT[(x, y)] = "CROP"

# SE (y 5..9, x 5..9): row 5 STRAWBERRY, row 6 MELON, rows 7,8,9 CROP
SE_LAYOUT = {}
for y in range(5, 10):
    for x in range(5, 10):
        if (x, y) in SHED_SET:
            SE_LAYOUT[(x, y)] = "SKIP"
        elif y == 5:
            SE_LAYOUT[(x, y)] = "STRAW"
        elif y == 6:
            SE_LAYOUT[(x, y)] = "MELON"
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

# Live market context set by agent.py each turn (module-level; the built
# main.py inlines all modules into one namespace so this just works).
# straw_drain: sustainable STRAWBERRY units/day from live town shops
# (spy.shop_drain). Straw seeds cost $100 and the item floors at 61 net
# units sold without shops — replant into straw only when drained.
_MARKET_CTX = {"straw_drain": 1, "day": 0}


def set_market_ctx(straw_drain, day):
    _MARKET_CTX["straw_drain"] = straw_drain
    _MARKET_CTX["day"] = day


def desired_crop_for(x, y):
    """Which crop belongs on this tile if it's empty. Consults full_layout()."""
    role = full_layout().get((x, y))
    if role == "STRAW":
        # S62 shop-adaptive REPLANTING. Early straw (planted D2-6, BEFORE
        # the first shop draws at D3+) is +EV in expectation (E[straw shops
        # by D24] ~4 of 8; straw ~$50/day/tile vs wheat $16) — plant
        # unconditionally early. From D10+ the shop picture is known:
        # replant into straw only when drain supports it (>=2 straw shops,
        # ~>=13/day), else rotate the tile to wheat. (A day-1 gate measured
        # -$5k: it skipped every early planting — the valuable ones.)
        if _MARKET_CTX["day"] >= 10 and _MARKET_CTX["straw_drain"] < 13:
            return "WHEAT"
        return "STRAWBERRY"
    if role == "MELON":
        return "MELON"
    if role == "CARROT":
        return "CARROT"
    return "WHEAT"
