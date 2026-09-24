# Session 3 — 8-20-2026: rules engine, the counter layer, and the honest
# status of the "fill 75 slots" planner

## 1. "What do you mean by clone?" — clarification
When I said "clone" in earlier messages I meant a TEST OPPONENT I generate with
the same economy params as our own bot (to prove we can beat copies of
ourselves). I did NOT mean our bot is a clone of the ladder meta — it is
clean-room, built from the game rules. And you're right about the plan: a copy
of us that replays our TIMING will desync, while our live router self-repairs.
The v4 counter + the v5 anti-mirror signature are built around exactly that.

## 2. What I built this session

### `scripts/rules.py` — the bot's rulebook (your "know the rules" ask)
Exact crop/animal/market tables + the price function, transcribed from the
official engine and verified against its price table. The "extra income days"
are encoded precisely:
- One-time crops (wheat/carrot/melon) have a watering BONUS WINDOW
  `ceil(max_day/2) .. max_day`; each watered day inside it adds +1 yield
  (+2 fertilized).
- FERTILIZER pays on **strawberry** (+4 units, ~+$268/tile) and tomato
  (+4 units, ~+$29); it is a LOSS on wheat (−$51) and does NOTHING on melon
  (harvest is locked to age 10, and daily watering already hits the 6 cap).
  So the rule is: fertilize strawberries, sell the rest.
- `plan_crop(crop, plant_day)` returns the full dated schedule (water days,
  harvest day, expected yield) so a planner can reason about timing.

### `agent/decision_agent_v4.py` — the counter layer (FLAGSHIP, verified)
Reads the opponent's PUBLIC farm every turn:
1. HERD TILT — opponent cow-heavy → swap 2 cows → 2 sheep within the SAME
   headcount (milk crashes for everyone; wool stays ours). No tilt toward cows
   vs a sheep-flooder (wool floors too fast).
2. FRONT-RUN SELLS — see their unharvested yield; sell ours one turn first.
3. CROP-MIX COUNTER — opponent heavy in crash-prone crops → we tilt to wheat.

Verified (5 seeds x 2 seats): +$1.7k vs mirror, +$13.9k vs cow-flooder,
+$0.8k vs sheep-flooder, +$0.4k vs goose-flooder — **+$16.9k total, no
regressions, and byte-identical to v2 vs PASS** (costs nothing when there is
no opponent signal).

### `agent/decision_agent_v5.py` — coverage router (EXPERIMENT, opt-in)
A first attempt at "fill 60+ tiles and re-route every match": a per-match
signature rotates quadrant assignment + sweep direction (anti-mirror), workers
share the animal chores then sweep their quadrant for the NEAREST
water/harvest/plant/dig, with emergency feed/water overrides (never-miss).

**Honest result: it does NOT beat v2 yet** (defaults to exactly v2, coverage
off). Measurements found the real constraint:
- v2's reactive chain is at a LOCAL OPTIMUM: ~$68.5k, 12 crops, 14 animals.
  More hires, earlier land, more seeds, hour-split orders — all tested — each
  regressed it.
- The sweep can't keep 14 animals serviced AND 60 crops watered from one
  reactive pool: workers end up 33% idle (PASS) while crops go unwatered and
  die, because the animal chores + the plant-time window crowd out watering.

## 3. The verdict (matches your own instinct)
The top bots win with one SET build + timing (a deterministic route). To hold
75+ tiles you need the same thing done DYNAMICALLY: a deterministic per-worker
ROUTE COMPILER that assigns each worker a dated sequence of tiles, replays it
through a cash/labour/feed LEDGER, and re-plans from the live board each match
(with a per-match signature so no two matches route identically). That is the
Aster-class build — and it is the next milestone. The pieces are ready to
start from:
- `scripts/sim.py` — exact, cloneable game simulator (the replay engine).
- `scripts/rules.py` — crop/animal/bonus math (the scheduler's rulebook).
- `scripts/planner.py` — capacity + what-if (the ledger's feasibility checks).
- `top10/shabby_farm_agent.py` — Aster, a real top-10 ledger planner, extracted
  and runnable locally as the reference opponent ($161k vs PASS).

## 4. What beats whom today (measured)
| Agent | vs PASS | vs mirror clone | vs cow-flood | vs Aster (real top-10) |
|---|---|---|---|---|
| v2 economy | $68.5k | +$0 | ~+$12.6k | −$73k |
| v4 counter | $68.5k | **+$1.7k** | **+$13.9k** | −$79k |
| Aster (opponent) | $161k | — | — | — |

The counter is ready and worth running on the ladder NOW (it beats clone/flood
armies). The ~$90k gap vs Aster is the route compiler / ledger — the next build.

## 5. How to test on your PC
```
pip install kaggle-environments==1.32.6

# rules engine (the "extra income days"):
python3 scripts/rules.py

# flagship counter agent:
python3 agent/decision_agent_v4.py              # $68,532 vs PASS (seed 1)

# contested margins (v4 vs archetypes, v2 as control):
python3 scripts/battle_contested.py 1,2,3 v4

# battle the real top-10 opponent (Aster):
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('a','top10/shabby_farm_agent.py')
aster = importlib.util.module_from_spec(spec); spec.loader.exec_module(aster)
from kaggle_environments import make
import decision_agent_v4 as v4
v4.set_params(dict(v4.V4_DEFAULT_PARAMS))
env = make('kaggriculture', configuration={'episodeSteps':720,'seed':1})
env.run([v4.agent, aster.agent])
print([s['reward'] for s in env.steps[-1]])
"

# experimental coverage router (defaults to v2; enable with coverage=True):
python3 agent/decision_agent_v5.py
```

## Files (download for your PC)
`agent/decision_agent_v4.py` (submit this), `agent/decision_agent_v5.py`,
`scripts/rules.py`, `scripts/sim.py`, `scripts/planner.py`,
`scripts/battle_contested.py`, `top10/shabby_farm_agent.py`, and this report.
