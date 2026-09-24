#!/usr/bin/env python3
"""Offline choreography optimizer: given a labor trace, recompute per-day
min-walk routes (angular arcs + NN chains) for the SAME completed task set.
Reports recoverable walk steps. Usage: python3 optimizer.py <trace.json>"""
import json, math, sys

def d(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])

def run(path):
    tr = json.load(open(path))["trace"]
    MOVES = {"EAST","WEST","NORTH","SOUTH"}
    TILEROPS = {"WATER","HARVEST","FEED","CARE","COLLECT_FERTILIZER","FERTILIZE","PLANT","DIG","BUILD_COOP","BUILD_PASTURE"}
    tsav = 0
    for day in range(30):
        tasks, units = [], None
        for rec in tr:
            if rec["step"] // 24 != day: continue
            if units is None:
                units = [tuple(rec["pos"]["farmer"])] + [tuple(p) for p in rec["pos"]["hands"]]
            acts = [("farmer", rec["act"]["farmer"], rec["pos"]["farmer"])]
            for i, h in enumerate(rec["act"]["hands"]):
                if i < len(rec["pos"]["hands"]):
                    acts.append((i, h, rec["pos"]["hands"][i]))
            for name, a, pos in acts:
                if a and a[0] in TILEROPS:
                    tasks.append((tuple(pos), a[0]))
        aw = sum(1 for rec in tr if rec["step"] // 24 == day
                 for a in [rec["act"]["farmer"]] + list(rec["act"]["hands"]) if a and a[0] in MOVES)
        if not tasks or not units: continue
        U = len(units)
        cx = sum(t[0][0] for t in tasks)/len(tasks); cy = sum(t[0][1] for t in tasks)/len(tasks)
        order = sorted(range(len(tasks)), key=lambda i: math.atan2(tasks[i][0][1]-cy, tasks[i][0][0]-cx))
        clusters = [[] for _ in range(U)]
        for k, ti in enumerate(order): clusters[k % U].append(tasks[ti])
        total = 0
        for u, cl in zip(units, clusters):
            pos, rem, w = u, list(cl), 0
            while rem:
                ni = min(range(len(rem)), key=lambda i: d(pos, rem[i][0]))
                w += d(pos, rem[ni][0]); pos = rem[ni][0]; rem.pop(ni)
            total += w
        tsav += max(0, aw - total)
        print(f"d{day:>2} tasks {len(tasks):>3} actual {aw:>4} optimal {total:>4} saved {aw-total:>4}")
    print(f"\nTOTAL recoverable: {tsav} steps (~{tsav//2} tile-ops)")

if __name__ == "__main__":
    run(sys.argv[1])
