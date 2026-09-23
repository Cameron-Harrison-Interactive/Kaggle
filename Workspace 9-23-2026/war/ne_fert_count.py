#!/usr/bin/env python3
import io, contextlib, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env


def Q(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


def main():
    ensure_env()
    import kaggle_environments as ke
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_41"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([resolve(bot), resolve("pass")])
    fert_n = water_n = fert_s = water_s = pickup_f = fert_all = 0
    fert_eod = strb_eod = fert_eod_s = strb_eod_s = 0
    for st in env.steps:
        obs = st[0]["observation"]
        day, hour = int(obs["day"]), int(obs["hour"])
        farm = obs["farms"][0]
        act = st[0].get("action") or {}
        units = []
        if isinstance(act.get("farmer"), list):
            units.append((tuple(farm.get("farmer") or (0, 0)), act["farmer"]))
        hands = list(farm.get("hands") or [])
        for i, h in enumerate(act.get("hands") or []):
            pos = tuple(hands[i]) if i < len(hands) else None
            units.append((pos, h))
        for pos, u in units:
            if not u:
                continue
            op = u[0]
            if op == "FERTILIZE":
                fert_all += 1
            if op == "PICKUP" and len(u) > 1 and u[1] == "FERTILIZER":
                pickup_f += 1
            if pos:
                qq = Q(pos[0], pos[1])
                if qq == "NE":
                    if op == "FERTILIZE":
                        fert_n += 1
                    if op == "WATER":
                        water_n += 1
                if qq == "SW":
                    if op == "FERTILIZE":
                        fert_s += 1
                    if op == "WATER":
                        water_s += 1
        if hour == 23:
            for y, row in enumerate(farm["tiles"]):
                for x, t in enumerate(row):
                    if not isinstance(t, dict):
                        continue
                    if t.get("kind") != "PLANT" or t.get("crop") != "STRAWBERRY":
                        continue
                    qq = Q(x, y)
                    flag = int(t.get("fertilized_until_day", -1)) >= day
                    if qq == "NE":
                        strb_eod += 1
                        fert_eod += int(flag)
                    if qq == "SW":
                        strb_eod_s += 1
                        fert_eod_s += int(flag)
    print("seed", seed, "bot", bot, "final", round(env.state[0].reward))
    print("PICKUP FERT", pickup_f, "FERTILIZE all", fert_all)
    print("NE WATER", water_n, "NE FERTILIZE", fert_n,
          "strb-days", strb_eod, "fert h23", fert_eod)
    print("SW WATER", water_s, "SW FERTILIZE", fert_s,
          "strb-days", strb_eod_s, "fert h23", fert_eod_s)


if __name__ == "__main__":
    main()
