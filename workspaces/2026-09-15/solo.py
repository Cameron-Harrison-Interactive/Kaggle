#!/usr/bin/env python3
"""solo.py - quick solo-gate runner: finals per seed for a bot vs passbot.

Usage: python3 solo.py [bot_path] [seed ...]   (default: live20, 42 202 303)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from watch import run_match

bot = sys.argv[1] if len(sys.argv) > 1 else "war/astra_live20.py"
seeds = [int(s) for s in sys.argv[2:]] or [42, 202, 303]
tot = 0
for s in seeds:
    _, r = run_match(bot, "war/passbot.py", s)
    tot += r[0]
    print(f"seed {s}: ${r[0]:,.0f}")
print(f"avg {len(seeds)} seeds: ${tot / len(seeds):,.0f}")
