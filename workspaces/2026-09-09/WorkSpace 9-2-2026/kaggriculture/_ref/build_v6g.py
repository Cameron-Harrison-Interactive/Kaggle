"""Build topbots/v6g.py — v4_fr1 spine + reactive guards (v3).

Guards:
  G1 water-rescue  — crop tiles that would die at EOD (consecutive_unwatered>=1,
                     not watered_today). Idle-hijack hands (fully idle rest of
                     day) rescue nearest targets from H16 on (or immediately
                     for tiles with no planned water today/tomorrow).
  G1b extra hand   — on days whose water plan exceeds the tape's emitted WATER
                     ops (build-time SHORT_DAYS), or with abandoned/overripe
                     targets, hire an 11th hand at H01 and drive it all day,
                     farthest-from-shed tiles first (matches drop order).
  G2 harvest-rescue— strawberry at yield cap / end-of-life, melon past window,
                     wheat/carrot overdue; idle-hijack + extra hand.
  G3 straw drain   — resize tape SELL STRAWBERRY to full live shed content;
                     append a sell at H20+ if a pile >= 10 remains.

Safety: guards only redirect PASS hand-turns or the guard-owned extra hand;
everything wrapped in try/except falling back to the pure tape action.
"""
import importlib.util
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# ---- 1. champion tape + spec ----
src = io.open("topbots/v4_fr1.py", encoding="utf-8").read()
tape_json = src.split("TAPE = json.loads(r'''")[1].split("''')")[0]
champion_spec = json.loads(
    src.split("tape_author3 spec ")[1].split("). Pure replay")[0]
)
print("spec ok:", champion_spec.get("straw_tiles"), "straw tiles,",
      champion_spec.get("hands"), "hands")

# ---- 2. author run: CROP_DUTIES -> WATER_PLAN ----
os.environ["TAPE_SPEC"] = json.dumps(champion_spec)
os.environ["TAPE_OUT"] = "/tmp/_v6g_author_out.py"
spec = importlib.util.spec_from_file_location("auth", "_ref/tape_author3.py")
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)
tape2 = auth.author()

regen_json = json.dumps(tape2, separators=(",", ":"))
print("regen byte-identical to champion:", regen_json == tape_json.strip())

tape = json.loads(tape_json)
water_plan = {}
for t, duties in auth.CROP_DUTIES.items():
    for d, act in duties:
        if act == "WATER" and 0 <= d < 30:
            water_plan.setdefault(d, []).append([t[0], t[1]])

# ---- 3. SHORT_DAYS: planned waters minus tape-emitted WATER ops ----
short_days = {}
for day in range(30):
    planned = len(water_plan.get(day, []))
    ops = 0
    for h in range(24):
        step = day * 24 + h
        acts = (tape[step].get("hands") or []) + [tape[step].get("farmer") or []]
        ops += sum(1 for a in acts if a and a[0] == "WATER")
    short_days[day] = max(0, planned - ops)
print("short days (day: shortfall):",
      {d: s for d, s in short_days.items() if s})

water_json = json.dumps(water_plan, separators=(",", ":"))
short_json = json.dumps(short_days, separators=(",", ":"))

