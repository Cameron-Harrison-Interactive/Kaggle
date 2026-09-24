# Test opponent: the "full side of cows" build that beat us live.
# Buys cows to 12, feeds/cares/milks them, wheat filler for feed.
def _move(pos, target):
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    if abs(dx) >= abs(dy):
        return ["EAST"] if dx > 0 else ["WEST"]
    return ["SOUTH"] if dy > 0 else ["NORTH"]


def agent(obs):
    try:
        player = obs.get("player", 0)
        farms = obs.get("farms", []) or []
        if not farms or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        farm = farms[player]
        private = obs.get("private", {}) or {}
        day = obs.get("day", 0)
        shed = private.get("shed", {}) or {}
        seeds = private.get("seeds", {}) or {}
        cash = float(farm.get("money", 0) or 0)
        tiles = farm.get("tiles", [])
        hands = farm.get("hands") or []
        farmer = farm.get("farmer")
        units = ([farmer] if farmer else []) + hands
        invs = private.get("inventories") or [{}]
        SHED_T = [(4, 4), (5, 4), (4, 5), (5, 5)]

        market = []
        # hire 8/day flat
        if day < 28:
            for _ in range(max(0, 8 - (farm.get("hires_today", 0) or 0))):
                market.append(["HIRE"])
        # cows to 12
        cows = sum(1 for row in tiles for t in row
                   if isinstance(t, dict) and t.get("animal") == "COW")
        if cows + shed.get("COW", 0) < 12 and day <= 18 and cash > 1800:
            market.append(["BUY_ANIMAL", "COW", 2])
        # feed wheat
        wheat = shed.get("WHEAT", 0)
        if day < 28 and wheat < cows + 3 and cash > 400:
            market.append(["BUY_PRODUCT", "WHEAT", min(12, cows + 3 - wheat)])
        # wheat seed
        if day <= 20 and seeds.get("WHEAT", 0) < 8 and cash > 250:
            market.append(["BUY_SEED", "WHEAT", 8])
        # sell milk/fert aggressively
        if shed.get("MILK", 0) >= 4 or day >= 27:
            market.append(["SELL", "MILK", shed.get("MILK", 0)])
        if shed.get("FERTILIZER", 0) >= 6 or day >= 27:
            market.append(["SELL", "FERTILIZER", shed.get("FERTILIZER", 0)])

        # scan needs
        unfed = []; fert = []; milk = []; unbuilt = []; dry = []; ripe = []; empty = []
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                if isinstance(t, dict):
                    if t.get("animal"):
                        if not t.get("fed_today"):
                            unfed.append((x, y))
                        if t.get("fertilizer_available"):
                            fert.append((x, y))
                        if (t.get("yield_units") or 0) > 0:
                            milk.append((x, y))
                    elif t.get("kind") == "PASTURE" and not t.get("animal"):
                        unbuilt.append((x, y))
                    elif t.get("kind") == "PLANT":
                        if not t.get("watered_today") and t.get("consecutive_unwatered", 0) >= 1:
                            dry.append((x, y))
                        elif (t.get("yield_units") or 0) > 0 and day - t.get("planted_day", day) >= 4:
                            ripe.append((x, y))
                elif t is None:
                    empty.append((x, y))

        def nearest(pos, lst):
            if not lst:
                return None
            return min(lst, key=lambda p: abs(p[0] - pos[0]) + abs(p[1] - pos[1]))

        acts = []
        for i, pos in enumerate(units):
            if pos is None:
                acts.append(["PASS"])
                continue
            pos = tuple(pos)
            inv = invs[i] if i < len(invs) else {}
            t = tiles[pos[1]][pos[0]]
            a = None
            if isinstance(t, dict) and t.get("animal"):
                if not t.get("fed_today") and inv.get("WHEAT", 0) > 0:
                    a = ["FEED"]
                elif (t.get("yield_units") or 0) > 0:
                    a = ["HARVEST"]
                elif t.get("fertilizer_available"):
                    a = ["COLLECT_FERTILIZER"]
                elif not t.get("cared_today") and day >= 7:
                    a = ["CARE"]
            elif isinstance(t, dict) and t.get("kind") == "PLANT":
                if (t.get("yield_units") or 0) > 0 and day - t.get("planted_day", day) >= 4:
                    a = ["HARVEST"]
                elif not t.get("watered_today"):
                    a = ["WATER"]
            elif t is None and (shed.get("COW", 0) > 0 or inv.get("COW", 0) > 0) \
                    and len(unbuilt) <= 0 and i <= 3:
                a = ["BUILD_PASTURE"]
            elif t is None and seeds.get("WHEAT", 0) > 0 and day <= 22 and i > 2:
                a = ["PLANT", "WHEAT"]
            if a is None:
                load = sum(v for k, v in inv.items()
                           if v > 0 and k not in ("WHEAT", "COW"))
                if load >= 2 or (inv.get("WHEAT", 0) > 6):
                    tgt = min(SHED_T, key=lambda p: abs(p[0]-pos[0])+abs(p[1]-pos[1]))
                    a = ["DROP"] if pos == tgt else _move(pos, tgt)
            if a is None and inv.get("WHEAT", 0) == 0 and unfed and shed.get("WHEAT", 0) > 0:
                tgt = min(SHED_T, key=lambda p: abs(p[0]-pos[0])+abs(p[1]-pos[1]))
                if pos == tgt:
                    a = ["PICKUP", "WHEAT", min(6, shed.get("WHEAT", 0))]
                else:
                    a = _move(pos, tgt)
            if a is None and inv.get("WHEAT", 0) > 0 and unfed:
                tgt = nearest(pos, unfed)
                a = ["FEED"] if pos == tgt else _move(pos, tgt)
            if a is None and inv.get("COW", 0) > 0:
                if unbuilt:
                    tgt = nearest(pos, unbuilt)
                    a = ["PLACE", "COW"] if pos == tgt else _move(pos, tgt)
                else:
                    a = ["PASS"]  # hold until a pasture frees up
            if a is None and shed.get("COW", 0) > 0 and unbuilt and i >= 2:
                tgt = min(SHED_T, key=lambda p: abs(p[0]-pos[0])+abs(p[1]-pos[1]))
                a = ["PICKUP", "COW", 1] if pos == tgt else _move(pos, tgt)
            if a is None and milk:
                tgt = nearest(pos, milk)
                a = ["HARVEST"] if pos == tgt else _move(pos, tgt)
            if a is None and fert:
                tgt = nearest(pos, fert)
                a = ["COLLECT_FERTILIZER"] if pos == tgt else _move(pos, tgt)
            if a is None and dry:
                tgt = nearest(pos, dry)
                a = ["WATER"] if pos == tgt else _move(pos, tgt)
            if a is None and ripe:
                tgt = nearest(pos, ripe)
                a = ["HARVEST"] if pos == tgt else _move(pos, tgt)
            if a is None and unfed and shed.get("WHEAT", 0) == 0 and i == 0:
                a = ["PASS"]
            acts.append(a or ["PASS"])

        return {"farmer": acts[0] if acts else ["PASS"],
                "hands": acts[1:1 + len(hands)], "market": market[:10]}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}
