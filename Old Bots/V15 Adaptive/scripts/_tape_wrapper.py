
import json
_ROUTE = json.load(open('/home/user/kaggriculture/data/care_v1.json'))
_STEP = 0
def agent(observation, configuration):
    global _STEP
    if _STEP < len(_ROUTE):
        t = _ROUTE[_STEP]
        _STEP += 1
        n_hands = len(observation["farms"][observation["player"]].get("hands") or [])
        hands = list(t.get("hands") or [])
        while len(hands) < n_hands:
            hands.append(["PASS"])
        return {"market": t.get("market") or [], "farmer": t.get("farmer") or ["PASS"],
                "hands": hands[:n_hands]}
    return {"market": [], "farmer": ["PASS"],
            "hands": [["PASS"]] * len(observation["farms"][observation["player"]].get("hands") or [])}
