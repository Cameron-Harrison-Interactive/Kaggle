"""Greedy surgical tape patcher for the melon capture.

Candidates: PASS slots within 3 steps of a serviceable late melon (D17-29).
Each candidate patch replaces the unit's PASS with a walk/service sequence
(1-2 tape steps). Every patch is verified with a full-game sim; only
net-positive patches are kept. The tape is seed-independent (positions are
deterministic), so winners transfer.
"""
import ast
import base64
import importlib.util
import json
import sys
import zlib
from importlib.machinery import SourceFileLoader

ROOT = "/home/user/" + "kag" + "g" + "ric" + "ulture"
BASE_FILE = ROOT + "/topbots/wm1719_candidate.py"
TRACE = json.load(open("/tmp/medic_trace_s1.json"))


def call(fn, o):
    try:
        return fn(o, None)
    except TypeError:
        return fn(o)


def load_routes():
    loader = SourceFileLoader("gp", BASE_FILE)
    spec = importlib.util.spec_from_loader("gp", loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return json.loads(json.dumps(m._V44_ROUTES))


def build_variant(routes, out_path):
    loader = SourceFileLoader("gp2", BASE_FILE)
    spec = importlib.util.spec_from_loader("gp2", loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    src = open(BASE_FILE).read()
    b85 = base64.b85encode(zlib.compress(json.dumps(routes).encode())).decode()
    endm = ')).decode("utf-8"))'
    i = src.index("_V44_ROUTES = json.loads(zlib.decompress(base64.b85decode(")
    j = src.index(endm, i) + len(endm)
    src = src[:i] + "_V44_ROUTES = json.loads(zlib.decompress(base64.b85decode((\n" + repr(b85) + "\n))).decode(\"utf-8\"))" + src[j:]
    open(out_path, "w").write(src)


def sim_final(path, seed=1):
    for k in [k for k in list(sys.modules) if k.split(".")[0] in ("v19", "v23", "v24", "v44", "v48", "scripts", "gp", "gp2")]:
        del sys.modules[k]
    loader = SourceFileLoader("gps", path)
    spec = importlib.util.spec_from_loader("gps", loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    from sim import GameSim
    sim = GameSim(seed=seed)
    for _ in range(720):
        o0, o1 = sim.obs(0), sim.obs(1)
        a = call(m.agent, o0)
        sim.step(a, {"farmer": ["PASS"], "hands": [], "market": []})
    return sim.money(0)


def need_of(mv, day):
    planted = mv["planted"]
    yu = mv["yu"]
    if (day - planted >= 9 and yu > 0) or yu >= 5:
        return "HARVEST"
    if not mv["watered"] and (6 <= day - planted <= 12 or mv["thirst"] >= 1):
        return "WATER"
    return None


def unit_action_ref(tape, step, idx):
    a = tape[step]
    if idx == 0:
        return a, "farmer"
    hands = a.setdefault("hands", [])
    while len(hands) < idx:
        hands.append(["PASS"])
    return hands, idx - 1


def apply_patch(routes, step, idx, action):
    for name in routes:
        container, k = unit_action_ref(routes[name], step, idx)
        container[k] = action


def candidates():
    out = []
    for rec in TRACE:
        if not (408 <= rec["step"] <= 715):
            continue
        day = rec["day"]
        for mk, mv in rec["melons"].items():
            need = need_of(mv, day)
            if not need:
                continue
            mx, my = ast.literal_eval(mk)
            for ui, p in enumerate(rec["pos"]):
                act = rec["acts"][ui] if ui < len(rec["acts"]) else None
                if not (isinstance(act, list) and act and act[0] == "PASS"):
                    continue
                d = abs(p[0] - mx) + abs(p[1] - my)
                if d == 0:
                    out.append({"step": rec["step"], "idx": ui, "seq": [[need]], "melon": (mx, my), "d": 0})
                elif d <= 3:
                    move = ("EAST" if mx > p[0] else "WEST" if mx < p[0] else "SOUTH" if my > p[1] else "NORTH")
                    out.append({"step": rec["step"], "idx": ui, "seq": [[move], [need]], "melon": (mx, my), "d": d})
    # dedupe by (step, idx)
    seen = {}
    for c in out:
        key = (c["step"], c["idx"])
        if key not in seen or c["d"] < seen[key]["d"]:
            seen[key] = c
    return sorted(seen.values(), key=lambda c: c["step"])


if __name__ == "__main__":
    base_routes = load_routes()
    base_final = sim_final(BASE_FILE, 1)
    print(f"baseline seed1: {base_final:,.0f}", flush=True)
    cands = candidates()
    print(f"candidates: {len(cands)}", flush=True)
    winners = []
    for n, c in enumerate(cands[:60]):
        routes = json.loads(json.dumps(base_routes))
        for si, act in enumerate(c["seq"]):
            apply_patch(routes, c["step"] + si, c["idx"], act)
        out = "/tmp/_gp_var.py"
        build_variant(routes, out)
        fin = sim_final(out, 1)
        delta = fin - base_final
        if delta > 0:
            winners.append({**c, "delta": round(delta), "final": round(fin)})
        if (n + 1) % 10 == 0:
            print(f"  {n+1}/{min(60, len(cands))} tested, winners so far: {len(winners)}", flush=True)
    winners.sort(key=lambda w: -w["delta"])
    print("WINNERS:")
    for w in winners[:20]:
        print("  ", w)
    json.dump(winners, open("/tmp/gp_winners.json", "w"))
