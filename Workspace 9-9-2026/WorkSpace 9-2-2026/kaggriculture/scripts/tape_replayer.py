"""Minimal route/tape replayer (Kaito-style repair layers).

Layers:
  1. hands alignment: pad/truncate hands list to live hand count
  2. bounded WEED repair: scripted PLANT/BUILD_* onto a WEED tile -> DIG
  3. safe fallback: on any error -> PASS (never crash the episode)

Route format: list of 719 dicts: {"farmer": [...], "hands": [[...]], "market": [...]}
Build from a mined tape JSON:  make_agent(json.load(open('tapes/X_YYYY.json'))['tape'])
"""
import json

_DIGGABLE = {"PLANT", "BUILD_PASTURE", "BUILD_COOP", "BUILD_BARN", "BUILD_SHED"}


def _g(obj, key, default=None):
    """Attribute/item-safe read that works on dict AND kaggle Struct."""
    try:
        v = obj[key]
        return v if v is not None else default
    except Exception:
        return getattr(obj, key, default)


class TapeReplayer:
    def __init__(self, route):
        self.route = route

    def agent(self, obs):
        try:
            step = int(_g(obs, "step", 0) or 0)
            player = int(_g(obs, "player", 0) or 0)
            farms = _g(obs, "farms") or [{}]
            farm = farms[player] if player < len(farms) else {}
            if not farm:
                return {"farmer": ["PASS"], "hands": [], "market": []}
            if not (0 <= step < len(self.route)):
                n = len(_g(farm, "hands") or [])
                return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}
            action = self.route[step]
            tiles = _g(farm, "tiles") or []
            farmer_pos = _g(farm, "farmer") or [0, 0]
            hands_pos = _g(farm, "hands") or []

            def tile_at(pos):
                x, y = int(pos[0]), int(pos[1])
                if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
                    return tiles[y][x]
                return None

            farmer = list(action.get("farmer") or ["PASS"])
            f = farmer[0] if farmer else "PASS"
            if f in _DIGGABLE:
                t = tile_at(farmer_pos)
                if isinstance(t, dict) and t.get("kind") == "WEED":
                    farmer = ["DIG"]
            hands_out = []
            raw_hands = action.get("hands") or []
            for i, h in enumerate(raw_hands):
                h = list(h) if isinstance(h, (list, tuple)) else ["PASS"]
                a = h[0] if h else "PASS"
                if a in _DIGGABLE and i < len(hands_pos):
                    t = tile_at(hands_pos[i])
                    if isinstance(t, dict) and t.get("kind") == "WEED":
                        h = ["DIG"]
                hands_out.append(h or ["PASS"])
            n_live = len(hands_pos)
            while len(hands_out) < n_live:
                hands_out.append(["PASS"])
            hands_out = hands_out[:n_live]
            market = action.get("market") or []
            return {"farmer": farmer, "hands": hands_out, "market": market}
        except Exception:
            n = len(farm.get("hands") or []) if farm else 0
            return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}


def make_agent(route):
    return TapeReplayer(route).agent
