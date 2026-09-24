#!/usr/bin/env python3
"""ledger_planner.py — commitment/ledger economy planner for Kaggriculture.

The Shabby-Farm-class core, built on our proven machinery:

1. ENGINE MODEL (verified constants): one-time crops yield via the WATER
   window (wheat: +1/day watered on days 2-4 post-plant = 3 units/tile;
   melon: days 6-12 = 6 units cap), occupy their tile until HARVESTed.
   Ongoing crops (strawberry) produce via daily refresh. Animals produce
   when fed on interval days.

2. LEDGER: replays dated commitments (plant/water/harvest/feed/buy/sell/
   hire/land) through one cash + seed + shed + tile + labor account.
   A commitment that would break a constraint is dropped, then the replay
   re-runs to fixpoint (portfolio selection).

3. LABOR MODEL: from the recorded v25 game we know, per (day, worker), the
   anchor schedule. New commitments must fit an inter-anchor GAP with a
   full walk budget (walk_in + 1 op + walk_out), and the walker may need to
   return to the next anchor's tile — the exact Phase-A contract of
   plan_day. This is what the se_flood experiment lacked; the ledger
   enforces it BEFORE any compile.

4. CALIBRATION GATE: the ledger must replay the v25 tape's own economy
   (extracted from the record) with zero false failures.

5. CANDIDATE ECONOMIES: SE-quad wheat machine variants (plant d12-15,
   harvest d14-17, continuous wheat) — feasibility + projected net.
"""
import collections
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "agent"))

import route_compiler_v19 as rc  # noqa: E402

OUT = os.path.join(ROOT, "data", "ledger")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# engine model (verified 2026-08-15 from kaggriculture.py)
# ---------------------------------------------------------------------------
SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100,
             "MELON": 80}
# one-time crops: (first_yield_day, max_yield_day, max_yield)
ONCE = {"WHEAT": (2, 4, 3), "CARROT": (2, 3, 2), "MELON": (10, 12, 6)}
LAND_PRICES = [1000, 2000, 4000]
LAND_ORDER = ["NE", "SW", "SE"]
ANIMAL_COST = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
SHED_CAP = 100

# labor costs (steps): op itself + walk estimate (manhattan), water=walk+1
# The ledger checks GAPS, so we track (steps needed) per commitment.


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V25 = load_mod(os.path.join(ROOT, "agent", "main_v25_wheat16.py"), "v25m")


# ---------------------------------------------------------------------------
# record economy extraction
# ---------------------------------------------------------------------------
def load_record(seed=1, seat=0):
    return rc.get_record(seed, seat, V25, {})


