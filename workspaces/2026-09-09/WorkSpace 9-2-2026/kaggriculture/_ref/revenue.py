"""revenue.py — per-product revenue + cost breakdown for a tape bot.
Usage: python3 _ref/revenue.py <bot.py> [seeds...]"""
import sys, os, json, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim

def load(path):
    spec = importlib.util.spec_from_file_location("botmod", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def call(fn, obs):
    try: return fn(obs, None)
    except TypeError: return fn(obs)

def run(path, seed):
    m = load(path)
    sim = GameSim(seed=seed)
    rev = {}; cost = {}; bought = {}
    for step in range(720):
        obs = sim.obs(0)
        money0 = obs['farms'][0]['money']
        a = call(m.agent, obs)
        sim.step(a, {"farmer": ["PASS"], "hands": [], "market": []})
        obs2 = sim.obs(0)
        dm = obs2['farms'][0]['money'] - money0
        if dm != 0:
            # attribute to this hour's market orders
            for o in a.get('market', []):
                if not o: continue
                if o[0] == 'SELL':
                    rev[o[1]] = rev.get(o[1], 0)  # actual split below
                elif o[0] in ('BUY_PRODUCT','BUY_SEED','BUY_ANIMAL'):
                    pass
            # crude: net delta attributed by scanning orders present
            sells = [o for o in a.get('market', []) if o and o[0]=='SELL']
            buys = [o for o in a.get('market', []) if o and o[0] in ('BUY_PRODUCT','BUY_SEED','BUY_ANIMAL')]
            if sells and not buys and dm > 0:
                # spread across sold items proportionally to qty (approx)
                tot = sum(o[2] for o in sells)
                for o in sells:
                    rev[o[1]] = rev.get(o[1], 0) + dm * o[2] / tot
            elif buys and dm < 0 and not sells:
                for o in buys:
                    key = o[0] + ':' + str(o[1])
                    # spread cost by qty*unitprice approx
                    price = {'BUY_SEED': {'MELON':80,'WHEAT':10,'STRAWBERRY':100,'TOMATO':50,'CARROT':20},
                             'BUY_ANIMAL': {'COW':400,'SHEEP':500,'GOOSE':300}}.get(o[0], {}).get(o[1], 25)
                    cost[key] = cost.get(key, 0) + price * o[2]
            elif buys and sells:
                for o in buys:
                    price = {'BUY_SEED': {'MELON':80,'WHEAT':10,'STRAWBERRY':100,'TOMATO':50,'CARROT':20},
                             'BUY_ANIMAL': {'COW':400,'SHEEP':500,'GOOSE':300}}.get(o[0], {}).get(o[1], 25)
                    cost[key if False else o[0]+':'+str(o[1])] = cost.get(o[0]+':'+str(o[1]), 0) + price*o[2]
                if dm > 0:
                    tot = sum(o[2] for o in sells)
                    for o in sells:
                        rev[o[1]] = rev.get(o[1], 0) + dm * o[2] / tot
            # hires: cost via money drop with no buys/sells
            if not sells and not buys and dm < 0:
                cost['HIRE'] = cost.get('HIRE', 0) + (-dm)
    return rev, cost, sim.money(0)

if __name__ == '__main__':
    path = sys.argv[1]
    seeds = [int(x) for x in sys.argv[2:]] or [1,2,3,4,5,6,7,8]
    agg_rev = {}; agg_cost = {}; finals = []
    for s in seeds:
        rev, cost, fin = run(path, s)
        finals.append(fin)
        for k, v in rev.items(): agg_rev[k] = agg_rev.get(k, 0) + v
        for k, v in cost.items(): agg_cost[k] = agg_cost.get(k, 0) + v
    n = len(seeds)
    print(f"== {path}  avg final {sum(finals)/n:,.0f}")
    print("  revenue/unit (avg per game):")
    for k in sorted(agg_rev, key=lambda k: -agg_rev[k]):
        print(f"    {k:12s} {agg_rev[k]/n:>10,.0f}")
    print("  costs (avg per game):")
    for k in sorted(agg_cost, key=lambda k: -agg_cost[k]):
        print(f"    {k:12s} {agg_cost[k]/n:>10,.0f}")