TEMPLATE = '''"""v6g — v4_fr1 (champion) spine + reactive guards.
Reactive layer: water-rescue (+ guard-owned 11th hand), harvest-rescue,
strawberry full-drain sells. Unit guards redirect only PASS hand-turns or the
extra guard hand; any guard error falls back to the pure tape action.
"""
import json

TAPE = json.loads(r\'\'\'@@TAPE@@\'\'\')
WATER_PLAN = {int(k): v for k, v in json.loads(r"""@@WATER@@""").items()}
SHORT_DAYS = {int(k): v for k, v in json.loads(r"""@@SHORT@@""").items()}


def _tape_action(step):
    if 0 <= step < len(TAPE):
        return TAPE[step]
    return {"farmer": ["PASS"], "hands": [], "market": []}


def _hand_idle_rest_of_day(step, hi):
    """True if hand hi's tape actions from `step` to end of day are all PASS."""
    day_end = (step // 24 + 1) * 24
    s = step
    while s < day_end and s < len(TAPE):
        hs = TAPE[s].get("hands") or []
        if hi < len(hs):
            a = hs[hi]
            if not (isinstance(a, list) and len(a) == 1 and a[0] == "PASS"):
                return False
        s += 1
    return True


def _guard(action, obs, step):
    day = obs.get("day", 0)
    hour = obs.get("hour", 0)
    farms = obs.get("farms") or []
    pi = obs.get("player", 0)
    farm = farms[pi] if pi < len(farms) else (farms[0] if farms else {})
    if not farm:
        return
    tiles = farm.get("tiles") or []
    hands = farm.get("hands") or []

    # ---------- rescue targets: (x, y, op, value) ----------
    # water: crop tile dies at EOD if unwatered 2 days running
    # targets: (x, y, op, value, hijack_ok).  hijack_ok=False means only the
    # guard-owned extra hands may take it (the tape still plans to cover it,
    # or it is early in the day); idle-hijacked hands stick to sure things.
    targets = []
    planned_now = set((x, y) for x, y in WATER_PLAN.get(day, []))
    planned_next = set((x, y) for x, y in WATER_PLAN.get(min(day + 1, 29), []))
    val = {"STRAWBERRY": 3.0, "MELON": 2.0}
    overripe = False
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if not (isinstance(t, dict) and t.get("kind") == "PLANT"):
                continue
            cu = t.get("consecutive_unwatered", 0)
            risk = cu >= 1 and not t.get("watered_today")
            if risk:
                # before H16 idle-hijack only tiles the tape abandoned (no
                # water planned today or tomorrow); extra hands take all
                hij = hour >= 16 or ((x, y) not in planned_now
                                    and (x, y) not in planned_next)
                targets.append((x, y, "WATER", val.get(t.get("crop"), 1.0), hij))
            yu = t.get("yield_units", 0)
            if yu <= 0:
                continue
            crop = t.get("crop")
            age = day - t.get("planted_day", day)
            grab = False
            if crop == "STRAWBERRY":
                if yu >= 4 or (age >= 15 and yu >= 1):
                    grab = True
                    overripe = True
            elif age > 12 and yu >= 1:   # melon past window
                grab = True
            elif crop in ("WHEAT", "CARROT") and age > 4 and yu >= 1:
                grab = True
            if risk and hour >= 20 and yu >= 1:
                grab = True   # salvage stock before EOD death
            if grab:
                v = val.get(crop, 1.0) - 0.5
                if risk:
                    v = val.get(crop, 1.0) + 1.5   # dying stock: salvage now
                targets.append((x, y, "HARVEST", v, hour >= 14))

    # ---------- guard-owned extra hands ----------
    tape_n = len(action["hands"])
    farm_n = len(hands)
    n_extra = farm_n - tape_n
    extras = list(range(tape_n, farm_n)) if 1 <= n_extra <= 3 else []
    endgame = day >= 26
    stock = 0
    if endgame:
        for row in tiles:
            for t in row:
                if (isinstance(t, dict) and t.get("kind") == "PLANT"
                        and t.get("yield_units", 0) > 0):
                    stock += t["yield_units"]
    if hour == 1 and len(action["market"]) < 10 and farm.get("money", 0) >= 800:
        short = SHORT_DAYS.get(day, 0)
        money = farm.get("money", 0)
        if targets or overripe or short > 0 or stock >= 4:
            if endgame and stock >= 1:
                n = 2 if (money >= 1500
                          and len(action["market"]) <= 8) else 1
            else:
                n = 2 if (short >= 5 and money >= 1200
                          and len(action["market"]) <= 8) else 1
            for _ in range(n):
                if len(action["market"]) < 10:
                    action["market"].append(["HIRE"])

    # ---------- assign rescuers ----------
    claimed = set()
    steps_left = 24 - hour

    def _assign(pos, far_first, allow_all):
        hx, hy = pos[0], pos[1]
        best, bkey = None, None
        for ti, tt in enumerate(targets):
            if ti in claimed:
                continue
            if not allow_all and not tt[4]:
                continue
            d = abs(hx - tt[0]) + abs(hy - tt[1])
            if d + 1 > steps_left:
                continue
            op_rank = 0 if tt[2] == "WATER" else 1
            if endgame:
                op_rank = 1 - op_rank   # collect stock before anything else
            if far_first:
                # value first (straw > melon > wheat), then farthest from
                # shed (matches the tape's drop order), then nearest step
                key = (op_rank, -tt[3],
                       -(abs(4 - tt[0]) + abs(4 - tt[1])), d)
            else:
                key = (-tt[3], d)
            if bkey is None or key < bkey:
                bkey, best = key, ti
        if best is None:
            return None
        claimed.add(best)
        tx, ty, op, _p = targets[best][:4]
        d = bkey[-1]
        if d == 0:
            return [op]
        dx, dy = tx - hx, ty - hy
        if abs(dx) >= abs(dy) and dx != 0:
            return ["EAST" if dx > 0 else "WEST"]
        if dy != 0:
            return ["SOUTH" if dy > 0 else "NORTH"]
        return None

    if targets:
        for ei in extras:
            if ei < farm_n:
                mv = _assign(hands[ei], True, True)
                if mv is not None:
                    action["hands"].append(mv)
        for hi in range(min(len(action["hands"]), len(hands))):
            a = action["hands"][hi]
            if not (isinstance(a, list) and len(a) == 1 and a[0] == "PASS"):
                continue
            if not _hand_idle_rest_of_day(step, hi):
                continue
            mv = _assign(hands[hi], False, False)
            if mv is not None:
                action["hands"][hi] = mv

    # ---------- strawberry full drain ----------
    mkt = action.get("market") or []
    if mkt:
        priv = obs.get("private") or {}
        shed = priv.get("shed") or {}
        straw = shed.get("STRAWBERRY", 0)
        if straw > 0:
            done = False
            for o in mkt:
                if (isinstance(o, list) and len(o) >= 3 and o[0] == "SELL"
                        and o[1] == "STRAWBERRY"):
                    try:
                        o[2] = straw
                    except Exception:
                        pass
                    done = True
                    break
            if not done and hour >= 20 and straw >= 10 and len(mkt) < 10:
                mkt.append(["SELL", "STRAWBERRY", straw])


def agent(obs, config=None):
    step = obs.get("step", 0)
    base = _tape_action(step)
    action = {
        "farmer": list(base.get("farmer") or ["PASS"]),
        "hands": [list(h) for h in (base.get("hands") or [])],
        "market": [list(m) for m in (base.get("market") or [])],
    }
    try:
        _guard(action, obs, step)
    except Exception:
        pass
    return action
'''

bot = (TEMPLATE.replace("@@TAPE@@", tape_json)
              .replace("@@WATER@@", water_json)
              .replace("@@SHORT@@", short_json))
io.open("topbots/v6g.py", "w", encoding="utf-8").write(bot)
print("v6g written:", os.path.getsize("topbots/v6g.py"), "bytes")
print("water plan days:", len(water_plan), " total planned waters:",
      sum(len(v) for v in water_plan.values()))
