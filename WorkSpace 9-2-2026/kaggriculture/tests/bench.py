"""Fast bench: solo + H2H BT + planted-tiles-over-time."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "agent"))

from sim import GameSim
from agent.custom import agent as custom
from agent.custom.board import Board
from agent.custom.plan import full_layout
import breaking_tie as BT


def call(fn, obs, cfg=None):
    try: return fn(obs, cfg)
    except TypeError: return fn(obs)


def solo(n_seeds=10):
    total = 0
    for seed in range(1, n_seeds+1):
        sim = GameSim(seed=seed)
        for _ in range(720):
            sim.step(custom(sim.obs(0)), {})
        total += sim.money(0)
    return total / n_seeds


def h2h_bt(n_seeds=10):
    delta = 0; wins = 0; n = 0
    for seed in range(1, n_seeds+1):
        for seat in [0,1]:
            sim = GameSim(seed=seed)
            for _ in range(720):
                obs0 = sim.obs(0); obs1 = sim.obs(1)
                if seat == 0:
                    a0 = call(custom, obs0); a1 = call(BT.agent, obs1)
                else:
                    a0 = call(BT.agent, obs0); a1 = call(custom, obs1)
                sim.step(a0, a1)
            c = sim.money(seat); o = sim.money(1-seat)
            if c > o: wins += 1
            delta += c - o
            n += 1
    return delta / n, wins, n


def plants_trace(seed=1):
    """Return (day, plants, empty_plantable, alive_animals) for each end-of-day."""
    sim = GameSim(seed=seed)
    trace = []
    layout = full_layout()
    for step in range(720):
        sim.step(custom(sim.obs(0)), {})
        b = Board(sim.obs(0))
        if b.hour == 0:
            n_plant = len(b.plants())
            empty = 0
            for (x,y), r in layout.items():
                if r in ("CROP","STRAW","MELON") and not b.is_locked(x,y) and b.tile(x,y) is None:
                    empty += 1
            alive = sum(1 for _ in b.animals())
            trace.append((b.day, n_plant, empty, alive))
    return trace


if __name__ == "__main__":
    s = solo(10)
    d, w, n = h2h_bt(10)
    print(f"SOLO(10): ${s:.0f}")
    print(f"H2H BT(20): {w}/{n}  delta ${d:+,.0f}")
    print()
    print("plants trace seed 1:")
    print(f"{'day':>3} {'plants':>7} {'empty':>6} {'alive':>6}")
    for d, p, e, a in plants_trace(1):
        if d % 3 == 0 or d in (1, 15, 27):
            print(f"D{d:>2}  {p:>7}  {e:>6}  {a:>6}")
