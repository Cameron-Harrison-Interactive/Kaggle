"""Counter-meta ROUTE COMPILER.

Generates a choreographed 719-turn route from a high-level spec:
- fixed spatial layout (pasture rings, crop interiors, melon/tomato plots)
- aggressive Seb-style economy (20 animals, wheat feed engine, cash cushion)
- zone-sweep worker scheduler (each worker owns a vertical strip; no crisscross)
- endgame premium push (late melons, tomatoes into the market vacuum)

Run:  python3 scripts/route_compiler.py [--out data/compiled_route.json]
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from kaggle_environments import make  # noqa: E402

# ----------------------------------------------------------------- spec -----
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
HIRES = {0: 7, 1: 8, 2: 9, 3: 10, 4: 11, 5: 12, 6: 12, 7: 12, 8: 12, 9: 12,
         10: 12, 11: 12, 12: 12, 13: 12, 14: 12, 15: 12, 16: 11, 17: 11,
         18: 11, 19: 11, 20: 11, 21: 10, 22: 10, 23: 10, 24: 9, 25: 9,
         26: 8, 27: 7, 28: 5, 29: 3}
ANIMAL_TARGETS = [(0, "COW", 2), (0, "SHEEP", 2), (3, "COW", 1), (4, "SHEEP", 1),
                  (5, "COW", 1), (6, "SHEEP", 2), (7, "COW", 1), (8, "SHEEP", 1),
                  (9, "COW", 2), (10, "SHEEP", 2), (11, "COW", 1), (12, "SHEEP", 1),
                  (13, "COW", 1), (14, "SHEEP", 2), (16, "SHEEP", 1)]  # 9C+11S
LAND_PLAN = {1: (7, 1900), 2: (11, 3400), 3: (15, 5400)}  # idx: (min_day, cash)
MELON_SLOTS, TOMATO_SLOTS = 8, 3
STRAW_SLOTS = 10
MELON_PLANT_UNTIL, TOMATO_PLANT_START, TOMATO_PLANT_UNTIL = 17, 9, 14
WHEAT_PLANT_UNTIL = 25
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Compiler:
    def __init__(self):
        self.melon_tiles = set()
        self.tomato_tiles = set()
        self.pasture_pool = []
        self.pasture_slots = []
        self.land_bought = set()
        self.desig_day = -1
        self.animal_tgt = {}      # unit -> committed pasture target
        self.assign = {}          # unit -> committed job
        self.zones = {}
        self.zone_day = -1
        self.chunks = {}

    # ------------------------------------------------------------- layout ---
    def designate(self, obs):
        p = obs["player"]
        farm = obs["farms"][p]
        size = len(farm["tiles"])
        half = size // 2
        quads = farm.get("unlocked_quadrants") or ["NW"]
        if self.desig_day < 0:
            near = sorted(((x, y) for x in range(1, half) for y in range(1, half)),
                          key=lambda t: dist(t, (half - 1, half - 1)))
            self.melon_tiles = set(near[:MELON_SLOTS])
            self.tomato_tiles = set(near[MELON_SLOTS:MELON_SLOTS + TOMATO_SLOTS])
            self.desig_day = obs["day"]

        def ring(q):
            xs = range(0, half) if q in ("NW", "SW") else range(half, size)
            ys = range(0, half) if q in ("NW", "NE") else range(half, size)
            x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
            out = [(x, y) for y in ys for x in xs
                   if x in (x0, x1) or y in (y0, y1)]
            out.sort(key=lambda t: -dist(t, (half - 0.5, half - 0.5)))
            return out

        for q in ("NW", "NE", "SW", "SE"):
            if q in quads:
                for t in ring(q):
                    if (t not in self.melon_tiles and t not in self.tomato_tiles
                            and t not in self.pasture_slots and t not in self.pasture_pool):
                        self.pasture_pool.append(t)

        animals = sum(1 for row in farm["tiles"] for t in row
                      if isinstance(t, dict) and "animal" in t)
        pipeline = obs["private"]["shed"].get("COW", 0) + \
            obs["private"]["shed"].get("SHEEP", 0) + \
            sum(inv.get("COW", 0) + inv.get("SHEEP", 0)
                for inv in obs["private"]["inventories"])
        need = min(animals + pipeline + 2, 22)
        while len(self.pasture_slots) < need and self.pasture_pool:
            self.pasture_slots.append(self.pasture_pool.pop(0))

    def make_zones(self, obs, n_units):
        p = obs["player"]
        farm = obs["farms"][p]
        size = len(farm["tiles"])
        # vertical strips over the whole board; strips sized by unit count
        cols = list(range(size))
        per = max(1, size // max(1, n_units))
        self.zones = {}
        for i in range(n_units):
            x0 = i * per
            x1 = (i + 1) * per - 1 if i < n_units - 1 else size - 1
            if x0 < size:
                self.zones[i] = (x0, min(x1, size - 1))

    # ------------------------------------------------------------ economy ---
    def market(self, obs, action):
        p = obs["player"]
        farm = obs["farms"][p]
        priv = obs["private"]
        day, hour = obs["day"], obs["hour"]
        cash = farm["money"]
        cushion = 250 if day <= 5 else (100 if day <= 27 else 40)
        orders = []

        def spend(cost):
            nonlocal cash
            if cash - cost >= cushion:
                cash -= cost
                return True
            return False

        def tile_at(pos):
            return farm["tiles"][pos[1]][pos[0]]

        if hour == 0:
            # land
            idx = len(farm.get("unlocked_quadrants") or ["NW"])
            if idx in LAND_PLAN and idx not in self.land_bought:
                min_day, need_cash = LAND_PLAN[idx]
                if day >= min_day and cash >= need_cash and len(orders) < 10:
                    orders.append(["BUY_LAND"])
                    self.land_bought.add(idx)
            # animals
            tgt = {"COW": 0, "SHEEP": 0}
            for dd, kind, n in ANIMAL_TARGETS:
                if day >= dd:
                    tgt[kind] += n
            placed = {"COW": 0, "SHEEP": 0}
            free_p = 0
            for row in farm["tiles"]:
                for t in row:
                    if isinstance(t, dict):
                        if "animal" in t:
                            placed[t["animal"]] += 1
                        elif t.get("kind") == "PASTURE":
                            free_p += 1
            unbuilt = sum(1 for t in self.pasture_slots if tile_at(t) is None)
            room = free_p + unbuilt + 2
            for kind in ("COW", "SHEEP"):
                if len(orders) >= 10:
                    break
                pipeline = priv["shed"].get(kind, 0) + \
                    sum(inv.get(kind, 0) for inv in priv["inventories"])
                need = max(0, tgt[kind] - placed[kind] - pipeline)
                want = 0
                cost = 400 if kind == "COW" else 500
                floor = 500 if day <= 8 else 300
                while need > 0 and room > 0 and want < 2 and cash - cost >= max(cushion, floor):
                    cash -= cost
                    want += 1; need -= 1; room -= 1
                if want:
                    orders.append(["BUY_ANIMAL", kind, want])
            # feed wheat
            animals = sum(placed.values())
            shed_w = priv["shed"].get("WHEAT", 0)
            carried = sum(inv.get("WHEAT", 0) for inv in priv["inventories"])
            wp = (obs.get("market") or {}).get("prices", {}).get("WHEAT", 25)
            if animals and shed_w + carried < animals + 5 and day <= 27 and \
                    wp <= 80 and len(orders) < 10:
                orders.append(["BUY_PRODUCT", "WHEAT",
                               min(8, animals + 5 - shed_w - carried)])
            # seeds
            dirt = sum(1 for row in farm["tiles"] for t in row if t is None)
            dirt -= sum(1 for t in self.pasture_slots if tile_at(t) is None)
            dirt -= sum(1 for t in self.melon_tiles | self.tomato_tiles
                        if tile_at(t) is None)
            seeds_w = priv["seeds"].get("WHEAT", 0)
            if day <= WHEAT_PLANT_UNTIL and len(orders) < 10:
                want = min(max(0, min(dirt + 8, 30) - seeds_w), 24)
                if want and spend(want * 10):
                    orders.append(["BUY_SEED", "WHEAT", want])
            seeds_st = priv["seeds"].get("STRAWBERRY", 0)
            if 5 <= day <= 18 and len(orders) < 10:
                want = max(0, STRAW_SLOTS - seeds_st) if day <= 8 else max(0, 3 - seeds_st)
                if want and spend(want * 100):
                    orders.append(["BUY_SEED", "STRAWBERRY", want])
            seeds_t = priv["seeds"].get("TOMATO", 0)
            if 7 <= day <= TOMATO_PLANT_UNTIL and len(orders) < 10:
                want = max(0, TOMATO_SLOTS - seeds_t) if day <= 10 else max(0, 2 - seeds_t)
                if want and spend(want * 50):
                    orders.append(["BUY_SEED", "TOMATO", want])
            seeds_m = priv["seeds"].get("MELON", 0)
            if len(orders) < 10:
                want = 0
                if day <= 2:
                    want = max(0, MELON_SLOTS - seeds_m)
                elif 13 <= day <= 15 and seeds_m < 6:
                    want = 6 - seeds_m
                if want and spend(want * 80):
                    orders.append(["BUY_SEED", "MELON", want])

        elif hour == 12:
            animals = sum(1 for row in farm["tiles"] for t in row
                          if isinstance(t, dict) and "animal" in t)
            shed_w = priv["shed"].get("WHEAT", 0)
            wp = (obs.get("market") or {}).get("prices", {}).get("WHEAT", 25)
            if animals and shed_w < animals + 8 and wp <= 80 and day <= 27 and \
                    len(orders) < 10:
                orders.append(["BUY_PRODUCT", "WHEAT", min(8, animals + 8 - shed_w)])
            if day <= WHEAT_PLANT_UNTIL and priv["seeds"].get("WHEAT", 0) < 6:
                dirt = sum(1 for row in farm["tiles"] for t in row if t is None)
                if dirt >= 2 and len(orders) < 10:
                    want = min(18, max(8, dirt))
                    if spend(want * 10):
                        orders.append(["BUY_SEED", "WHEAT", want])

        # sells at h6 and h18
        if hour in (6, 18):
            shed = priv["shed"]
            animals = sum(1 for row in farm["tiles"] for t in row
                          if isinstance(t, dict) and "animal" in t)
            if day >= 27 or (day == 26 and hour >= 12):
                keep = min(animals, shed.get("WHEAT", 0)) if day < 29 else 0
                for item in PRODUCTS:
                    q = shed.get(item, 0) - (keep if item == "WHEAT" else 0)
                    if q > 0 and len(orders) < 10:
                        orders.append(["SELL", item, q])
            else:
                for item, cap, minq in (("FERTILIZER", 4, 1), ("STRAWBERRY", 5, 3),
                                        ("MILK", 6, 4), ("WOOL", 5, 3), ("MELON", 5, 3),
                                        ("TOMATO", 5, 3)):
                    q = shed.get(item, 0)
                    if q >= minq and len(orders) < 10:
                        orders.append(["SELL", item, min(q, cap)])
                if hour == 18:
                    q = shed.get("WHEAT", 0)
                    if q > 25 and day >= 4 and len(orders) < 10:
                        orders.append(["SELL", "WHEAT", min(q - 25, 15)])

        # workforce hiring fills remaining slots (buys keep priority)
        if hour in (0, 6, 12):
            n_pl = sum(1 for row in farm["tiles"] for t in row
                       if isinstance(t, dict) and t.get("kind") == "PLANT")
            n_an = sum(1 for row in farm["tiles"] for t in row
                       if isinstance(t, dict) and "animal" in t)
            target = min(14, 2 + n_pl // 2 + n_an // 2)
            target = min(target, HIRES.get(day, 0))
            current = len(farm.get("hands") or []) + \
                sum(1 for o in orders if o[0] == "HIRE")
            hired = farm.get("hires_today", 0) + \
                sum(1 for o in orders if o[0] == "HIRE")
            while current < target and len(orders) < 10:
                cost = FIB[hired] if hired < len(FIB) else 377
                if not spend(cost):
                    break
                orders.append(["HIRE"]); hired += 1; current += 1

        action["market"] = orders[:10]
        return action

    # -------------------------------------------------------------- units ---
    def units(self, obs, action):
        p = obs["player"]
        farm = obs["farms"][p]
        priv = obs["private"]
        day = obs["day"]
        size = len(farm["tiles"])
        half = size // 2
        shed_tiles = [(half - 1, half - 1), (half, half - 1),
                      (half - 1, half), (half, half)]

        positions = [farm.get("farmer")] + list(farm.get("hands") or [])
        invs = list(priv.get("inventories") or [])
        units = [(i, tuple(pos)) for i, pos in enumerate(positions) if pos is not None]
        while len(invs) < len(positions):
            invs.append({})
        n_units = len(units)

        if self.zone_day != day or len(self.zones) != n_units:
            self.zone_day = day
            self.make_zones(obs, n_units)
            self.assign = {}

        # ---------------- scan board ----------------
        free_pastures = []
        jobs_by_zone = {i: [] for i in range(n_units)}
        n_unfed = 0
        waiting = priv["shed"].get("COW", 0) + priv["shed"].get("SHEEP", 0) + \
            sum(inv.get("COW", 0) + inv.get("SHEEP", 0) for inv in invs)
        n_plants = 0
        plant_cap = int(n_units * 2.2)
        seeds = dict(priv["seeds"])

        def zone_of(x):
            for i, (x0, x1) in self.zones.items():
                if x0 <= x <= x1:
                    return i
            return 0

        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                if isinstance(t, dict):
                    if "animal" in t:
                        if not t.get("fed_today"):
                            n_unfed += 1
                            jobs_by_zone[zone_of(x)].append((1, (x, y), "FEED", None))
                        elif not t.get("cared_today"):
                            jobs_by_zone[zone_of(x)].append((9, (x, y), "CARE", None))
                        if t.get("fertilizer_available"):
                            jobs_by_zone[zone_of(x)].append((3.5, (x, y), "COLLECT_FERTILIZER", None))
                    elif t.get("kind") == "PLANT":
                        n_plants += 1
                        age = day - t.get("planted_day", day)
                        crop = t.get("crop")
                        yu = t.get("yield_units", 0)
                        if not t.get("watered_today"):
                            cu = t.get("consecutive_unwatered", 0)
                            if age == 0:
                                jobs_by_zone[zone_of(x)].append((0.5, (x, y), "WATER", None))
                            elif cu >= 1:
                                jobs_by_zone[zone_of(x)].append((2, (x, y), "WATER", None))
                            else:
                                jobs_by_zone[zone_of(x)].append((3, (x, y), "WATER", None))
                        if crop in ("STRAWBERRY", "TOMATO"):
                            if yu >= 3 or (day >= 26 and yu > 0):
                                jobs_by_zone[zone_of(x)].append((4, (x, y), "HARVEST", None))
                        else:
                            maturity = 4 if crop == "WHEAT" else 12
                            if yu > 0 and (age >= maturity or yu >= 6 or day >= 27):
                                jobs_by_zone[zone_of(x)].append((4, (x, y), "HARVEST", None))
                    elif t.get("kind") == "WEED":
                        jobs_by_zone[zone_of(x)].append((5, (x, y), "DIG", None))
                    elif t.get("kind") == "PASTURE" and "animal" not in t:
                        free_pastures.append((x, y))
                elif t is None:
                    if n_plants >= plant_cap:
                        continue
                    if (x, y) in self.melon_tiles:
                        if seeds.get("MELON", 0) > 0 and day <= MELON_PLANT_UNTIL:
                            jobs_by_zone[zone_of(x)].append((5.5, (x, y), "PLANT", "MELON"))
                            seeds["MELON"] -= 1; n_plants += 1
                        elif seeds.get("WHEAT", 0) > 0 and day <= WHEAT_PLANT_UNTIL:
                            jobs_by_zone[zone_of(x)].append((5.5, (x, y), "PLANT", "WHEAT"))
                            seeds["WHEAT"] -= 1; n_plants += 1
                    elif (x, y) in self.tomato_tiles:
                        if seeds.get("TOMATO", 0) > 0 and TOMATO_PLANT_START <= day <= TOMATO_PLANT_UNTIL:
                            jobs_by_zone[zone_of(x)].append((5.5, (x, y), "PLANT", "TOMATO"))
                            seeds["TOMATO"] -= 1; n_plants += 1
                        elif seeds.get("WHEAT", 0) > 0 and day <= WHEAT_PLANT_UNTIL:
                            jobs_by_zone[zone_of(x)].append((5.5, (x, y), "PLANT", "WHEAT"))
                            seeds["WHEAT"] -= 1; n_plants += 1
                    elif (x, y) not in self.pasture_slots:
                        late_melon = seeds.get("MELON", 0) > 0 and 15 <= day <= MELON_PLANT_UNTIL
                        if late_melon:
                            jobs_by_zone[zone_of(x)].append((5.5, (x, y), "PLANT", "MELON"))
                            seeds["MELON"] -= 1; n_plants += 1
                        elif seeds.get("WHEAT", 0) > 0 and day <= WHEAT_PLANT_UNTIL:
                            jobs_by_zone[zone_of(x)].append((5.5, (x, y), "PLANT", "WHEAT"))
                            seeds["WHEAT"] -= 1; n_plants += 1

        # pasture builds (zone-local)
        built = 0
        for pos in self.pasture_slots:
            if farm["tiles"][pos[1]][pos[0]] is None and built < max(1, waiting + 1 - len(free_pastures)):
                jobs_by_zone[zone_of(pos[0])].append((6, pos, "BUILD_PASTURE", None))
                built += 1
        # animal pickups (barn zone, limited)
        carrying = sum(1 for inv in invs if inv.get("COW", 0) or inv.get("SHEEP", 0))
        placed_count = sum(1 for row in farm["tiles"] for t in row
                           if isinstance(t, dict) and "animal" in t)
        if waiting > 0 and free_pastures and carrying < 3 and placed_count < 22:
            for k in range(min(3 - carrying, waiting, len(free_pastures))):
                st = shed_tiles[k % 4]
                jobs_by_zone[zone_of(st[0])].append((4.2, st, "PICKUP_ANIMAL", None))

        for i in jobs_by_zone:
            jobs_by_zone[i].sort(key=lambda j: (j[0], j[1][1], j[1][0]))

        # ---------------- chunk planning (every 4h) ----------------
        all_jobs = []
        for lst in jobs_by_zone.values():
            all_jobs.extend(lst)
        all_jobs.sort(key=lambda j: (j[1][1], j[1][0] if j[1][1] % 2 == 0 else -j[1][0]))
        hour = obs["hour"]
        if hour % 4 == 0 or len(self.chunks) != n_units:
            self.chunks = {i: [] for i in range(n_units)}
            if n_units > 0 and all_jobs:
                per = max(1, math.ceil(len(all_jobs) / n_units))
                for k, j in enumerate(all_jobs):
                    self.chunks[min(k // per, n_units - 1)].append(j)
                for z in self.chunks:
                    self.chunks[z].sort(key=lambda j: (j[0], j[1][1], j[1][0]))

        # ---------------- assign ----------------
        out = [None] * len(positions)
        used = set()
        shed_w = priv["shed"].get("WHEAT", 0)
        total_wheat_carried = sum((invs[i].get("WHEAT", 0) if i < len(invs) else 0)
                                  for i, _ in units)
        feed_deficit = max(0, n_unfed - total_wheat_carried)

        def step(pos, tgt):
            dx, dy = tgt[0] - pos[0], tgt[1] - pos[1]
            if dx and abs(dx) >= abs(dy):
                return ["EAST"] if dx > 0 else ["WEST"]
            if dy:
                return ["SOUTH"] if dy > 0 else ["NORTH"]
            if dx:
                return ["EAST"] if dx > 0 else ["WEST"]
            return ["PASS"]

        def valid(verb, pos, arg, inv):
            t = farm["tiles"][pos[1]][pos[0]]
            if verb == "WATER":
                return isinstance(t, dict) and t.get("kind") == "PLANT" and not t.get("watered_today")
            if verb == "PLANT":
                return t is None and seeds.get(arg, 0) > 0
            if verb == "HARVEST":
                return isinstance(t, dict) and t.get("yield_units", 0) > 0
            if verb == "DIG":
                return isinstance(t, dict) and t.get("kind") == "WEED"
            if verb == "FEED":
                return isinstance(t, dict) and "animal" in t and not t.get("fed_today")
            if verb == "CARE":
                return isinstance(t, dict) and "animal" in t and t.get("fed_today") and not t.get("cared_today")
            if verb == "COLLECT_FERTILIZER":
                return isinstance(t, dict) and t.get("fertilizer_available")
            if verb == "BUILD_PASTURE":
                return t is None
            if verb == "PICKUP_ANIMAL":
                return priv["shed"].get("COW", 0) > 0 or priv["shed"].get("SHEEP", 0) > 0
            return False

        for i, pos in units:
            inv = invs[i] if i < len(invs) else {}
            wheat_carry = inv.get("WHEAT", 0)
            # 1) carry animal -> place
            if inv.get("COW", 0) or inv.get("SHEEP", 0):
                kind = "COW" if inv.get("COW", 0) else "SHEEP"
                tgt = self.animal_tgt.get(i)
                ok = False
                if tgt is not None:
                    t = farm["tiles"][tgt[1]][tgt[0]]
                    ok = isinstance(t, dict) and t.get("kind") == "PASTURE" and "animal" not in t
                if not ok:
                    if free_pastures:
                        tgt = min(free_pastures, key=lambda t: dist(pos, t))
                        self.animal_tgt[i] = tgt
                    else:
                        self.animal_tgt.pop(i, None)
                        sh = min(shed_tiles, key=lambda t: dist(pos, t))
                        out[i] = ["DROP"] if pos == sh else step(pos, sh)
                        continue
                if pos == tgt:
                    if tgt in free_pastures:
                        free_pastures.remove(tgt)
                    self.animal_tgt.pop(i, None)
                    out[i] = ["PLACE", kind]
                else:
                    out[i] = step(pos, tgt)
                continue
            # 2) haul goods to shed
            prods = sum(v for k, v in inv.items() if k in PRODUCTS)
            if prods - wheat_carry >= 4:
                sh = min(shed_tiles, key=lambda t: dist(pos, t))
                out[i] = ["DROP"] if pos == sh else step(pos, sh)
                continue
            # 3) committed job
            prev = self.assign.get(i)
            if prev:
                verb, jpos, arg = prev
                if valid(verb, jpos, arg, inv) and (verb, jpos) not in used and \
                        not (verb == "FEED" and wheat_carry <= 0):
                    used.add((verb, jpos))
                    if pos == jpos:
                        if verb == "PICKUP_ANIMAL":
                            k2 = "COW" if priv["shed"].get("COW", 0) > 0 else "SHEEP"
                            out[i] = ["PICKUP", k2, 1]
                        else:
                            out[i] = self._verb(verb, arg)
                        self.assign.pop(i, None)
                    else:
                        out[i] = step(pos, jpos)
                    continue
                self.assign.pop(i, None)
            # 4) feed deficit: fetch wheat before any other work
            if feed_deficit > 0 and wheat_carry == 0 and shed_w > 0 and day <= 28:
                sh = min(shed_tiles, key=lambda t: dist(pos, t))
                if pos == sh:
                    out[i] = ["PICKUP", "WHEAT", 3]
                    feed_deficit -= 3
                else:
                    out[i] = step(pos, sh)
                    feed_deficit -= 3
                continue
            # 5) own chunk first, then nearest other chunk
            act = None
            order = [i] + sorted((z for z in self.chunks if z != i),
                                 key=lambda z: abs(z - i))
            for z in order:
                for pri, jpos, verb, arg in self.chunks.get(z, []):
                    if (verb, jpos) in used:
                        continue
                    if not valid(verb, jpos, arg, inv):
                        continue
                    if verb == "FEED" and wheat_carry <= 0:
                        continue
                    used.add((verb, jpos))
                    if pos == jpos:
                        if verb == "PICKUP_ANIMAL":
                            k2 = "COW" if priv["shed"].get("COW", 0) > 0 else "SHEEP"
                            act = ["PICKUP", k2, 1]
                        else:
                            act = self._verb(verb, arg)
                    else:
                        act = step(pos, jpos)
                        self.assign[i] = (verb, jpos, arg)
                    break
                if act:
                    break
            out[i] = act or ["PASS"]

        action["farmer"] = out[0] if out and out[0] else ["PASS"]
        action["hands"] = [a if a else ["PASS"] for a in out[1:]]
        return action

    def _verb(self, verb, arg):
        if verb == "PLANT":
            return ["PLANT", arg]
        if verb == "PICKUP_ANIMAL":
            return ["PASS"]
        return [verb] if not arg else [verb, arg]

    # ------------------------------------------------------------- driver ---
    def act(self, obs, configuration):
        action = {"market": [], "farmer": ["PASS"], "hands": []}
        try:
            self.designate(obs)
            self.market(obs, action)
            self.units(obs, action)
        except Exception:
            pass
        return action


def compile_route(seed=1, out_path=None):
    out_path = out_path or os.path.join(HERE, "..", "data", "compiled_route.json")
    comp = Compiler()
    tape = []

    def rec(obs, config):
        a = comp.act(obs, config)
        tape.append({
            "market": [list(o) for o in (a.get("market") or [])],
            "farmer": list(a.get("farmer") or ["PASS"]),
            "hands": [list(h) for h in (a.get("hands") or [])],
        })
        return a

    pass_src = ('def agent(observation, configuration):\n'
                '    return {"market": [], "farmer": ["PASS"], '
                '"hands": [["PASS"]] * len(observation["farms"][observation["player"]].get("hands") or [])}\n')
    pass_path = os.path.join(HERE, "_pass_agent.py")
    with open(pass_path, "w") as f:
        f.write(pass_src)

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([rec, pass_path])
    reward = env.steps[-1][0].reward or 0
    from run_local import audit
    r = audit(env)
    with open(out_path, "w") as f:
        json.dump(tape, f)
    print(f"compiled route: {len(tape)} turns -> {out_path}")
    print(f"  reward ${reward:,.0f} | esc={r['animal_escapes']} weed_outs={r['weed_outs']} "
          f"anim={r['animals_end']} peak={r['peak_crops']} fert={r['fert_sold']}")
    return tape


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    compile_route(seed=args.seed, out_path=args.out)
