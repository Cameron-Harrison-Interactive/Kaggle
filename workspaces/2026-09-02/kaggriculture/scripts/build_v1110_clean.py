"""Clean build of v11.10 = v11.9 + feed rescue v2.

Splices a fresh, self-contained rescue function into v11.9's gold_floor
module (replacing the session-80 rescue v1 block), re-encodes, splices into
the file.  No in-place patching archaeology.
"""
import json
import zlib
import base64
import os

ROOT = os.path.expanduser('/home/user/WorkSpace 8-27-2026/kaggriculture')
SRC = open(os.path.join(ROOT, 'topbots/v119_FINAL.py')).read()


def decode_var(src, name):
    i = src.find(name + ' = json.loads(zlib.decompress(base64.b85decode((')
    if i < 0:
        i = src.find(name + ' = json.loads(zlib.decompress(base64.b85decode(')
    start = src.index("'", i)
    pos = start
    chunks = []
    while True:
        e = src.index("'", pos + 1)
        chunks.append(src[pos + 1:e])
        rest = src[e + 1:e + 12].lstrip('\n \t')
        if rest.startswith(')'):
            break
        if rest.startswith("'"):
            pos = e + 1 + (len(src[e + 1:e + 12]) - len(src[e + 1:e + 12].lstrip('\n \t')))
            continue
        raise RuntimeError('unexpected terminator near ' + repr(src[e:e + 30]))
    blob = ''.join(chunks)
    return json.loads(zlib.decompress(base64.b85decode(blob)).decode('utf-8'))


def blob_expr(obj):
    b85 = base64.b85encode(zlib.compress(json.dumps(obj).encode())).decode()
    return '(\n' + repr(b85) + '\n)'


