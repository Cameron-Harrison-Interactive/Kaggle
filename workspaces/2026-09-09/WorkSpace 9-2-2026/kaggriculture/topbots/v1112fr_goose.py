"""v1112fr_goose v3 — v1112fr + reactive goose overlay.  **VERDICT: NET-NEGATIVE.**

Mechanically complete (coops built D11, geese bought/placed/fed/cared,
eggs+fert sold; wrapper proven +0.000 vs baseline in isolation).  Economics:
-8-seed solo avg -23.5k vs v1112fr.  Decomposed (see SESSION_NOTES_0902b):
  * wrapper overhead:        +0     (proven, 6 seeds exact)
  * 2 extra PASS hands/day: -13.1k  (fib fees ~7k + spawn-tile shift breaks
                             their tapes' authored walk trajectories ~6k;
                             deterministic across seeds)
  * land+geese+wheat+shed:  ~-10k   (SE $4k inside their D11-D16 wheat-carry
                             accumulation window; shed slots at their 98/100
                             peak; their carry sells collapsed 3067->2428)
  * goose revenue:          +2.5k   (eggs+fert, 4-6 geese placed)
Structural: the host runs shed/cash/labor/spawn at ~100% utilization with
zero slack; geese displace higher-yielding uses.  Their config vetoes
(maximum_geese: 0) are deliberate tuning, not oversight.  Kept as the
reference implementation + engine-mechanics documentation.
"""

import os
import importlib.util

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "_v1112fr_goose_base", os.path.join(_HERE, "v1112fr.py")
)
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
_base_agent = _base.agent

# ------------------------------------------------------------------ knobs
N_GEESE = 10
COOP_SITES = [
    (5, 5), (6, 5), (7, 5), (8, 5),
    (5, 6), (6, 6), (7, 6), (8, 6),
    (5, 7), (6, 7), (7, 7), (8, 7),
][:N_GEESE]
N_HANDS = 2
LAND_DAY = 11
LAND_CASH = 8500
GOOSE_START_DAY = 11
GOOSE_END_DAY = 14
GOOSE_CASH = 4500
HIRE_HOUR = 3
SELL_HOUR = 20
WIND_DOWN_DAY = 29
SHED_ACC = {(4, 4), (5, 4), (4, 5), (5, 5)}

_GS = {"last_step": -1}


def _reset():
    return {
        "last_step": -1,
        "land": None,
        "land_day": -1,
        "hire_day": -1,
        "pre_hire_count": -1,
        "wheat_bought_today": 0,
    }


def _step_toward(pos, target):
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    if abs(dx) >= abs(dy) and dx != 0:
        return ["EAST"] if dx > 0 else ["WEST"]
    if dy != 0:
        return ["SOUTH"] if dy > 0 else ["NORTH"]
    return ["PASS"]


def _tile_at(farm, x, y):
    try:
        return farm["tiles"][y][x]
    except Exception:
        return None


