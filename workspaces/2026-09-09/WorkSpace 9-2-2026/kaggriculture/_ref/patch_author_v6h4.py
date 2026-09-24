"""Patch #4 (v6h2): capacity-aware straw p+12 harvest deferral + fixes.

1. Deferral pre-pass in author(): a straw tile's FIRST harvest (p+12) may
   slip to p+13/14/15 (yield persists on the tile; the p+16 final harvest
   may NOT defer - the tile dies right after). While a day's non-deferrable
   inflow + 4u per kept straw harvest + margin would pass 96, defer straw
   p+12 groups (latest-in-snake first) into the next day. Sell-independent
   (fixed estimates only) -> deterministic and stable across passes.
2. The sell planner is rebuilt INSIDE author() with the actual (deferred)
   straw arrival days, so its depth counter tracks real sales.
3. Straw yield 8 -> 4 per harvest in both the planner and the CAP inflow
   model (the 8 was 2x reality; its phantom-sales counter suppressed later
   straw sells).
4. Endgame H23 dump sells EVERYTHING (was wheat+fert only - milk/wool/straw/
   melon standing stock overflowed the shed on D28 evening).
"""
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
if "straw_moves" in src:
    raise SystemExit("patch #4 already applied")

REPL = []


def rep(old, new):
    REPL.append((old, new))


# --- 1+3: planner signature, straw arrival moves, yield 4 ---
rep('''def _build_sell_plans():
    """Returns (h00_rows, h23_rows) per day: price-aware trickle in the
    morning, pile-drain at H23, endgame dump."""''',
    '''def _build_sell_plans(straw_moves=None):
    """Returns (h00_rows, h23_rows) per day: price-aware trickle in the
    morning, pile-drain at H23, endgame dump. straw_moves maps
    (tile, planned_day) -> deferred day for capacity-deferred straw
    harvests so the arrival schedule (and the depth counter) tracks the
    tape's actual execution."""''')

rep('''    for (t, d), crop in HARVEST_CROP.items():
        if crop == "STRAWBERRY" and d < DAYS:
            prod["STRAWBERRY"][d] += 8
        elif crop == "MELON" and d < DAYS:
            prod["MELON"][d] += 5
        elif crop == "CARROT" and d < DAYS:
            prod["CARROT"][d] += 3''',
    '''    for (t, d), crop in HARVEST_CROP.items():
        if crop == "STRAWBERRY" and d < DAYS:
            _nd = (straw_moves or {}).get((t, d), d)
            prod["STRAWBERRY"][_nd] += 4
        elif crop == "MELON" and d < DAYS:
            prod["MELON"][d] += 5
        elif crop == "CARROT" and d < DAYS:
            prod["CARROT"][d] += 3''')

# --- 4: endgame H23 dumps everything ---
rep('''    if day >= DAYS - 2:
        rows += [["SELL", "WHEAT", 99]]
        if FERT_SELL_QTY[day] > 0:
            rows.append(["SELL", "FERTILIZER", 99])''',
    '''    if day >= DAYS - 2:
        # dump EVERYTHING: the EOD inventory drop discards overflow, so any
        # standing stock not sold here is at risk tonight (engine no-ops
        # sells of items not in the shed - zero-cost insurance)
        for _it in ("WHEAT", "FERTILIZER", "MILK", "WOOL", "EGG",
                    "STRAWBERRY", "MELON", "CARROT"):
            rows.append(["SELL", _it, 99])''')

