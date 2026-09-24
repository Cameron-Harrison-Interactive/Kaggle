"""Patch #6 (v6i): two-pass author — the sell planner reads the tape's
ACTUAL executed harvest days instead of the planned calendar.

Runtime capacity carries shift harvests +1 day; the planner's arrival
model (and its depth counter k) drifted, throttling mid-season sells and
floor-dumping the surplus at the endgame. Pass 1 records every executed
HARVEST (tile, day); the actual per-item arrival schedule feeds
_build_sell_plans; pass 2 rebuilds the tape with truthful sells (unit rows
are identical — sells never affect unit actions)."""
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
if "HARVEST_LOG" in src:
    raise SystemExit("patch #6 already applied")

REPL = []


def rep(old, new):
    REPL.append((old, new))


# --- A: globals ---
rep('''ANIMAL_TILE_SET = frozenset(t for t, _k, _pd in ANIMALS)''',
    '''ANIMAL_TILE_SET = frozenset(t for t, _k, _pd in ANIMALS)

# executed HARVEST ops (tile, day) recorded during tape emission; pass 2
# rebuilds the sell plans from this ground truth.
HARVEST_LOG = []''')

# --- B: record executed harvests in work_row ---
rep('''        if pos[u] == tile:
            a = list(acts[sub[u]])
            if a[0] == "BUILD":
                a = [STRUCT[a[1]]]
            row = a
            sub[u] += 1''',
    '''        if pos[u] == tile:
            a = list(acts[sub[u]])
            if a[0] == "BUILD":
                a = [STRUCT[a[1]]]
            row = a
            if a[0] == "HARVEST":
                HARVEST_LOG.append((tile, day))
            sub[u] += 1''')

# --- C: planner accepts a prod override ---
rep('''def _build_sell_plans(straw_moves=None):''',
    '''def _build_sell_plans(straw_moves=None, prod_override=None):''')

rep('''    _FIRST = {"SHEEP": 6, "COW": 6, "GOOSE": 4}
    _THEN = {"SHEEP": 4, "COW": 3, "GOOSE": 2}
    prod = {it: [0] * DAYS for it in ("WOOL", "MILK", "EGG",
                                      "STRAWBERRY", "MELON", "CARROT")}
    for tile, kind, pd in ANIMALS:
        item = {"SHEEP": "WOOL", "COW": "MILK", "GOOSE": "EGG"}[kind]
        evs = animal_harvest_days(kind, pd)
        for i, ev in enumerate(evs):
            if ev < DAYS:
                prod[item][ev] += _FIRST[kind] if i == 0 else _THEN[kind]
    for (t, d), crop in HARVEST_CROP.items():
        if crop == "STRAWBERRY" and d < DAYS:
            _nd = (straw_moves or {}).get((t, d), d)
            prod["STRAWBERRY"][_nd] += 4
        elif crop == "MELON" and d < DAYS:
            prod["MELON"][d] += 5
        elif crop == "CARROT" and d < DAYS:
            prod["CARROT"][d] += 3''',
    '''    _FIRST = {"SHEEP": 6, "COW": 6, "GOOSE": 4}
    _THEN = {"SHEEP": 4, "COW": 3, "GOOSE": 2}
    prod = {it: [0] * DAYS for it in ("WOOL", "MILK", "EGG",
                                      "STRAWBERRY", "MELON", "CARROT")}
    if prod_override is not None:
        # ground truth: the tape's own executed harvest days
        for it in prod:
            prod[it] = list(prod_override.get(it, [0] * DAYS))
    else:
        for tile, kind, pd in ANIMALS:
            item = {"SHEEP": "WOOL", "COW": "MILK", "GOOSE": "EGG"}[kind]
            evs = animal_harvest_days(kind, pd)
            for i, ev in enumerate(evs):
                if ev < DAYS:
                    prod[item][ev] += _FIRST[kind] if i == 0 else _THEN[kind]
        for (t, d), crop in HARVEST_CROP.items():
            if crop == "STRAWBERRY" and d < DAYS:
                _nd = (straw_moves or {}).get((t, d), d)
                prod["STRAWBERRY"][_nd] += 4
            elif crop == "MELON" and d < DAYS:
                prod["MELON"][d] += 5
            elif crop == "CARROT" and d < DAYS:
                prod["CARROT"][d] += 3''')

