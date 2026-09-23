#!/usr/bin/env python3
"""
census.py - per-day episode census for Kaggressure builds.

Answers "what is the bot actually doing, day by day":
  * when each crop first goes in the ground + standing tiles per day
  * sell tape: units + price per good per day (submitted orders ~ executed)
  * money ramp, herd size, crew size, quads owned
  * price curves for STRB / MELON / key animal goods

Usage (from workspace root):
    python war/census.py                          # live20 vs passbot, 42,101,202
    python war/census.py --bot live20 --seeds 42,101,202
    python war/census.py --bot war/astra_live20.py --seeds 42
    python war/census.py --bot live20 --opponent tetsu --seeds 42
    python war/census.py --list
"""
import argparse
import contextlib
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import BOTS, resolve, ensure_env, env_name  # noqa: E402

CROPS = ("WHEAT", "CARROT", "MELON", "STRAWBERRY", "TOMATO")
GOODS = ("WHEAT", "CARROT", "MELON", "STRAWBERRY", "EGG", "MILK", "WOOL", "FERTILIZER")
ECON_LOG = "/tmp/astra_econ19.txt"


def run_one(path_a, path_b, seed):
    """Run one episode; return (per-day dict, rewards, order tape)."""
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])
    rewards = [float(env.state[0].reward), float(env.state[1].reward)]

    days = {}
    tape = []          # (day, hour, item, qty, price)
    first_plant = {}   # crop -> day
    for step in env.steps:
        s0 = step[0] or {}
        obs = s0.get("observation") or {}
        if "farms" not in obs:
            continue
        day = int(obs.get("day", 0))
        hour = int(obs.get("hour", 0))
        farm = obs["farms"][0]
        px = (obs.get("market", {}) or {}).get("prices", {}) or {}
        inv = (obs.get("market", {}) or {}).get("inventory", {}) or {}

        standing = {c: 0 for c in CROPS}
        herd = 0
        for row in farm.get("tiles", []):
            for t in row:
                if not isinstance(t, dict):
                    continue
                if t.get("kind") == "PLANT":
                    standing[t["crop"]] = standing.get(t["crop"], 0) + 1
                elif t.get("kind") in ("COOP", "PASTURE") and t.get("animal"):
                    herd += 1
        for c in CROPS:
            if standing.get(c) and c not in first_plant:
                first_plant[c] = day

        d = days.setdefault(day, {
            "cash": 0.0, "quads": 1, "crew": 1, "herd": 0,
            "standing": {c: 0 for c in CROPS},
            "px": {}, "inv": {}, "sells": {},
        })
        d["cash"] = float(farm.get("money", 0))
        d["quads"] = len(farm.get("unlocked_quadrants", ["NW"]))
        d["crew"] = 1 + len(farm.get("hands") or [])
        d["herd"] = herd
        d["standing"] = standing
        d["px"] = dict(px)
        d["inv"] = dict(inv)

        act = s0.get("action") or {}
        for o in act.get("market", []) or []:
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] in GOODS:
                qty = int(o[2]) if str(o[2]).isdigit() else 0
                if qty > 0:
                    tape.append((day, hour, o[1], min(qty, 900000), px.get(o[1], 0)))
    return days, rewards, tape, first_plant


def tape_stats(tape):
    """units + approx revenue per good; per-day sells for STRB/MELON."""
    per_good = {}
    for day, hour, item, qty, price in tape:
        g = per_good.setdefault(item, {"units": 0, "rev": 0.0, "px_first": None,
                                       "px_last": None, "by_day": {}})
        g["units"] += qty
        g["rev"] += qty * price
        g["px_first"] = g["px_first"] or price
        g["px_last"] = price
        g["by_day"][day] = g["by_day"].get(day, 0) + qty
    return per_good


