"""Harvest elite episodes from Kaggle's daily top-episodes dataset.

Downloads top-rated episode replays one at a time (32MB each), extracts:
  - per-agent action tapes (720 steps) -> /tmp/elite_tapes/{team}_{eid}.json
  - build census (herd, crops, sells, money curve) -> appended to census.json
then deletes the raw replay to stay under the /tmp cap.

Usage: python3 harvest_elite.py DAY_SLUG N_EPISODES [start_offset]
"""
import csv
import json
import os
import subprocess
import sys
from collections import defaultdict

DAY = sys.argv[1] if len(sys.argv) > 1 else "kaggriculture-episodes-2026-09-04"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 8
OFFSET = int(sys.argv[3]) if len(sys.argv) > 3 else 0
BASE = f"https://www.kaggle.com/api/v1/datasets/download/kaggle/{DAY}"
OUT = "/tmp/elite_tapes"
os.makedirs(OUT, exist_ok=True)

rows = []
with open("/tmp/daymanifest.csv") as f:
    for r in csv.DictReader(f):
        rows.append(r)
rows.sort(key=lambda r: -float(r["avg_score"]))
rows = rows[OFFSET:OFFSET + N]
print(f"harvesting {len(rows)} episodes from {DAY} (offset {OFFSET})", flush=True)

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
for i, r in enumerate(rows):
    eid = r["episode_id"]
    raw = f"/tmp/ep_{eid}.json"
    url = f"{BASE}/{eid}.json"
    subprocess.run(["curl", "-sL", "-o", raw, url], check=True, timeout=240)
    try:
        d = json.load(open(raw))
    except Exception as e:
        print(f"  {eid}: BAD DOWNLOAD ({e})", flush=True)
        os.path.exists(raw) and os.remove(raw)
        continue
    info = d.get("info") or {}
    teams = info.get("TeamNames") or ["A", "B"]
    seed = (info.get("seed") or 0)
    rewards = d.get("rewards") or [0, 0]
    steps = d.get("steps") or []
    print(f"  {eid}: {teams[0]} ${rewards[0]:,.0f} vs {teams[1]} ${rewards[1]:,.0f}  seed={seed} avg={r['avg_score']}", flush=True)
    for seat in (0, 1):
        team = str(teams[seat]).replace(" ", "_").replace("/", "_")
        tape = []
        sells = defaultdict(int)
        money = {}
        herd = defaultdict(int)
        crops = defaultdict(int)
        for st in steps:
            if seat < len(st):
                a = (st[seat].get("action") or {})
                tape.append({
                    "farmer": list(a.get("farmer") or ["PASS"]),
                    "hands": [list(h) for h in (a.get("hands") or [])],
                    "market": [list(m) for m in (a.get("market") or [])],
                })
                for o in (a.get("market") or []):
                    if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                        sells[o[1]] += o[2] if isinstance(o[2], (int, float)) else 0
                obs = st[seat].get("observation") or {}
                f = (obs.get("farms") or [None, None])
                f = f[seat] if seat < len(f) else None
                if f:
                    if obs.get("hour") == 23:
                        money[obs.get("day", 0)] = f.get("money", 0)
                    if obs.get("hour") == 12:
                        for row in (f.get("tiles") or []):
                            for t in row:
                                if isinstance(t, dict) and t.get("animal"):
                                    herd[t["animal"]] += 1
                                elif isinstance(t, dict) and t.get("kind") == "PLANT":
                                    crops[t.get("crop")] += 1
        rec = {
            "eid": eid, "team": teams[seat], "seat": seat, "seed": seed,
            "reward": rewards[seat], "avg_score": r["avg_score"],
            "sells": dict(sells),
            "money_d": {str(k): v for k, v in sorted(money.items()) if k % 4 == 0},
            "herd_d20": dict(herd), "crops_d20": dict(crops),
        }
        with open(f"{OUT}/{team}_{eid}.json", "w") as f:
            json.dump({"eid": eid, "opp": teams[1 - seat], "seat": seat,
                       "seed": seed, "me": rewards[seat],
                       "opp_m": rewards[1 - seat], "len": len(tape),
                       "tape": tape}, f)
        with open(f"{OUT}/census.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
    os.remove(raw)
    print(f"    tapes saved ({len(tape)} steps); raw deleted", flush=True)
print("done ->", OUT, flush=True)
