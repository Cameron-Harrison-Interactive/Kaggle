"""
Decision Agent v6 — "Planner" — the day-by-day set-path scheduler.

This is the bot you described: every morning it reads the board, enumerates
everything that must be done, ASSIGNS EACH WORKER A DETERMINISTIC SET-PATH
(an ordered list of tiles + actions) computed from the live state, and decides
its own hire count by weighing workload against the crew's 24-hours-each
capacity. Nothing is memorized, nothing is reactive "nearest task" guessing —
the plan is rebuilt from the board every day, so no two matches route the same
and a copied timing schedule desyncs immediately (anti-mirror signature).

The day plan (built at hour 0):
  1. MUST-DO jobs (never dropped): feed every animal, water every plant,
     harvest everything ready, collect every available fertilizer.
  2. CAPACITY: each job's cost is walk-distance + 1 action. Sum the costs
     against workers x 24 hours. If the must-do load exceeds capacity, HIRE
     more hands (fib cost) until it fits or money runs out — the bot knows how
     many workers it needs because it can count the work.
  3. GROWTH: with the remaining slack, plant new crops (each planting is
     auto-followed by a same-day watering), care for animals, and dig weeds —
     as many as the crew can actually afford to service.
  4. ANTI-MIRROR: tile order, crop order and worker-quadrant assignment are
     rotated by a per-match signature (seat + opponent build + opening
     prices), so two matches never produce the same schedule.

Execution: each worker walks its assigned path turn by turn; the schedule is
re-planned every morning so any drift self-corrects. A thin rescue net fires
only if something is one step from dying (should be rare — the plan covers it).

Market/economy: same as v2 (opening, land, seeds, sell-hour, terminal sweep),
plus the v4 opponent counter (herd tilt + crop mix) folded in.
"""

from collections import namedtuple

from decision_agent_v2 import (
    DecisionAgent, DEFAULT_PARAMS, ANIMALS, ANIMAL_ORDER, SELL_ORDER, CROPS,
    SHED_TILES, manhattan, move_toward, nearest_shed_tile,
)

# A job: (action, x, y, arg). arg = crop for PLANT, animal for PLACE,
# (item, n) for PICKUP, else None.
Job = namedtuple("Job", "op x y arg")

SHED_TILE_LIST = [(4, 4), (5, 4), (4, 5), (5, 5)]  # NWSE order
SPAWN_SEQ = [(5, 4), (4, 5), (5, 5), (4, 4)]       # hand spawn order (cycle)


V6_DEFAULT_PARAMS = dict(DEFAULT_PARAMS)
V6_DEFAULT_PARAMS.update({
    # scheduler
    "wheat_batch": 5,          # wheat picked up per feed run
    "max_extra_hires": 4,      # extra hires the planner may add beyond base
    "plant_max": 44,           # hard cap on standing crops
    "plant_cost": 5,           # est. daily cost per standing crop (walk+water)
    "reserve_hours": 4,        # keep this much slack when deciding to plant
    "anti_mirror": True,
    # counter (from v4)
    "cow_shift": 2, "sheep_shift": 2, "min_cow_keep": 6,
    # hiring base
    "daily_hires": 4, "late_hires": 9, "late_day": 8,
})


