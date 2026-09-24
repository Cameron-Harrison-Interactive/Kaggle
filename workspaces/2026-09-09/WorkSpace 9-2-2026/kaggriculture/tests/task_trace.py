"""Diagnostic: at a given day, list all tasks generated with priorities."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))

from sim import GameSim
from agent.custom.board import Board
from agent.custom import agent as custom
from agent.custom.tasks import (
    generate_tasks, generate_planting_tasks, generate_build_and_place_tasks
)
from agent.custom.assigner import assign


sim = GameSim(seed=1)
for step in range(24*15 + 3):
    sim.step(custom(sim.obs(0)), {})
b = Board(sim.obs(0))
tasks = list(generate_tasks(b))
tasks.extend(generate_planting_tasks(b))
tasks.extend(generate_build_and_place_tasks(b, {'SHEEP':5,'COW':5,'GOOSE':6}))

# Group by kind, count by priority tier
from collections import Counter
by_kind = Counter()
for t in tasks:
    by_kind[(t.kind, t.priority)] += 1
print(f"D{b.day}H{b.hour}: {len(tasks)} tasks, {len(b.units)} units")
for (k, p), c in sorted(by_kind.items(), key=lambda x: -x[0][1]):
    print(f"  pri={p:>3} {k:>20}: {c}")

# Now show assignments
asgn = assign(b, tasks)
print("Assignments:")
for u in range(len(b.units)):
    t = asgn.get(u)
    if t:
        print(f"  u{u} @ {b.units[u]}: {t.kind}@{t.target} pri={t.priority}")
    else:
        print(f"  u{u} @ {b.units[u]}: IDLE")
