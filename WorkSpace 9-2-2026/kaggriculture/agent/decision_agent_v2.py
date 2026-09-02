"""
Decision Agent v2 — clean-room, reactive, evolvable. NO tape DNA.

Why v1 scored $0 (all fixed here):
  1. Day-0 spend blew the $3,000 budget (6 cows + 4 sheep = $4,400), so the
     seed orders never executed.  ->  v2 buys a sane, budgeted opening.
  2. Animals were bought but never placed: v1 had no PICKUP and its PLACE
     branch was a stub, so $2,900 of livestock sat in the shed all game.
     ->  v2 implements PICKUP-from-shed -> BUILD -> PLACE -> daily FEED.
  3. v1's PLANT loop `break`ed on the first scanned empty tile (0,0), 8 steps
     away, so it planted exactly ONE crop all game.
     ->  v2 plants the NEAREST empty tile (Manhattan distance; the board has
         no movement obstacles, so Manhattan == true distance).
  4. v1 only sold on day >= 28, so it had zero income while daily hires
     drained its cash to $0.  ->  v2 sells milk/wool/eggs/fertilizer/crops
     daily and does a full liquidation sweep in the final days.

Interface is identical to v1 — agent(obs, config) and set_params(params) —
so it drops straight into battle_harness / the search scripts.

Engine facts this agent is built on (from kaggriculture.json / engine source):
  * 24 turns/day, 30 days, 720 steps, startingMoney $3,000.
  * Movement is never blocked (even LOCKED tiles are passable), so path
    length between two tiles is Manhattan distance.
  * Workers auto-drop their inventory into the shed at end of day.
  * FEED needs WHEAT in the WORKER'S inventory (not the shed).
  * A plant must be watered on its planting day (starts consec_unwatered=1).
  * An animal escapes after 2 consecutive unfed days; must be fed daily.
"""

from kaggle_environments import make  # noqa: F401  (kept for __main__)

BOARD = 10
HALF = BOARD // 2

# The four tiles orthogonally adjacent to the shed (one per quadrant).
SHED_TILES = {(HALF - 1, HALF - 1), (HALF, HALF - 1), (HALF - 1, HALF), (HALF, HALF)}

# Crop economics (from the engine's CROPS table).
#   seed, first_yield_day, max_yield_day, max_yield, ongoing
CROPS = {
    "WHEAT":      {"seed": 10,  "first": 2,  "max_day": 4,  "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first": 2,  "max_day": 3,  "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first": 8,  "max_day": 8,  "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "max_day": 10, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first": 10, "max_day": 12, "max_yield": 6, "ongoing": False},
}

