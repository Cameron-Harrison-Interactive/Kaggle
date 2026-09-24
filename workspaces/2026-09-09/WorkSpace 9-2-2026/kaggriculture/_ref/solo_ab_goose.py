"""Solo A/B: v1112fr_goose vs v1112fr baseline, N seeds, with telemetry.

Run:  cd kaggriculture && python3 _ref/solo_ab_goose.py [n_seeds]
"""
import sys, importlib.util, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim  # noqa: E402


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def run(agent_mod, seed, telem=None):
    sim = GameSim(seed=seed)
    a1 = {"farmer": ["PASS"], "hands": [], "market": []}
    hand_sum = 0
    for step in range(720):
        o = sim.obs(0)
        a = agent_mod.agent(o, None)
        farm = o["farms"][0]
        hand_sum += len(farm.get("hands", []) or [])
        if telem is not None:
            for od in a.get("market", []) or []:
                if od and od[0] == "SELL" and od[1] in ("EGG", "FERTILIZER"):
                    telem[od[1]] = telem.get(od[1], 0) + int(od[2])
            if o["hour"] == 23:
                g = sum(1 for row in farm["tiles"] for t in row
                        if isinstance(t, dict) and t.get("animal") == "GOOSE")
                telem["geese_max"] = max(telem.get("geese_max", 0), g)
        sim.step(a, a1)
    return sim.money(0), hand_sum


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    gk = load(os.path.join(ROOT, "topbots", "v1112fr_goose.py"), "gk_ab")
    bb = load(os.path.join(ROOT, "topbots", "v1112fr.py"), "bb_ab")
    tot_g = tot_b = 0.0
    print("seed |  goose$    base$   delta | geese eggs fert | hands(g/base)")
    for seed in range(1, n + 1):
        t = {}
        mg, hg = run(gk, seed, t)
        mb, hb = run(bb, seed)
        tot_g += mg
        tot_b += mb
        print(f"{seed:4d} | {mg:8.0f} {mb:8.0f} {mg-mb:+7.0f} | "
              f"{t.get('geese_max',0):5d} {t.get('EGG',0):4d} {t.get('FERTILIZER',0):4d} | "
              f"{hg:5d}/{hb:<5d} {'HIRE-DAMAGE' if hg < hb - 50 else ''}")
    print(f"AVG  | {tot_g/n:8.0f} {tot_b/n:8.0f} {(tot_g-tot_b)/n:+7.0f}")


if __name__ == "__main__":
    main()