RESCUE = r'''
_FEED_RESCUE_V2 = {0: {}, 1: {}}
_FR2_NOHIJACK = (
    "FEED", "CARE", "COLLECT_FERTILIZER", "HARVEST", "WATER", "PLANT",
    "BUILD_PASTURE", "BUILD_COOP", "BUILD_BARN", "BUILD_SHED",
)
_FR2_ANIMALS_ARG = ("COW", "SHEEP", "GOOSE")


def _fr2_tile(farm, position):
    try:
        x, y = int(position[0]), int(position[1])
        rows = farm.get("tiles", []) or []
        if 0 <= y < len(rows) and 0 <= x < len(rows[y]):
            return rows[y][x]
    except (TypeError, ValueError):
        pass
    return None


def _fr2_shed_acc(size):
    h = size // 2
    return {(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)}


def _fr2_wheat(inv):
    try:
        return int((inv or {}).get("WHEAT", 0) or 0)
    except (AttributeError, TypeError):
        return 0


def _apply_feed_rescue_v2(obs, result, route_name=None, routes=None):
    """Anti-starvation override v2 (wheat-aware; ep 101033101 forensics).

    Escape rule: 2 consecutive unfed days.  Rescue v1 failed in the field
    because it issued FEED without wheat in hand (no-op) and dispatched the
    nearest unit wheat-blind at H20+ — too late to fetch.  v2:
      * eligible: unfed today AND (streak>=1 from H18, streak==0 from H22)
      * stand-down: if the executing tape schedules ANY FEED within the next
        few steps, the wave is working -> no new dispatch
      * dispatch tiers (max 2/step): T0 carries wheat (d<=5, reachable);
        T1 on shed tile with shed wheat; T2 fetch-capable
        (d(unit->shed)+d(shed->animal)+2 <= hours left)
      * transaction phases fetch -> walk -> feed; FEED only when carrying
        wheat (on-shed pickup retry; one last-resort attempt if dry)
      * never hijacks FEED/CARE/COLLECT_FERTILIZER/HARVEST/WATER/PLANT/
        BUILD_*/animal PICKUP-PLACE-DROP
    """
    step = int(get(obs, "step", 0) or 0)
    hour = step % 24
    if hour < 18:
        return result
    seat = 1 if int(get(obs, "player", 0) or 0) == 1 else 0
    state = _FEED_RESCUE_V2[seat]
    if step == 0 or step < int(state.get("_last", -1)):
        state = {}
        _FEED_RESCUE_V2[seat] = state
    state["_last"] = step
    farms = list(get(obs, "farms", []) or [])
    farm = farms[seat] if seat < len(farms) else {}
    if not farm:
        return result
    rows = farm.get("tiles", []) or []
    size = len(rows)
    if size <= 0:
        return result
    private = get(obs, "private", {}) or {}
    shed_wheat = int((private.get("shed", {}) or {}).get("WHEAT", 0) or 0)
    invs = private.get("inventories", []) or []
    shed_acc = _fr2_shed_acc(size)
    starving = []
    any_streaked = False
    for y in range(size):
        for x in range(size):
            t = rows[y][x]
            if isinstance(t, dict) and t.get("animal") and not t.get("fed_today"):
                streak = int(t.get("consecutive_unfed", 0) or 0)
                if (streak >= 1 and hour >= 18) or (streak == 0 and hour >= 22):
                    starving.append((x, y))
                    if streak >= 1:
                        any_streaked = True
    if not starving:
        for k in list(state.keys()):
            if k != "_last":
                state.pop(k, None)
        return result
    positions = [farm.get("farmer")] + list(farm.get("hands", []) or [])
    units = [result.get("farmer")] + list(result.get("hands", []) or [])
    scripted = [
        (str(u[0]) if isinstance(u, list) and u else "PASS") for u in units
    ]
    changed = False

    def hijackable(idx):
        verb = scripted[idx]
        if verb in _FR2_NOHIJACK:
            return False
        if verb in ("PICKUP", "PLACE", "DROP"):
            u = units[idx]
            arg = str(u[1]) if isinstance(u, list) and len(u) > 1 else ""
            if arg in _FR2_ANIMALS_ARG:
                return False
        return True

    # ---- continue active transactions
    for actor in list(state.keys()):
        if actor == "_last":
            continue
        idx = 0 if actor == "farmer" else int(actor) + 1
        tx = state[actor]
        if (idx >= len(units) or idx >= len(positions) or positions[idx] is None
                or step - int(tx["start"]) > 12):
            state.pop(actor, None)
            continue
        px, py = int(positions[idx][0]), int(positions[idx][1])
        tile = _fr2_tile(farm, [px, py])
        still = (tx["x"], tx["y"]) in starving
        if (isinstance(tile, dict) and tile.get("animal")
                and not tile.get("fed_today")):
            if _fr2_wheat(invs[idx] if idx < len(invs) else None) > 0:
                units[idx] = ["FEED"]
                changed = True
                state.pop(actor, None)
            elif (px, py) in shed_acc and shed_wheat > 0:
                units[idx] = ["PICKUP", "WHEAT", min(4, shed_wheat)]
                changed = True
            else:
                units[idx] = ["FEED"]  # one last-resort attempt (harmless no-op)
                changed = True
                state.pop(actor, None)
            continue
        if not still:
            state.pop(actor, None)
            continue
        if tx.get("phase") == "fetch":
            sx, sy = int(tx["sx"]), int(tx["sy"])
            if (px, py) in shed_acc:
                if shed_wheat > 0:
                    units[idx] = ["PICKUP", "WHEAT", min(4, shed_wheat)]
                    changed = True
                tx["phase"] = "walk"
                continue
            if sx > px:
                units[idx] = ["EAST"]
            elif sx < px:
                units[idx] = ["WEST"]
            elif sy > py:
                units[idx] = ["SOUTH"]
            else:
                units[idx] = ["NORTH"]
            changed = True
            continue
        if tx["x"] > px:
            units[idx] = ["EAST"]
        elif tx["x"] < px:
            units[idx] = ["WEST"]
        elif tx["y"] > py:
            units[idx] = ["SOUTH"]
        else:
            units[idx] = ["NORTH"]
        changed = True

    # ---- dispatch new transactions
    active_targets = {
        (int(a["x"]), int(a["y"]))
        for a in state.values() if isinstance(a, dict) and "x" in a
    }
    # stand-down: tape schedules a FEED soon -> wave is working.  Only for
    # first-missed-day animals (streak 0): a streaked animal has already lost
    # a full day — one more miss is an escape, so it always gets dispatched.
    if not any_streaked and routes is not None and route_name in routes:
        route = routes[route_name]
        lo, hi = max(0, step - 1), min(len(route), step + 4)
        for k in range(lo, hi):
            a_k = route[k] or {}
            if any(
                isinstance(u, list) and u and u[0] == "FEED"
                for u in ([a_k.get("farmer") or []]
                          + list(a_k.get("hands", []) or []))
            ):
                if changed:
                    result = dict(result)
                    result["farmer"] = units[0]
                    result["hands"] = units[1:]
                return result
    hours_left = 24 - hour
    dispatched = 0
    for (sx, sy) in starving:
        if dispatched >= 2:
            break
        if (sx, sy) in active_targets:
            continue
        best, best_key = None, None
        for idx, p in enumerate(positions):
            if p is None or not hijackable(idx):
                continue
            actor = "farmer" if idx == 0 else str(idx - 1)
            if actor in state:
                continue
            px, py = int(p[0]), int(p[1])
            d = abs(px - sx) + abs(py - sy)
            carry = _fr2_wheat(invs[idx] if idx < len(invs) else None)
            ds = min(abs(px - ax) + abs(py - ay) for ax, ay in shed_acc)
            if carry > 0 and d <= 5 and d + 1 <= hours_left:
                key = (0, d, "walk")
            elif (px, py) in shed_acc and shed_wheat > 0 and ds + d + 2 <= hours_left + 2:
                key = (1, d, "fetch")
            elif shed_wheat > 0 and ds + d + 2 <= hours_left:
                key = (2, ds + d, "fetch")
            else:
                continue
            if best_key is None or key < best_key:
                best, best_key = idx, key
        if best is None:
            continue
        actor = "farmer" if best == 0 else str(best - 1)
        px, py = int(positions[best][0]), int(positions[best][1])
        if best_key[2] == "fetch":
            nx, ny = min(shed_acc, key=lambda s: abs(px - s[0]) + abs(py - s[1]))
            state[actor] = {"start": step, "x": sx, "y": sy,
                            "phase": "fetch", "sx": nx, "sy": ny}
        else:
            state[actor] = {"start": step, "x": sx, "y": sy, "phase": "walk"}
        dispatched += 1
        changed = True

    if changed:
        result = dict(result)
        result["farmer"] = units[0]
        result["hands"] = units[1:]
    return result
'''


