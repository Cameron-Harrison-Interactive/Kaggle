#!/usr/bin/env python3
"""Extract compact war-model intel from a kaggriculture replay JSON.
Output: /home/user/intel/eps/ep_<id>.json.gz  (or --stdout for debug)
Records per player per day: money, crew, tiles census, sells (units/rev/avg px
via market-delta attribution), buys, hires, land; market inv+price at h0.
"""
import json, gzip, sys, os, re
from collections import defaultdict

TOWN_CENTER = ["WHEAT","CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL"]
SHOPS = {
    "BAKERY":["EGG","WHEAT"], "PIZZA_SHOP":["MILK","TOMATO","WHEAT"],
    "BRUNCH_SPOT":["EGG","WHEAT","STRAWBERRY"], "YARN_STORE":["WOOL"],
    "ICE_CREAM_SHOP":["STRAWBERRY","MILK","WHEAT"], "PET_CAFE":["CARROT"],
    "SMOOTHIE_SHOP":["STRAWBERRY","MILK"],
    "FARMERS_MARKET":["WHEAT","CARROT","TOMATO","STRAWBERRY"],
}
ITEMS = ["WHEAT","CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL","FERTILIZER"]

def town_consumption(step, shops):
    """units consumed from market inventory by town at this step (negative = drain)."""
    drain = defaultdict(int)
    if step % 4 == 0:
        for s in shops:
            for it in SHOPS[s]:
                drain[it] -= (2 if len(SHOPS[s]) == 1 else 1)
    if step % 24 == 0:
        for it in TOWN_CENTER:
            drain[it] -= 1
    return drain

def tile_census(tiles):
    c = defaultdict(int)
    for row in tiles:
        for t in row:
            if t is None: c["EMPTY"] += 1
            elif t == "LOCKED": c["LOCKED"] += 1
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "WEED": c["WEED"] += 1
                elif k == "PLANT": c["crop:"+t.get("crop","?")] += 1
                elif "animal" in t: c["an:"+t["animal"]] += 1
                elif k == "COOP": c["COOP"] += 1
                elif k == "PASTURE": c["PASTURE"] += 1
                else: c["other"] += 1
    return dict(c)

