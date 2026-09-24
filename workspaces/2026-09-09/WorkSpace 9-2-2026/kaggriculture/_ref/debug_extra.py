"""Trace the 11th (guard) hand's position + emitted action, D16, seed 1."""
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

m = load(os.path.join(ROOT, 'topbots', 'v6g.py'), 'v6gx')
sim = simmod.GameSim(seed=1)

for step in range(720):
    o = sim.obs(0)
    day, hour = o['day'], o['hour']
    base_a = m._tape_action(step)
    action = {
        'farmer': list(base_a.get('farmer') or ['PASS']),
        'hands': [list(h) for h in (base_a.get('hands') or [])],
        'market': [list(x) for x in (base_a.get('market') or [])],
    }
    m._guard(action, o, step)
    if day == 16 and 0 <= hour <= 23:
        hands = o['farms'][0].get('hands') or []
        extra = f'farm_hands={len(hands)}'
        pos = hands[10] if len(hands) > 10 else None
        act10 = action['hands'][10] if len(action['hands']) > 10 else None
        print(f'H{hour:02d} extra_pos={pos} act10={act10} '
              f'n_action_hands={len(action["hands"])} {extra}')
    sim.step(action, {'farmer': ['PASS'], 'hands': [], 'market': []})
