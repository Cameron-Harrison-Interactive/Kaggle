#!/usr/bin/env python3
"""Ladder replay analyzer (R51+). Parses kaggle replay JSONs (kaggle competitions replay <id>)
and reports, per episode + aggregate, the things we actually care about:
  W/L, final leftovers (carried goods / on-plant units / idle seeds / unspent cash),
  dirt-by-day (owned non-LOCKED tiles that are None), late milk/wool/egg prices vs our herd,
  animal buy days, sell volume by good.

Usage: python3 war/ladder_replay_analysis.py /tmp/replays [--team "Harrison Interactive"] [--days 25] [--ep 109082582]
"""
import json, glob, sys, argparse, collections

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--team", default="Harrison Interactive")
ap.add_argument("--days", default="20,23,25,27,29")
ap.add_argument("--ep", default=None)
args = ap.parse_args()

GOODS = ["MILK", "WOOL", "EGG", "STRAWBERRY", "MELON", "WHEAT", "CARROT", "TOMATO"]
ANIMALS = ["COW", "SHEEP", "GOOSE"]

def farm_of(obs, k):
    return obs["farms"][k]

def owned_tiles(farm):
    out = []
    for row in farm["tiles"]:
        for t in row:
            if t != "LOCKED":
                out.append(t)
    return out

def dirt_weed_planted(farm):
    d = w = p = 0
    for t in owned_tiles(farm):
        if t is None: d += 1
        elif isinstance(t, dict) and t.get("crop") == "WEED": w += 1
        elif isinstance(t, dict): p += 1
    return d, w, p

def on_plant_units(farm):
    tot = collections.Counter()
    for t in owned_tiles(farm):
        if isinstance(t, dict) and t.get("yield_units"):
            tot[t["crop"]] += t["yield_units"]
    return tot

def herd(shed):
    return {a: shed.get(a, 0) for a in ANIMALS}

episodes = []
for fn in sorted(glob.glob(args.dir + "/episode-*-replay.json")):
    r = json.load(open(fn))
    tn = r["info"]["TeamNames"]
    ep_id = r["info"]["EpisodeId"]
    if args.ep and str(ep_id) != args.ep: continue
    if args.team in tn:
        us = tn.index(args.team)
    else:
        us = 0  # validation vs self: just take p0
    them = 1 - us
    steps = r["steps"]
    n = len(steps)

    our_reward = steps[-1][us]["reward"]
    opp_reward = steps[-1][them]["reward"] if len(tn) == 2 or True else None
    opp_name = tn[them] if tn[them] != args.team else "(self/validation)"

    # index steps by (day, hour) from OUR obs
    by_day = {}
    for i in range(n):
        o = steps[i][us]["observation"]
        by_day.setdefault(o["day"], []).append(i)

    days_report = [int(x) for x in args.days.split(",")]

    # dirt by day (max within the day, us / them)
    dirt_us, dirt_them, herd_us, herd_them, money_us = {}, {}, {}, {}, {}
    for d in sorted(by_day):
        du = dt = 0
        for i in by_day[d]:
            o = steps[i][us]["observation"]
            a, _, _ = dirt_weed_planted(farm_of(o, us))
            b, _, _ = dirt_weed_planted(farm_of(o, them))
            du = max(du, a); dt = max(dt, b)
        dirt_us[d], dirt_them[d] = du, dt
        last = by_day[d][-1]
        o = steps[last][us]["observation"]
        herd_us[d] = herd(o["private"]["shed"])
        herd_them[d] = herd(o["private"]["shed"] if False else steps[last][them]["observation"]["private"]["shed"])
        money_us[d] = farm_of(o, us)["money"]

    # final state
    last_o = steps[n-1][us]["observation"]
    fin_farm = farm_of(last_o, us)
    fin_priv = last_o["private"]
    carried = dict(fin_priv["inventories"][0]) if fin_priv["inventories"] else {}
    fin_shed = fin_priv["shed"]
    idle_seeds = {k: v for k, v in fin_shed.items() if k in ("CARROT","MELON","STRAWBERRY","TOMATO","WHEAT") and v > 0}
    fin_herd = herd(fin_shed)
    fin_units = on_plant_units(fin_farm)
    fin_prices = last_o["market"]["prices"]
    fin_inv_market = last_o["market"]["inventory"]

    # prices at report days (hour 23)
    px_at = {}
    for d in sorted(by_day):
        o = steps[by_day[d][-1]][us]["observation"]
        px_at[d] = o["market"]["prices"]

    # actions: sells by good (us), animal buys with day, crew size
    sells = collections.Counter()
    buys_animals = []  # (day, what, qty)
    hires = []
    for i in range(n):
        a = steps[i][us]["action"]
        o = steps[i][us]["observation"]
        d = o["day"]
        for op in a.get("market", []):
            if len(op) >= 3 and op[0] == "SELL": sells[op[1]] += op[2]
            elif len(op) >= 3 and op[0] == "BUY" and op[1] in ANIMALS: buys_animals.append((d, op[1], op[2]))
        fa = a.get("farmer", [])
        if fa and fa[0] == "HIRE": hires.append(d)

    episodes.append(dict(ep=ep_id, opp=opp_name, us=us, r_us=our_reward, r_opp=opp_reward,
                         dirt_us=dirt_us, dirt_them=dirt_them, herd_us=herd_us, herd_them=herd_them,
                         money_us=money_us, carried=carried, fin_herd=fin_herd, fin_units=dict(fin_units),
                         idle_seeds=idle_seeds, fin_prices=fin_prices, px_at=px_at,
                         sells=dict(sells), buys_animals=buys_animals, fin_money=fin_farm["money"],
                         crew=len(fin_farm["hands"]), unlocked=fin_farm["unlocked_quadrants"],
                         statuses=steps[-1][us]["status"]))

