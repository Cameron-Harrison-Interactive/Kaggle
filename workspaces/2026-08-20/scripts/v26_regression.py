#!/usr/bin/env python3
"""v26_regression.py — replay EVERY live episode of v24 against v25 (baseline)
and v26 (candidate), seat-correct, using the recorded opponent actions.

For each episode:
  1. download the replay (if not cached), extract the opponent's full
     720-step action sequence (offset-corrected), delete the 28MB replay;
  2. run our agent (v25 baseline + v26 candidate) in OUR live seat against
     the replay opponent in THEIR live seat;
  3. record rewards, escapes, and W/L for each candidate.

Output: data/regression_v26/results.json + a summary print.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, "/home/user/kaggriculture/agent")
from kaggle_environments import make

OUR_TEAM = "Harrison Interactive"
BASE = "/home/user/kaggriculture/data/regression_v26"
OPP_DIR = os.path.join(BASE, "opp_actions")
os.makedirs(OPP_DIR, exist_ok=True)

import importlib.util


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V25 = load_mod("/home/user/kaggriculture/agent/main_v25_wheat16.py", "v25mod")
V26 = load_mod("/home/user/kaggriculture/agent/main_v26_feedguard.py", "v26mod")


class ReplayOpp:
    def __init__(self, acts):
        self.acts = acts
        self.i = -1

    def __call__(self, obs, configuration=None):
        self.i += 1
        return self.acts[min(self.i, len(self.acts) - 1)]


def get_opp_actions(eid):
    """Extract the opponent's action sequence from a live replay file."""
    rp = f"/home/user/episode-{eid}-replay.json"
    if not os.path.exists(rp):
        subprocess.run(["kaggle", "competitions", "replay", eid,
                        "-p", "/home/user", "-q"], capture_output=True)
    try:
        r = json.load(open(rp))
    except Exception:
        return None
    os.remove(rp)
    steps = r["steps"]
    info = r.get("info") or {}
    teams = info.get("TeamNames") or ["?", "?"]
    our_seat = 0 if teams[0] == OUR_TEAM else 1
    opp_seat = 1 - our_seat
    seed = info.get("seed")
    acts = []
    for t in range(720):
        a = steps[min(t + 1, 719)][opp_seat].get("action") or {}
        acts.append({"farmer": a.get("farmer") or ["PASS"],
                     "hands": a.get("hands") or [],
                     "market": a.get("market") or []})
    path = os.path.join(OPP_DIR, f"{eid}.json")
    json.dump({"actions": acts, "our_seat": our_seat, "opp_seat": opp_seat,
               "seed": seed, "teams": teams, "opponent": teams[opp_seat]},
              open(path, "w"))
    return path


def count_escapes(out, seat):
    esc = 0
    prev = {}
    for st in out:
        farm = (st[seat].get("observation") or {}).get("farms") or [{}]
        tiles = (farm[0] if farm else {}).get("tiles") or []
        cur = {}
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                if isinstance(t, dict) and "animal" in t:
                    cur[(x, y)] = t["animal"]
        for pos in prev:
            if pos not in cur:
                esc += 1
        prev = cur
    return esc


def play(agent, opp_seat, our_seat, seed, opp):
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": int(seed)})
    agents = [None, None]
    agents[opp_seat] = ReplayOpp(opp)
    agents[our_seat] = agent
    out = env.run(agents)
    last = out[-1]
    return (last[opp_seat].get("reward"), last[our_seat].get("reward"),
            count_escapes(out, our_seat))


def main():
    ids = [l.strip() for l in open("/home/user/episodes_v24.txt") if l.strip()]
    results = []
    done = set()
    if os.path.exists(os.path.join(BASE, "results.json")):
        done = {r["episode"] for r in
                json.load(open(os.path.join(BASE, "results.json")))}
    todo = [i for i in ids if i not in done]
    print(f"{len(ids)} episodes, {len(done)} cached, {len(todo)} to run",
          flush=True)
    for k, eid in enumerate(todo):
        path = os.path.join(OPP_DIR, f"{eid}.json")
        if not os.path.exists(path):
            path = get_opp_actions(eid)
        if not path:
            print(f"  {eid}: no actions, skip", flush=True)
            continue
        d = json.load(open(path))
        opp, our_seat, opp_seat = d["actions"], d["our_seat"], d["opp_seat"]
        seed = d["seed"]
        try:
            o25, u25, e25 = play(V25.agent, opp_seat, our_seat, seed, opp)
            o26, u26, e26 = play(V26.agent, opp_seat, our_seat, seed, opp)
        except Exception as ex:
            print(f"  {eid}: run error {ex}", flush=True)
            continue
        live_us = None
        # live result from the earlier sweep summaries
        summ = f"/home/user/kaggriculture/data/live_v24/{eid}.json"
        if os.path.exists(summ):
            s = json.load(open(summ))
            live_us = s.get("final_us")
            live_opp = s.get("final_opp")
        res = {"episode": eid, "opponent": d["opponent"], "seed": seed,
               "our_seat": our_seat,
               "v25": [o25, u25, e25], "v26": [o26, u26, e26],
               "live": [live_opp, live_us] if live_us is not None else None}
        results.append(res)
        flip = ("WIN->WIN" if u25 > o25 and u26 > o26 else
                "LOSS->WIN" if u25 <= o25 and u26 > o26 else
                "WIN->LOSS" if u25 > o25 and u26 <= o26 else
                "LOSS->LOSS" if u25 <= o25 and u26 <= o26 else "?")
        d26 = (u26 - o26) - (u25 - o25)
        print(f"  {eid}: {flip:10s} d26={d26:+8,.0f} "
              f"(v25 {u25:,.0f} vs {o25:,.0f} | v26 {u26:,.0f} vs {o26:,.0f}) "
              f"esc25={e25} esc26={e26}", flush=True)
    # merge with cached
    cached = []
    if os.path.exists(os.path.join(BASE, "results.json")):
        cached = [r for r in json.load(open(os.path.join(BASE, "results.json")))
                  if r["episode"] not in {r2["episode"] for r2 in results}]
    allres = cached + results
    json.dump(allres, open(os.path.join(BASE, "results.json"), "w"), indent=1)

    wins25 = sum(1 for r in allres if r["v25"][1] > r["v25"][0])
    wins26 = sum(1 for r in allres if r["v26"][1] > r["v26"][0])
    flips = sum(1 for r in allres
                if (r["v25"][1] > r["v25"][0]) != (r["v26"][1] > r["v26"][0]))
    dsum = sum((r["v26"][1] - r["v26"][0]) - (r["v25"][1] - r["v25"][0])
               for r in allres)
    print(f"\n=== REGRESSION SUITE: {len(allres)} episodes ===", flush=True)
    print(f"v25 baseline wins: {wins25}/{len(allres)}", flush=True)
    print(f"v26 candidate wins: {wins26}/{len(allres)}", flush=True)
    print(f"outcome flips: {flips} | total margin delta (v26-v25): {dsum:+,.0f}",
          flush=True)


if __name__ == "__main__":
    main()