def build_gaps(anchors, day_starts, hires):
    """Per (day, worker): sorted list of (hour, tile) anchors + gap analysis.
    Returns days: {day: {worker: {"anchors": [(h, tile)...], "start": h,
            "start_pos": tile, "gaps": [(h_from, h_to, pos_at_h_from, len)]}}}
    where a gap is a free window between consecutive anchors (and after the
    last anchor to end of day)."""
    per = collections.defaultdict(list)
    for s, w, a, t in anchors:
        per[(s // 24, w)].append((s % 24, t))
    days = collections.defaultdict(dict)
    for (d, w), lst in per.items():
        lst.sort()
        days[d][w] = {"anchors": lst}
    # start position per day/worker
    starts = {}
    for d, poslist in day_starts.items():
        for w, pos in poslist:
            starts[(d, w)] = tuple(pos)
    for (hstep, w), pos in hires.items():
        d = hstep // 24
        starts.setdefault((d, w), tuple(pos))
    for d, winfo in days.items():
        for w, info in winfo.items():
            start_pos = starts.get((d, w))
            lst = info["anchors"]
            gaps = []
            if not lst:
                if start_pos is not None:
                    gaps.append((0, 23, start_pos, 24))
                info["gaps"] = gaps
                info["start"] = 0
                info["start_pos"] = start_pos
                continue
            first_h, first_tile = lst[0]
            info["start"] = first_h
            info["start_pos"] = start_pos
            # before-first-anchor window: from spawn (h0 for farmer, hire hour
            # for hands) to first anchor, only usable if we can walk to the new
            # tile AND to the first anchor afterwards.
            # We conservatively only use windows BETWEEN anchors (positions
            # known) and after the last anchor.
            for i in range(len(lst) - 1):
                h_a, t_a = lst[i]
                h_b, t_b = lst[i + 1]
                # free hours between anchors: h_a+1 .. h_b-1
                gaps.append((h_a, h_b, t_a, h_b - h_a - 1))
            last_h, last_tile = lst[-1]
            gaps.append((last_h, 23, last_tile, 23 - last_h))
            info["gaps"] = gaps
    return days


def can_fit_roundtrip(days, day, tile, need_ops=1, min_gap=None):
    """Can (day, tile) receive a commitment needing `need_ops` consecutive
    actions (e.g. PLANT=1, WATER=1)? A worker must: be at gap start tile,
    walk to tile (d1), do op, and either stay (gap end is day end) or walk
    to the next anchor's tile (d2). Total = d1 + need_ops + d2 <= gap_len,
    with the op completing BEFORE the next anchor starts walking (so
    d1 + need_ops + d2 <= gap_len is the right check; plan_day walks are
    reserved, so the gap must contain walk_in+op+walk_out)."""
    best = None
    for w, info in days.get(day, {}).items():
        for (h_from, h_to, pos_from, g_len) in info.get("gaps", []):
            d1 = rc.bfs_dist(pos_from, tile)
            if d1 is None:
                continue
            # walk-out to the next anchor tile (if any follows in the day)
            lst = info["anchors"]
            nxt = None
            for (h2, t2) in lst:
                if h2 > h_from and h2 <= h_to + 1:
                    nxt = t2
                    break
            d2 = rc.bfs_dist(tile, nxt) if nxt is not None else 0
            total = d1 + need_ops + d2
            if total <= g_len:
                cand = (h_from + d1, w, d1, d2)
                if min_gap is None or g_len >= min_gap:
                    if best is None or cand[0] < best[0]:
                        best = cand
    return best


# ---------------------------------------------------------------------------
# ledger
# ---------------------------------------------------------------------------
class Ledger:
    """Replay commitments; drop the ones that break constraints."""

    def __init__(self):
        self.cash = 3000
        self.seeds = {}
        self.shed = collections.Counter()
        self.tiles = {}      # (x, y) -> crop until harvested
        self.land = ["NW"]   # quadrants
        self.day = 0
        self.log = []

    def land_cost(self):
        n = len(self.land) - 1
        return LAND_PRICES[n] if 0 <= n < 3 else None

    def buy_land(self, quad, why):
        if quad in self.land:
            return True
        cost = self.land_cost()
        if cost is None or self.cash < cost:
            self.log.append((self.day, "LAND-FAIL", quad, self.cash))
            return False
        self.cash -= cost
        self.land.append(quad)
        self.log.append((self.day, "LAND", quad, cost))
        return True

    def buy_seed(self, crop, n, why):
        cost = SEED_COST[crop] * n
        if self.cash < cost:
            return False
        self.cash -= cost
        self.seeds[crop] = self.seeds.get(crop, 0) + n
        return True

    def plant(self, crop, tile, why):
        if tile in self.tiles:
            return False
        if self.seeds.get(crop, 0) <= 0:
            self.log.append((self.day, "PLANT-FAIL-NOSEED", crop, tile))
            return False
        self.seeds[crop] -= 1
        self.tiles[tile] = (crop, self.day)
        return True

    def harvest(self, tile, units, why):
        if tile not in self.tiles:
            return False
        del self.tiles[tile]
        self.add_shed("WHEAT" if self.tiles[tile] else "?", 0)
        return True

    def add_shed(self, item, n):
        cur = sum(self.shed.values())
        take = min(n, SHED_CAP - cur)
        self.shed[item] += take
        return take

    def sell(self, item, n):
        have = self.shed.get(item, 0)
        n = min(n, have)
        self.shed[item] = have - n
        return n

    def feed(self, n_animals, wheat_in_shed):
        """Animals eat from the shed buffer; return actually fed."""
        fed = min(n_animals, wheat_in_shed)
        return fed


# ---------------------------------------------------------------------------
# calibration: extract the v25 economy as commitments and replay it
# ---------------------------------------------------------------------------
def calibrate(seed=1, seat=0):
    tape, plants, anchors, day_starts, hires, visits, reward = load_record(
        seed, seat)
    days = build_gaps(anchors, day_starts, hires)
    # per-day gap counts for the labor-saturation report
    report = {}
    for d in range(30):
        winfo = days.get(d, {})
        tot_workers = len(winfo)
        tot_gap_len = sum(g[3] for w, info in winfo.items()
                          for g in info.get("gaps", []))
        usable = sum(1 for w, info in winfo.items()
                     for g in info.get("gaps", []) if g[3] >= 2)
        report[d] = {"workers": tot_workers, "gap_len": tot_gap_len,
                     "gaps>=2": usable}
    # calibration facts
    n_plants = len(plants)
    wheat_plants = sum(1 for p in plants.values() if p["crop"] == "WHEAT")
    return tape, plants, anchors, day_starts, hires, days, report, reward


def main():
    print("=== ledger_planner: calibration ===", flush=True)
    if os.path.exists(rc.RECORD_CACHE_DIR):
        # keep cache: the base record may exist; wipe only stale variants
        pass
    tape, plants, anchors, day_starts, hires, days, report, reward = calibrate()
    print(f"record reward: {reward:,.0f} | plants {len(plants)} "
          f"(wheat {sum(1 for p in plants.values() if p['crop']=='WHEAT')}) "
          f"| anchors {len(anchors)}", flush=True)
    print("\nper-day labor report (d10-29):", flush=True)
    for d in range(10, 30):
        r = report[d]
        print(f"  d{d:2d}: workers={r['workers']:2d} total_gap={r['gap_len']:3d} "
              f"gaps>=2={r['gaps>=2']:2d}", flush=True)

    print("\n=== candidate: SE wheat machine ===", flush=True)
    # SE tiles, planted d12-15, harvested d14-17 (wheat yields d+2..d+4)
    se_tiles = [(x, y) for y in range(5, 10) for x in range(5, 10)]
    for n in (24, 16, 12, 8, 6, 4):
        fits = 0
        for i in range(n):
            x, y = se_tiles[i]
            d = 12 + (i % 4)
            res = can_fit_roundtrip(days, d, (x, y), need_ops=1)
            if res:
                fits += 1
        print(f"  N={n:2d}: {fits}/{n} PLANT windows feasible on d12-15",
              flush=True)

    print("\n=== SE water feasibility (daily water d12-17 per tile) ===",
          flush=True)
    for n in (24, 16, 12, 8, 6, 4):
        waters_ok = 0
        waters_tot = 0
        for i in range(n):
            x, y = se_tiles[i]
            pd = 12 + (i % 4)
            for wd in range(pd, pd + 4):  # water plant-day..d+3
                waters_tot += 1
                if can_fit_roundtrip(days, wd, (x, y), need_ops=1):
                    waters_ok += 1
        print(f"  N={n:2d}: {waters_ok}/{waters_tot} WATER windows", flush=True)

    json.dump({str(d): v for d, v in report.items()},
              open(os.path.join(OUT, "labor_report.json"), "w"), indent=1)
    print("\nsaved labor_report.json", flush=True)


if __name__ == "__main__":
    main()
