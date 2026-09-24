def agent(obs, config=None):
    n = 1 + len(obs["farms"][obs["player"]].get("hands") or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * (n - 1), "market": []}
