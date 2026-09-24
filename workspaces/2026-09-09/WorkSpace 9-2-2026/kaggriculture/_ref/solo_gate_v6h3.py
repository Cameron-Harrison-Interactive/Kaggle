"""Solo A/B gate: v6h2s (live champ) vs v6h3 (DIG-before-BUILD patch #7).

Run:  cd kaggress... && python3 _ref/solo_gate_v6h3.py [n_seeds]
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


def run(agent_mod, seed):
    sim = GameSim(seed=seed)
    a1 = {"farmer": ["PASS"], "hands": [], "market": []}
    for step in range(720):
        o = sim.obs(0)
        a = agent_mod.agent(o, None)
        sim.step(a, a1)
    return sim.money(0)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    a = load(os.path.join(ROOT, "topbots", "v6h2s.py"), "v6h2s_gate")
    b = load(os.path.join(ROOT, "topbots", "v6h3.py"), "v6h3_gate")
    rec = [123361, 115096, 123783, 109526, 120540, 117597,
           131599, 121670, 128819, 116855, 129332, 113890]
    tot_a = tot_b = 0
    print("seed |   v6h2s    v6h3    delta | note")
    for seed in range(1, n + 1):
        ma = run(a, seed)
        mb = run(b, seed)
        tot_a += ma
        tot_b += mb
        note = ""
        if seed <= len(rec) and ma != rec[seed - 1]:
            note = f"! v6h2s={ma} != recorded {rec[seed-1]}"
        print(f"{seed:4d} | {int(ma):8,d} {int(mb):8,d} {int(mb-ma):+8,d} | {note}")
    print(f"AVG  | {tot_a/n:8,.0f} {tot_b/n:8,.0f} {(tot_b-tot_a)/n:+8,.0f} |")


if __name__ == "__main__":
    main()
