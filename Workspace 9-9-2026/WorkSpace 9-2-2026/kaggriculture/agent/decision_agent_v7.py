"""
Decision Agent v7 — "Aware" — a farmer that plans the whole day before it
steps into the field.

The model is a REAL FARMER, not a reactive worker:
  * It KNOWS its field: it tracks every crop (where, planted when, watered
    when), every animal (placed when, fed today?, next production), the shed,
    seeds, money, and the days remaining.
  * It KNOWS the rules (scripts/rules.py): a crop needs water on its planting
    day and every day after; an animal needs feed daily; a plant sowed at hour
    22 must be watered at hour 23; a melon needs 10 days, wheat 4, a
    strawberry pays over 16 days — so "what to plant" depends on the days
    left AND the match (prices, opponent).
  * It BUILDS THE DAY as a timeline: every worker gets an ordered list of
    (tile, action) with movement simulated exactly (Manhattan — movement is
    never blocked), so a job is only accepted if it finishes by hour 24.
    Planting is scheduled as PLANT-then-WATER on the same tile, and the water
    slot is guaranteed before it ever plants. Nothing is "jump and find out".
  * It DECIDES ITS OWN CREW: if the day's must-do work (feed + water + harvest
    + fertilizer) doesn't fit the crew's hours, it hires more hands (fib cost)
    until it fits or it runs out of money.
  * ANTI-MIRROR: crop order / tile order / assignment rotate by a per-match
    signature (seat + opponent build + opening prices), so no two matches
    produce the same schedule — a copied "set build and timing" can never
    sync to us.
  * COUNTER (from v4): herd tilt away from the opponent's glut product,
    front-run sells, crop-mix counter.

Every plan is rebuilt each morning from the live board, so the schedule
self-corrects daily and can never desync the way a frozen tape does.
"""

from decision_agent_v2 import (
    DecisionAgent, DEFAULT_PARAMS, ANIMALS, ANIMAL_ORDER, SELL_ORDER, CROPS,
    SHED_TILES, manhattan, move_toward, nearest_shed_tile,
)
from collections import namedtuple

Job = namedtuple("Job", "op x y arg")

SHED_TILE_LIST = [(4, 4), (5, 4), (4, 5), (5, 5)]  # NWSE
SPAWN_SEQ = [(5, 4), (4, 5), (5, 5), (4, 4)]

# Days a crop needs before it's fully done (one-time: max_day; ongoing: last
# production day).
CROP_NEED = {"WHEAT": 4, "CARROT": 3, "MELON": 10, "STRAWBERRY": 16, "TOMATO": 11}
CROP_UNITS = {"WHEAT": 4, "CARROT": 3, "MELON": 6, "STRAWBERRY": 4, "TOMATO": 4}
GLUT_DISCOUNT = {"WHEAT": 0.85, "CARROT": 0.7, "MELON": 0.55,
                 "STRAWBERRY": 0.6, "TOMATO": 0.4}
BASE_PRICE = {"WHEAT": 25, "CARROT": 35, "MELON": 250, "STRAWBERRY": 120, "TOMATO": 60}

FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]


V7_DEFAULT_PARAMS = dict(DEFAULT_PARAMS)
V7_DEFAULT_PARAMS.update({
    "daily_hires": 4, "late_hires": 8, "late_day": 5,
    "land_density": 0.75, "sw_land_day": 12, "se_land_day": 18,
    "max_extra_hires": 4,
    "plant_max": 48,
    "wheat_batch": 5,
    "anti_mirror": True,
    "frontrun_pending": 3,
    "cow_shift": 2, "sheep_shift": 2, "min_cow_keep": 6,
})


