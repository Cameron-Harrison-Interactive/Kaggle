"""Diagnose v1112fr solo run: idle units, free tiles, cash, shed, H00 order room.

Run:  cd kaggriculture && python3 _ref/diag_v44_idle.py
"""
import sys, importlib.util, os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim  # noqa: E402


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def free_tiles(farm):
    out = []
    for y, row in enumerate(farm["tiles"]):
        for x, t in enumerate(row):
            if t is None:
                out.append((x, y))
    return out


def main():
    m = load(os.path.join(ROOT, "topbots", "v1112fr.py"), "b0")
    sim = GameSim(seed=1)
    a1 = {"farmer": ["PASS"], "hands": [], "market": []}
    idle_pos = defaultdict(list)      # hour -> [(day, x, y)]
    h00_orders = []
    layout_days = {0, 5, 10, 15, 20, 25, 29}
    for step in range(720):
        o = sim.obs(0)
        a = m.agent(o, None)
        farm = o["farms"][0]
        hour, day = o["hour"], o["day"]
        # units: farmer + hands positions
        pos = [farm.get("farmer")] + list(farm.get("hands", []) or [])
        acts = [a.get("farmer", ["PASS"])] + list(a.get("hands", []) or [])
        for i, (p, ac) in enumerate(zip(pos, acts)):
            verb = ac[0] if isinstance(ac, list) and ac else str(ac)
            if verb == "PASS" and p:
                idle_pos[hour].append((day, p[0], p[1]))
        if hour == 0:
            h00_orders.append((day, len(a.get("market", [])),
                               farm["money"], o["private"]["shed"].get("WHEAT", 0)))
        if hour == 23 and day in layout_days:
            ft = free_tiles(farm)
            print(f"D{day:02d} free tiles ({len(ft)}): {ft}")
        sim.step(a, a1)

    print("\nIDLE unit positions by hour (count, sample positions):")
    for h in range(24):
        rows = idle_pos[h]
        if not rows:
            continue
        c = Counter((x, y) for _, x, y in rows)
        print(f"  H{h:02d}: {len(rows):4d} idle  top: {c.most_common(6)}")

    print("\nD H00: n_orders  cash  shedWHEAT")
    for d, n, cash, w in h00_orders:
        print(f"  D{d:02d}: {n:2d}  ${cash:7.0f}  {w}")

    print("\nfinal money:", sim.money(0))


if __name__ == "__main__":
    main()
