"""Deep-dive: which animal buys fail and why (cash stolen by maker?).

Picks v11.7 losses w/ final_herd=13 + normal games, traces herd by day,
cash at each BUY_ANIMAL step, and maker wheat buys nearby."""
import json
import os
import subprocess

env = dict(os.environ)
os.makedirs('/tmp/esc', exist_ok=True)
GAMES = [
    ('v117_13_a', 100620339),   # Andrew Reed, final 13
    ('v117_13_b', 100654386),   # probably6767, final 13
    ('v117_15_a', 100684096),   # Anaconda, final 16
    ('v116_15_a', 100627159),   # v11.6 Jean-Louis, final 15
]
out = {}
for tag, eid in GAMES:
    path = f'/tmp/esc/episode-{eid}-replay.json'
    r = subprocess.run(['kaggle', 'competitions', 'replay', str(eid), '-p', '/tmp/esc'],
                       capture_output=True, text=True, env=env, timeout=90)
    if not os.path.exists(path):
        print(tag, 'download failed')
        continue
    d = json.load(open(path))
    os.remove(path)
    info = d.get('info', {})
    teams = info.get('TeamNames') or ['?', '?']
    me = teams.index('Harrison Interactive') if 'Harrison Interactive' in teams else 0
    steps = d['steps']
    herd_days = {}
    buy_events = []
    maker_wheat_buys_near = []
    for si in range(len(steps)):
        obs = steps[si][me].get('observation') or {}
        farms = obs.get('farms') or []
        act = steps[si][me].get('action') or {}
        if farms and len(farms) > me:
            f = farms[me]
            if si % 24 == 23:
                cnt = sum(1 for row in f['tiles'] for t in row if isinstance(t, dict) and t.get('animal'))
                herd_days[si // 24] = cnt
        money = f.get('money', 0) if farms and len(farms) > me else 0
        for o in (act.get('market') or []):
            if isinstance(o, list) and len(o) >= 2:
                if o[0] == 'BUY_ANIMAL':
                    buy_events.append({'step': si, 'animal': o[1], 'qty': o[2] if len(o) > 2 else 1,
                                       'cash_at_step': round(money)})
                elif o[0] == 'BUY_PRODUCT' and o[1] == 'WHEAT':
                    maker_wheat_buys_near.append({'step': si, 'qty': o[2] if len(o) > 2 else 1,
                                                  'cash': round(money)})
    # determine which buys failed: herd count after each buy window
    print(f'=== {tag} ({teams[1 - me]}): herd_by_day={herd_days}')
    print(f'    animal buy orders (step, animal, qty, cash_at_order):')
    for b in buy_events:
        print(f'      {b}')
    # wheat maker buys in the animal-buy window (steps 90-270)
    near = [w for w in maker_wheat_buys_near if 90 <= w['step'] <= 270]
    print(f'    maker wheat buys in buy window (90-270): {len(near)} totaling {sum(w["qty"] for w in near)} units')
    out[tag] = {'herd': herd_days, 'buys': buy_events, 'maker_window': near}
json.dump(out, open('/tmp/buyfail.json', 'w'))
