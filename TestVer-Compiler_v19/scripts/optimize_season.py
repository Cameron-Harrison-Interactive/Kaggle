#!/usr/bin/env python3
"""Offline season optimizer for HI_AgriBot.

Searches over strategic parameters (hire curve, animal targets, land timing,
strawberry waves, planting throttle) by patching the planner template,
simulating 3 seeds against the starter, and scoring mean income.
The adaptive runtime stays — we optimize the STRATEGY it runs.

Usage:  python scripts/optimize_season.py [--rounds N]
"""
import os, re, sys, shutil, statistics, itertools, random, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "agent", "main.py")
WORK = "/tmp/opt_candidate.py"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from kaggle_environments import make
from run_local import audit

SEEDS = (1, 2, 3)

HIRE_TMPL = '''    if not final_day:
        if day <= 2:
            want = {h0}
        elif day <= 6:
            want = {h1}
        elif day <= 11:
            want = {h2}
        elif day <= 20:
            want = {h3}
        elif day <= 26:
            want = {h4}
        else:
            want = {h5}'''


def build_candidate(p):
    s = open(TEMPLATE).read()
    # hire curve
    new_hire = HIRE_TMPL.format(**p)
    pat = re.compile(r"    if not final_day:\n        if day <= 2:.*?want = \d+\n(?=        if proj)", re.S)
    assert pat.search(s), "hire block not found"
    s = pat.sub(new_hire + "\n", s)
    # animal targets
    s = re.sub(r'"target_cows": \d+,', f'"target_cows": {p["cows"]},', s)
    s = re.sub(r'"target_sheep": \d+,', f'"target_sheep": {p["sheep"]},', s)
    # land timing
    s = re.sub(r'"buy_ne_day": \d+,', f'"buy_ne_day": {p["ne"]},', s)
    s = re.sub(r'"buy_sw_day": \d+,', f'"buy_sw_day": {p["sw"]},', s)
    # strawberry wave-2 cap (sb < N)
    s = re.sub(r"11 <= day <= 16 and sb < \d+", f"11 <= day <= 16 and sb < {p['sb_cap']}", s)
    # planting throttle: _plant_bump values
    s = re.sub(r"_plant_bump = 3\n", f"_plant_bump = {p['pb_low']}\n", s)
    s = re.sub(r"_plant_bump = 2 if fill_boost else 0",
               f"_plant_bump = {p['pb_high']} if fill_boost else 0", s)
    open(WORK, "w").write(s)


def score(p, seeds=SEEDS):
    build_candidate(p)
    ms, esc, peaks = [], 0, []
    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([WORK, "starter"])
        r = audit(env)
        ms.append(env.steps[-1][0].reward or 0)
        esc += r["animal_escapes"]
        peaks.append(r["peak_crops"])
    income = statistics.mean(ms)
    penalty = esc * 5000  # escapes are unacceptable
    return income - penalty, dict(income=income, esc=esc,
                                  peak=statistics.mean(peaks), min=min(ms))


BASELINE = dict(h0=6, h1=8, h2=12, h3=12, h4=11, h5=8,
                cows=8, sheep=6, ne=7, sw=11, sb_cap=44, pb_low=3, pb_high=2)


def neighbors(p):
    out = []
    moves = {
        "h0": (4, 5, 6, 7, 8), "h1": (6, 8, 9, 10), "h2": (10, 12, 13, 14),
        "h3": (11, 12, 13, 14, 15), "h4": (10, 11, 12), "h5": (6, 8, 10),
        "cows": (6, 8, 10, 12), "sheep": (4, 6, 8),
        "ne": (6, 7, 8), "sw": (10, 11, 12), "sb_cap": (32, 44, 50),
        "pb_low": (2, 3, 4), "pb_high": (1, 2, 3),
    }
    for k, vals in moves.items():
        for v in vals:
            if v != p[k]:
                q = dict(p); q[k] = v
                out.append(q)
    return out


def main():
    rounds = 8
    if "--rounds" in sys.argv:
        rounds = int(sys.argv[sys.argv.index("--rounds") + 1])
    log = os.path.join(ROOT, "data", "opt_log.jsonl")
    best_p, best_s = dict(BASELINE), None
    t0_score, info = score(best_p)
    best_s = t0_score
    print(f"baseline: {info} score={t0_score:,.0f}", flush=True)
    with open(log, "a") as f:
        f.write(json.dumps({"params": best_p, **info, "score": t0_score}) + "\n")
    for rnd in range(rounds):
        cands = neighbors(best_p)
        random.shuffle(cands)
        improved = False
        for c in cands[:6]:  # sample 6 neighbors per round
            sc, info = score(c)
            with open(log, "a") as f:
                f.write(json.dumps({"round": rnd, "params": c, **info, "score": sc}) + "\n")
            tag = "+" if sc > best_s else "-"
            print(f"r{rnd} [{tag}] {sc:,.0f} (inc {info['income']:,.0f}, esc {info['esc']}, "
                  f"pk {info['peak']:.0f}) delta={ {k: v for k, v in c.items() if v != BASELINE.get(k)} }",
                  flush=True)
            if sc > best_s + 300:
                best_p, best_s = c, sc
                improved = True
                break
        if not improved:
            print(f"r{rnd}: no improvement, random restart nudge")
            q = dict(best_p)
            k = random.choice(list(q))
            q[k] = random.choice(neighbors(q)[0].values()) if False else q[k]
    print(f"\nBEST: score={best_s:,.0f}\nparams={best_p}")
    with open(log, "a") as f:
        f.write(json.dumps({"BEST": best_p, "score": best_s}) + "\n")


if __name__ == "__main__":
    main()
