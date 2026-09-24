"""Patch tape_author3.py: exact tape-grounded wheat ledger + H04 pickup window.

A) buy sizing from the day's OWN pickup plan (no model drift -> no clipped
   pickups -> no starved cows),
B) pickup window extended to H04 (late hires' 4th entry (FERT) was silently
   lost), wheat/fert sells moved to H04 (after the last pickup),
C) sell planners read the exact post-pickup shed.
Idempotent: refuses to apply if markers already present.
"""
import io
import os
import shutil

ROOT = "/home/user/WorkSpace 9-2-2026"
real = [d for d in os.listdir(ROOT)
        if os.path.isdir(os.path.join(ROOT, d))
        and os.path.isdir(os.path.join(ROOT, d, "topbots"))][0]
os.chdir(os.path.join(ROOT, real))

P = "_ref/tape_author3.py"
src = io.open(P, encoding="utf-8").read()
if "SHED_W" in src:
    raise SystemExit("already patched — aborting")
shutil.copy(P, P + ".bak_pre_v6h2")

REPL = []


def rep(old, new):
    REPL.append((old, new))


# --- R1: market_plan signature + exact buy sizing ---
rep('''def market_plan(day):
    """(h00_orders, h01_orders)"""''',
    '''def market_plan(day, feed_need=None):
    """(h00_orders, h01_orders); feed_need = today's planned WHEAT pickups
    (exact sizing against the tape-grounded SHED_W ledger when provided)"""''')

rep('''    n_animals = len(animals_on(day))
    if n_animals:
        buys.append(["BUY_PRODUCT", "WHEAT",
                     max(0, n_animals + FEED_BUFFER - WHEAT_SHED[day])])''',
    '''    n_animals = len(animals_on(day))
    if n_animals:
        _need = feed_need if feed_need is not None else n_animals
        buys.append(["BUY_PRODUCT", "WHEAT",
                     max(0, _need + FEED_BUFFER - SHED_W["wheat"])])''')

# --- R2: sell_plan_h01 ---
rep('''def sell_plan_h01(day):
    """Post-pickup sells: wheat (only the surplus above a 2-day feed
    reserve — own wheat beats buying it back at drained prices) and
    fertilizer surplus."""
    s = []
    endgame = day >= DAYS - 2
    n_an = len(animals_on(day))
    _fr = int(SPEC.get("feed_reserve", 2))
    if day < COW_DAY:
        surplus = max(0, WHEAT_SHED[day] - 4)
    else:
        surplus = max(0, WHEAT_SHED[day] - n_an * _fr)
        if surplus < 20:
            surplus = 0''',
    '''def sell_plan_h01(day, post_pickup_wheat=None):
    """Post-pickup sells: wheat (only the surplus above a 2-day feed
    reserve — own wheat beats buying it back at drained prices) and
    fertilizer surplus."""
    s = []
    endgame = day >= DAYS - 2
    n_an = len(animals_on(day))
    _fr = int(SPEC.get("feed_reserve", 2))
    _w = post_pickup_wheat if post_pickup_wheat is not None else WHEAT_SHED[day]
    if day < COW_DAY:
        surplus = max(0, _w - 4)
    else:
        surplus = max(0, _w - n_an * _fr)
        if surplus < 20:
            surplus = 0''')

# --- R3: sell_plan_h23 ---
rep('''def sell_plan_h23(day):
    """Late-day pile drain (before the EOD inventory drop). Wheat/fert have
    flat price curves — always worth a second pass."""''',
    '''def sell_plan_h23(day, post_pickup_wheat=None):
    """Late-day pile drain (before the EOD inventory drop). Wheat/fert have
    flat price curves — always worth a second pass."""''')

rep('''        if day < COW_DAY:
            surplus = max(0, WHEAT_SHED[day] - 4)
        else:
            surplus = max(0, WHEAT_SHED[day] - n_an * _fr2)
            if surplus < 20:
                surplus = 0''',
    '''        _w = (post_pickup_wheat if post_pickup_wheat is not None
              else WHEAT_SHED[day])
        if day < COW_DAY:
            surplus = max(0, _w - 4)
        else:
            surplus = max(0, _w - n_an * _fr2)
            if surplus < 20:
                surplus = 0''')

# --- R4: two-pass market plan + pickups first ---
rep('''    h00, h01_mkt = market_plan(day)
    # assemble the market queues up front: H00 = morning sells + buys (sells
    # first, funding the buys), H01 = overflow buys + hire overflow, H03 =
    # wheat/fert sells AFTER the H01-H03 pickup window (an H01 wheat sell
    # would drain the shed before the H02/H03 pickups)
    sells_h00 = sell_plan_h00(day)
    sells_h01 = sell_plan_h01(day)
    full_h00 = sells_h00 + h00
    overflow = full_h00[10:]
    mkt_h00 = full_h00[:10]
    mkt_h01 = overflow + h01_mkt
    n_late = sum(1 for o in mkt_h01 if o and o[0] == "HIRE")
    pickups = []
    for u in range(n_units):
        late = (u >= n_units - n_late) and u > 0''',
    '''    # two-pass market plan: pass 1 fixes the hire split (order COUNTS are
    # size-independent), then today's pickups are computed from the chunks
    # and pass 2 sizes the WHEAT buy from the tape's own pickup demand
    # against the exact running shed ledger — the plan buys exactly what the
    # plan will pick up (no model drift, no clipped pickups).
    _h00, _h01 = market_plan(day)
    sells_h00 = sell_plan_h00(day)
    _ovf = (sells_h00 + _h00)[10:]
    n_late = sum(1 for o in _ovf + _h01 if o and o[0] == "HIRE")
    pickups = []
    for u in range(n_units):
        late = (u >= n_units - n_late) and u > 0''')

