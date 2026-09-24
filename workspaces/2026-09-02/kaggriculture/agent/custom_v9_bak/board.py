"""
board.py — read-only view of the game world that our planner uses.

Wraps the raw obs dict in a fast, ergonomic API. NO decision logic here — this
is pure "what does the world look like right now". Everything downstream reads
through Board so we have ONE place that knows the obs schema.

Coord convention: engine uses (x, y) with y growing DOWN. Tiles indexed as
farm["tiles"][y][x]. We keep the same convention throughout.
"""

BOARD_SIZE = 10
TURNS_PER_DAY = 24
SHED_CAP = 100

# Verbatim from engine — DO NOT redefine these anywhere else.
CROPS = {
    "WHEAT":      {"seed": 10, "first": 2, "max_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first": 2, "max_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first": 8, "max_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100,"first": 10,"max_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first": 10,"max_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "struct": "COOP",    "first": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "struct": "PASTURE", "first": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "struct": "PASTURE", "first": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER"]

# Shed-access tiles (NWSE order) — must match engine _shed_access_tiles().
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
SHED_SET = set(SHED_TILES)

# Quadrant of a tile.
def quadrant(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")

QUAD_TILES = {
    q: [(x, y) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE) if quadrant(x, y) == q]
    for q in ("NW", "NE", "SW", "SE")
}


class Board:
    """Read-only, per-turn view. Cheap to build; do NOT mutate."""

    def __init__(self, obs):
        self.obs = obs
        self.player = int(obs.get("player", 0))
        self.day = int(obs.get("day", 0))
        self.hour = int(obs.get("hour", 0))
        self.step = int(obs.get("step", 0))
        self.farms = obs["farms"]
        self.farm = self.farms[self.player]
        self.opp = self.farms[1 - self.player]
        self.private = obs["private"]
        self.shed = self.private["shed"]
        self.seeds = self.private["seeds"]
        self.inventories = self.private["inventories"]
        self.market = obs["market"]
        self.prices = self.market["prices"]
        self.inventory = self.market["inventory"]
        self.town = obs["town"]
        self.tiles = self.farm["tiles"]
        self.farmer = tuple(self.farm["farmer"])
        self.hands = [tuple(h) for h in self.farm["hands"]]
        self.units = [self.farmer] + self.hands  # index 0 = main farmer
        self.money = float(self.farm["money"])
        self.hires_today = int(self.farm["hires_today"])
        self.unlocked = list(self.farm["unlocked_quadrants"])
        self.unlocked_set = set(self.unlocked)

    # ---------- tile inspection ----------
    def tile(self, x, y):
        return self.tiles[y][x]

    def is_locked(self, x, y):
        return self.tiles[y][x] == "LOCKED"

    def is_empty(self, x, y):
        return self.tiles[y][x] is None

    def is_plant(self, x, y):
        t = self.tiles[y][x]
        return isinstance(t, dict) and t.get("kind") == "PLANT"

    def is_animal(self, x, y):
        t = self.tiles[y][x]
        return isinstance(t, dict) and "animal" in t

    def is_structure_empty(self, x, y, struct):
        """PASTURE or COOP with no animal placed."""
        t = self.tiles[y][x]
        return isinstance(t, dict) and t.get("kind") == struct and "animal" not in t

    def is_weed(self, x, y):
        t = self.tiles[y][x]
        return isinstance(t, dict) and t.get("kind") == "WEED"

    # ---------- inventories ----------
    def unit_inv(self, idx):
        """Farmer inventory dict — empty {} if not yet allocated."""
        if idx < len(self.inventories):
            return self.inventories[idx]
        return {}

    def unit_holding(self, idx, item):
        return self.unit_inv(idx).get(item, 0)

    def unit_carry_total(self, idx):
        return sum(self.unit_inv(idx).values())

    def shed_total(self):
        return sum(self.shed.values())

    def shed_room(self):
        return max(0, SHED_CAP - self.shed_total())

    # ---------- quadrant / tile queries ----------
    def owned_tiles(self):
        """All non-LOCKED tile coords."""
        out = []
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                if self.tiles[y][x] != "LOCKED":
                    out.append((x, y))
        return out

    def find_tiles(self, pred):
        """Iterate (x,y) where pred(tile) is truthy."""
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                t = self.tiles[y][x]
                if pred(t):
                    yield (x, y)

    def plants(self):
        return list(self.find_tiles(lambda t: isinstance(t, dict) and t.get("kind") == "PLANT"))

    def animals(self):
        return list(self.find_tiles(lambda t: isinstance(t, dict) and "animal" in t))

    def empty_tiles(self):
        """Owned, empty (None) tiles."""
        return list(self.find_tiles(lambda t: t is None))

    def empty_structures(self, struct):
        return list(self.find_tiles(lambda t: isinstance(t, dict) and t.get("kind") == struct and "animal" not in t))

    def weeds(self):
        return list(self.find_tiles(lambda t: isinstance(t, dict) and t.get("kind") == "WEED"))

    # ---------- market ----------
    def price(self, item):
        return int(self.prices.get(item, 0))

    def market_inv(self, item):
        return int(self.inventory.get(item, 0))
