"""Rewrite targeting+assignment in build_v6g.py: value-first selection."""
import io
import os

base = '/home/user/WorkSpace 9-2-2026'
real = [d for d in os.listdir(base)
        if os.path.isdir(os.path.join(base, d))
        and os.path.isdir(os.path.join(base, d, 'topbots'))][0]
p = os.path.join(base, real, '_ref', 'build_v6g.py')
src = io.open(p, encoding='utf-8').read()

OLD = '''    # ---------- G1/G2: rescue targets ----------
    # A crop tile dies at EOD if unwatered two days running.  Tiles on the
    # tape's every-other-day cadence sit at cu=1 on their off day and are
    # covered by tomorrow's planned water, so before H16 we only rescue
    # tiles that are AT RISK and have NO planned water today or tomorrow
    # (i.e. the tape abandoned them).  From H16 on we rescue every
    # still-unwatered at-risk tile (catches failed planned waterings).
    targets = []
    planned_now = set((x, y) for x, y in WATER_PLAN.get(day, []))
    planned_next = set((x, y) for x, y in WATER_PLAN.get(min(day + 1, 29), []))
    val = {"STRAWBERRY": 3, "MELON": 2}
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if not (isinstance(t, dict) and t.get("kind") == "PLANT"):
                continue
            cu = t.get("consecutive_unwatered", 0)
            if cu >= 1 and not t.get("watered_today"):
                if hour >= 16 or ((x, y) not in planned_now
                                  and (x, y) not in planned_next):
                    v = val.get(t.get("crop"), 1)
                    targets.append((x, y, "WATER", -v))
    if hour >= 14:
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                if not (isinstance(t, dict) and t.get("kind") == "PLANT"):
                    continue
                yu = t.get("yield_units", 0)
                if yu <= 0:
                    continue
                crop = t.get("crop")
                age = day - t.get("planted_day", day)
                grab = False
                if crop == "STRAWBERRY":
                    if yu >= 4 or (age >= 15 and yu >= 1):
                        grab = True
                elif age > 12 and yu >= 1:   # melon past window
                    grab = True
                elif crop in ("WHEAT", "CARROT") and age > 4 and yu >= 1:
                    grab = True
                if grab:
                    targets.append((x, y, "HARVEST", -val.get(crop, 1)))
    # water before harvest; high-value crops first within each kind
    targets.sort(key=lambda z: (1 if z[3] >= 0 else 0, z[3]))
'''

NEW = '''    # ---------- G1/G2: rescue targets ----------
    # A crop tile dies at EOD if unwatered two days running.  Tiles on the
    # tape's every-other-day cadence sit at cu=1 on their off day and are
    # covered by tomorrow's planned water, so before H16 we only rescue
    # tiles that are AT RISK and have NO planned water today or tomorrow
    # (i.e. the tape abandoned them).  From H16 on we rescue every
    # still-unwatered at-risk tile (catches failed planned waterings).
    targets = []   # (x, y, op, score)
    planned_now = set((x, y) for x, y in WATER_PLAN.get(day, []))
    planned_next = set((x, y) for x, y in WATER_PLAN.get(min(day + 1, 29), []))
    val = {"STRAWBERRY": 3.0, "MELON": 2.0}
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if not (isinstance(t, dict) and t.get("kind") == "PLANT"):
                continue
            cu = t.get("consecutive_unwatered", 0)
            if cu >= 1 and not t.get("watered_today"):
                if hour >= 16 or ((x, y) not in planned_now
                                  and (x, y) not in planned_next):
                    targets.append((x, y, "WATER", val.get(t.get("crop"), 1.0)))
    if hour >= 14:
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                if not (isinstance(t, dict) and t.get("kind") == "PLANT"):
                    continue
                yu = t.get("yield_units", 0)
                if yu <= 0:
                    continue
                crop = t.get("crop")
                age = day - t.get("planted_day", day)
                grab = False
                if crop == "STRAWBERRY":
                    if yu >= 4 or (age >= 15 and yu >= 1):
                        grab = True
                elif age > 12 and yu >= 1:   # melon past window
                    grab = True
                elif crop in ("WHEAT", "CARROT") and age > 4 and yu >= 1:
                    grab = True
                if grab:
                    targets.append((x, y, "HARVEST",
                                    val.get(crop, 1.0) - 0.5))
'''

assert src.count(OLD) == 1, f'count={src.count(OLD)}'
src = src.replace(OLD, NEW)

OLD2 = '''    def _assign(hi, pos, relax):
        hx, hy = pos[0], pos[1]
        best, bd = None, 99
        for ti, tt in enumerate(targets):
            if ti in claimed:
                continue
            d = abs(hx - tt[0]) + abs(hy - tt[1])
            if d < bd:
                bd, best = d, ti
        if best is None:
            return None
        tx, ty, op, _p = targets[best]
'''
NEW2 = '''    def _assign(hi, pos, relax):
        hx, hy = pos[0], pos[1]
        best, bkey = None, None
        for ti, tt in enumerate(targets):
            if ti in claimed:
                continue
            d = abs(hx - tt[0]) + abs(hy - tt[1])
            key = (-tt[3], d)
            if bkey is None or key < bkey:
                bkey, best = key, ti
        if best is None:
            return None
        bd = bkey[1]
        tx, ty, op, _p = targets[best]
'''
assert src.count(OLD2) == 1, f'count2={src.count(OLD2)}'
src = src.replace(OLD2, NEW2)

io.open(p, 'w', encoding='utf-8').write(src)
print('targeting + assignment rewritten')
