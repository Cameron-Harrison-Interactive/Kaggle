"""price_series.py — dump WHEAT (+MILK) market inventory/price by day, solo & H2H.
Usage: python3 _ref/price_series.py <bot.py> [opp.py] [seed]
"""
import sys, os, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim

def load(path, name="botmod"):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def call(fn, obs):
    try:
        return fn(obs, None)
    except TypeError:
        return fn(obs)

def run(path, opp_path, seed):
    m0 = load(path, "b0")
    m1 = load(opp_path, "b1") if opp_path else None
    sim = GameSim(seed=seed)
    a1 = {"farmer": ["PASS"], "hands": [], "market": []}
    rows = []
    for step in range(720):
        o0 = sim.obs(0)
        a0 = call(m0.agent, o0)
        if m1 is not None:
            o1 = sim.obs(1)
            a1 = call(m1.agent, o1)
        sim.step(a0, a1)
        if step % 24 == 23:  # end of day
            mk = sim.obs(0)["market"]
            inv = mk["inventory"]; pr = mk["prices"]
            rows.append((step // 24,
                         inv["WHEAT"] - 10000, pr["WHEAT"],
                         inv["MILK"] - 10000, pr["MILK"]))
    return rows

if __name__ == "__main__":
    bot = sys.argv[1]
    opp = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].isdigit() else None
    seed = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 1
    rows = run(bot, opp, seed)
    mode = "H2H vs " + opp if opp else "SOLO"
    print(f"== {mode} seed {seed} (inv shown as delta from I0=10000) ==")
    print("day  w_inv   w$    m_inv   m$")
    for d, wi, wp, mi, mp in rows:
        print(f"{d:3d} {wi:+6d} {wp:4d} {mi:+6d} {mp:4d}")
