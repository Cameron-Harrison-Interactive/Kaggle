"""Patch #3: multi-item shed-capacity ledger + H23 emergency drain.

The EOD inventory drop is capped at 100 TOTAL shed slots — v6h's full
execution (52u straw days, daily milk/wool collects, wheat harvests)
overflows and discards produce. This adds an exact running per-item ledger
(standing shed stock through H00 sells -> buys -> pickups -> H04 sells ->
H23 sells) plus the day's end-of-day inventory inflow (harvest/collect/
pickup leftovers), and when standing + inflow would exceed 96 it appends
emergency H23 sells (WHEAT first — the H00 buy re-tops it — then FERTILIZER,
then products), merged into the H23 row list (<=10 orders).
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
if "CAP_LEDGER" in src:
    raise SystemExit("patch #3 already applied")

REPL = []


def rep(old, new):
    REPL.append((old, new))


# --- global capacity ledger ---
rep('''SHED_W = {"lo": 0, "hi": 0}   # lo: lower bound (buy sizing), hi: upper (sell sizing)''',
    '''SHED_W = {"lo": 0, "hi": 0}   # lo: lower bound (buy sizing), hi: upper (sell sizing)

# multi-item shed-capacity ledger: standing stock per item through the day
# (H00 sells -> buys -> pickups -> H04 sells -> H23 sells) plus the EOD
# inventory inflow; when the total would pass the shed cap the H23 drain
# sells flat-curve items first so the EOD drop never discards produce.
CAP_LEDGER = {}''')

# --- reset in author() ---
rep('''    SHED_W["lo"] = SHED_W["hi"] = 0   # ledger restarts with the empty shed''',
    '''    SHED_W["lo"] = SHED_W["hi"] = 0   # ledger restarts with the empty shed
    CAP_LEDGER.clear()''')

# --- capacity flows + emergency drain, inserted after the H01 queue assembly ---
rep('''    full_h00 = sells_h00 + h00
    overflow = full_h00[10:]
    mkt_h00 = full_h00[:10]
    mkt_h01 = overflow + h01_mkt

    pos = list(starts)''',
    '''    full_h00 = sells_h00 + h00
    overflow = full_h00[10:]
    mkt_h00 = full_h00[:10]
    mkt_h01 = overflow + h01_mkt

    # ---- capacity ledger: exact standing stock + tonight's inflow ----
    n_feed_exec = sum(1 for ch in chunks for _p, _t, acts in ch
                      for a in acts if a[0] == "FEED")
    n_fert_exec = sum(1 for ch in chunks for _p, _t, acts in ch
                      for a in acts if a[0] == "FERTILIZE")
    n_collect = sum(1 for ch in chunks for _p, _t, acts in ch
                    for a in acts if a[0] == "COLLECT_FERTILIZER")
    fert_need = sum(p[2] for pk in pickups for p in pk
                    if p[0] == "PICKUP" and p[1] == "FERTILIZER")
    crop_of = {}
    for t, dl in CROP_DUTIES.items():
        for _d2, act in dl:
            if act.startswith("PLANT:"):
                crop_of[t] = act.split(":")[1]
    harv = {}
    for ch in chunks:
        for _p, t, acts in ch:
            for a in acts:
                if a[0] == "HARVEST" and t in crop_of:
                    c = crop_of[t]
                    harv[c] = harv.get(c, 0) + 1
    inv_eod = {"WHEAT": max(0, feed_need - n_feed_exec)
               + 4 * harv.get("WHEAT", 0),
               "FERTILIZER": max(0, fert_need + n_collect - n_fert_exec)}
    for c, y in (("STRAWBERRY", 8), ("MELON", 5), ("CARROT", 3)):
        if harv.get(c):
            inv_eod[c] = y * harv[c]
    _FIRST = {"SHEEP": 6, "COW": 6, "GOOSE": 4}
    _THEN = {"SHEEP": 4, "COW": 3, "GOOSE": 2}
    for _tile, _kind, _pd in ANIMALS:
        _item = {"SHEEP": "WOOL", "COW": "MILK", "GOOSE": "EGG"}[_kind]
        _evs = animal_harvest_days(_kind, _pd)
        if day in _evs:
            inv_eod[_item] = (inv_eod.get(_item, 0)
                              + (_FIRST[_kind] if _evs.index(day) == 0
                                 else _THEN[_kind]))
    # shed flows in day order
    for o in sells_h00:
        if o[0] == "SELL":
            CAP_LEDGER[o[1]] = max(0, CAP_LEDGER.get(o[1], 0) - o[2])
    CAP_LEDGER["WHEAT"] = CAP_LEDGER.get("WHEAT", 0) + _bw
    for _kind in ("COW", "SHEEP", "GOOSE"):
        _nb = sum(o[2] for o in h00 + h01_mkt
                  if o[:2] == ["BUY_ANIMAL", _kind])
        CAP_LEDGER[_kind] = CAP_LEDGER.get(_kind, 0) + _nb
    CAP_LEDGER["WHEAT"] = max(0, CAP_LEDGER["WHEAT"] - feed_need)
    CAP_LEDGER["FERTILIZER"] = max(0, CAP_LEDGER.get("FERTILIZER", 0)
                                    - fert_need)
    for _kind in ("COW", "SHEEP", "GOOSE"):
        _np = sum(p[2] for pk in pickups for p in pk
                  if p[0] == "PICKUP" and p[1] == _kind)
        CAP_LEDGER[_kind] = max(0, CAP_LEDGER.get(_kind, 0) - _np)
    for o in sells_h01:
        if o[0] == "SELL":
            CAP_LEDGER[o[1]] = max(0, CAP_LEDGER.get(o[1], 0) - o[2])
    h23_base = sell_plan_h23(day, post_pick_hi)
    for o in h23_base:
        if o[0] == "SELL":
            CAP_LEDGER[o[1]] = max(0, CAP_LEDGER.get(o[1], 0) - o[2])
    standing = sum(v for k, v in CAP_LEDGER.items()
                   if k not in ("COW", "SHEEP", "GOOSE"))
    over = standing + sum(inv_eod.values()) - 96
    emerg = []
    if over > 0:
        for _it, _floor in (("WHEAT", 0), ("FERTILIZER", 2), ("MILK", 0),
                            ("WOOL", 0), ("EGG", 0), ("STRAWBERRY", 0),
                            ("MELON", 0), ("CARROT", 0)):
            if over <= 0:
                break
            _free = CAP_LEDGER.get(_it, 0) - _floor
            if _free <= 0:
                continue
            _q = min(_free, over)
            emerg.append(["SELL", _it, _q])
            CAP_LEDGER[_it] -= _q
            over -= _q
    # merge emergency into the H23 rows (same-item rows combine; emergency
    # first — discard prevention outranks trickle revenue)
    _merged = {}
    for o in emerg + [r for r in h23_base]:
        if o[0] == "SELL":
            _merged[o[1]] = _merged.get(o[1], 0) + o[2]
        else:
            _merged[json.dumps(o)] = o
    mkt23_rows = ([["SELL", it, q] for it, q in _merged.items()
                   if isinstance(it, str)]
                  + [v for k, v in _merged.items() if not isinstance(k, str)])
    mkt23_rows = [r if len(r) == 3 else r for r in mkt23_rows][:10]

    pos = list(starts)''')

# --- H23 row emission uses the merged rows ---
rep('''        mkt23 = sell_plan_h23(day, post_pick_hi) if h == HOURS - 1 else []''',
    '''        mkt23 = mkt23_rows if h == HOURS - 1 else []''')

# --- end-of-day: fold the inflow into the capacity ledger ---
rep('''    SHED_W["lo"] = max(0, post_pick_w - sold_w + 2 * wheat_h)
    SHED_W["hi"] = max(0, post_pick_hi - sold_w + 4 * wheat_h)''',
    '''    SHED_W["lo"] = max(0, post_pick_w - sold_w + 2 * wheat_h)
    SHED_W["hi"] = max(0, post_pick_hi - sold_w + 4 * wheat_h)
    for _it, _n in inv_eod.items():
        CAP_LEDGER[_it] = CAP_LEDGER.get(_it, 0) + _n''')

for old, new in REPL:
    n = src.count(old)
    if n != 1:
        raise SystemExit("anchor x%d: %.100s" % (n, old))
    src = src.replace(old, new)

io.open(P, "w", encoding="utf-8").write(src)
ast.parse(io.open(P, encoding="utf-8").read())
print("patch #3 applied (%d replacements), syntax OK" % len(REPL))
