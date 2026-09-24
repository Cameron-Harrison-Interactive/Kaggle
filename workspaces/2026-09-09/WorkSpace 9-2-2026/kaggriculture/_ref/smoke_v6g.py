"""Smoke test: v6g vs champion on a seed — guard activity, straw throughput, money."""
import importlib.util
import os
import sys

base = '/home/user/WorkSpace 9-2-2026'
real = [d for d in os.listdir(base)
        if os.path.isdir(os.path.join(base, d))
        and os.path.isdir(os.path.join(base, d, 'topbots'))][0]
ROOT = os.path.join(base, real)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

import sim as simmod

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

SEED = int(os.environ.get('SEED', '1'))


def run(bot_name, guard_debug=False):
    m = load(os.path.join(ROOT, 'topbots', bot_name + '.py'), bot_name + '_run')
    stats = {'move': 0, 'WATER': 0, 'HARVEST': 0, 'mkt_resize': 0, 'mkt_append': 0,
             'straw_units': 0, 'unfed_days': 0}
    sim = simmod.GameSim(seed=SEED)
    for step in range(720):
        o = sim.obs(0)
        if guard_debug:
            base_a = m._tape_action(step)
            action = {
                'farmer': list(base_a.get('farmer') or ['PASS']),
                'hands': [list(h) for h in (base_a.get('hands') or [])],
                'market': [list(x) for x in (base_a.get('market') or [])],
            }
            shed_before = dict(((o.get('private') or {}).get('shed') or {}))
            m._guard(action, o, step)  # let exceptions surface
            for before, after in zip(base_a.get('hands') or [], action['hands']):
                if before != after:
                    if after and after[0] in ('NORTH', 'SOUTH', 'EAST', 'WEST'):
                        stats['move'] += 1
                    elif after and after[0] in ('WATER', 'HARVEST'):
                        stats[after[0]] += 1
            stats['mkt_resize'] += sum(
                1 for b, a in zip(base_a.get('market') or [], action['market']) if b != a)
            stats['mkt_append'] += len(action['market']) - len(base_a.get('market') or [])
        else:
            action = m.agent(o, None)
        shed_before = shed_before if guard_debug else (
            dict(((o.get('private') or {}).get('shed') or {})))
        has_straw_sell = any(isinstance(x, list) and len(x) >= 3 and x[0] == 'SELL'
                             and x[1] == 'STRAWBERRY' for x in (action.get('market') or []))
        sim.step(action, {'farmer': ['PASS'], 'hands': [], 'market': []})
        if has_straw_sell:
            shed_after = ((sim.obs(0).get('private') or {}).get('shed') or {}).get('STRAWBERRY', 0)
            stats['straw_units'] += max(0, shed_before.get('STRAWBERRY', 0) - shed_after)
    # end-of-game metrics
    o = sim.obs(0)
    farm = o['farms'][0]
    weeds = sum(1 for row in farm['tiles'] for t in row if isinstance(t, dict) and t.get('kind') == 'WEED')
    unfed = sum(1 for row in farm['tiles'] for t in row
                if isinstance(t, dict) and t.get('animal') and t.get('consecutive_unfed', 0) > 0)
    return sim.money(0), stats, weeds, unfed


import os as _os
for bot in ('v4_fr1', _os.environ.get('BOT', 'v6g')):
    money, stats, weeds, unfed = run(bot, guard_debug=(bot == 'v6g'))
    print(f'{bot:8s} seed {SEED}: money={money:>9,.0f}  straw_sold={stats["straw_units"]:3d}u  '
          f'weeds={weeds:3d}  tiles_unfed_now={unfed:2d}  guard={stats}')