def _goose_overlay(obs, action):
    step = int(obs.get("step", 0) or 0)
    if step <= _GS.get("last_step", -1) or "land" not in _GS:
        _GS.clear()
        _GS.update(_reset())
    if step // 24 != _GS["last_step"] // 24:
        _GS["wheat_bought_today"] = 0
    _GS["last_step"] = step

    day = step // 24
    hour = step % 24
    seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
    farms = obs.get("farms", []) or []
    if seat >= len(farms):
        return
    farm = farms[seat] or {}
    private = obs.get("private", {}) or {}
    shed = private.get("shed", {}) or {}
    money = float(farm.get("money", 0) or 0)
    unlocked = farm.get("unlocked_quadrants", []) or []
    market = action.get("market")
    if not isinstance(market, list):
        market = []
        action["market"] = market
    hands_pos = list(farm.get("hands", []) or [])
    hands_act = action.get("hands")
    if not isinstance(hands_act, list):
        hands_act = []
        action["hands"] = hands_act
    invs = private.get("inventories", []) or []
    wind_down = day >= WIND_DOWN_DAY

    # ---------------------------------------------------------------- land
    if _GS["land"] == "done":
        pass
    elif _GS["land"] == "ordered":
        if "SE" in unlocked:
            _GS["land"] = "done"
        elif day >= _GS["land_day"] + 2:
            _GS["land"] = None
    if (
        _GS["land"] is None
        and day >= LAND_DAY
        and 1 <= hour <= 20
        and len(unlocked) >= 3
        and "SE" not in unlocked
        and money >= LAND_CASH
        and len(market) < 8
    ):
        market.append(["BUY_LAND"])
        _GS["land"] = "ordered"
        _GS["land_day"] = day
        return

    if _GS["land"] != "done":
        return

    # ------------------------------------------------------- board reading
    builds, goose_coops, empty_coops = [], [], []
    for (x, y) in COOP_SITES:
        t = _tile_at(farm, x, y)
        if t is None or (isinstance(t, dict) and t.get("kind") == "WEED"):
            builds.append((x, y))
        elif isinstance(t, dict) and t.get("animal") == "GOOSE":
            goose_coops.append(((x, y), t))
        elif isinstance(t, dict) and t.get("kind") == "COOP" and "animal" not in t:
            empty_coops.append((x, y))

    shed_geese = int(shed.get("GOOSE", 0) or 0)
    owned = len(goose_coops) + shed_geese
    shed_wheat = int(shed.get("WHEAT", 0) or 0)

    # ------------------------------------------------------------- market
    if (
        day <= 28
        and hour == HIRE_HOUR
        and _GS["hire_day"] != day
        and money >= 900
        and len(market) < 8
    ):
        for _ in range(N_HANDS):
            market.append(["HIRE"])
        _GS["hire_day"] = day
        _GS["pre_hire_count"] = len(hands_pos)

    if (
        GOOSE_START_DAY <= day <= GOOSE_END_DAY
        and 4 <= hour <= 9
        and owned < N_GEESE
        and _GS.get("geese_day") != day
        and money - 600 >= GOOSE_CASH
        and len(market) < 9
        and sum(int(v or 0) for v in shed.values()) <= 88
    ):
        n = min(2, N_GEESE - owned)
        market.append(["BUY_ANIMAL", "GOOSE", n])
        _GS["geese_day"] = day
        money -= 300 * n

    # belt-neutral wheat: replace what the geese eat today (skip wind-down)
    eat_today = 0 if wind_down else len(goose_coops)
    if (
        not wind_down
        and eat_today > 0
        and hour == 4
        and _GS["wheat_bought_today"] < eat_today
        and shed_wheat + eat_today <= 45
        and money >= eat_today * 60
        and len(market) < 9
    ):
        market.append(["BUY_PRODUCT", "WHEAT", eat_today])
        _GS["wheat_bought_today"] = eat_today

    if hour >= SELL_HOUR and len(market) < 9:
        eggs = int(shed.get("EGG", 0) or 0)
        if eggs >= 4:
            market.append(["SELL", "EGG", eggs])
        fert = int(shed.get("FERTILIZER", 0) or 0)
        if fert >= 15:
            market.append(["SELL", "FERTILIZER", fert])

    # ------------------------------------------------------ unit driving
    n_hands = min(len(hands_pos), len(hands_act))
    sites = [s for (s, _t) in goose_coops]
    need_feed = [s for (s, t) in goose_coops if not t.get("fed_today")]
    need_colf = [s for (s, t) in goose_coops if t.get("fertilizer_available")]
    need_care = [
        s
        for (s, t) in goose_coops
        if not t.get("cared_today") and t.get("fed_today")
    ]
    need_harv = [
        s
        for (s, t) in goose_coops
        if int(t.get("yield_units", 0) or 0) >= 3
        or (int(t.get("yield_units", 0) or 0) >= 1 and hour >= 21)
    ]
    behind = bool(need_feed) and hour >= 17

    def nearest(site_list, pos):
        if not site_list:
            return None
        cands = [s for s in site_list if s != (pos[0], pos[1])]
        if not cands:
            return None
        return min(cands, key=lambda s: abs(s[0] - pos[0]) + abs(s[1] - pos[1]))

    def unit_action(idx, feed_only):
        pos = hands_pos[idx]
        px, py = int(pos[0]), int(pos[1])
        raw_inv = invs[idx + 1] if idx + 1 < len(invs) else {}
        inv = dict(raw_inv or {})
        carry_wheat = int(inv.get("WHEAT", 0) or 0)
        carry_goose = int(inv.get("GOOSE", 0) or 0)
        carry_out = int(inv.get("EGG", 0) or 0) + int(inv.get("FERTILIZER", 0) or 0)
        here = (px, py)
        tile = _tile_at(farm, px, py)
        on_empty_coop = (
            isinstance(tile, dict)
            and tile.get("kind") == "COOP"
            and "animal" not in tile
        )
        on_goose = isinstance(tile, dict) and tile.get("animal") == "GOOSE"

        def walk(tgt):
            if tgt is None:
                return None
            return _step_toward(here, tgt)

        # ---------------- wind-down (D29+): harvest & deposit only ----------
        if wind_down:
            if carry_out > 0 or carry_wheat > 0 or carry_goose > 0:
                if here in SHED_ACC:
                    return ["DROP"]
                return walk((4, 4))
            if on_goose:
                if int(tile.get("yield_units", 0) or 0) >= 2:
                    return ["HARVEST"]
                if tile.get("fertilizer_available"):
                    return ["COLLECT_FERTILIZER"]
            tgt = nearest(
                [s for (s, t) in goose_coops
                 if int(t.get("yield_units", 0) or 0) >= 2], here)
            return walk(tgt)

        # ---------------- PLACE mission (carrying geese: place them) --------
        if carry_goose > 0:
            if on_empty_coop:
                return ["PLACE", "GOOSE"]
            tgt = nearest(empty_coops, here)
            if tgt is not None:
                return walk(tgt)
            # nowhere to place: park them back at the shed
            if here in SHED_ACC:
                return ["DROP"]
            return walk((4, 4))

        # ---------------- FEED mission --------------------------------------
        if need_feed:
            if on_goose and not tile.get("fed_today") and carry_wheat > 0:
                return ["FEED"]
            if carry_wheat > 0:
                return walk(nearest(need_feed, here))
            if here in SHED_ACC and shed_wheat > 4:
                return ["PICKUP", "WHEAT", min(max(len(need_feed), 4), shed_wheat - 4)]
            if shed_wheat > 4:
                return walk((4, 4))
            # no wheat anywhere: fall through to tour duties

        # ---------------- FETCH geese mission (one hand at a time) ----------
        others_placing = any(
            int(dict(invs[j + 1] or {}).get("GOOSE", 0) or 0) > 0
            for j in range(n_hands)
            if j != idx and j + 1 < len(invs)
        )
        if (
            not feed_only
            and not others_placing
            and shed_geese > 0
            and empty_coops
            and hour <= 17
            and not behind
        ):
            if here in SHED_ACC:
                take = min(shed_geese, len(empty_coops))
                return ["PICKUP", "GOOSE", take]
            return walk((4, 4))

        # ---------------- TOUR mission (colfert > harvest > care) -----------
        if feed_only:
            return None
        if on_goose:
            if tile.get("fertilizer_available"):
                return ["COLLECT_FERTILIZER"]
            if int(tile.get("yield_units", 0) or 0) >= 3 or (
                int(tile.get("yield_units", 0) or 0) >= 1 and hour >= 21
            ):
                return ["HARVEST"]
            if not tile.get("cared_today") and tile.get("fed_today"):
                return ["CARE"]
        if need_colf:
            return walk(nearest(need_colf, here))
        if need_harv:
            return walk(nearest(need_harv, here))
        if need_care:
            return walk(nearest(need_care, here))

        # ---------------- BUILD mission -------------------------------------
        if builds and shed_geese == 0:
            if here in COOP_SITES and tile is None:
                return ["BUILD_COOP"]
            if here in COOP_SITES and isinstance(tile, dict) and tile.get("kind") == "WEED":
                return ["DIG"]
            return walk(nearest(builds, here))

        # ---------------- deposit / idle ------------------------------------
        if carry_out > 0 and here in SHED_ACC:
            return ["DROP"]
        if (carry_out > 0 or carry_wheat > 0) and not need_feed:
            return walk((4, 4))
        return None

    # our hands: the last N_HANDS indices, only while PASS
    if _GS["hire_day"] == day and _GS["pre_hire_count"] >= 0:
        expected = _GS["pre_hire_count"] + N_HANDS
        if n_hands >= expected:
            for idx in range(expected - 1, _GS["pre_hire_count"] - 1, -1):
                if hands_act[idx] != ["PASS"]:
                    continue
                raw_inv = invs[idx + 1] if idx + 1 < len(invs) else {}
                has_wheat = int(dict(raw_inv or {}).get("WHEAT", 0) or 0) > 0
                act = unit_action(idx, feed_only=False)
                if act:
                    hands_act[idx] = act
                    # a wheat-carrying walker is on the FEED mission: claim its target
                    if act[0] in ("EAST", "WEST", "NORTH", "SOUTH") and has_wheat and need_feed:
                        tgt = nearest(need_feed, (int(hands_pos[idx][0]), int(hands_pos[idx][1])))
                        if tgt in need_feed:
                            need_feed.remove(tgt)


    # backup feeders H19-21 when behind
    if 19 <= hour <= 21 and need_feed and not wind_down:
        mine = set()
        if _GS["hire_day"] == day and _GS["pre_hire_count"] >= 0:
            mine = set(range(_GS["pre_hire_count"], _GS["pre_hire_count"] + N_HANDS))
        for idx in range(n_hands - 1, -1, -1):
            if idx in mine or hands_act[idx] != ["PASS"]:
                continue
            if not need_feed:
                break
            act = unit_action(idx, feed_only=True)
            if act:
                hands_act[idx] = act
                tgt = nearest(need_feed, (int(hands_pos[idx][0]), int(hands_pos[idx][1])))
                if tgt in need_feed:
                    need_feed.remove(tgt)


def agent(obs, configuration=None):
    action = _base_agent(obs, configuration)
    try:
        if isinstance(action, dict):
            _goose_overlay(obs, action)
    except Exception:
        pass
    return action
