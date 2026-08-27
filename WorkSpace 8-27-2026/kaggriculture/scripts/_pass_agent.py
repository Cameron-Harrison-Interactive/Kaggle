
def agent(observation, configuration):
    return {"market": [], "farmer": ["PASS"], "hands": [["PASS"]] * len(observation["farms"][observation["player"]].get("hands") or [])}
