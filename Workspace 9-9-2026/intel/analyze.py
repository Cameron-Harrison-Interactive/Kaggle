#!/usr/bin/env python3
"""War-model intel analysis over harvested episodes."""
import json, gzip, glob, statistics as st
from collections import defaultdict

EPS = sorted(glob.glob("/home/user/intel/eps/ep_*.json.gz"))
data = []
for f in EPS:
    try: data.append(json.load(gzip.open(f)))
    except Exception: pass
print(f"loaded {len(data)} episodes")

ITEMS = ["WHEAT","CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL","FERTILIZER"]

# ---------- 1. team table ----------
teamstats = defaultdict(lambda: {"eps":0,"wins":0,"gold":[],"best":0})
for d in data:
    r0, r1 = d["rewards"]
    if r0 is None or r1 is None: continue
    for p, (name, rew, other) in enumerate([(d["teams"][0], r0, r1), (d["teams"][1], r1, r0)]):
        if name == "US": name = "Harrison Interactive(US)"
        ts = teamstats[name]
        ts["eps"] += 1
        ts["gold"].append(rew)
        if rew > other: ts["wins"] += 1
        ts["best"] = max(ts["best"], rew)

rows = sorted(teamstats.items(), key=lambda kv: -st.median(kv[1]["gold"]))
print("\n=== TEAM TABLE (by median gold) ===")
print(f"{'team':32s} {'eps':>4s} {'W':>4s} {'med':>8s} {'avg':>8s} {'max':>8s}")
for name, ts in rows[:50]:
    print(f"{name[:32]:32s} {ts['eps']:4d} {ts['wins']:4d} {st.median(ts['gold']):8.0f} {st.mean(ts['gold']):8.0f} {ts['best']:8.0f}")

# ---------- 2. winner vs loser patterns ----------
def day_units(pl, it): return sum(pl["sell_units"].get(it, [0]*30))
win_feats = []; lose_feats = []
for d in data:
    r0, r1 = d["rewards"]
    if r0 is None or r1 is None or abs(r0-r1) < 1: continue
    w = 0 if r0 > r1 else 1
    for p, store in ((w, win_feats), (1-w, lose_feats)):
        pl = d["players"][p]
        sells = {it: day_units(pl, it) for it in ITEMS}
        tot = sum(sells.values()) or 1
        store.append({
            "gold": d["rewards"][p],
            "crew_max": max([c or 1 for c in pl["crew_d"]]),
            "quads": max([q or 1 for q in pl["quad_d"]]),
            "animals": sum(v for k, v in (pl["tiles_d"][29] or {}).items() if k.startswith("an:")),
            "fert_sold": sells["FERTILIZER"],
            "wheat_sh": sells["WHEAT"]/tot,
            "animal_sh": (sells["MILK"]+sells["WOOL"]+sells["EGG"])/tot,
            "melon_sh": sells["MELON"]/tot,
            "strb_sh": sells["STRAWBERRY"]/tot,
            "carrot_sh": sells["CARROT"]/tot,
            "wheat_u": sells["WHEAT"], "milk_u": sells["MILK"], "wool_u": sells["WOOL"],
            "strb_u": sells["STRAWBERRY"], "melon_u": sells["MELON"], "egg_u": sells["EGG"],
            "fert_u": sells["FERTILIZER"], "carrot_u": sells["CARROT"],
        })

def med(store, k): 
    v = [x[k] for x in store if x[k] is not None]
    return st.median(v) if v else 0
print("\n=== WINNERS vs LOSERS (medians) ===")
print(f"{'feature':16s} {'winners':>10s} {'losers':>10s}")
for k in ["gold","crew_max","quads","animals","fert_sold","wheat_sh","animal_sh","melon_sh","strb_sh","carrot_sh","wheat_u","milk_u","wool_u","strb_u","melon_u","egg_u","fert_u","carrot_u"]:
    print(f"{k:16s} {med(win_feats,k):10.1f} {med(lose_feats,k):10.1f}")