# --- 2: deferral pre-pass + planner rebuild + day loop integration ---
rep('''def author():
    tape = []
    carry = []  # list of [group, age]
    stats = []
    SHED_W["lo"] = SHED_W["hi"] = 0   # ledger restarts with the empty shed
    CAP_LEDGER.clear()''',
    '''def author():
    global SELL_H00, SELL_H23
    tape = []
    carry = []  # list of [group, age]
    stats = []
    SHED_W["lo"] = SHED_W["hi"] = 0   # ledger restarts with the empty shed
    CAP_LEDGER.clear()

    # ---- v6h2: straw p+12 harvest deferral (capacity pre-pass) ----
    # The EOD inventory drop is capped at 100 total shed slots. A straw
    # tile's first harvest (p+12) may slip later (yield persists on the
    # tile); the p+16 final harvest may not (the tile dies right after).
    # While fixed inflow + 4u/kept straw + margin would pass 96, defer
    # straw p+12 groups into the next day (latest-in-snake first).
    p_day = {}
    for _t, _dl in CROP_DUTIES.items():
        for _d, _a in _dl:
            if _a == "PLANT:STRAWBERRY":
                p_day[_t] = _d
    _AF = {"SHEEP": 6, "COW": 6, "GOOSE": 4}
    _AT = {"SHEEP": 4, "COW": 3, "GOOSE": 2}
    fixed_in = [0] * DAYS
    for _d in range(DAYS):
        fixed_in[_d] += len(animals_on(_d))          # fert collects
        for (_t, _hd), _c in HARVEST_CROP.items():
            if _hd == _d and _c == "WHEAT":
                fixed_in[_d] += 4
            elif _hd == _d and _c == "MELON":
                fixed_in[_d] += 5
            elif _hd == _d and _c == "CARROT":
                fixed_in[_d] += 3
        for _tile, _kind, _pd in ANIMALS:
            _evs = animal_harvest_days(_kind, _pd)
            if _d in _evs:
                fixed_in[_d] += (_AF[_kind] if _evs.index(_d) == 0
                                 else _AT[_kind])
    day_groups = {d: day_duties(d) for d in range(DAYS)}

    def _is_deferrable_straw(g, d):
        if len(g[2]) != 1 or g[2][0][0] != "HARVEST":
            return False
        _p = p_day.get(g[1])
        if _p is None:
            return False
        return 12 <= d - _p <= 14 and d + 1 <= _p + 14

    straw_moves = {}
    _load = {}
    for _d in range(DAYS):
        _gs = day_groups[_d]
        _straw = [g for g in _gs if _is_deferrable_straw(g, _d)]
        _rest = [g for g in _gs if not _is_deferrable_straw(g, _d)]
        _over = (fixed_in[_d] + 4 * (len(_straw) + len(_load.get(_d, [])))
                 + 12 - 96)
        _i = len(_straw) - 1
        while _over > 0 and _i >= 0:
            g = _straw[_i]
            if _d + 1 <= p_day[g[1]] + 14:
                straw_moves[(g[1], _d)] = _d + 1
                _load.setdefault(_d + 1, []).append(g)
                _straw.pop(_i)
                _over -= 4
            _i -= 1
        day_groups[_d] = _rest + _straw + _load.pop(_d, [])
    if VERBOSE and straw_moves:
        print("straw deferrals:", len(straw_moves),
              "moves:", sorted(straw_moves.items()))
    # rebuild the sell plans on the ACTUAL (deferred) arrival schedule
    SELL_H00, SELL_H23 = _build_sell_plans(straw_moves)''')

rep('''    for day in range(DAYS):
        fresh = [[g, 0] for g in day_duties(day)]''',
    '''    for day in range(DAYS):
        fresh = [[g, 0] for g in day_groups[day]]''')

# --- 3b: CAP inflow model straw yield 4 ---
rep('''    for c, y in (("STRAWBERRY", 8), ("MELON", 5), ("CARROT", 3)):''',
    '''    for c, y in (("STRAWBERRY", 4), ("MELON", 5), ("CARROT", 3)):''')

for old, new in REPL:
    n = src.count(old)
    if n != 1:
        raise SystemExit("anchor x%d: %.100s" % (n, old))
    src = src.replace(old, new)

io.open(P, "w", encoding="utf-8").write(src)
ast.parse(io.open(P, encoding="utf-8").read())
print("patch #4 applied (%d replacements), syntax OK" % len(REPL))
