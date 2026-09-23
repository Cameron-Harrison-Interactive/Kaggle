"""
R34 (09-13, user design - OPENING REDESIGN, whole-commit branch):
astra_live20_1 = live20 [9f2d6f63] with the user's plan-1 opening:
(1) d4 row-wheat sell -> SECOND row cycle (4 tiles) + ONE cow, no R30
    d5-9 burst - steady 1-2 animals/day toward the north cap 18;
(2) NE-FIRST: the d4 wheat money opens NE the day it clears cost+fill
    (bar $1,450 vs the old $2,350 - no $900 animal pre-budget for NE);
(3) NE crop tiles grow the melon/wheat/carrot cash mix d4-10 (no strb
    seeds before d10 - mix first, factory second);
(4) strb factory LATE and BIGGER: target 38 (peace), window extended
    d12 -> d15 (engine: 4 productions at d10/12/14/16 after planting,
    so d13 = last 4-tick day, d15 = 3 ticks at peak prices);
(5) SE opens from d12 (herd 8+ measured pace), gets a 3rd worker
    ("keep everything full always"; crew stays 14: NW4/NE5/SW2/SE3).
Test protocol (user): live20_1 vs live20 head-to-head + solo gates.

Kaggressure: live-route staged-growth agent.
Standard library only.

Experimental, unbenchmarked candidate:
- 2-goose opening
- target herd: 6 cows, 6 sheep, 8 geese
- hourly shed sales
- live routing with shared resource reservations

- no blind daily action tape

Uses the documented default 10x10 / 24-turn / 30-day game.

R51a (09-14, ladder replay autopsy): FINAL LIQUIDATION only. The 27
pulled ladder episodes end with wool 10 + egg 8 + fert 4 collected into
the shed at d29 h22-23 and never sold (~$2-3k/game, 26/27 games) - they
were reserved for pickup jobs. On the last two days all shed
reservations are zeroed except d28 feed wheat.
"""

import math
from collections import Counter

# ---------- Game tables ----------

CROPS = {
    # seed cost, productive horizon, expected unfertilized units, yield cap
    "WHEAT": (10, 4, 4, 6),
    "CARROT": (20, 3, 3, 4),
    "TOMATO": (50, 11, 4, 4),
    "STRAWBERRY": (100, 16, 4, 4),
    "MELON": (80, 10, 6, 6),
}

ANIMALS = {
    # purchase cost, structure, product, first production, interval, held cap
    "GOOSE": (300, "COOP", "EGG", 4, 1, 4),
    "COW": (400, "PASTURE", "MILK", 8, 2, 6),
    "SHEEP": (500, "PASTURE", "WOOL", 6, 3, 6),
}

# base, throughput, scarcity shape/target, glut shape/target
MARKET = {
    "WHEAT": (25, 400, "sqrt", .80, "log", .20),
    "CARROT": (35, 450, "hinge", 1.00, "sqrt", .70),
    "TOMATO": (60, 200, "hinge", .40, "sqrt", .60),
    "STRAWBERRY": (120, 100, "sqrt", .70, "linear", 1.60),
    "MELON": (250, 300, "log", .20, "sq", 3.60),
    "EGG": (50, 332, "hinge", .40, "log", .20),
    "MILK": (160, 122, "sqrt", .60, "linear", 1.60),
    "WOOL": (200, 105, "log", .20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", .40, "linear", .40),
}

SHOPS = {
    "BAKERY": {"EGG": 1, "WHEAT": 1},
    "PIZZA_SHOP": {"MILK": 1, "TOMATO": 1, "WHEAT": 1},
    "BRUNCH_SPOT": {"EGG": 1, "WHEAT": 1, "STRAWBERRY": 1},
    "YARN_STORE": {"WOOL": 2},
    "ICE_CREAM_SHOP": {"STRAWBERRY": 1, "MILK": 1, "WHEAT": 1},
    "PET_CAFE": {"CARROT": 2},
    "SMOOTHIE_SHOP": {"STRAWBERRY": 1, "MILK": 1},
    "FARMERS_MARKET": {
        "WHEAT": 1, "CARROT": 1, "TOMATO": 1, "STRAWBERRY": 1
    },
}

QUOTAS = {
    "NW": {"COW": 2, "SHEEP": 1, "GOOSE": 2},
    "NE": {"COW": 2, "SHEEP": 2, "GOOSE": 1},
    "SW": {"COW": 1, "SHEEP": 2, "GOOSE": 2},
    "SE": {"COW": 1, "SHEEP": 1, "GOOSE": 3},
}

SHED = ((4, 4), (5, 4), (4, 5), (5, 5))
# R109 KEEP on 82. New land is berries only if straw>=160 (140
# planted berries into $149 and we sat $361 d12 vs 65's wheat
# cash). vs-pass = 82. H2H vs 41 12-0, vs 78 12-0, vs 65 10-2
# (82 was 8-4). NEXT SUBMIT.
# R90 KEEP. Shrink to 8-16 vs 30+ berries ONLY if straw quote <$160.
# vs-pass = 61 (129077). H2H vs 41 10-2 median +8446 (61 was 4-8).
# R89 KEEP on R86. vs-pass 6-seed AVG 129077 (+9882 vs 58 119195).
# H2H vs 58 10-2 median +4595. (1) opp_strb>=30 stay 8-16, do not
# match 33/45. (2) fill SW the day it opens (d12h23 21 plants vs 8).
# (3) NE d7 bar is land+$150 (fill-seed pre-budget dropped). (4) yarn
# or milk -> 2 geese, keep cow/sheep 6+1 SW. North 6 + 3 pads stay.
# Do not edit 41/51. Do not restack R87/R88.
# R86 town routes on R84 chassis. North herd + 3 SW pads unchanged.
# Every shop type has a routine. Sell on shop-consume hours (0/4/8/
# 12/16/20) so the town eats what we just sold. Berry shops raise
# the factory (ladder 140k bots run 33 with 0 weeds; v32 33-berry
# is 676, v33 8-berry is 610). Do not overwrite 41/51.
SCATTER_PADS = (
    (3, 5), (2, 5), (4, 6),
    (6, 5), (7, 6), (8, 5),
)
FIB = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610)
STATE = {}

# ---------- Geometry and prices ----------

def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def shed_near(p):
    return min(SHED, key=lambda s: (distance(p, s), s))


def quadrant(p):
    return ("N" if p[1] < 5 else "S") + ("W" if p[0] < 5 else "E")


def animal_line(p):
    # TWO north animal rows (user directive): NW/NE host the herd in
    # rows y=3 and y=4 (up to ~9-10 spots, capped at 8/quad by the
    # planner). South quads have no animals - their edge row y=5 is
    # ordinary crop ground.
    return p[1] in (3, 4)


def move(p, goal):
    dx, dy = goal[0] - p[0], goal[1] - p[1]
    if abs(dx) >= abs(dy) and dx:
        return ["EAST" if dx > 0 else "WEST"]
    if dy:
        return ["SOUTH" if dy > 0 else "NORTH"]
    return ["PASS"]


def shape(name, x, throughput):
    x = max(0.0, x)
    if name == "sqrt":
        return math.sqrt(x)
    if name == "sq":
        return x * x
    if name == "log":
        return math.log1p(x)
    if name == "log10":
        return math.log10(1 + x)
    if name == "hinge":
        u = x / throughput
        return u + 8 * max(0.0, u - 1) ** 2
    return x


def price(item, inventory, overrides=None):
    b, t, below, bt, above, at = MARKET[item]
    o = (overrides or {}).get(item, {})
    b = o.get("base", b)
    t = o.get("T", t)
    anchor = o.get("I0", 10000)
    below = o.get("below_func", below)
    above = o.get("above_func", above)
    bt = o.get("below_target", bt)
    at = o.get("above_target", at)
    scarce = inventory < anchor
    f, target = (below, bt) if scarce else (above, at)
    change = target * b * shape(f, abs(inventory - anchor), t)
    change /= max(1e-12, shape(f, t, t))
    return max(1, int(round(b + change if scarce else b - change)))


def sale_value(item, inventory, quantity, overrides=None):
    value = 0
    for _ in range(max(0, int(quantity))):
        p = price(item, inventory, overrides)
        value += p
        # Documented price-floor rule: floor sales do not increase inventory.
        if p > 1:
            inventory += 1
    return value


def stock_size(inventory):
    return sum(max(0, int(v)) for v in inventory.values())


# ---------- Agent ----------

