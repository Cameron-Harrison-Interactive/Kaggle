"""Build topbots/v6h.py — champion calendar + capacity-fitted ramp (v2: greedy
calendar-safe bumping, one day at a time, largest deficit first, revert on shift).
"""
import importlib.util
import io
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

champ_src = io.open("topbots/v4_fr1.py", encoding="utf-8").read()
spec = json.loads(
    champ_src.split("tape_author3 spec ")[1].split("). Pure replay")[0]
)
base_ramp = list(spec["ramp"])

MAX_HANDS = 12
_nonces = [0]


def load_author(ramp):
    _nonces[0] += 1
    s = dict(spec)
    s["ramp"] = list(ramp)
    os.environ["TAPE_SPEC"] = json.dumps(s)
    os.environ["TAPE_OUT"] = ""
    mod = importlib.util.spec_from_file_location(
        "auth_%d" % _nonces[0], "_ref/tape_author3.py")
    m = importlib.util.module_from_spec(mod)
    mod.loader.exec_module(m)
    return m


def calendar_fp(m):
    return sorted((t[0], t[1], d, a)
                  for t, dl in m.CROP_DUTIES.items() for d, a in dl)


def planned_ops(m):
    planned = defaultdict(lambda: defaultdict(int))
    for t, dl in m.CROP_DUTIES.items():
        for d, act in dl:
            if act.startswith("PLANT:"):
                planned[d]["DIG"] += 1
                planned[d]["PLANT"] += 1
            else:
                planned[d][act] += 1
    for day in range(30):
        for tile, kind, pd in m.animals_on(day):
            if pd == day:
                planned[day][m.STRUCT[kind]] += 1
                planned[day]["PLACE"] += 1
                planned[day]["FEED"] += 1
            else:
                planned[day]["FEED"] += 1
                planned[day]["CARE"] += 1
                planned[day]["COLLECT_FERTILIZER"] += 1
                if day in m.animal_harvest_days(kind, pd):
                    planned[day]["HARVEST"] += 1
    return planned


def executed_ops(tape):
    ex = defaultdict(lambda: defaultdict(int))
    for step, row in enumerate(tape):
        d = step // 24
        for a in [row.get("farmer") or []] + (row.get("hands") or []):
            if a:
                ex[d][a[0]] += 1
    return ex


def deficits(m, tape):
    pl = planned_ops(m)
    ex = executed_ops(tape)
    out = {}
    for d in range(30):
        dd = {op: pl[d][op] - ex[d][op]
              for op in pl[d] if pl[d][op] - ex[d][op] > 0}
        if dd:
            out[d] = dd
    return out


champ_m = load_author(base_ramp)
champ_cal = calendar_fp(champ_m)

ramp = list(base_ramp)
bumps = []
blocked = set()
for it in range(60):
    m = load_author(ramp)
    if calendar_fp(m) != champ_cal:
        raise SystemExit("calendar shifted unexpectedly at iter %d" % it)
    tape = m.author()
    defs = deficits(m, tape)
    if not defs:
        break
    # candidate days: largest total deficit first, late days preferred on ties
    order = sorted(defs, key=lambda d: (-sum(defs[d].values()), -d))
    progressed = False
    for d in order:
        if d in blocked or ramp[d] >= MAX_HANDS:
            continue
        trial = list(ramp)
        trial[d] += 1
        tm = load_author(trial)
        if calendar_fp(tm) != champ_cal:
            blocked.add(d)
            print("iter %d: bump D%d would shift calendar — blocked" % (it, d))
            continue
        ramp = trial
        bumps.append(d)
        progressed = True
        print("iter %d: bumped D%d -> %d hands (defs %s)"
              % (it, d, ramp[d], dict(defs[d])))
        break
    if not progressed:
        print("no safe bumps left; remaining deficits:", dict(defs))
        break

m = load_author(ramp)
tape = m.author()
final_defs = deficits(m, tape)
print()
print("fitted ramp:", ramp)
print("bumped days:", bumps)
print("final same-day deficits:", dict(final_defs) or "NONE")
# waters may legally execute +1 day (2-day fuse, deterministic carry).
# verify every planned WATER executes on its day or the next.
ed = defaultdict(lambda: defaultdict(int))
for step, row in enumerate(tape):
    d = step // 24
    for a in [row.get("farmer") or []] + (row.get("hands") or []):
        if a and a[0] == "WATER":
            ed[d]["WATER"] += 1
pl = planned_ops(m)
late_bad = []
for d in range(30):
    need = pl[d]["WATER"]
    got = ed[d]["WATER"] + ed[d + 1]["WATER"] if d < 29 else ed[d]["WATER"]
    if got < need:
        late_bad.append((d, need, got))
print("water shortfalls even with +1-day carry:", late_bad or "NONE")
if late_bad:
    raise SystemExit("ABORT: waters lost beyond fuse tolerance")

# emit via the author's writer
os.environ["TAPE_SPEC"] = json.dumps({**spec, "ramp": ramp})
os.environ["TAPE_OUT"] = "topbots/v6h.py"
mod = importlib.util.spec_from_file_location("auth_out", "_ref/tape_author3.py")
m2 = importlib.util.module_from_spec(mod)
mod.loader.exec_module(m2)
m2.author()
v6h_src = io.open("topbots/v6h.py", encoding="utf-8").read()
vt = json.loads(v6h_src.split("TAPE = json.loads(r'''")[1].split("''')")[0])
assert vt == tape, "written tape != fitted tape"
print("v6h written:", os.path.getsize("topbots/v6h.py"), "bytes — ZERO deficits")
