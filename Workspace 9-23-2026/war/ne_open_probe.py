#!/usr/bin/env python3
"""When does NE open, what cash/density did we have earlier, melon timing."""
import io, contextlib, os, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env


def quad(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


def run(bot, seed):
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([resolve(bot), resolve("pass")])
    return env


def analyse(env):
    ne_open = None
    rows = []
    melon_sold = 0
    last_owned = 1
    for st in env.steps:
        raw = st[0]
        obs = raw["observation"] if raw else {}
        if "farms" not in obs:
            continue
        day = int(obs["day"])
        hour = int(obs["hour"])
        farm = obs["farms"][0]
        priv = obs.get("private") or {}
        owned = farm.get("unlocked_quadrants", ["NW"])
        money = float(farm.get("money", 0))
        hands = 1 + len(farm.get("hands") or [])
        tiles = farm.get("tiles", [])
        plants = weeds = dirt = animals = 0
        crops = Counter()
        nw_plants = ne_plants = 0
        melon_units = 0
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                q = quad(x, y)
                if q not in owned:
                    continue
                if t is None:
                    dirt += 1
                    continue
                if not isinstance(t, dict):
                    continue
                if t.get("kind") == "WEED":
                    weeds += 1
                elif t.get("kind") == "PLANT":
                    plants += 1
                    crops[t.get("crop")] += 1
                    if q == "NW":
                        nw_plants += 1
                    if q == "NE":
                        ne_plants += 1
                    if t.get("crop") == "MELON":
                        melon_units += int(t.get("yield_units", 0) or 0)
                elif t.get("animal"):
                    animals += 1
        shed = Counter((priv.get("shed") or {}) if isinstance(priv, dict) else {})
        # try step observation
        if not shed:
            p0 = st[0].get("observation", {})
            priv2 = p0.get("private") or {}
            shed = Counter(priv2.get("shed") or {})
        px = (obs.get("market") or {}).get("prices") or {}
        if len(owned) > last_owned and ne_open is None and "NE" in owned:
            ne_open = (day, hour, money, plants, dirt, animals, dict(crops),
                       dict(px), dict(shed))
        last_owned = len(owned)
        if hour == 0:
            rows.append(dict(
                d=day, m=money, n=hands, owned=len(owned),
                plants=plants, dirt=dirt, weeds=weeds, an=animals,
                nw=nw_plants, ne=ne_plants, crops=dict(crops),
                melon_u=melon_units, shed_m=int(shed.get("MELON", 0)),
                fert_px=px.get("FERTILIZER"), melon_px=px.get("MELON"),
                strb_px=px.get("STRAWBERRY"),
            ))
    return ne_open, rows, float(env.state[0].reward)


def main():
    ensure_env()
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_34"
    seeds = [int(s) for s in sys.argv[2:]] or [42, 5, 101]
    for s in seeds:
        env = run(bot, s)
        ne, rows, reward = analyse(env)
        print("=" * 70)
        print("seed %d  final $%.0f  bot %s" % (s, reward, bot))
        if ne:
            d, h, m, plants, dirt, an, crops, px, shed = ne
            print("  NE OPENED d%d h%d  cash=$%.0f  plants=%d dirt=%d an=%d" % (
                d, h, m, plants, dirt, an))
            print("  crops", crops)
            print("  px melon=%s fert=%s strb=%s" % (
                px.get("MELON"), px.get("FERTILIZER"), px.get("STRAWBERRY")))
        else:
            print("  NE NEVER OPENED")
        print("  day  cash   n own pl dirt an  NW NE  crops                  melon$ fert$")
        for r in rows:
            if r["d"] > 16:
                break
            crops = "".join("%s%d" % (k[0], v) for k, v in sorted(r["crops"].items())) or "-"
            print("  %3d %6.0f %3d %3d %3d %4d %2d  %2d %2d  %-20s %5s %5s" % (
                r["d"], r["m"], r["n"], r["owned"], r["plants"], r["dirt"],
                r["an"], r["nw"], r["ne"], crops, r["melon_px"], r["fert_px"]))


if __name__ == "__main__":
    main()
