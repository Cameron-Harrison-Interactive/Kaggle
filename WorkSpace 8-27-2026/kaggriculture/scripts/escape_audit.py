"""Download v11.7/v11.6 games; for each, check our herd trajectory for ESCAPES
(animal count drops) and record results."""
import json
import os
import subprocess
import sys

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
            rows.append({'tag': tag, 'eid': eid, 'error': 'dl'})
            continue
        try:
            d = json.load(open(path))
        except Exception:
            rows.append({'tag': tag, 'eid': eid, 'error': 'parse'})
            continue
        os.remove(path)
        info = d.get('info', {})
        teams = info.get('TeamNames') or ['?', '?']
        rewards = d.get('rewards') or [0, 0]
        me = teams.index('Harrison Interactive') if 'Harrison Interactive' in teams else -1
        if me < 0:
            rows.append({'tag': tag, 'eid': eid, 'error': 'notours'})
            continue
        steps = d['steps']
        # herd by day + escapes
        herd_by_day = {}
        escapes = []
        prev = None
        for si in range(len(steps)):
            obs = steps[si][me].get('observation') or {}
            farms = obs.get('farms') or []
            if not farms or len(farms) <= me:
                continue
            f = farms[me]
            day = int(obs.get('day', 0) or 0)
            if si % 24 == 23:
                cnt = {}
                for row in f['tiles']:
                    for t in row:
                        if isinstance(t, dict) and t.get('animal'):
                            cnt[t['animal']] = cnt.get(t['animal'], 0) + 1
                total = sum(cnt.values())
                herd_by_day[day] = total
                if prev is not None and total < prev:
                    escapes.append((day, prev, total))
                prev = total
        rows.append({'tag': tag, 'eid': eid, 'opp': teams[1 - me], 'me': rewards[me],
                     'opp_m': rewards[1 - me], 'res': 'W' if rewards[me] > rewards[1 - me] else ('L' if rewards[me] < rewards[1 - me] else 'T'),
                     'herd': herd_by_day, 'escapes': escapes,
                     'final_herd': herd_by_day.get(max(herd_by_day), 0) if herd_by_day else 0})
json.dump(rows, open('/tmp/esc_results.json', 'w'))
esc_games = [r for r in rows if r.get('escapes')]
loss_games = [r for r in rows if r.get('res') == 'L']
print(f'total {len(rows)} games | losses: {len(loss_games)} | games WITH animal drops: {len(esc_games)}')
print()
print('=== GAMES WITH ANIMAL DROPS ===')
for r in esc_games:
    print(f"{r['tag']} {r['eid']} {r['res']} vs {r.get('opp', '?')[:22]:22} drops={r['escapes']} herd_by_day={r['herd']}")
print()
print('=== ALL LOSSES (herd check) ===')
for r in loss_games:
    has_esc = 'ANIMALS-LOST' if r.get('escapes') else 'full-herd'
    print(f"{r['tag']} {r['eid']} vs {r.get('opp', '?')[:22]:22} {r.get('me', 0):>8,.0f} vs {r.get('opp_m', 0):<8,.0f} {has_esc} final_herd={r.get('final_herd')}")
