import json, os, importlib.util
_TAPE = json.load(open("/home/user/kaggriculture/data/seb_opening_tape.json"))
_CUTOFF = len(_TAPE)
_spec = importlib.util.spec_from_file_location("_cm","/home/user/kaggriculture/scripts/counter_meta.py")
_cm = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_cm)
_PLANNER = _cm.CounterMeta()
_log=[]
def agent(observation, configuration):
    step = observation.get("step", 0)
    if step < _CUTOFF:
        t=_TAPE[step]
        n=1+len(observation["farms"][observation["player"]].get("hands") or [])
        hands=list(t["hands"])
        while len(hands)<n-1: hands.append(["PASS"])
        hands=hands[:max(0,n-1)]
        act={"market":t["market"][:10],"farmer":t["farmer"],"hands":hands}
    else:
        act=_PLANNER.act(observation,configuration)
    if step<4:
        _log.append({"step":step,"market":act["market"],"farmer":act["farmer"],"nhands":len(act["hands"]),
                     "obs_money":observation["farms"][observation["player"]]["money"],
                     "obs_hands":len(observation["farms"][observation["player"]]["hands"])})
        open("/tmp/hyb_log.json","w").write(json.dumps(_log))
    return act