# --- D: two-pass author ---
rep('''    if VERBOSE and straw_moves:
        print("straw deferrals:", len(straw_moves),
              "moves:", sorted(straw_moves.items()))
    # rebuild the sell plans on the ACTUAL (deferred) arrival schedule
    SELL_H00, SELL_H23 = _build_sell_plans(straw_moves)

    def snake_key(e):
        _p, (x, y), _a = e
        return (x, y if x % 2 == 0 else -y)

    for day in range(DAYS):
        fresh = [[g, 0] for g in day_groups[day]]
        merged = carry + fresh
        # re-sort everything into the spatial snake (carried groups keep their
        # spatial slot — no scatter)
        merged.sort(key=lambda ga: snake_key(ga[0]))
        groups = [g for g, _age in merged]
        rows, leftover = build_day2(day, groups)
        tape.extend(rows)
        # age the leftovers; drop stale (>=2 days) non-critical groups
        age_of = {id(g): a for g, a in merged}
        new_carry = []
        n_drop = 0
        for g in leftover:
            age = age_of.get(id(g), 0) + 1
            critical = (any(a[0] in ("FEED", "PLACE", "BUILD") for a in g[2])
                        or (SPEC.get("animal_critical", 1)
                            and g[1] in ANIMAL_TILE_SET)
                        or (SPEC.get("water_critical", 0) and g[1] in STRAW_SET
                            and any(a[0] == "WATER" for a in g[2])))
            if age >= 2 and not critical:
                n_drop += 1
                continue
            new_carry.append([g, age])
        carry = new_carry
        if leftover:
            stats.append((day, len(leftover), n_drop))
    if VERBOSE and stats:
        print("carry-over (day, left, dropped):", stats[:14],
              "total-left", sum(s[1] for s in stats))
    return tape''',
    '''    if VERBOSE and straw_moves:
        print("straw deferrals:", len(straw_moves),
              "moves:", sorted(straw_moves.items()))
    # pass-1 sell plans: best static estimate (deferred arrivals)
    SELL_H00, SELL_H23 = _build_sell_plans(straw_moves)

    def snake_key(e):
        _p, (x, y), _a = e
        return (x, y if x % 2 == 0 else -y)

    def _run_days():
        tape = []
        carry = []  # list of [group, age]
        stats = []
        SHED_W["lo"] = SHED_W["hi"] = 0
        CAP_LEDGER.clear()
        del HARVEST_LOG[:]
        for day in range(DAYS):
            fresh = [[g, 0] for g in day_groups[day]]
            merged = carry + fresh
            # re-sort everything into the spatial snake (carried groups keep
            # their spatial slot — no scatter)
            merged.sort(key=lambda ga: snake_key(ga[0]))
            groups = [g for g, _age in merged]
            rows, leftover = build_day2(day, groups)
            tape.extend(rows)
            # age the leftovers; drop stale (>=2 days) non-critical groups
            age_of = {id(g): a for g, a in merged}
            new_carry = []
            n_drop = 0
            for g in leftover:
                age = age_of.get(id(g), 0) + 1
                critical = (any(a[0] in ("FEED", "PLACE", "BUILD")
                                for a in g[2])
                            or (SPEC.get("animal_critical", 1)
                                and g[1] in ANIMAL_TILE_SET)
                            or (SPEC.get("water_critical", 0)
                                and g[1] in STRAW_SET
                                and any(a[0] == "WATER" for a in g[2])))
                if age >= 2 and not critical:
                    n_drop += 1
                    continue
                new_carry.append([g, age])
            carry = new_carry
            if leftover:
                stats.append((day, len(leftover), n_drop))
        return tape, stats

    # pass 1: emit with estimated sells, recording actual harvest days
    tape, stats = _run_days()

    # ground-truth arrival schedule from the tape's own execution
    def _actual_prod():
        crop_of = {}
        for t, dl in CROP_DUTIES.items():
            for _d2, act in dl:
                if act.startswith("PLANT:"):
                    crop_of[t] = act.split(":")[1]
        _YLDC = {"STRAWBERRY": 4, "MELON": 5, "CARROT": 3}
        prod = {it: [0] * DAYS for it in ("WOOL", "MILK", "EGG",
                                          "STRAWBERRY", "MELON", "CARROT")}
        animal_of = {t: k for t, k, _pd in ANIMALS}
        seen = {}
        for tile, d in list(HARVEST_LOG):
            if d >= DAYS:
                continue
            if tile in animal_of:
                kind = animal_of[tile]
                item = {"SHEEP": "WOOL", "COW": "MILK",
                        "GOOSE": "EGG"}[kind]
                i = seen.get(tile, 0)
                prod[item][d] += (6 if i == 0
                                  else _THEN_REF[kind])
                seen[tile] = i + 1
            elif tile in crop_of and crop_of[tile] in _YLDC:
                prod[crop_of[tile]][d] += _YLDC[crop_of[tile]]
        return prod

    _THEN_REF = {"SHEEP": 4, "COW": 3, "GOOSE": 2}
    actual = _actual_prod()
    if VERBOSE:
        print("actual arrivals (pass1):",
              {it: [(d, n) for d, n in enumerate(v) if n]
               for it, v in actual.items() if any(v)})
    # pass 2: identical unit rows, sell plans rebuilt on ground truth
    SELL_H00, SELL_H23 = _build_sell_plans(None, prod_override=actual)
    tape, stats = _run_days()
    if VERBOSE and stats:
        print("carry-over (day, left, dropped):", stats[:14],
              "total-left", sum(s[1] for s in stats))
    return tape''')

for old, new in REPL:
    n = src.count(old)
    if n != 1:
        raise SystemExit("anchor x%d: %.100s" % (n, old))
    src = src.replace(old, new)

io.open(P, "w", encoding="utf-8").write(src)
ast.parse(io.open(P, encoding="utf-8").read())
print("patch #6 applied (%d replacements), syntax OK" % len(REPL))
