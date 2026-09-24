"""eval_shape.py — solo eval with farm-shape diagnostics:
strawberry tiles alive/planted/dead, animals placed, missed feeds, SE status.

Usage: python3 _ref/eval_shape.py <bot.py> [seeds...]
"""
import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim  # noqa: E402


def load(path, name="botmod"):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def call(fn, obs):
    try:
        return fn(obs, None)
    except TypeError:
        return fn(obs)


def solo_diag(mod, seed):
    sim = GameSim(seed=seed)
    a1 = {"farmer": ["PASS"], "hands": [], "market": []}
    straw_planted = 0      # max strawberries ever alive
    straw_dead = 0         # strawberries that turned to WEED
    cows = sheep = 0
    unfed_animal_days = 0
    for step in range(720):
        o = sim.obs(0)
        a = call(mod.agent, o)
        farm = o["farms"][0]
        for row in farm["tiles"]:
            for t in row:
                if not isinstance(t, dict):
                    continue
                if t.get("crop") == "STRAWBERRY":
                    straw_planted += 1
                if t.get("kind") == "WEED":
                    straw_dead += 1  # approximate: weeds incl. random spawns
                if t.get("animal") == "COW":
                    cows += 1
                    if not t.get("fed_today") and o["hour"] == 23:
                        unfed_animal_days += 1
                if t.get("animal") == "SHEEP":
                    sheep += 1
                    if not t.get("fed_today") and o["hour"] == 23:
                        unfed_animal_days += 1
        sim.step(a, a1)
    return {
        "money": sim.money(0),
        "straw_tile_steps": straw_planted,   # sum over hours; /24 = tile-days
        "weeds": straw_dead,
        "cow_tile_steps": cows // 24,
        "sheep_tile_steps": sheep // 24,
        "unfed": unfed_animal_days,
    }


if __name__ == "__main__":
    bot = sys.argv[1]
    seeds = [int(x) for x in sys.argv[2:]] or list(range(1, 13))
    mod = load(bot, "eb")
    tot = 0.0
    print(f"{bot}: seed  money   strawTileDays weeds cows sheep unfedDays")
    for s in seeds:
        d = solo_diag(mod, s)
        tot += d["money"]
        print(f"  {s:4d} {d['money']:8.0f} {d['straw_tile_steps']:8d} {d['weeds']:6d} "
              f"{d['cow_tile_steps']:5d} {d['sheep_tile_steps']:5d} {d['unfed']:5d}")
    print(f"AVG money over {len(seeds)} seeds: {tot/len(seeds):,.0f}")