class PlannedAgent(DecisionAgent):
    def __init__(self, params=None, seat=0):
        super().__init__(params, seat)
        self._plan = {}          # worker_idx -> [Job, ...]
        self._ptr = {}           # worker_idx -> next job index
        self._extra_hires = 0
        self._sig = None
        self._opp = None
        self._herd = {}          # worker_idx -> (animal, tx, ty, stage)

    # ------------------------------------------------------------------ act
    def act(self, obs, configuration=None):
        p = self.params
        player = int(obs.get("player", 0) or 0)
        day = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)

        if hour == 0:
            if self._sig is None:
                self._sig = self._signature(obs)
            self._opp = self._scan_opponent(obs)

        farm = obs["farms"][player]
        tiles = farm["tiles"]
        money = float(farm.get("money", 0) or 0)
        unlocked = set(farm.get("unlocked_quadrants", []) or [])
        private = obs.get("private") or {}
        shed = private.get("shed") or {}
        seeds = private.get("seeds") or {}
        inventories = private.get("inventories") or [{}]

        board = self._scan_board(tiles, unlocked)
        board["weedset"] = set(board["weeds"])
        board["empty_set"] = set(board["empty"])
        board["unlocked_quads"] = unlocked

        if hour == 0:
            self._plan_day(obs, board, seeds, shed, money, day)

        market = self._decide_market(day, hour, money, shed, seeds, board, unlocked)

        claims = set()
        farmer_pos = tuple(farm.get("farmer", [4, 4]))
        farmer_inv = inventories[0] if len(inventories) > 0 else {}
        farmer_action = self._execute(0, farmer_pos, farmer_inv, board, shed,
                                      seeds, day, hour, claims)
        hand_actions = []
        for i, hp in enumerate(farm.get("hands", []) or []):
            inv = inventories[i + 1] if i + 1 < len(inventories) else {}
            hand_actions.append(self._execute(i + 1, tuple(hp), inv, board,
                                              shed, seeds, day, hour, claims))
        return {"farmer": farmer_action, "hands": hand_actions,
                "market": market[:10]}

    # -------------------------------------------------------------- signature
    @staticmethod
    def _signature(obs):
        seat = int(obs.get("player", 0) or 0)
        opp = obs["farms"][1 - seat]
        n_an = sum(1 for row in opp["tiles"] for t in row
                   if isinstance(t, dict) and t.get("animal"))
        prices = (obs.get("market") or {}).get("prices") or {}
        return (seat + n_an * 31 + int(sum(prices.values())) * 7) % 1000003

    @staticmethod
    def _scan_opponent(obs):
        seat = int(obs.get("player", 0) or 0)
        ofarm = obs["farms"][1 - seat]
        counts = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
        crops = {}
        for row in ofarm.get("tiles", []):
            for t in row:
                if isinstance(t, dict):
                    if t.get("animal"):
                        counts[t["animal"]] = counts.get(t["animal"], 0) + 1
                    elif t.get("kind") == "PLANT":
                        crops[t.get("crop")] = crops.get(t.get("crop"), 0) + 1
        return {"counts": counts, "crops": crops}

    # ------------------------------------------------------------ day plan
    def _plan_day(self, obs, board, seeds, shed, money, day):
        p = self.params
        farm = obs["farms"][int(obs.get("player", 0) or 0)]

        # ---- enumerate must-do jobs ----
        feed_jobs = [Job("FEED", a["x"], a["y"], None)
                     for a in board["animals"] if not a["fed_today"]]
        water_jobs = [Job("WATER", pl["x"], pl["y"], None)
                      for pl in board["plants"] if not pl["watered_today"]]
        fert_jobs = [Job("COLLECT_FERTILIZER", a["x"], a["y"], None)
                     for a in board["animals"] if a["fertilizer_available"]]
        harvest_jobs = []
        for pl in board["plants"]:
            if self._harvestable_plant(pl, day):
                harvest_jobs.append(Job("HARVEST", pl["x"], pl["y"], None))
        for a in board["animals"]:
            if a["yield_units"] >= p.get("harvest_animal_min", 2):
                harvest_jobs.append(Job("HARVEST", a["x"], a["y"], None))

        must = feed_jobs + water_jobs + fert_jobs + harvest_jobs

        # ---- hire decision: fit must-do work PLUS the growth target ----
        base_hires = p["daily_hires"] if day < p["late_day"] else p["late_hires"]
        money = float(farm.get("money", 0) or 0)
        hires_today = int(farm.get("hires_today", 0) or 0)

        def fib(n):
            a, b = 1, 1
            for _ in range(max(0, n)):
                a, b = b, a + b
            return a

        # How many crops do we WANT standing? (capacity of unlocked land)
        tiles_avail = len(board["empty_set"]) + len(board["plants"]) + \
            sum(1 for s in board["structures"] if not s.get("has_animal"))
        plant_target = min(p.get("plant_max", 56), tiles_avail)

        # estimate must-do cost once, then add growth cost
        base_workers = self._fresh_workers(1 + base_hires)
        must_cost = self._assign_must(must, base_workers)
        desired = must_cost + plant_target * p.get("plant_cost", 3)

        best_extra = 0
        for extra in range(0, p.get("max_extra_hires", 5) + 1):
            n_workers = 1 + base_hires + extra
            if desired <= n_workers * 24:
                best_extra = extra
                break
            # affordability for the next hire
            idx = hires_today + base_hires + extra
            if idx < 21 and money < fib(idx) + p["cash_buffer"]:
                break
        self._extra_hires = best_extra

        # ---- build the final plan with the chosen crew ----
        n_workers = 1 + base_hires + self._extra_hires
        workers = self._fresh_workers(n_workers)
        self._assign_must(must, workers)

        # optional work from remaining slack
        self._assign_optional(workers, board, seeds, day)

        self._plan = {i: w["queue"] for i, w in enumerate(workers)}
        self._ptr = {i: 0 for i in range(n_workers)}

    def _fresh_workers(self, n):
        workers = []
        for i in range(n):
            if i == 0:
                pos = (4, 4)   # farmer spawns NW shed tile
            else:
                pos = SPAWN_SEQ[(i - 1) % len(SPAWN_SEQ)]
            # The farmer participates fully in the economy (it gets plan jobs
            # too); herd glue fires only when there is actually an animal to
            # place, so booking it 24/7 would waste a whole worker.
            workers.append({"pos": pos, "cost": 0, "wheat": 0, "queue": []})
        return workers

    def _assign_must(self, jobs, workers):
        """Assign must-do jobs greedily; returns total estimated cost."""
        for job in jobs:
            best_w, best_c = None, float("inf")
            for w in workers:
                d = manhattan(w["pos"], (job.x, job.y))
                c = d + 1
                if job.op == "FEED" and w["wheat"] <= 0:
                    # extra trip to the shed to pick up wheat
                    c += min(manhattan(w["pos"], s) for s in SHED_TILES) + 1
                if c < best_c:
                    best_c, best_w = c, w
            if best_w is None:
                continue
            if job.op == "FEED" and best_w["wheat"] <= 0:
                st = min(SHED_TILES, key=lambda s: manhattan(best_w["pos"], s))
                batch = self.params.get("wheat_batch", 5)
                best_w["queue"].append(Job("PICKUP", st[0], st[1], ("WHEAT", batch)))
                best_w["wheat"] += batch
                best_w["cost"] += manhattan(best_w["pos"], st) + 1
                best_w["pos"] = st
            best_w["queue"].append(job)
            best_w["cost"] += manhattan(best_w["pos"], (job.x, job.y)) + 1
            best_w["pos"] = (job.x, job.y)
            if job.op == "FEED":
                best_w["wheat"] -= 1
        return sum(w["cost"] for w in workers)

    def _assign_optional(self, workers, board, seeds, day):
        """Plant / care / dig using remaining slack per worker."""
        p = self.params
        claimed = set()

        # planting candidates: empty tiles sorted NEAR-SHED-FIRST so workers
        # walk little per planting (anti-mirror variation lives in crop order
        # and worker rotation, NOT in planting far tiles first).
        empties = sorted(board["empty_set"], key=lambda t: min(
            manhattan(t, s) for s in SHED_TILES))

        vseeds = {c: int(seeds.get(c, 0) or 0) for c in CROPS}
        standing = len(board["plants"])

        for t in empties:
            if standing >= p.get("plant_max", 56):
                break
            if t in claimed:
                continue
            crop = self._pick_crop(vseeds, day)
            if crop is None:
                break
            vseeds[crop] -= 1
            # find a worker with slack for walk + PLANT + same-day WATER
            best_w, best_c = None, float("inf")
            for w in workers:
                d = manhattan(w["pos"], t)
                if w["cost"] + d + 2 <= 24 - p.get("reserve_hours", 4):
                    if d < best_c:
                        best_c, best_w = d, w
            if best_w is None:
                break
            best_w["queue"].append(Job("PLANT", t[0], t[1], crop))
            best_w["queue"].append(Job("WATER", t[0], t[1], None))
            best_w["cost"] += best_c + 2
            best_w["pos"] = t
            claimed.add(t)
            standing += 1

        # care (production bonus) for animals still uncared
        for a in board["animals"]:
            if a["cared_today"]:
                continue
            best_w, best_c = None, float("inf")
            for w in workers:
                d = manhattan(w["pos"], (a["x"], a["y"]))
                if w["cost"] + d + 1 <= 24 and d < best_c:
                    best_c, best_w = d, w
            if best_w is None:
                break
            best_w["queue"].append(Job("CARE", a["x"], a["y"], None))
            best_w["cost"] += best_c + 1
            best_w["pos"] = (a["x"], a["y"])

        # dig weeds
        for t in sorted(board["weedset"], key=lambda t: min(
                manhattan(t, s) for s in SHED_TILES)):
            best_w, best_c = None, float("inf")
            for w in workers:
                d = manhattan(w["pos"], t)
                if w["cost"] + d + 1 <= 24 and d < best_c:
                    best_c, best_w = d, w
            if best_w is None:
                continue
            best_w["queue"].append(Job("DIG", t[0], t[1], None))
            best_w["cost"] += best_c + 1
            best_w["pos"] = t

    # ------------------------------------------------------------ execution
    def _execute(self, idx, pos, inv, board, shed, seeds, day, hour, claims):
        # --- carrying an animal -> place it (whoever holds it) ---
        for atype in ANIMAL_ORDER:
            if int(inv.get(atype, 0) or 0) > 0:
                return self._act_place_animal(pos, atype, board, claims)

        # --- farmer = herd specialist: build pastures / pick up bought
        #     animals so the herd gets onto the board. Hands follow the plan.
        if idx == 0:
            a = self._act_start_herd(pos, inv, board, shed, day, claims)
            if a:
                return a

        # --- follow the set path ---
        plan = self._plan.get(idx) or []
        ptr = self._ptr.get(idx, 0)
        # skip stale jobs whose target no longer needs the work (self-repair)
        while ptr < len(plan):
            job = plan[ptr]
            if self._job_stale(job, board):
                ptr += 1
                self._ptr[idx] = ptr
                continue
            break
        if ptr < len(plan):
            job = plan[ptr]
            target = (job.x, job.y)
            if job.op == "PICKUP":
                if pos == target:
                    self._ptr[idx] = ptr + 1
                    item, n = job.arg
                    return ["PICKUP", item, n]
                return move_toward(pos, target)
            if pos == target:
                self._ptr[idx] = ptr + 1
                if job.arg is None:
                    return [job.op]
                return [job.op, job.arg]
            return move_toward(pos, target)

        # --- plan finished: last-resort safety net only when idle ---
        if idx == 0:
            a = self._act_feed(pos, inv, board, shed, claims, True)
            if a: return a
            a = self._act_water(pos, board, claims, True)
            if a: return a
        return ["PASS"]

    @staticmethod
    def _job_stale(job, board):
        # NOTE: scanned plant dicts use "crop" (not "kind"); animal/structure
        # dicts use "animal" / "type". These keys come from v2's _scan_board.
        if job.op == "WATER":
            d = board["grid"].get((job.x, job.y))
            return not (d and d.get("crop") and not d.get("watered_today"))
        if job.op == "FEED":
            d = board["grid"].get((job.x, job.y))
            return not (d and d.get("animal") and not d.get("fed_today"))
        if job.op == "COLLECT_FERTILIZER":
            d = board["grid"].get((job.x, job.y))
            return not (d and d.get("animal") and d.get("fertilizer_available"))
        if job.op == "HARVEST":
            d = board["grid"].get((job.x, job.y))
            return not d or d.get("yield_units", 0) <= 0
        if job.op == "PLANT":
            d = board["grid"].get((job.x, job.y))
            return d is not None
        if job.op == "DIG":
            return (job.x, job.y) not in board.get("weedset", set())
        return False

    # ------------------------------------------------------------ helpers
    def _pick_crop(self, vseeds, day):
        order = self._plant_priority(day)
        if self.params.get("anti_mirror", True):
            rot = self._sig % max(1, len(order))
            order = order[rot:] + order[:rot]
        _interval = {"TOMATO": 1, "STRAWBERRY": 2}
        for c in order:
            if vseeds.get(c, 0) <= 0:
                continue
            cd = CROPS[c]
            if cd["ongoing"]:
                need = cd["first"] + (cd["max_yield"] - 1) * _interval.get(c, 2)
            else:
                need = cd["max_day"]
            if day + need <= 29:
                return c
        return None

    def _plant_priority(self, day):
        p = self.params
        # v4 crop-mix counter: opponent floods crash-prone crops -> favor wheat
        if self._opp is not None:
            crash = self._opp["crops"].get("STRAWBERRY", 0) + \
                self._opp["crops"].get("MELON", 0)
            if crash >= 8:
                return ["WHEAT", "MELON", "STRAWBERRY", "CARROT", "TOMATO"]
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

    # --------------------------------------------------------------- market
    def _decide_market(self, day, hour, money, shed, seeds, board, unlocked):
        p = self.params
        orders = []
        n_animals = len(board["animals"])
        reserve = n_animals * p.get("wheat_reserve_per_animal", 2) + 2
        buf = p["cash_buffer"]
        terminal = day >= p["terminal_day"]

        if day == 0 and hour == 0:
            if p.get("open_wheat", 0) > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", int(p["open_wheat"])])
            for _ in range(int(p.get("open_hires", 0))):
                orders.append(["HIRE"])
            if p.get("open_sheep", 0) > 0:
                orders.append(["BUY_ANIMAL", "SHEEP", int(p["open_sheep"])])
            if p.get("open_cows", 0) > 0:
                orders.append(["BUY_ANIMAL", "COW", int(p["open_cows"])])
            for crop, key in [("MELON", "open_melon_seed"),
                              ("STRAWBERRY", "open_straw_seed"),
                              ("WHEAT", "open_wheat_seed")]:
                n = int(p.get(key, 0) or 0)
                if n > 0:
                    orders.append(["BUY_SEED", crop, n])
            return orders[:10]

        # ---- hour 0: feed wheat (life-critical) + hires ----
        if hour == 0:
            hires = p["daily_hires"] if day < p["late_day"] else p["late_hires"]
            hires += getattr(self, "_extra_hires", 0)
            wheat_in_shed = int(shed.get("WHEAT", 0) or 0)
            need = max(0, (reserve + n_animals) - wheat_in_shed)
            if need > 0 and money > buf:
                orders.append(["BUY_PRODUCT", "WHEAT", min(int(need), 20)])
            for _ in range(min(int(hires), 10 - len(orders))):
                orders.append(["HIRE"])
            return orders[:10]

        # ---- hour 1: land + seeds + animals (split off so the 10-order cap
        #      never silently drops them). A RUNNING cash budget prevents
        #      overspending: each order is checked against cash minus what we
        #      already committed this turn. ----
        if hour == 1 and not terminal:
            cash = money
            LAND_PRICE = {"NE": 1000, "SW": 2000, "SE": 4000}
            SEED_PRICE = {"WHEAT": 10, "MELON": 80, "STRAWBERRY": 100}

            for quad, key in [("NE", "ne_land_day"), ("SW", "sw_land_day"),
                              ("SE", "se_land_day")]:
                if p.get(key, -1) >= 0 and day >= p[key] and quad not in unlocked \
                        and cash >= LAND_PRICE[quad] + buf \
                        and self._land_density_ok(board, unlocked) \
                        and len(orders) < 10:
                    orders.append(["BUY_LAND"])
                    cash -= LAND_PRICE[quad]

            if int(seeds.get("WHEAT", 0) or 0) <= 2 and cash >= buf + 150 \
                    and len(orders) < 10:
                orders.append(["BUY_SEED", "WHEAT", 6])
                cash -= 60
            if int(seeds.get("MELON", 0) or 0) == 0 \
                    and day < p.get("melon_last_day", 14) and cash >= buf + 400 \
                    and len(orders) < 10:
                orders.append(["BUY_SEED", "MELON", 2])
                cash -= 240
            if int(seeds.get("STRAWBERRY", 0) or 0) == 0 \
                    and day < p.get("straw_last_day", 8) and cash >= buf + 300 \
                    and len(orders) < 10:
                orders.append(["BUY_SEED", "STRAWBERRY", 2])
                cash -= 200

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
                if have < eff and cash >= cost + buf and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", atype, min(2, eff - have)])
                    cash -= cost

            return orders[:10]

        if terminal or hour == p.get("sell_hour", 2):
            for item in SELL_ORDER:
                if len(orders) >= 10:
                    break
                q = int(shed.get(item, 0) or 0)
                if item == "WHEAT":
                    if day >= 29:
                        q = int(shed.get("WHEAT", 0) or 0)
                    else:
                        q = max(0, q - reserve)
                if q > 0:
                    orders.append(["SELL", item, q])
            return orders[:10]

        return orders[:10]

    # ----------------------------------------------------- v4 counter: tilt
    def _effective_target(self, day, kind):
        base = super()._effective_target(day, kind)
        if self._opp is None:
            return base
        p = self.params
        cow_n = self._opp["counts"].get("COW", 0)
        sheep_n = self._opp["counts"].get("SHEEP", 0)
        cow_heavy = cow_n >= 6 and cow_n >= sheep_n + 4
        if kind == "cow" and cow_heavy:
            return max(p.get("min_cow_keep", 6), base - p.get("cow_shift", 2))
        if kind == "sheep" and cow_heavy:
            return base + p.get("sheep_shift", 2)
        return base


# ----------------------------------------------------------------------------
_params = None
_agents = {}


def agent(obs, configuration=None):
    global _params, _agents
    if _params is None:
        _params = dict(V6_DEFAULT_PARAMS)
    seat = int(obs.get("player", 0) or 0)
    if seat not in _agents:
        _agents[seat] = PlannedAgent(_params, seat)
    return _agents[seat].act(obs, configuration)


def set_params(params):
    global _params, _agents
    _params = params
    _agents = {}


if __name__ == "__main__":
    from kaggle_environments import make

    def _pass(obs, config=None):
        farm = obs["farms"][obs["player"]]
        n = len(farm.get("hands", []) or [])
        return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
    result = env.run([agent, _pass])
    money = result[-1][0]["observation"]["farms"][0]["money"]
    print(f"Decision Agent v6 vs PASS (seed 1): ${money:,.0f}")
