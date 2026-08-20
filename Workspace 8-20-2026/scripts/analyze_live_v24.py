#!/usr/bin/env python3
"""analyze_live_v24.py — fine-toothed forensic pass over ALL of v24's live episodes.

For each episode: download the replay, extract a compact fingerprint
(escapes, failed plants/buys/sells, per-day money/crops/animals/weeds,
opponent opening + key-day market signatures, the divergence point),
save it to data/live_v24/<episode>.json, delete the 28MB replay.

Then aggregate: data/live_v24/SUMMARY.json + a printed report.
"""
import json
import os
import subprocess
import sys

OUT = "/home/user/kaggriculture/data/live_v24"
os.makedirs(OUT, exist_ok=True)
OUR_TEAM = "Harrison Interactive"

SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}


def fmt(o):
    if not o:
        return ""
    if len(o) == 1:
        return o[0]
    if len(o) == 2:
        return f"{o[0]}:{o[1]}"
    return f"{o[0]}:{o[1]}{o[2]}"


def analyze(path):
    replay = json.load(open(path))
    steps = replay["steps"]
    info = replay.get("info") or {}
    teams = info.get("TeamNames") or ["?", "?"]
    seed = info.get("seed")
    our_seat = 0 if teams[0] == OUR_TEAM else 1
    opp_seat = 1 - our_seat

    fin = steps[-1]
    res = {
        "episode": info.get("EpisodeId"),
        "teams": teams,
        "opponent": teams[opp_seat],
        "seed": seed,
        "our_seat": our_seat,
        "final_us": fin[our_seat].get("reward"),
        "final_opp": fin[opp_seat].get("reward"),
    }

    # per-player step-level audit
    escapes = {0: [], 1: []}
    failed_plants = {0: {}, 1: {}}   # (day, crop) -> count
    failed_seed_buys = {0: [], 1: []}
    failed_sells = {0: [], 1: []}    # sells with empty shed
    prev_anim = {0: {}, 1: {}}
    daily = {0: [], 1: []}           # per-day: money, animals, plants, weeds
    shed_empty_sells = {0: 0, 1: 0}

    for si in range(720):
        for p in (0, 1):
            obs = steps[si][p].get("observation") or {}
            farm = (obs.get("farms") or [{}])[p]
            priv = obs.get("private") or {}
            cur = {}
            plants = weeds = 0
            for y, row in enumerate(farm.get("tiles") or []):
                for x, t in enumerate(row):
                    if isinstance(t, dict):
                        if t.get("animal"):
                            cur[(x, y)] = t["animal"]
                        elif t.get("kind") == "PLANT":
                            plants += 1
                        elif t.get("kind") == "WEED":
                            weeds += 1
            for pos, a in prev_anim[p].items():
                if pos not in cur:
                    escapes[p].append({"day": si // 24, "tile": list(pos), "animal": a})
            prev_anim[p] = cur
            if si % 24 == 0:
                daily[p].append({"d": si // 24, "money": round(farm.get("money") or 0),
                                 "animals": len(cur), "plants": plants, "weeds": weeds})
            act = steps[si][p].get("action") or {}
            seeds = dict(priv.get("seeds") or {})
            shed = dict(priv.get("shed") or {})
            money = farm.get("money") or 0
            for k in ("farmer", "hands"):
                units = [act.get(k)] if k == "farmer" else (act.get("hands") or [])
                for u in units:
                    if u and u[0] == "PLANT" and len(u) > 1 and seeds.get(u[1], 0) <= 0:
                        key = (si // 24, u[1])
                        failed_plants[p][str(key)] = failed_plants[p].get(str(key), 0) + 1
            for o in (act.get("market") or []):
                if o and o[0] == "BUY_SEED" and len(o) > 2:
                    cost = SEED_COST.get(o[1], 99) * int(o[2])
                    if money < cost:
                        failed_seed_buys[p].append((si // 24, o[1], int(o[2])))
                if o and o[0] == "SELL" and len(o) > 2 and shed.get(o[1], 0) <= 0 and int(o[2]) > 0:
                    failed_sells[p].append((si // 24, o[1], int(o[2])))

    res["escapes_us"] = escapes[our_seat]
    res["escapes_opp"] = escapes[opp_seat]
    res["failed_plants_us"] = failed_plants[our_seat]
    res["failed_plants_opp"] = failed_plants[opp_seat]
    res["failed_seed_buys_us"] = failed_seed_buys[our_seat]
    res["failed_sells_us"] = failed_sells[our_seat]
    res["failed_sells_opp"] = failed_sells[opp_seat]
    res["daily_us"] = daily[our_seat]
    res["daily_opp"] = daily[opp_seat]

    # opponent signatures
    def market_at(p, t):
        return [fmt(o) for o in (steps[t + 1][p].get("action") or {}).get("market") or []]
    res["opp_d0h0"] = market_at(opp_seat, 0)
    res["opp_d0h1"] = market_at(opp_seat, 1)
    res["opp_d10h1"] = market_at(opp_seat, 10 * 24 + 1)
    res["opp_d10h2"] = market_at(opp_seat, 10 * 24 + 2)
    # wheat flood d27-29 (sell wheat total)
    wf = 0
    for t in range(27 * 24, min(30 * 24, 719)):
        for o in (steps[t + 1][opp_seat].get("action") or {}).get("market") or []:
            if o and o[0] == "SELL" and o[1] == "WHEAT":
                wf += int(o[2])
    res["opp_wheat_flood_d27_29"] = wf
    # opp d0 wheat buy qty
    qty = 0
    for o in (steps[1][opp_seat].get("action") or {}).get("market") or []:
        if o and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT":
            qty += int(o[2])
    res["opp_d0_wheat_qty"] = qty

    # our own metrics
    res["our_max_crops"] = max(d["plants"] for d in daily[our_seat])
    res["our_max_animals"] = max(d["animals"] for d in daily[our_seat])
    res["our_end_animals"] = daily[our_seat][-1]["animals"]

    # divergence: first day opp leads by >=3000 and keeps leading to the end
    lead_start = None
    for i in range(30):
        d_us = daily[our_seat][i]["money"]
        d_opp = daily[opp_seat][i]["money"]
        if d_opp - d_us >= 3000:
            lead_start = i
            break
    res["opp_lead_start_day"] = lead_start
    return res


def main():
    ids = [l.strip() for l in open("/home/user/episodes_v24.txt") if l.strip()]
    done = {f.replace(".json", "") for f in os.listdir(OUT) if f.endswith(".json")}
    todo = [i for i in ids if i not in done]
    print(f"{len(ids)} episodes total, {len(done)} done, {len(todo)} to process", flush=True)
    results = []
    for eid in todo:
        rp = f"/home/user/episode-{eid}-replay.json"
        if not os.path.exists(rp):
            subprocess.run(["kaggle", "competitions", "replay", eid, "-p", "/home/user", "-q"],
                           capture_output=True)
            # the CLI names the file itself; find it
            import glob
            cands = glob.glob(f"/home/user/episode-{eid}-replay.json")
            if not cands:
                print(f"  {eid}: download failed", flush=True)
                continue
            rp = cands[0]
        try:
            res = analyze(rp)
        except Exception as e:
            print(f"  {eid}: analysis error {e}", flush=True)
            os.remove(rp)
            continue
        os.remove(rp)
        with open(os.path.join(OUT, f"{eid}.json"), "w") as f:
            json.dump(res, f)
        results.append(res)
        wl = "WIN " if res["final_us"] > res["final_opp"] else "LOSS"
        print(f"  {eid}: {wl} {res['final_us']:,.0f} vs {res['final_opp']:,.0f} "
              f"({res['opponent']:30s}) esc_us={len(res['escapes_us'])} "
              f"fp={sum(res['failed_plants_us'].values())} "
              f"maxcrops={res['our_max_crops']}", flush=True)

    # aggregate
    allres = []
    for f in os.listdir(OUT):
        if f.endswith(".json") and f != "SUMMARY.json":
            r = json.load(open(os.path.join(OUT, f)))
            if "final_us" in r:
                allres.append(r)
    wins = [r for r in allres if r["final_us"] > r["final_opp"]]
    losses = [r for r in allres if r["final_us"] < r["final_opp"]]
    ties = [r for r in allres if r["final_us"] == r["final_opp"]]
    print(f"\n=== SUMMARY: {len(allres)} games | {len(wins)} W | {len(losses)} L | {len(ties)} T", flush=True)
    print(f"win rate: {len(wins)/max(1,len(allres))*100:.1f}%", flush=True)
    if wins:
        print(f"avg win margin: {sum(r['final_us']-r['final_opp'] for r in wins)/len(wins):,.0f}", flush=True)
    if losses:
        print(f"avg loss margin: {sum(r['final_opp']-r['final_us'] for r in losses)/len(losses):,.0f}", flush=True)
    json.dump({"wins": len(wins), "losses": len(losses), "ties": len(ties),
               "results": allres},
              open(os.path.join(OUT, "SUMMARY.json"), "w"), indent=1)
    print("saved SUMMARY.json", flush=True)


if __name__ == "__main__":
    main()
