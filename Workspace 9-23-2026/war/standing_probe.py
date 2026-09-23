#!/usr/bin/env python3
"""standing_probe.py - per-day standing / crew / cash curve for a bot.

Usage: python3 war/standing_probe.py [bot] [seed]
"""
import io
import contextlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env  # noqa: E402


def main():
    ensure_env()
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_10"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([resolve(bot), resolve("pass")])

    print("  day crew plants animals weeds dirt  cash   standing/crew")
    rows = []
    for st in env.steps:
        obs = (st[0] or {}).get("observation") or {}
        if "farms" not in obs:
            continue
        if obs.get("hour") != 12:
            continue
        day = int(obs.get("day", 0))
        f = obs["farms"][0]
        grid = {}
        for y, row in enumerate(f.get("tiles", [])):
            for x, t in enumerate(row):
                grid[(x, y)] = t
        plants = sum(1 for t in grid.values()
                     if isinstance(t, dict) and t.get("kind") == "PLANT")
        animals = sum(1 for t in grid.values()
                      if isinstance(t, dict) and t.get("animal"))
        weeds = sum(1 for t in grid.values()
                    if isinstance(t, dict) and t.get("kind") == "WEED")
        quads = len(f.get("unlocked_quadrants", []))
        own = quads * 25
        dirt = own - plants - animals - weeds - 4
        crew = 1 + len(f.get("hands") or [])
        cash = float(f.get("money", 0))
        rows.append((day, crew, plants, animals, weeds, dirt, cash))
        print("  %3d %4d %6d %7d %5d %5d %7.0f   %6.1f"
              % (day, crew, plants, animals, weeds, dirt, cash,
                 (plants + animals) / max(1, crew)))
    print("\nfinal: $%s" % env.state[0].reward)


if __name__ == "__main__":
    main()
