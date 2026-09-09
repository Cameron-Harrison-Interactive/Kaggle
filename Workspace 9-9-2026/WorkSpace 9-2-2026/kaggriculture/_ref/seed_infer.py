"""seed_infer.py — validate seed inference from public observations. v2

Per game (GameSim, v6h2 vs v1112fr):
  1. GROUND TRUTH: K._spawn_weeds wrapper records per-farm pre-spawn empty
     count + draw indices of spawned weeds; K._end_of_day records the appended
     shop (if any). -> exact (day, N, weed_idx, shop) for EVERY day 0..28.
  2. AGENT-VIEW RECONSTRUCTION from hourly public snapshots (what a live agent
     sees): at H0 of day D, empty-at-spawn = tiles None at H0  ∪  NEW weeds
     (WEED at H0, not WEED at H23 snapshot). Compares to ground truth (known
     edge case: opponent DIG of an old weed at H23 followed by a re-weed at
     EOD is misclassified — reported if it occurs).
  3. LIVE-STYLE PIN TIMELINE: filters arrive one day at a time; candidates =
     seeds passing ALL filters for days 0..d. Reports the day the seed is
     uniquely pinned (assuming compute keeps up) + measured us/candidate.

Usage: python _ref/seed_infer.py [seeds_csv] [range_power]
"""
import sys, os, time, random, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import sim
K = sim.K

SHOPS_SORTED = sorted(["BAKERY", "PIZZA_SHOP", "BRUNCH_SPOT", "YARN_STORE",
                       "ICE_CREAM_SHOP", "PET_CAFE", "SMOOTHIE_SHOP", "FARMERS_MARKET"])

# ---------------- ground truth recorders ----------------
DAY_LOG = []  # per day: {"day":, "n":, "widx": [...], "shop": str|None}
_orig_spawn = K._spawn_weeds
_orig_eod = K._end_of_day
_cur = []    # spawn entries for the current day


def _rec_spawn(farm, board_size, weed_chance, rng):
    was_none = [[farm["tiles"][y][x] is None for x in range(board_size)]
                for y in range(board_size)]
    _orig_spawn(farm, board_size, weed_chance, rng)
    n = sum(sum(r) for r in was_none)
    widx, i = [], -1
    for y in range(board_size):
        for x in range(board_size):
            if was_none[y][x]:
                i += 1
                if farm["tiles"][y][x] is not None:  # weed spawned here
                    widx.append(i)
    _cur.append((n, widx))


def _rec_eod(state, env, day):
    del _cur[:]
    shops = state[0].observation.town["unlocked_shops"]
    n_shops = len(shops)
    _orig_eod(state, env, day)
    shops = state[0].observation.town["unlocked_shops"]
    shop = shops[-1] if len(shops) == n_shops + 1 else None
    if len(_cur) == 2:
        (n0, w0), (n1, w1) = _cur
        DAY_LOG.append({"day": day, "n": n0 + n1, "widx": w0 + [n0 + i for i in w1],
                        "shop": shop})


K._spawn_weeds = _rec_spawn
K._end_of_day = _rec_eod


