"""Emit topbots/v6h3.py: the LIVE champion v6h2s + runtime weed-guard.

The tape is copied VERBATIM from topbots/v6h2s.py (no author re-emit — the
author has drifted since the v6h2 emit, and one-change discipline demands
v6h3 differ from the live bot by exactly one thing). The change is a
reactive guard in the player: when a unit's row is
BUILD_PASTURE/BUILD_COOP/PLACE/PLANT and the tile under that unit is an
actual WEED at that moment, emit DIG instead and replay the original row
next hour via a per-unit queue (row order preserved => walks stay
coherent). Weed-free seeds replay v6h2s byte-identically (no lottery
re-roll, no shared-market butterfly). Weeded seeds recover the placement
(seeds-3/5 milk leak: ~$19.5k / $3.7k in solo).
"""
import ast
import io
import os

ROOT = "/home/user/WorkSpace 9-2-2026"
real = [d for d in os.listdir(ROOT)
        if os.path.isdir(os.path.join(ROOT, d))
        and os.path.isdir(os.path.join(ROOT, d, "topbots"))][0]
os.chdir(os.path.join(ROOT, real))

src = io.open("topbots/v6h2s.py", encoding="utf-8").read()

GUARD = '''

# ---- v6h3 runtime weed-guard ----
# Weeds spawn only on empty (None) tiles at EOD (p=.005/tile/day), so tiles
# scheduled for a later BUILD_PASTURE/COOP or first PLANT can be weeded when
# the tape reaches them; a blind row then fails silently (cows bought but
# never placed = the seeds-3/5 milk leak). The guard watches the tile under
# the unit at the moment a build/place/plant row fires: if it is a WEED,
# emit DIG (clears it) and replay the row next hour via a per-unit queue.
# Row order is preserved (each delayed row pushes the current tape row back)
# so walk sequences stay coherent; on weed-free seeds the guard never fires
# and the action stream is byte-identical to the v6h2 tape.
_WG = {"q": {}}
_WG_TRIG = ("BUILD_PASTURE", "BUILD_COOP", "PLACE", "PLANT")


def _wg_weed_at(farm, pos):
    try:
        tile = farm["tiles"][pos[1]][pos[0]]
        return isinstance(tile, dict) and tile.get("kind") == "WEED"
    except Exception:
        return False


def _wg_row(farm, pos, key, row):
    q = _WG["q"].get(key)
    if q:
        row, cur = q.pop(0), row
        q.append(cur)
    if (isinstance(row, list) and row and row[0] in _WG_TRIG
            and pos is not None and _wg_weed_at(farm, pos)):
        _WG["q"].setdefault(key, []).append(row)
        return ["DIG"]
    return row

'''

anchor = "def agent(obs, configuration=None):"
assert anchor in src, "agent anchor missing"
out = src.replace(anchor, GUARD + "\n" + anchor, 1)

OLD = """    rows = list(t.get('hands', []))
    if len(rows) > farm_hands:
        rows = rows[:farm_hands]
    elif len(rows) < farm_hands:
        rows = rows + [['PASS']] * (farm_hands - len(rows))"""
NEW = """    rows = list(t.get('hands', []))
    if len(rows) > farm_hands:
        rows = rows[:farm_hands]
    elif len(rows) < farm_hands:
        rows = rows + [['PASS']] * (farm_hands - len(rows))
    try:
        if step == 0:
            _WG['q'].clear()  # fresh episode: no stale replay queues
        _farm = (obs.get('farms', []) or [])[seat]
        _hpos = list(_farm.get('hands', []) or [])
        rows = [_wg_row(_farm, _hpos[i] if i < len(_hpos) else None,
                        (seat, i), r)
                for i, r in enumerate(rows)]
        _frow = _wg_row(_farm, _farm.get('farmer'), (seat, -1),
                        list(t.get('farmer', ['PASS'])))
    except Exception:
        _frow = t.get('farmer', ['PASS'])"""
assert OLD in out, "rows block missing"
out = out.replace(OLD, NEW, 1)

OLD2 = "    return {'farmer': t.get('farmer', ['PASS']), 'hands': rows,\n            'market': mk}"
NEW2 = "    return {'farmer': _frow, 'hands': rows,\n            'market': mk}"
assert OLD2 in out, "return block missing"
out = out.replace(OLD2, NEW2, 1)

io.open("topbots/v6h3.py", "w", encoding="utf-8").write(out)

final = io.open("topbots/v6h3.py", encoding="utf-8").read()
ast.parse(final)

# tape identity check
Q = chr(39) * 3
MARK = "TAPE = json.loads(r" + Q
same_tape = (final.split(MARK)[1].split(Q)[0]
             == src.split(MARK)[1].split(Q)[0])

# entrypoint check: _kaggle_submission_entrypoint must still be last
assert final.rstrip().endswith("return agent(obs, configuration)")
print("v6h3.py written:", os.path.getsize("topbots/v6h3.py"),
      "bytes; parses OK; tape verbatim from v6h2s:", same_tape)
