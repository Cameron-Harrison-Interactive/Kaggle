# Session 4 — 8-20-2026: the set-path planner (v6) — built, and the honest status

## What you asked for, and what I built
You were right that I kept falling back to reactive designs. This session I
built the thing you described — **a bot that, every morning, computes a SET
PATH for every worker from the live board, decides its own hire count by
weighing workload against capacity, and re-derives everything each match so no
two games route the same.**

### `agent/decision_agent_v6.py` — the day planner
- At hour 0 it enumerates MUST-DO jobs (feed every animal, water every plant,
  harvest everything ready, collect every fertilizer), estimates each job's
  cost (walk + 1 action), and **assigns each worker a deterministic ordered
  path** (greedy nearest-worker assignment).
- **Capacity-aware hiring**: if the workload exceeds `workers × 24` hours, it
  hires more hands (fib cost) until it fits — the "knows it needs more hires"
  logic. Growth (planting) is also fed into the hire decision.
- **Growth**: plants new crops (each planting auto-followed by a same-day
  watering) up to what the crew can actually service, plus care + dig.
- **Anti-mirror signature**: crop order and assignment rotate per match
  (seat + opponent build + prices), so no two matches produce the same
  schedule — a copied timing plan desyncs.
- **v4 counter folded in**: herd tilt (away from the opponent's glut) and
  crop-mix counter.

## Bugs I found and fixed this session (all real, all would have bitten later)
1. **The 10-order market cap silently drops orders** — `wheat + 9 hires = 10`
   on late days, so land/seeds/animals were dropped → herd never grew. Fixed
   by splitting orders across hours (h0 = wheat+hires, h1 = land/seeds/animals).
2. **Stale-job check used a "kind" key that scanned tiles don't have** — every
   WATER job was marked stale, so nothing was ever watered. Fixed.
3. **Overspend churn** — every buy was checked against the same starting cash,
   so one morning could blow the whole bank. Fixed with a running cash budget.
4. **Far-tile planting thrash** — anti-mirror rotation put far corner tiles
   first, making workers walk 8-10 steps per planting. Fixed: plant
   near-shed-first (anti-mirror lives in crop order, not tile order).
5. **Wasted farmer** — booking the farmer 24/7 for herd duty left a full
   worker idle on quiet days. Fixed: farmer takes plan jobs too.
6. **Seed-limitation insight** — v2's 12-crop cap is seed-limited, not
   labor-limited, but giving it more seeds/crops *lowers* its score (measured
   $68.5k → $35k). The reactive chain can't profitably hold more crops; that
   is exactly what the planner is meant to solve.

## The honest bottom line
- **v6 is built and runs, but it does NOT beat v2's $68.5k yet** (currently
  ~$5-8k, oscillating). The remaining gap is one specific thing: **my
  hand-rolled cost model underestimates execution time**, so the plan assigns
  more work than the workers actually complete, crops get planted at hour 22
  and die unwatered, and the farm churns.
- That gap is fixable, and the fix is precisely the "ledger" you described:
  **simulate each worker's route with the real movement rules** (or score
  candidate day-plans with the exact simulator `sim.py`) instead of estimating
  `walk+1`. I have `sim.py` verified against the engine — it's the right tool
  and it's already in the workspace.

## What IS ready to run (verified this session)
- **`agent/decision_agent_v4.py`** — the counter layer. Verified again just
  now: identical to v2 vs PASS ($68,532), and +$20.2k margin vs a 14-cow
  flooder on seed 1. This is the bot to submit against clone/flood armies.
- **`scripts/rules.py`** — the rulebook for "extra income days" (watering
  bonus windows, fertilizer economics: strawberry +$268/tile, wheat −$51,
  melon $0).

## Where we're heading (the path to the autonomous 10-20k-line bot)
v6 IS the skeleton. The next iterations, in order:
1. Replace v6's cost estimate with **exact route simulation** (per-worker path
   replay using real movement) — this closes the plan-vs-reality gap.
2. Fold in **rules.py scheduling** (fertilize strawberries, harvest at peak,
   maturity-gated planting) so the planner hits the bonus windows.
3. **Self-play tune** with `sim.py` + the search harness against the top-10
   archetypes (Aster included).
4. Keep v4's counter as the live head while v6 matures.

## Files this session
`agent/decision_agent_v6.py` (the planner), `agent/decision_agent_v4.py`
(the verified counter — submit this), `scripts/rules.py` (the rulebook),
`scripts/sim.py` + `scripts/planner.py` (verified simulator + what-if),
`scripts/battle_contested.py` (margin harness), `top10/shabby_farm_agent.py`
(real top-10 opponent).