modules = dict(decode_var(SRC, '_V44_MODULES'))
gf = modules['v44.gold_floor']

# --- replace the v1 rescue block (from "_FEED_RESCUE = " to "def selected_route")
i0 = gf.index("_FEED_RESCUE = {0: {}, 1: {}}")
i1 = gf.index("def selected_route(obs: Any, config: GoldFloorConfig) -> str:")
assert "def _apply_feed_rescue(obs, result):" in gf[i0:i1]
gf = gf[:i0] + RESCUE + "\n\n" + gf[i1:]

# --- replace the call site
old_call = "        result = _apply_feed_rescue(obs, result)"
assert gf.count(old_call) == 1
gf = gf.replace(old_call,
                "        result = _apply_feed_rescue_v2(obs, result, route_name, routes)")

modules['v44.gold_floor'] = gf

out = SRC
end_marker = ')).decode("utf-8"))'
i = out.index('_V44_MODULES = json.loads(zlib.decompress(base64.b85decode(')
j = out.index(end_marker, i) + len(end_marker)
out = out[:i] + '_V44_MODULES = json.loads(zlib.decompress(base64.b85decode(' + blob_expr(modules) + ')).decode("utf-8"))' + out[j:]
outpath = os.path.join(ROOT, 'topbots/v1110_nocap.py')
open(outpath, 'w').write(out)
print(f'{outpath}: {len(out)} bytes')

import importlib.util
from importlib.machinery import SourceFileLoader
loader = SourceFileLoader('v1110clean', outpath)
spec = importlib.util.spec_from_loader('v1110clean', loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
print('import OK; agent =', type(m.agent))
