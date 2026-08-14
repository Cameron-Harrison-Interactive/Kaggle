#!/usr/bin/env python3
"""Replay analyzer for Kaggriculture.

Extracts per-player strategy stats from a replay JSON:
  - money curve by day
  - market orders by type/day (hires, buys, sells per product)
  - animals bought/placed/alive per day
  - crops planted/harvested/weeds per day
  - fertilizer produced/sold
  - final state summary
Usage: python3 scripts/analyze_replay.py data/replays/episode-XXX-replay.json [out.json]
"""
import json, sys, collections

def load_replay(path):
    with open(path) as f:
        return json.load(f)

def main(path, out=None):
    rp = load_replay(path)
    steps = rp["steps"]
    info = rp.get("info", {})
    cfg = rp.get("configuration", {})
    agents = info.get("TeamNames", info.get("agents", ["p0", "p1"]))

    stats = [{
        "name": agents[i] if i < len(agents) else f"p{i}",
        "money_by_day": {},
        "orders": collections.defaultdict(lambda: collections.Counter()),  # day -> Counter
        "sells_units": collections.Counter(),
        "buys_units": collections.Counter(),
        "hires_by_day": collections.Counter(),
        "animals_on_farm_by_day": {},
        "crops_on_farm_by_day": {},
        "weeds_by_day": {},
        "pastures_by_day": {},
        "quads_by_day": {},
        "fertilizer_sold": 0, "fertilizer_sold_by_day": collections.Counter(),
        "milk_sold": 0, "wool_sold": 0, "wheat_sold": 0, "wheat_bought": 0,
        "melon_sold": 0, "strawberry_sold": 0, "tomato_sold": 0, "egg_sold": 0,
        "plant_counts": collections.Counter(),
        "harvest_counts": collections.Counter(),
        "water_counts": collections.Counter(),
        "feed_counts": collections.Counter(),
        "care_counts": collections.Counter(),
        "collect_fert_counts": collections.Counter(),
        "dig_counts": collections.Counter(),
        "dead_animals": 0,
    } for i in range(2)]

    prev_animals = [0, 0]
    for step_i, step in enumerate(steps):
        day = step_i // 24
        for pi in (0, 1):
            st = stats[pi]
            obs = step[pi].get("observation", {}) or {}
            action = step[pi].get("action", {}) or {}
            farm = (obs.get("farms") or [None, None])[pi] if obs.get("farms") else None
            # money
            if farm:
                st["money_by_day"][day] = farm.get("money", 0)
                animals = crops = weeds = pastures = 0
                for row in farm.get("tiles", []):
                    for t in row:
                        if isinstance(t, dict):
                            k = t.get("kind")
                            if t.get("animal"): animals += 1
                            if k == "PLANT": crops += 1
                            elif k == "WEED": weeds += 1
                            elif k in ("COOP", "PASTURE"): pastures += 1
                st["animals_on_farm_by_day"][day] = animals
                st["crops_on_farm_by_day"][day] = crops
                st["weeds_by_day"][day] = weeds
                st["pastures_by_day"][day] = pastures
                st["quads_by_day"][day] = sorted(farm.get("unlocked_quadrants", []))
                if animals < prev_animals[pi] - 0 and day > 0:
                    pass
                prev_animals[pi] = animals
            # actions
            if isinstance(action, dict):
                market = action.get("market", []) or []
                for o in market:
                    if not o: continue
                    key = o[0]
                    st["orders"][day][key] += 1
                    if key == "SELL" and len(o) >= 3:
                        item, n = o[1], o[2]
                        st["sells_units"][item] += n
                        if item == "FERTILIZER":
                            st["fertilizer_sold"] += n
                            st["fertilizer_sold_by_day"][day] += n
                        elif item == "MILK": st["milk_sold"] += n
                        elif item == "WOOL": st["wool_sold"] += n
                        elif item == "WHEAT": st["wheat_sold"] += n
                        elif item == "MELON": st["melon_sold"] += n
                        elif item == "STRAWBERRY": st["strawberry_sold"] += n
                        elif item == "TOMATO": st["tomato_sold"] += n
                        elif item == "EGG": st["egg_sold"] += n
                    elif key == "BUY_PRODUCT" and len(o) >= 3 and o[1] == "WHEAT":
                        st["wheat_bought"] += o[2]
                    elif key == "BUY_SEED" and len(o) >= 3:
                        st["buys_units"]["SEED_" + o[1]] += o[2]
                    elif key == "BUY_ANIMAL" and len(o) >= 3:
                        st["buys_units"]["ANIMAL_" + o[1]] += o[2]
                    elif key == "HIRE":
                        st["hires_by_day"][day] += 1
                units = [("farmer", action.get("farmer"))] + [(f"hand{i}", a) for i, a in enumerate(action.get("hands", []) or [])]
                for uname, a in units:
                    if not a: continue
                    k = a[0]
                    if k == "PLANT": st["plant_counts"][day] += 1
                    elif k == "WATER": st["water_counts"][day] += 1
                    elif k == "HARVEST": st["harvest_counts"][day] += 1
                    elif k == "FEED": st["feed_counts"][day] += 1
                    elif k == "CARE": st["care_counts"][day] += 1
                    elif k == "COLLECT_FERTILIZER": st["collect_fert_counts"][day] += 1
                    elif k == "DIG": st["dig_counts"][day] += 1

    # final money
    final_rewards = [s.get("reward", 0) for s in steps[-1]]
    report = {"episode": path, "agents": agents, "rewards": final_rewards}
    outp = {}
    for pi, st in enumerate(stats):
        d = dict(st)
        for k in list(d.keys()):
            if isinstance(d[k], collections.Counter):
                d[k] = dict(sorted(d[k].items()))
        d["totals"] = {
            "sells": dict(sorted(st["sells_units"].items())),
            "buys": dict(sorted(st["buys_units"].items())),
            "hires_total": sum(st["hires_by_day"].values()),
            "fertilizer_sold": st["fertilizer_sold"],
        }
        d["money_start"] = st["money_by_day"].get(0)
        d["money_end"] = st["money_by_day"].get(max(st["money_by_day"].keys(), default=0))
        d["animals_end"] = st["animals_on_farm_by_day"].get(max(st["animals_on_farm_by_day"].keys(), default=0))
        d["crops_end"] = st["crops_on_farm_by_day"].get(max(st["crops_on_farm_by_day"].keys(), default=0))
        d["weeds_end"] = st["weeds_by_day"].get(max(st["weeds_by_day"].keys(), default=0))
        outp[st["name"]] = d
    report["players"] = outp
    text = json.dumps(report, indent=1, default=str)
    if out:
        with open(out, "w") as f:
            f.write(text)
        print(f"wrote {out}")
    # compact console summary
    print(f"\n=== {path} ===")
    print(f"rewards: {final_rewards}  agents: {agents}")
    for name, d in outp.items():
        print(f"\n-- {name}: end ${d['money_end']:.0f}, animals_end={d['animals_end']}, weeds_end={d['weeds_end']}, hires={d['totals']['hires_total']}")
        print("   sells:", d["totals"]["sells"])
        print("   buys :", d["totals"]["buys"])
        days = sorted(d["quads_by_day"].keys())
        for day in (0, 4, 6, 7, 10, 11, 15, 20, 29):
            if day in d["quads_by_day"]:
                print(f"   d{day:2d}: money=${d['money_by_day'].get(day,0):.0f} quads={d['quads_by_day'][day]} animals={d['animals_on_farm_by_day'].get(day)} crops={d['crops_on_farm_by_day'].get(day)} weeds={d['weeds_by_day'].get(day)}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
