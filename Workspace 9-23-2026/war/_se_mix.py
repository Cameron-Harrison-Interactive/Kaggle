#!/usr/bin/env python3
import io, contextlib, os, sys
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env

def Q(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")

def main():
    ensure_env()
    import kaggle_environments as ke
    bot = sys.argv[1]
    seed = int(sys.argv[2])
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([resolve(bot), resolve("pass")])
    print("seed", seed, "bot", bot, "final", round(env.state[0].reward))
    for st in env.steps:
        obs = st[0]["observation"]
        day, hour = int(obs["day"]), int(obs["hour"])
        if hour != 23 or day not in (12, 16, 20, 24, 29):
            continue
        farm = obs["farms"][0]
        c = Counter()
        dirt = 0
        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                if Q(x, y) != "SE":
                    continue
                if t is None:
                    dirt += 1
                elif isinstance(t, dict) and t.get("kind") == "PLANT":
                    c[t.get("crop")] += 1
        print("d%d SE" % day, dict(c), "dirt", dirt)
    print("owned last", env.state[0]["observation"]["farms"][0].get("unlocked_quadrants"))

if __name__ == "__main__":
    main()
