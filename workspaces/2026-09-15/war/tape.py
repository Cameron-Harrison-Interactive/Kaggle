#!/usr/bin/env python3
"""tape.py - both-sides match analyzer.

Usage: python war/tape.py <A.py> <B.py> <seed> [--days 12,15,18,21,24,27,29]

Runs one episode locally and reports, for BOTH players:
  - day table (chosen days): cash, quads, crew, herd, standing crops, weeds
  - revenue by good (from each agent's SELL tape, priced at execution hour)
  - spend by category (BUY_SEED / BUY_ANIMAL / BUY_LAND / BUY_PRODUCT)
  - pocket state at h23 (seeds by crop, shed by good) - the idle-money leak
"""
import contextlib
import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from watch import env_name, ensure_env  # noqa: E402

GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")


def run(path_a, path_b, seed):
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])

    pl = [{"cash": [], "quads": [], "crew": [], "herd": [], "stand": [],
           "weeds": [], "seeds": {}, "shed": {},
           "sell": {}, "buy": {}}
          for _ in range(2)]

    for step in env.steps:
        for i in (0, 1):
            st = step[i] or {}
            obs = st.get("observation") or {}
            if "farms" not in obs or len(obs["farms"]) <= i:
                continue
            day, hour = int(obs.get("day", 0)), int(obs.get("hour", 0))
            p = pl[i]
            act = st.get("action") or {}
            px = ((obs.get("market", {}) or {}).get("prices", {}) or {})
            for o in act.get("market", []) or []:
                if not (isinstance(o, list) and len(o) >= 3):
                    continue
                op, item = o[0], o[1]
                if op == "SELL" and item in GOODS:
                    q = int(o[2]) if str(o[2]).isdigit() else 0
                    if 0 < q < 900000:  # 10^6 = sell-all idiom (tetsu)
                        g = p["sell"].setdefault(item, [0, 0.0])
                        g[0] += q
                        g[1] += q * px.get(item, 0)
                elif op in ("BUY_SEED", "BUY_PRODUCT") and item in GOODS:
                    q = int(o[2]) if str(o[2]).isdigit() else 0
                    if q > 0:
                        g = p["buy"].setdefault(op + " " + item, [0, 0.0])
                        g[0] += q
                        g[1] += q * px.get(item, 0)
                elif op == "BUY_ANIMAL" and item in ("COW", "SHEEP", "GOOSE"):
                    q = int(o[2]) if str(o[2]).isdigit() else 0
                    g = p["buy"].setdefault("BUY_ANIMAL " + str(item), [0, 0.0])
                    g[0] += q
                    g[1] += q * {"COW": 400, "SHEEP": 500, "GOOSE": 300}[item]
                elif op == "BUY_LAND":
                    g = p["buy"].setdefault("BUY_LAND", [0, 0.0])
                    g[0] += 1
                    g[1] += (1000, 2000, 4000)[min(3, g[0] - 1)]
            if hour != 23:
                continue
            f = obs["farms"][i]
            p = pl[i]
            standing, herd, weeds = {}, 0, 0
            for row in f.get("tiles", []):
                for t in row:
                    if not isinstance(t, dict):
                        continue
                    if t.get("kind") == "PLANT":
                        standing[t["crop"]] = standing.get(t["crop"], 0) + 1
                    elif t.get("kind") == "WEED":
                        weeds += 1
                    elif t.get("kind") in ("COOP", "PASTURE") and t.get("animal"):
                        herd += 1
            p["cash"].append((day, float(f.get("money", 0))))
            p["quads"].append((day, len(f.get("unlocked_quadrants", ["NW"]))))
            p["crew"].append((day, 1 + len(f.get("hands") or [])))
            p["herd"].append((day, herd))
            p["stand"].append((day, standing))
            p["weeds"].append((day, weeds))
            priv = obs.get("private", {}) or {}
            if priv:
                p["seeds"][day] = dict(priv.get("seeds", {}) or {})
                p["shed"][day] = dict(priv.get("shed", {}) or {})
    return pl, [float(env.state[0].reward), float(env.state[1].reward)]


def main():
    A, B, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    days = [int(x) for x in
            (sys.argv[5].split(",") if len(sys.argv) > 5 else
             [5, 10, 13, 16, 19, 22, 25, 27, 29])] if len(sys.argv) > 4 and \
        sys.argv[4] == "--days" else [5, 10, 13, 16, 19, 22, 25, 27, 29]
    pl, rewards = run(A, B, seed)
    names = [os.path.basename(A), os.path.basename(B)]
    print(f"seed {seed}: {names[0]} ${rewards[0]:,.0f}  vs  "
          f"{names[1]} ${rewards[1]:,.0f}   (gap {rewards[0]-rewards[1]:+,.0f})")
    for i in (0, 1):
        p, n = pl[i], names[i]
        print("\n" + "=" * 100)
        print(f"PLAYER {i}: {n}")
        hdr = ("day  cash    qd crw hd | WHE CAR MEL STR TOM | wds | pocket: seeds / shed")
        print(hdr)
        for d in days:
            cash = dict(p["cash"]).get(d, 0)
            qd = dict(p["quads"]).get(d, 1)
            crw = dict(p["crew"]).get(d, 1)
            hd = dict(p["herd"]).get(d, 0)
            st = dict(p["stand"]).get(d, {})
            wds = dict(p["weeds"]).get(d, 0)
            sd = p["seeds"].get(d, {})
            sh = p["shed"].get(d, {})
            seeds_s = " ".join(f"{k[:3]}{v}" for k, v in sorted(sd.items()) if v) or "-"
            shed_s = " ".join(f"{k[:3]}{v}" for k, v in sorted(sh.items()) if v) or "-"
            print(f"d{d:<3} {cash:>7,.0f}  {qd}  {crw:>2} {hd:>2} | "
                  f"{st.get('WHEAT',0):>3} {st.get('CARROT',0):>3} "
                  f"{st.get('MELON',0):>3} {st.get('STRAWBERRY',0):>3} "
                  f"{st.get('TOMATO',0):>3} | {wds:>3} | {seeds_s} / {shed_s}")
        print("\n  REVENUE by good (units, approx $):")
        tot = 0
        for item, (q, r) in sorted(p["sell"].items(), key=lambda kv: -kv[1][1]):
            print(f"    {item:<12} {q:>5} u   ${r:>9,.0f}")
            tot += r
        print(f"    {'TOTAL':<12} {'':>7}   ${tot:>9,.0f}")
        print("\n  SPEND by category (units/qty, approx $):")
        for item, (q, r) in sorted(p["buy"].items(), key=lambda kv: -kv[1][1]):
            print(f"    {item:<22} {q:>5}     ${r:>9,.0f}")
    print("\n" + "=" * 100)
    print("CASH GAP by day (A - B):")
    ca, cb = dict(pl[0]["cash"]), dict(pl[1]["cash"])
    for d in days:
        if d in ca and d in cb:
            print(f"  d{d:<3} {ca[d]:>9,.0f} vs {cb[d]:>9,.0f}  gap {ca[d]-cb[d]:+10,.0f}")


if __name__ == "__main__":
    main()
