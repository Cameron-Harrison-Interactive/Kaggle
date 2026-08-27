"""Harvest real ladder episode replays -> compact opponent profiles.

Downloads each episode replay (~30MB), extracts opponent behavior, deletes replay.
Output: analysis/episode_profiles.jsonl (one compact profile per episode).
"""
import json
import os
import subprocess
import sys
import time

OUR_NAME = "Harrison Interactive"
SUBMISSIONS = [55730825, 55716221, 55748620, 55754663, 55730353]
OUT = os.path.join(os.path.dirname(__file__), "..", "analysis", "episode_profiles.jsonl")
TMP = "/tmp/replays/harvest.json"


def list_episode_ids():
    env = dict(os.environ)
    ids = {}
    for sub in SUBMISSIONS:
        out = subprocess.run(
            ["kaggle", "competitions", "episodes", str(sub)],
            capture_output=True, text=True, env=env, timeout=120,
        ).stdout
        for line in out.splitlines():
            parts = line.split()
            if parts and parts[0].isdigit() and any("COMPLETED" in x for x in parts):
                ids.setdefault(int(parts[0]), sub)
    return ids


def money_curve(obs_steps, idx):
    """Our stored per-step reward is final; recompute from observations."""
    return obs_steps


def extract(d, episode_id, submission_id):
    info = d.get("info", {})
    names = info.get("TeamNames") or info.get("Agents") and [a.get("Name") for a in info["Agents"]]
    if not names or len(names) != 2:
        return None
    steps = d["steps"]
    n = len(steps)
    if OUR_NAME not in names:
        return {"episode_id": episode_id, "submission_id": submission_id,
                "names": names, "error": "our name absent"}
    me = names.index(OUR_NAME)
    opp = 1 - me
    opp_name = names[opp]

    # per-step data for opponent
    sells = []          # (day, hour, item, qty_submitted)
    buys = []           # (day, hour, kind, item, qty)
    hires = []          # (day, hour)
    money = []          # opp money per step
    inv_delta_items = []  # not needed; inventory attribution via orders
    quad_unlocks = []   # (day, n_quads)
    hand_counts = []    # hands count per step (sampled)
    final_tiles = None
    last_day_seen = 0

    for si in range(n):
        st = steps[si][opp]
        obs = st.get("observation") or {}
        day, hour = obs.get("day", -1), obs.get("hour", -1)
        farms = obs.get("farms") or []
        if len(farms) > opp:
            f = farms[opp]
            money.append(f.get("money", 0))
            uq = len(f.get("unlocked_quadrants", []))
            if not quad_unlocks or quad_unlocks[-1][1] != uq:
                quad_unlocks.append((day, uq))
            hand_counts.append((day, len(f.get("hands", []))))
            last_day_seen = day
            if si == n - 1:
                final_tiles = f.get("tiles")
        act = st.get("action") or {}
        mk = act.get("market") or []
        for o in mk:
            # order formats: [op, item, qty] or [op, item] or nested
            if not isinstance(o, (list, tuple)) or len(o) < 2:
                continue
            op, item = o[0], o[1]
            qty = o[2] if len(o) > 2 and isinstance(o[2], int) else 1
            if op == "SELL":
                sells.append((day, hour, item, qty))
            elif op == "BUY_ANIMAL":
                buys.append((day, hour, "ANIMAL", item, qty))
            elif op == "BUY_SEED":
                buys.append((day, hour, "SEED", item, qty))
            elif op == "BUY_PRODUCT":
                buys.append((day, hour, "PRODUCT", item, qty))
            elif op == "BUY_LAND":
                buys.append((day, hour, "LAND", item, qty))
        if act.get("hire") or (isinstance(act.get("farmer"), list) and act["farmer"] and act["farmer"][0] == "HIRE"):
            hires.append((day, hour))
        # HIRE also possible via market? engine: HIRE is atomic order
        for o in mk:
            if isinstance(o, (list, tuple)) and o and o[0] == "HIRE":
                hires.append((day, hour))

    # money-jump sell events (ground truth): money[i] - money[i-1] > 0 at step i
    jumps = []
    for i in range(1, len(money)):
        dm = money[i] - money[i - 1]
        if dm > 50:  # threshold: revenue inflow
            day = steps[i][opp].get("observation", {}).get("day", -1)
            hour = steps[i][opp].get("observation", {}).get("hour", -1)
            jumps.append((day, hour, round(dm, 1)))

    # aggregate sell-hour histogram weighted by submitted qty
    hist = {}
    for day, hour, item, qty in sells:
        hist.setdefault(hour, 0)
        hist[hour] += qty
    item_totals = {}
    for day, hour, item, qty in sells:
        item_totals[item] = item_totals.get(item, 0) + qty

    animal_buys = {}
    for day, hour, kind, item, qty in buys:
        if kind == "ANIMAL":
            animal_buys[item] = animal_buys.get(item, 0) + qty

    # herd census from final tiles
    herd = {}
    crops = {}
    buildings = {"PASTURE": 0, "COOP": 0}
    if final_tiles:
        for row in final_tiles:
            for t in row:
                if isinstance(t, dict):
                    if t.get("animal"):
                        herd[t["animal"]] = herd.get(t["animal"], 0) + 1
                    if t.get("crop"):
                        crops[t["crop"]] = crops.get(t["crop"], 0) + 1
                    if t.get("kind") in buildings:
                        buildings[t["kind"]] += 1

    # money checkpoints
    def money_at_day(day_q):
        for i in range(len(money) - 1, -1, -1):
            if steps[i][opp].get("observation", {}).get("day", 99) <= day_q:
                return round(money[i], 0)
        return None

    rewards = d.get("rewards") or [None, None]
    return {
        "episode_id": episode_id,
        "submission_id": submission_id,
        "opp_name": opp_name,
        "seed": info.get("seed"),
        "me_final": rewards[me],
        "opp_final": rewards[opp],
        "win": (rewards[me] or 0) > (rewards[opp] or 0),
        "sell_hour_hist_qty": hist,
        "sell_item_totals": item_totals,
        "sell_events_n": len(sells),
        "money_jumps": jumps[-400:],
        "n_money_jumps": len(jumps),
        "animal_buys": animal_buys,
        "hires_n": len(hires),
        "first_hire_day": hires[0][0] if hires else None,
        "last_day": last_day_seen,
        "quad_unlocks": quad_unlocks,
        "max_hands": max((h for _, h in hand_counts), default=0),
        "final_herd": herd,
        "final_crops": crops,
        "buildings": buildings,
        "money_d1": money_at_day(1), "money_d5": money_at_day(5),
        "money_d10": money_at_day(10), "money_d20": money_at_day(20),
    }


