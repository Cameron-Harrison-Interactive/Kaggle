"""v6j_sweep.py — calibrate the milk gate (MG) in v6h2. One-change discipline:
variants differ ONLY in the MG constant (gate reactive layer, endorsed).

Sweep: gate x cap, days=28. Gates: 12-seed solo (vs pass) vs v6h2's 121,006
floor; then H2H vs v1112fr (12 seeds, seat 0) for the top solo variants.
"""
import sys, os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import h2h_forced as H
import sim

V6H2 = os.path.join(ROOT, "topbots", "v6h2.py")
V1112 = os.path.join(ROOT, "topbots", "v1112fr.py")
BASE_MG = 'MG = {"on": 0, "gate": 170.0, "cap": 40, "days": 28}'


def pass_agent(obs, configuration=None):
    f = obs["farms"][obs["player"]]
    return {"farmer": ["PASS"], "hands": [["PASS"] for _ in (f.get("hands") or [])], "market": []}


def make_variant(gate, cap, days=28):
    src = open(V6H2).read()
    assert BASE_MG in src, "MG line not found"
    new_mg = 'MG = {"on": 1, "gate": %s, "cap": %s, "days": %s}' % (gate, cap, days)
    out = src.replace(BASE_MG, new_mg)
    path = os.path.join(ROOT, "topbots", "_v6j_g%s_c%s.py" % (gate, cap))
    open(path, "w").write(out)
    return path


def solo12(path):
    tot = []
    for seed in range(1, 13):
        H._st["force"] = None; H._st["seen"] = 0
        a = H.load_agent(path)
        g = sim.GameSim(seed=seed)
        for _ in range(720):
            o = g.obs(0)
            g.step(a(o), pass_agent(g.obs(1)))
        tot.append(g.money(0))
    return tot


def h2h12(path):
    tot = []
    for seed in range(1, 13):
        out = H.run_h2h(path, V1112, seed, force=None)
        tot.append(out["a"] - out["b"])
    return tot


if __name__ == "__main__":
    results = {}
    for gate in (140, 150, 160, 170, 185):
        for cap in (30, 50):
            p = make_variant(gate, cap)
            s = solo12(p)
            results[(gate, cap)] = s
            print(f"gate {gate} cap {cap:>2}: avg {sum(s)/12:>9,.0f}  per-seed {[int(x) for x in s]}", flush=True)
    base = solo12(V6H2)
    print(f"BASELINE v6h2 : avg {sum(base)/12:>9,.0f}", flush=True)

    top = sorted(results.items(), key=lambda kv: -sum(kv[1]))[:4]
    print("\n=== H2H (vs v1112fr, 12 seeds, seat0) for top 4 + baseline ===", flush=True)
    bh = h2h12(V6H2)
    print(f"BASELINE v6h2 : avg margin {sum(bh)/12:>+9,.0f}", flush=True)
    for (gate, cap), s in top:
        p = os.path.join(ROOT, "topbots", "_v6j_g%s_c%s.py" % (gate, cap))
        m = h2h12(p)
        print(f"gate {gate} cap {cap:>2}: solo {sum(s)/12:>9,.0f}  h2h margin {sum(m)/12:>+9,.0f}", flush=True)