def extract(path, ep_id):
    with open(path) as f:
        r = json.load(f)
    steps = r["steps"]
    n = len(steps)
    teams = r.get("info", {}).get("TeamNames", ["P0","P1"])
    seed = r.get("info", {}).get("seed")
    rewards = r.get("rewards") or [steps[-1][p].get("reward") for p in range(2)]

    out = {
        "ep": ep_id, "seed": seed, "teams": teams, "rewards": rewards,
        "n_steps": n,
        "players": [], "market_daily": [], "final_inv": None,
    }

    # per-player daily accumulation
    P = []
    for p in range(2):
        P.append({
            "money_d": [None]*30, "money_eod": [None]*30, "crew_d": [None]*30, "quad_d": [None]*30,
            "tiles_d": [None]*30, "shed_d": [None]*30,
            "sell_units": defaultdict(lambda: [0]*30),  # item -> per-day units (attributed)
            "sell_req": defaultdict(lambda: [0]*30),    # requested (order volume)
            "buy_seed": defaultdict(lambda: [0]*30),
            "buy_animal": defaultdict(lambda: [0]*30),
            "buy_prod": defaultdict(lambda: [0]*30),
            "hires_d": [0]*30, "land_d": [0]*30,
            "acts": defaultdict(int),                   # action op totals
            "plant_crop": defaultdict(int),
            "final_shed": None, "final_money": None,
        })

    prev_inv = None
    # combined requested sells per step (for attribution) and market deltas
    # we walk steps; obs[t][p].observation is the state BEFORE action t.
    for t in range(n):
        day = t // 24
        if day > 29: day = 29
        obs0 = steps[t][0]["observation"]
        mkt = obs0.get("market", {})
        inv = mkt.get("inventory", {})
        px = mkt.get("prices", {})
        town = obs0.get("town", {})
        shops = town.get("unlocked_shops", []) if isinstance(town, dict) else []

        if t % 24 == 0:  # day start snapshot
            out["market_daily"].append({
                "day": day,
                "inv": {k: inv.get(k) for k in ITEMS},
                "px": {k: px.get(k) for k in ITEMS},
                "shops": list(shops),
            })

        farms = obs0.get("farms", [])
        # request book for this step
        req_sell = [defaultdict(int), defaultdict(int)]
        for p in range(2):
            a = steps[t][p].get("action") or {}
            mk = a.get("market", []) if isinstance(a, dict) else []
            if not isinstance(mk, list): mk = []
            for o in mk[:10]:
                if isinstance(o, list) and len(o) >= 3 and o[0] in ("SELL","BUY_SEED","BUY_ANIMAL","BUY_PRODUCT"):
                    try: q = int(o[2])
                    except: continue
                    if q <= 0: continue
                    key = {"SELL":"sell_req","BUY_SEED":"buy_seed","BUY_ANIMAL":"buy_animal","BUY_PRODUCT":"buy_prod"}[o[0]]
                    P[p][key][o[1]][day] += q
                elif isinstance(o, list) and o and o[0] in ("HIRE","BUY_LAND"):
                    if o[0] == "HIRE": P[p]["hires_d"][day] += 1
                    elif o[0] == "BUY_LAND": P[p]["land_d"][day] += 1
            # unit action counts
            fa = a.get("farmer"); ha = a.get("hands", []) if isinstance(a, dict) else []
            for ua in ([fa] + list(ha)):
                if isinstance(ua, list) and ua:
                    op = ua[0]
                    P[p]["acts"][op] += 1
                    if op == "PLANT" and len(ua) > 1: P[p]["plant_crop"][ua[1]] += 1

        # money/crew/tiles at this step (from shared farms)
        for p in range(2):
            if p < len(farms):
                fm = farms[p]
                if t % 24 == 0 or t == n-1:
                    P[p]["money_d"][day] = fm.get("money")
                    P[p]["quad_d"][day] = len(fm.get("unlocked_quadrants", []))
                # crew = max over day (hands despawn EOD, h0 always shows 1)
                c = 1 + len(fm.get("hands", []))
                if P[p]["crew_d"][day] is None or c > P[p]["crew_d"][day]:
                    P[p]["crew_d"][day] = c
                if t % 24 == 23 or t == n-1:
                    P[p]["tiles_d"][day] = tile_census(fm.get("tiles", []))
                # day-end money
                if t % 24 == 23 or t == n-1:
                    P[p]["money_eod"][day] = fm.get("money")

        # market delta attribution vs next step (executed sells combined)
        if prev_inv is not None and t > 0:
            pass
        prev_inv = dict(inv)

    # SECOND PASS: executed sells per item per day per player via market inv deltas.
    # delta_inv[t] = sells_p0 + sells_p1 - prod_buys - town_cons ; attribute by request share.
    for it in ITEMS:
        for day in range(30):
            t0, t1 = day*24, min((day+1)*24, n)
            if t0 >= n: break
            inv_a = steps[t0][0]["observation"]["market"]["inventory"].get(it, 10000)
            inv_b = steps[t1-1][0]["observation"]["market"]["inventory"].get(it, 10000) if t1-1 < n else inv_a
            # need inv at day END (after last step of day): use next day's first obs if exists
            if t1 < n:
                inv_end = steps[t1][0]["observation"]["market"]["inventory"].get(it, 10000)
            else:
                inv_end = steps[n-1][0]["observation"]["market"]["inventory"].get(it, 10000)
            delta = inv_end - inv_a
            # town consumption for the day
            cons = 0
            shops_at = steps[t0][0]["observation"].get("town", {}).get("unlocked_shops", [])
            for t in range(t0, t1):
                d = town_consumption(t, shops_at)
                cons += -d.get(it, 0)
            # executed product buys (approx = requested, only WHEAT/FERT possible)
            buys = P[0]["buy_prod"][it][day] + P[1]["buy_prod"][it][day]
            sells_total = delta + cons + buys
            if sells_total < 0: sells_total = 0
            # attribute by requested share
            r0 = P[0]["sell_req"][it][day]; r1 = P[1]["sell_req"][it][day]
            tot_req = r0 + r1
            if tot_req > 0:
                P[0]["sell_units"][it][day] = round(sells_total * r0 / tot_req, 1)
                P[1]["sell_units"][it][day] = round(sells_total * r1 / tot_req, 1)
            elif sells_total > 0:
                P[0]["sell_units"][it][day] = round(sells_total / 2, 1)

    # final states + shed values
    fin = steps[n-1][0]["observation"]
    out["final_inv"] = {k: fin["market"]["inventory"].get(k) for k in ITEMS}
    out["final_px"] = {k: fin["market"]["prices"].get(k) for k in ITEMS}
    for p in range(2):
        # own shed from own obs
        po = steps[n-1][p].get("observation", {})
        shed = (po.get("private", {}) or {}).get("shed", {})
        P[p]["final_shed"] = dict(shed)
        fm = fin["farms"][p] if p < len(fin.get("farms", [])) else {}
        P[p]["final_money"] = fm.get("money")
        P[p]["shed_value"] = sum(shed.get(k,0) * (out["final_px"].get(k) or 0) for k in ITEMS)
        # compress dicts
        P[p]["sell_units"] = {k: v for k, v in P[p]["sell_units"].items() if any(x > 0 for x in v)}
        P[p]["sell_req"] = {k: v for k, v in P[p]["sell_req"].items() if any(x > 0 for x in v)}
        P[p]["buy_seed"] = {k: v for k, v in P[p]["buy_seed"].items() if any(x > 0 for x in v)}
        P[p]["buy_animal"] = {k: v for k, v in P[p]["buy_animal"].items() if any(x > 0 for x in v)}
        P[p]["buy_prod"] = {k: v for k, v in P[p]["buy_prod"].items() if any(x > 0 for x in v)}
        P[p]["plant_crop"] = dict(P[p]["plant_crop"])
        P[p]["acts"] = dict(P[p]["acts"])
        out["players"].append(P[p])
    return out

if __name__ == "__main__":
    path = sys.argv[1]
    m = re.search(r"(\d+)", os.path.basename(path))
    ep_id = int(m.group(1)) if m else 0
    out = extract(path, ep_id)
    os.makedirs("/home/user/intel/eps", exist_ok=True)
    with gzip.open(f"/home/user/intel/eps/ep_{ep_id}.json.gz", "wt") as f:
        json.dump(out, f)
    print(f"ep_{ep_id}: {' vs '.join(out['teams'])} rewards={out['rewards']}")
