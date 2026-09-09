"""Aster: one dated portfolio, compiled into this turn's legal actions.

Every strategic choice is a ``Commitment``.  A commitment owns all of its
dated operations, inputs, outputs, capital, site occupancy, and market orders.
``Ledger`` replays commitments through one cash/work/market account;
``portfolio()`` contains only commitments that survive that replay.  Market
orders and field tasks are therefore two views of the same accepted plan.
"""

import math
from bisect import bisect_right
from dataclasses import dataclass, field, replace
from functools import lru_cache


# Engine laws ----------------------------------------------------------------


@dataclass(frozen=True)
class Crop:
    seed: int
    first: int
    last: int
    interval: int
    cap: int
    ongoing: bool


@dataclass(frozen=True)
class Animal:
    cost: int
    structure: str
    first: int
    interval: int
    held: int
    product: str


CROPS = {
    "WHEAT": Crop(10, 2, 4, 0, 6, False),
    "CARROT": Crop(20, 2, 3, 0, 4, False),
    "TOMATO": Crop(50, 8, 8, 1, 4, True),
    "STRAWBERRY": Crop(100, 10, 10, 2, 4, True),
    "MELON": Crop(80, 10, 12, 0, 6, False),
}

ANIMALS = {
    "GOOSE": Animal(300, "COOP", 4, 1, 4, "EGG"),
    "COW": Animal(400, "PASTURE", 8, 2, 6, "MILK"),
    "SHEEP": Animal(500, "PASTURE", 6, 3, 6, "WOOL"),
}

PRODUCTS = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER",
)

SHOPS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}