def load_agent(path):
    spec = importlib.util.spec_from_file_location("sb_" + os.path.basename(path), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def board_farms(obs):
    out = []
    for farm in obs["farms"]:
        rows = []
        for row in farm["tiles"]:
            rows.append([(t["kind"] if isinstance(t, dict) else t) for t in row])
        out.append(rows)
    return out


def run_game(seed, a_path, b_path):
    DAY_LOG.clear()
    a = load_agent(a_path); b = load_agent(b_path)
    g = sim.GameSim(seed=seed)
    snaps = {}
    opp_h23_plant = 0
    for _ in range(720):
        o = g.obs(0)
        d, h = o["day"], o["hour"]
        act0, act1 = a(o), b(g.obs(1))
        farm0 = o["farms"][0]
        units = [tuple(farm0["farmer"])] + [tuple(p) for p in (farm0.get("hands") or [])]
        snaps[(d, h)] = (board_farms(o), act0, units)
        if h == 23:
            for u in (act1.get("hands") or []) + [act1.get("farmer") or []]:
                if isinstance(u, list) and u and u[0] == "PLANT":
                    opp_h23_plant += 1
        g.step(act0, act1)
    gt = [dict(d) for d in DAY_LOG]
    recon = []
    for d in gt:
        D = d["day"] + 1
        if (D, 0) not in snaps:
            break
        prev, curr = snaps[(D - 1, 23)][0], snaps[(D, 0)][0]
        act0, units = snaps[(D - 1, 23)][1], snaps[(D - 1, 23)][2]
        # tiles OUR units PLANT on at H23: plant succeeds -> tile occupied at
        # spawn (living plant, or WEED if it died unwatered: _new_plant starts
        # consecutive_unwatered=1, +1 at refresh = 2 -> instant death). Either
        # way NOT empty at spawn. If the tile is None at H0 the plant failed
        # (not empty tile / no seed) -> still empty at spawn.
        planted = set()
        for idx, uact in enumerate([act0.get("farmer")] + list(act0.get("hands") or [])):
            if isinstance(uact, list) and uact and uact[0] == "PLANT" and idx < len(units):
                x, y = units[idx]
                planted.add((y, x))
        # None-at-H23 snapshot: only these can be empty at spawn. (A PLANT at
        # H23 that is WEED at H0 DIED at refresh -> never empty, no draw; a
        # PLANT at H23 that is None at H0 was harvested/dug -> WAS empty,
        # counted via "None at H0".)
        prev_none = {(p, y, x) for p, f in enumerate(prev) for y, r in enumerate(f)
                     for x, k in enumerate(r) if k is None}
        new_weeds = set()
        for p, f in enumerate(curr):
            for y, r in enumerate(f):
                for x, k in enumerate(r):
                    if k == "WEED" and (p, y, x) in prev_none:
                        new_weeds.add((p, y, x))
        widx = []
        n = 0
        for p, f in enumerate(curr):
            for y, r in enumerate(f):
                for x, k in enumerate(r):
                    if p == 0 and (y, x) in planted and k is not None:
                        continue  # our own H23 plant (occupied at spawn)
                    if k is None or (p, y, x) in new_weeds:
                        if (p, y, x) in new_weeds:
                            widx.append(n)
                        n += 1
        recon.append({"day": d["day"], "n": n, "widx": widx})
    return gt, recon, opp_h23_plant


# ---------------- candidate filters ----------------
def make_filter(day, n, weed_idx, shop):
    ws = list(weed_idx)

    if not ws and shop is None:
        def test(seed, _d=day, _n=n):
            rng = random.Random((seed * 1_000_003) ^ _d)
            rr = rng.random
            for _ in range(_n):
                if rr() < 0.005:
                    return False
            return True
        return test

    if not ws:
        def test(seed, _d=day, _n=n, _s=shop):
            rng = random.Random((seed * 1_000_003) ^ _d)
            rr = rng.random
            for _ in range(_n):
                if rr() < 0.005:
                    return False
            return rng.choice(SHOPS_SORTED) == _s
        return test

    def test(seed, _d=day, _n=n, _ws=ws, _s=shop):
        rng = random.Random((seed * 1_000_003) ^ _d)
        rr = rng.random
        bad = [i for i in range(_n) if rr() < 0.005]
        if bad != _ws:
            return False
        return _s is None or rng.choice(SHOPS_SORTED) == _s
    return test


def main():
    seeds = [int(x) for x in (sys.argv[1].split(",") if len(sys.argv) > 1 else list(range(1, 13)))]
    power = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    R = 1 << power
    OURS = os.path.join(ROOT, "topbots", "v6h2.py")
    OPP = os.path.join(ROOT, "topbots", "v1112fr.py")
    print(f"sweep range: 0..{R-1} (2^{power}); true seeds {seeds}")

    # per-candidate cost calibration (no-weed draw-day filter, n~12)
    f_cal = make_filter(2, 12, [], "YARN_STORE")
    t0 = time.time(); Rcal = 20000
    for s in range(Rcal):
        f_cal(s)
    us = (time.time() - t0) / Rcal * 1e6
    print(f"calibration: {us:.2f} us/candidate  -> full-range first pass 2^{power} = "
          f"{us * R / 1e6:.0f}s; whole-game budget ~288s (0.4s x 720 turns)")

    pinned_days, recon_bad, opp_plants = [], 0, []
    for s in seeds:
        gt, recon, opp_plant = run_game(s, OURS, OPP)
        mism = [(g["day"], g["n"], r["n"], g["widx"], r["widx"])
                for g, r in zip(gt, recon) if g["n"] != r["n"] or g["widx"] != r["widx"]]
        recon_bad += len(mism); opp_plants.append(opp_plant)
        # live-style timeline: cumulative filtering
        cands = None
        pin_day = None
        for d in gt:
            f = make_filter(d["day"], d["n"], d["widx"], d["shop"])
            t0 = time.time()
            if cands is None:
                cands = [x for x in range(R) if f(x)]
            else:
                cands = [x for x in cands if f(x)]
            dt = time.time() - t0
            if len(cands) <= 1 and pin_day is None:
                pin_day = d["day"]
                print(f"  seed {s}: PINNED at day {pin_day} (shop morning D{pin_day+1}); "
                      f"true_in={s in cands}; cands={cands}")
                break
        if pin_day is None:
            print(f"  seed {s}: NOT pinned by day {gt[-1]['day']}; survivors={len(cands)} "
                  f"true_in={s in cands}")
        else:
            pinned_days.append(pin_day)
        if mism:
            print(f"    recon mismatches (day, gt_n, rec_n, gt_widx, rec_widx): {mism}")
    print(f"\nrecon mismatches total: {recon_bad}; opponent H23 PLANT actions seen: {sum(opp_plants)}")
    if pinned_days:
        print(f"pinned {len(pinned_days)}/{len(seeds)}; pin days: {sorted(pinned_days)}")


if __name__ == "__main__":
    main()
