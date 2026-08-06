"""
evolution.py — single-episode evolution runner.

Run:
    python Scripts\\evolution.py 100
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AGENT_DIR = os.path.join(ROOT, "Agent")
DATA_DIR  = os.path.join(ROOT, "Data")
os.makedirs(DATA_DIR, exist_ok=True)
sys.path.insert(0, ROOT)
sys.path.insert(0, AGENT_DIR)

N = int(sys.argv[1]) if len(sys.argv) > 1 else 50


def main():
    from kaggle_environments import make
    print(f"Running {N} matches against 'starter' ...")
    wins = 0
    total_cash = 0
    best_cash = 0
    t0 = time.time()
    for i in range(1, N + 1):
        env = make("kagriculture", configuration={"episodeSteps": 720})
        env.run([os.path.join(AGENT_DIR, "main.py"), "starter"])
        p0 = env.state[0].reward if env.state[0].reward is not None else 0
        p1 = env.state[1].reward if env.state[1].reward is not None else 0
        total_cash += p0
        if p0 > p1:
            wins += 1
        if p0 > best_cash:
            best_cash = p0
        if i % 10 == 0:
            print(f"  match {i:3d}/{N}  winrate={wins/i*100:.0f}%  avg_cash=${total_cash/i:.0f}  best=${best_cash:.0f}")
    elapsed = time.time() - t0
    print(f"Done. {N} matches in {elapsed:.1f}s ({N/elapsed:.1f} matches/s)")
    print(f"Win rate: {wins/N*100:.1f}%")
    print(f"Average cash: ${total_cash/N:.0f}")
    print(f"Best cash: ${best_cash:.0f}")


if __name__ == "__main__":
    main()
