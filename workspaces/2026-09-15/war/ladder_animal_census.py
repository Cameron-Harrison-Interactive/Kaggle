#!/usr/bin/env python3
"""R51 deep animal-census on ladder replays: placed animals, feed coverage, escapes,
animal-program P&L, and TRUE end leftovers (full shed dump)."""
import json, glob, collections, sys

ANIMALS = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
PROD = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}

def tile_animals(farm):
    out = collections.Counter()
    fed = 0
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict) and "animal" in t:
                out[t["animal"]] += 1
                if t.get("fed_today"): fed += 1
    return out, fed

tot = collections.Counter()
eps = []
for fn in sorted(glob.glob("/tmp/replays/episode-*-replay.json")):
    r = json.load(open(fn))
    tn = r["info"]["TeamNames"]
    us = tn.index("Harrison Interactive") if "Harrison Interactive" in tn else 0
    them = 1 - us
    steps = r["steps"]; n = len(steps)
    opp = tn[them] if tn[them] != "Harrison Interactive" else "(self)"

    # per-day: placed herd, fed count at h23, escapes (placed drop day-over-day)
    daily = {}
    prev_placed = collections.Counter()
    for i in range(n):
        o = steps[i][us]["observation"]
        d, h = o["day"], o["hour"]
        placed, fed = tile_animals(o["farms"][us])
        if h == 23:
            escaped = {k: prev_placed[k] - placed[k] for k in prev_placed if prev_placed[k] > placed[k]}
            daily[d] = dict(placed=dict(placed), fed=fed, escaped=dict(escaped),
                            unfed=sum(placed.values()) - fed,
                            consec_unfed_1=sum(1 for row in o["farms"][us]["tiles"] for t in row
                                               if isinstance(t, dict) and "animal" in t and t.get("consecutive_unfed", 0) == 1))
            prev_placed = placed

    # animal program P&L from actions
    spend_animals = 0; feed_buy_cost = 0; feed_units = 0
    buys = collections.Counter(); sells = collections.Counter(); fert_sold = 0
    for i in range(n):
        a = steps[i][us]["action"]; o = steps[i][us]["observation"]
        for op in a.get("market", []):
            if op[0] == "BUY_ANIMAL": spend_animals += ANIMALS[op[1]] * op[2]; buys[op[1]] += op[2]
            elif op[0] == "BUY_PRODUCT" and op[1] == "WHEAT":
                feed_units += op[2]; feed_buy_cost += op[2] * o["market"]["prices"]["WHEAT"]
            elif op[0] == "SELL":
                sells[op[1]] += op[2]
                if op[1] == "FERTILIZER": fert_sold += op[2]

    # TRUE end leftovers: full shed dump + carried + on-plant
    last_o = steps[n-1][us]["observation"]
    shed = last_o["private"]["shed"]
    shed_goods = {k: v for k, v in shed.items() if v > 0}
    carried = last_o["private"]["inventories"][0] if last_o["private"]["inventories"] else {}
    onplant = collections.Counter()
    for row in last_o["farms"][us]["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("yield_units") and "animal" not in t:
                onplant[t["crop"]] += t["yield_units"]
    # animals still in shed at end (bought, never placed = dead money)
    shed_animals = {k: shed.get(k, 0) for k in ANIMALS if shed.get(k, 0)}

    # revenue estimate for animal goods using day price at sell time (approx: use px at that step)
    rev = collections.Counter()
    for i in range(n):
        a = steps[i][us]["action"]; o = steps[i][us]["observation"]
        for op in a.get("market", []):
            if op[0] == "SELL" and op[1] in ("MILK", "WOOL", "EGG", "FERTILIZER"):
                rev[op[1]] += op[2] * o["market"]["prices"][op[1]]
    animal_rev = rev["MILK"] + rev["WOOL"] + rev["EGG"] + rev["FERTILIZER"]
    net = animal_rev - spend_animals - feed_buy_cost

    eps.append(dict(ep=r["info"]["EpisodeId"], opp=opp, daily=daily, buys=dict(buys), sells=dict(sells),
                    spend=spend_animals, feed_cost=feed_buy_cost, feed_units=feed_units,
                    animal_rev=animal_rev, net=net, rev=dict(rev), shed_goods=shed_goods,
                    carried=dict(carried), onplant=dict(onplant), shed_animals=shed_animals,
                    r_us=steps[-1][us]["reward"], r_opp=steps[-1][them]["reward"]))

print("=== ANIMAL PROGRAM P&L (us, per episode) ===")
print(f"{'ep':>10} {'opp':<20} {'buys C/S/G':<12} {'spend':>6} {'feed$':>6} {'animRev':>8} {'NET':>8} | escapes total | animal-days unfed | end shed")
for e in eps:
    esc = sum(sum(dd["escaped"].values()) for dd in e["daily"].values())
    unfed = sum(dd["unfed"] for dd in e["daily"].values())
    b = e["buys"]
    print(f"{e['ep']:>10} {e['opp'][:20]:<20} {b.get('COW',0)}/{b.get('SHEEP',0)}/{b.get('GOOSE',0):<6} {e['spend']:>6.0f} {e['feed_cost']:>6.0f} {e['animal_rev']:>8.0f} {e['net']:>8.0f} | {esc:>4} | {unfed:>5} | {e['shed_goods']} {e['shed_animals']}")

print("\n=== AGGREGATE ===")
n = len(eps)
for k in ["spend", "feed_cost", "animal_rev", "net"]:
    print(f"{k:<12} avg={sum(e[k] for e in eps)/n:8.0f}")
tot_buys = collections.Counter()
for e in eps: tot_buys.update(e["buys"])
print("total buys:", dict(tot_buys))
tot_sells = collections.Counter()
for e in eps: tot_sells.update(e["sells"])
print("total sells:", dict(tot_sells))
tot_esc = sum(sum(dd["escaped"].values()) for e in eps for dd in e["daily"].values())
tot_unfed = sum(dd["unfed"] for dd in e["daily"].values() for e in [x for x in eps if dd in x["daily"].values()])
print("total escapes (all eps):", tot_esc)

print("\n=== TRUE END LEFTOVERS (full shed + carried + on-plant, nonempty only) ===")
for e in eps:
    nz = {**e["shed_goods"], **{("carried:"+k): v for k, v in e["carried"].items()},
          **{("onplant:"+k): v for k, v in e["onplant"].items()}, **{("shedA:"+k): v for k, v in e["shed_animals"].items()}}
    if nz:
        print(f"{e['ep']} vs {e['opp'][:18]:<18} {nz}")

print("\n=== ONE EPISODE DETAIL (last one): placed/fed/unfed/escaped by day ===")
e = eps[-1]
for d in sorted(e["daily"]):
    dd = e["daily"][d]
    if dd["placed"] or dd["escaped"]:
        print(f"  d{d}: placed={dd['placed']} fed={dd['fed']} unfed={dd['unfed']} neardeath(consec1)={dd['consec_unfed_1']} escaped={dd['escaped']}")
