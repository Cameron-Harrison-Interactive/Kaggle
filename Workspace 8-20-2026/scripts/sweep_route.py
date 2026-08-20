"""Sweep-based route choreographer — the counter-meta route compiler core.

Units walk their zone in snake order servicing every tile (water/harvest/plant/
dig), instead of greedy crisscross. Dedicated feeders handle animal logistics.
Same-day watering guaranteed: planters water what they planted next turn.

Run: python3 scripts/sweep_route.py [--out data/sweep_route.json]
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from route_compiler import (Compiler, FIB, HIRES, ANIMAL_TARGETS, LAND_PLAN,  # noqa: E402
                            MELON_SLOTS, TOMATO_SLOTS, MELON_PLANT_UNTIL,
                            TOMATO_PLANT_START, TOMATO_PLANT_UNTIL,
                            WHEAT_PLANT_UNTIL, PRODUCTS, dist)
from kaggle_environments import make  # noqa: E402


class SweepCompiler(Compiler):
    def __init__(self):
        Compiler.__init__(self)
        self.sweep_day = -1
        self.zone_lists = {}
        self.sweep_idx = {}
        self.last_plant = {}
        self.n_feeders = 0
        self.straw_tiles = set()

    def designate(self, obs):
        """Trade-model layout: strawberry + melon on interior tiles across quadrants,
        pasture rings outside. Overrides Compiler.designate."""
        p = obs["player"]
        farm = obs["farms"][p]
        size = len(farm["tiles"])
        half = size // 2
        quads = farm.get("unlocked_quadrants") or ["NW"]
        if self.desig_day < 0:
            interior = []
            for q in ("NW", "NE", "SW", "SE"):
                xs = range(0, half) if q in ("NW", "SW") else range(half, size)
                ys = range(0, half) if q in ("NW", "NE") else range(half, size)
                x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
                for y in ys:
                    for x in xs:
                        if x in (x0, x1) or y in (y0, y1):
                            continue
                        interior.append((x, y))
            interior.sort(key=lambda t: dist(t, (half - 1, half - 1)))
            STRAW, MELON = 10, 8
            self.straw_tiles = set(interior[:STRAW])
            self.melon_tiles = set(interior[STRAW:STRAW + MELON])
            self.tomato_tiles = set()
            self.desig_day = obs["day"]
        # pasture pool: outer rings
        def ring(q):
            xs = range(0, half) if q in ("NW", "SW") else range(half, size)
            ys = range(0, half) if q in ("NW", "NE") else range(half, size)
            x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
            out = [(x, y) for y in ys for x in xs
                   if x in (x0, x1) or y in (y0, y1)]
            out.sort(key=lambda t: dist(t, (half - 0.5, half - 0.5)))
            return out
        for q in ("NW", "NE", "SW", "SE"):
            if q in quads:
                for t in ring(q):
                    if (t not in self.melon_tiles and t not in self.straw_tiles
                            and t not in self.pasture_slots and t not in self.pasture_pool):
                        self.pasture_pool.append(t)
        animals = sum(1 for row in farm["tiles"] for t in row
                      if isinstance(t, dict) and "animal" in t)
        pipeline = obs["private"]["shed"].get("COW", 0) + \
            obs["private"]["shed"].get("SHEEP", 0) + \
            sum(inv.get("COW", 0) + inv.get("SHEEP", 0)
                for inv in obs["private"]["inventories"])
        need = min(animals + pipeline + 2, 22)
        self.pasture_pool.sort(key=lambda t: dist(t, (half - 0.5, half - 0.5)))
        while len(self.pasture_slots) < need and self.pasture_pool:
            self.pasture_slots.append(self.pasture_pool.pop(0))

    # ------------------------------------------------- daily zone building ---
    def build_zones(self, obs, n_units):
        p = obs["player"]
        farm = obs["farms"][p]
        size = len(farm["tiles"])
        half = size // 2
        quads = farm.get("unlocked_quadrants") or ["NW"]
        tiles = []
        for y in range(size):
            for x in range(size):
                q = ("NW" if x < half else "NE") if y < half else \
                    ("SW" if x < half else "SE")
                if q in quads:
                    tiles.append((x, y))
        # snake order
        tiles.sort(key=lambda t: (t[1], t[0] if t[1] % 2 == 0 else -t[0]))
        n_sweep = max(1, n_units - self.n_feeders)
        self.zone_lists = {}
        per = max(1, len(tiles) // n_sweep)
        for i in range(n_sweep):
            seg = tiles[i * per:(i + 1) * per] if i < n_sweep - 1 else tiles[i * per:]
            self.zone_lists[i] = seg
        self.sweep_idx = {i: 0 for i in range(n_sweep)}

    # --------------------------------------------------------------- units ---
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
        if n_units == 0:
            action["farmer"] = ["PASS"]; action["hands"] = []
            return action

        # feeder count scales with herd
        animals = sum(1 for row in farm["tiles"] for t in row
                      if isinstance(t, dict) and "animal" in t)
        pipeline_now = priv["shed"].get("COW", 0) + priv["shed"].get("SHEEP", 0)
        if animals == 0 and pipeline_now == 0:
            self.n_feeders = 0
            self.n_placers = 0
        else:
            self.n_placers = 0
            self.n_feeders = min(4, max(1, animals // 5 + 1))

        if self.sweep_day != day or len(self.zone_lists) != max(1, n_units - self.n_feeders):
            self.sweep_day = day
            self.build_zones(obs, n_units)
            self.last_plant = {}

        seeds = dict(priv["seeds"])
        shed_w = priv["shed"].get("WHEAT", 0)
        out = [None] * len(positions)

        def step(pos, tgt):
            dx, dy = tgt[0] - pos[0], tgt[1] - pos[1]
            if dx and abs(dx) >= abs(dy):
                return ["EAST"] if dx > 0 else ["WEST"]
            if dy:
                return ["SOUTH"] if dy > 0 else ["NORTH"]
            if dx:
                return ["EAST"] if dx > 0 else ["WEST"]
            return ["PASS"]

        def nearest(pos, lst):
            return min(lst, key=lambda t: dist(pos, t))

        # collect dynamic facts
        unfed = []
        fert_ready = []
        fed_uncared = []
        free_pastures = []
        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                if isinstance(t, dict) and "animal" in t:
                    if not t.get("fed_today"):
                        unfed.append((x, y))
                    elif not t.get("cared_today"):
                        fed_uncared.append((x, y))
                    if t.get("fertilizer_available"):
                        fert_ready.append((x, y))
                elif isinstance(t, dict) and t.get("kind") == "PASTURE" and "animal" not in t:
                    free_pastures.append((x, y))
        waiting = priv["shed"].get("COW", 0) + priv["shed"].get("SHEEP", 0) + \
            sum(inv.get("COW", 0) + inv.get("SHEEP", 0) for inv in invs)

        feeder_ids = [units[k][0] for k in range(max(0, n_units - self.n_feeders), n_units)]
        placer_idx = n_units - self.n_feeders - self.n_placers
        placer_ids = [units[k][0] for k in range(max(0, placer_idx), max(0, n_units - self.n_feeders))] if self.n_placers > 0 else []
        n_plants = sum(1 for row in farm["tiles"] for t in row
                       if isinstance(t, dict) and t.get("kind") == "PLANT")
        n_sweepers = max(1, n_units - self.n_feeders)
        plant_cap = int(n_sweepers * 2.0)

        for i, pos in units:
            inv = invs[i] if i < len(invs) else {}
            wheat_carry = inv.get("WHEAT", 0)

            # 0) same-day watering of own planting
            lp = self.last_plant.get(i)
            if lp and lp[1] == day:
                t = farm["tiles"][lp[0][1]][lp[0][0]]
                if pos == lp[0]:
                    if isinstance(t, dict) and t.get("kind") == "PLANT" and not t.get("watered_today"):
                        out[i] = ["WATER"]
                        self.last_plant.pop(i, None)
                        continue
                else:
                    out[i] = step(pos, lp[0])
                    continue

            # 1) carrying animal -> place
            if inv.get("COW", 0) or inv.get("SHEEP", 0):
                kind = "COW" if inv.get("COW", 0) else "SHEEP"
                tgt = self.animal_tgt.get(i)
                ok = False
                if tgt is not None:
                    t = farm["tiles"][tgt[1]][tgt[0]]
                    ok = isinstance(t, dict) and t.get("kind") == "PASTURE" and "animal" not in t
                if not ok:
                    if free_pastures:
                        tgt = nearest(pos, free_pastures)
                        self.animal_tgt[i] = tgt
                    else:
                        self.animal_tgt.pop(i, None)
                        sh = nearest(pos, shed_tiles)
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

            # 2) haul full inventory to shed
            prods = sum(v for k, v in inv.items() if k in PRODUCTS)
            if prods - wheat_carry >= 4:
                sh = nearest(pos, shed_tiles)
                if pos == sh:
                    out[i] = ["DROP"]
                    # resume sweep near the shed
                    self.sweep_idx[i] = self._nearest_idx(i, pos)
                else:
                    out[i] = step(pos, sh)
                continue

            # ---------- FEEDERS ----------
            if i in feeder_ids:
                # FEEDING FIRST (no escapes): one big wheat pickup feeds the herd
                if unfed:
                    if wheat_carry > 0:
                        tgt = nearest(pos, unfed)
                        if pos == tgt:
                            out[i] = ["FEED"]
                            unfed.remove(tgt)
                        else:
                            out[i] = step(pos, tgt)
                    else:
                        if shed_w > 0:
                            sh = nearest(pos, shed_tiles)
                            if pos == sh:
                                out[i] = ["PICKUP", "WHEAT", min(shed_w, len(unfed) + 4)]
                            else:
                                out[i] = step(pos, sh)
                        else:
                            out[i] = ["PASS"]
                    continue
                # then place waiting animals (batch pickup, rule-1 places them)
                if waiting > 0 and free_pastures:
                    carried_animals = inv.get("COW", 0) + inv.get("SHEEP", 0)
                    if carried_animals == 0:
                        sh = nearest(pos, shed_tiles)
                        if pos == sh:
                            cw = priv["shed"].get("COW", 0)
                            sw = priv["shed"].get("SHEEP", 0)
                            kind = "COW" if cw >= sw else "SHEEP"
                            n = min(3, cw if kind == "COW" else sw)
                            out[i] = ["PICKUP", kind, max(1, n)]
                        else:
                            out[i] = step(pos, sh)
                        continue
                    else:
                        out[i] = ["PASS"]; continue
                # then collect fertilizer
                if fert_ready:
                    tgt = nearest(pos, fert_ready)
                    if pos == tgt:
                        out[i] = ["COLLECT_FERTILIZER"]
                        fert_ready.remove(tgt)
                    else:
                        out[i] = step(pos, tgt)
                    continue
                # then care
                if fed_uncared:
                    tgt = nearest(pos, fed_uncared)
                    if pos == tgt:
                        out[i] = ["CARE"]
                        fed_uncared.remove(tgt)
                    else:
                        out[i] = step(pos, tgt)
                    continue
                out[i] = ["PASS"]
                continue

            # ---------- SWEEPERS ----------
            L = self.zone_lists.get(i, [])
            if not L:
                out[i] = ["PASS"]
                continue
            idx = self.sweep_idx.get(i, 0)
            # find next tile needing work (scan forward, wrap once)
            target = None
            n = len(L)
            for k in range(n):
                j = (idx + k) % n
                x, y = L[j]
                t = farm["tiles"][y][x]
                need = self._tile_need(t, (x, y), day, seeds)
                if need:
                    if need[0] == "PLANT" and n_plants >= plant_cap:
                        continue
                    target = (j, (x, y), need)
                    break
            if target is None:
                # zone clear: help any water-urgent tile globally? just pass
                out[i] = ["PASS"]
                continue
            j, tpos, need = target
            if pos != tpos:
                out[i] = step(pos, tpos)
                self.sweep_idx[i] = j
                continue
            # at tile: act
            verb, arg = need
            if verb == "PLANT":
                seeds[arg] = seeds.get(arg, 0) - 1
                n_plants += 1
                self.last_plant[i] = (tpos, day)
                out[i] = ["PLANT", arg]
            elif verb == "HARVEST":
                out[i] = ["HARVEST"]
            else:
                out[i] = [verb]
            self.sweep_idx[i] = (j + 1) % n
            continue

        action["farmer"] = out[0] if out and out[0] else ["PASS"]
        action["hands"] = [a if a else ["PASS"] for a in out[1:]]
        return action

    def _nearest_idx(self, i, pos):
        L = self.zone_lists.get(i, [])
        if not L:
            return 0
        best = 0; bd = 10 ** 9
        for k, t in enumerate(L):
            d = dist(pos, t)
            if d < bd:
                bd = d; best = k
        return best

    def _tile_need(self, t, pos, day, seeds):
        """Returns (verb, arg) if tile needs work, else None."""
        if isinstance(t, dict):
            if "animal" in t:
                return None  # feeders handle
            kind = t.get("kind")
            if kind == "PLANT":
                if not t.get("watered_today"):
                    return ("WATER", None)
                crop = t.get("crop")
                yu = t.get("yield_units", 0)
                age = day - t.get("planted_day", day)
                if crop in ("STRAWBERRY", "TOMATO"):
                    if yu >= 3 or (day >= 26 and yu > 0):
                        return ("HARVEST", None)
                else:
                    maturity = 4 if crop == "WHEAT" else 12
                    if yu > 0 and (age >= maturity or yu >= 6 or day >= 27):
                        return ("HARVEST", None)
                return None
            if kind == "WEED":
                return ("DIG", None)
            return None
        if t is None:
            if pos in self.pasture_slots:
                return ("BUILD_PASTURE", None)
            if pos in self.straw_tiles:
                if seeds.get("STRAWBERRY", 0) > 0 and 6 <= day <= 18:
                    return ("PLANT", "STRAWBERRY")
                elif seeds.get("WHEAT", 0) > 0 and day <= WHEAT_PLANT_UNTIL:
                    return ("PLANT", "WHEAT")
                return None
            if pos in self.melon_tiles:
                if seeds.get("MELON", 0) > 0 and day <= MELON_PLANT_UNTIL:
                    return ("PLANT", "MELON")
            elif pos in self.tomato_tiles:
                if seeds.get("TOMATO", 0) > 0 and TOMATO_PLANT_START <= day <= TOMATO_PLANT_UNTIL:
                    return ("PLANT", "TOMATO")
            elif seeds.get("WHEAT", 0) > 0 and day <= WHEAT_PLANT_UNTIL:
                return ("PLANT", "WHEAT")
            elif seeds.get("MELON", 0) > 0 and 15 <= day <= MELON_PLANT_UNTIL:
                return ("PLANT", "MELON")
            return None
        return None


def compile_sweep(seed=1, out_path=None):
    out_path = out_path or os.path.join(HERE, "..", "data", "sweep_route.json")
    comp = SweepCompiler()
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
    print(f"sweep route: {len(tape)} turns -> {out_path}")
    print(f"  reward ${reward:,.0f} | esc={r['animal_escapes']} weed_outs={r['weed_outs']} "
          f"anim={r['animals_end']} peak={r['peak_crops']} avg={r['avg_crops']:.1f} "
          f"fert={r['fert_sold']} hires={r['hires']}")
    return tape


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    compile_sweep(seed=args.seed, out_path=args.out)
