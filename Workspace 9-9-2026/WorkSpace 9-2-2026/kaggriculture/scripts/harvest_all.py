"""Harvest all our episodes (v11.6/11.4/11.3) -> results table + loss corpus."""
import json
import os
import subprocess
import sys

env = dict(os.environ)
eps_map = json.load(open('/tmp/our_eps.json'))
os.makedirs('/tmp/allgames', exist_ok=True)
rows = []
for label, eps in eps_map.items():
    for eid in eps:
        path = f'/tmp/allgames/episode-{eid}-replay.json'
        r = subprocess.run(['kaggle', 'competitions', 'replay', str(eid), '-p', '/tmp/allgames'],
                           capture_output=True, text=True, env=env, timeout=90)
        if not os.path.exists(path):
            rows.append({'sub': label, 'eid': eid, 'error': 'download'})
            continue
        try:
            d = json.load(open(path))
        except Exception:
            rows.append({'sub': label, 'eid': eid, 'error': 'parse'})
            continue
        os.remove(path)
        info = d.get('info', {})
        teams = info.get('TeamNames') or ['?', '?']
        rewards = d.get('rewards') or [0, 0]
        me = teams.index('Harrison Interactive') if 'Harrison Interactive' in teams else -1
        if me < 0:
            rows.append({'sub': label, 'eid': eid, 'error': 'not-ours', 'teams': teams})
            continue
        my, th = rewards[me], rewards[1 - me]
        rows.append({'sub': label, 'eid': eid, 'opp': teams[1 - me], 'me': my, 'opp_money': th,
                     'res': 'W' if my > th else ('L' if my < th else 'T'),
                     'margin': my - th, 'seed': info.get('seed')})
json.dump(rows, open('/tmp/all_results.json', 'w'), indent=0)
w = sum(1 for r in rows if r.get('res') == 'W')
l = sum(1 for r in rows if r.get('res') == 'L')
t = sum(1 for r in rows if r.get('res') == 'T')
print(f'total: {w}W-{l}L-{t}T of {len(rows)}')
for r in sorted(rows, key=lambda r: (r.get('res') or 'E', -(r.get('margin') or 0))):
    if r.get('error'):
        print(f"  {r['sub']} {r['eid']}: {r['error']}")
    else:
        print(f"  {r['sub']} {r['eid']}: {r['res']} vs {r['opp'][:24]:24} {r['me']:>8,.0f} vs {r['opp_money']:<8,.0f} margin={r['margin']:+,.0f}")
