"""Per-straw-tile lifecycle trace: champion seed 1 — deaths, events, harvests."""
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

m = load(os.path.join(ROOT, 'topbots', 'v4_fr1.py'), 'champ')
sim = simmod.GameSim(seed=1)

# track straw tiles by position
trace = {}   # (x,y) -> list of (day, hour, event, detail)
prev = {}    # (x,y) -> dict of tile fields last seen

def scan(o, day, hour):
    farm = o['farms'][0]
    for y, row in enumerate(farm['tiles']):
        for x, t in enumerate(row):
            key = (x, y)
            if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY':
                cur = (t.get('planted_day'), t.get('consecutive_unwatered'),
                       t.get('yield_units'), t.get('watered_today'))
                if key not in prev:
                    trace.setdefault(key, []).append((day, hour, 'PLANT', cur))
                elif prev[key] != cur:
                    p = prev[key]
                    if p[2] != cur[2]:
                        trace.setdefault(key, []).append(
                            (day, hour, f'yield {p[2]}->{cur[2]}', cur))
                    if p[1] != cur[1]:
                        trace.setdefault(key, []).append(
                            (day, hour, f'cu {p[1]}->{cur[1]}', cur))
                    prev[key] = cur
                    continue
                prev[key] = cur
            elif key in prev and not (isinstance(t, dict) and t.get('crop') == 'STRAWBERRY'):
                kind = t.get('kind') if isinstance(t, dict) else t
                trace.setdefault(key, []).append((day, hour, f'GONE->{kind}', None))
                del prev[key]

for step in range(720):
    o = sim.obs(0)
    scan(o, o['day'], o['hour'])
    a = m.agent(o, None)
    sim.step(a, {'farmer': ['PASS'], 'hands': [], 'market': []})

print('straw tiles:', len(trace))
tot_yield = 0
for key in sorted(trace):
    events = [e for e in trace[key] if 'yield' in e[2] or 'GONE' in e[2] or e[2] == 'PLANT']
    yield_events = [e for e in trace[key] if e[2].startswith('yield')]
    final = prev.get(key)
    tot_yield += (final[2] if final else 0)
    print(f'{key}: ' + ' | '.join(f'D{e[0]}H{e[1]:02d} {e[2]}' for e in events))
print('sum of final yield_units still on tiles:', tot_yield)
print('final money:', f'{sim.money(0):,.0f}')