# ---- report ----
W = L = 0
print(f"{'ep':>10} {'opp':<24} {'us':>8} {'them':>8} {'W/L':<3} | d25dirt us/th | fin herd C/S/G | MILKpx WOOLpx EGGpx | carried$ ~onplant | endcash")
tot = []
for e in episodes:
    win = e["r_us"] > e["r_opp"]
    W += win; L += (not win)
    d25u = e["dirt_us"].get(25, 0); d25t = e["dirt_them"].get(25, 0)
    fp = e["fin_prices"]
    carried_val = sum({"MILK":160,"WOOL":200,"EGG":50,"STRAWBERRY":120,"MELON":250,"WHEAT":25,"CARROT":35,"TOMATO":60}.get(k, 0)*v for k, v in e["carried"].items())
    op_units = sum(e["fin_units"].values())
    h = e["fin_herd"]
    print(f"{e['ep']:>10} {e['opp'][:24]:<24} {e['r_us']:>8.0f} {e['r_opp']:>8.0f} {'W' if win else 'L':<3} | {d25u:>4}/{d25t:<4} | {h['COW']}/{h['SHEEP']}/{h['GOOSE']} | {fp['MILK']:>6.0f} {fp['WOOL']:>6.0f} {fp['EGG']:>5.0f} | {carried_val:>7.0f} {op_units:>5} | {e['fin_money']:>7.0f}")
    tot.append(e)

print(f"\n=== RECORD: {W}-{L} over {len(episodes)} episodes ===")

def agg(name, f):
    vals = [f(e) for e in tot]
    print(f"{name:<44} avg={sum(vals)/len(vals):8.1f}  min={min(vals):8.1f}  max={max(vals):8.1f}")

print("\n=== AGGREGATES (us) ===")
agg("final money", lambda e: e["fin_money"])
agg("dirt d25 (max in day)", lambda e: e["dirt_us"].get(25, 0))
agg("dirt d29 (max in day)", lambda e: e["dirt_us"].get(29, 0))
agg("final cows", lambda e: e["fin_herd"]["COW"])
agg("final sheep", lambda e: e["fin_herd"]["SHEEP"])
agg("final geese", lambda e: e["fin_herd"]["GOOSE"])
agg("final MILK px", lambda e: e["fin_prices"]["MILK"])
agg("final WOOL px", lambda e: e["fin_prices"]["WOOL"])
agg("final EGG px", lambda e: e["fin_prices"]["EGG"])
agg("milk sold units", lambda e: e["sells"].get("MILK", 0))
agg("wool sold units", lambda e: e["sells"].get("WOOL", 0))
agg("egg sold units", lambda e: e["sells"].get("EGG", 0))

print("\n=== LEFTOVER DETAIL (carried goods + on-plant units at end, us) ===")
for e in tot:
    print(f"{e['ep']} vs {e['opp'][:20]:<20} carried={e['carried']} onplant={e['fin_units']} idle_seeds={e['idle_seeds']} endcash={e['fin_money']:.0f} crew={e['crew']} unlocked={e['unlocked']}")

print("\n=== ANIMAL BUYS (day, kind, qty) us ===")
for e in tot:
    if e["buys_animals"]:
        print(f"{e['ep']} vs {e['opp'][:20]:<20} {e['buys_animals']}")

print("\n=== LATE PRICES: milk/wool/egg at d20 / d25 / d29 ===")
for e in tot:
    def g(d, k): return e["px_at"].get(d, {}).get(k, 0)
    print(f"{e['ep']} vs {e['opp'][:20]:<20} milk {g(20,'MILK'):>5.0f}/{g(25,'MILK'):>5.0f}/{g(29,'MILK'):>5.0f}  wool {g(20,'WOOL'):>5.0f}/{g(25,'WOOL'):>5.0f}/{g(29,'WOOL'):>5.0f}  egg {g(20,'EGG'):>5.0f}/{g(25,'EGG'):>5.0f}/{g(29,'EGG'):>5.0f}")