def main():
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            try:
                done.add(json.loads(line)["episode_id"])
            except Exception:
                pass
    eps = list_episode_ids()
    todo = {e: s for e, s in eps.items() if e not in done}
    print(f"total episodes {len(eps)}, already done {len(done)}, todo {len(todo)}", flush=True)
    env = dict(os.environ)
    ok = fail = 0
    with open(OUT, "a") as fout:
        for i, (eid, sub) in enumerate(sorted(todo.items())):
            try:
                if os.path.exists(TMP):
                    os.remove(TMP)
                r = subprocess.run(
                    ["kaggle", "competitions", "replay", str(eid), "-p", "/tmp/replays"],
                    capture_output=True, text=True, env=env, timeout=90,
                )
                path = f"/tmp/replays/episode-{eid}-replay.json"
                if not os.path.exists(path):
                    raise RuntimeError(f"download failed: {r.stderr[-100:]}")
                d = json.load(open(path))
                os.remove(path)
                prof = extract(d, eid, sub)
                if prof:
                    fout.write(json.dumps(prof) + "\n")
                    fout.flush()
                    ok += 1
                else:
                    fail += 1
            except Exception as e:
                fail += 1
                print(f"  ep {eid} FAIL: {e}", flush=True)
            if (i + 1) % 25 == 0:
                print(f"  progress {i+1}/{len(todo)} ok={ok} fail={fail}", flush=True)
    print(f"DONE ok={ok} fail={fail}", flush=True)


if __name__ == "__main__":
    main()