def agent(obs, configuration=None):
    cfg = configuration or {}
    seat = int(obs["player"])
    day, hour = int(obs["day"]), int(obs["hour"])

    if day == 0 and hour == 0:
        STATE[seat] = {"goals": {}, "plans": {}, "ptrs": {},
                    "plan_day": -1, "planned_seeds": -1, "plan_workers": 0, "crew": 1}
    state = STATE.setdefault(seat, {"goals": {}, "plans": {}, "ptrs": {},
                                     "plan_day": -1, "planned_seeds": -1,
                                     "plan_workers": 0, "crew": 1})
    old_goals = state["goals"]

    farm = obs["farms"][seat]
    opponent = obs["farms"][1 - seat]
    # War mode (TRACE-06 + mirror lesson): vs a strb-heavy opponent
    # (standing >= 35, e.g. Tetsu's ~35-40), escalate strb target 33 -> 45
    # (volume = denial ammunition: our extra units crash the shared strb
    # market they depend on; measured -79k -> -57k). Vs balanced opponents
    # (e.g. our own 33-standing line) stay at 33: in a mutual-dump market
    # the LOWER-volume clone takes less inframarginal price damage
    # (measured: fixed-45 loses 0-20 to the 33-build). Latch: once the
    # opponent crosses the threshold, war stays on for the season.
    # R21 (user): full opponent crop census, read live every turn -
    # the mirror layer works vs ANY ladder line (10+ metas, not just
    # tetsu): we match the crops worth denying (see crash math below)
    # and profit from what they DON'T stand (animals + the open crops).
    opp_crops = Counter()
    for row in opponent.get("tiles", []):
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                opp_crops[t.get("crop")] += 1
    opp_strb = opp_crops.get("STRAWBERRY", 0)
    # R38 (user): the opponent's HERD census - "by day 15 read their
    # animals; whatever they are weak on, we add a row of that in SW."
    opp_animals = Counter()
    for row in opponent.get("tiles", []):
        for t in row:
            if isinstance(t, dict) and t.get("animal"):
                opp_animals[t["animal"]] += 1
    if opp_strb >= 35:
        state["war"] = True
    war = bool(state.get("war"))
    # R20 (user): MATCH the opponent's strawberry volume - denial
    # parity: every unit they sell, we sell one too, so the price they
    # realize stays low ("they still get less"), and the ground beyond
    # the match opens for melons (the top-meta shape: melons still
    # worth ~150 at the end). PEACE PATH (opp < 35): target =
    # min(45, max(33, opp_strb)) - floor 33 = the proven economy (B1
    # measured floor-24 at -8..-10k strb revenue). WAR PATH (opp >= 35,
    # e.g. Tetsu's pure strb factory): keep the measured 45-tile
    # escalation - vs a strb-only build, 15 extra denial tiles beat
    # the melon wave by ~$12k (B5 vs baseline: -97.9k vs -85.7k
    # median; the user's call that strb-heavy is now mid-ladder means
    # the peace path is what plays the top meta).
    # R34: strb target now computed AFTER quoted() (below) - the bigger
    # late factory is gated on the LIVE strb quote (shallow-demand seeds
    # crash: 777 ran 121u at $201 avg vs 42's $280).
    strb_target = 33
    # R21 (user): the mirror generalizes to MELON - the #2 dump crop.
    # Crash math: melon glut is squared (+100 net units ~= $150, +180
    # ~= floor) - when a melon-first line out-stands our country, match
    # their standing (deny their dump; our fert'd ticks halve our
    # cost/unit so we win the crashed market on unit economics). When
    # they run none (or few), melon country stands at 16 = the profit
    # leg. Cap 24 = seed/labor sanity on a nuked market. Wheat is NOT
    # mirrored (log curve - matching buys ~no denial); carrot mild,
    # left to argmax; tomato forbidden (standing order); animals are
    # the profit leg, never mirrored.
    melon_cap = 24 if war else min(24, max(16, opp_crops.get("MELON", 0)))
    # R23 (user doctrine): match their crops - ALL of them. Wheat and
    # carrot arms join strb/melon; each engages ONLY vs a committed
    # line of that crop (wheat >= 25 standing, carrot >= 20) and stays
    # asleep otherwise (solo: byte-identical). Tomato stays forbidden
    # (standing order); animals are NEVER mirrored - they are the
    # profit leg ("our animals and other crops profit over them").
    wheat_target = (min(40, opp_crops.get("WHEAT", 0))
                    if opp_crops.get("WHEAT", 0) >= 25 else 0)
    carrot_target = (min(24, opp_crops.get("CARROT", 0))
                     if opp_crops.get("CARROT", 0) >= 20 else 0)
    private = obs.get("private", {})
    grid = farm["tiles"]
    owned = set(farm.get("unlocked_quadrants", ["NW"]))
    money = float(farm.get("money", 0))
    shed = Counter(private.get("shed", {}))
    seeds = Counter(private.get("seeds", {}))
    inventories = list(private.get("inventories", [{}]))
    positions = [tuple(farm["farmer"])]
    positions += [tuple(p) for p in farm.get("hands", [])]
    while len(inventories) < len(positions):
        inventories.append({})

    market = obs.get("market", {})
    prices = market.get("prices", {})
    market_inventory = market.get("inventory", {})
    # R40 (tape: melons hostage vs RAHMAN): track market inventory
    # drift - the floor may hold stock ONLY while withholding has
    # power (still scarce-ish vs the 10000 anchor, or actively
    # draining). Once the glut is banked (inv >= anchor, not
    # draining), the recovery never comes - dump for salvage.
    _inv_hist = state.setdefault("inv_hist", {})
    _drain = {
        k: market_inventory.get(k, 10000) < _inv_hist.get(k, 10000)
        for k in MARKET}
    for k in MARKET:
        _inv_hist[k] = market_inventory.get(k, 10000)
    overrides = cfg.get("marketParams", {}) or {}
    turns = int(cfg.get("turnsPerDay", 24))
    episodes = int(cfg.get("episodeSteps", 720))
    total_days = max(1, math.ceil(episodes / turns))
    final_day = day >= total_days - 1
    remaining = turns - hour
    step = day * turns + hour
    final_step = episodes - 1

    def quoted(item):
        return prices.get(
            item,
            price(item, market_inventory.get(item, 10000), overrides)
        )

    # R86: every shop, every unlock day (3,6,9,12,15,18,21,24), every
    # sell tick (hour 0/4/8/12/16/20 = shops consume AFTER our SELL
    # this step; hour 0 also town-center). Drawn with replacement,
    # cap 8. We cannot see tomorrow's draw.
    #   BAKERY         egg, wheat
    #   PIZZA_SHOP     milk, tomato, wheat
    #   BRUNCH_SPOT    egg, wheat, strawberry
    #   YARN_STORE     wool x2
    #   ICE_CREAM_SHOP strawberry, milk, wheat
    #   PET_CAFE       carrot x2
    #   SMOOTHIE_SHOP  strawberry, milk
    #   FARMERS_MARKET wheat, carrot, tomato, strawberry
    _shops = list((obs.get("town", {}) or {}).get("unlocked_shops", []))
    n_bakery = _shops.count("BAKERY")
    n_pizza = _shops.count("PIZZA_SHOP")
    n_brunch = _shops.count("BRUNCH_SPOT")
    n_yarn = _shops.count("YARN_STORE")
    n_ice = _shops.count("ICE_CREAM_SHOP")
    n_pet = _shops.count("PET_CAFE")
    n_smoothie = _shops.count("SMOOTHIE_SHOP")
    n_farmers = _shops.count("FARMERS_MARKET")
    n_strb_shop = n_brunch + n_ice + n_smoothie + n_farmers
    n_tom_shop = n_pizza + n_farmers
    n_carrot_shop = n_pet + n_farmers
    n_milk_shop = n_pizza + n_ice + n_smoothie
    n_egg_shop = n_bakery + n_brunch
    n_wheat_shop = n_bakery + n_pizza + n_brunch + n_ice + n_farmers
    days_left = max(0, total_days - day)
    shop_tick = (hour % 4 == 0)  # town consumes after this sell
    carrot_cap = 24 if n_pet else 20

    # R39 (user): SELL FLOOR - "crashing our own price is fine, but do
    # not sell below a threshold - only sell when price recovers." The
    # government move: QUANTITY RESTRICTION. Sales execute per-unit
    # (each unit +1 town inventory), so a full dump saws its own price
    # down; we sell only the prefix whose MARGINAL price clears the
    # floor and hold the rest - shops drain the inventory back and the
    # held units sell into the recovery (inventory never resets; the
    # drain is the recovery). DENIAL CARVE-OUT: when the OPPONENT is
    # the flooder, we dump at any price - a crashed shared market IS
    # the weapon vs their revenue. Floors = ~40% of base price.
    SELL_FLOOR = {"WHEAT": 10, "CARROT": 14, "TOMATO": 24,
                  "STRAWBERRY": 48, "MELON": 100, "EGG": 20,
                  "MILK": 64, "WOOL": 80, "FERTILIZER": 40}

    # R45 (elite-tape decode): the ENDGAME CARROT ROTATION - when the
    # strb factory dies d24+, the taped 169k class refills with carrot
    # (3-day cycles, endgame px $80-130) NOT wheat ($40-50). Gated on
    # the LIVE quote: carrot must pay >= 2x wheat and >= $60 absolute
    # (user tape ep4: "carrots went up to 130 by the end").
    _endgame_carrot = (day >= 23
                       and quoted("CARROT") >= 60
                       and quoted("CARROT") >= 2 * quoted("WHEAT"))

    def _denial(item):
        # true when the opponent is flooding this market - denial mode
        # overrides the floor (volume is ammunition; measured TRACE-06)
        if item in ("WHEAT", "CARROT", "MELON", "STRAWBERRY"):
            return opp_crops.get(item, 0) >= {
                "MELON": 12, "STRAWBERRY": 30,
                "WHEAT": 25, "CARROT": 20}[item]
        src = {"EGG": "GOOSE", "MILK": "COW", "WOOL": "SHEEP"}.get(item)
        if src:
            # Already-dead market: dumping at $1 is not a weapon.
            # ep 110064585 wool $11 while milk $230.
            if quoted(item) < SELL_FLOOR.get(item, 1):
                return False
            return opp_animals.get(src, 0) >= 3
        if item == "FERTILIZER":
            return sum(opp_animals.values()) >= 8
        return False

    # R34 (user): the BIGGER late factory (38) only while the market is
    # deep enough to pay for the marginal tiles - LIVE quote >= $180.
    # Mirror doctrine intact: vs a strb-committed opponent (>= 30
    # standing) we MATCH their volume instead (mutual-dump markets
    # punish the bigger dumper - measured fixed-45 lesson); vs strb-
    # heavy (>= 35) the war latch above already runs 45.
    if opp_strb >= 30 and quoted("STRAWBERRY") < 160:
        # v34 losses: straw $30 when both dumped. Stay small.
        # v35 loss vs 124k: straw held $200 because shops ate the
        # berries - capping at 16 while they ran 40 left $40k on
        # the table. Only shrink when the quote is already dead.
        strb_target = 8
        if n_strb_shop >= 2:
            strb_target = 16
    else:
        strb_target = 8
        # 2 shops + straw>=160 = 33 (72 KEEP). Stefano: 1 smoothie,
        # they 33 we 16. Only bump 16->33 on 1 shop if THEY already
        # committed 30+ and the quote is still alive. Do not plant
        # 33 on a 1-shop board vs a 33-clone (s101 vs 41 -1k).
        if n_strb_shop >= 2 and quoted("STRAWBERRY") >= 160 and day <= 22:
            strb_target = 33
        elif n_strb_shop >= 1 and quoted("STRAWBERRY") >= 140 and day <= 22:
            strb_target = 33 if opp_strb >= 30 else 16
    if day <= 12:
        strb_target = max(strb_target, 12)

    plants, animals, structures, empty, weeds = [], [], [], [], []
    tile_map = {}
    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            pos = (x, y)
            if quadrant(pos) not in owned:
                continue
            tile_map[pos] = tile
            if tile is None:
                empty.append(pos)
            elif isinstance(tile, dict):
                if tile.get("kind") == "PLANT":
                    plants.append((pos, tile))
                elif tile.get("kind") == "WEED":
                    weeds.append(pos)
                elif tile.get("kind") in ("COOP", "PASTURE"):
                    structures.append((pos, tile))
                    if tile.get("animal"):
                        animals.append((pos, tile))

    counts = Counter(t["crop"] for _, t in plants)
    herd = Counter(t["animal"] for _, t in animals)
    held_animals = Counter({k: shed[k] for k in ANIMALS})
    all_carried = Counter()
    for inv in inventories:
        all_carried.update(inv)
        for kind in ANIMALS:
            held_animals[kind] += int(inv.get(kind, 0))

    opponent_crops = Counter()
    for row in opponent.get("tiles", []):
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                opponent_crops[tile["crop"]] += 1

    demand = Counter({k: 1 for k in MARKET if k != "FERTILIZER"})
    shop_ticks = turns / max(1, int(cfg.get("townShopSellInterval", 4)))
    for shop in obs.get("town", {}).get("unlocked_shops", []):
        for item, qty in SHOPS.get(shop, {}).items():
            demand[item] += qty * shop_ticks

    # ---------- Crop investment model ----------
    # This is a forecast, not a claim to know the opponent's future sales.

    def crop_score(crop, projected_counts=None):
        n = projected_counts if projected_counts is not None else counts
        cost, horizon, units, cap = CROPS[crop]
        if day + horizon >= total_days - 1:
            return -1e9

        # Opening bridge: avoid locking the opening wallet in slow crops.
        if day < 2 and crop not in ("WHEAT", "CARROT"):
            return -1e9

        inv = market_inventory.get(crop, 10000)
        own_supply = n[crop] * units * .65
        opposing_supply = opponent_crops[crop] * units * .45
        future_inv = inv + own_supply + opposing_supply - demand[crop] * horizon
        expected = sale_value(crop, future_inv, units, overrides)

        # Value per occupied day; mild preference for less service-heavy crops.
        score = (expected - cost) / (horizon + 1)
        if crop == "WHEAT" and herd:
            score *= 1.08
        return score

    # ---------- Harvest decisions ----------

    def harvestable(tile):
        crop = tile["crop"]
        units = int(tile.get("yield_units", 0))
        if units <= 0:
            return False
        if final_day:
            return True
        if crop == "STRAWBERRY":
            return True
        if crop == "TOMATO":
            # R33: batch at 2 units (production is 1/day - a daily
            # single-unit stop wastes worker time; the 4-unit cap
            # means waiting loses nothing)
            return final_day or units >= 2
        age = day - int(tile.get("planted_day", day))
        target = {"WHEAT": 4, "CARROT": 3, "MELON": 6}[crop]
        peak = {"WHEAT": 4, "CARROT": 3, "MELON": 10}[crop]
        lifespan = int(tile.get("max_lifespan_step", -1))
        near_decay = lifespan >= 0 and lifespan <= step + turns
        # R28 (user): LIQUIDITY HARVEST - crops are liquid, not
        # hold-to-maturity: pick the melon the moment its value beats
        # the seed spend WHEN CASH IS THIN ("we just need to make more
        # than we spend... buy and sell demand"). A wave melon at age 8
        # holds ~3 units (~$750 vs the $80 seed = 9x) - during the
        # d8-11 trough that cash compounds faster in animals/land than
        # the last 2-3 units (~2 more days) would. Cash-rich days keep
        # the full-maturity rule (waiting is +$250/water-day when we
        # don't need the money).
        if (crop == "MELON" and units >= 4
                and ((age >= 9 and money < 600)
                     # R38 (user): FIRST-SELLER - vs a melon-heavy
                     # opponent, cash out at first yield instead of
                     # holding into their dump ("cash out a day early
                     # so they cash out for less").
                     or (opp_crops.get("MELON", 0) >= 12
                         and age >= 10))):
            return True
        return units >= target or age >= peak or near_decay

    # ---------- Fertilizer allocation ----------
    # Keep only fertilizer with a plausible profitable use today.

    fert_candidates = []
    if not final_day:
        for pos, tile in plants:
            crop = tile["crop"]
            if int(tile.get("fertilized_until_day", -1)) >= day:
                continue
            if harvestable(tile):
                continue

            age = day - int(tile.get("planted_day", day))
            units = int(tile.get("yield_units", 0))
            extra = 0

            if crop in ("WHEAT", "CARROT", "MELON"):
                start, end = {
                    "WHEAT": (2, 4),
                    "CARROT": (2, 3),
                    "MELON": (6, 12),
                }[crop]
                ticks = sum(start <= age + j <= end for j in range(3))
                extra = min(ticks, max(0, CROPS[crop][3] - units))
            else:
                production = (
                    (8, 9, 10, 11) if crop == "TOMATO"
                    else (10, 12, 14, 16)
                )
                extra = sum(age <= tick <= age + 2 for tick in production)

            value = extra * quoted(crop) - quoted("FERTILIZER")
            if value > 35:
                fert_candidates.append((value, pos))

    fert_candidates.sort(reverse=True)
    fert_total = shed["FERTILIZER"] + all_carried["FERTILIZER"]
    fert_targets = {
        pos for _, pos in fert_candidates[:min(8, fert_total)]
    }
    fert_keep = max(0, len(fert_targets) - all_carried["FERTILIZER"])
    # R64: strawberries are never in fert_targets (harvestable() is
    # always true once they hold a unit), so hourly sells emptied the
    # shed and NE pickup found nothing. Hold fert the day of a tick
    # AND the day before so h0 stock exists.
    if not final_day and quoted("STRAWBERRY") > quoted("FERTILIZER"):
        _nk = 0
        for _pos, _t in plants:
            if quadrant(_pos) not in ("NE", "SW") or _t.get("crop") != "STRAWBERRY":
                continue
            if int(_t.get("fertilized_until_day", -1)) >= day:
                continue
            _age = day - int(_t.get("planted_day", day))
            _tick = _age >= 9 and (_age - 9) % 2 == 0
            _tmrw = (_age + 1) >= 9 and (_age + 1 - 9) % 2 == 0
            if _tick or _tmrw:
                _nk += 1
        fert_keep = max(fert_keep, min(16, _nk))

    # ---------- Strawberry blueprint quota (TRACE-05) ----------
    # Measured on the stored TRACE-05 capture (nb3_tetsu_r5, seed 42): the
    # +$91k gap is dominated by a 33-standing strawberry factory funded d2-8
    # at spend-to-floor priority (~$5-8k/day from d12; strb price ROSE
    # 128->232 all season because town demand eats market inventory, so the
    # 0.65 own-supply forecast can never argmax it — live7 planted zero).
    STRB_TARGET = strb_target
    # Coverage (user directive 09-11, restated): EVERY owned quad is
    # covered — no dirt, no empty spot. Safety is structural now: the
    # zoned planner plants only inside each zone's service capacity
    # (8 standing tiles per quad worker), so coverage can never outrun
    # maintenance (the unbudgeted all-quad fill measured -28k on seed
    # 202, 09-11). COVERAGE_QUADS is retired.

    # tile sets shared by the planner, the market pipeline and the log
    # Crop ground = every tile outside the two north animal rows.
    # (The SW/SE override is vestigial - animal rows only exist in the
    # north - but harmless.)
    crop_empty = [p for p in empty
                  if not animal_line(p) or quadrant(p) in ("SW", "SE")]
    crop_weeds = [p for p in weeds
                  if not animal_line(p) or quadrant(p) in ("SW", "SE")]
    # R38 (user): reserve the SW animal-row tiles from CROP planting
    # (installs are refused on planted tiles - the row must stay bare
    # until the herd lands). Nearest-shed SW tiles first.
    _sw_reserved = set()
    if state.get("sw_row"):
        _swk_need = state.get("sw_target", 4)
        _swk_have = sum(1 for p, t in animals if quadrant(p) == "SW")
        _sw_reserved = set(sorted(
            (p for p in crop_empty + crop_weeds if quadrant(p) == "SW"),
            key=lambda p: distance(p, shed_near(p)))[:max(
                0, _swk_need - _swk_have)])
        crop_empty = [p for p in crop_empty if p not in _sw_reserved]
        crop_weeds = [p for p in crop_weeds if p not in _sw_reserved]
    for _p in SCATTER_PADS:
        if quadrant(_p) in owned:
            _sw_reserved.add(_p)
    crop_empty = [p for p in crop_empty if p not in _sw_reserved]
    crop_weeds = [p for p in crop_weeds if p not in _sw_reserved]
    available_sites = [
        pos for pos, tile in tile_map.items()
        if pos not in SHED and animal_line(pos) and (
            tile is None
            or (isinstance(tile, dict) and (
                tile.get("kind") == "WEED"
                or (tile.get("kind") in ("COOP", "PASTURE")
                    and not tile.get("animal"))))
        )
    ]

    # ---------- R33 (user): MEASURED SE FILL - read the market, then
    # plant. "By the time tomatoes need to be planted we measure the
    # opp - do they have any, what are the prices at. If they're
    # acceptable where we double our profits counting labor/seed we
    # plant; if not we raise the crop target to fill the whole thing
    # with whatever the opponent is NOT planting." crop_score already
    # prices each crop's marginal tile NET OF SEED COST with our own
    # flood projected (their acres are opposing_supply, shop drain is
    # in the demand model), so the gate reads the LIVE market, never a
    # constant. TOMATO bar: score >= 2x the wheat churn it displaces
    # ("double our profits"). FALLBACK: the only standing crop whose
    # horizon still fits the SE window is MELON (strb is horizon-
    # blocked past d12 - which is WHY SE cycles wheat; wheat/carrot
    # churn the argmax already picks) - raise the melon cap by SE's
    # empty tiles while the marginal melon tile still out-scores
    # wheat churn (the sq glut curve prices our own flood honestly).
    # If neither clears, wheat churn stands: measured, not guessed.
    se_fill_tomato = False
    se_fill_n = 0
    # R84 tomatoes: every seed draws a different town (shops unlock
    # every 3 days with replacement). Only PIZZA_SHOP and
    # FARMERS_MARKET drain tomatoes. If those shops never show, or
    # show after the 8-day first-yield window, we plant zero. Quote
    # and opponent acres are the glut check - not a calendar.
    tomato_ok = False
    tomato_cap = 0
    tomato_room = 0
    _tom_ground = [p for p in crop_empty
                   if quadrant(p) in ("SW", "SE") and p not in SCATTER_PADS]
    tomato_room = len(_tom_ground)
    if (not final_day and day >= 2 and day + 8 <= total_days - 2
            and ("SW" in owned or "SE" in owned)
            and n_tom_shop >= 1
            and quoted("TOMATO") >= 50
            and opponent_crops.get("TOMATO", 0) < 12):
        tomato_ok = True
        tomato_cap = 6 if n_tom_shop == 1 else 8
        se_fill_tomato = True
    # Stefano: 8 tomato on SW while 8 berries and straw $149.
    # Factory tiles first. Tomato after the quota is close.
    if (quoted("STRAWBERRY") >= 140
            and counts.get("STRAWBERRY", 0) + seeds.get("STRAWBERRY", 0)
            < STRB_TARGET - 4):
        tomato_ok = False
        tomato_cap = 0
    if ("SE" in owned and not final_day
            and 6 <= day and day + 8 <= total_days - 2):
        se_fill_n = sum(1 for p in crop_empty if quadrant(p) == "SE")
        if se_fill_n >= 3:
            proj_m = Counter(counts)
            proj_m["MELON"] += se_fill_n
            s_wheat = max(1e-9, crop_score("WHEAT"))
            if (not tomato_ok
                    and crop_score("MELON", proj_m) > s_wheat):
                melon_cap += se_fill_n

    # ---------- Planned dispatch (user's main.py architecture port) ----------
    # The day is planned before the field is entered: every must-job is
    # routed into a per-worker timeline with an exact hour budget (Manhattan
    # distance is exact; movement is never blocked). Crew size comes from
    # the plan itself — hire until ZERO must-jobs drop. Workers then follow
    # their timelines; jobs already done are skipped, so live-board drift
    # self-corrects. Same-day service is STRUCTURAL: every PLANT carries its
    # WATER, survival water is scheduled first, and there is no priority
    # auction to lose to — nothing needs a deadline overlay.

    # engine crop table (line-verified): first_yield, max_yield_day,
    # interval, max_yield, ongoing
    ECROPS = {
        "WHEAT": (2, 4, 0, 6, False),
        "CARROT": (2, 3, 0, 4, False),
        "TOMATO": (8, 8, 1, 4, True),
        "STRAWBERRY": (10, 10, 2, 4, True),
        "MELON": (10, 12, 0, 6, False),
    }

    def serpentine(quad_name):
        ys = range(5) if quad_name[0] == "N" else range(5, 10)
        xs = range(5) if quad_name[1] == "W" else range(5, 10)
        order, flip = [], 0
        for y in ys:
            row = list(xs)
            if flip:
                row.reverse()
            flip ^= 1
            order += [(x, y) for x in row]
        return order

    def needs_water(tile):
        # survival: one miss from death; ongoing: production days only
        # (EOD +1 is automatic; water enables the fertilized +2); finite:
        # bonus window while still gaining yield.
        crop = tile["crop"]
        if int(tile.get("consecutive_unwatered", 0)) >= 1:
            return True
        if crop == "TOMATO":
            # R33 (user): survival-only watering - engine-verified that
            # the EOD base unit needs NO water (water buys the fert
            # bonus, skipped on a ~$60 crop, + survival, handled above)
            return False
        first, max_day, interval, cap, ongoing = ECROPS[crop]
        age = day - int(tile.get("planted_day", day))
        if ongoing:
            tick = first - 1
            return age >= tick and (age - tick) % interval == 0
        ws = (max_day + 1) // 2
        return ws <= age <= max_day and int(tile.get("yield_units", 0)) < cap

    def plan_crop_choice(vseeds, filler=False, quad=None, pos=None):
        # R27 (user, v2): NW = wheat desk + melon rows. The ANIMAL ROWS
        # are dead ground until the herd arrives - one MELON WAVE ripens
        # there d0->d12 (~6 tiles x 6 units x ~$250 = $9-12k, the cash
        # that buys NE + the herd as the tiles clear; the opening
        # cow+sheep keep 2 of the 8 row sites, geese auto-pause while
        # rows are full - the engine refuses installs on planted tiles,
        # so the herd resume is automatic). The CROP TILES are wheat
        # only, all game ("just wheat in the rest for feed/sell" - feed
        # security + the gentle-log price curve). The mix (strb/melon/
        # carrot/wheat) lives in NE/SW/SE, mainly the south (no animal
        # rows, 25 crop tiles each). NO strb in NW, ever.
        if pos is not None and pos in SCATTER_PADS:
            return None
        if pos is not None and quadrant(pos) == "NW" and animal_line(pos):
            # R27 v3 (user swap): the ROWS grow WHEAT - one fast cycle
            # ($10 seeds, cash+feed in 2-4 days) that never blocks the
            # herd for long ("aren't blocking the herd slots for 10
            # days" - a wheat tile clears within ~2 days whenever an
            # animal needs the slot). The MELON WAVE moved to the
            # regular crop tiles (never host animals; crop workers tend
            # them natively - no A-worker budget conflict, which is what
            # killed the row melons). Cap 6: the opening cow+sheep keep
            # their 2 sites.
            if (day <= 4 and vseeds.get("WHEAT", 0) > 0
                    and sum(1 for p, _t in plants
                            if p != pos and quadrant(p) == "NW"
                            and animal_line(p)
                            and isinstance(_t, dict)
                            and _t.get("kind") == "PLANT") < 6):
                return "WHEAT"
            # R34 (user, live20.1): SECOND row cycle - after the d4 sell
            # fills 4 of the cleared row tiles with wheat again (the
            # d4-8 cash bridge while NE opens; the other row sites stay
            # free for the steady herd installs).
            if (4 < day <= 8 and vseeds.get("WHEAT", 0) > 0
                    and sum(1 for p, _t in plants
                            if p != pos and quadrant(p) == "NW"
                            and animal_line(p)
                            and isinstance(_t, dict)
                            and _t.get("kind") == "PLANT") < 4):
                return "WHEAT"
            return None  # after the cycle, rows wait for animals
        if quad == "NW" and not war:
            # the melon wave owns the crop tiles first (d0-12: ~15
            # tiles x 6 units x ~$250 = the war chest that buys NE +
            # the herd + the factory), THEN the pure wheat feed desk
            # ("swap to just wheat after the animals are placed" - the
            # rows are gone to the herd by then, feed comes home-grown)
            if (day <= 12 and vseeds.get("MELON", 0) > 0
                    and counts["MELON"] < 15):
                return "MELON"
            if vseeds.get("WHEAT", 0) > 0 and day <= 26:
                return "WHEAT"
            return None
        # strawberry blueprint quota first (live18 plant-time semantics),
        # then the argmax over live-scored crops. MELON standing cap: the
        # planner plants everything that fits (unlike the old auction,
        # which starved PLANT priority) and a melon flood (measured 18-27
        # standing vs live18's 2-3) eats the daily labor budget — each
        # melon tile needs daily water in its gain window plus harvest —
        # starving the harvests that ARE revenue (strb 4-10 units and
        # melon 8-20 units left unharvested at h23). Cap standing melon
        # like the strb target; live18's winning shape ran 2-3.
        # strawberry blueprint quota first (TRACE-05) - the factory the
        # whole economy rides on. R20 (user): the match lives on the
        # NORTH quads; the south is melon country ("the rest is open
        # for melons"). A quota with tile-priority everywhere could
        # never complete (33 target vs 30 north tiles pre-SW) and
        # held every tile hostage - 12 melon seeds sat in pocket all
        # season (census B3: melon standing 0). North-only release
        # frees SW/SE for the melon waves while NW/NE carry the match.
        if (not final_day and vseeds.get("STRAWBERRY", 0) > 0
                and counts["STRAWBERRY"] < STRB_TARGET
                and (war or quad is None or quad != "NW")):
            return "STRAWBERRY"
        # R84: tomatoes on SW/SE only when the town is actually
        # buying them. Caps 6/8 so we don't flood a one-shop drain.
        # Carrot still takes the rest of the south (R79).
        if (quad in ("SW", "SE") and tomato_ok
                and vseeds.get("TOMATO", 0) > 0
                and counts["TOMATO"] < tomato_cap
                and day + 8 <= total_days - 2):
            return "TOMATO"
        # R79: freed SW/SE ground is carrot, not wheat. Melon still
        # wins argmax until melon_cap; after that carrot takes the tile.
        if (quad in ("SW", "SE") and not final_day
                and vseeds.get("CARROT", 0) > 0
                and counts["CARROT"] < carrot_cap
                and day <= 26):
            return "CARROT"
        # Quad policies REVERTED 09-12 (measured -12k mid-game cash on
        # all seeds: hard-coded floors displaced the argmax crops that
        # pay for them). The user's quad ROLES stand - north herd + feed
        # security via the argmax wheat preference, SW/SE serve the crop
        # score - but no hard floors. Re-add one at a time, measured.
        live = [
            c for c in CROPS
            if vseeds.get(c, 0) > 0 and crop_score(c) > 0
            and not (c == "MELON"
                     and counts["MELON"] >= melon_cap)
            # R84: tomato only on SW/SE while the shop-quote gate is open
            and not (c == "TOMATO" and (not tomato_ok or quad not in ("SW", "SE")))
        ]
        if filler:
            # Coverage fallback (user directive: no dirt). Fillers sit at
            # the bottom of the priority order — only chosen when no
            # scored crop fits. CARROT only while its fast-cash window is
            # open; WHEAT is the standing filler (4-day cycles).
            # R78: after the 8-berry cap, fill is melon (argmax) then
            # carrot/wheat. Wheat-only fill (R77) left the labor idle
            # on cheap grain. Carrot holds price under volume; wheat
            # is feed + dirt cover.
            _fill_order = ("CARROT", "WHEAT")
            for c in _fill_order:
                if vseeds.get(c, 0) > 0 and c not in live:
                    if c == "WHEAT" and day > 27:
                        continue
                    if c == "CARROT" and day > 26:
                        continue
                    live.append(c)
        if not live:
            # R24 (user): sunk planting, GENERALIZED - any pocket seed
            # may take an empty spot when time permits. A paid seed's
            # cost is spent; any yield is free (measured: 10-12 carrot
            # + 10 wheat seeds rotted in pocket at the whistle while
            # carrot fetched $72). The planner tends per-crop already -
            # needs_water knows each crop's own schedule (strb tick
            # days, melon windows, wheat/carrot survival), fert
            # candidates value each crop's ticks, harvest rules are
            # per-crop - so a mixed band stays alive: every stop is
            # decided by ITS tile's crop, never the zone's. Caps still
            # bind (tending capacity: the melon-flood lesson), the
            # window must still reach a yield, and the callers' budget
            # + zone_room checks are the "time permits".
            for c in ("MELON", "STRAWBERRY", "CARROT", "WHEAT"):
                if (vseeds.get(c, 0) > 0
                        and day + (10 if c == "STRAWBERRY"
                                   else ECROPS[c][0]) <= (
                            total_days - 1 if c in ("WHEAT", "STRAWBERRY")
                            else total_days - 2)
                        and (c != "MELON" or counts["MELON"] < melon_cap)
                        and (c != "STRAWBERRY"
                             or counts["STRAWBERRY"] < STRB_TARGET)):
                    return c
            return None
        return max(live, key=lambda c: (crop_score(c), c))

    def build_plan(n_workers, budget, pinned=None):
        """Zone-plan the day (user spec 09-11): every worker OWNS territory.
        3 workers per owned quad (the quad's serpentine split into contiguous
        bands), 1 worker per 5 animals (the animal lines). Each worker walks
        ONE explicit route: shed errands first (animal/wheat/fert pickup),
        then a single pass over their own tiles in serpentine order, doing
        every job at each stop — harvest, replant, water, dig, plant,
        fertilize — with dying plants hoisted to the front. No cross-quad
        assignment, no global auction, no overlays: the route IS the
        assignment. Planting is budgeted to the zone's service capacity
        (8 standing tiles per quad worker) so the plan never creates a crop
        it cannot tend end-to-end. Must-work that does not fit the day is
        counted dropped (never silently skipped) and the crew loop hires
        until nothing drops. Returns (timelines, dropped)."""
        pinned = None  # pinning measured net -6.5k solo (round 5)
        pin_ex = set()
        workers = []
        for i in range(n_workers):
            # A planned phantom (hire not yet landed) spawns at h1 at the
            # earliest — budget 24h for it and its tail job dies mid-walk
            # at h23 (measured: 10/11 workers exactly one job short).
            wbudget = budget if i < len(positions) else budget - 1
            start = positions[i] if i < len(positions) else SHED[i % 4]
            # Seed cargo from the LIVE inventory: hourly replans (seed
            # arrivals) reset pointers, and a rebuild that starts cargo at
            # zero orphans everything workers already carry.
            inv0 = inventories[i] if i < len(inventories) else {}
            carried = sum(
                q for k, q in inv0.items()
                if k in MARKET and k not in ("WHEAT", "FERTILIZER") and q > 0
            )
            workers.append({"pos": start, "busy": 0, "plan": [],
                            "cargo": carried, "wbudget": wbudget})
        dropped = 0

        def prefix_pads(w, q, slot, nslot):
            if q not in ("SW", "SE"):
                return
            pads = [pos for pos in SCATTER_PADS if quadrant(pos) == q]
            mine = pads[slot::max(1, nslot)]
            if not mine:
                return
            need = 0
            for pos_a in mine:
                _t = tile_map.get(pos_a)
                if (isinstance(_t, dict) and _t.get("animal")
                        and not _t.get("fed_today") and not final_day):
                    need += 1
            if need and shed.get("WHEAT", 0) > 0 and not final_day:
                st = shed_near(w["pos"])
                take = min(int(shed.get("WHEAT", 0)), need)
                if w["busy"] + distance(w["pos"], st) + 1 <= w["wbudget"]:
                    w["plan"].append(("PICKUP_WHEAT", st, take))
                    w["busy"] += distance(w["pos"], st) + 1
                    w["pos"] = st
            for pos_a in mine:
                tile = tile_map.get(pos_a)
                if not (isinstance(tile, dict) and tile.get("animal")):
                    continue
                d = distance(w["pos"], pos_a)
                cap = w["wbudget"]
                if (not tile.get("fed_today") and not final_day
                        and w["busy"] + d + 1 <= cap):
                    w["plan"].append(("FEED", pos_a, None))
                    w["busy"] += d + 1
                    w["pos"] = pos_a
                    d = 0
                if (not final_day and not tile.get("cared_today")
                        and quoted(ANIMALS[tile["animal"]][2]) > 10
                        and w["busy"] + d + 1 <= cap):
                    w["plan"].append(("CARE", pos_a, None))
                    w["busy"] += d + 1
                    w["pos"] = pos_a
                    d = 0
                if (int(tile.get("yield_units", 0)) >= 1
                        and w["busy"] + d + 1 <= cap):
                    w["plan"].append(("HARVEST", pos_a, None))
                    w["busy"] += d + 1
                    w["pos"] = pos_a
                    w["cargo"] += 1
                    d = 0
                if (tile.get("fertilizer_available")
                        and w["busy"] + d + 1 <= cap):
                    w["plan"].append(("COLLECT_FERTILIZER", pos_a, None))
                    w["busy"] += d + 1
                    w["pos"] = pos_a
                    w["cargo"] += 1


        def maybe_drop(w):
            # hourly dump cycle: return cargo to the shed in small chunks so
            # the market sells absorb into rising prices instead of one
            # end-of-day glut burst. (Threshold 2 measured CATASTROPHIC:
            # constant shed returns from the far fields ate the workday —
            # $40-65k. Keep 4; the EOD auto-drop rescues the remainder.)
            if w["cargo"] < 4:
                return
            st = shed_near(w["pos"])
            if w["busy"] + distance(w["pos"], st) + 1 <= budget:
                w["plan"].append(("DROP", st, None))
                w["busy"] += distance(w["pos"], st) + 1
                w["pos"] = st
                w["cargo"] = 0

        # ---- 0. zone staffing: ONE TEAM OF 3 PER QUAD (user spec 09-11):
        # 1 animal-line worker + 2 crop workers per quad = 12 hires at the
        # full farm. The herd tops out at 16 = 4 animals per quad — one
        # A-worker covers their quad's whole line. Team order is (crop,
        # animal, crop) so a scarce-body trim cuts the NEWEST quad's second
        # crop worker first and the first quad's team last (with 1-2
        # workers the crops still get tended: animals tolerate a missed
        # feeding day, dying crops do not — measured 630 missed waters
        # when this was wrong).
        quads = sorted(owned)
        roles = []
        _four = len(quads) == 4
        for q in quads:
            if q == "NW":
                # NW team: 3 crop + 2 animal workers (8 row spots) -
                # full crop coverage stays here (early melon/strb live
                # in NW; trimming it zeroed the melons, measured).
                # EXCEPTION - 4 quads owned: NW lends its 3rd crop
                # worker to the south (its farm is the wheat desk by
                # then, ~15 tiles = 2 workers). R30: the old 16-role
                # list + tail-pop trimmed SW to ZERO workers the day SE
                # opened (sorted order NE,NW,SE,SW - pop hits SW first)
                # -> 9 strb + 2 melo died in one night, 15 weeds stood
                # un-dug to the whistle. Every quad keeps its team.
                roles += ([("Q", q), ("A", q), ("Q", q), ("A", q)]
                          if _four else
                          [("Q", q), ("A", q), ("Q", q), ("A", q), ("Q", q)])
            elif q == "NE":
                # NE team: 2 crop + 3 ANIMAL workers (10 row spots) -
                # the 5th A-worker comes out of NE's third CROP slot,
                # not NW's (user 09-12: 5 workers for 18 animals)
                roles += [("Q", q), ("A", q), ("Q", q), ("A", q), ("A", q)]
            else:
                # south team: pure crops. 4 quads: 2 workers each (=
                # 4 south workers total, up from 3-with-SW-at-zero);
                # 3 quads: 3 workers.
                # R34 (user, live20.1): "keep everything full always" -
                # SE gets the 3rd south worker in the 4-quad form (2
                # workers x 8-tile zone cap = the 10-crop ceiling the
                # user measured; 3 workers cap SE at 24 of 25). Crew
                # stays 14: NW 4 + NE 5 + SW 2 + SE 3.
                roles += ([("Q", q), ("Q", q), ("Q", q)]
                          if (not _four or q == "SE")
                          else [("Q", q), ("Q", q)])
        qi = 0
        while len(roles) < n_workers:
            roles.append(("Q", quads[qi % len(quads)]))
            qi += 1
        while len(roles) > n_workers:
            roles.pop()

        animal_wr = [i for i, r in enumerate(roles) if r[0] == "A"]
        quad_wr = {}
        for i, r in enumerate(roles):
            if r[0] == "Q":
                quad_wr.setdefault(r[1], []).append(i)

        # ---- 1. ANIMAL ZONE: installs first, then the line sweep ----
        # Site choice is quota-respecting (unchanged); execution belongs to
        # the animal-line owners. Workers START on shed tiles — the pickup
        # is free — so the DIG->BUILD->PLACE chain runs by mid-morning.
        install_jobs = []
        if not final_day:
            # North concentration (user directive 09-11): the herd lives
            # in NW + NE only (4 engine sites per quad = 8 animals max).
            # South quads are pure crop ground — their line tiles plant.
            # R38: ...except the SW ANIMAL ROW: when active, its
            # reserved tiles host the oppositional herd.
            sites = [s for s in available_sites
                     if quadrant(s) in ("NW", "NE")]
            for _p in SCATTER_PADS:
                if _p in sites or quadrant(_p) not in owned:
                    continue
                _t = tile_map.get(_p)
                if _t is None or (isinstance(_t, dict) and (
                        _t.get("kind") == "WEED"
                        or (_t.get("kind") in ("COOP", "PASTURE")
                            and not _t.get("animal")))):
                    sites.append(_p)
            if state.get("sw_row"):
                sites += [p for p, t in tile_map.items()
                          if quadrant(p) == "SW" and p not in SHED and (
                              t is None
                              or (isinstance(t, dict) and (
                                  t.get("kind") == "WEED"
                                  or (t.get("kind") in ("COOP", "PASTURE")
                                      and not t.get("animal")))))]
            # 8 animals per north quad (user directive 09-11): the row
            # tiles hold them - NW's line has exactly 8 non-shed spots.
            # The old per-kind QUOTAS were OUR routing choice, not an
            # engine rule; the real constraints are structure type
            # (goose=COOP, cow/sheep=PASTURE) and one animal per tile.
            qcount = Counter(quadrant(pos_s) for pos_s, _ in animals)
            used = set()
            for kind in ("GOOSE", "COW", "SHEEP"):
                for _ in range(held_animals[kind]):
                    matching = []
                    for pos_s in sites:
                        if pos_s in used:
                            continue
                        q = quadrant(pos_s)
                        # R62: NW scripted route tends 6 packed tiles
                        # by the shed (3 per A-worker). Farther tiles
                        # are crop ground - an 8th animal on (0,3) is
                        # an animal we cannot care.
                        if q == "NW" and pos_s not in (
                                (4, 3), (3, 3), (2, 3),
                                (3, 4), (2, 4), (1, 4)):
                            continue
                        if q in ("SW", "SE") and pos_s not in SCATTER_PADS:
                            continue
                        if qcount[q] >= (6 if q == "NW"
                                         else (3 if q in ("SW", "SE") else 10)):
                            continue
                        t_s = tile_map[pos_s]
                        if (isinstance(t_s, dict)
                                and t_s.get("kind") in ("COOP", "PASTURE")
                                and t_s["kind"] != ANIMALS[kind][1]):
                            continue
                        existing = (isinstance(t_s, dict)
                                    and t_s.get("kind") == ANIMALS[kind][1])
                        matching.append((
                            0 if existing else 1,
                            # R38: north rows fill first; SW sites are
                            # for the oppositional row's surplus only
                            0 if q in ("NW", "NE") else 1,
                            distance(pos_s, shed_near(pos_s)), pos_s))
                    if not matching:
                        break
                    pos_s = min(matching)[3]
                    used.add(pos_s)
                    qcount[quadrant(pos_s)] += 1
                    install_jobs.append((pos_s, kind))
        def install_exec(q):
            # R38: a quad with no A-worker (SW's row runs on the crop
            # worker fallback) executes its OWN installs - never the
            # north A-workers (measured 303: they walked south, the
            # north feed/collect lines starved, -71.7k cascade).
            return ([i for i, r in enumerate(roles) if r == ("A", q)]
                    or [i for i, r in enumerate(roles) if r == ("Q", q)][:1]
                    or animal_wr or list(range(n_workers)))
        hw = 0
        nw_late_installs = []
        for pos_s, kind in install_jobs:
            placed_install = False
            # CARGO-AWARE INSTALL: an animal already carried by a worker
            # (picked up before a rebuild reset the pointers) installs
            # from where it stands — no shed pickup. The shed path would
            # assign the job to a worker with an empty inventory, the
            # PICKUP finds nothing, the INSTALL stale-skips, and the
            # animal rides in the pocket all season (measured: cow+sheep
            # stranded from d1, egg/wool/milk/fert production dead).
            carrier = None
            for ci in range(min(n_workers, len(inventories))):
                if int(inventories[ci].get(kind, 0)) > 0:
                    carrier = ci
                    break
            if carrier is not None:
                w = workers[carrier]
                c_cost = distance(w["pos"], pos_s) + 2
                if w["busy"] + c_cost <= budget:
                    w["plan"].append(("INSTALL", pos_s, kind))
                    w["busy"] += c_cost
                    w["pos"] = pos_s
                    placed_install = True
            if not placed_install:
                # R62: NW installs wait until AFTER the scripted animal
                # sweep. Morning installs on d10-11 ate 8-16h and cut
                # CARE from ~100% (herd 6) to 12-25% (herd 8). A shed
                # animal can wait one night; an un-cared cow cannot.
                if quadrant(pos_s) == "NW":
                    nw_late_installs.append((pos_s, kind))
                    continue
                _cand = install_exec(quadrant(pos_s))
                for _ in range(n_workers):
                    w = workers[_cand[hw % len(_cand)]]
                    hw += 1
                    st = shed_near(w["pos"])
                    cost = (distance(w["pos"], st) + 1
                            + distance(st, pos_s) + 2)
                    if w["busy"] + cost <= budget:
                        w["plan"].append(("PICKUP_ANIMAL", st, kind))
                        w["plan"].append(("INSTALL", pos_s, kind))
                        w["busy"] += cost
                        w["pos"] = pos_s
                        placed_install = True
                        break
            if not placed_install:
                dropped += 1

        # Animals belong to their quad's team: the quad's A-worker feeds,
        # collects, harvests and cares for their OWN line (user spec: 1
        # animal worker per quad; 16 herd = 4/quad).
        animals_by_quad = {}
        for _a in sorted(animals, key=lambda a: (a[0][1], a[0][0])):
            animals_by_quad.setdefault(quadrant(_a[0]), []).append(_a)
        shed_wheat = shed["WHEAT"]
        for q in quads:
            wr_q = [i for i, r in enumerate(roles) if r == ("A", q)]
            mine_q = animals_by_quad.get(q, [])
            if not mine_q and not (q == "NW" and nw_late_installs):
                continue
            # R27: plants standing in the ANIMAL ROWS (the melon-row
            # window) are the A-worker's ground - the crop-band re-trim
            # on a quad-open orphaned them (measured: row melons
            # unwatered from the NE-open day, dead by d10, the $9k
            # wave never sold, -35k).
            row_plants_q = [(p, t) for p, t in plants
                            if quadrant(p) == q and animal_line(p)]
            if not wr_q:
                if q in ("SW", "SE"):
                    continue
                # FEEDING NEVER DEPENDS ON CREW SIZE (user: nothing gets
                # lost): if the quad's animal worker was trimmed, the
                # quad's first crop worker - or the farmer - runs the
                # animal line BEFORE their crop band (the animal sweep
                # builds first, so the timeline is feed-then-crops).
                wr_q = ([i for i, r in enumerate(roles) if r == ("Q", q)][:1]
                        or ([0] if n_workers else []))
                if not wr_q:
                    dropped += sum(1 for _, t in mine_q
                                   if not t.get("fed_today") and not final_day)
                    continue
            # ---- R62 NW SCRIPTED ANIMAL ROUTE ----
            # Packed 6 animals on the tiles next to the shed, 3 per
            # A-worker. Walk order is shed-adjacent first. Every stop
            # is FEED -> CARE -> HARVEST -> COLLECT, no mid-row DROP.
            # Holes fill FIRST (workers spawn at the shed): 2 installs
            # on an empty band (opening), 1 while growing, 0 at 3/worker.
            # 3 animals + walks ~16h so the install still fits; a 4th
            # on the same worker does not. Extras go to NE.
            if q == "NW":
                NW_BANDS = (
                    ((4, 3), (3, 3), (2, 3)),
                    ((3, 4), (2, 4), (1, 4)),
                )
                nband = min(len(wr_q), len(NW_BANDS))
                for si, wi in enumerate(wr_q[:nband] if nband else wr_q[:1]):
                    w = workers[wi]
                    bt = NW_BANDS[si if si < 2 else 0]
                    mine = sorted([(p, t) for p, t in mine_q if p in bt],
                                  key=lambda a: -a[0][0])
                    # install into this band's holes before the sweep
                    my_inst = [(ps, k) for ps, k in list(nw_late_installs)
                               if ps in bt]
                    n_inst = (2 if not mine else (1 if len(mine) < 3 else 0))
                    n_inst = min(n_inst, len(my_inst))
                    taken = 0
                    keep = []
                    for ps, k in nw_late_installs:
                        if taken < n_inst and ps in bt:
                            st = shed_near(w["pos"])
                            wheat_pick = shed_wheat > 0 and not final_day
                            extra = ((1 if wheat_pick else 0)
                                     + (0 if final_day else 2))
                            cost = (distance(w["pos"], st) + 1
                                    + distance(st, ps) + 2 + extra)
                            if w["busy"] + cost <= budget:
                                if wheat_pick:
                                    w["plan"].append(("PICKUP_WHEAT", st, 1))
                                    shed_wheat -= 1
                                w["plan"].append(("PICKUP_ANIMAL", st, k))
                                w["plan"].append(("INSTALL", ps, k))
                                if not final_day:
                                    if wheat_pick:
                                        w["plan"].append(("FEED", ps, None))
                                    w["plan"].append(("CARE", ps, None))
                                w["busy"] += cost
                                w["pos"] = ps
                                taken += 1
                                continue
                        keep.append((ps, k))
                    nw_late_installs[:] = keep
                    if not mine:
                        continue
                    to_feed = ([a for a in mine
                                if not a[1].get("fed_today")]
                               if not final_day else [])
                    if to_feed and shed_wheat > 0:
                        st = shed_near(w["pos"])
                        take = min(shed_wheat, len(to_feed))
                        if w["busy"] + distance(w["pos"], st) + 1 <= budget:
                            w["plan"].append(("PICKUP_WHEAT", st, take))
                            w["busy"] += distance(w["pos"], st) + 1
                            w["pos"] = st
                            shed_wheat -= take
                    for pos_a, tile in mine:
                        d = distance(w["pos"], pos_a)
                        needs_feed = (not tile.get("fed_today")
                                      and not final_day)
                        if needs_feed:
                            if (quoted(ANIMALS[tile["animal"]][2]) <= 10
                                    and int(tile.get("consecutive_unfed", 0)) < 1):
                                needs_feed = False
                        if needs_feed:
                            if w["busy"] + d + 1 <= budget:
                                w["plan"].append(("FEED", pos_a, None))
                                w["busy"] += d + 1
                                w["pos"] = pos_a
                                d = 0
                            else:
                                dropped += 1
                        if (not final_day and not tile.get("cared_today")
                                and quoted(ANIMALS[tile["animal"]][2]) > 10
                                and w["busy"] + d + 1 <= budget
                                and ("CARE", pos_a) not in pin_ex):
                            w["plan"].append(("CARE", pos_a, None))
                            w["busy"] += d + 1
                            w["pos"] = pos_a
                            d = 0
                        if (int(tile.get("yield_units", 0)) >= 1
                                and w["busy"] + d + 1 <= budget
                                and ("HARVEST", pos_a) not in pin_ex):
                            w["plan"].append(("HARVEST", pos_a, None))
                            w["busy"] += d + 1
                            w["pos"] = pos_a
                            w["cargo"] += 1
                            d = 0
                        if (tile.get("fertilizer_available")
                                and w["busy"] + d + 1 <= budget
                                and ("COLLECT_FERTILIZER", pos_a) not in pin_ex):
                            w["plan"].append(("COLLECT_FERTILIZER", pos_a, None))
                            w["busy"] += d + 1
                            w["pos"] = pos_a
                            w["cargo"] += 1
                            d = 0
                    for pos_r, tile_r in (row_plants_q[si::max(1, len(wr_q))]
                                          if row_plants_q else []):
                        if not (isinstance(tile_r, dict)
                                and tile_r.get("kind") == "PLANT"):
                            continue
                        d2 = distance(w["pos"], pos_r)
                        if harvestable(tile_r):
                            if w["busy"] + d2 + 1 <= budget:
                                w["plan"].append(("HARVEST", pos_r, None))
                                w["busy"] += d2 + 1
                                w["pos"] = pos_r
                                w["cargo"] += 1
                            else:
                                dropped += 1
                        elif (not tile_r.get("watered_today")
                              and not final_day and needs_water(tile_r)
                              and w["busy"] + d2 + 1 <= budget):
                            w["plan"].append(("WATER", pos_r, None))
                            w["busy"] += d2 + 1
                            w["pos"] = pos_r
                continue
            per = max(1, (len(mine_q) + len(wr_q) - 1) // len(wr_q))
            for si, wi in enumerate(wr_q):
                w = workers[wi]
                mine = mine_q[si * per:(si + 1) * per]
                if not mine:
                    continue
                to_feed = ([a for a in mine
                            if not a[1].get("fed_today")]
                           if not final_day else [])
                if to_feed and shed_wheat > 0:
                    st = shed_near(w["pos"])
                    take = min(shed_wheat, len(to_feed))
                    if w["busy"] + distance(w["pos"], st) + 1 <= budget:
                        w["plan"].append(("PICKUP_WHEAT", st, take))
                        w["busy"] += distance(w["pos"], st) + 1
                        w["pos"] = st
                        shed_wheat -= take
                # FEED FIRST (decay fix, 09-12, measured: herd 16 holds
                # to d28 on all seeds): pass 1 feeds EVERY animal; pass 2
                # chains collect/harvest/care per stop. (The two-traversal
                # variant broke 42's feeding; the quad-policy variant
                # starved mid-game cash - both reverted.)
                # FEED FIRST (decay fix, 09-12, measured: herd 16 holds
                # to d28 on all seeds): pass 1 feeds EVERY animal; pass 2
                # chains collect/harvest/care per stop. (Care-coverage
                # variants all measured negative: care-in-pass-1 62-65k,
                # smart every-production-day care 55.0k vs this 70.2k -
                # the A-worker day cannot hold feed+care+collect+harvest
                # for 16 animals; care loses to collections every time.
                # ENGINE TRUTH for the future fix: the care bonus
                # ACCUMULATES per cared+fed day and is consumed on the
                # next production refresh - daily care = cows +2, sheep
                # +3 per production. Capturing it needs MORE labor, not
                # reordering: 3 A-workers per north quad at herd 8+.)
                # ---- R52-A MERGED SWEEP (one traversal, all ops/stop) ----
                # OLD: pass 1 fed every animal, pass 2 chained
                # collect/harvest/care - the row was WALKED TWICE a day.
                # Measured (walk_probe, seed 42): FEED 2.11 moves/op,
                # COLLECT 1.69 -> the A-worker day is walk-bound and CARE
                # (last op of pass 2) is what the budget cuts. One
                # traversal = ~half the row walking for the same ops.
                # Op PRIORITY is unchanged (feed, collect, harvest, care) -
                # this patch only merges the walk.
                # Feed stays a guaranteed PREFIX of the walk: every animal
                # that still needs feeding is visited before any animal
                # that is already fed (survival can never lose to care).
                _unfed, _fedq = [], []
                for pos_a, tile in mine:
                    if not tile.get("fed_today") and not final_day:
                        # R38 (user tape, milk $1): FLOOR TRIAGE - a
                        # floored product's animal goes SURVIVAL-ONLY
                        # (engine truth: production is unfed; feed buys
                        # survival + the care bonus). Feed every other
                        # day, keep the asset alive for a price
                        # recovery - half the feed wheat, zero loss.
                        if ((quoted(ANIMALS[tile["animal"]][2]) <= 10
                             or quadrant(pos_a) == "SW")
                                and int(tile.get("consecutive_unfed", 0)) < 1):
                            _fedq.append((pos_a, tile, False))
                            continue
                        _unfed.append((pos_a, tile, True))
                    else:
                        _fedq.append((pos_a, tile, False))
                for pos_a, tile, _needs_feed in _unfed + _fedq:
                    d = distance(w["pos"], pos_a)
                    if _needs_feed:
                        if w["busy"] + d + 1 <= budget:
                            w["plan"].append(("FEED", pos_a, None))
                            w["busy"] += d + 1
                            w["pos"] = pos_a
                            d = 0
                        else:
                            # an unfed animal is a drop, never a silent
                            # skip - escapes take two consecutive misses
                            dropped += 1
                    if (tile.get("fertilizer_available")
                            and w["busy"] + d + 1 <= budget
                            and ("COLLECT_FERTILIZER", pos_a) not in pin_ex):
                        w["plan"].append(("COLLECT_FERTILIZER", pos_a, None))
                        w["busy"] += d + 1
                        w["pos"] = pos_a
                        w["cargo"] += 1
                        d = 0
                        maybe_drop(w)
                    if (int(tile.get("yield_units", 0)) >= 1
                            and w["busy"] + d + 1 <= budget
                            and ("HARVEST", pos_a) not in pin_ex):
                        w["plan"].append(("HARVEST", pos_a, None))
                        w["busy"] += d + 1
                        w["pos"] = pos_a
                        w["cargo"] += 1
                        d = 0
                        maybe_drop(w)
                    if (not final_day and not tile.get("cared_today")
                            and quoted(ANIMALS[tile["animal"]][2]) > 10
                            and quadrant(pos_a) != "SW"
                            and w["busy"] + d + 1 <= budget
                            and ("CARE", pos_a) not in pin_ex):
                        w["plan"].append(("CARE", pos_a, None))
                        w["busy"] += d + 1
                        w["pos"] = pos_a
                # R27: tend the row plants (harvests first, then the
                # water each crop's own schedule demands - needs_water
                # is per-crop). The A-worker already walks these rows.
                for pos_r, tile_r in (row_plants_q[si::len(wr_q)]
                                      if row_plants_q else []):
                    if not (isinstance(tile_r, dict)
                            and tile_r.get("kind") == "PLANT"):
                        continue
                    d2 = distance(w["pos"], pos_r)
                    if harvestable(tile_r):
                        if w["busy"] + d2 + 1 <= budget:
                            w["plan"].append(("HARVEST", pos_r, None))
                            w["busy"] += d2 + 1
                            w["pos"] = pos_r
                            w["cargo"] += 1
                            maybe_drop(w)
                        else:
                            dropped += 1
                    elif (not tile_r.get("watered_today")
                          and not final_day and needs_water(tile_r)
                          and w["busy"] + d2 + 1 <= budget):
                        w["plan"].append(("WATER", pos_r, None))
                        w["busy"] += d2 + 1
                        w["pos"] = pos_r

        # R62: NW installs that waited for the animal sweep. Do NOT
        # count a miss as dropped - a shed animal is not must-work
        # (counting it inflated the crew when the sweep used the day).
        hw_nw = 0
        for pos_s, kind in nw_late_installs:
            placed_install = False
            _cand = install_exec("NW")
            if not _cand:
                continue
            for _ in range(n_workers):
                w = workers[_cand[hw_nw % len(_cand)]]
                hw_nw += 1
                st = shed_near(w["pos"])
                wheat_pick = shed_wheat > 0 and not final_day
                # shed pickups (animal + optional wheat), walk to site,
                # DIG/BUILD/PLACE (~2), then same-tile FEED+CARE so a
                # same-day place is not left unfed until tomorrow
                # (the h0 sweep already ran before this install).
                extra = (1 if wheat_pick else 0) + (0 if final_day else 2)
                cost = (distance(w["pos"], st) + 1
                        + distance(st, pos_s) + 2 + extra)
                if w["busy"] + cost <= budget:
                    if wheat_pick:
                        w["plan"].append(("PICKUP_WHEAT", st, 1))
                        shed_wheat -= 1
                    w["plan"].append(("PICKUP_ANIMAL", st, kind))
                    w["plan"].append(("INSTALL", pos_s, kind))
                    if not final_day:
                        if wheat_pick:
                            w["plan"].append(("FEED", pos_s, None))
                        w["plan"].append(("CARE", pos_s, None))
                    w["busy"] += cost
                    w["pos"] = pos_s
                    placed_install = True
                    break
            # leftover hours only; otherwise the animal waits until
            # tomorrow's sweep has slack (opening days have empty
            # sweeps so these land the same day).
            _ = placed_install

        # ---- 2. CROP ZONES: one band per worker, one pass per band ----
        vseeds = {c: seeds[c] for c in CROPS}
        planned_standing = Counter()   # per-quad plants added by THIS plan
        live_standing = Counter(quadrant(p) for p, _ in plants)
        ZONE_CAP = 8                    # standing tiles one quad worker tends
        # Revenue reservation: the strb factory and the melon window own
        # zone room ahead of wheat/carrot fillers (measured: fillers
        # occupied the capacity and melon sold 0 units vs baseline 66,
        # strb 128 vs 172 — coverage must never crowd out revenue).
        _rev_reserved = max(0, STRB_TARGET - counts["STRAWBERRY"])
        if 8 <= day <= total_days - 12:
            _rev_reserved += max(0, melon_cap - counts["MELON"])
        fert_by_quad = {}
        for pos_f in fert_targets:
            fert_by_quad.setdefault(quadrant(pos_f), []).append(pos_f)

        for q in quads:
            wr = quad_wr.get(q, [])
            if not wr:
                continue
            # animal rows are the herd's ground - crop bands skip them,
            # EXCEPT NW row tiles that are empty or planted (the melon-
            # row window: dead ground until the herd arrives). CRITICAL:
            # planted row tiles STAY in the band - the crop workers tend
            # what they plant (v1 dropped them post-planting: nobody
            # watered the row melons and all 5 died by d4, the $9k dump
            # never landed, herd+factory starved = -41k).
            band_order = [p for p in serpentine(q)
                          if not animal_line(p)
                          or (q == "NW"
                              and (tile_map.get(p) is None
                                   or (isinstance(tile_map.get(p), dict)
                                       and tile_map[p].get("kind")
                                       == "PLANT")))]
            k = len(wr)
            chunk = (len(band_order) + k - 1) // k
            zone_room = ZONE_CAP * k - live_standing[q] - planned_standing[q]
            # New SW is dirt (v34 losses: 20 empty the morning it
            # opens). Cover every crop tile; berry reservation can
            # wait one day.
            if q == "SW" and live_standing[q] < 18:
                zone_room = 25 - live_standing[q] - planned_standing[q]
            ne_hold = 4 if q == "NE" else 0
            if q == "NE":
                # R68: packed crop walk from the NE shed. 15 tiles
                # (y=0-2, x=5-9), two workers, shed-adjacent first.
                # Every stop: water+fert on a paying tick berry, then
                # harvest, then replant. No dying-first reorder.
                NE_BANDS = (
                    ((5, 2), (6, 2), (6, 1), (5, 1),
                     (5, 0), (6, 0), (7, 0)),
                    ((7, 1), (7, 2), (8, 2), (8, 1),
                     (8, 0), (9, 0), (9, 1), (9, 2)),
                )
                _pay = (not final_day
                        and quoted("STRAWBERRY") > quoted("FERTILIZER"))
                _use = ([NE_BANDS[0] + NE_BANDS[1]] if len(wr) < 2
                        else NE_BANDS)
                for si, wi in enumerate(wr[:len(_use)]):
                    w = workers[wi]
                    prefix_pads(w, q, si, len(_use))
                    band = _use[si]
                    my_fert = []
                    if _pay:
                        for _p in band:
                            _t = tile_map.get(_p)
                            if not (isinstance(_t, dict)
                                    and _t.get("kind") == "PLANT"
                                    and _t.get("crop") == "STRAWBERRY"):
                                continue
                            if int(_t.get("fertilized_until_day", -1)) >= day:
                                continue
                            _age = day - int(_t.get("planted_day", day))
                            if _age >= 9 and (_age - 9) % 2 == 0:
                                my_fert.append(_p)
                    # R78: mix tiles that already pay fert (wheat/carrot/
                    # melon in fert_targets). Cap 4 — leftover on the
                    # walk, not uncapped all-fert.
                    # R94b: when straw is rich, do not spray wheat.
                    if quoted("STRAWBERRY") < 160:
                        for _p in band:
                            if _p in my_fert or _p not in fert_targets:
                                continue
                            my_fert.append(_p)
                    my_fert = my_fert[:4]
                    if my_fert:
                        _have = 0
                        if wi < len(inventories):
                            _have = int(
                                inventories[wi].get("FERTILIZER", 0) or 0)
                        _carry = len(my_fert)
                        if _have >= 1:
                            my_fert = my_fert[:min(_carry, _have)]
                        else:
                            st = shed_near(w["pos"])
                            if (w["busy"] + distance(w["pos"], st) + 1
                                    <= budget
                                    and shed["FERTILIZER"] > 0):
                                w["plan"].append(("PICKUP_FERT", st, _carry))
                                w["busy"] += distance(w["pos"], st) + 1
                                w["pos"] = st
                                my_fert = my_fert[:_carry]
                            else:
                                my_fert = []
                    for pos_b in band:
                        tile = tile_map.get(pos_b)
                        _empty = tile is None
                        _weed = (isinstance(tile, dict)
                                 and tile.get("kind") == "WEED"
                                 and day < total_days - 2)
                        if _empty or _weed:
                            kind_b = "EMPTY" if _empty else "WEED"
                            crop = plan_crop_choice(vseeds, filler=True,
                                                    quad=q, pos=pos_b)
                            if crop is None or zone_room <= 0:
                                continue
                            if (crop == "WHEAT" and not final_day
                                    and ne_hold > 0):
                                ne_hold -= 1
                                continue
                            cost = 3 if kind_b == "WEED" else 2
                            d = distance(w["pos"], pos_b)
                            if w["busy"] + d + cost <= budget:
                                if kind_b == "WEED":
                                    w["plan"].append(("DIG", pos_b, None))
                                w["plan"].append(("PLANT", pos_b, crop))
                                w["plan"].append(("WATER", pos_b, None))
                                w["busy"] += d + cost
                                w["pos"] = pos_b
                                vseeds[crop] -= 1
                                planned_standing[q] += 1
                                zone_room -= 1
                            continue
                        if not (isinstance(tile, dict)
                                and tile.get("kind") == "PLANT"):
                            continue
                        _ne_rotate = (
                            tile.get("crop") == "WHEAT"
                            and vseeds.get("STRAWBERRY", 0) > 0
                            and counts["STRAWBERRY"] < STRB_TARGET
                            and not final_day
                            and int(tile.get("yield_units", 0)) > 0
                            and day - int(tile.get("planted_day", day)) >= 2
                        )
                        _did_h = False
                        _sprayed = False
                        if pos_b in my_fert:
                            if (not tile.get("watered_today")
                                    and not final_day
                                    and needs_water(tile)):
                                d = distance(w["pos"], pos_b)
                                if w["busy"] + d + 1 <= w["wbudget"]:
                                    w["plan"].append(("WATER", pos_b, None))
                                    w["busy"] += d + 1
                                    w["pos"] = pos_b
                                    _sprayed = True
                            if w["busy"] + 1 <= w["wbudget"]:
                                w["plan"].append(("FERTILIZE", pos_b, None))
                                w["busy"] += 1
                                my_fert.remove(pos_b)
                        if harvestable(tile) or _ne_rotate:
                            d = distance(w["pos"], pos_b)
                            if w["busy"] + d + 1 <= w["wbudget"]:
                                w["plan"].append(("HARVEST", pos_b, None))
                                w["busy"] += d + 1
                                w["pos"] = pos_b
                                w["cargo"] += 1
                                _did_h = True
                                if not my_fert:
                                    maybe_drop(w)
                                if (tile["crop"] not in ("TOMATO", "STRAWBERRY")
                                        and not final_day
                                        and zone_room > 0):
                                    crop = plan_crop_choice(
                                        vseeds, filler=True,
                                        quad=q, pos=pos_b)
                                    if (crop is not None
                                            and w["busy"] + 2 <= budget):
                                        w["plan"].append(("PLANT", pos_b, crop))
                                        w["plan"].append(("WATER", pos_b, None))
                                        w["busy"] += 2
                                        vseeds[crop] -= 1
                                        planned_standing[q] += 1
                                        zone_room -= 1
                            else:
                                dropped += 1
                        if ((not tile.get("watered_today") and not final_day
                                and needs_water(tile))
                                and not _sprayed and not _did_h):
                            d = distance(w["pos"], pos_b)
                            if w["busy"] + d + 1 <= w["wbudget"]:
                                w["plan"].append(("WATER", pos_b, None))
                                w["busy"] += d + 1
                                w["pos"] = pos_b
                            elif (int(tile.get("consecutive_unwatered", 0)) >= 1
                                  or tile["crop"] in ("STRAWBERRY", "TOMATO")):
                                dropped += 1
                continue
            if q == "SW":
                # R69: packed crop walk from the SW shed (4,5).
                # 24 crop tiles (skip the shed), shed-adjacent first.
                # 2 workers x 12, or 3 x 8 before SE opens.
                # Every stop: water+fert on a paying tick berry, then
                # harvest, then replant. No dying-first reorder.
                SW2 = (
                    ((3, 5), (3, 6), (4, 6), (4, 7), (3, 7), (3, 8),
                     (4, 8), (4, 9), (3, 9), (2, 9), (2, 8), (2, 7)),
                    ((2, 5), (2, 6), (1, 6), (1, 5), (0, 5), (0, 6),
                     (0, 7), (1, 7), (1, 8), (0, 8), (0, 9), (1, 9)),
                )
                SW3 = (
                    ((3, 5), (3, 6), (4, 6), (4, 7),
                     (3, 7), (3, 8), (4, 8), (4, 9)),
                    ((3, 9), (2, 9), (2, 8), (2, 7),
                     (2, 6), (2, 5), (1, 5), (1, 6)),
                    ((1, 7), (1, 8), (1, 9), (0, 9),
                     (0, 8), (0, 7), (0, 6), (0, 5)),
                )
                if len(wr) >= 3:
                    _use = SW3
                elif len(wr) == 2:
                    _use = SW2
                else:
                    _use = [SW2[0] + SW2[1]]
                _pay = (not final_day
                        and quoted("STRAWBERRY") > quoted("FERTILIZER"))
                for si, wi in enumerate(wr[:len(_use)]):
                    w = workers[wi]
                    prefix_pads(w, q, si, len(_use))
                    band = _use[si]
                    my_fert = []
                    if _pay:
                        for _p in band:
                            _t = tile_map.get(_p)
                            if not (isinstance(_t, dict)
                                    and _t.get("kind") == "PLANT"
                                    and _t.get("crop") == "STRAWBERRY"):
                                continue
                            if int(_t.get("fertilized_until_day", -1)) >= day:
                                continue
                            _age = day - int(_t.get("planted_day", day))
                            if _age >= 9 and (_age - 9) % 2 == 0:
                                my_fert.append(_p)
                    # R78: mix tiles that already pay fert (wheat/carrot/
                    # melon in fert_targets). Cap 4 — leftover on the
                    # walk, not uncapped all-fert.
                    # R94b: when straw is rich, do not spray wheat.
                    if quoted("STRAWBERRY") < 160:
                        for _p in band:
                            if _p in my_fert or _p not in fert_targets:
                                continue
                            my_fert.append(_p)
                    my_fert = my_fert[:4]
                    if my_fert:
                        _have = 0
                        if wi < len(inventories):
                            _have = int(
                                inventories[wi].get("FERTILIZER", 0) or 0)
                        _carry = len(my_fert)
                        if _have >= 1:
                            my_fert = my_fert[:min(_carry, _have)]
                        else:
                            st = shed_near(w["pos"])
                            if (w["busy"] + distance(w["pos"], st) + 1
                                    <= budget
                                    and shed["FERTILIZER"] > 0):
                                w["plan"].append(("PICKUP_FERT", st, _carry))
                                w["busy"] += distance(w["pos"], st) + 1
                                w["pos"] = st
                                my_fert = my_fert[:_carry]
                            else:
                                my_fert = []
                    for pos_b in band:
                        if pos_b in _sw_reserved:
                            continue
                        tile = tile_map.get(pos_b)
                        _empty = tile is None
                        _weed = (isinstance(tile, dict)
                                 and tile.get("kind") == "WEED"
                                 and day < total_days - 2)
                        if _empty or _weed:
                            kind_b = "EMPTY" if _empty else "WEED"
                            crop = plan_crop_choice(vseeds, filler=True,
                                                    quad=q, pos=pos_b)
                            if crop is None or zone_room <= 0:
                                continue
                            if (crop in ("WHEAT", "CARROT")
                                    and not (q == "SW" and live_standing[q] < 18)
                                    and zone_room <= _rev_reserved
                                    and not ((crop == "WHEAT" and wheat_target
                                              and counts["WHEAT"] < wheat_target)
                                             or (crop == "CARROT"
                                                 and carrot_target
                                                 and counts["CARROT"]
                                                 < carrot_target))):
                                continue
                            cost = 3 if kind_b == "WEED" else 2
                            d = distance(w["pos"], pos_b)
                            if w["busy"] + d + cost <= budget:
                                if kind_b == "WEED":
                                    w["plan"].append(("DIG", pos_b, None))
                                w["plan"].append(("PLANT", pos_b, crop))
                                w["plan"].append(("WATER", pos_b, None))
                                w["busy"] += d + cost
                                w["pos"] = pos_b
                                vseeds[crop] -= 1
                                planned_standing[q] += 1
                                zone_room -= 1
                            continue
                        if not (isinstance(tile, dict)
                                and tile.get("kind") == "PLANT"):
                            continue
                        _did_h = False
                        _sprayed = False
                        if pos_b in my_fert:
                            if (not tile.get("watered_today")
                                    and not final_day
                                    and needs_water(tile)):
                                d = distance(w["pos"], pos_b)
                                if w["busy"] + d + 1 <= w["wbudget"]:
                                    w["plan"].append(("WATER", pos_b, None))
                                    w["busy"] += d + 1
                                    w["pos"] = pos_b
                                    _sprayed = True
                            if w["busy"] + 1 <= w["wbudget"]:
                                w["plan"].append(("FERTILIZE", pos_b, None))
                                w["busy"] += 1
                                my_fert.remove(pos_b)
                        if harvestable(tile):
                            d = distance(w["pos"], pos_b)
                            if w["busy"] + d + 1 <= w["wbudget"]:
                                w["plan"].append(("HARVEST", pos_b, None))
                                w["busy"] += d + 1
                                w["pos"] = pos_b
                                w["cargo"] += 1
                                _did_h = True
                                if not my_fert:
                                    maybe_drop(w)
                                if (tile["crop"] not in ("TOMATO", "STRAWBERRY")
                                        and not final_day
                                        and zone_room > 0):
                                    crop = plan_crop_choice(
                                        vseeds, filler=True,
                                        quad=q, pos=pos_b)
                                    if (crop is not None
                                            and w["busy"] + 2 <= budget):
                                        w["plan"].append(("PLANT", pos_b, crop))
                                        w["plan"].append(("WATER", pos_b, None))
                                        w["busy"] += 2
                                        vseeds[crop] -= 1
                                        planned_standing[q] += 1
                                        zone_room -= 1
                            else:
                                dropped += 1
                        if ((not tile.get("watered_today") and not final_day
                                and needs_water(tile))
                                and not _sprayed and not _did_h):
                            d = distance(w["pos"], pos_b)
                            if w["busy"] + d + 1 <= w["wbudget"]:
                                w["plan"].append(("WATER", pos_b, None))
                                w["busy"] += d + 1
                                w["pos"] = pos_b
                            elif (int(tile.get("consecutive_unwatered", 0)) >= 1
                                  or tile["crop"] in ("STRAWBERRY", "TOMATO")):
                                dropped += 1
                continue
            # R64: two NE strawberries, tick day only. Water then fert
            # at the same stop. Start a couple (user: +1 per 5 successes).
            _ne_pair = []
            if (q == "NE" and not final_day
                    and quoted("STRAWBERRY") > quoted("FERTILIZER")):
                for _p in band_order:
                    _t = tile_map.get(_p)
                    if not (isinstance(_t, dict)
                            and _t.get("kind") == "PLANT"
                            and _t.get("crop") == "STRAWBERRY"):
                        continue
                    if int(_t.get("fertilized_until_day", -1)) >= day:
                        continue
                    _age = day - int(_t.get("planted_day", day))
                    if _age >= 9 and (_age - 9) % 2 == 0:
                        _ne_pair.append(_p)
                    if len(_ne_pair) >= 2:
                        break
            for bi, wi in enumerate(wr):
                w = workers[wi]
                prefix_pads(w, q, bi, max(1, len(wr)))
                band = band_order[bi * chunk:(bi + 1) * chunk]
                band_set = set(band)
                # fert prefix: carry one unit for a band target
                my_fert = [p for p in fert_by_quad.get(q, []) if p in band_set]
                if q == "NE":
                    my_fert = [p for p in _ne_pair if p in band_set]
                if quoted("STRAWBERRY") >= 160:
                    my_fert = [p for p in my_fert
                               if (isinstance(tile_map.get(p), dict)
                                   and tile_map[p].get("crop") == "STRAWBERRY")]
                if my_fert:
                    _carry = min(2, len(my_fert))
                    _have = 0
                    if q == "NE" and wi < len(inventories):
                        _have = int(inventories[wi].get("FERTILIZER", 0) or 0)
                    if q == "NE" and _have >= 1:
                        my_fert = my_fert[:min(_carry, _have)]
                    else:
                        st = shed_near(w["pos"])
                        if (w["busy"] + distance(w["pos"], st) + 1 <= budget
                                and shed["FERTILIZER"] > 0):
                            w["plan"].append(("PICKUP_FERT", st, _carry))
                            w["busy"] += distance(w["pos"], st) + 1
                            w["pos"] = st
                            my_fert = my_fert[:_carry]
                        else:
                            my_fert = []
                # stop list: dying plants AND tick-day waters first
                # (TRACE-06 / round-6 lever, delivered 09-12: an ongoing
                # crop's yield only accumulates if its TICK day is watered
                # - measured on seed 42, strb tiles cycled age 9/11/13
                # unwatered -> y0 -> died -> replanted: a zero-production
                # churn that stalled the whole mid-game).
                stops = []
                for idx, pos_b in enumerate(band):
                    tile = tile_map.get(pos_b)
                    if tile is None:
                        stops.append((1, idx, pos_b, "EMPTY"))
                    elif isinstance(tile, dict):
                        if (tile.get("kind") == "WEED"
                                # R37 (user tape, ep 108021898): weeds
                                # at d28-29 don't count against us - skip
                                # the dig, spend the labor on harvests.
                                and day < total_days - 2):
                            stops.append((1, idx, pos_b, "WEED"))
                        elif tile.get("kind") == "PLANT":
                            dying = (not tile.get("watered_today")
                                     and int(tile.get("consecutive_unwatered", 0)) >= 1)
                            tick = (not dying and not tile.get("watered_today")
                                    and needs_water(tile)
                                    and tile["crop"] in ("STRAWBERRY", "TOMATO"))
                            stops.append((0 if (dying or tick) else 1,
                                          idx, pos_b, "PLANT"))
                stops.sort(key=lambda st_: (st_[0], st_[1]))
                for _, idx, pos_b, kind_b in stops:
                    tile = tile_map.get(pos_b)
                    if kind_b == "PLANT":
                        _ne_rotate = (
                            q == "NE" and tile.get("crop") == "WHEAT"
                            and vseeds.get("STRAWBERRY", 0) > 0
                            and counts["STRAWBERRY"] < STRB_TARGET
                            and not final_day
                            and int(tile.get("yield_units", 0)) > 0
                            and day - int(tile.get("planted_day", day)) >= 2
                        )
                        _did_h = False
                        _sprayed = False
                        # R64: water+fert BEFORE harvest so a cargo DROP
                        # cannot dump the spray units.
                        if pos_b in _ne_pair or pos_b in my_fert:
                            if (not tile.get("watered_today") and not final_day
                                    and needs_water(tile)):
                                d = distance(w["pos"], pos_b)
                                if w["busy"] + d + 1 <= w["wbudget"]:
                                    w["plan"].append(("WATER", pos_b, None))
                                    w["busy"] += d + 1
                                    w["pos"] = pos_b
                                    _sprayed = True
                            if (pos_b in my_fert
                                    and w["busy"] + 1 <= w["wbudget"]):
                                w["plan"].append(("FERTILIZE", pos_b, None))
                                w["busy"] += 1
                                my_fert.remove(pos_b)
                        if harvestable(tile) or _ne_rotate:
                            d = distance(w["pos"], pos_b)
                            if w["busy"] + d + 1 <= w["wbudget"]:
                                w["plan"].append(("HARVEST", pos_b, None))
                                w["busy"] += d + 1
                                w["pos"] = pos_b
                                w["cargo"] += 1
                                _did_h = True
                                if not my_fert:
                                    maybe_drop(w)
                                if (tile["crop"] not in ("TOMATO", "STRAWBERRY")
                                        and not final_day
                                        and zone_room > 0):
                                    crop = plan_crop_choice(vseeds, filler=True,
                                                            quad=q, pos=pos_b)
                                    if crop is not None and w["busy"] + 2 <= budget:
                                        w["plan"].append(("PLANT", pos_b, crop))
                                        w["plan"].append(("WATER", pos_b, None))
                                        w["busy"] += 2
                                        vseeds[crop] -= 1
                                        planned_standing[q] += 1
                                        zone_room -= 1
                            else:
                                # a ripe harvest is never silently lost
                                dropped += 1
                        if ((not tile.get("watered_today") and not final_day
                                and needs_water(tile))
                                and not _sprayed and not _did_h):
                            d = distance(w["pos"], pos_b)
                            if w["busy"] + d + 1 <= w["wbudget"]:
                                w["plan"].append(("WATER", pos_b, None))
                                w["busy"] += d + 1
                                w["pos"] = pos_b
                            elif (int(tile.get("consecutive_unwatered", 0)) >= 1
                                  or tile["crop"] in ("STRAWBERRY", "TOMATO")):
                                dropped += 1
                    elif kind_b in ("WEED", "EMPTY"):
                        # dig-and-replant in one chain; a weed we cannot
                        # replant is left standing (never traded for dirt).
                        # Fillers (wheat/carrot) only plant in room beyond
                        # the revenue reservation.
                        if pos_b in _sw_reserved:
                            continue
                        crop = plan_crop_choice(vseeds, filler=True,
                                                quad=q, pos=pos_b)
                        if crop is None or zone_room <= 0:
                            continue
                        if (q == "NE" and crop == "WHEAT" and not final_day
                                and ne_hold > 0):
                            ne_hold -= 1
                            continue
                        if (crop in ("WHEAT", "CARROT")
                                and q != "NW"
                                and q != "NE"
                                and not (q == "SW" and live_standing[q] < 18)
                                and zone_room <= _rev_reserved
                                and not ((crop == "WHEAT" and wheat_target
                                          and counts["WHEAT"] < wheat_target)
                                         or (crop == "CARROT"
                                             and carrot_target
                                             and counts["CARROT"]
                                             < carrot_target))):
                            continue
                        cost = 3 if kind_b == "WEED" else 2
                        d = distance(w["pos"], pos_b)
                        if w["busy"] + d + cost <= budget:
                            if kind_b == "WEED":
                                w["plan"].append(("DIG", pos_b, None))
                            w["plan"].append(("PLANT", pos_b, crop))
                            w["plan"].append(("WATER", pos_b, None))
                            w["busy"] += d + cost
                            w["pos"] = pos_b
                            vseeds[crop] -= 1
                            planned_standing[q] += 1
                            zone_room -= 1

        # (R50 ZERO-WASTE round reverted wholesale: emergency water
        # sweep + d28 banking + value-tier stops measured 95.4-95.6k vs
        # v28's 97.9k. The waste census: 42 water-deaths/season, but 36
        # land on d28-29 where the R29 wheat fill's d28 watering IS the
        # value (banking young wheat at 1-2 units + skipping its water
        # loses 2-4 units x $45 x 20-40 tiles); midgame deaths ~13/
        # season ~ $3-5k < seed noise. The planner already allocates
        # the marginal op correctly - the tape's 0 weeds come from
        # offline-searched routes + the tick labor model, not triage.)
        # R79: leftover hours pick every wool/milk/egg and bag of fert
        # still sitting on an animal. Does not steal crop hours — only
        # slack after the band. Any worker with a window.
        _booked = set()
        for _w in workers:
            for _op, _pos, _ in _w["plan"]:
                if _op in ("HARVEST", "COLLECT_FERTILIZER"):
                    _booked.add((_op, _pos))
        _left = []
        for _pos, _t in animals:
            if int(_t.get("yield_units", 0)) >= 1 and (
                    "HARVEST", _pos) not in _booked:
                _left.append(("HARVEST", _pos))
            if _t.get("fertilizer_available") and (
                    "COLLECT_FERTILIZER", _pos) not in _booked:
                _left.append(("COLLECT_FERTILIZER", _pos))
        for _op, _pos in _left:
            _best = None
            _best_c = 99
            for _w in workers:
                _c = distance(_w["pos"], _pos) + 1
                if _w["busy"] + _c <= _w["wbudget"] and _c < _best_c:
                    _best = _w
                    _best_c = _c
            if _best is None:
                continue
            _best["plan"].append((_op, _pos, None))
            _best["busy"] += _best_c
            _best["pos"] = _pos
            _best["cargo"] += 1

        # ---- 3. end-of-plan cargo drops (shed feeds the hourly sells) ----
        for w in workers:
            if w["cargo"] > 0:
                st = shed_near(w["pos"])
                if w["busy"] + distance(w["pos"], st) + 1 <= budget:
                    w["plan"].append(("DROP", st, None))
                    w["busy"] += distance(w["pos"], st) + 1

        return {i: w["plan"] for i, w in enumerate(workers)}, dropped

    # ---- replan policy: first decision of the day, or new seeds/workers
    #      arrived mid-day (the plan is a pure function of the live board;
    #      rebuilding it from current positions self-corrects any drift) ----
    # Faithful to user_main: plan ONCE at day start; new bodies (hires
    # landing) get their pre-built timeline on arrival via one rebuild.
    # Seed arrivals do NOT rebuild — mid-day buys plant next morning (the
    # hourly-rebuild variant reset pointers constantly: tail DROPs and
    # INSTALLs never executed before the next reset; measured $47-66k vs
    # live18's $94k).
    _plans_cur = state.get("plans") or {}
    _ptrs_cur = state.get("ptrs") or {}
    _pending_install = any(
        j[0] in ("INSTALL", "PICKUP_ANIMAL")
        for _i, _pl in _plans_cur.items()
        for j in _pl[_ptrs_cur.get(_i, 0):])
    _held_now = sum(
        q for k, q in shed.items() if k in ANIMALS) + sum(
        q for inv in inventories for k, q in inv.items() if k in ANIMALS)
    _short = (len(positions) < int(state.get("plan_workers", 0)))
    # Orphan rebuild only when ACTIONABLE: held animals with no pending
    # install AND a site a rebuild could allocate (measured: an unhousable
    # sheep — 5 animals bought, 4 NW sites, goose/cow quotas consume them
    # — fired the trigger EVERY HOUR for days: ~50-150 full-plan pointer
    # resets/season = the "workers walking over work already done" in
    # replays). Dedup key: same day+hour+held+sites never rebuilds twice.
    _orphan_animals = (_held_now > 0 and not _pending_install)
    if (state.get("plan_day") != day
            or len(positions) > state.get("plan_workers", 0)
            or len(owned) > int(state.get("plan_quads", 0) or 0)
            or (hour == 4 and state.get("h4_done") != day and _short)
            or _orphan_animals):
        budget = turns - hour
        state["h4_done"] = day
        # Crew sizes to WORK (zero drops, cap 15) — cash caps the hire
        # loop, not the plan: mid-game h0 cash is thin (spend-to-floor)
        # and affordability-capped crews of 6-11 starved harvests while
        # units wasted at the per-tile cap (measured seed 202 d14-21:
        # $7k revenue vs live18's $41k).
        # Mid-day rebuild: pin each real worker's in-flight job chain
        # (current job + same-tile successors, e.g. DIG->PLANT->WATER)
        # so the rebuild re-plans the REMAINING work without abandoning
        # walks in progress — the replay-visible "walking over work
        # already done". Fresh day builds have nothing in flight.
        pinned = {}
        if state.get("plan_day") == day and hour > 0:
            _oldp = state.get("plans") or {}
            _oldt = state.get("ptrs") or {}
            _pin_ops = {"WATER", "HARVEST", "PLANT", "DIG", "FERTILIZE",
                        "INSTALL", "FEED", "CARE", "COLLECT_FERTILIZER"}
            for _i in range(min(len(positions), 16)):
                _pl_old = _oldp.get(_i)
                if not _pl_old:
                    continue
                _k = _oldt.get(_i, 0)
                if _k >= len(_pl_old):
                    continue
                _chain = []
                for _j in range(_k, min(_k + 3, len(_pl_old))):
                    _job = _pl_old[_j]
                    if _job[0] not in _pin_ops:
                        break
                    if _j > _k and _job[1] != _pl_old[_k][1]:
                        break
                    _chain.append(_job)
                if _chain:
                    pinned[_i] = _chain
        # Spec floor (user formula): 3 workers per owned quad + 1 per 5
        # animals. The farm's STANDING is its load forecast — sizing the
        # crew off one morning's job list oscillated to crew=1 on light
        # days (no animal-line worker -> egg/wool/milk/fert production
        # collapsed to ~10% of baseline) and back-swelled the next day.
        # User spec 09-11: one team of 3 per quad (1 animal + 2 crop
        # workers) = 12 hires at the full farm. Animals are the money
        # engine — the team exists to keep them producing and the crops
        # fertilized and watered.
        _spec_n = 0
        for q in owned:
            _spec_n += 5 if q in ("NW", "NE") else 3
        _spec_n = min(16, _spec_n)
        best_plans, best_n, best_dropped = None, len(positions), 10 ** 9
        for n in range(max(1, len(positions)), 17):
            p_try, dropped = build_plan(n, budget, pinned=pinned)
            if dropped < best_dropped:
                best_plans, best_n, best_dropped = p_try, n, dropped
            if dropped == 0:
                break
        # PLAN for what exists (every real body gets a band); HIRE toward
        # the spec (cash-capped). Planning 15 for a 6-body farm left 9
        # bands unmanned — the collapse measured at $6k finals.
        best_n = max(best_n, 0)
        plans = best_plans
        ptrs = {i: 0 for i in plans}
        state["plans"] = plans
        state["ptrs"] = ptrs
        state["plan_day"] = day
        state["plan_quads"] = len(owned)
        state["plan_workers"] = best_n
        # hires target the SPEC crew (3/quad + 1/5 animals), not just the
        # zero-drop floor — the standing farm is tomorrow's load too
        # ---- R52b WORK-AWARE CREW FLOOR ----
        # `dropped` counts ONLY must-work, so every routing improvement
        # shrinks the crew - and a shrinking crew starves the farm that
        # funds the next hire (measured death spiral: crew 13->10,
        # plants 70->30, seed 5 -36.6k). Floor the crew on the farm's
        # POTENTIAL load instead: owned ground + the herd. The hire block
        # caps desired_hands at 13 (crew 14) and gates on cash, so this
        # can only stop a collapse, never over-hire past the optimum.
        _work_floor = min(13, max(4, (25 * len(owned) + len(animals)) // 5))
        state["crew"] = max(best_n, _spec_n, _work_floor)
    else:
        plans = state.get("plans") or {}
        ptrs = dict(state.get("ptrs") or {})

    # ---- execute timelines (stale jobs skip; resources reserved
    #      within the turn exactly like the old dispatcher) ----
    free_shed = Counter(shed)
    free_seeds = Counter(seeds)
    actions = [["PASS"] for _ in positions]

    for i in range(len(positions)):
        pos, inv = positions[i], inventories[i]
        plan_i = plans.get(i) or []
        ptr = ptrs.get(i, 0)
        act = None

        while act is None and ptr < len(plan_i):
            op, tgt, arg = plan_i[ptr]
            tile = tile_map.get(tgt) if tgt else None

            if op == "PICKUP_WHEAT":
                if pos == tgt:
                    take = min(arg, free_shed["WHEAT"])
                    if take > 0:
                        free_shed["WHEAT"] -= take
                        act = ["PICKUP", "WHEAT", take]
                    ptr += 1
                    continue
                act = move(pos, tgt)
                break
            if op == "PICKUP_ANIMAL":
                if pos == tgt:
                    if free_shed[arg] > 0:
                        free_shed[arg] -= 1
                        act = ["PICKUP", arg, 1]
                    ptr += 1
                    continue
                act = move(pos, tgt)
                break
            if op == "PICKUP_FERT":
                if pos == tgt:
                    if free_shed["FERTILIZER"] > 0:
                        _take = max(1, min(arg, free_shed["FERTILIZER"]))
                        free_shed["FERTILIZER"] -= _take
                        act = ["PICKUP", "FERTILIZER", _take]
                    ptr += 1
                    continue
                act = move(pos, tgt)
                break
            if op == "DROP":
                if pos == tgt:
                    act = ["DROP"]
                    ptr += 1
                    break
                act = move(pos, tgt)
                break

            # tile jobs: staleness from the live board
            if op == "WATER":
                ok = (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                      and not tile.get("watered_today"))
            elif op == "FEED":
                ok = (isinstance(tile, dict) and tile.get("animal")
                      and not tile.get("fed_today")
                      and inv.get("WHEAT", 0) > 0)
            elif op == "CARE":
                ok = (isinstance(tile, dict) and tile.get("animal")
                      and not tile.get("cared_today"))
            elif op == "COLLECT_FERTILIZER":
                ok = (isinstance(tile, dict) and tile.get("animal")
                      and tile.get("fertilizer_available"))
            elif op == "HARVEST":
                ok = isinstance(tile, dict) and int(tile.get("yield_units", 0)) > 0
            elif op == "FERTILIZE":
                ok = (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                      and int(tile.get("fertilized_until_day", -1)) < day
                      and inv.get("FERTILIZER", 0) > 0)
            elif op == "DIG":
                ok = isinstance(tile, dict) and tile.get("kind") == "WEED"
            elif op == "PLANT":
                ok = ((tile is None or (isinstance(tile, dict)
                        and tile.get("kind") == "WEED"))
                      and free_seeds.get(arg, 0) > 0)
            elif op == "INSTALL":
                # tile None (and NOT a shed tile) => BUILD; WEED => DIG;
                # existing matching structure => PLACE.
                ok = (inv.get(arg, 0) > 0 and tgt not in SHED
                      and (tile is None
                           or (isinstance(tile, dict)
                               and (tile.get("kind") == "WEED"
                                    or tile.get("kind") == ANIMALS[arg][1]
                                    or tile.get("kind") in ("COOP", "PASTURE")))))
            else:
                ok = False

            if not ok:
                ptr += 1
                continue

            if pos != tgt:
                act = move(pos, tgt)
                break

            consumed = True
            if op == "PLANT":
                if isinstance(tile, dict) and tile.get("kind") == "WEED":
                    # weed chain: DIG first, PLANT lands next decision
                    # (same structural pattern as the INSTALL chain)
                    act = ["DIG"]
                    consumed = False
                else:
                    free_seeds[arg] -= 1
                    act = ["PLANT", arg]
            elif op == "INSTALL":
                # Engine truth (L493-505): BUILD_* only creates the EMPTY
                # structure — the animal is placed by a later PLACE. The
                # job stays current until the animal is actually on the
                # tile (DIG -> BUILD -> PLACE across decisions).
                if isinstance(tile, dict) and tile.get("kind") == "WEED":
                    act = ["DIG"]
                    consumed = False
                elif tile is None:
                    act = ["BUILD_" + ANIMALS[arg][1]]
                    consumed = False
                elif tile.get("kind") in ("COOP", "PASTURE"):
                    act = ["PLACE", arg]
                else:
                    act = None  # incompatible structure: stale
                    consumed = False
            else:
                act = [op]
            if act is not None:
                ptr += 1 if consumed else 0
                break
            ptr += 1 if not consumed else 0
            continue

        if act is None:
            # timeline exhausted: late-day cargo safety return
            cargo = sum(q for k, q in inv.items()
                        if k in MARKET and k not in ("WHEAT", "FERTILIZER"))
            if cargo > 0 and remaining <= distance(pos, shed_near(pos)) + 2:
                act = (["DROP"] if pos in SHED
                       else move(pos, shed_near(pos)))
            else:
                act = ["PASS"]

        actions[i] = act
        ptrs[i] = ptr

    state["ptrs"] = ptrs

    # ---------- Market: sell available production every hour ----------

    orders = []
    max_orders = int(cfg.get("maxMarketOrdersPerTurn", 10))
    virtual_cash = money

    feed_today = sum(not t.get("fed_today") for _, t in animals)
    pending_animals = sum(held_animals.values())
    reserve_wheat = (
        0 if final_day
        else max(4, feed_today + len(animals) + pending_animals
                 - all_carried["WHEAT"])
    )

    # Pending fert sprays: keep shed fertilizer for plan pickups still to
    # run today (hourly sales otherwise starve afternoon sprays — measured
    # 2-6 starved pickups/day d15+). Bounded: at most 6, fert only — a
    # stuck/reserved unit costs a falling $50-100 price, a starved spray
    # costs a doubled production tick.
    pending_plan_pickups = Counter()
    _plans_now = state.get("plans") or {}
    _ptrs_now = state.get("ptrs") or {}
    for _j, _pl in _plans_now.items():
        for _job in _pl[_ptrs_now.get(_j, 0):]:
            if _job[0] == "PICKUP_FERT":
                pending_plan_pickups["FERTILIZER"] += 1
    pending_plan_pickups["FERTILIZER"] = min(
        pending_plan_pickups["FERTILIZER"], 16)

    sellable = {}
    for item in MARKET:
        keep = reserve_wheat if item == "WHEAT" else (
            fert_keep if item == "FERTILIZER" and not final_day else 0
        )
        # Do not sell stock reserved for a PICKUP issued this turn, nor
        # stock owed to PENDING plan pickups later today (the old reserve
        # only covered same-turn pickups, so hourly fert sales starved
        # afternoon sprays — measured 2-6 starved pickups/day d15+).
        # R51 (27 ladder replays): on the LAST TWO DAYS nothing is
        # reserved except d28's feed wheat - the d29 h22-23 leftovers
        # (wool 10 + egg 8 + fert 4 unsold in 26/27 games, ~$2-3k each)
        # were pickup reservations for jobs that no longer matter.
        if final_day:
            reserved_pickup = 0
        elif day >= total_days - 2 and item != "WHEAT":
            reserved_pickup = 0
        else:
            reserved_pickup = max(0, shed[item] - free_shed[item])
        _pend = (0 if (final_day or (day >= total_days - 2
                                     and item != "WHEAT"))
                 else pending_plan_pickups[item])
        qty = max(0, shed[item] - max(keep, reserved_pickup, _pend))
        # R86 sell calendar. Shops consume AFTER our SELL on hours
        # 0/4/8/12/16/20. On those ticks we sell into the drain. Off
        # those ticks, hold anything the town is a customer for so we
        # don't saw the price for 3 hours of no drain. Melon has no
        # shop - sell whenever. Shed backup (>80) or last 2 days dump.
        _town_wants = {
            "WHEAT": n_wheat_shop, "CARROT": n_carrot_shop,
            "TOMATO": n_tom_shop, "STRAWBERRY": n_strb_shop,
            "EGG": n_egg_shop, "MILK": n_milk_shop, "WOOL": n_yarn,
            "MELON": 0, "FERTILIZER": 0,
        }.get(item, 0)
        if (qty and _town_wants and not shop_tick
                and not final_day and day < total_days - 2
                and sum(shed.values()) < 80):
            qty = 0
        # R39 (user): the floor - through d27, outside denial mode,
        # with shed room to hold: sell only down to the marginal floor
        # (and hold EVERYTHING while the quoted price is under it).
        if (qty and not final_day and day < total_days - 2
                and not _denial(item)):
            fl = SELL_FLOOR[item]
            if quoted(item) < fl:
                # hold ONLY while withholding has power (R40): the
                # market is still below its anchor or shops are
                # actively draining it. Glut banked = the recovery
                # never comes - sell for salvage before the whistle.
                if (sum(shed.values()) < 88
                        and (market_inventory.get(item, 10000) < 10000
                             or _drain.get(item))):
                    qty = 0
            else:
                inv = market_inventory.get(item, 10000)
                q_floor = 0
                while (q_floor < qty
                        and price(item, inv + q_floor, overrides) >= fl):
                    q_floor += 1
                qty = q_floor
        if qty:
            sellable[item] = qty

    # Capture high-value inventory first, but retain order capacity for feed.
    sell_order = sorted(
        sellable,
        key=lambda item: -sale_value(
            item, market_inventory.get(item, 10000),
            sellable[item], overrides
        )
    )
    for item in sell_order:
        if len(orders) >= max_orders:
            break
        qty = sellable[item]
        orders.append(["SELL", item, qty])
        estimate = sale_value(
            item, market_inventory.get(item, 10000), qty, overrides
        )
        # Sales are uncertain against simultaneous opponent market orders.
        virtual_cash += estimate * .80

    def buy_order(order, estimated_cost, reserve=0):
        # ---- R53 FIX 1: SEED BUY CAP (endgame leak) ----
        # Measured (endgame_probe, v30 seed 42): the wheat pouch went
        # 20 -> 43 on d28 and 43 seeds sat unsellable at the horn ($430).
        # A seed sown on d28 first-yields on d30 - after the horn - so it
        # can never be planted at all. Cap every seed buy by the crop's
        # last plantable day and by the crew's measured plant rate (~8/day).
        # last_plant = (total_days - 1) - first_yield_day:
        #   wheat/carrot d27 · tomato d21 · melon/strawberry d19.
        if order[0] == "BUY_SEED" and len(order) >= 3:
            _c = order[1]
            _lp = (total_days - 1) - ECROPS[_c][0]
            if day > _lp:
                return False
            _room = 8 * (_lp - day + 1) - int(seeds.get(_c, 0))
            if _room < order[2]:
                if _room <= 0:
                    return False
                order = ["BUY_SEED", _c, _room]
                estimated_cost = CROPS[_c][0] * _room
        nonlocal virtual_cash
        if len(orders) >= max_orders:
            return False
        if virtual_cash < estimated_cost + reserve:
            return False
        orders.append(order)
        virtual_cash -= estimated_cost
        return True

    # Buy feed before growth. No arbitrary maximum acceptable wheat price:
    # saving an established animal can justify expensive emergency feed.
    if not final_day:
        feed_stock = shed["WHEAT"] + all_carried["WHEAT"]
        feed_target = max(4, feed_today + len(animals) + pending_animals)
        deficit = max(0, feed_target - feed_stock)
        if deficit:
            qty = min(deficit, 30)
            unit_estimate = price(
                "WHEAT",
                market_inventory.get("WHEAT", 10000) - qty,
                overrides
            )
            affordable = int(max(0, virtual_cash - 70) // max(1, unit_estimate))
            qty = min(qty, affordable)
            if qty:
                buy_order(["BUY_PRODUCT", "WHEAT", qty],
                          qty * unit_estimate, 70)

    # ---------- Land: expansion gate (TRACE-03 fix + TRACE-05 blueprint path) ----------
    # (live19 note: ordered BEFORE hires — a 13-hand crew fills all 10
    #  market slots at h0-3 and starves BUY_LAND; land is one-shot and
    #  cannot wait for the day to fill.)
    # Original paths kept: density>=.80 and cash-rich (cost+8000), day cap 21.
    # TRACE-05/live10/live11 measurements: the strb factory forms late while
    # quad 1 is monopolized — Tetsu buys quad 2 at d6 spend-to-floor. live10's
    # standalone land path starved the seed budget; live11's opening-herd
    # trickle ($500-900/day from d1) funds both. Blueprint path: while the
    # strb quota is unfilled, buy land at spend-to-floor (reserve 150),
    # ordered BEFORE seed buys so land takes cash priority. This diff vs
    # live11 touches ONLY the land gate (animal buys unchanged in this diff).
    if (
        hour <= 3 and 1 <= len(owned) < 3 and day <= 21
        and len(orders) < max_orders
    ):
        # REAL crop ground: north quads lose 10 tiles to the two animal
        # rows (one is the shed), south quads are full 25. The old 20x
        # count capped NW density at 15/20 = .75 forever - NE NEVER
        # opened while $18k sat idle (measured, trace d18).
        crop_capacity = sum(
            15 if q in ("NW", "NE") else 25 for q in owned)
        density = len(plants) / max(1, crop_capacity)
        land_cost = (1000, 2000, 4000)[len(owned) - 1]
        # urgent must match the watering schedule: ongoing crops sit at
        # cuw=1 every other morning BY DESIGN (their water is planned for
        # today). Counting them blocked every BUY_LAND for days (live17's
        # measured lesson, now correct under planned watering).
        urgent = sum(
            not t.get("watered_today")
            and int(t.get("consecutive_unwatered", 0)) >= 1
            and t["crop"] not in ("TOMATO", "STRAWBERRY")
            for _, t in plants
        )
        # R20: a finite-crop ramp (wheat/carrot/melon d1-13) sits at
        # cuw=1 on alternating mornings BY DESIGN (survival water every
        # other day; pre-window melons need none) - measured 5-9
        # "urgent" tiles at every h0 with ZERO tile deaths, which
        # blocked every h0 land buy through the ramp (user: buy the
        # land the same day they do or sooner). Scale the bound with
        # the crop count; a real fire still exceeds it.
        _urgent_bound = max(2, len(positions),
                            (len(plants) + 1) // 2 + 2
                            if day <= 13 else 0)
        quota_pressure = (
            1 <= day <= 16 and counts["STRAWBERRY"] < STRB_TARGET
        )
        # Land discipline (replays 107580250/107583283): the panic arm
        # (money >= cost + 8000) stacked NE + SW in one day "catching up"
        # and the fill cash was gone — NE sat until d15. Now: at most ONE
        # quad per day (land_day latch, in the outer condition), fields we
        # own must be real-full (density >= .80) or the strb blueprint
        # needs the escape hatch, and the 4th quad (SE — the animal quad)
        # only opens once the herd can populate it.
        herd_ready = (len(owned) < 3
                      or (day >= 16
                          and len(animals) + sum(held_animals.values()) >= 8)
                      # R34: the earlier herd (steady pace from d4) lets
                      # SE open from d12 once 8+ animals are down
                      or (day >= 12
                          and len(animals) + sum(held_animals.values()) >= 8))
        # Post-purchase solvency: after the land payment we must still
        # afford the opener seeds (same-turn pre-buy) AND a wage/seed
        # operating buffer. Replay 107580250 + local seed 202: SW bought
        # with $2161 -> $170 left -> crew stuck at 1 -> the new quad's 37
        # planned jobs sat unexecuted for days (solo -41k).
        _next_q = next((q for q in ("NE", "SW", "SE") if q not in owned), None)
        _fill_cost = 0
        if _next_q is not None:
            _qt = sum(1 for y in range(10) for x in range(10)
                      if quadrant((x, y)) == _next_q
                      and not animal_line((x, y)) and (x, y) not in SHED)
            _fill_cost = _qt * 10  # R42: wheat opener ($10 seed)
        # NW-FIRST (user directive 09-11 night): fill the quad we OWN to
        # real-full before buying the next one — no early escape hatch
        # (the quota_pressure arm is retired). NE opens only when the
        # first revenue drop can fund the whole package outright: land +
        # opener seeds + animals for the new line (~a cow and a sheep).
        # R20 bridge: while the strb match is still forming (d8-13), the
        # GROUND is the priority - the $900 new-line animal budget defers
        # (the herd is NW-install-capped until this land lands, so the
        # budgeted animals cannot be bought anyway).
        # (R25 fast-land v2 retest with all safety nets: 68.8k = -10.5k,
        # THIRD failure - the cheap bar drains the strb/melon/herd
        # funding mid-game regardless of dirt prevention. The bridge bar
        # is correct for this chassis. Do not retest.)
        _animal_budget = (0 if (8 <= day <= 13
                                and counts["STRAWBERRY"] < STRB_TARGET)
                          else 900)
        # R34 (user, live20.1): NE-FIRST - the d4 row-wheat money opens
        # NE the day it clears cost+fill (no $900 animal pre-budget:
        # the herd paces itself on the $400 buy reserve, and NE's own
        # rows cannot host until its wheat clears anyway). SW keeps the
        # full package bar; the strb-formation deferral window follows
        # the factory's new d10-15 schedule.
        if len(owned) == 1:
            _animal_budget = 0
        elif 10 <= day <= 15 and counts["STRAWBERRY"] < STRB_TARGET:
            _animal_budget = 0
        _need = land_cost + 150 + _fill_cost + _animal_budget
        _dens = .90 if day <= 13 else .95
        # NE on day 7 if the $1000 is there. Fill-seed pre-budget was
        # pushing the bar to $1300 and we bought d8. Density bar stays.
        if len(owned) == 1 and day >= 6:
            _need = land_cost + 150
            _dens = .80
        if (density >= _dens
                and money >= _need
                and herd_ready
                and urgent <= _urgent_bound):
            land_ok = True
            if buy_order(["BUY_LAND"], land_cost, 150):
                state["land_day"] = day
                state["land_fill"] = _next_q

    # ---------- Quad-opening fill: same-turn seed pre-buy ----------
    # (replay 107581262: NE opened with 6 dirt, no planting for 2 days —
    # the pipeline had no seeds for the new tiles). Buy the opener crop
    # the SAME TURN as the land purchase, AFTER it (land keeps cash
    # priority). No idle stock, no leak window into other quads' dirt:
    # carrots while their economics hold, wheat for late quads.
    if (not final_day and state.get("land_day") == day
            and state.get("land_fill")):
        _qf = state["land_fill"]
        q_tiles = sum(
            1 for y in range(10) for x in range(10)
            if quadrant((x, y)) == _qf
            and not animal_line((x, y)) and (x, y) not in SHED)
        opener = "WHEAT"
        if (quoted("STRAWBERRY") >= 160 and not final_day
                and day + 10 <= total_days - 1):
            opener = "STRAWBERRY"
        want = max(0, q_tiles - seeds[opener])
        # (R40 pre-buy cap 6 measured -7.1k on seed 101 - its NE opener
        # leans on the full carrot buy; the idle-carrot leak is ~$300.
        # Left uncapped.)
        if want > 0:
            unit = CROPS[opener][0]
            qty = min(want, int(max(0, virtual_cash - 150) // unit))
            if qty > 0 and buy_order(
                ["BUY_SEED", opener, qty], unit * qty, 150
            ):
                seeds[opener] += qty

    # (R47 DOUBLE-WAVE experiment reverted: NE d4-9 melons + cheap
    # wheat cover measured 88.3k solo = -9.6k vs v28; 42 +3.5k but 101
    # -27.6k / 5 -13.9k / 303 -17.3k - the second wave holds NE through
    # d15-18, exactly the strb factory's formation window (the R41
    # ground-competition lesson, mirrored). Wave tiles 16-30 dump into
    # the recovery at ~$120 vs the first 15 at ~$250 - marginal
    # $550/tile MINUS $500-1,000/tile of displaced factory ticks.
    # The 15-tile wave is the measured optimum. Do not retest.)
    # ---------- Crop replacement / expansion seed pipeline ----------
    # R25 (user invariant): seeds to refill come BEFORE the herd in the
    # morning cash queue - "if we are about to harvest 10 crops we need
    # 10 replacement seeds; empty dirt tiles = loss of money". The
    # pipeline's slots already count imminent-harvest tiles (they are
    # tomorrow's dirt), so ordering it first guarantees the refill
    # budget exists before any animal buy ("1 here or 2 there when the
    # math lines up" - the herd is now affordability-paced by construction).
    if day >= 2 and not final_day:
        # live12 log measured: d20+ the 12-stock is clogged with strb
        # seeds no live crop_score would ever sow (factory at target or
        # window closed) while standing collapses 46->17 with tiles empty.
        # Count only seeds the model would still plant toward the stock,
        # so the pipeline can keep buying LIVE seeds late. (live13's cap
        # change is NOT included — that was its measured failure mode.)
        standing_seeds = sum(
            seeds[c] for c in CROPS if crop_score(c) > 0
        )
        slots = len(crop_empty) + sum(
            harvestable(t) and t["crop"] not in ("TOMATO", "STRAWBERRY")
            for _, t in plants
        )

        # Seed stock does not imply permission to exceed tending capacity.
        # Zone-based: 3 workers/quad x 8 standing tiles (the spec staffing),
        # matching the planner's own ZONE_CAP so buys track plantable room.
        field_capacity = max(12, 24 * len(owned) - len(animals))
        room = max(0, field_capacity - len(plants)
                   + sum(harvestable(t) for _, t in plants))
        need = max(0, min(12, slots, room) - standing_seeds)
        # R37: late-game labor cap - the crew plants ~8/day; buying
        # beyond that just strands seeds in the shed (tape: 19 idle
        # carrot seeds at the whistle).
        if day >= 24:
            need = min(need, 8 * max(0, total_days - 2 - day))

        projected = Counter(counts)
        projected.update(seeds)
        purchases = Counter()
        # Window gate: first yield must land before the season ends
        # (measured: 12 dead melon seeds bought after d18 = $960 sunk).
        # R34 (user): strb window extended to d15 - engine truth is 4
        # productions at first+0/2/4/6 (d10-16 after planting), so d13
        # is the last 4-tick plant day and d15 still lands 3 ticks at
        # the season's best prices (px 256->282 late). Mix-first: no
        # strb seeds before d10 (NE grows melon/wheat/carrot cash while
        # the herd builds; the wave dump + milk ramp fund the factory).
        # R40 (tape: 75 seeds idle): POCKET CAP - the pipeline may not
        # buy a crop that already has >= 4 seeds in pocket; the plan
        # plants ~8/day, so buys must track actual planting (the tape's
        # 15 idle carrots came from argmax buys the plan never planted).
        cands = [c for c in CROPS
                 if day + (14 if c == "STRAWBERRY" else ECROPS[c][0])
                 <= (total_days - 1 if c == "STRAWBERRY"
                     else total_days - 2)
                 and not (c == "STRAWBERRY" and day < 0)
                 and not (c == "TOMATO" and not tomato_ok)
                 and seeds.get(c, 0) < 4]
        for _ in range(need) if cands else []:
            crop = max(cands, key=lambda c: (crop_score(c, projected), c))
            if crop_score(crop, projected) <= 0:
                break
            cost = CROPS[crop][0]
            if virtual_cash < cost + 600:
                break
            # Budget each seed now; append aggregated orders afterward.
            virtual_cash -= cost
            projected[crop] += 1
            purchases[crop] += 1

        # R84: tomato seeds only when pizza/farmers-market is draining
        # them and SW/SE has empty crop ground. Pace 3/day, keep $150.
        if (tomato_ok and day + 8 <= total_days - 2
                and len(orders) < max_orders):
            tom_have = counts.get("TOMATO", 0) + seeds.get("TOMATO", 0)
            tom_need = max(0, min(tomato_cap, tomato_room) - tom_have)
            if tom_need > 0 and virtual_cash >= 50 + 150:
                q = min(tom_need, 3)
                orders.append(["BUY_SEED", "TOMATO", q])
                virtual_cash -= 50 * q

        for crop, qty in purchases.items():
            if len(orders) < max_orders:
                orders.append(["BUY_SEED", crop, qty])
            else:
                virtual_cash += qty * CROPS[crop][0]

    # ---------- Herd growth (moved 09-11: animals are the
    # money engine — their buys claim the morning cash BEFORE
    # the daily wage queue; measured: wages crowded the herd
    # out of the d8-12 window and egg/wool/milk never formed) ----------
    # Includes animals already in the shed or carried by workers.

    buy_cand = None
    buy_ok = False
    # R42 MEASURED VERDICT on "4 more sheep": REJECTED - there is no
    # free slot. North cap 18 is full (6c/6s/6g); every slot taken from
    # a cow loses ~$141/day (milk $283 x interval 2) vs a sheep's
    # ~$50-67/day at $150-200 wool - sheep need wool ~$420 to beat a
    # cow and the price curve tops out ~$240 (base 200, log .20).
    # Wool-rich games are captured by the 6 sheep we already run (the
    # price is the gain, not the headcount); wool-crash games are
    # protected by the static buy gate (wool < $60 stops buys).
    targets = {
        # R23: goose ceiling 8 (v21's mix - 201 eggs vs our 139) BUT the
        # extra 2 only after the milk engine is complete (cows+sheep at
        # 6): the naive ceiling-8 crowded cows out of the d18 growth
        # window and milk fell 91->54 units (-$11.3k). Late geese eat
        # nothing from milk; SE (3 coop sites) opens ~d16 anyway.
        # (R32 cow-for-geese swap measured -7.4k: milk +1.5-2k but eggs
        # 130 -> 59-71 units; the R30 acceleration already buys cows to
        # 4 by d7, so the swap only moves cow #2 up ~4 days. Geese stay
        # the opener fuel. Do not swap.)
        # (R33 goose-ramp pull d4-7 -> d1-4 measured: 6-seed WASH, avg
        # -0.15k; d1-3 cash is thin AND the install sites sit under the
        # melon wave until d10-12, so the d4-7 ramp is already at the
        # physical limit. A 3rd goose at d0 would starve the wave seeds
        # (cow-swap measured d0 headroom under $440). Do not retest.)
        "GOOSE": 0,
        # R30 (user): accelerate d5-9 - the wave pre-buys its seeds d0-1,
        # so the d5-9 cash ($550-1000/day measured) is surplus; buy the
        # herd to the NW install cap NOW (each cow bought d5 vs d9 =
        # ~2 extra milk productions; installs auto-block while row
        # wheat occupies sites, so this can only buy what fits).
        # R34 (user, live20.1): steady herd pace replaces the R30 d5-9
        # burst - ONE cow at d4 (right after the row-wheat sell), then
        # ceilings rise 1/day (cows from d4, sheep from d5) toward the
        # north cap; the $400 buy reserve + install-site availability
        # pace the actual buys at 1-2/day. NE land claims the morning
        # cash FIRST (land block is above this one), so the d4 wheat
        # money opens NE before any cow #2.
        "COW": min(6, day + 2) + (
            1 if n_milk_shop and "SW" in owned and quoted("MILK") >= 80 else 0),
        "SHEEP": min(6, max(0, day - 4)) + (
            1 if n_yarn and "SW" in owned and quoted("WOOL") >= 80 else 0),
    }

    if day <= 18 and not final_day:
        candidates = []
        _north = [q for q in ("NW", "NE") if q in owned]
        # north rows exactly: NW 8 (10 line tiles minus 2 shed), NE 10
        # -> 18 animals = the north filled to the brim (user 09-12)
        # (R31 hold-at-6 test: -3.9k - the 2 delayed animals out-earn
        # their wheat rows ~2:1; early buys are the measured payer)
        _north_cap = sum(6 if q == "NW" else 10 for q in _north)
        _north_cap += sum(1 for pos in SCATTER_PADS if quadrant(pos) in owned)
        # R38: SW row animals never count against the north cap
        _herd_total = len(animals) + int(sum(held_animals.values()))
        for kind in ("GOOSE", "COW", "SHEEP"):
            actual = herd[kind] + held_animals[kind]
            goal = targets[kind]
            if actual >= goal or _herd_total >= _north_cap:
                continue


            cost, structure, product, first, interval, cap = ANIMALS[kind]
            if day + first >= total_days - 2:
                continue
            if kind == "SHEEP" and quoted("WOOL") < 80:
                continue
            if kind == "COW" and quoted("MILK") < 80:
                continue

            compatible = 0
            for pos in available_sites:
                if quadrant(pos) not in ("NW", "NE"):
                    continue
                tile = tile_map[pos]
                if tile is None or tile.get("kind") == "WEED":
                    compatible += 1
                elif tile.get("kind") == structure:
                    compatible += 1
            if compatible <= sum(held_animals.values()):
                continue

            candidates.append((actual / max(1, goal), kind))

        if candidates:
            kind = min(candidates)[1]
            current = herd[kind] + held_animals[kind]
            qty = 2 - current if day == 0 and kind == "COW" else 1
            qty = max(1, qty)
            # Growth reserve lowered 1100 -> 400 (user: animals are the
            # money engine; the 1100 bar left cows/sheep at half volume
            # all season once NW's 8 row spots filled and NE opened).
            # (R25 closing-window 150 test: seed 202 -> 51.4k, the
            # d12-18 animal buys ate melon wave 2 - the 400 reserve is
            # load-bearing protection for the melon window. Herd caps
            # 17 on cash, not reserve. Do not lower.)
            reserve = 650 if kind == "GOOSE" and current < 2 else 400
            buy_cand = kind
            buy_ok = buy_order(["BUY_ANIMAL", kind, qty],
                               ANIMALS[kind][0] * qty, reserve)

    # ---------- R38 (user): SW OPPOSITIONAL ANIMAL ROWS ----------
    # "By day 15 read the opponents' animals - whatever one they are
    # weak on, add a row of 4 of that animal in SW; 8 if they have
    # time to pay." Gate: opponent runs NONE of the kind (the open
    # market), the live product price clears 2x the buy cost over the
    # remaining productions ("an animal is like 300 - selling the good
    # from it 2 times gives us a profit"), and the north goal for the
    # kind is already met (these buys are SW-bound surplus). Buys pace
    # 1/day at the $400 reserve; installs land on reserved SW tiles.
    # R43 RE-MEASURED (user: "+2 sheep, 20 animals total, not
    # replacing cows"): solo 73,161/65,557/80,278 = 73.0k vs 99.3k =
    # -26.2k. THIRD STRIKE on south animals at crew 14 (R38 x2, R43):
    # the herd DID reach 20, but the 2 sheep's ~2-3 ops/day came from
    # the SW fallback crop worker - strb standing collapsed 38 -> 2,
    # weeds ran to 30-49 (dead, unwatered tiles). 2 sheep gross ~$1.5k
    # vs ~$18k of destroyed factory. The crew has ZERO south slack;
    # a 15th hand costs $377/day vs the sheep's ~$100/day gross. The
    # north's 18 sites are the profitable frontier. DISABLED.
    if (15 <= day <= 20 and not final_day and "SW" in owned
            and len(orders) < max_orders
            and False  # R43: disabled - third strike, see verdict
            and not state.get("sw_row")):
        pass
    if state.get("sw_row") and day <= 19 and not final_day:
        _swk = state["sw_row"]
        _sw_installed = sum(
            1 for p, t in animals
            if quadrant(p) == "SW" and t.get("animal") == _swk)
        _sw_held = held_animals[_swk] - max(
            0, min(held_animals[_swk],
                   targets[_swk] - herd[_swk]))
        _sw_room = state.get("sw_target", 4) - _sw_installed - _sw_held
        if (_sw_room > 0 and len(orders) < max_orders
                and buy_order(["BUY_ANIMAL", _swk, 1],
                              ANIMALS[_swk][0], 400)):
            pass  # the install path + SW site reservation handle the rest


    # ---------- Hire based on the PLAN (single source of truth) ----------
    # The morning planner already computed the smallest crew that routes
    # every must-job with zero drops; hire toward that number. Actual
    # positions are used each turn; hires are never assumed to exist
    # before they appear in the observation.

    harvest_count = sum(harvestable(t) for _, t in plants)
    desired_hands = max(3, min(13, int(state.get("crew", 1)) - 1))
    if day <= 1:
        desired_hands = max(desired_hands, 8)

    hires_today = int(farm.get("hires_today", len(positions) - 1))
    hire_mult = float(cfg.get("farmHandCostMult", 1))
    if hour <= 3:
        # THE CORE CREW IS ALWAYS AFFORDABLE (stall fix, 09-12): hands
        # are daily and FIB-priced - the first six cost $12 TOTAL. The
        # old $180-250 reserve blocked hand #4 on broke mornings (seed
        # 42, d13: cash $71 -> 4 bodies -> 7 strb tick-tiles unwatered
        # -> zero yields -> tiles died -> the stall fed itself for a
        # week). A thin reserve for the first six hands; the expensive
        # tail (FIB 21+) keeps the full reserve.
        while hires_today < desired_hands and hires_today < len(FIB):
            cost = FIB[hires_today] * hire_mult
            _res = 20 if hires_today < 6 else (250 if day < 2 else 180)
            if not buy_order(["HIRE"], cost, _res):
                break
            hires_today += 1

    # ---------- Opening seed bridge ----------
    if day <= 1:
        for crop, target in (("WHEAT", 8), ("CARROT", 4)):
            need = max(0, target - counts[crop] - seeds[crop])
            if need:
                qty = min(need, int(max(0, virtual_cash - 800) // CROPS[crop][0]))
                if qty:
                    if buy_order(["BUY_SEED", crop, qty],
                                 qty * CROPS[crop][0], 800):
                        seeds[crop] += qty

    # ---------- Opening herd (TRACE-05 cadence) ----------
    # Tetsu's d0 order buys COW 2 + SHEEP 2 alongside the seeds,
    # spend-to-floor; the fert/wool/milk trickle ($300-900/day by d6) then
    # FUNDS the strb build and land. live9's quota starved d3-12 because a
    # geese-only opening ($200/day eggs) cannot fund it. Quad-NW quota
    # (2/1/2 = 5 sites) respected — all opening animals place immediately;
    # land gate and QUOTAS untouched.
    if day <= 1 and not final_day:
        # Opening (sweep 09-11, 9 animal starts x 3 seeds): the cow AT
        # DAY 0 is what drives the ramp (its $160 milk from d8; goose-
        # only openings finished -20k). COW+SHEEP (2 head, $900) ties the
        # 4-head goose-first ramp exactly - the growth block normalizes
        # the mix within a day. User spec: 1-3 animals to start.
        for kind, want in (("COW", 1), ("SHEEP", 1)):
            held = herd[kind] + held_animals[kind]
            if held >= want:
                continue
            qty = want - held
            if buy_order(["BUY_ANIMAL", kind, qty],
                         ANIMALS[kind][0] * qty, 80):
                held_animals[kind] += qty

    # ---------- Melon early boost (user 09-11; R20: the missed window) ----------
    # Census R19: when melons got ground they earned +$10.5k (76 units @
    # $230). The match-strb factory frees that ground: standing cap 16,
    # TWO waves (d2-6 plant -> d12-16 harvest; replant d8-16 -> d18-28
    # harvest - the user's "rest is open for melons"). Market math:
    # ~150-180 season units holds avg ~$150-200 (the #1 ladder shape:
    # melons still worth ~150 at the end).
    # R21: boost gap stays 12 at baseline (single-intent diff: the
    # mirror engages ONLY when an opponent out-stands our country - a
    # 17+ melon line raises cap+gap+reservation together; everything
    # else is byte-identical to R20).
    _m_gap_n = 6 if war else min(12, melon_cap)
    _m_last = 10 if war else 16
    _m_res = 400 if war else 150
    if day <= 1:
        _m_gap_n, _m_res = 12, 150  # 150k mix: 12 melon, rest berries
    if day <= _m_last and not final_day:
        m_gap = _m_gap_n - counts["MELON"] - seeds["MELON"]
        if m_gap > 0:
            qty = min(m_gap, int(max(0, virtual_cash - _m_res) // 80))
            if qty > 0 and buy_order(["BUY_SEED", "MELON", qty],
                                     80 * qty, _m_res):
                seeds["MELON"] += qty

    # ---------- Strawberry blueprint quota: spend-to-floor funding ----------
    # (R20: ordered AFTER the melon boost - at target 33 the $400/day
    # strb buys starved the melon window entirely; census B3/B4: zero
    # melon seeds ever bought, 12-tile wave never existed)
    # TRACE-05 cadence: Tetsu bought 33 strb seeds across d2-8 with money at
    # $27-2k (feed and herd keep priority; the argmax pipeline yields cash
    # to this quota). Replant-on-death keeps the factory at target through
    # d16; natural die-off ends it d20+ exactly like the captured run.
    # R27: no ground, no spend - strb seeds wait for NE (first factory
    # ground) or d10 at the latest (user: strb starts after NE unlock;
    # d1-9 NW cash funds wheat/melon-rows + the herd instead). Rate 8
    # for the compressed window (d12 = last 4-tick plant day).
    # R79: carrot ammo for SW/SE even when the fields are already
    # wheat — harvest-replant converts them. Do not wait on empty dirt.
    if (day <= 22
            and not final_day):
        strb_gap = STRB_TARGET - counts["STRAWBERRY"] - seeds["STRAWBERRY"]
        if strb_gap > 0:
            _res = 1150 if "NE" not in owned else 150
            if "NE" not in owned:
                _pace = 2
            elif strb_gap >= 8:
                _pace = 8
            else:
                _pace = 4
            qty = min(_pace, strb_gap, int(max(0, virtual_cash - _res) // 100))
            if qty > 0 and buy_order(
                ["BUY_SEED", "STRAWBERRY", qty], 100 * qty, 150
            ):
                seeds["STRAWBERRY"] += qty

    # Carrot after the factory. Luka 13 carrot / 3 strb at d12.
    _strb_behind = (
        quoted("STRAWBERRY") >= 140
        and counts.get("STRAWBERRY", 0) + seeds.get("STRAWBERRY", 0)
        < STRB_TARGET - 4)
    if (8 <= day <= 26 and not final_day
            and ("SW" in owned or "SE" in owned)
            and not _strb_behind):
        _cgap = 20 - counts["CARROT"] - seeds["CARROT"]
        if _cgap > 0:
            _cq = min(6, _cgap, int(max(0, virtual_cash - 150) // 20))
            if _cq > 0 and buy_order(
                ["BUY_SEED", "CARROT", _cq], 20 * _cq, 150
            ):
                seeds["CARROT"] += _cq

    # ---------- R29 (user): endgame wheat fill ----------
    # d25-27 the fields die back while wheat still fetches ~$50: fill
    # EVERY empty+weed tile with wheat ($10 seed, first yield d28-29,
    # watered window adds units) and liquidate at the whistle - unsold
    # shed/workers stock is worthless at the final horn (final score =
    # money). Uncapped: the whole point is zero dirt at the end.
    if 25 <= day <= 27 and not final_day:
        _efill = "CARROT" if _endgame_carrot else "WHEAT"
        _eseed_cost = 20 if _efill == "CARROT" else 10
        _eslots = len(crop_empty) + len(crop_weeds)
        _egap = _eslots - seeds["WHEAT"] if _efill == "WHEAT" else (
            _eslots - seeds["CARROT"])
        if _egap > 0:
            # R37 (user tape: 55 wheat + 19 carrot seeds idle in the
            # shed at the whistle): never buy more seeds than the crew
            # can still PLANT - ~8 plants/day across the endgame crew.
            _eq = min(_egap, 8 * max(0, total_days - 2 - day),
                      int(max(0, virtual_cash - 150) // _eseed_cost))
            if _eq > 0 and buy_order(["BUY_SEED", _efill, _eq],
                                      _eseed_cost * _eq, 150):
                seeds[_efill] += _eq

    # ---------- Coverage fillers: never an empty spot (dirt) ----------
    # Buy wheat (carrot while its window is open) to cover every empty +
    # weed tile in the coverage quads. Cash-gated, 150 reserve, <=10/day.
    if day >= 1 and not final_day:
        cov_slots = len(crop_empty) + len(crop_weeds)
        # R27: carrot filler only where carrots can plant (NE/SW/SE);
        # NW is the wheat desk - a carrot seed bought for NW rots
        # R78: mix ammo for the tiles past the 8-berry cap.
        # Carrot while its 3-day cycle still pays; wheat always.
        _strb_behind = (
            quoted("STRAWBERRY") >= 140
            and counts.get("STRAWBERRY", 0) + seeds.get("STRAWBERRY", 0)
            < STRB_TARGET - 4)
        if day <= 26 and not _strb_behind:
            _cneed = max(0, min(20, cov_slots) - counts.get("CARROT", 0)
                         - seeds["CARROT"])
            if _cneed > 0:
                _cq = min(_cneed, int(max(0, virtual_cash - 150) // 20))
                if _cq > 0 and buy_order(
                    ["BUY_SEED", "CARROT", _cq], 20 * _cq, 150
                ):
                    seeds["CARROT"] += _cq
        filler_crop = "WHEAT"
        filler_seeds = seeds["WHEAT"] + seeds["CARROT"]
        gap = min(10, cov_slots - filler_seeds)
        if gap > 0:
            unit = CROPS[filler_crop][0]
            qty = min(gap, int(max(0, virtual_cash - 150) // unit))
            if qty > 0 and buy_order(
                ["BUY_SEED", filler_crop, qty], unit * qty, 150
            ):
                seeds[filler_crop] += qty

    # ---------- R23: opener ammunition (wheat floor while land pends) ----------
    # The v21-port failure mode (b): land bought at land+150 -> $150
    # left -> same-turn pre-buy funds 0-7 seeds -> the new quad sits
    # dirt for days. Hold a small wheat floor so the fill ALWAYS has
    # seeds in pocket, whatever the morning cash.
    if 8 <= day <= 21 and len(owned) < 4 and not final_day:
        _wshort = 6 - seeds["WHEAT"]
        if _wshort > 0:
            _wq = min(_wshort, int(max(0, virtual_cash - 150) // 10))
            if _wq > 0 and buy_order(["BUY_SEED", "WHEAT", _wq],
                                      10 * _wq, 150):
                seeds["WHEAT"] += _wq

    try:
        with open("/tmp/astra_econ19.txt", "a") as _lf:
            _lf.write(
                f"d{day} h{hour} cash={money:.0f} hands={len(positions)-1} "
                f"desired={desired_hands} orders={len(orders)} "
                f"an={len(animals)} shed_an={sum(int(shed[k]) for k in ANIMALS)} "
                f"car_an={sum(int(all_carried[k]) for k in ANIMALS)} "
                f"tgt={dict(targets)} owned={len(owned)} sites={len(available_sites)} "
                f"plants={len(plants)} seeds={int(sum(seeds.values()))} "
                f"crop_empty={len(crop_empty)} crop_weeds={len(crop_weeds)} "
                f"dens={len(plants)/max(1, 20*len(owned)):.2f} "
                f"land_req={(1000, 2000, 4000)[len(owned)-1] if len(owned) < 4 else 0} "
                f"qC={sum(QUOTAS[q]['COW'] for q in owned)} "
                f"qS={sum(QUOTAS[q]['SHEEP'] for q in owned)} "
                f"qG={sum(QUOTAS[q]['GOOSE'] for q in owned)} "
                f"buy_cand={buy_cand} buy_ok={buy_ok} land_ok={state.get('land_day') == day}\n"
            )
    except Exception:
        pass
    return {
        "farmer": actions[0],
        "hands": actions[1:],
        "market": orders[:max_orders],
    }
