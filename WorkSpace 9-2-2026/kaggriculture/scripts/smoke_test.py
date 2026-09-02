"""
smoke_test.py — end-to-end test that Kaggle's framework can actually load and
run our main.py.  Catches the class of bug where main.py imports/parses fine
but Kaggle's `get_last_callable` picks the wrong function as the entrypoint
(e.g., picks `set_params` instead of `agent`, and the game silently PASSes).

Usage:
    python3 scripts/smoke_test.py

Exits non-zero if final money is <= starting money (a strong sign the wrong
callable is being used and the framework is defaulting to PASS).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.abspath(os.path.join(HERE, "..", "main.py"))

# --- 1. Check that get_last_callable picks `agent` (not set_params etc.)
raw = open(MAIN_PY).read()
env = {}
exec(compile(raw, "main.py", "exec"), env)
callables = [(k, v) for k, v in env.items() if callable(v)]
last_name = callables[-1][0]
print(f"[1] last callable in main.py: {last_name!r}")
if last_name not in ("agent", "_kaggle_submission_entrypoint"):
    print(f"    FAIL — Kaggle framework will use {last_name!r} as the "
          f"entrypoint, but that is neither `agent` nor `_kaggle_submission_entrypoint`.  "
          f"Move a valid entrypoint to be the LAST function/class defined in main.py.")
    sys.exit(1)

# --- 2. Run one full match via the ACTUAL Kaggle framework
from kaggle_environments import make


def _pass(obs, config=None):
    farm = obs["farms"][obs["player"]]
    n = len(farm.get("hands", []) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}


env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
t0 = time.time()
result = env.run([MAIN_PY, _pass])
dt = time.time() - t0
money = result[-1][0]["observation"]["farms"][0]["money"]
print(f"[2] vs PASS seed 1 via kaggle_environments.make: ${money:,.0f}  ({dt:.1f}s)")
if money <= 3000:
    print(f"    FAIL — final money {money} <= starting money 3000.  Framework "
          f"is defaulting to PASS.  Check step 1.")
    sys.exit(2)

print("SMOKE TEST PASS.")
