"""diag_tape.py — per-day diagnosis of a generated tape: cash, herd, escapes,
duties, sells, tile census. Usage: python3 _ref/diag_tape.py <bot.py> [seed]"""
import sys, os, json, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim

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

def diag(path, seed=1):
    m = load(path)
    sim = GameSim(seed=seed)
    prev_animals = {}
    for day in range(30):
        day_money0 = None
        escaped = []
        sold = {}
        for h in range(24):
            obs = sim.obs(0)
            farm = obs['farms'][0]
            if h == 0:
                day_money0 = farm['money']
                # census animals
                cur = {}
                for y, row in enumerate(farm['tiles']):
                    for x, tile in enumerate(row):
                        if isinstance(tile, dict) and 'animal' in tile:
                            cur[(x, y)] = tile['animal']
                for k, v in prev_animals.items():
                    if k not in cur:
                        escaped.append((k, v))
                prev_animals = cur
                census = {}
                for y, row in enumerate(farm['tiles']):
                    for x, tile in enumerate(row):
                        if isinstance(tile, dict):
                            k = tile.get('kind')
                            if 'animal' in tile:
                                k = 'A:' + tile['animal']
                            elif k == 'PLANT':
                                k = 'P:' + tile['crop']
                            census[k] = census.get(k, 0) + 1
                        elif tile is None:
                            census['EMPTY'] = census.get('EMPTY', 0) + 1
                        elif tile == 'LOCKED':
                            census['LOCKED'] = census.get('LOCKED', 0) + 1
            a = call(m.agent, obs)
            for o in a.get('market', []):
                if o and o[0] == 'SELL':
                    pass
            sim.step(a, {"farmer": ["PASS"], "hands": [], "market": []})
        obs = sim.obs(0)
        farm = obs['farms'][0]
        shed = obs['private']['shed']
        print(f"D{day:2d} ${farm['money']:>9,.0f} Δ{farm['money']-day_money0:>8,.0f} "
              f"herd={len(prev_animals)} esc={escaped} "
              f"shed={dict(sorted(shed.items()))}")
        if day % 5 == 4 or day == 29:
            print(f"     census: {dict(sorted(census.items()))}")
    print('FINAL:', sim.money(0))

if __name__ == '__main__':
    diag(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