# Animal economics (from the engine's ANIMALS table).
#   cost, structure, first_yield_day, interval(days), max_held, product
ANIMALS = {
    "GOOSE": {"cost": 300, "struct": "COOP",    "first": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "struct": "PASTURE", "first": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "struct": "PASTURE", "first": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

# Order to try placing/selling — sheep first (fastest first yield).
ANIMAL_ORDER = ["SHEEP", "COW", "GOOSE"]

# Base prices for sell-timing heuristics.
BASE_PRICE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
              "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}

SELL_ORDER = ["MILK", "WOOL", "EGG", "FERTILIZER", "MELON", "STRAWBERRY",
              "CARROT", "TOMATO", "WHEAT"]

# ----------------------------------------------------------------------------
# Parameters — every knob here is evolvable by the search scripts.
# ----------------------------------------------------------------------------
DEFAULT_PARAMS = {
    # --- Opening (day 0, hour 0) ---
    "open_wheat": 12,       # BUY_PRODUCT WHEAT n  (feed stock)
    "open_hires": 4,        # HIRE count day 0
    "open_sheep": 2,
    "open_cows": 2,
    "open_geese": 0,
    "open_melon_seed": 5,
    "open_straw_seed": 4,
    "open_wheat_seed": 6,
    "open_carrot_seed": 0,

    # --- Hiring ---
    "daily_hires": 4,       # hands hired each morning (early game)
    "late_hires": 8,        # hands hired each morning (late game)
    "late_day": 10,         # switch to late_hires on this day

    # --- Land timing (-1 = never). Bought only if affordable AND the current
    #     land is mostly full (density gate) so plants stay compact. ---
    "ne_land_day": 6,       # NE quadrant  ($1,000)
    "sw_land_day": 12,      # SW quadrant  ($2,000)
    "se_land_day": 16,      # SE quadrant  ($4,000)
    "land_density": 0.60,   # buy next quadrant only when >= this full

    # --- Animals (targets ramp from `target_*` to `final_*` over the ramp days) ---
    "target_sheep": 2,   "final_sheep": 4,  "sheep_ramp_start": 0, "sheep_ramp_end": 6,
    "target_cow": 2,     "final_cow": 10,   "cow_ramp_start": 3,   "cow_ramp_end": 18,
    "target_goose": 0,   "final_goose": 0,

    # --- Crops (planting weights for the mid/late game) ---
    "crop_wheat": 0.5,
    "crop_melon": 0.25,
    "crop_straw": 0.2,
    "crop_carrot": 0.05,
    "crop_tomato": 0.0,
    "slow_crop_days": 2,    # during days 0..N plant slow/valuable crops first

    # --- Seed rebuys ---
    "melon_last_day": 14,   # keep rebuying melon seeds until this day
    "straw_last_day": 8,    # keep rebuying strawberry seeds until this day

    # --- Behavior ---
    "harvest_animal_min": 2,       # harvest an animal when yield >= this
    "plant_cutoff": 12,            # stop planting after this hour (fresh plants
                                   # must be watered the same day they're sown)
    "sell_hour": 2,                # hour of the day to run daily sells
    "wheat_reserve_per_animal": 2, # shed wheat kept back for feeding
    "cash_buffer": 250,            # never let cash fall below this
    "terminal_day": 28,            # liquidate everything from this day on
}


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def move_toward(pos, goal):
    """One step in the direction of goal. Returns ['DIR'] or ['PASS']."""
    if pos == goal:
        return ["PASS"]
    px, py = pos
    gx, gy = goal
    dx, dy = gx - px, gy - py
    if abs(dx) >= abs(dy):
        return ["EAST"] if dx > 0 else ["WEST"] if dx < 0 else ["PASS"]
    return ["SOUTH"] if dy > 0 else ["NORTH"] if dy < 0 else ["PASS"]


def nearest_shed_tile(pos):
    return min(SHED_TILES, key=lambda t: manhattan(pos, t))


class DecisionAgent:
    def __init__(self, params=None, seat=0):
        self.params = dict(DEFAULT_PARAMS)
        if params:
            self.params.update(params)
        self.seat = seat
        self._board_cache = None

    # ------------------------------------------------------------------ act
    def act(self, obs, configuration=None):
        p = self.params
        day = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)
        player = int(obs.get("player", 0) or 0)

        farm = obs["farms"][player]
        tiles = farm["tiles"]
        money = float(farm.get("money", 0) or 0)
        unlocked = set(farm.get("unlocked_quadrants", []) or [])

        private = obs.get("private") or {}
        shed = private.get("shed") or {}
        seeds = private.get("seeds") or {}
        inventories = private.get("inventories") or [{}]

        board = self._scan_board(tiles, unlocked)

        market = self._decide_market(day, hour, money, shed, seeds, board, unlocked)

        # Worker actions. Job-claiming prevents every worker doing the same task.
        claims = set()
        farmer_pos = tuple(farm.get("farmer", [HALF - 1, HALF - 1]))
        farmer_inv = inventories[0] if len(inventories) > 0 else {}
        farmer_action = self._decide_worker(farmer_pos, farmer_inv, board,
                                            shed, seeds, day, hour, claims)

        hand_actions = []
        for i, hp in enumerate(farm.get("hands", []) or []):
            inv = inventories[i + 1] if i + 1 < len(inventories) else {}
            hand_actions.append(self._decide_worker(tuple(hp), inv, board,
                                                    shed, seeds, day, hour, claims))

        return {"farmer": farmer_action, "hands": hand_actions,
                "market": market[:10]}

    # ------------------------------------------------------------- scanning
    def _scan_board(self, tiles, unlocked):
        board = {
            "grid": {},          # (x, y) -> tile dict (plants/structures only)
            "empty": [],         # [(x, y), ...] empty unlocked tiles
            "weeds": [],         # [(x, y), ...]
            "plants": [],        # dicts with x, y
            "animals": [],       # dicts with x, y, animal type
            "structures": [],    # dicts with x, y, type, has_animal
        }
        for y in range(BOARD):
            row = tiles[y] if y < len(tiles) else []
            for x in range(BOARD):
                t = row[x] if x < len(row) else None
                if t is None:
                    if self._quad(y, x) in unlocked:
                        board["empty"].append((x, y))
                    continue
                if t == "LOCKED":
                    continue
                if isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "PLANT":
                        d = {"x": x, "y": y, "crop": t.get("crop"),
                             "planted_day": t.get("planted_day", 0),
                             "yield_units": t.get("yield_units", 0),
                             "watered_today": t.get("watered_today", False),
                             "consec_unwatered": t.get("consecutive_unwatered", 0)}
                        board["plants"].append(d)
                        board["grid"][(x, y)] = d
                    elif kind == "WEED":
                        board["weeds"].append((x, y))
                    elif kind in ("COOP", "PASTURE"):
                        animal = t.get("animal")
                        d = {"x": x, "y": y, "type": kind,
                             "has_animal": animal is not None,
                             "animal": animal,
                             "yield_units": t.get("yield_units", 0),
                             "fed_today": t.get("fed_today", False),
                             "cared_today": t.get("cared_today", False),
                             "consec_unfed": t.get("consecutive_unfed", 0),
                             "fertilizer_available": t.get("fertilizer_available", False)}
                        board["structures"].append(d)
                        board["grid"][(x, y)] = d
                        if animal:
                            board["animals"].append(d)
        return board

    @staticmethod
    def _quad(y, x):
        return ("N" if y < HALF else "S") + ("W" if x < HALF else "E")

    # ------------------------------------------------------------ market
    def _decide_market(self, day, hour, money, shed, seeds, board, unlocked):
        p = self.params
        orders = []
        n_animals = len(board["animals"])
        reserve = n_animals * p.get("wheat_reserve_per_animal", 2) + 2
        buf = p["cash_buffer"]
        terminal = day >= p["terminal_day"]

        # ---- opening day ----
        if day == 0 and hour == 0:
            if p.get("open_wheat", 0) > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", int(p["open_wheat"])])
            for _ in range(int(p.get("open_hires", 0))):
                orders.append(["HIRE"])
            if p.get("open_sheep", 0) > 0:
                orders.append(["BUY_ANIMAL", "SHEEP", int(p["open_sheep"])])
            if p.get("open_cows", 0) > 0:
                orders.append(["BUY_ANIMAL", "COW", int(p["open_cows"])])
            if p.get("open_geese", 0) > 0:
                orders.append(["BUY_ANIMAL", "GOOSE", int(p["open_geese"])])
            for crop, key in [("MELON", "open_melon_seed"),
                              ("STRAWBERRY", "open_straw_seed"),
                              ("WHEAT", "open_wheat_seed"),
                              ("CARROT", "open_carrot_seed")]:
                n = int(p.get(key, 0) or 0)
                if n > 0:
                    orders.append(["BUY_SEED", crop, n])
            return orders[:10]

        # ---- morning routine (hour 0) ----
        if hour == 0:
            hires = p["daily_hires"] if day < p["late_day"] else p["late_hires"]
            for _ in range(min(int(hires), 10)):
                orders.append(["HIRE"])

            # land: buy once the scheduled day has passed, we can afford it,
            # and the current farm is mostly full (density gate).
            for quad, key, price in [("NE", "ne_land_day", 1000),
                                     ("SW", "sw_land_day", 2000),
                                     ("SE", "se_land_day", 4000)]:
                if p.get(key, -1) >= 0 and day >= p[key] and quad not in unlocked \
                        and money >= price + buf \
                        and self._land_density_ok(board, unlocked) \
                        and len(orders) < 10:
                    orders.append(["BUY_LAND"])

            # seed rebuys (skip once we're liquidating)
            if not terminal:
                if int(seeds.get("WHEAT", 0) or 0) == 0 and money > buf + 120 \
                        and len(orders) < 10:
                    orders.append(["BUY_SEED", "WHEAT", 5])
                if int(seeds.get("MELON", 0) or 0) == 0 \
                        and day < p.get("melon_last_day", 14) and money > buf + 500 \
                        and len(orders) < 10:
                    orders.append(["BUY_SEED", "MELON", 3])
                if int(seeds.get("STRAWBERRY", 0) or 0) == 0 \
                        and day < p.get("straw_last_day", 8) and money > buf + 500 \
                        and len(orders) < 10:
                    orders.append(["BUY_SEED", "STRAWBERRY", 2])

                # grow the herd toward the ramp targets
                on_board = {"SHEEP": 0, "COW": 0, "GOOSE": 0}
                for a in board["animals"]:
                    t = a.get("animal")
                    if t in on_board:
                        on_board[t] += 1
                for atype, tkey in [("SHEEP", "sheep"), ("COW", "cow"),
                                    ("GOOSE", "goose")]:
                    eff = self._effective_target(day, tkey)
                    have = on_board[atype] + int(shed.get(atype, 0) or 0)
                    cost = ANIMALS[atype]["cost"]
                    if have < eff and money > cost + buf and len(orders) < 10:
                        orders.append(["BUY_ANIMAL", atype,
                                       min(2, eff - have)])

            # feed wheat top-up (always — keep the herd alive).
            # Buy enough for today's feeding PLUS a small buffer, capped so a
            # huge herd can't bankrupt us in one morning.
            wheat_in_shed = int(shed.get("WHEAT", 0) or 0)
            need = max(0, (reserve + n_animals) - wheat_in_shed)
            if need > 0 and money > buf and len(orders) < 10:
                orders.append(["BUY_PRODUCT", "WHEAT", min(int(need), 20)])

            return orders[:10]

        # ---- selling (daily at sell_hour; every hour on terminal days) ----
        if terminal or hour == p.get("sell_hour", 2):
            for item in SELL_ORDER:
                if len(orders) >= 10:
                    break
                q = int(shed.get(item, 0) or 0)
                if item == "WHEAT":
                    if day >= 29:          # last full day: dump everything
                        q = int(shed.get("WHEAT", 0) or 0)
                    else:                  # keep the feed reserve alive
                        q = max(0, q - reserve)
                if q > 0:
                    orders.append(["SELL", item, q])
            return orders[:10]

        return orders[:10]

    # ------------------------------------------------------------ worker
    def _decide_worker(self, pos, inv, board, shed, seeds, day, hour, claims):
        p = self.params

        # 0. Carrying an animal -> place it (build the structure if needed).
        for atype in ANIMAL_ORDER:
            if int(inv.get(atype, 0) or 0) > 0:
                return self._act_place_animal(pos, atype, board, claims)

        # 1. Emergency feed (animals one miss away from escaping).
        a = self._act_feed(pos, inv, board, shed, claims, emergency=True)
        if a: return a

        # 2. Emergency water (plants one miss away from becoming weeds).
        a = self._act_water(pos, board, claims, emergency=True)
        if a: return a

        # 3. Get bought animals out of the shed (build + pickup).
        a = self._act_start_herd(pos, inv, board, shed, day, claims)
        if a: return a

        # 4. Feed (daily upkeep).
        a = self._act_feed(pos, inv, board, shed, claims, emergency=False)
        if a: return a

        # 5. Water (daily upkeep).
        a = self._act_water(pos, board, claims, emergency=False)
        if a: return a

        # 6. Harvest (crops at peak, animals above threshold).
        a = self._act_harvest(pos, board, day, claims)
        if a: return a

        # 7. Plant seeds (early enough that fresh plants get watered same-day).
        a = self._act_plant(pos, board, seeds, day, hour, claims)
        if a: return a

        # 8. Collect fertilizer (one-time per animal per day; lost if skipped).
        a = self._act_collect(pos, board, claims)
        if a: return a

        # 9. Care (banks a production bonus; skippable for a day).
        a = self._act_care(pos, board, claims)
        if a: return a

        # 10. Dig weeds (they block planting).
        a = self._act_dig(pos, board, claims)
        if a: return a

        return ["PASS"]

    def _act_place_animal(self, pos, atype, board, claims):
        struct = ANIMALS[atype]["struct"]
        here = board["grid"].get(pos)
        if here and here.get("type") == struct and not here.get("has_animal"):
            return ["PLACE", atype]
        # nearest matching empty structure
        best = None
        for s in board["structures"]:
            if s.get("type") == struct and not s.get("has_animal"):
                d = manhattan(pos, (s["x"], s["y"]))
                if best is None or d < best[0]:
                    best = (d, s)
        if best:
            target = (best[1]["x"], best[1]["y"])
            return self._move_or_act(pos, target, ["PLACE", atype])
        # no structure yet -> build one on the nearest empty tile
        target = self._nearest_empty(pos, board, claims, "build")
        if target:
            claims.add(("build", target[0], target[1]))
            return self._move_or_act(pos, target, ["BUILD_" + struct])
        return None

    def _act_feed(self, pos, inv, board, shed, claims, emergency):
        unfed = [a for a in board["animals"] if not a["fed_today"]]
        if emergency:
            unfed = [a for a in unfed if a["consec_unfed"] >= 1]
        if not unfed:
            return None
        if int(inv.get("WHEAT", 0) or 0) > 0:
            unfed.sort(key=lambda a: manhattan(pos, (a["x"], a["y"])))
            for a in unfed:
                ap = (a["x"], a["y"])
                if ("feed", ap[0], ap[1]) in claims:
                    continue
                claims.add(("feed", ap[0], ap[1]))
                return self._move_or_act(pos, ap, ["FEED"])
            return None
        # no wheat in hand -> fetch some from the shed
        wheat_in_shed = int(shed.get("WHEAT", 0) or 0)
        if wheat_in_shed <= 0:
            return None
        n = min(wheat_in_shed, max(1, len(unfed)))
        target = nearest_shed_tile(pos)
        return self._move_or_act(pos, target, ["PICKUP", "WHEAT", n])

    def _act_water(self, pos, board, claims, emergency):
        plants = [pl for pl in board["plants"] if not pl["watered_today"]]
        if emergency:
            plants = [pl for pl in plants if pl["consec_unwatered"] >= 1]
        if not plants:
            return None
        plants.sort(key=lambda pl: (-pl["consec_unwatered"],
                                    manhattan(pos, (pl["x"], pl["y"]))))
        for pl in plants:
            pp = (pl["x"], pl["y"])
            if ("water", pp[0], pp[1]) in claims:
                continue
            claims.add(("water", pp[0], pp[1]))
            return self._move_or_act(pos, pp, ["WATER"])
        return None

    def _act_harvest(self, pos, board, day, claims):
        p = self.params
        candidates = []
        for pl in board["plants"]:
            if self._harvestable_plant(pl, day):
                candidates.append((manhattan(pos, (pl["x"], pl["y"])),
                                   (pl["x"], pl["y"]), ["HARVEST"]))
        for a in board["animals"]:
            if a["yield_units"] >= p.get("harvest_animal_min", 2) or day >= p.get("terminal_day", 28):
                candidates.append((manhattan(pos, (a["x"], a["y"])),
                                   (a["x"], a["y"]), ["HARVEST"]))
        candidates.sort(key=lambda c: c[0])
        for _, target, action in candidates:
            if ("harvest", target[0], target[1]) in claims:
                continue
            claims.add(("harvest", target[0], target[1]))
            return self._move_or_act(pos, target, action)
        return None

    def _act_collect(self, pos, board, claims):
        ferts = [a for a in board["animals"] if a["fertilizer_available"]]
        if not ferts:
            return None
        ferts.sort(key=lambda a: manhattan(pos, (a["x"], a["y"])))
        for a in ferts:
            ap = (a["x"], a["y"])
            if ("fert", ap[0], ap[1]) in claims:
                continue
            claims.add(("fert", ap[0], ap[1]))
            return self._move_or_act(pos, ap, ["COLLECT_FERTILIZER"])
        return None

    def _act_care(self, pos, board, claims):
        uncared = [a for a in board["animals"] if not a["cared_today"]]
        if not uncared:
            return None
        uncared.sort(key=lambda a: manhattan(pos, (a["x"], a["y"])))
        for a in uncared:
            ap = (a["x"], a["y"])
            if ("care", ap[0], ap[1]) in claims:
                continue
            claims.add(("care", ap[0], ap[1]))
            return self._move_or_act(pos, ap, ["CARE"])
        return None

    def _act_start_herd(self, pos, inv, board, shed, day, claims):
        """Make progress on moving bought animals out of the shed."""
        on_board = {"SHEEP": 0, "COW": 0, "GOOSE": 0}
        for a in board["animals"]:
            t = a.get("animal")
            if t in on_board:
                on_board[t] += 1
        targets = {"SHEEP": self._effective_target(day, "sheep"),
                   "COW": self._effective_target(day, "cow"),
                   "GOOSE": self._effective_target(day, "goose")}

        # anything still needed, in shed, and not already being carried?
        for atype in ANIMAL_ORDER:
            needed = targets[atype] - on_board[atype]
            if needed <= 0:
                continue
            in_shed = int(shed.get(atype, 0) or 0)
            if in_shed <= 0:
                continue
            struct = ANIMALS[atype]["struct"]
            empty_struct = [s for s in board["structures"]
                            if s.get("type") == struct and not s.get("has_animal")]
            if empty_struct:
                # go pick the animal up (placement happens via priority 0)
                target = nearest_shed_tile(pos)
                return self._move_or_act(pos, target, ["PICKUP", atype, 1])
            # need to build a structure first
            target = self._nearest_empty(pos, board, claims, "build")
            if target:
                claims.add(("build", target[0], target[1]))
                return self._move_or_act(pos, target, ["BUILD_" + struct])
        return None

    def _act_plant(self, pos, board, seeds, day, hour, claims):
        # A seed planted on day D MUST be watered on day D (it starts at
        # consecutive_unwatered=1 and dies at the end-of-day refresh). Never
        # plant so late in the day that a fresh plant can't be watered.
        if hour >= self.params.get("plant_cutoff", 12):
            return None
        order = self._plant_priority(day)
        for crop in order:
            if int(seeds.get(crop, 0) or 0) <= 0:
                continue
            target = self._nearest_empty(pos, board, claims, "plant")
            if target:
                claims.add(("plant", target[0], target[1]))
                return self._move_or_act(pos, target, ["PLANT", crop])
            return None
        return None

    def _act_dig(self, pos, board, claims):
        if not board["weeds"]:
            return None
        target = min(board["weeds"], key=lambda w: manhattan(pos, w))
        return self._move_or_act(pos, target, ["DIG"])

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _harvestable_plant(pl, day):
        crop = pl["crop"]
        cd = CROPS.get(crop)
        if not cd:
            return False
        if pl["yield_units"] <= 0:
            return False
        age = day - pl["planted_day"]
        if cd["ongoing"]:
            return age >= cd["first"]
        # one-time: harvest at peak (watering is a higher priority, so the
        # final bonus lands before the harvest in the same turn).
        return age >= cd["max_day"]

    @staticmethod
    def _move_or_act(pos, target, action):
        if pos == target:
            return action
        return move_toward(pos, target)

    @staticmethod
    def _nearest_empty(pos, board, claims, claim_key):
        best = None
        for t in board["empty"]:
            if (claim_key, t[0], t[1]) in claims:
                continue
            d = manhattan(pos, t)
            if best is None or d < best[0]:
                best = (d, t)
        return best[1] if best else None

    def _plant_priority(self, day):
        p = self.params
        if day <= p.get("slow_crop_days", 2):
            return ["MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"]
        weights = [
            ("WHEAT", p.get("crop_wheat", 0.5)),
            ("MELON", p.get("crop_melon", 0.25)),
            ("STRAWBERRY", p.get("crop_straw", 0.2)),
            ("CARROT", p.get("crop_carrot", 0.05)),
            ("TOMATO", p.get("crop_tomato", 0.0)),
        ]
        weights.sort(key=lambda x: -x[1])
        return [c for c, w in weights if w > 0]

    def _land_density_ok(self, board, unlocked):
        """True if the currently-owned land is mostly occupied.

        Keeps the farm compact so the reactive workers don't spend all their
        time walking across an empty, unmanageable board.
        """
        occupied = len(board["plants"]) + len(board["structures"]) + len(board["weeds"])
        total = 25 * len(unlocked)
        if total <= 0:
            return False
        return occupied / total >= self.params.get("land_density", 0.60)

    def _effective_target(self, day, kind):
        """Ramp the animal target from `target_<kind>` to `final_<kind>`."""
        p = self.params
        early = int(p.get("target_" + kind, 0) or 0)
        final = int(p.get("final_" + kind, early) or early)
        start = int(p.get(kind + "_ramp_start", 0) or 0)
        end = int(p.get(kind + "_ramp_end", 0) or 0)
        if end <= start:
            return final
        frac = min(1.0, max(0.0, (day - start) / (end - start)))
        return int(round(early + (final - early) * frac))


# ----------------------------------------------------------------------------
# Kaggle entry point (identical interface to v1).
# ----------------------------------------------------------------------------
_params = None
_agents = {}


def agent(obs, configuration=None):
    global _params, _agents
    if _params is None:
        _params = dict(DEFAULT_PARAMS)
    seat = int(obs.get("player", 0) or 0)
    if seat not in _agents:
        _agents[seat] = DecisionAgent(_params, seat)
    return _agents[seat].act(obs, configuration)


def set_params(params):
    global _params, _agents
    _params = params
    _agents = {}


def _pass_agent(obs, config=None):
    farm = obs["farms"][obs["player"]]
    n = len(farm.get("hands", []) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}


if __name__ == "__main__":
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
    result = env.run([agent, _pass_agent])
    final = result[-1]
    money = final[0]["observation"]["farms"][0]["money"]
    print(f"Decision Agent v2 vs PASS (seed 1): ${money:,.0f}")