MARKET = {
    "WHEAT": (25, 400, "sqrt", .80, "log", .20),
    "CARROT": (35, 450, "log", .20, "sqrt", .70),
    "TOMATO": (60, 200, "linear", .40, "sqrt", .60),
    "STRAWBERRY": (120, 100, "sqrt", .70, "linear", 1.60),
    "MELON": (250, 300, "log", .20, "sq", 3.60),
    "EGG": (50, 332, "linear", .40, "log", .20),
    "MILK": (160, 122, "sqrt", .60, "linear", 1.60),
    "WOOL": (200, 105, "log", .20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", .40, "linear", .40),
}

BOARD = 10
HALF = BOARD // 2
DAY_TURNS = 24
SEASON_DAYS = 30
MARKET_ZERO = 10_000
MAX_ORDERS = 10
SHED_CAPACITY = 100
LAND_ORDER = ("NE", "SW", "SE")
LAND_PRICES = (1000, 2000, 4000)
SHED_TILES = (
    (HALF - 1, HALF - 1), (HALF, HALF - 1),
    (HALF - 1, HALF), (HALF, HALF),
)


def _get(value, key, default=None):
    return value.get(key, default) if isinstance(value, dict) else getattr(value, key, default)


def _shape(name, value):
    value = max(0.0, value)
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    return value


@lru_cache(maxsize=65_536)
def price(item, inventory):
    base, scale, below, below_target, above, above_target = MARKET[item]
    delta = int(inventory) - MARKET_ZERO
    curve, target = (below, below_target) if delta < 0 else (above, above_target)
    amplitude = target * base / _shape(curve, scale)
    return max(1, int(round(base - math.copysign(amplitude * _shape(curve, abs(delta)), delta))))


@lru_cache(maxsize=65_536)
def sale_value(item, inventory, units):
    return sum(price(item, int(inventory) + offset) for offset in range(max(0, int(units))))


@lru_cache(maxsize=65_536)
def buy_cost(item, inventory, units):
    return sum(price(item, int(inventory) - offset - 1) for offset in range(max(0, int(units))))


@lru_cache(maxsize=None)
def fib(index):
    a, b = 1, 1
    for _ in range(max(0, int(index))):
        a, b = b, a + b
    return a


_DISTANCE = tuple(
    tuple(
        abs(left % BOARD - right % BOARD) + abs(left // BOARD - right // BOARD)
        for right in range(BOARD * BOARD)
    )
    for left in range(BOARD * BOARD)
)
_TILE_BY_ID = tuple(
    (index % BOARD, index // BOARD)
    for index in range(BOARD * BOARD)
)


def distance(left, right):
    """Board Manhattan distance without allocation or memoization hashing."""
    return _DISTANCE[left[1] * BOARD + left[0]][right[1] * BOARD + right[0]]


def step_toward(origin, target):
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    if abs(dx) >= abs(dy) and dx:
        return "EAST" if dx > 0 else "WEST"
    if dy:
        return "SOUTH" if dy > 0 else "NORTH"
    return None


@lru_cache(maxsize=None)
def travel(tile):
    return 1 + 2 * min(distance(tile, shed) for shed in SHED_TILES)


def quadrant(tile):
    x, y = tile
    return ("N" if y < HALF else "S") + ("W" if x < HALF else "E")


TILES = tuple(sorted(
    ((x, y) for y in range(BOARD) for x in range(BOARD)),
    key=lambda tile: (travel(tile), tile),
))
# Observation ----------------------------------------------------------------


@dataclass
class Memory:
    last_step: int = -1
    last_market: dict | None = None
    own_flow: dict = field(default_factory=dict)
    opponent_daily: dict = field(default_factory=lambda: {item: 0.0 for item in PRODUCTS})
    samples: int = 0
    planned_day: int = -1
    targets: dict = field(default_factory=dict)
    routes: dict = field(default_factory=dict)
    crew_target: int | None = None
    day_tasks: tuple = ()
    completed_tasks: set = field(default_factory=set)
    opponent_schedule_step: int = -1
    opponent_schedule: list | None = None

    def reset(self):
        self.__dict__.update(Memory().__dict__)


MEMORY = {0: Memory(), 1: Memory()}


@dataclass
class World:
    player: int
    step: int
    day: int
    hour: int
    farm: dict
    opponent: dict
    tiles: list
    money: float
    shed: dict
    seeds: dict
    inventories: list
    actors: list
    market: dict
    shops: tuple
    unlocked: tuple

    @classmethod
    def read(cls, observation):
        player = int(_get(observation, "player", 0))
        farms = _get(observation, "farms", [])
        farm, opponent = farms[player], farms[1 - player]
        private = _get(observation, "private", {})
        inventories = [dict(inv) for inv in (_get(private, "inventories", []) or [{}])]
        actors = [tuple(farm["farmer"])] + [tuple(pos) for pos in farm.get("hands", [])]
        while len(inventories) < len(actors):
            inventories.append({})
        market = _get(observation, "market", {})
        return cls(
            player, int(_get(observation, "step", 0) or 0),
            int(_get(observation, "day", 0)), int(_get(observation, "hour", 0)),
            farm, opponent, farm["tiles"], float(farm.get("money", 0)),
            dict(_get(private, "shed", {}) or {}), dict(_get(private, "seeds", {}) or {}),
            inventories, actors, dict(market["inventory"]),
            tuple(_get(observation, "town", {}).get("unlocked_shops", [])),
            tuple(farm.get("unlocked_quadrants", ("NW",))),
        )

    @property
    def horizon(self):
        return max(1, SEASON_DAYS - self.day)

    @property
    def stock(self):
        """Everything owned; carried goods become shed stock at day end."""
        stock = {item: int(self.shed.get(item, 0)) for item in PRODUCTS}
        for inventory in self.inventories:
            for item in PRODUCTS:
                stock[item] += int(inventory.get(item, 0))
        return stock

    @property
    def shed_stock(self):
        """Goods that the current market phase can actually sell."""
        return {item: int(self.shed.get(item, 0)) for item in PRODUCTS}

    @property
    def pending(self):
        pending = {name: int(self.shed.get(name, 0)) for name in ANIMALS}
        for inventory in self.inventories:
            for name in ANIMALS:
                pending[name] += int(inventory.get(name, 0))
        return pending

    @property
    def shed_tiles(self):
        return tuple(tile for tile in SHED_TILES if self.tiles[tile[1]][tile[0]] != "LOCKED")


@lru_cache(maxsize=32_768)
def town_consumption(item, shops, step):
    """Exact public demand applied after `step` by the engine."""
    if step < 0:
        return 0
    day = step // DAY_TURNS
    units = 0
    if step % 4 == 0:
        units += sum(
            2 if len(SHOPS.get(shop, ())) == 1 else 1
            for shop in shops if item in SHOPS.get(shop, ())
        )
    if step % 12 == 0 and item != "FERTILIZER":
        units += 4 if day >= 20 else 2 if day >= 10 else 1
    return units


@lru_cache(maxsize=8_192)
def town_demand(item, shops, day):
    return sum(
        town_consumption(item, shops, day * DAY_TURNS + hour)
        for hour in range(DAY_TURNS)
    )


def expected_town_demand(world, item, day):
    """Expected public demand after known and future random shop unlocks.

    Shop identities are hidden until their three-day unlock, but the draw is
    uniform without replacement from a public set.  Freezing today's shops for
    the whole horizon systematically prices every not-yet-unlocked buyer at
    zero; the expectation below is the exact mean over that public draw.
    """
    current = set(world.shops)
    remaining = [shop for shop in SHOPS if shop not in current]
    future_unlocks = min(
        len(remaining), max(0, day // 3 - world.day // 3),
    )

    def weight(shop):
        products = SHOPS[shop]
        return (2 if len(products) == 1 else 1) if item in products else 0

    active_weight = sum(weight(shop) for shop in current)
    expected_weight = active_weight
    if remaining:
        expected_weight += future_unlocks * sum(map(weight, remaining)) / len(remaining)
    shop_demand = (DAY_TURNS // 4) * expected_weight
    center_demand = town_demand(item, (), day)
    return shop_demand + center_demand


def observe_market(memory, world):
    if memory.last_market is not None:
        n = memory.samples
        previous_step = world.step - 1
        shops = world.shops
        # A shop unlocked at the day boundary did not consume on the preceding
        # transition; the engine appends it after town demand.
        if (
            world.hour == 0 and world.day and world.day % 3 == 0
            and world.day // 3 <= len(SHOPS)
        ):
            shops = shops[:-1]
        for item in PRODUCTS:
            observed = world.market[item] - memory.last_market[item]
            own = memory.own_flow.get(item, 0.0)
            town = town_consumption(item, shops, previous_step)
            per_turn = observed - own + town
            daily = per_turn * DAY_TURNS
            memory.opponent_daily[item] = (memory.opponent_daily[item] * n + daily) / (n + 1)
        memory.samples += 1
    memory.last_market = dict(world.market)
    memory.own_flow = {}


# One planning vocabulary -----------------------------------------------------


@dataclass(frozen=True)
class Flow:
    day: int
    item: str
    units: int
    from_stock: bool = False


@dataclass(frozen=True)
class Operation:
    day: int
    action: tuple
    need: str | None = None
    bulk: int = 1
    protects: tuple = ()
    critical: bool = False


@dataclass(frozen=True)
class Commitment:
    key: str
    role: str
    tile: tuple | None
    capital: int = 0
    orders: tuple = ()
    operations: tuple = ()
    inputs: tuple = ()
    outputs: tuple = ()
    future_orders: tuple = ()
    fertilized: bool = False

    @property
    def site(self):
        return self.tile


@dataclass
class Projection:
    feasible: bool
    terminal: float
    cash: tuple
    market: tuple
    hires: tuple
    orders: list
    commitments: tuple
    rival_revenue: float = 0.0

    @property
    def utility(self):
        """The candidate-dependent part of final score margin."""
        return self.terminal - self.rival_revenue

    def worth(self, day, item, units):
        when = min(max(0, int(day)), len(self.market) - 1)
        return sale_value(item, self.market[when][item], units)


@dataclass(frozen=True)
class PortfolioBook:
    """One compiled physical portfolio, independent of liquidation timing."""

    commitments: tuple
    capital: tuple
    orders: tuple
    arrivals: tuple
    stock_sales: tuple
    needs: tuple
    work: tuple
    workloads: tuple


def joint_sale_value(item, inventory, ours, theirs):
    """Replay the engine's per-unit lockstep quote for one shared pool."""
    inventory = int(inventory)
    ours, theirs = max(0, int(ours)), max(0, int(theirs))
    own_value = rival_value = 0
    paired = min(ours, theirs)
    for _ in range(paired):
        quote = price(item, inventory)
        own_value += quote
        rival_value += quote
        inventory += 2
    if ours > paired:
        extra = ours - paired
        own_value += sale_value(item, inventory, extra)
        inventory += extra
    elif theirs > paired:
        extra = theirs - paired
        rival_value += sale_value(item, inventory, extra)
        inventory += extra
    return own_value, rival_value, inventory


def joint_buy_cost(item, inventory, ours, theirs):
    """Replay the engine's post-buy lockstep quote for a shared input."""
    inventory = int(inventory)
    ours, theirs = max(0, int(ours)), max(0, int(theirs))
    own_cost = rival_cost = 0
    paired = min(ours, theirs)
    for _ in range(paired):
        quote = price(item, inventory - 1)
        own_cost += quote
        rival_cost += quote
        inventory -= 2
    if ours > paired:
        extra = ours - paired
        own_cost += buy_cost(item, inventory, extra)
        inventory -= extra
    elif theirs > paired:
        extra = theirs - paired
        rival_cost += buy_cost(item, inventory, extra)
        inventory -= extra
    return own_cost, rival_cost, inventory


def _valued(operations, outputs):
    """Resolve prerequisite loss after the commitment's output is known."""
    totals = {}
    for flow in outputs:
        totals[flow.item] = totals.get(flow.item, 0) + flow.units
    protects = tuple(sorted(totals.items()))
    return tuple(
        replace(operation, protects=protects) if operation.critical else operation
        for operation in operations
    )


def _sale_day(day, horizon):
    return day + 1 if day + 1 < horizon else None


def crop_commitment(
    world, tile, name, capital=0, orders=(), state=None, fertilized=False,
):
    crop = CROPS[name]
    horizon = world.horizon
    operations, inputs, outputs, future_orders = [], [], [], []
    orders = list(orders)
    if state is None:
        planted_day = world.day
        age = 0
        held = 0 if crop.ongoing else 1
        watered_today = False
        unwatered = 1
        fertilized_until = -1
        tile_state = world.tiles[tile[1]][tile[0]]
        if tile_state not in (None, "LOCKED"):
            operations.append(Operation(0, ("DIG",), critical=True))
        operations.append(Operation(
            0, ("PLANT", name), need="SEED:" + name, critical=True,
        ))
    else:
        planted_day = int(state["planted_day"])
        age = world.day - planted_day
        held = int(state.get("yield_units", 0))
        watered_today = bool(state.get("watered_today"))
        unwatered = int(state.get("consecutive_unwatered", 0))
        fertilized_until = int(state.get("fertilized_until_day", -1))

    harvest_age = None
    if not crop.ongoing:
        window_start = (crop.last + 1) // 2
        natural_harvest = min(crop.last, window_start + crop.cap - 2)
        harvest_age = min(natural_harvest, age + horizon - 2)
        if harvest_age < crop.first:
            return None
    production_count = max(0, (age - crop.first) // max(1, crop.interval) + 1) if crop.ongoing and age >= crop.first else 0

    for day in range(horizon):
        current_age = world.day + day - planted_day
        if day == 0:
            watered = watered_today
        else:
            watered = False
        window = (crop.last + 1) // 2 <= current_age <= crop.last
        next_age = current_age + 1
        produces = (
            crop.ongoing and next_age >= crop.first
            and (next_age - crop.first) % crop.interval == 0
            and production_count < crop.cap
        )
        should_water = not watered and (
            unwatered >= 1 or window or (fertilized and produces)
        )
        can_gain_extra = (
            (not crop.ongoing and window and held + 1 < crop.cap)
            or (crop.ongoing and produces)
        )
        if (
            fertilized and should_water and can_gain_extra
            and fertilized_until < world.day + day
        ):
            operations.append(Operation(
                day, ("FERTILIZE",), need="FERTILIZER",
                protects=((name, 1),),
            ))
            inputs.append(Flow(day, "FERTILIZER", 1))
            fertilized_until = world.day + day + 2
        if should_water:
            bonus = 2 if fertilized_until >= world.day + day else 1
            operations.append(Operation(
                day, ("WATER",),
                protects=((name, bonus),) if window and unwatered < 1 else (),
                critical=unwatered >= 1,
            ))
            watered = True
            if not crop.ongoing and window:
                held = min(crop.cap, held + bonus)

        if not crop.ongoing and (
            current_age >= harvest_age
            or (current_age >= crop.first and held >= crop.cap)
        ):
            sell = _sale_day(day, horizon)
            if held and sell is not None:
                operations.append(Operation(day, ("HARVEST",), protects=((name, held),)))
                outputs.append(Flow(sell, name, held))
            next_harvest = day + natural_harvest + 1
            if next_harvest >= horizon:
                break
            if day == 0:
                capital += crop.seed
                orders.append(("BUY_SEED", name, 1))
            else:
                future_orders.append((day, ("BUY_SEED", name, 1), crop.seed))
            operations.append(Operation(
                day, ("PLANT", name), need="SEED:" + name, critical=True,
            ))
            operations.append(Operation(day, ("WATER",), critical=True))
            planted_day = world.day + day
            held = 1
            watered_today = True
            unwatered = 0
            fertilized_until = -1
            harvest_age = natural_harvest
            continue

        if produces:
            gain = 2 if watered and fertilized_until >= world.day + day else 1
            if held and held + gain > crop.cap:
                sell = _sale_day(day, horizon)
                if sell is not None:
                    operations.append(Operation(day, ("HARVEST",), protects=((name, held),)))
                    outputs.append(Flow(sell, name, held))
                    held = 0
            held = min(crop.cap, held + gain)
            production_count += 1

        if watered:
            unwatered = 0
        else:
            unwatered += 1
            if unwatered >= 2:
                break

        if crop.ongoing and (production_count >= crop.cap or day == horizon - 2) and held:
            sell = _sale_day(day, horizon)
            if sell is not None:
                operations.append(Operation(day, ("HARVEST",), protects=((name, held),)))
                outputs.append(Flow(sell, name, held))
                held = 0

    if not outputs:
        return None
    return Commitment(
        f"crop:{name}:{tile}:{'fert' if fertilized else 'plain'}",
        name, tile, capital, tuple(orders),
        _valued(operations, outputs), tuple(inputs), tuple(outputs),
        tuple(future_orders), fertilized,
    )


def animal_commitment(world, tile, name, capital=0, orders=(), state=None):
    animal = ANIMALS[name]
    horizon = world.horizon
    operations, inputs, outputs = [], [], []
    if state is None:
        placed_day = world.day
        held = pending_bonus = 0
        fed_today = cared_today = False
        fertilizer_available = False
        tile_state = world.tiles[tile[1]][tile[0]]
        if (
            tile_state not in (None, "LOCKED")
            and not (
                isinstance(tile_state, dict)
                and tile_state.get("kind") == animal.structure
                and not tile_state.get("animal")
            )
        ):
            operations.append(Operation(0, ("DIG",), critical=True))
            tile_state = None
        if not (isinstance(tile_state, dict) and tile_state.get("kind") == animal.structure):
            operations.append(Operation(0, ("BUILD_" + animal.structure,), critical=True))
        operations.append(Operation(0, ("PLACE", name), need=name, critical=True))
        consecutive_unfed = 0
    else:
        placed_day = int(state["placed_day"])
        held = int(state.get("yield_units", 0))
        pending_bonus = int(state.get("pending_care_bonus", 0))
        fed_today = bool(state.get("fed_today"))
        cared_today = bool(state.get("cared_today"))
        fertilizer_available = bool(state.get("fertilizer_available"))
        consecutive_unfed = int(state.get("consecutive_unfed", 0))

    for day in range(horizon):
        fed = fed_today if day == 0 else False
        cared = cared_today if day == 0 else False
        if day < horizon - 1:
            if not fed:
                operations.append(Operation(
                    day, ("FEED",), need="WHEAT",
                    protects=((animal.product, 1),),
                    critical=consecutive_unfed >= 1,
                ))
                inputs.append(Flow(day, "WHEAT", 1))
                fed = True
            if not cared:
                operations.append(Operation(
                    day, ("CARE",), protects=((animal.product, 1),),
                ))
                cared = True
        if fertilizer_available:
            sell = _sale_day(day, horizon)
            if sell is not None:
                operations.append(Operation(day, ("COLLECT_FERTILIZER",), protects=(("FERTILIZER", 1),)))
                outputs.append(Flow(sell, "FERTILIZER", 1))

        next_day = world.day + day + 1
        since_first = next_day - placed_day - animal.first
        produces = since_first >= 0 and since_first % animal.interval == 0
        if produces:
            gain = 1 + pending_bonus
            if held and held + gain > animal.held:
                sell = _sale_day(day, horizon)
                if sell is not None:
                    operations.append(Operation(day, ("HARVEST",), protects=((animal.product, held),)))
                    outputs.append(Flow(sell, animal.product, held))
                    held = 0
            held = min(animal.held, held + gain)
            pending_bonus = 0
        if cared and fed:
            pending_bonus += 1
        consecutive_unfed = 0 if fed else consecutive_unfed + 1
        fertilizer_available = True
        if day == horizon - 2 and held:
            sell = _sale_day(day, horizon)
            if sell is not None:
                operations.append(Operation(day, ("HARVEST",), protects=((animal.product, held),)))
                outputs.append(Flow(sell, animal.product, held))
                held = 0

    product_units = sum(flow.units for flow in outputs if flow.item == animal.product)
    if not product_units:
        return None
    return Commitment(
        f"animal:{name}:{tile}", name, tile, capital, tuple(orders),
        _valued(operations, outputs), tuple(inputs), tuple(outputs),
    )


def sale_commitment(item, units, day):
    return Commitment(
        f"stock:{item}", item, None, outputs=(Flow(day, item, units, True),),
    )


def land_bundle(asset, land_cost):
    return replace(
        asset,
        key="land+" + asset.key,
        capital=asset.capital + land_cost,
        orders=(("BUY_LAND",),) + asset.orders,
    )


def use_owned_seed(commitment, available):
    """Pay an immediate replant order from seed inventory exactly once."""
    if commitment is None or available <= 0 or commitment.role not in CROPS:
        return commitment, available
    target = ("BUY_SEED", commitment.role)
    orders = list(commitment.orders)
    for index, order in enumerate(orders):
        if order[:2] != target or int(order[2]) <= 0:
            continue
        units = int(order[2])
        if units == 1:
            orders.pop(index)
        else:
            orders[index] = (order[0], order[1], units - 1)
        return replace(
            commitment,
            capital=commitment.capital - CROPS[commitment.role].seed,
            orders=tuple(orders),
        ), available - 1
    return commitment, available


# Dated ledger ----------------------------------------------------------------


def _group_orders(orders):
    grouped, atomic = {}, []
    for order in orders:
        if order[0] in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"):
            key = order[:2]
            grouped[key] = grouped.get(key, 0) + int(order[2])
        else:
            atomic.append(list(order))
    merged = [[op, item, units] for (op, item), units in grouped.items() if units > 0]
    sales = [order for order in merged if order[0] == "SELL"]
    buys = [order for order in merged if order[0] != "SELL"]
    land = [order for order in atomic if order[0] == "BUY_LAND"]
    hires = [order for order in atomic if order[0] == "HIRE"]
    return sales + land + hires + buys


def _market_capacity(world, day):
    """Order slots remaining in a projected day, not in a single turn."""
    turns = max(1, DAY_TURNS - world.hour) if day == 0 else DAY_TURNS
    return MAX_ORDERS * turns


@lru_cache(maxsize=512)
def _spawned(existing, count):
    occupancy = {tile: 0 for tile in SHED_TILES}
    for position in existing:
        if position in occupancy:
            occupancy[position] += 1
    result = []
    for _ in range(count):
        tile = min(SHED_TILES, key=lambda point: (occupancy[point], SHED_TILES.index(point)))
        occupancy[tile] += 1
        result.append(tile)
    return tuple(result)


def _path(origin, tiles):
    """Return the constructive visit order and its movement cost."""
    remaining = set(tiles)
    route, cost = [], 0
    while remaining:
        step, tile = min((distance(origin, tile), tile) for tile in remaining)
        cost += step
        origin = tile
        remaining.remove(tile)
        route.append(tile)
    return tuple(route), cost


def _requirements(tiles, jobs):
    required = {}
    for tile in tiles:
        for operation in jobs[tile]:
            if operation.need and not operation.need.startswith("SEED:"):
                required[operation.need] = required.get(operation.need, 0) + operation.bulk
    return required


def _route_cost_from(origin, inventory, route, required, actions, depots):
    missing = {
        item: units - int(inventory.get(item, 0))
        for item, units in required.items()
        if units > int(inventory.get(item, 0))
    }
    links = sum(distance(left, right) for left, right in zip(route, route[1:]))
    if missing:
        approach = min(
            distance(origin, depot) + (distance(depot, route[0]) if route else 0)
            for depot in depots
        )
        return len(missing) + approach + links + actions
    approach = distance(origin, route[0]) if route else 0
    return approach + links + actions


def _route_cost(origin, inventory, route, jobs, depots):
    return _route_cost_from(
        origin, inventory, route, _requirements(route, jobs),
        sum(len(jobs[tile]) for tile in route), depots,
    )


def _insert(
    origin, route, links, actions, tile, missing_count, depots,
):
    """Price insertion on integer tile IDs without Python distance calls."""
    distances = _DISTANCE
    missing = missing_count > 0
    starts = depots if missing else (origin,)
    pickup = missing_count
    best = None
    # Every insertion except the first shares the same best depot approach.
    # Computing that approach once removes a four-way depot loop from every
    # interior edge without changing the constructive route heuristic.
    if route:
        first = route[0]
        approach, _, start = min(
            (
                distances[origin][depot] + distances[depot][first],
                _TILE_BY_ID[depot], depot,
            )
            for depot in starts
        )
        for index in range(1, len(route) + 1):
            previous = route[index - 1]
            following = route[index] if index < len(route) else None
            movement = distances[previous][tile]
            if following is not None:
                movement += (
                    distances[tile][following] - distances[previous][following]
                )
            choice = (
                approach + pickup + links + movement + actions,
                index, _TILE_BY_ID[start], links + movement,
            )
            if best is None or choice < best:
                best = choice

    # Inserting at the front can change which depot is cheapest, so retain the
    # exact per-depot comparison for this single edge.
    following = route[0] if route else None
    for start in starts:
        approach = distances[origin][start] if missing else 0
        movement = distances[start][tile]
        if following is not None:
            movement += distances[tile][following]
        new_links = links + (
            distances[tile][following] if following is not None else 0
        )
        choice = (
            approach + pickup + links + movement + actions,
            0, _TILE_BY_ID[start], new_links,
        )
        if best is None or choice < best:
            best = choice
    return best[1], best[0], best[3]


def _partition(jobs, roots, inventories, capacities, depots=SHED_TILES):
    """Assign complete tile bundles to the least-loaded constructive routes."""
    tile_for = {tile[1] * BOARD + tile[0]: tile for tile in jobs}
    job_ids = tuple(tile_for)
    root_ids = tuple(tile[1] * BOARD + tile[0] for tile in roots)
    depot_ids = tuple(tile[1] * BOARD + tile[0] for tile in depots)
    routes = [[] for _ in roots]
    links = [0 for _ in roots]
    costs = [0 for _ in roots]
    requirements = [{} for _ in roots]
    missing_counts = [0 for _ in roots]
    actions = [0 for _ in roots]
    tile_requirements = {
        tile_id: _requirements((tile_for[tile_id],), jobs)
        for tile_id in job_ids
    }
    tile_actions = {
        tile_id: len(jobs[tile_for[tile_id]])
        for tile_id in job_ids
    }
    ranked = sorted(
        job_ids,
        key=lambda tile_id: (
            tile_actions[tile_id]
            + min(_DISTANCE[root][tile_id] for root in root_ids),
            tile_for[tile_id],
        ),
        reverse=True,
    )
    for tile in ranked:
        choices = []
        normalized_costs = [
            cost / max(1, capacity)
            for cost, capacity in zip(costs, capacities)
        ]
        ranked_loads = sorted(
            ((load, actor) for actor, load in enumerate(normalized_costs)),
            reverse=True,
        )
        total_cost = sum(costs)
        for actor in range(len(roots)):
            added_missing = sum(
                requirements[actor].get(item, 0) <= int(inventories[actor].get(item, 0))
                < requirements[actor].get(item, 0) + units
                for item, units in tile_requirements[tile].items()
            )
            missing_count = missing_counts[actor] + added_missing
            action_count = actions[actor] + tile_actions[tile]
            index, cost, link_count = _insert(
                root_ids[actor], routes[actor], links[actor], action_count,
                tile, missing_count, depot_ids,
            )
            normalized = cost / max(1, capacities[actor])
            if len(ranked_loads) == 1:
                other = 0
            elif ranked_loads[0][1] == actor:
                other = ranked_loads[1][0]
            else:
                other = ranked_loads[0][0]
            choices.append((
                max(normalized, other), total_cost - costs[actor] + cost,
                actor, cost, index, action_count, link_count, missing_count,
            ))
        _, _, actor, cost, index, action_count, link_count, missing_count = min(choices)
        routes[actor] = routes[actor][:index] + [tile] + routes[actor][index:]
        links[actor] = link_count
        costs[actor] = cost
        for item, units in tile_requirements[tile].items():
            requirements[actor][item] = requirements[actor].get(item, 0) + units
        missing_counts[actor] = missing_count
        actions[actor] = action_count
    return [[_TILE_BY_ID[tile] for tile in route] for route in routes], costs


def _labor(world, day, jobs, memory=None):
    """Return the cheapest feasible crew, or the best attainable partial crew."""
    if not jobs:
        return 0, 0, True
    turns = max(1, DAY_TURNS - world.hour) if day == 0 else DAY_TURNS
    existing = tuple(world.actors) if day == 0 else (SHED_TILES[0],)
    existing_inventories = tuple(world.inventories) if day == 0 else ({},)

    # During the live day, price the same stable routes execution is following.
    # Repartitioning the residual work here used to invent emergency hires for
    # actors whose accepted routes were already on schedule.
    if day == 0 and memory is not None and memory.routes:
        routed = {
            actor: [tile for tile in route if tile in jobs]
            for actor, route in memory.routes.items()
        }
        assigned = {tile for route in routed.values() for tile in route}
        if assigned == set(jobs):
            crew = max(routed, default=-1) + 1
            roots = existing + _spawned(existing, max(0, crew - len(existing)))
            inventories = existing_inventories + tuple({} for _ in range(max(0, crew - len(existing))))
            capacities = tuple(
                turns if actor < len(existing) else max(0, turns - 1)
                for actor in range(crew)
            )
            costs = [
                _route_cost(
                    roots[actor], inventories[actor], routed.get(actor, ()), jobs,
                    world.shed_tiles,
                )
                for actor in range(crew)
            ]
            if all(cost <= capacities[actor] for actor, cost in enumerate(costs)):
                return max(0, crew - len(existing)), sum(costs), True

    # Every operation consumes a turn even in the impossible zero-travel
    # schedule.  Crews below this bound cannot be feasible, so constructing
    # their routes proves nothing and was the planner's dominant cost on large
    # farms.
    operations = sum(len(bundle) for bundle in jobs.values())
    existing_capacity = len(existing) * turns
    hire_capacity = max(1, turns - 1)
    first_hires = max(
        0, math.ceil(max(0, operations - existing_capacity) / hire_capacity),
    )
    # Across the crew's disjoint routes, visiting N distinct work tiles needs
    # at least N-C unit-length links for C actors, even before approach and
    # pickup travel.  Fold that unavoidable movement into the capacity lower
    # bound so crews that cannot possibly fit are never constructed.
    while first_hires < MAX_ORDERS:
        crew = len(existing) + first_hires
        movement_floor = max(0, len(jobs) - crew)
        total_capacity = existing_capacity + first_hires * hire_capacity
        if operations + movement_floor <= total_capacity:
            break
        first_hires += 1
    max_hires = min(
        _market_capacity(world, day),
        max(0, len(jobs) - len(existing)),
    )
    partial = None
    # The zero-travel lower bound can itself exceed the ten market slots.  In
    # that case there is no feasible crew, but execution still needs the best
    # legal partial crew rather than an empty search (and a None sentinel).
    first_legal_hires = min(first_hires, max_hires)
    for hires in range(first_legal_hires, max_hires + 1):
        roots = existing + _spawned(existing, hires)
        inventories = existing_inventories + tuple({} for _ in range(hires))
        capacities = tuple([turns] * len(existing) + [max(0, turns - 1)] * hires)
        _, costs = _partition(jobs, roots, inventories, capacities, world.shed_tiles)
        if all(cost <= capacity for cost, capacity in zip(costs, capacities)):
            return hires, sum(costs), True
        overflow = tuple(max(0, cost - capacity) for cost, capacity in zip(costs, capacities))
        choice = sum(overflow), max(overflow, default=0), hires, sum(costs)
        if partial is None or choice < partial[0]:
            partial = choice, hires, sum(costs)
    _, hires, cost = partial
    return hires, cost, False


def _labor_bound(world, day, jobs):
    """Admissible optimistic crew bound for portfolio branch-and-bound."""
    turns = max(1, DAY_TURNS - world.hour) if day == 0 else DAY_TURNS
    existing = len(world.actors) if day == 0 else 1
    operations = sum(len(bundle) for bundle in jobs.values())
    existing_capacity = existing * turns
    hire_capacity = max(1, turns - 1)
    hires = max(
        0, math.ceil(max(0, operations - existing_capacity) / hire_capacity),
    )
    max_hires = min(
        _market_capacity(world, day),
        max(0, len(jobs) - existing),
    )
    while hires <= max_hires:
        crew = existing + hires
        movement_floor = max(0, len(jobs) - crew)
        total_capacity = existing_capacity + hires * hire_capacity
        if operations + movement_floor <= total_capacity:
            return hires, operations + movement_floor, True
        hires += 1
    return (
        max_hires,
        operations + max(0, len(jobs) - existing - max_hires),
        False,
    )


def _visible_opponent_schedule(world):
    """Project dated output from every public rival crop and animal."""
    schedule = [{item: 0.0 for item in PRODUCTS} for _ in range(world.horizon)]
    proxy = replace(
        world,
        farm=world.opponent,
        tiles=world.opponent["tiles"],
        unlocked=tuple(world.opponent.get("unlocked_quadrants", ("NW",))),
    )
    for y, row in enumerate(proxy.tiles):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            commitment = None
            if tile.get("kind") == "PLANT" and tile.get("crop") in CROPS:
                commitment = crop_commitment(
                    proxy, (x, y), tile["crop"], state=tile,
                    fertilized=int(tile.get("fertilized_until_day", -1)) >= world.day,
                )
            elif tile.get("animal"):
                commitment = animal_commitment(
                    proxy, (x, y), tile["animal"], state=tile,
                )
            if commitment is None:
                continue
            for flow in commitment.outputs:
                if flow.day < world.horizon:
                    schedule[flow.day][flow.item] += flow.units
    return schedule


def _visible_opponent_inputs(world):
    """Project dated public input demand from rival crops and animals."""
    schedule = [{item: 0.0 for item in PRODUCTS} for _ in range(world.horizon)]
    proxy = replace(
        world,
        farm=world.opponent,
        tiles=world.opponent["tiles"],
        unlocked=tuple(world.opponent.get("unlocked_quadrants", ("NW",))),
    )
    for y, row in enumerate(proxy.tiles):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            commitment = None
            if tile.get("kind") == "PLANT" and tile.get("crop") in CROPS:
                commitment = crop_commitment(
                    proxy, (x, y), tile["crop"], state=tile,
                    fertilized=int(tile.get("fertilized_until_day", -1)) >= world.day,
                )
            elif tile.get("animal"):
                commitment = animal_commitment(
                    proxy, (x, y), tile["animal"], state=tile,
                )
            if commitment is None:
                continue
            for flow in commitment.inputs:
                if flow.day < world.horizon:
                    schedule[flow.day][flow.item] += flow.units
    return schedule


def _opponent_schedule(world, memory):
    """Cache the public lifecycle replay once per observed turn."""
    if memory.opponent_schedule_step != world.step:
        memory.opponent_schedule = _visible_opponent_schedule(world)
        memory.opponent_schedule_step = world.step
    return memory.opponent_schedule


class Ledger:
    """The sole economic authority: replay commitments, cash, work and market."""

    def __init__(self, world, memory):
        self.world = world
        self.memory = memory
        self._labor_cache = {}
        self._bound_cache = {}
        self._candidate_cache = {}
        visible = _opponent_schedule(world, memory)
        visible_inputs = _visible_opponent_inputs(world)
        visible_mean = {
            item: sum(day[item] for day in visible) / max(1, world.horizon)
            for item in PRODUCTS
        }
        residual = {
            item: max(0.0, memory.opponent_daily[item] - visible_mean[item])
            for item in PRODUCTS
        }
        self.opponent = [
            {item: day[item] + residual[item] for item in PRODUCTS}
            for day in visible
        ]
        observed_inputs = {
            item: max(0.0, -memory.opponent_daily[item])
            for item in PRODUCTS
        }
        self.opponent_inputs = [
            {
                item: max(day[item], observed_inputs[item])
                for item in PRODUCTS
            }
            for day in visible_inputs
        ]
        self.town = tuple(
            {
                item: int(round(expected_town_demand(
                    world, item, world.day + day,
                )))
                for item in PRODUCTS
            }
            for day in range(world.horizon)
        )

    def candidate(self, tile, role, owned=False, land_cost=0, fertilized=False):
        """Build each immutable physical option once per planning search."""
        key = tile, role, bool(owned), int(land_cost), bool(fertilized)
        if key not in self._candidate_cache:
            self._candidate_cache[key] = _candidate(
                self.world, tile, role, owned, land_cost, fertilized,
            )
        return self._candidate_cache[key]

    @staticmethod
    def workload(day, jobs):
        # Future days share the same roots, empty inventories and 24-turn
        # capacity.  Routing consumes only bundle length and pickup demand;
        # action names, output values and the calendar label are irrelevant.
        # Canonicalizing that sufficient statistic turns equivalent lifecycle
        # days into one exact scheduling problem.
        workload = []
        for tile, operations in jobs.items():
            required = {}
            for operation in operations:
                if operation.need and not operation.need.startswith("SEED:"):
                    required[operation.need] = (
                        required.get(operation.need, 0) + operation.bulk
                    )
            if day:
                # Future actor inventories are empty, so only the presence of
                # each pickup type affects route cost.
                required = {item: 1 for item in required}
            workload.append((tile, len(operations), tuple(sorted(required.items()))))
        return 0 if day == 0 else 1, tuple(sorted(workload))

    def labor(self, day, jobs, key=None):
        key = self.workload(day, jobs) if key is None else key
        if key not in self._labor_cache:
            self._labor_cache[key] = _labor(self.world, day, jobs, self.memory)
        return self._labor_cache[key]

    def labor_bound(self, day, jobs, key=None):
        key = self.workload(day, jobs) if key is None else key
        if key not in self._bound_cache:
            self._bound_cache[key] = _labor_bound(self.world, day, jobs)
        return self._bound_cache[key]

    def compile(self, commitments):
        """Compile invariant physical flows and work exactly once per closure."""
        commitments = tuple(commitments)
        horizon = self.world.horizon
        capital = [0 for _ in range(horizon)]
        orders = [[] for _ in range(horizon)]
        arrivals = [{} for _ in range(horizon)]
        stock_sales = [{} for _ in range(horizon)]
        needs = [{} for _ in range(horizon)]
        work = [{} for _ in range(horizon)]

        capital[0] = sum(commitment.capital for commitment in commitments)
        for commitment in commitments:
            orders[0].extend(commitment.orders)
            for day, order, amount in commitment.future_orders:
                if day < horizon:
                    capital[day] += amount
                    orders[day].append(order)
            for flow in commitment.outputs:
                if flow.day >= horizon:
                    continue
                buckets = stock_sales if flow.from_stock else arrivals
                bucket = buckets[flow.day]
                bucket[flow.item] = bucket.get(flow.item, 0) + flow.units
            for flow in commitment.inputs:
                if flow.day < horizon:
                    bucket = needs[flow.day]
                    bucket[flow.item] = bucket.get(flow.item, 0) + flow.units
            if commitment.tile is not None:
                for operation in commitment.operations:
                    if operation.day < horizon:
                        work[operation.day].setdefault(
                            commitment.tile, [],
                        ).append(operation)

        workloads = tuple(
            self.workload(day, jobs) for day, jobs in enumerate(work)
        )
        return PortfolioBook(
            commitments,
            tuple(capital),
            tuple(tuple(day) for day in orders),
            tuple(arrivals),
            tuple(stock_sales),
            tuple(needs),
            tuple(work),
            workloads,
        )

    def liquidation_schedule(self, book, market_path):
        """Sell true surplus without crossing the shed boundary first."""
        schedule = []
        horizon = self.world.horizon
        occupancy_delta = [0 for _ in range(horizon + 1)]

        def occupy(first, last, units):
            if units <= 0 or first > last or first >= horizon:
                return
            first = max(0, first)
            last = min(horizon - 1, last)
            occupancy_delta[first] += units
            occupancy_delta[last + 1] -= units

        # Pending animals share today's physical shed but leave it when their
        # accepted PLACE operations execute. Seeds are stored separately.
        occupy(0, 0, sum(int(self.world.shed.get(name, 0)) for name in ANIMALS))

        for item in PRODUCTS:
            # Each unit carries the first day on which it can exist in shed
            # stock.  Current carried inventory lands only after today's
            # market; commitment outputs are already dated to their first
            # sellable day by the lifecycle model.
            supplies = [0 for _ in range(self.world.horizon)]
            supplies[0] = self.world.shed_stock[item]
            carried = self.world.stock[item] - self.world.shed_stock[item]
            if self.world.horizon > 1:
                supplies[1] += carried
            for day in range(self.world.horizon):
                supplies[day] += book.arrivals[day].get(item, 0)

            # Reserve the latest eligible supply for each chronological input;
            # earlier units remain more flexible for sale.  Unmatched demand
            # is procured by evaluate() on its due day.
            for due in range(self.world.horizon):
                demand = book.needs[due].get(item, 0)
                for first in range(due, -1, -1):
                    reserved = min(demand, supplies[first])
                    supplies[first] -= reserved
                    demand -= reserved
                    occupy(first, due, reserved)
                    if not demand:
                        break

            for first, units in enumerate(supplies):
                if not units:
                    continue
                day = max(
                    range(first, self.world.horizon),
                    key=lambda day: price(item, market_path[day][item]),
                )
                schedule.append([item, day, first, units])
                occupy(first, day, units)

        occupancy = []
        live = 0
        for day in range(horizon):
            live += occupancy_delta[day]
            occupancy.append(live)

        # A unit arriving on day d cannot be sold before that boundary. When
        # the boundary would overflow, advance the cheapest eligible sale to
        # some day < d. This is the storage dual of cash-prefix closure.
        feasible = True
        for boundary in range(horizon):
            overflow = occupancy[boundary] - SHED_CAPACITY
            while overflow > 0:
                choices = []
                for index, (item, old_day, first, units) in enumerate(schedule):
                    if units <= 0 or first >= boundary or old_day < boundary:
                        continue
                    early = max(
                        range(first, boundary),
                        key=lambda day: price(item, market_path[day][item]),
                    )
                    loss = (
                        price(item, market_path[old_day][item])
                        - price(item, market_path[early][item])
                    )
                    choices.append((
                        loss, -price(item, market_path[early][item]),
                        index, early,
                    ))
                if not choices:
                    feasible = False
                    break
                _, _, index, early = min(choices)
                item, old_day, first, units = schedule[index]
                moved = min(overflow, units)
                schedule[index][3] -= moved
                schedule.append([item, early, first, moved])
                for day in range(early + 1, old_day + 1):
                    occupancy[day] -= moved
                overflow -= moved
            if not feasible:
                break
        return [row for row in schedule if row[3] > 0], feasible

    @staticmethod
    def sales(schedule):
        grouped = {}
        for item, day, _, units in schedule:
            grouped[(item, day)] = grouped.get((item, day), 0) + units
        return tuple(
            sale_commitment(item, units, day)
            for (item, day), units in grouped.items()
        )

    def close(self, assets, exact_labor=True):
        """Close an asset portfolio with its best reachable stock-sale schedule."""
        book = self.compile(assets)
        assets_only = self._evaluate(book, exact_labor)
        schedule, capacity_feasible = self.liquidation_schedule(
            book, assets_only.market,
        )
        if not schedule:
            return replace(
                assets_only,
                feasible=assets_only.feasible and capacity_feasible,
            )
        result = self._evaluate(book, exact_labor, schedule)
        if not capacity_feasible:
            result = replace(result, feasible=False)

        # If a cash prefix binds, advance the cheapest units that can legally
        # arrive by that date.  Repeat because advancing sales changes prices.
        for _ in range(len(schedule) + 1):
            short = next((day for day, cash in enumerate(result.cash) if cash < 0), None)
            if short is None:
                return result
            options = []
            for index, (item, old_day, first, units) in enumerate(schedule):
                if old_day <= short or first > short:
                    continue
                new_day = max(
                    range(first, short + 1),
                    key=lambda day: price(item, result.market[day][item]),
                )
                old_price = price(item, result.market[old_day][item])
                new_price = price(item, result.market[new_day][item])
                loss = old_price - new_price
                options.append((
                    loss / max(1, new_price), loss, -new_price,
                    index, new_day, units,
                ))
            if not options:
                return result
            # Advancing one unit and replaying the full horizon made closure
            # quadratic once material accounting exposed hundreds of real
            # surplus units.  Advance the same cheapest-loss frontier until
            # the current cash deficit is covered, then replay once to reprice
            # the batch.  The next iteration still verifies the exact prefix.
            deficit = -result.cash[short]
            raised = 0
            for _, _, negative_price, index, new_day, units in sorted(options):
                price_now = -negative_price
                moved = min(units, math.ceil((deficit - raised) / price_now))
                if moved == units:
                    schedule[index][1] = new_day
                else:
                    item, old_day, first, _ = schedule[index]
                    schedule[index][3] -= moved
                    schedule.append([item, new_day, first, moved])
                raised += moved * price_now
                if raised >= deficit:
                    break
            result = self._evaluate(book, exact_labor, schedule)
            if not capacity_feasible:
                result = replace(result, feasible=False)
        return result

    def evaluate(self, commitments, exact_labor=True):
        return self._evaluate(self.compile(commitments), exact_labor)

    def _evaluate(self, book, exact_labor=True, liquidation=()):
        """Replay a compiled portfolio under one candidate liquidation policy."""
        world = self.world
        horizon = world.horizon
        market = dict(world.market)
        stock = dict(world.stock)
        cash = float(world.money)
        capital = book.capital
        daily_orders = [list(day) for day in book.orders]
        cash_path, market_path, hires_path = [], [], []
        rival_revenue = 0.0
        feasible = True

        arrivals = book.arrivals
        needs = book.needs
        work = book.work
        stock_sales = [dict(day) for day in book.stock_sales]
        for item, day, _, units in liquidation:
            bucket = stock_sales[day]
            bucket[item] = bucket.get(item, 0) + units

        for day in range(horizon):
            market_path.append(dict(market))
            revenue = 0
            for item in PRODUCTS:
                stock[item] = stock.get(item, 0) + arrivals[day].get(item, 0)
                sold_stock = stock_sales[day].get(item, 0)
                if sold_stock > stock.get(item, 0):
                    feasible = False
                if day == 0 and sold_stock > world.shed_stock[item]:
                    feasible = False
                stock[item] = max(0, stock.get(item, 0) - sold_stock)
                visible_rival = max(0, int(round(self.opponent[day][item])))
                own_value, rival_value, inventory = joint_sale_value(
                    item, market[item], sold_stock, visible_rival,
                )
                revenue += own_value
                rival_revenue += rival_value
                market[item] = inventory
                if sold_stock:
                    daily_orders[day].append(("SELL", item, sold_stock))

            input_cost = 0
            for item, units in needs[day].items():
                from_stock = min(units, stock.get(item, 0))
                stock[item] = stock.get(item, 0) - from_stock
                shortage = units - from_stock
                if shortage:
                    # In an otherwise unobserved simultaneous market, mirror
                    # demand is the neutral self-play prior.  Visible or
                    # learned rival demand can only make that pressure larger.
                    rival_units = max(
                        shortage,
                        int(round(self.opponent_inputs[day][item])),
                    )
                    own_cost, _, market[item] = joint_buy_cost(
                        item, market[item], shortage, rival_units,
                    )
                    input_cost += own_cost
                    daily_orders[day].append(("BUY_PRODUCT", item, shortage))

            if exact_labor:
                hires, _, labor_feasible = self.labor(
                    day, work[day], book.workloads[day],
                )
            else:
                hires, _, labor_feasible = self.labor_bound(
                    day, work[day], book.workloads[day],
                )
            already = int(world.farm.get("hires_today", 0)) if day == 0 else 0
            payroll = sum(fib(already + index) for index in range(hires))
            daily_orders[day].extend(("HIRE",) for _ in range(hires))

            cash += revenue - input_cost - payroll - capital[day]
            cash_path.append(cash)
            hires_path.append(hires)
            feasible &= cash >= 0 and labor_feasible
            feasible &= len(_group_orders(daily_orders[day])) <= _market_capacity(
                world, day,
            )

            for item in PRODUCTS:
                market[item] -= self.town[day][item]

        compiled = _group_orders(daily_orders[0])
        arrivals = sum(
            order[2] for order in compiled if order[0] in ("BUY_ANIMAL", "BUY_PRODUCT")
        )
        departures = sum(order[2] for order in compiled if order[0] == "SELL")
        feasible &= sum(world.shed.values()) - departures + arrivals <= SHED_CAPACITY
        commitments = book.commitments + self.sales(liquidation)
        return Projection(
            bool(feasible), cash, tuple(cash_path), tuple(market_path),
            tuple(hires_path), compiled, commitments, rival_revenue,
        )


# Portfolio -------------------------------------------------------------------


def existing_commitments(world, memory=None):
    commitments = []
    seeds = {name: int(world.seeds.get(name, 0)) for name in CROPS}
    for y, row in enumerate(world.tiles):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            position = (x, y)
            if tile.get("kind") == "PLANT":
                target = memory.targets.get(position) if memory is not None else None
                fertilized = bool(
                    isinstance(target, tuple) and len(target) > 1 and target[1]
                )
                commitment = crop_commitment(
                    world, position, tile["crop"], state=tile,
                    fertilized=fertilized,
                )
                commitment, seeds[tile["crop"]] = use_owned_seed(
                    commitment, seeds[tile["crop"]],
                )
            elif tile.get("animal"):
                commitment = animal_commitment(world, position, tile["animal"], state=tile)
            else:
                commitment = None
            if commitment is not None:
                commitments.append(commitment)
    return commitments


def _sites(world, quadrants):
    crop_sites, animal_sites = [], []
    for tile in TILES:
        if quadrant(tile) not in quadrants:
            continue
        state = world.tiles[tile[1]][tile[0]]
        if state is None or state == "LOCKED" or (isinstance(state, dict) and state.get("kind") == "WEED"):
            crop_sites.append(tile)
            animal_sites.append(tile)
        elif isinstance(state, dict) and state.get("kind") in ("COOP", "PASTURE") and not state.get("animal"):
            crop_sites.append(tile)
            animal_sites.append(tile)
    return crop_sites, animal_sites


def _candidate(
    world, tile, role, owned=False, land_cost=0, fertilized=False,
):
    if role in CROPS:
        capital = 0 if owned else CROPS[role].seed
        orders = () if owned else (("BUY_SEED", role, 1),)
        commitment = crop_commitment(
            world, tile, role, capital, orders, fertilized=fertilized,
        )
    else:
        capital = 0 if owned else ANIMALS[role].cost
        orders = () if owned else (("BUY_ANIMAL", role, 1),)
        commitment = animal_commitment(world, tile, role, capital, orders)
    if commitment is not None and land_cost:
        commitment = land_bundle(commitment, land_cost)
    return commitment


def _site_kind(world, tile):
    state = world.tiles[tile[1]][tile[0]]
    if not isinstance(state, dict):
        return state
    if state.get("kind") == "WEED":
        return "WEED"
    return state.get("kind")


def _frontier(
    world, crop_sites, animal_sites, roles, owned=False, land_cost=0,
    factory=None,
):
    """One undominated site per physical kind and role.

    Empty tiles with the same state produce the same asset.  More travel can
    never improve cash, output, or feasibility, so those copies are omitted.
    """
    factory = factory or (
        lambda tile, role, owned, land_cost, fertilized: _candidate(
            world, tile, role, owned, land_cost, fertilized,
        )
    )
    candidates = []
    for role in roles:
        sites = crop_sites if role in CROPS else animal_sites
        nearest = {}
        for tile in sites:
            kind = _site_kind(world, tile)
            key = kind if role in CROPS else (kind == ANIMALS[role].structure, kind)
            if key not in nearest or travel(tile) < travel(nearest[key]):
                nearest[key] = tile
        for tile in nearest.values():
            variants = (False, True) if role in CROPS else (False,)
            candidates.extend(
                factory(tile, role, owned, land_cost, fertilized)
                for fertilized in variants
            )
    return candidates


def _best_addition(ledger, accepted, candidates, baseline):
    frontier = []
    baseline_floor = min(baseline.cash)
    for commitment in candidates:
        if commitment is None:
            continue
        optimistic = ledger.close(
            accepted + [commitment], exact_labor=False,
        )
        gain = optimistic.utility - baseline.utility
        funding = max(0.0, baseline_floor - min(optimistic.cash))
        # A dollar consumed at the tightest cash prefix is not merely a dollar
        # of terminal cost: it also removes the option to fund the next
        # profitable commitment.  Preserve that option at par; the ledger's
        # own terminal gain still decides among equally funded choices.
        score = gain - funding
        if optimistic.feasible and gain > 0:
            frontier.append((score, gain, commitment))

    best = None
    for upper_score, upper_gain, commitment in sorted(
        frontier, key=lambda choice: choice[:2], reverse=True,
    ):
        if best is not None and (upper_score, upper_gain) <= best[:2]:
            break
        outcome = ledger.close(accepted + [commitment])
        gain = outcome.utility - baseline.utility
        funding = max(0.0, baseline_floor - min(outcome.cash))
        score = gain - funding
        choice = score, gain, commitment, outcome
        if outcome.feasible and gain > 0 and (
            best is None or choice[:2] > best[:2]
        ):
            best = choice
    return best


def _refill_below(world, ledger, accepted, outcome, capital_ceiling):
    """Replace one lumpy purchase with any better bundle of cheaper assets.

    Ordinary greedy addition cannot see that foregoing one animal may finance
    a whole crop portfolio.  Once that capital is released, however, the same
    ledger can price the replacement bundle directly.  Requiring every
    replacement asset to be strictly cheaper makes the exchange acyclic and
    keeps this a small economic neighborhood rather than a combinatorial
    search.
    """
    accepted = list(accepted)
    while True:
        occupied = {
            commitment.site for commitment in accepted
            if commitment.site is not None
        }
        crop_sites, animal_sites = _sites(world, set(world.unlocked))
        crop_sites = [tile for tile in crop_sites if tile not in occupied]
        animal_sites = [tile for tile in animal_sites if tile not in occupied]
        candidates = []
        for role in (*CROPS, *ANIMALS):
            for commitment in _frontier(
                world, crop_sites, animal_sites, (role,), owned=False,
                factory=ledger.candidate,
            ):
                if commitment is not None and commitment.capital < capital_ceiling:
                    candidates.append(commitment)
        best = _best_addition(ledger, accepted, candidates, outcome)
        if best is None:
            return accepted, outcome
        _, _, commitment, outcome = best
        accepted.append(commitment)


def _exchange_opening(world, ledger, accepted, outcome):
    """Climb from a greedy opening to its capital-exchange optimum.

    For each purchased animal type, remove its least valuable instance and let
    the ledger spend the released capital on a bundle of strictly cheaper
    assets.  A profitable exchange becomes the new portfolio and the process
    repeats.  This preserves the single economic objective while repairing
    the classic indivisible-knapsack failure of one-asset-at-a-time greed.
    """
    if world.day != 0 or existing_commitments(world):
        return list(accepted), outcome

    accepted = list(accepted)
    while True:
        improvement = None
        roles = {
            commitment.role for commitment in accepted
            if commitment.role in ANIMALS and commitment.capital > 0
        }
        for role in roles:
            removals = []
            for index, commitment in enumerate(accepted):
                if commitment.role != role or commitment.capital <= 0:
                    continue
                trial = accepted[:index] + accepted[index + 1:]
                trial_outcome = ledger.close(trial)
                removals.append((trial_outcome.utility, index, commitment, trial))
            if not removals:
                continue
            _, _, removed, trial = max(removals, key=lambda choice: choice[0])
            trial_outcome = ledger.close(trial)
            trial, trial_outcome = _refill_below(
                world, ledger, trial, trial_outcome, removed.capital,
            )
            if trial_outcome.utility <= outcome.utility:
                continue
            choice = trial_outcome.utility, trial, trial_outcome
            if improvement is None or choice[0] > improvement[0]:
                improvement = choice
        if improvement is None:
            return accepted, outcome
        _, accepted, outcome = improvement


def _land_package(
    world, ledger, accepted, outcome, quadrants, occupied, resources,
):
    """Price a fixed-cost quadrant by its conditional asset portfolio.

    Charging land to each first asset hides ordinary fixed-cost
    complementarity.  Represent access itself as a commitment, debit it once,
    then build the conditional portfolio under the real remaining cash and
    labor constraints.  Every prefix still passes the authoritative ledger.
    """
    land_index = len(quadrants) - 1
    if not (0 <= land_index < len(LAND_ORDER)):
        return None
    target = LAND_ORDER[land_index]
    crop_sites, animal_sites = _sites(world, set(quadrants) | {target})
    crop_sites = [
        tile for tile in crop_sites
        if quadrant(tile) == target and tile not in occupied
    ]
    animal_sites = [
        tile for tile in animal_sites
        if quadrant(tile) == target and tile not in occupied
    ]
    land = Commitment(
        f"land:{target}", "LAND", None,
        capital=LAND_PRICES[land_index], orders=(("BUY_LAND",),),
    )
    trial = list(accepted) + [land]
    trial_outcome = ledger.close(trial)
    if not trial_outcome.feasible:
        return None
    package = [land]
    trial_resources = dict(resources)
    trial_occupied = set(occupied)
    while True:
        candidates = []
        open_crops = [tile for tile in crop_sites if tile not in trial_occupied]
        open_animals = [tile for tile in animal_sites if tile not in trial_occupied]
        for role in (*CROPS, *ANIMALS):
            candidates.extend(_frontier(
                world, open_crops, open_animals, (role,),
                owned=trial_resources[role] > 0,
                factory=ledger.candidate,
            ))
        best = _best_addition(ledger, trial, candidates, trial_outcome)
        if best is None:
            break
        _, _, commitment, trial_outcome = best
        package.append(commitment)
        trial.append(commitment)
        trial_occupied.add(commitment.site)
        if not any(
            order[0] in ("BUY_SEED", "BUY_ANIMAL")
            for order in commitment.orders
        ):
            trial_resources[commitment.role] -= 1
    if len(package) == 1:
        return None
    if trial_outcome.utility <= outcome.utility:
        return None
    return package, trial_outcome


def portfolio(world, memory):
    ledger = Ledger(world, memory)
    accepted = existing_commitments(world, memory)
    outcome = ledger.close(accepted)
    occupied = {commitment.site for commitment in accepted if commitment.site is not None}
    resources = {**{name: int(world.seeds.get(name, 0)) for name in CROPS}, **world.pending}
    quadrants = list(world.unlocked)

    while True:
        crop_sites, animal_sites = _sites(world, set(quadrants))
        crop_sites = [tile for tile in crop_sites if tile not in occupied]
        animal_sites = [tile for tile in animal_sites if tile not in occupied]
        candidates = []
        for role in (*CROPS, *ANIMALS):
            candidates.extend(_frontier(
                world, crop_sites, animal_sites, (role,),
                owned=resources[role] > 0,
                factory=ledger.candidate,
            ))

        land_index = len(quadrants) - 1
        if 0 <= land_index < len(LAND_ORDER):
            next_quadrant = LAND_ORDER[land_index]
            land_crops, land_animals = _sites(world, set(quadrants) | {next_quadrant})
            land_crops = [
                tile for tile in land_crops
                if quadrant(tile) == next_quadrant and tile not in occupied
            ]
            land_animals = [
                tile for tile in land_animals
                if quadrant(tile) == next_quadrant and tile not in occupied
            ]
            for role in (*CROPS, *ANIMALS):
                candidates.extend(_frontier(
                    world, land_crops, land_animals, (role,),
                    owned=resources[role] > 0,
                    land_cost=LAND_PRICES[land_index],
                    factory=ledger.candidate,
                ))

        best = _best_addition(ledger, accepted, candidates, outcome)
        if best is None:
            packaged = _land_package(
                world, ledger, accepted, outcome,
                quadrants, occupied, resources,
            )
            if packaged is None:
                break
            additions, outcome = packaged
        else:
            _, _, commitment, outcome = best
            additions = [commitment]

        for commitment in additions:
            accepted.append(commitment)
            if commitment.site is not None:
                occupied.add(commitment.site)
            bought = any(
                order[0] in ("BUY_SEED", "BUY_ANIMAL")
                for order in commitment.orders
            )
            if commitment.role in resources and not bought:
                resources[commitment.role] -= 1
        if any(
            order[0] == "BUY_LAND"
            for commitment in additions for order in commitment.orders
        ):
            quadrants.append(LAND_ORDER[len(quadrants) - 1])

    accepted, outcome = _exchange_opening(world, ledger, accepted, outcome)
    return tuple(accepted), outcome


def materialize(world, memory):
    """Rebuild the day's accepted commitments from the live engine state."""
    resources = {**{name: int(world.seeds.get(name, 0)) for name in CROPS}, **world.pending}
    commitments = []
    for tile, target in memory.targets.items():
        role, fertilized = (
            target if isinstance(target, tuple) else (target, False)
        )
        state = world.tiles[tile[1]][tile[0]]
        if role in CROPS and isinstance(state, dict) and state.get("crop") == role:
            commitment = crop_commitment(
                world, tile, role, state=state, fertilized=fertilized,
            )
            commitment, resources[role] = use_owned_seed(
                commitment, resources[role],
            )
        elif role in ANIMALS and isinstance(state, dict) and state.get("animal") == role:
            commitment = animal_commitment(world, tile, role, state=state)
        else:
            owned = resources[role] > 0
            commitment = _candidate(
                world, tile, role, owned=owned, fertilized=fertilized,
            )
            if owned and commitment is not None:
                resources[role] -= 1
        if commitment is not None:
            commitments.append(commitment)

    target_quadrants = {quadrant(tile) for tile in memory.targets}
    highest_land = max(
        (index for index, name in enumerate(LAND_ORDER) if name in target_quadrants),
        default=-1,
    )
    missing_land = [
        index for index in range(highest_land + 1)
        if LAND_ORDER[index] not in world.unlocked
    ]
    if missing_land and commitments:
        # Land unlocks in fixed engine order, so one earliest locked target can
        # carry every prerequisite order without creating another plan object.
        index = next(
            i for i, commitment in enumerate(commitments)
            if commitment.site and quadrant(commitment.site) not in world.unlocked
        )
        commitment = commitments[index]
        commitments[index] = replace(
            commitment,
            capital=commitment.capital + sum(LAND_PRICES[i] for i in missing_land),
            orders=tuple(("BUY_LAND",) for _ in missing_land) + commitment.orders,
        )
    return tuple(commitments), Ledger(world, memory).close(commitments)


# Execution -------------------------------------------------------------------


@dataclass(frozen=True)
class Task:
    tile: tuple
    action: tuple
    value: float
    sequence: int
    need: str | None = None
    bulk: int = 1
    produces: tuple = ()
    uid: int = -1


def tasks_from(projection):
    tasks = []
    for commitment in projection.commitments:
        sequence = 0
        for operation in commitment.operations:
            if operation.day != 0 or commitment.tile is None:
                continue
            value = sum(
                projection.worth(0, item, units) for item, units in operation.protects
            )
            tasks.append(Task(
                commitment.tile, operation.action, max(1.0, value), sequence,
                operation.need, operation.bulk,
                operation.protects if operation.action[0] in (
                    "HARVEST", "COLLECT_FERTILIZER",
                ) else (), len(tasks),
            ))
            sequence += 1
    return tasks


def _task_legal(world, task):
    """Whether this planned operation can change the live engine state now."""
    tile = world.tiles[task.tile[1]][task.tile[0]]
    op = task.action[0]
    if op == "DIG":
        return tile is not None and not (
            isinstance(tile, dict) and tile.get("animal")
        )
    if op in ("BUILD_COOP", "BUILD_PASTURE"):
        return tile is None
    if op == "PLACE":
        role = task.action[1]
        return (
            role in ANIMALS and isinstance(tile, dict)
            and tile.get("kind") == ANIMALS[role].structure
            and not tile.get("animal")
        )
    if op == "PLANT":
        return tile is None
    if op == "WATER":
        return (
            isinstance(tile, dict) and tile.get("kind") == "PLANT"
            and not tile.get("watered_today")
        )
    if op == "FERTILIZE":
        return isinstance(tile, dict) and tile.get("kind") == "PLANT"
    if op == "HARVEST":
        if not isinstance(tile, dict) or int(tile.get("yield_units", 0)) <= 0:
            return False
        if tile.get("kind") != "PLANT":
            return bool(tile.get("animal"))
        crop = CROPS[tile["crop"]]
        return world.day - int(tile["planted_day"]) >= crop.first
    if op == "FEED":
        return bool(
            isinstance(tile, dict) and tile.get("animal")
            and not tile.get("fed_today")
        )
    if op == "CARE":
        return bool(
            isinstance(tile, dict) and tile.get("animal")
            and not tile.get("cared_today")
        )
    if op == "COLLECT_FERTILIZER":
        return bool(
            isinstance(tile, dict) and tile.get("animal")
            and tile.get("fertilizer_available")
        )
    return True


def _jobs(tasks):
    grouped = {}
    for task in tasks:
        grouped.setdefault(task.tile, []).append(task)
    return tuple(
        (tile, tuple(sorted(bundle, key=lambda task: task.sequence)))
        for tile, bundle in grouped.items()
    )


def _routes(world, job_map, projection, memory):
    """Materialize the ledger's day crew as stable actor routes."""
    live_tiles = set(job_map)
    routes = {
        actor: [tile for tile in route if tile in live_tiles]
        for actor, route in memory.routes.items()
    }
    assigned = {tile for route in routes.values() for tile in route}
    missing = live_tiles - assigned
    planned_hires = projection.hires[0] if projection.hires else 0
    if memory.crew_target is not None:
        planned_hires = min(
            planned_hires,
            max(0, memory.crew_target - len(world.actors)),
        )
    # Only ten new workers can be bought this turn, but a day can stage more
    # hires over later turns and existing workers remain available throughout.
    crew = len(world.actors) + min(MAX_ORDERS, planned_hires)
    if missing or planned_hires:
        existing = tuple(world.actors)
        roots = existing + _spawned(existing, max(0, crew - len(existing)))
        inventories = tuple(world.inventories) + tuple({} for _ in range(max(0, crew - len(existing))))
        turns = max(1, DAY_TURNS - world.hour)
        capacities = tuple(
            turns if actor < len(existing) else max(0, turns - 1)
            for actor in range(crew)
        )
        planned, _ = _partition(
            job_map, roots, inventories, capacities,
            world.shed_tiles,
        )
        routes = {actor: list(route) for actor, route in enumerate(planned)}
    memory.routes = routes
    return routes


def dispatch(world, tasks, projection=None, memory=None):
    projection = projection or Projection(True, 0, (), (), (0,), [], ())
    memory = memory or Memory()
    jobs = _jobs(tasks)
    job_map = dict(jobs)
    routes = _routes(world, job_map, projection, memory)
    actions = [["PASS"] for _ in world.actors]
    claimed = {}

    # A route is one promise: load its inputs, then visit its tiles in order.
    for actor in range(len(world.actors)):
        route = routes.get(actor, [])
        if not route:
            inventory = world.inventories[actor]
            carried = sum(int(units) for units in inventory.values())
            room = SHED_CAPACITY - sum(int(units) for units in world.shed.values())
            if carried and carried <= room and world.shed_tiles:
                origin = world.actors[actor]
                depot = min(world.shed_tiles, key=lambda tile: distance(origin, tile))
                actions[actor] = (
                    ["DROP"] if origin == depot
                    else [step_toward(origin, depot)]
                )
            continue
        origin = world.actors[actor]
        inventory = world.inventories[actor]
        required, first, priority = {}, {}, {}
        for route_index, tile in enumerate(route):
            for task in job_map[tile]:
                if not task.need or task.need.startswith("SEED:"):
                    continue
                required[task.need] = required.get(task.need, 0) + task.bulk
                first[task.need] = min(
                    first.get(task.need, (route_index, task.sequence)),
                    (route_index, task.sequence),
                )
                priority[task.need] = max(priority.get(task.need, 0), task.value)
        missing = [
            resource for resource, units in required.items()
            if inventory.get(resource, 0) < units
            and world.shed.get(resource, 0) > claimed.get(resource, 0)
        ]
        if missing and world.shed_tiles:
            resource = min(missing, key=lambda item: (first[item], -priority[item], item))
            target = route[0]
            depot = min(
                world.shed_tiles,
                key=lambda tile: distance(origin, tile) + distance(tile, target),
            )
            available = world.shed.get(resource, 0) - claimed.get(resource, 0)
            take = min(available, required[resource] - inventory.get(resource, 0))
            claimed[resource] = claimed.get(resource, 0) + take
            if origin == depot:
                actions[actor] = ["PICKUP", resource, take]
            else:
                actions[actor] = [step_toward(origin, depot)]
            continue

        # Missing optional inputs reduce output; they must not freeze the
        # route.  Only PLANT and PLACE create the entity required by later
        # operations at that site, so those two are dependency barriers.
        selected = None
        for tile in route:
            for task in job_map[tile]:
                resource = task.need
                if resource and resource.startswith("SEED:"):
                    available = (
                        world.seeds.get(resource[5:], 0)
                        - claimed.get(resource, 0)
                    )
                    ready = available > 0
                elif resource:
                    ready = inventory.get(resource, 0) >= task.bulk
                else:
                    ready = True
                legal = _task_legal(world, task)
                ready &= legal
                if ready:
                    selected = tile, task
                    break
                if not legal or task.action[0] in ("PLANT", "PLACE"):
                    break
            if selected is not None:
                break
        if selected is None:
            continue

        tile, task = selected
        resource = task.need
        if (
            resource and resource.startswith("SEED:")
            and origin == tile
        ):
            claimed[resource] = claimed.get(resource, 0) + 1

        if origin != tile:
            actions[actor] = [step_toward(origin, tile)]
        else:
            actions[actor] = list(task.action)
            if task.uid >= 0:
                memory.completed_tasks.add(task.uid)
    return actions


def _market_forecast(world, memory, item):
    """Market inventory before each remaining turn, excluding our own sales."""
    turns = max(1, SEASON_DAYS * DAY_TURNS - world.step)
    inventory = float(world.market[item])
    visible = _opponent_schedule(world, memory)
    visible_daily = sum(day[item] for day in visible) / max(1, world.horizon)
    opponent = max(
        visible_daily, memory.opponent_daily[item],
    ) / DAY_TURNS
    path = []
    for offset in range(turns):
        path.append(inventory)
        inventory += opponent
        inventory -= town_consumption(item, world.shops, world.step + offset)
    return path


def _order_cost(world, orders):
    """Cash required by this turn's non-sale orders in their engine order."""
    cost = 0
    hires = int(world.farm.get("hires_today", 0))
    land = len(world.unlocked) - 1
    market = dict(world.market)
    for order in orders:
        op = order[0]
        if op == "HIRE":
            cost += fib(hires)
            hires += 1
        elif op == "BUY_LAND" and land < len(LAND_PRICES):
            cost += LAND_PRICES[land]
            land += 1
        elif op == "BUY_SEED":
            cost += CROPS[order[1]].seed * int(order[2])
        elif op == "BUY_ANIMAL":
            cost += ANIMALS[order[1]].cost * int(order[2])
        elif op == "BUY_PRODUCT":
            units = int(order[2])
            cost += buy_cost(order[1], market[order[1]], units)
            market[order[1]] -= units
    return cost


def _reserved_shed(world, commitments):
    """Current shed units that dated future supply cannot replace."""
    reserved = {item: 0 for item in PRODUCTS}
    for item in PRODUCTS:
        # Tie order deliberately spends future/carried supply before current
        # shed stock, freeing every safely replaceable shed unit for sale.
        supplies = [(0, 0)] * int(world.shed.get(item, 0))
        supplies.extend(
            [(0, 1)] * sum(
                int(inventory.get(item, 0))
                for inventory in world.inventories
            )
        )
        demands = []
        for commitment in commitments:
            for flow in commitment.outputs:
                if flow.item == item and not flow.from_stock:
                    supplies.extend([(flow.day, 2)] * flow.units)
            for flow in commitment.inputs:
                if flow.item == item:
                    demands.extend([flow.day] * flow.units)
        supplies.sort()
        for due in sorted(demands):
            index = bisect_right(supplies, (due, 99)) - 1
            if index < 0:
                continue
            _, source = supplies.pop(index)
            if source == 0:
                reserved[item] += 1
    return reserved


def market_orders(world, memory, projection, tasks):
    """Replace dated liquidation guesses with a live reservation-price auction."""
    fixed = [
        order for order in projection.orders
        if order[0] not in ("SELL", "HIRE")
    ]
    planned_hires = sum(order[0] == "HIRE" for order in projection.orders)
    if memory.crew_target is not None:
        planned_hires = min(
            planned_hires,
            max(0, memory.crew_target - len(world.actors)),
        )
    fixed.extend(["HIRE"] for _ in range(planned_hires))

    reserved = _reserved_shed(world, projection.commitments)

    available = {
        item: max(0, int(world.shed.get(item, 0)) - reserved.get(item, 0))
        for item in PRODUCTS
    }
    forecasts = {
        item: _market_forecast(world, memory, item)
        for item, units in available.items() if units
    }
    curves = {}
    for item, units in available.items():
        if not units:
            continue
        path = forecasts[item]
        curve = []
        for unit in range(units):
            now = price(item, world.market[item] + unit)
            future = max(
                price(item, int(inventory) + unit)
                for inventory in path[1:]
            ) if len(path) > 1 else 0
            curve.append((future - now, now))
        curves[item] = curve

    # A day-level plan can contain more orders than one turn.  Compile only a
    # legal prefix, and reserve sale slots whenever that prefix needs funding
    # or shed room.  Previously ten fixed orders crowded out their own funding
    # sale, so the same unaffordable hires were retried while the farm died.
    selected_fixed = fixed[:MAX_ORDERS]
    sold = {}
    while True:
        sale_cash = sum(
            sum(now for _, now in curves[item][:units])
            for item, units in sold.items()
        )
        incoming = sum(
            int(order[2]) for order in selected_fixed
            if order[0] in ("BUY_ANIMAL", "BUY_PRODUCT")
        )
        cash_need = max(
            0, math.ceil(_order_cost(world, selected_fixed) - world.money - sale_cash),
        )
        room_need = max(
            0,
            sum(world.stock.values()) + incoming
            - SHED_CAPACITY - sum(sold.values()),
        )
        if not cash_need and not room_need:
            break

        slots_full = len(selected_fixed) + len(sold) >= MAX_ORDERS
        frontier = []
        for item, curve in curves.items():
            unit = sold.get(item, 0)
            if unit >= len(curve) or (slots_full and item not in sold):
                continue
            regret, now = curve[unit]
            frontier.append((regret / max(1, now), regret, -now, item))
        if not frontier:
            if selected_fixed:
                selected_fixed.pop()
                continue
            break
        _, _, _, item = min(frontier)
        sold[item] = sold.get(item, 0) + 1

    # The closed ledger owns discretionary liquidation timing. Runtime can add
    # sales for immediate funding and storage safety, but does not replace the
    # policy that priced the accepted portfolio.
    planned = {}
    for order in projection.orders:
        if order[0] != "SELL":
            continue
        item, units = order[1], int(order[2])
        planned[item] = min(
            available.get(item, 0), planned.get(item, 0) + units,
        )
    slots = max(0, MAX_ORDERS - len(selected_fixed) - len(sold))
    selected = sorted(
        (item for item, units in planned.items() if units),
        key=lambda item: (
            -sale_value(item, world.market[item], planned[item]), item,
        ),
    )[:slots]
    for item in selected:
        sold[item] = max(sold.get(item, 0), planned[item])

    # Harvests live in actor inventories until the boundary, so they are not
    # a prerequisite for this turn's crew or purchases.  Use only remaining
    # order slots to clear their eventual shed room; never evict the workers
    # needed to perform the harvest itself.
    future_room = max(
        0,
        sum(world.stock.values()) + incoming
        + sum(units for task in tasks for _, units in task.produces)
        - SHED_CAPACITY - sum(sold.values()),
    )
    while future_room > 0:
        slots_full = len(selected_fixed) + len(sold) >= MAX_ORDERS
        frontier = []
        for item, curve in curves.items():
            unit = sold.get(item, 0)
            if unit >= len(curve) or (slots_full and item not in sold):
                continue
            regret, now = curve[unit]
            frontier.append((regret / max(1, now), regret, -now, item))
        if not frontier:
            break
        _, _, _, item = min(frontier)
        sold[item] = sold.get(item, 0) + 1
        future_room -= 1

    # Nothing can be carried beyond the season.
    # The interpreter marks DONE after processing step 718; hour 23 is a
    # recorded terminal observation, not an actionable turn.
    if world.step >= SEASON_DAYS * DAY_TURNS - 2:
        final_items = sorted(
            (item for item, units in available.items() if units),
            key=lambda item: -sale_value(item, world.market[item], available[item]),
        )[:slots]
        sold = {item: available[item] for item in final_items}

    sales = [["SELL", item, units] for item, units in sold.items() if units > 0]
    return sales + selected_fixed


def agent(observation, configuration=None):
    world = World.read(observation)
    memory = MEMORY[world.player]
    if world.step == 0 or world.step <= memory.last_step:
        memory.reset()
    memory.last_step = world.step
    observe_market(memory, world)

    if memory.planned_day != world.day:
        # Routes are an execution schedule for one day.  Letting yesterday's
        # actor indices enter today's labor oracle can preserve a large stale
        # crew even when today's work is smaller (or empty); on the final day
        # this previously hired fifteen hands for no field work at all.
        memory.routes = {}
        memory.crew_target = None
        memory.day_tasks = ()
        memory.completed_tasks = set()
        commitments, projection = portfolio(world, memory)
        memory.targets = {
            commitment.site: (commitment.role, commitment.fertilized)
            for commitment in commitments if commitment.site is not None
        }
        memory.planned_day = world.day
        memory.crew_target = len(world.actors) + min(
            _market_capacity(world, 0),
            projection.hires[0] if projection.hires else 0,
        )
        memory.day_tasks = tuple(tasks_from(projection))
    else:
        _, projection = materialize(world, memory)
    tasks = [
        task for task in memory.day_tasks
        if task.uid not in memory.completed_tasks
    ]
    actions = dispatch(world, tasks, projection, memory)
    orders = market_orders(world, memory, projection, tasks)
    flow = {item: 0 for item in PRODUCTS}
    for order in orders:
        if order[0] == "SELL":
            flow[order[1]] += order[2]
        elif order[0] == "BUY_PRODUCT":
            flow[order[1]] -= order[2]
    memory.own_flow = flow
    return {
        "farmer": actions[0] if actions else ["PASS"],
        "hands": actions[1:1 + len(world.farm.get("hands", []))],
        "market": orders,
    }