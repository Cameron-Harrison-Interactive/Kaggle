"""Definitive isolated bench: v11.9 vs v11.10, one subprocess per game."""
import json, subprocess, sys, time, os

PY = sys.executable
RUN = "/home/user/_ref/run_isolated.py"
SEEDS = [1, 3, 5, 7, 9, 11, 13, 19]
OPPS = ["bt", "v46", "k2900", "moon", "soil"]
GHOST = "ghost:101033101:1"  # Shinichiro Yoshida (lost ep), opp was seat 1

def game(version, opponent, seed, seat):
    r = subprocess.run([PY, RUN, version, opponent, str(seed), str(seat)],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        return {"err": r.stderr[-300:]}
    return json.loads(r.stdout.strip().splitlines()[-1])

results = {}
t0 = time.time()

print("=== ghost: Shinichiro episode (live v11.9: $77,372, 3 escapes) ===")
for v in ("v119", "v1110"):
    g = game(v, GHOST, 45626426, 0)
    results[(v, "ghost")] = g
    print(f"  {v}: ${g.get('cash',0):,.0f}  herd={g.get('herd')} shed={g.get('shed')} escapes={g.get('escapes')}")

print("\n=== field: per-game (v1110 margin) - (v119 margin) ===")
tot = 0; n = 0; nonzero = 0
for opp in OPPS:
    row = []
    for s in SEEDS:
        for seat in (0, 1):
            a = game("v1110", opp, s, seat)
            b = game("v119", opp, s, seat)
            if "err" in a or "err" in b:
                row.append(None); continue
            dd = (a["cash"] - a["opp_cash"]) - (b["cash"] - b["opp_cash"])
            tot += dd; n += 1
            if dd != 0: nonzero += 1
            row.append(dd)
    vals = [x for x in row if x is not None]
    print(f"  {opp:6}: avg {sum(vals)/len(vals):+9,.0f}  [" +
          ' '.join(' err ' if x is None else f'{x/1000:+.1f}' for x in row) + "]")

print("\n=== solo vs pass ===")
row = []
for s in SEEDS:
    a = game("v1110", "pass", s, 0)
    b = game("v119", "pass", s, 0)
    row.append(a["cash"] - b["cash"])
print("  " + ' '.join(f'{x/1000:+.1f}' for x in row), f"  avg {sum(row)/len(row):+,.0f}")

print(f"\nH2H total: {tot/n:+,.0f}/game over {n} games, nonzero: {nonzero}  ({time.time()-t0:.0f}s)")
json.dump(results, open("/home/user/_ref/ghost_results.json", "w"), indent=1, default=str)
