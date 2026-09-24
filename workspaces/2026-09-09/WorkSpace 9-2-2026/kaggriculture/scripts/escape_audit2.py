"""Escape audit v2: track ANIMAL TILES (not totals) — catches escapes masked
by same-day placements. Runs on v11.7 + v11.6 episode lists."""
import json
import os
import subprocess

env = dict(os.environ)
os.makedirs('/tmp/esc', exist_ok=True)
rows = []
for tag in ('v117', 'v116'):
    eps = json.load(open(f'/tmp/eps_{tag}.json'))
    for eid in eps:
        path = f'/tmp/esc/episode-{eid}-replay.json'
        r = subprocess.run(['kaggle', 'competitions', 'replay', str(eid), '-p', '/tmp/esc'],
                           capture_output=True, text=True, env=env, timeout=90)
        if not os.path.exists(path):
            continue
        try:
            d = json.load(open(path))
        except Exception:
            os.remove(path)
            continue
        os.remove(path)
        info = d.get('info', {})
        teams = info.get('TeamNames') or ['?', '?']
        rewards = d.get('rewards') or [0, 0]
        me = teams.index('Harrison Interactive') if 'Harrison Interactive' in teams else -1
        if me < 0:
            continue
        steps = d['steps']
        known = {}
        escapes = []
        for si in range(len(steps)):
            obs = steps[si][me].get('observation') or {}
            farms = obs.get('farms') or []
            if not farms or len(farms) <= me:
                continue
            f = farms[me]
            day = int(obs.get('day', 0) or 0)
            now = {}
            for y, row in enumerate(f['tiles']):
                for x, t in enumerate(row):
                    if isinstance(t, dict) and t.get('animal'):
                        now[(x, y)] = t
            for pos in list(known):
                if pos not in now and not known[pos].get('gone'):
                    known[pos]['gone'] = True
                    escapes.append({'pos': pos, 'animal': known[pos]['animal'],
                                    'placed': known[pos]['placed_day'], 'vanished_day': day})
            for pos, t in now.items():
                if pos not in known or known[pos].get('gone'):
                    known[pos] = {'animal': t['animal'], 'placed_day': t.get('placed_day')}
        if escapes:
            rows.append({'tag': tag, 'eid': eid, 'opp': teams[1 - me],
                         'res': 'W' if rewards[me] > rewards[1 - me] else 'L',
                         'me': rewards[me], 'opp_m': rewards[1 - me],
                         'escapes': escapes, 'seat': me})
print(f'games with escapes: {len(rows)}')
for r in rows:
    esc = '; '.join(f"{e['animal']}@{e['pos']} placedD{e['placed']} goneD{e['vanished_day']}" for e in r['escapes'])
    print(f"  {r['tag']} {r['eid']} seat{r['seat']} {r['res']} vs {r['opp'][:22]:22} {r['me']:>8,.0f}v{r['opp_m']:<8,.0f} :: {esc}")
json.dump(rows, open('/tmp/escapes_v2.json', 'w'))
