"""Patch #5 (v6i): all animal-tile groups become critical (spec knob
animal_critical, default on for new builds). FEED/PLACE/BUILD already were;
CARE / COLLECT_FERTILIZER / animal HARVEST were silently droppable under
load — a map-first violation and the direct cause of milk-collect losses
when the staggered straw waves densify D20-27."""
import ast
import io
import os

ROOT = "/home/user/WorkSpace 9-2-2026"
real = [d for d in os.listdir(ROOT)
        if os.path.isdir(os.path.join(ROOT, d))
        and os.path.isdir(os.path.join(ROOT, d, "topbots"))][0]
os.chdir(os.path.join(ROOT, real))

P = "_ref/tape_author3.py"
src = io.open(P, encoding="utf-8").read()
if "ANIMAL_TILE_SET" in src:
    raise SystemExit("patch #5 already applied")

REPL = []


def rep(old, new):
    REPL.append((old, new))


# animal tile set global
rep('''SHED_W = {"lo": 0, "hi": 0}   # lo: lower bound (buy sizing), hi: upper (sell sizing)''',
    '''SHED_W = {"lo": 0, "hi": 0}   # lo: lower bound (buy sizing), hi: upper (sell sizing)

# every duty on an animal tile is critical when animal_critical is set:
# FEED/PLACE/BUILD always were; CARE / COLLECT_FERTILIZER / animal HARVEST
# must never be silently dropped either (care bonus + milk/wool collects).
ANIMAL_TILE_SET = frozenset(t for t, _k, _pd in ANIMALS)''')

# is_critical in build_day2
rep('''    def is_critical(g):
        if any(a[0] in ("FEED", "PLACE", "BUILD") for a in g[2]):
            return True
        return (_WC and g[1] in STRAW_SET
                and any(a[0] == "WATER" for a in g[2]))''',
    '''    _AC = SPEC.get("animal_critical", 1)

    def is_critical(g):
        if any(a[0] in ("FEED", "PLACE", "BUILD") for a in g[2]):
            return True
        if _AC and g[1] in ANIMAL_TILE_SET:
            return True
        return (_WC and g[1] in STRAW_SET
                and any(a[0] == "WATER" for a in g[2]))''')

# carry-drop critical check in author()
rep('''            critical = (any(a[0] in ("FEED", "PLACE", "BUILD") for a in g[2])
                        or (SPEC.get("water_critical", 0) and g[1] in STRAW_SET
                            and any(a[0] == "WATER" for a in g[2])))''',
    '''            critical = (any(a[0] in ("FEED", "PLACE", "BUILD") for a in g[2])
                        or (SPEC.get("animal_critical", 1)
                            and g[1] in ANIMAL_TILE_SET)
                        or (SPEC.get("water_critical", 0) and g[1] in STRAW_SET
                            and any(a[0] == "WATER" for a in g[2])))''')

for old, new in REPL:
    n = src.count(old)
    if n != 1:
        raise SystemExit("anchor x%d: %.100s" % (n, old))
    src = src.replace(old, new)

io.open(P, "w", encoding="utf-8").write(src)
ast.parse(io.open(P, encoding="utf-8").read())
print("patch #5 applied (%d replacements), syntax OK" % len(REPL))
