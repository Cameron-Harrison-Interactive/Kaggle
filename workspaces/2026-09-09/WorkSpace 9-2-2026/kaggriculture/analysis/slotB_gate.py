import importlib.util, json
from kaggle_environments import make
from kaggle_environments.core import environments
NAME = [k for k in environments if k.startswith("kagg") and "beginner" not in k][0]
WS = open("/tmp/ws").read().strip()
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    fn = getattr(mod, "kaggle_entry_agent", None) or mod.agent
    return lambda obs, config=None: fn(obs, config)
A = load(WS + "/topbots/tt_router_938.py", "live_router")
B = load("/tmp/slotB/main.py", "clone")
W = L = T = 0; marg = 0
for seed in range(101, 121):
    s = seed % 2
    pair = [None, None]; pair[s] = B; pair[1 - s] = A   # clone in the same seat the control's "side A" used
    env = make(NAME, configuration={"episodeSteps": 720, "seed": seed})
    env.run(pair)
    a = env.steps[-1][s]["reward"] or 0
    b = env.steps[-1][1 - s]["reward"] or 0
    if a > b: W += 1
    elif b > a: L += 1
    else: T += 1
    marg += a - b
    print(f"seed {seed}: clone {a:,.0f} vs router {b:,.0f} {'TIE' if a==b else ('W' if a>b else 'L')}", flush=True)
print(f"\nGATE RESULT: clone {W}W-{L}L-{T}T margin {marg:+,.0f}")
print("CONTROL (session 119) was 0W-3W-17T — must match exactly for byte-identical behavior")