class AwareAgent(DecisionAgent):
    def __init__(self, params=None, seat=0):
        super().__init__(params, seat)
        self._timelines = {}
        self._ptrs = {}
        self._extra_hires = 0
        self._sig = None
        self._opp = None
        self._memory = {"planted": {}, "last_day": -1, "log": []}

    # ------------------------------------------------------------------ act
    def act(self, obs, configuration=None):
        p = self.params
        player = int(obs.get("player", 0) or 0)
        day = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)

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
        self._last_prices = (obs.get("market") or {}).get("prices") or {}

        if hour == 0:
            if self._sig is None:
                self._sig = self._signature(obs)
            self._opp = self._scan_opponent(obs)
            self._remember_day(board, day)
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

    # ------------------------------------------------------------ awareness
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
        pending = {}
        for row in ofarm.get("tiles", []):
            for t in row:
                if isinstance(t, dict):
                    if t.get("animal"):
                        counts[t["animal"]] = counts.get(t["animal"], 0) + 1
                        prod = ANIMALS[t["animal"]]["product"]
                        pending[prod] = pending.get(prod, 0) + \
                            int(t.get("yield_units", 0) or 0)
                    elif t.get("kind") == "PLANT":
                        crops[t.get("crop")] = crops.get(t.get("crop"), 0) + 1
        return {"counts": counts, "crops": crops, "pending": pending}

    def _remember_day(self, board, day):
        """Keep a running memory of what we planted and when (the 'farmer
        knows their field' ledger)."""
        mem = self._memory
        if mem["last_day"] != day:
            mem["last_day"] = day
        for pl in board["plants"]:
            key = (pl["x"], pl["y"])
            if key not in mem["planted"]:
                mem["planted"][key] = {"crop": pl["crop"],
                                       "planted_day": pl["planted_day"]}

    # ------------------------------------------------------------ day plan
    def _plan_day(self, obs, board, seeds, shed, money, day):
        p = self.params
        farm = obs["farms"][int(obs.get("player", 0) or 0)]
        hires_today = int(farm.get("hires_today", 0) or 0)

        # ---- enumerate must-do work ----
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
        herd_prep = self._herd_prep_jobs(board, shed, day)

        # wheat we can count on today: in the shed now + what the hour-0 buy
        # will add (the scheduler must not plan pickups past it).
        n_animals = len(board["animals"])
        reserve = n_animals * p.get("wheat_reserve_per_animal", 2) + 2
        planned_wheat = int(shed.get("WHEAT", 0) or 0) + \
            min(20, max(0, (reserve + n_animals) - int(shed.get("WHEAT", 0) or 0)))

        # ---- choose crew size so MUST-DO fits ----
        base = p["daily_hires"] if day < p["late_day"] else p["late_hires"]

        best_extra = 0
        for extra in range(0, p.get("max_extra_hires", 4) + 1):
            n = 1 + base + extra
            workers, dropped = self._try_plan(n, herd_prep, must, planned_wheat)
            if dropped == 0:
                best_extra = extra
                break
            idx = hires_today + base + extra
            cost = FIB[idx] if idx < len(FIB) else FIB[-1]
            if money < cost + p["cash_buffer"]:
                best_extra = extra
                break
        self._extra_hires = best_extra

        # ---- final plan: herd prep + must-do, then growth in the slack ----
        n = 1 + base + self._extra_hires
        workers, _ = self._try_plan(n, herd_prep, must, planned_wheat)
        self._schedule_growth(workers, board, seeds, day)

        self._timelines = {i: w["plan"] for i, w in enumerate(workers)}
        self._ptrs = {i: 0 for i in range(len(workers))}

    def _herd_prep_jobs(self, board, shed, day):
        """Schedule build-pasture + pickup + PLACE as PLAN jobs (not reactive
        glue). The full walk cost is accounted, so the farmer's day never
        overruns and its feed jobs actually execute."""
        on_board = {"SHEEP": 0, "COW": 0, "GOOSE": 0}
        for a in board["animals"]:
            t = a.get("animal")
            if t in on_board:
                on_board[t] += 1
        jobs = []
        for atype in ANIMAL_ORDER:
            needed = self._effective_target(day, atype.lower()) - on_board[atype]
            while needed > 0 and int(shed.get(atype, 0) or 0) > 0:
                struct = ANIMALS[atype]["struct"]
                empty_struct = [s for s in board["structures"]
                                if s.get("type") == struct and not s.get("has_animal")]
                if not empty_struct:
                    if not board["empty_set"]:
                        break
                    t = min(board["empty_set"],
                            key=lambda t: min(manhattan(t, s) for s in SHED_TILES))
                    jobs.append(Job("BUILD_" + struct, t[0], t[1], None))
                    pasture = t
                else:
                    pasture = (empty_struct[0]["x"], empty_struct[0]["y"])
                st = (4, 4)
                jobs.append(Job("PICKUP", st[0], st[1], (atype, 1)))
                jobs.append(Job("PLACE", pasture[0], pasture[1], atype))
                needed -= 1
                if len(jobs) >= 6:
                    return jobs
        return jobs

    def _fresh_workers(self, n):
        workers = []
        for i in range(n):
            pos = (4, 4) if i == 0 else SPAWN_SEQ[(i - 1) % len(SPAWN_SEQ)]
            workers.append({"pos": pos, "busy": 0, "wheat": 0, "plan": []})
        return workers

    def _try_plan(self, n_workers, herd_prep, must_jobs, planned_wheat):
        """Greedy list scheduling with per-worker wheat bookkeeping.

        Herd-prep jobs are pre-assigned to the farmer (worker 0) in order, so
        the herd grows without preempting feeding. Then must-do jobs (feed /
        water / fert / harvest) are scheduled so each finishes by hour 24.
        Feed jobs require a wheat pickup (walk to the shed, +1); the shared
        `planned_wheat` budget is decremented per unit picked up, so the plan
        never assumes wheat that won't exist.

        Movement is exact Manhattan distance, so this is the true completion
        estimate. Returns (workers, n_dropped).
        """
        workers = self._fresh_workers(n_workers)
        batch = self.params.get("wheat_batch", 5)
        shed_wheat = int(planned_wheat)
        dropped = 0

        # pre-assign herd prep to the farmer
        for job in herd_prep:
            w = workers[0]
            d = manhattan(w["pos"], (job.x, job.y))
            if w["busy"] + d + 1 > 24:
                break
            w["plan"].append(job)
            w["busy"] += d + 1
            w["pos"] = (job.x, job.y)

        for job in must_jobs:
            placed = False
            if job.op == "FEED":
                best = None
                for w in workers:
                    if w["wheat"] > 0:
                        d = manhattan(w["pos"], (job.x, job.y))
                        c = d + 1
                        need_pickup = False
                    else:
                        st = min(SHED_TILES, key=lambda s: manhattan(w["pos"], s))
                        d1 = manhattan(w["pos"], st)
                        d2 = manhattan(st, (job.x, job.y))
                        c = d1 + 1 + d2 + 1
                        need_pickup = True
                        if w["busy"] == 0:      # never pick up at hour 0
                            c += 1
                    if w["busy"] + c <= 24 and (need_pickup is False or shed_wheat > 0):
                        if best is None or c < best[0]:
                            best = (c, w, need_pickup)
                if best is not None:
                    c, w, need_pickup = best
                    if need_pickup:
                        st = min(SHED_TILES, key=lambda s: manhattan(w["pos"], s))
                        if w["busy"] == 0:
                            w["plan"].append(Job("PASS", w["pos"][0], w["pos"][1], None))
                            w["busy"] += 1
                        w["plan"].append(Job("PICKUP", st[0], st[1], ("WHEAT", batch)))
                        w["busy"] += manhattan(w["pos"], st) + 1
                        w["pos"] = st
                        got = min(batch, shed_wheat)
                        w["wheat"] += got
                        shed_wheat -= got
                    w["plan"].append(job)
                    w["busy"] += manhattan(w["pos"], (job.x, job.y)) + 1
                    w["wheat"] -= 1
                    w["pos"] = (job.x, job.y)
                    placed = True
            else:
                best = None
                for w in workers:
                    d = manhattan(w["pos"], (job.x, job.y))
                    c = d + 1
                    if w["busy"] + c <= 24:
                        if best is None or c < best[0]:
                            best = (c, w)
                if best is not None:
                    c, w = best
                    w["plan"].append(job)
                    w["busy"] += c
                    w["pos"] = (job.x, job.y)
                    placed = True
            if not placed:
                dropped += 1
        return workers, dropped

    def _schedule_growth(self, workers, board, seeds, day):
        """Plant/care/dig in remaining slack. A plant is only accepted if the
        SAME-DAY WATER slot also fits (plant then water on the same tile)."""
        p = self.params
        vseeds = {c: int(seeds.get(c, 0) or 0) for c in CROPS}
        standing = len(board["plants"])
        claimed = set()

        # empty tiles near-shed-first (short walks); anti-mirror rotates the
        # crop choice, not the tile order.
        empties = sorted(board["empty_set"], key=lambda t: min(
            manhattan(t, s) for s in SHED_TILES))

        for t in empties:
            if standing >= p.get("plant_max", 48):
                break
            if t in claimed:
                continue
            crop = self._pick_crop(vseeds, day)
            if crop is None:
                break
            # find a worker that can walk there, PLANT, then WATER same day
            best = None
            for w in workers:
                d = manhattan(w["pos"], t)
                if w["busy"] + d + 2 <= 24:
                    if best is None or d < best[0]:
                        best = (d, w)
            if best is None:
                break
            d, w = best
            vseeds[crop] -= 1
            w["plan"].append(Job("PLANT", t[0], t[1], crop))
            w["plan"].append(Job("WATER", t[0], t[1], None))
            w["busy"] += d + 2
            w["pos"] = t
            claimed.add(t)
            standing += 1

        # care (production bonus) — cheap, do if slack remains
        for a in board["animals"]:
            if a["cared_today"]:
                continue
            best = None
            for w in workers:
                d = manhattan(w["pos"], (a["x"], a["y"]))
                if w["busy"] + d + 1 <= 24:
                    if best is None or d < best[0]:
                        best = (d, w)
            if best is None:
                break
            d, w = best
            w["plan"].append(Job("CARE", a["x"], a["y"], None))
            w["busy"] += d + 1
            w["pos"] = (a["x"], a["y"])

        # dig weeds
        for t in sorted(board["weedset"], key=lambda t: min(
                manhattan(t, s) for s in SHED_TILES)):
            best = None
            for w in workers:
                d = manhattan(w["pos"], t)
                if w["busy"] + d + 1 <= 24:
                    if best is None or d < best[0]:
                        best = (d, w)
            if best is None:
                continue
            d, w = best
            w["plan"].append(Job("DIG", t[0], t[1], None))
            w["busy"] += d + 1
            w["pos"] = t

    # -------------------------------------------------------- crop choice
    def _pick_crop(self, vseeds, day):
        """Choose the best crop given the days left, prices, and opponent."""
        p = self.params
        prices = getattr(self, "_last_prices", None) or {}
        scores = []
        for crop, need in CROP_NEED.items():
            if vseeds.get(crop, 0) <= 0:
                continue
            if day + need > 29:
                continue
            price = prices.get(crop, BASE_PRICE[crop])
            rev = CROP_UNITS[crop] * price * GLUT_DISCOUNT[crop]
            if day <= 3 and crop in ("STRAWBERRY", "MELON"):
                rev *= 1.5          # long crops must be sown early
            if crop == "MELON" and day >= 19:
                continue            # can't mature
            if crop == "STRAWBERRY" and day >= 14:
                continue
            net = rev - CROPS[crop]["seed"]
            scores.append((net, crop))
        if not scores:
            return None
        scores.sort(reverse=True)
        # anti-mirror: if the top two are close, rotate by the match signature
        if self.params.get("anti_mirror", True) and len(scores) >= 2 and self._sig is not None:
            if abs(scores[0][0] - scores[1][0]) < 0.2 * scores[0][0]:
                if self._sig % 2:
                    scores = [scores[1], scores[0]] + scores[2:]
        return scores[0][1]

    # ------------------------------------------------------------ execution
    def _execute(self, idx, pos, inv, board, shed, seeds, day, hour, claims):
        # NOTE: herd growth is fully scheduled (BUILD -> PICKUP -> PLACE jobs);
        # nothing reactive preempts the plan. Carrying animals are placed by
        # the PLACE jobs themselves.
        plan = self._timelines.get(idx) or []
        ptr = self._ptrs.get(idx, 0)
        while ptr < len(plan) and self._job_stale(plan[ptr], board):
            ptr += 1
        self._ptrs[idx] = ptr

        if ptr < len(plan):
            job = plan[ptr]
            t = (job.x, job.y)
            if job.op == "PASS":
                self._ptrs[idx] = ptr + 1
                return ["PASS"]
            if job.op == "PICKUP":
                if pos == t:
                    self._ptrs[idx] = ptr + 1
                    item, n = job.arg
                    return ["PICKUP", item, n]
                return move_toward(pos, t)
            if pos == t:
                self._ptrs[idx] = ptr + 1
                if job.arg is None:
                    return [job.op]
                return [job.op, job.arg]
            return move_toward(pos, t)

        # plan finished — safety: water anything still dry (shouldn't happen)
        a = self._act_water(pos, board, claims, True)
        if a: return a
        return ["PASS"]

    @staticmethod
    def _job_stale(job, board):
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
            return board["grid"].get((job.x, job.y)) is not None
        if job.op == "DIG":
            return (job.x, job.y) not in board.get("weedset", set())
        if job.op == "CARE":
            d = board["grid"].get((job.x, job.y))
            return not (d and d.get("animal") and not d.get("cared_today"))
        if job.op == "PLACE":
            d = board["grid"].get((job.x, job.y))
            struct = ANIMALS.get(job.arg, {}).get("struct")
            return not (d and d.get("type") == struct and not d.get("has_animal"))
        if job.op == "BUILD_PASTURE" or job.op == "BUILD_COOP":
            return board["grid"].get((job.x, job.y)) is not None
        return False

    # -------------------------------------------------------------- market
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

        # ---- hour 1: animals FIRST (the income engine), then seeds, then
        #      land — with a running cash budget so one morning can't blow
        #      the whole bank. ----
        if hour == 1 and not terminal:
            cash = money
            LAND_PRICE = {"NE": 1000, "SW": 2000, "SE": 4000}

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

            if int(seeds.get("WHEAT", 0) or 0) <= 2 and cash >= buf + 150 \
                    and len(orders) < 10:
                orders.append(["BUY_SEED", "WHEAT", 6])
                cash -= 60
            if int(seeds.get("MELON", 0) or 0) == 0 \
                    and day < p.get("melon_last_day", 14) and cash >= buf + 400 \
                    and len(orders) < 10:
                orders.append(["BUY_SEED", "MELON", 2])
                cash -= 160
            if int(seeds.get("STRAWBERRY", 0) or 0) == 0 \
                    and day < p.get("straw_last_day", 8) and cash >= buf + 300 \
                    and len(orders) < 10:
                orders.append(["BUY_SEED", "STRAWBERRY", 2])
                cash -= 200

            for quad, key in [("NE", "ne_land_day"), ("SW", "sw_land_day"),
                              ("SE", "se_land_day")]:
                if p.get(key, -1) >= 0 and day >= p[key] and quad not in unlocked \
                        and cash >= LAND_PRICE[quad] + buf \
                        and self._land_density_ok(board, unlocked) \
                        and len(orders) < 10:
                    orders.append(["BUY_LAND"])
                    cash -= LAND_PRICE[quad]

            return orders[:10]

        # ---- selling (front-run + daily + terminal) ----
        if self.params.get("frontrun_enabled", True) and self._opp is not None \
                and not terminal and hour == p.get("sell_hour", 2):
            for item in SELL_ORDER:
                if len(orders) >= 10:
                    break
                if self._opp["pending"].get(item, 0) < p.get("frontrun_pending", 3):
                    continue
                q = int(shed.get(item, 0) or 0)
                if item == "WHEAT":
                    q = max(0, q - reserve)
                if q > 0:
                    orders.insert(0, ["SELL", item, q])

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

    # ------------------------------------------------------ v4 counter tilt
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
        _params = dict(V7_DEFAULT_PARAMS)
    seat = int(obs.get("player", 0) or 0)
    if seat not in _agents:
        _agents[seat] = AwareAgent(_params, seat)
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
    print(f"Decision Agent v7 vs PASS (seed 1): ${money:,.0f}")