rep('''        pickups.append(pk or [["PASS"]])

    pos = list(starts)''',
    '''        pickups.append(pk or [["PASS"]])

    feed_need = sum(p[2] for pk in pickups for p in pk
                    if p[0] == "PICKUP" and p[1] == "WHEAT")
    h00, h01_mkt = market_plan(day, feed_need)
    pre_w = SHED_W["wheat"]
    post_buy_w = pre_w + sum(o[2] for o in h00 + h01_mkt
                             if len(o) > 2 and o[0] == "BUY_PRODUCT"
                             and o[1] == "WHEAT")
    post_pick_w = post_buy_w - feed_need
    sells_h01 = sell_plan_h01(day, post_pick_w)
    # assemble the market queues: H00 = morning sells + buys (sells first,
    # funding the buys), H01 = overflow buys + hire overflow, H04 =
    # wheat/fert sells AFTER the H01-H04 pickup window
    full_h00 = sells_h00 + h00
    overflow = full_h00[10:]
    mkt_h00 = full_h00[:10]
    mkt_h01 = overflow + h01_mkt

    pos = list(starts)''')

# --- R5: pickup window to H04, sells at H04 ---
rep('''        if h <= 3:
            # pickup hours: each unit does its h-th pickup if it has one,
            # otherwise starts working; H03 also runs the wheat/fert sells
            # (after this turn's unit pickups)
            mkt = mkt_h01[:10] if h == 1 else (sells_h01 if h == 3 else [])''',
    '''        if h <= 4:
            # pickup hours: each unit does its h-th pickup if it has one,
            # otherwise starts working (H04 drains entries pushed past the
            # window by a late-hire lead PASS); H04 also runs the wheat/fert
            # sells AFTER the pickup window
            mkt = mkt_h01[:10] if h == 1 else (sells_h01 if h == 4 else [])''')

# --- R6: H23 sells get the exact shed; end-of-day ledger update ---
rep('''        mkt23 = sell_plan_h23(day) if h == HOURS - 1 else []''',
    '''        mkt23 = sell_plan_h23(day, post_pick_w) if h == HOURS - 1 else []''')

rep('''    for u in range(n_units):
        if cur[u] < len(chunks[u]):
            leftover.extend(g for g in chunks[u][cur[u]:] if is_critical(g))
    return day_rows, leftover''',
    '''    for u in range(n_units):
        if cur[u] < len(chunks[u]):
            leftover.extend(g for g in chunks[u][cur[u]:] if is_critical(g))
    # ---- exact wheat ledger into tomorrow's H00 (all terms from the plan;
    # harvests counted at a conservative 2u — leftovers recycle at EOD) ----
    _h23 = sell_plan_h23(day, post_pick_w)
    sold_w = sum(o[2] for o in sells_h01 + _h23 if o[:2] == ["SELL", "WHEAT"])
    wheat_h = sum(1 for (_t, _d), _c in HARVEST_CROP.items()
                  if _c == "WHEAT" and _d == day)
    SHED_W["wheat"] = max(0, post_pick_w - sold_w + 2 * wheat_h)
    return day_rows, leftover''')

# --- R7: SHED_W global ---
rep('''WHEAT_SHED = _wheat_ledger()''',
    '''WHEAT_SHED = _wheat_ledger()

# exact wheat ledger: what the TAPE ITSELF leaves in the shed at each H00.
# Author-time running value (reset per author() call); drift-free because
# every term comes from the emitted plan: buys, pickups, sells, and a
# conservative 2u/wheat-harvest for the EOD inventory drop.
SHED_W = {"wheat": 0}''')

# --- R8: reset in author() ---
rep('''def author():
    tape = []
    carry = []  # list of [group, age]
    stats = []''',
    '''def author():
    tape = []
    carry = []  # list of [group, age]
    stats = []
    SHED_W["wheat"] = 0   # exact ledger restarts with the empty shed''')

for old, new in REPL:
    n = src.count(old)
    if n != 1:
        raise SystemExit("anchor found %d times (need 1):\n%.120s" % (n, old))
    src = src.replace(old, new)

io.open(P, "w", encoding="utf-8").write(src)
print("patched: %d replacements" % len(REPL))
import ast
ast.parse(io.open(P, encoding="utf-8").read())
print("syntax OK")
