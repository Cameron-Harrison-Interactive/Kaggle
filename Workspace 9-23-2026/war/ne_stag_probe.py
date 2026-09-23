#!/usr/bin/env python3
"""NE animals vs crops, and which day each strawberry was planted."""
import io, contextlib, os, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env


def Q(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


def main():
    ensure_env()
    import kaggle_environments as ke
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_34"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([resolve(bot), resolve("pass")])
    print("seed", seed, "bot", bot, "final", round(env.state[0].reward))
    print("d  cash  own  NWan NEan  NEcrop NEdirt  strb_stand  strb_seeds  planted_today")
    prev_strb = {}
    plant_days = Counter()
    for st in env.steps:
        obs = st[0]["observation"]
        day, hour = int(obs["day"]), int(obs["hour"])
        if hour != 23:
            continue
        farm = obs["farms"][0]
        priv = obs["private"]
        owned = farm.get("unlocked_quadrants", ["NW"])
        money = float(farm.get("money", 0))
        seeds = Counter(priv.get("seeds") or {})
        nwan = nean = necrop = nedirt = 0
        strb = 0
        by_planted = Counter()
        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                q = Q(x, y)
                if not isinstance(t, dict):
                    if q == "NE" and t is None:
                        nedirt += 1
                    continue
                if t.get("animal"):
                    if q == "NW":
                        nwan += 1
                    if q == "NE":
                        nean += 1
                if q != "NE":
                    continue
                if t.get("kind") == "PLANT":
                    necrop += 1
                    if t.get("crop") == "STRAWBERRY":
                        strb += 1
                        pd = int(t.get("planted_day", day))
                        by_planted[pd] += 1
                        key = (x, y)
                        if key not in prev_strb or prev_strb[key] != pd:
                            plant_days[pd] += 1
                            prev_strb[key] = pd
        print(" %2d %5.0f %3d  %4d %4d  %6d %6d  %9d  %10d  %s" % (
            day, money, len(owned), nwan, nean, necrop, nedirt, strb,
            seeds.get("STRAWBERRY", 0),
            dict(by_planted) or "-"))
        if day >= 20:
            break
    print("first-seen plant days", dict(plant_days))


if __name__ == "__main__":
    main()
