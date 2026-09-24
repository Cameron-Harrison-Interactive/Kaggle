"""Build topbots/v6i.py: v6h2 author + straw_stagger 3 + re-fitted ramp.

The stagger spreads the 13 straw tiles over plant days p, p+1, p+2 ->
first harvests p+12 on three days (5/4/4 tiles), final harvests p+16 on
three days, keeping every day's EOD shed inflow under the 100 cap AND
selling straw in shallow daily batches (better depth) instead of one
52-unit morning dump.

Ramp fit: same greedy capacity fitter as v6h, but the calendar guard is
SELF-CONSISTENT (iteration 0's calendar with the stagger on; any bump that
shifts it is reverted). Water +1-day carry relaxation verified as before.
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
    champ_src.split("tape_author3 spec ")[1].split("). Pure replay")[0])
SPEC = {**spec, "straw_stagger": 3}
base_ramp = list(spec["ramp"])

MAX_HANDS = 12
_nonces = [0]


def load_author(ramp):
    _nonces[0] += 1
    s = dict(SPEC)
    s["ramp"] = list(ramp)
    os.environ["TAPE_SPEC"] = json.dumps(s)
    os.environ["TAPE_OUT"] = ""
    mod = importlib.util.spec_from_file_location(
        "authi_%d" % _nonces[0], "_ref/tape_author3.py")
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


m0 = load_author(base_ramp)
cal0 = calendar_fp(m0)
# sanity: straw plant + harvest day distribution with the stagger
from collections import Counter
plants = Counter()
harv = Counter()
for t, dl in m0.CROP_DUTIES.items():
    for d, a in dl:
        if a == "PLANT:STRAWBERRY":
            plants[d] += 1
        if a == "HARVEST":
            # include only straw tiles
            if any(x == "PLANT:STRAWBERRY" for _d, x in dl):
                harv[d] += 1
print("straw plant days:", dict(sorted(plants.items())))
print("straw harvest days:", dict(sorted(harv.items())))
late = [d for d in harv if d > 28]
if late:
    raise SystemExit("ABORT: straw harvest beyond D28 (unsellable): %s" % late)

ramp = list(base_ramp)
bumps = []
blocked = set()
for it in range(80):
    m = load_author(ramp)
    if calendar_fp(m) != cal0:
        raise SystemExit("calendar drifted at iter %d" % it)
    tape = m.author()
    defs = deficits(m, tape)
    if not defs:
        break
    order = sorted(defs, key=lambda d: (-sum(defs[d].values()), -d))
    progressed = False
    for d in order:
        if d in blocked or ramp[d] >= MAX_HANDS:
            continue
        trial = list(ramp)
        trial[d] += 1
        tm = load_author(trial)
        if calendar_fp(tm) != cal0:
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

# waters may legally execute +1 day (2-day fuse, deterministic carry)
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

# ---- emit v6i ----
Q = chr(39) * 3
MARK = "TAPE = json.loads(r" + Q
new_spec = dict(SPEC)
new_spec["ramp"] = ramp
docstring = '"""v3 generated tape (tape_author3 spec %s). Pure replay."""' % json.dumps(new_spec)
head_end = champ_src.index(MARK)
head = champ_src[:head_end]
ds0 = head.index("tape_author3 spec ") + len("tape_author3 spec ")
ds1 = head.index("). Pure replay")
new_head = head[:ds0] + json.dumps(new_spec) + head[ds1:]
open_q = champ_src.index(Q, head_end + len(MARK) - len(Q))
close_q = champ_src.index(Q, open_q + 3)
tail = champ_src[close_q + 3:]
body = json.dumps(tape, separators=(",", ":"))
bot = new_head + MARK + body + Q + tail
io.open("topbots/v6i.py", "w", encoding="utf-8").write(bot)
v6i_src = io.open("topbots/v6i.py", encoding="utf-8").read()
vt = json.loads(v6i_src.split(MARK)[1].split(Q)[0])
assert vt == tape, "round-trip mismatch"
import ast
ast.parse(v6i_src)
print("v6i.py written:", os.path.getsize("topbots/v6i.py"), "bytes, parses OK")
