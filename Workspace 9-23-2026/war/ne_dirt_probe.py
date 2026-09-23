#!/usr/bin/env python3
"""Hour-by-hour NE tiles / seeds / crew around the open."""
import io, contextlib, os, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env


def quad(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


def main():
    ensure_env()
    import kaggle_environments as ke
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_34"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([resolve(bot), resolve("pass")])
    print("seed", seed, "bot", bot, "final", env.state[0].reward)
    print("d  h  cash  crew own  NWpl NEpl NEdirt NEweed seeds(W/M/S)  NE tiles y0-2")
    for st in env.steps:
        obs = st[0]["observation"]
        day, hour = int(obs["day"]), int(obs["hour"])
        if day < 6 or day > 12:
            continue
        if hour not in (0, 1, 2, 3, 12, 23):
            continue
        farm = obs["farms"][0]
        priv = obs["private"]
        owned = farm.get("unlocked_quadrants", ["NW"])
        money = float(farm.get("money", 0))
        crew = 1 + len(farm.get("hands") or [])
        seeds = Counter(priv.get("seeds") or {})
        nw_pl = ne_pl = ne_dirt = ne_weed = 0
        ne_row = []
        for y in range(10):
            for x in range(10):
                t = farm["tiles"][y][x]
                q = quad(x, y)
                if q == "NW" and isinstance(t, dict) and t.get("kind") == "PLANT":
                    nw_pl += 1
                if q != "NE":
                    continue
                if t is None:
                    ne_dirt += 1
                    tok = "."
                elif t == "LOCKED":
                    tok = "#"
                elif isinstance(t, dict):
                    if t.get("kind") == "WEED":
                        ne_weed += 1
                        tok = "x"
                    elif t.get("kind") == "PLANT":
                        ne_pl += 1
                        tok = t["crop"][0]
                    elif t.get("animal"):
                        tok = t["animal"][0]
                    else:
                        tok = t.get("kind", "?")[0]
                else:
                    tok = "?"
                if y <= 2:
                    ne_row.append(tok)
        print(" %d %2d %5.0f %4d %3d  %4d %4d %6d %6d  W%d M%d S%d  %s" % (
            day, hour, money, crew, len(owned), nw_pl, ne_pl, ne_dirt, ne_weed,
            seeds.get("WHEAT", 0), seeds.get("MELON", 0), seeds.get("STRAWBERRY", 0),
            "".join(ne_row)))


if __name__ == "__main__":
    main()
