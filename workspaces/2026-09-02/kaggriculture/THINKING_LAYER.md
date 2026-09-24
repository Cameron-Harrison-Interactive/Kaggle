# The "Full AI Bot" — thinking layer (built 8-20-2026, session 2)

Answers the question: *"Do we need to train a model?"* — **No.** The bot you're
describing is a planning system, and it's now built (foundation + thinking
layer). Here is the architecture and how to use each piece.

## The 3 layers
```
┌────────────────────────────────────────────────────────────┐
│ L1  PERFECT STATE TRACKER   — see everything, miss nothing │
│     (decision_agent_v2 already scans every tile, plant,    │
│      animal, price, worker each turn)                      │
├────────────────────────────────────────────────────────────┤
│ L2  CAPACITY-AWARE ROUTER  — never miss a feed/water/fert  │
│     planner.daily_capacity()                               │
├────────────────────────────────────────────────────────────┤
│ L3  LOOKAHEAD PLANNER      — think on its feet             │
│     sim.GameSim (exact) + planner.what_if()                │
└────────────────────────────────────────────────────────────┘
```

## L3a — `scripts/sim.py` (exact, fast simulator)
Drives the **official engine's own interpreter** (imported, not re-copied), so
rules are bit-for-bit correct. **Verified**: replays of real games match on
final money AND every market price at every day boundary (5 seeds).

- `GameSim(seed).step(a0, a1)` — advance one turn (~40 µs).
- `GameSim(seed).clone()` — branch the game to test "what if I did X instead".
- `sim.verify_sim()` — re-run the verification anytime.

## L3b — `scripts/planner.py` (the thinking)
### Never-miss capacity check
```
planner.daily_capacity(obs, expected_hires=N)
```
Lists every critical task (feed/water/fert), estimates worker-steps with a
greedy assignment, and compares to `workers × 24`. If OVERLOADED, the bot
knows *before* buying that it can't afford another animal/crop — this is the
"knows if we can handle adding an animal" feature.

### What-if lookahead
```
planner.what_if(sim, days, options)
```
Clones the game and simulates each candidate decision forward, with the
opponent's behaviour frozen (replayed from a baseline) to isolate OUR decision.
Returns the dollar outcome of each option.

## Demo — run it
```
python3 scripts/demo_planner.py 1        # or any seed
```
Example output (seed 1, decision at day 8, 6-day lookahead):
```
Capacity: workers=5 plants=10 animals=4  need ~106 steps vs 120 -> OK
   extra 1 SHEEP (d8)        $4,643  (-647)   ← early sheep doesn't pay back
   extra 2 hands (d8,d9)     $6,629  (+1,339) ← crew was the bottleneck
   unlock next quadrant (d8) $5,288  (-2)     ← ~break-even in 6 days
```
Same decisions on seed 3 give *different* numbers (extra cow +$348, land −$906)
— the planner reads the actual board, so no two matches decide the same way.

## Where this is headed (next step)
Wire L2 + L3 into the live agent (`decision_agent_v3.py`):
1. At hour 0 each day, run `daily_capacity`. If overloaded → drop CARE first,
   then planting; if there's slack → consider one more animal/crop.
2. Before big buys (animal, land), run `what_if` over the next 2–4 days and
   only commit if the simulation says it pays.
3. Keep the reflex layer (emergency feed/water) for anything the plan misses.

That gives a bot that routes in real time from the live state (never the same
twice), never misses a critical task, and makes tradeoff decisions by
simulation instead of guesswork — with no training required.