def report(seed, days, rewards, first_plant, bot_name, opp_name, per_good):
    lines = []
    w = lines.append
    w("=" * 110)
    w("SEED %s  %s vs %s   FINAL: A $%.0f   B $%.0f" % (
        seed, bot_name, opp_name, rewards[0], rewards[1]))
    fp = "  ".join("%s d%s" % (c.lower(), first_plant.get(c, "-"))
                   for c in ("WHEAT", "CARROT", "MELON", "STRAWBERRY"))
    w("first plant: " + fp)
    w("day  cash    qud crw herd |  standing WHE CAR MEL STR | sold that day  WHE CAR MEL STR EGG MIL WOOL FER | px: STR MEL")
    for day in sorted(days):
        d = days[day]
        st = d["standing"]
        sd = {g: per_good.get(g, {}).get("by_day", {}).get(day, 0)
              for g in ("WHEAT", "CARROT", "MELON", "STRAWBERRY",
                        "EGG", "MILK", "WOOL", "FERTILIZER")}
        w("d%-3d %7.0f  %d   %2d  %3d  |          %3d %3d %3d %3d |               %3d %3d %3d %3d %3d %3d %3d %3d | %3d %3d" % (
              day, d["cash"], d["quads"], d["crew"], d["herd"],
              st.get("WHEAT", 0), st.get("CARROT", 0), st.get("MELON", 0),
              st.get("STRAWBERRY", 0),
              sd["WHEAT"], sd["CARROT"], sd["MELON"], sd["STRAWBERRY"],
              sd["EGG"], sd["MILK"], sd["WOOL"], sd["FERTILIZER"],
              d["px"].get("STRAWBERRY", 0), d["px"].get("MELON", 0)))
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", default="live20")
    ap.add_argument("--opponent", default="pass")
    ap.add_argument("--seeds", default="42,101,202")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="summary only, no day table")
    args = ap.parse_args()
    if args.list:
        for k, v in sorted(BOTS.items()):
            print("%-8s %s" % (k, v))
        return
    path_a, path_b = resolve(args.bot), resolve(args.opponent)
    ensure_env()
    bot_name = os.path.splitext(os.path.basename(path_a))[0]
    opp_name = os.path.splitext(os.path.basename(path_b))[0]
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]

    finals = []
    for seed in seeds:
        if os.path.exists(ECON_LOG):
            os.remove(ECON_LOG)
        import time
        t0 = time.time()
        days, rewards, tape, first_plant = run_one(path_a, path_b, seed)
        dt = time.time() - t0
        finals.append(rewards[0])
        g = tape_stats(tape)

        if not args.quiet:
            for ln in report(seed, days, rewards, first_plant, bot_name, opp_name, g):
                print(ln)
        # ---- summary ----
        print("---- seed %s summary (%.0fs) ----" % (seed, dt))
        print("final A $%.0f  (B $%.0f)" % (rewards[0], rewards[1]))
        fp = ", ".join("%s:%s" % (c.lower(), first_plant.get(c, "-"))
                       for c in ("WHEAT", "CARROT", "MELON", "STRAWBERRY"))
        print("first plants: %s" % fp)
        for item in ("WHEAT", "CARROT", "MELON", "STRAWBERRY", "EGG", "MILK", "WOOL", "FERTILIZER"):
            if item in g:
                gg = g[item]
                avg = gg["rev"] / gg["units"] if gg["units"] else 0
                print("  %-10s units %5d  approx rev $%8.0f  avg $%6.0f  px %s->%s" % (
                    item, gg["units"], gg["rev"], avg, gg["px_first"], gg["px_last"]))
        # money ramp + strb/melon price curve
        marks = [5, 10, 12, 15, 20, 25, 29]
        ramp = "  ".join("d%d $%.0f" % (m, days[m]["cash"]) if m in days else "d%d -" % m
                         for m in marks)
        print("cash ramp: %s" % ramp)
        for item in ("STRAWBERRY", "MELON"):
            curve = " ".join("%d:%s" % (m, days[m]["px"].get(item, "-")) for m in marks if m in days)
            invs = " ".join("%d:%s" % (m, days[m]["inv"].get(item, "-")) for m in marks if m in days)
            print("%s px: %s   (net inv vs 10000 anchor: %s)" % (item, curve, invs))
        herd_max = max(d["herd"] for d in days.values())
        crew_max = max(d["crew"] for d in days.values())
        strb_max = max(d["standing"].get("STRAWBERRY", 0) for d in days.values())
        melon_max = max(d["standing"].get("MELON", 0) for d in days.values())
        print("max: herd %d  crew %d  strb standing %d  melon standing %d" % (
            herd_max, crew_max, strb_max, melon_max))
        if os.path.exists(ECON_LOG):
            keep = "/tmp/census_econ_s%d.txt" % seed
            os.replace(ECON_LOG, keep)
            print("econ log kept: %s" % keep)
        print()
    print("=" * 60)
    print("GATE  %s  seeds %s: %s  avg %.1f" % (
        bot_name, seeds, " / ".join("%.1f" % f for f in finals),
        sum(finals) / max(1, len(finals))))


if __name__ == "__main__":
    main()
