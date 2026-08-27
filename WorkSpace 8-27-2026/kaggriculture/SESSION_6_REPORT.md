# Session 6 — 8-20-2026: the single-file submission (main.py) + honest contested results

## What you asked for, delivered
1. **One file to submit.** Kaggle loads a single `main.py` — so `main.py` is now
   THE submission: fully self-contained (only `from collections import
   namedtuple`, nothing else), 887 lines, and it contains every system.
2. **Fertilizer only where it pays.** Fertilizer is spent ONLY on strawberries
   when `strawberry_price * 1.2 > fertilizer_price` (i.e. the expected +4
   units beat the fertilizer's sell value) AND the strawberry price is ≥ $90.
   Otherwise fertilizer is SOLD — it's worth $100+ early and only falls. No
   "+$20 and waste moves vs sell for $60" ever happens: the gate is computed
   from the live prices every day.
3. **"Params search" explained** (and why the bot self-manages): the search is
   only my offline tool to pick a handful of fixed constants. The SHIPPED bot
   decides everything at runtime from live state — hires, crop choice,
   fertilizer use, sell/buy timing, herd tilt. I run the tuning here; your PC
   is only for things that would take me hours.

## What's inside main.py (all six systems)
1. **Aware day planner** — every morning: enumerate must-do (feed/water/harvest
   /fert), build a full timeline per worker with EXACT movement simulation
   (Manhattan; board has no obstacles), only accept jobs that finish by hour
   24. Plant only if the same-day water slot is guaranteed (no hour-22 plants).
2. **Self-decided crew** — hires extra hands (fib cost) until the must-do work
   fits or money runs out.
3. **Rules engine** — exact crop/animal/market tables + exact price function.
4. **Market reader** — buys wheat in bulk when cheap (<$20), minimal when
   expensive (>$32); holds wheat as feed while below base; sells milk/wool/
   melon the day they land (their price only falls); **stops buying cows/
   sheep the moment their product price crashes** (milk<$50 / wool<$60) and
   pivots the freed cash into the crop economy.
5. **Opponent counter** — herd tilt away from the opponent's glut, front-run
   sells, crop-mix counter (all reading the opponent's PUBLIC farm).
6. **Anti-mirror** — crop choice/assignment rotate by a per-match signature, so
   no two matches route the same and copied timing can never sync to us.

## Measured results (honest)
| Matchup | Result |
|---|---|
| main.py vs PASS (10 seeds) | **$59,809 avg** (min $50.0k, max $66.4k) |
| main.py vs v2 (our reactive bot) | 1W-5L, **−$14.9k avg** |
| main.py vs v25 tape (our $145k champion) | 0W-6L, **−$111k avg** |

The contested numbers confirm exactly what you told me: solo gold is smoke.
When two 14-cow herds face off, milk and wool crash to $1 for BOTH sides, and
our animal-heavy economy is the one that loses most. Meanwhile the v25 tape
holds ~60 crops (wheat/melon income that's far less glut-sensitive), which is
why it wins by so much.

## The real gap, named precisely
The one thing separating us from v25 (and from Aster) is **crop scale**: they
run 50-60 crops with a deterministic per-worker route; our planner caps at
~20 because the timeline scheduler can't yet chain a worker across a whole
quadrant efficiently. That is the "route compiler / ledger" build I flagged —
and it is the LAST architecture piece. The market-reader pivot added this
session is correct and stays, but it can't out-earn a 3x crop disadvantage.

## Bottom line
`main.py` is a complete, self-contained, rules-aware, opponent-reading,
market-reading, anti-mirror bot — everything you've asked for is in it and it
scores ~$60k solo with zero weeds and a full 14-animal herd. It does not yet
beat our own v25 tape head-to-head, and I won't pretend otherwise: the
remaining work is the deterministic route compiler to scale crops to 50+.

## Next (my recommendation, one build)
Build the **route compiler** into main.py: instead of the greedy per-day
timeline, pre-compute each worker's full-season tile assignment (dated crop
schedule: sow on D, water daily, harvest at peak, replant), replay it through
a cash/labour/feed ledger exactly like Aster does, and re-derive it from the
live board every morning so it stays anti-mirror and self-repairing. That is
the ~$145k class of agent, and main.py's market-reader + counter + planner
already provide everything around it. Say the word and I'll start it.

## Files
`main.py` — THE submission (self-contained).
Support/dev (not needed for submission): `agent/decision_agent_v{2,4,7}.py`,
`scripts/rules.py`, `scripts/sim.py`, `scripts/planner.py`,
`scripts/search_params.py`, `top10/shabby_farm_agent.py` (Aster, real top-10).