# ---------- 3. market inventory paths (day 0,7,14,21,29) ----------
print("\n=== MARKET INVENTORY (median across all eps; I0=10000) ===")
hdr = "item     " + "".join(f"  d{d:02d}   " for d in (0,7,14,21,29))
print(hdr)
mkt_paths = {it: {d: [] for d in (0,7,14,21,29)} for it in ITEMS}
px_end = {it: [] for it in ITEMS}
for d in data:
    md = d["market_daily"]
    for it in ITEMS:
        for dd in (0,7,14,21,29):
            if dd < len(md):
                mkt_paths[it][dd].append(md[dd]["inv"].get(it, 10000))
        px_end[it].append(d["final_px"].get(it, 0))
for it in ITEMS:
    row = f"{it:9s}" + "".join(f"{st.median(mkt_paths[it][dd]):7.0f} " for dd in (0,7,14,21,29))
    row += f" | end px med {st.median(px_end[it]):4.0f}  %eps<$10: {100*sum(1 for x in px_end[it] if x<10)/len(px_end[it]):3.0f}%"
    print(row)

# ---------- 4. money timing (winners) ----------
print("\n=== WINNER money curve (median EOD money by day) ===")
curve = {d: [] for d in range(30)}
for x in win_feats: pass
wcurves = []
for d in data:
    r0, r1 = d["rewards"]
    if r0 is None or r1 is None: continue
    w = 0 if r0 > r1 else 1
    mc = d["players"][w].get("money_eod") or [None]*30
wcurves.append(mc)
days = [0,5,10,15,20,25,28,29]
print("day:  " + " ".join(f"{d:7d}" for d in days))
print("med:  " + " ".join(f"{st.median([c[d] for c in wcurves if c[d] is not None]):7.0f}" for d in days))
# share of final gold earned by day
shares = []
for c in wcurves:
    fin = c[29]
    if not fin: continue
    m20 = c[20] or 0
    shares.append(max(0,(fin-m20))/fin if fin>0 else 0)
print(f"winner share of final gold earned AFTER day 20: median {st.median(shares)*100:.0f}%")

# ---------- 5. endgame: shed value left ----------
sv_w = [x for x in (d["players"][0]["shed_value"] for d in data)]
sv_all = []
for d in data:
    for p in range(2): sv_all.append(d["players"][p]["shed_value"])
print(f"\n=== ENDGAME SHED VALUE (gold left on table at horn) ===")
print(f"median {st.median(sv_all):.0f}, mean {st.mean(sv_all):.0f}, p90 {sorted(sv_all)[int(.9*len(sv_all))]:.0f}")
big = sum(1 for x in sv_all if x > 2000)
print(f"players leaving >$2000 in shed: {big}/{len(sv_all)} ({100*big/len(sv_all):.0f}%)")

# ---------- 6. revenue-by-item proxy: units*avg price per day ----------
# approximate revenue per item per player: sum over days of units[d]*px_at_h0[d]
rev_item = defaultdict(list)
for d in data:
    md = d["market_daily"]
    for p in range(2):
        pl = d["players"][p]
        revs = {}
        for it in ITEMS:
            u = pl["sell_units"].get(it)
            if not u: continue
            r = 0
            for day in range(30):
                if u[day] and day < len(md):
                    r += u[day] * (md[day]["px"].get(it) or 0)
            revs[it] = r
        tot = sum(revs.values()) or 1
        for it, r in revs.items():
            rev_item[it].append(r / tot)
print("\n=== REVENUE SHARE BY ITEM (median share of a player's sell revenue) ===")
for it in ITEMS:
    v = rev_item[it]
    if v: print(f"{it:12s} med share {st.median(v)*100:5.1f}%   players selling any: {len(v)}/{len(data)*2}")

json.dump({"teams": {k: {"eps":v["eps"],"wins":v["wins"],"med":st.median(v["gold"]),"avg":st.mean(v["gold"]),"max":v["best"]} for k,v in teamstats.items()}},
          open("/home/user/intel/team_stats.json","w"), indent=1)
print("\nsaved team_stats.json")
