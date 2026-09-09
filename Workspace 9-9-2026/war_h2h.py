#!/usr/bin/env python3
"""H2H bench: python3 h2h.py A.py B.py seed1,seed2,... [swap]
Prints per-game golds + W/L + median diff oriented A-minus-B."""
import sys, time, io, contextlib
import kaggle_environments as ke

def play(a, b, seed):
    env = ke.make("kaggriculture", configuration={"seed": seed}, debug=False)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        env.run([a, b])
    s0, s1 = env.state[0], env.state[1]
    return (s0.reward, s1.reward, s0.status, s1.status)

def main():
    A, B = sys.argv[1], sys.argv[2]
    seeds = [int(x) for x in sys.argv[3].split(",")]
    swap = len(sys.argv) > 4 and sys.argv[4] == "swap"
    games = [(A, B, 1)] + ([(B, A, -1)] if swap else [])
    wins = [0, 0]  # A wins, B wins
    diffs = []
    for seed in seeds:
        for x, y, sign in games:
            t0 = time.time()
            rx, ry, sx, sy = play(x, y, seed)
            nx, ny = x.split("/")[-1], y.split("/")[-1]
            d = sign * ((rx or 0) - (ry or 0))
            if sx != "DONE" or sy != "DONE":
                print(f"seed {seed} {nx} vs {ny}: STATUS {sx}/{sy} r={rx}/{ry}")
                print(buf.getvalue()[-500:])
            if d > 0: wins[0] += 1
            elif d < 0: wins[1] += 1
            diffs.append(d)
            print(f"seed {seed} {nx:16s} vs {ny:16s} {rx:>8.0f} - {ry:>8.0f}  diff {d:+7.0f}  ({time.time()-t0:.0f}s)")
    na, nb = A.split("/")[-1], B.split("/")[-1]
    med = sorted(diffs)[len(diffs)//2]
    print(f"\n=== {na} vs {nb}: {wins[0]}-{wins[1]} (of {len(diffs)}) median diff {med:+.0f} mean {sum(diffs)/len(diffs):+.0f} ===")

main()
