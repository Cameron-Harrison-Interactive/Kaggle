"""Debug v6g guard: why do far-east straw tiles die at D15/D17 despite water-rescue?"""
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

m = load(os.path.join(ROOT, 'topbots', 'v6g.py'), 'v6gdbg')
sim = simmod.GameSim(seed=1)

WATCH = {(8, 0), (9, 0), (9, 1), (9, 2), (9, 3), (9, 4)}

for step in range(720):
    o = sim.obs(0)
    day, hour = o['day'], o['hour']
    base_a = m._tape_action(step)
    action = {
        'farmer': list(base_a.get('farmer') or ['PASS']),
        'hands': [list(h) for h in (base_a.get('hands') or [])],
        'market': [list(x) for x in (base_a.get('market') or [])],
    }
    if 11 <= day <= 18 and hour in (0, 12, 16, 20, 23):
        farm = o['farms'][0]
        tiles = farm['tiles']
        hands = farm.get('hands') or []
        tape_hands = base_a.get('hands') or []
        idle = [hi for hi in range(min(len(tape_hands), len(hands)))
                if tape_hands[hi] == ['PASS'] and m._hand_idle_rest_of_day(step, hi)]
        now_pass = [hi for hi in range(min(len(tape_hands), len(hands)))
                    if tape_hands[hi] == ['PASS']]
        planned = set((x, y) for x, y in m.WATER_PLAN.get(day, []))
        watch_status = []
        for (x, y) in sorted(WATCH):
            t = tiles[y][x]
            if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY':
                watch_status.append(
                    f'({x},{y})cu{t.get("consecutive_unwatered")}'
                    f'w{int(bool(t.get("watered_today")))}'
                    f'p{int((x, y) in planned)}')
        print(f'D{day}H{hour:02d} hands={len(hands)} pass_now={now_pass} idle_rest={idle} '
              f'| {" ".join(watch_status)}')
    m._guard(action, o, step)
    if 11 <= day <= 18 and hour in (0, 16):
        for hi, (b, a) in enumerate(zip(base_a.get('hands') or [], action['hands'])):
            if b != a:
                print(f'    D{day}H{hour:02d} hijack hand{hi}: {b} -> {a}')
    sim.step(action, {'farmer': ['PASS'], 'hands': [], 'market': []})

print('final money:', f'{sim.money(0):,.0f}')
