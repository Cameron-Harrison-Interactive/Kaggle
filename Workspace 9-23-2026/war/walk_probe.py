#!/usr/bin/env python3
"""walk_probe.py - attribute every MOVE step to the op it was traveling for.

For each unit we track its position hour by hour. When a productive op
executes at tile P, the moves since the previous op are charged to that op.
End-of-day leftover moves are charged to "TAIL" (walking that produced
nothing before the horn).

Usage: python3 war/walk_probe.py [bot] [seed ...]
"""
import io
import contextlib
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env  # noqa: E402


def run(path_a, path_b, seed):
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])
    return env


def analyse(env, verbose=True):
    steps = env.steps
    moves_for = Counter()      # op -> moves spent traveling to it
    ops_done = Counter()       # op -> count
    moves_total = 0
    tail_moves = 0
    pass_hours = 0
    shed_moves = 0

    # per unit: pending move count and last seen position
    pending = {}
    prev_pos = {}

    prev_day = None
    for st in steps:
        obs = (st[0] or {}).get("observation") or {}
        if "farms" not in obs:
            continue
        day = int(obs.get("day", 0))
        hour = int(obs.get("hour", 0))
        act = (st[0] or {}).get("action") or {}
        farm = obs["farms"][0]
        units_pos = [tuple(farm.get("farmer") or (0, 0))]
        units_pos += [tuple(h) for h in (farm.get("hands") or [])]
        units_act = []
        fa = act.get("farmer")
        if isinstance(fa, list):
            units_act.append(fa)
        for h in (act.get("hands") or []):
            units_act.append(h)

        if day != prev_day:
            # charge unspent moves at the day boundary as TAIL
            for k, v in pending.items():
                tail_moves += v
            pending = {}
            prev_pos = {}
            prev_day = day

        for ui in range(min(len(units_pos), len(units_act))):
            p = units_pos[ui]
            a = units_act[ui]
            op = a[0] if a else "PASS"
            # how far did this unit move this hour?
            d = 0
            if ui in prev_pos:
                d = abs(p[0] - prev_pos[ui][0]) + abs(p[1] - prev_pos[ui][1])
            prev_pos[ui] = p
            if op in ("NORTH", "SOUTH", "EAST", "WEST") or d > 0:
                pending[ui] = pending.get(ui, 0) + (d if d else 1)
                moves_total += (d if d else 1)
                continue
            if op == "PASS":
                pass_hours += 1
                continue
            # productive / shed op
            ops_done[op] += 1
            m = pending.pop(ui, 0)
            moves_for[op] += m
            if op in ("PICKUP", "DROP"):
                shed_moves += m

    for k, v in pending.items():
        tail_moves += v

    if verbose:
        print("=" * 68)
        print("WALK ATTRIBUTION  (moves charged to the op they were walking to)")
        print("=" * 68)
        tot_ops = sum(ops_done.values())
        print("total moves %d | ops %d | pass-hours %d | day-tail moves %d"
              % (moves_total, tot_ops, pass_hours, tail_moves))
        print("moves per op: %.2f" % (moves_total / max(1, tot_ops)))
        print()
        print("  %-22s %7s %7s %8s %8s" % ("OP", "count", "moves", "mv/op", "%moves"))
        rows = sorted(moves_for.items(), key=lambda kv: -kv[1])
        for op, mv in rows:
            c = ops_done[op]
            print("  %-22s %7d %7d %8.2f %7.1f%%" % (
                op, c, mv, mv / max(1, c), 100.0 * mv / max(1, moves_total)))
        print("  %-22s %7s %7d %8s %7.1f%%" % (
            "(day-tail, produced nothing)", "", tail_moves, "",
            100.0 * tail_moves / max(1, moves_total)))
        print()
        print("SHED-TRIP BURDEN: %d moves (%.1f%% of all walking) for %d ops"
              % (shed_moves, 100.0 * shed_moves / max(1, moves_total),
                 ops_done["PICKUP"] + ops_done["DROP"]))
    return dict(moves_for=moves_for, ops=ops_done, moves=moves_total,
                tail=tail_moves, shed=shed_moves, passes=pass_hours)


def main():
    ensure_env()
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_10"
    seeds = [int(s) for s in sys.argv[2:]] or [42]
    pa, pb = resolve(bot), resolve("pass")
    A = Counter()
    for s in seeds:
        env = run(pa, pb, s)
        print("\n### seed %d  final $%s" % (s, env.state[0].reward))
        r = analyse(env, verbose=len(seeds) == 1)
        A.update(r["moves_for"])
        A["__moves"] += r["moves"]
        A["__ops"] += sum(r["ops"].values())
        A["__tail"] += r["tail"]
        A["__shed"] += r["shed"]
        A["__pass"] += r["passes"]
        if len(seeds) > 1:
            print("  seed %d: moves %d ops %d mv/op %.2f tail %d shed %d pass %d"
                  % (s, r["moves"], sum(r["ops"].values()),
                     r["moves"] / max(1, sum(r["ops"].values())), r["tail"],
                     r["shed"], r["passes"]))
    if len(seeds) > 1:
        print("\nAGGREGATE %d seeds: moves %d ops %d mv/op %.2f | tail %d (%.1f%%)"
              " shed %d (%.1f%%) pass %d"
              % (len(seeds), A["__moves"], A["__ops"],
                 A["__moves"] / max(1, A["__ops"]), A["__tail"],
                 100.0 * A["__tail"] / max(1, A["__moves"]), A["__shed"],
                 100.0 * A["__shed"] / max(1, A["__moves"]), A["__pass"]))
        print("  moves by op:")
        for k, v in sorted(((k, v) for k, v in A.items()
                            if not k.startswith("__")), key=lambda kv: -kv[1]):
            print("    %-22s %7d" % (k, v))


if __name__ == "__main__":
    main()
