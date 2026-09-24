"""h2h_forced.py — quick H2H runner (GameSim-based) with optional forced shop sequence.

The forced-shop patch wraps K._end_of_day: after the original EOD appends the
naturally-drawn shop, we rewrite it to FORCE[draw_index]. The RNG stream is
untouched (weeds identical to natural), only the appended entry changes — so
forced runs isolate the VALUE of a given shop set with zero farm changes.

Usage:
  python _ref/h2h_forced.py <A.py> <B.py> <seed> natural
  python _ref/h2h_forced.py <A.py> <B.py> <seed> YARN_STORE,YARN_STORE,...
Prints one JSON line: {"a":, "b":, "margin":, "shops":, "secs":}
"""
import sys, os, json, time, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import sim  # scripts/sim.py — exact-engine GameSim harness
K = sim.K

_st = {"force": None, "seen": 0}
_orig_eod = K._end_of_day


def _eod(state, env, day):
    _orig_eod(state, env, day)
    force = _st["force"]
    if force is None:
        return
    town = state[0].observation.town
    shops = town["unlocked_shops"]
    n = len(shops)
    if n > _st["seen"]:
        idx = _st["seen"]
        if idx < len(force):
            shops[-1] = force[idx]
        _st["seen"] = n


K._end_of_day = _eod

_mod_n = [0]


def load_agent(path):
    _mod_n[0] += 1
    name = "bot_%d_%s" % (_mod_n[0], os.path.basename(path).replace(".", "_"))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def run_h2h(a_path, b_path, seed, force=None, steps=720):
    """Returns dict with final money for A (seat0) and B (seat1)."""
    _st["force"] = list(force) if force else None
    _st["seen"] = 0
    a = load_agent(a_path)
    b = load_agent(b_path)
    g = sim.GameSim(seed=seed)
    t0 = time.time()
    g.run(a, b, steps=steps)
    dt = time.time() - t0
    shops = list(g.state[0].observation.town["unlocked_shops"])
    return {"a": g.money(0), "b": g.money(1), "margin": g.money(0) - g.money(1),
            "shops": shops, "secs": round(dt, 1)}


if __name__ == "__main__":
    a_path, b_path, seed, spec = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    force = None if spec == "natural" else spec.split(",")
    out = run_h2h(a_path, b_path, seed, force)
    print(json.dumps(out))
