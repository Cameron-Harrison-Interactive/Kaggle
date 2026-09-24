"""trace_tape.py — replay a pure-replay tape bot and log every action with
unit positions + resulting tile state. Reconstructs the author's duty plan."""
import sys, os, json, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim

def load_tape(path):
    src = open(path).read()
    m = re.search(r"TAPE = json.loads\(r'''(\[.*\])'''\)", src, re.S)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"^TAPE\s*=\s*(\[.*\])\s*$", src, re.M | re.S)
    return json.loads(m.group(1))

def trace(seed=1, tape_path='topbots/v130_gen.py'):
    tape = load_tape(tape_path)
    sim = GameSim(seed=seed)
    log = []
    for step in range(720):
        obs = sim.obs(0)
        day, hour = step // 24, step % 24
        farm = obs['farms'][0]
        act = tape[step]
        # record positions
        pos = {'farmer': tuple(farm['farmer'])}
        for i, h in enumerate(farm.get('hands', [])):
            pos[f'h{i}'] = tuple(h)
        # apply
        sim.step(act, {"farmer": ["PASS"], "hands": [], "market": []})
        newobs = sim.obs(0)
        log.append({'step': step, 'day': day, 'hour': hour, 'pos': pos,
                    'act': act, 'money': newobs['farms'][0]['money']})
    return log, sim

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'topbots/v130_gen.py'
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    log, sim = trace(seed, path)
    # Print days 0-2 with positions+actions
    for e in log[:48]:
        print(f"s{e['step']} D{e['day']}H{e['hour']} pos={e['pos']} f={e['act']['farmer']} h={e['act']['hands'][:4]} m={e['act']['market']}")
    print('final:', sim.money(0))
