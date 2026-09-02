# Session 5 — 8-20-2026: the "fully aware" bot (v7) — BUILT AND RUNNING

## What you asked for, built for real this time
> "The Bot/AI should always know the rules/days, what it watered and when it
> needs watering again, what to plant based on how long is left... Fully Aware
> BOT, not some half-baked lets jump and then figure it out plan."

That is exactly what `agent/decision_agent_v7.py` now does. It is a **day
planner**, not a reactive worker:

1. **It knows its field.** It scans the board and keeps a running memory of
   every crop (where, planted when) and every animal (placed when, fed today,
   next production). It knows a plant needs water on its planting day and
   every day after; it knows an animal needs feed daily.
2. **It knows the rules** (see `scripts/rules.py`): melon needs 10 days, wheat
   4, strawberry pays out over 16 days, so "what to plant" is decided by the
   days left AND the live prices. It knows you can't plant at hour 22 unless a
   water slot at hour 23 is already guaranteed — so it only plants when the
   same-day water is booked.
3. **It plans the whole day before stepping into the field.** Every worker gets
   a complete ordered timeline (tile → action → tile → action...). Movement is
   simulated EXACTLY (Manhattan distance — the board has no obstacles), so the
   scheduler only accepts a job if it truly finishes by hour 24. A planting is
   scheduled as PLANT-then-WATER on the same tile with the water slot
   guaranteed. Nothing is "jump and find out."
4. **It decides its own crew.** If the must-do work (feed + water + harvest +
   fertilizer) doesn't fit the crew's hours, it hires more hands (fib cost)
   until it fits or the money runs out.
5. **Anti-mirror.** Crop order and assignment rotate by a per-match signature
   (seat + opponent build + prices), so no two matches produce the same
   schedule — a copied "set build and timing" can never sync to us.
6. **Counter (from v4).** Herd tilt away from the opponent's glut product,
   front-run sells, crop-mix counter — all folded in.

## Bugs found & fixed on the way (all would have bitten later)
- The 10-order market cap silently dropping animal/land/seed buys → split
  orders across hours (h0 wheat+hires, h1 animals→seeds→land) with a running
  cash budget.
- The stale-check used a tile key ("kind") that scanned tiles don't have → all
  water jobs were skipped → nothing was watered. Fixed.
- **The farmer (cheapest feeder, since it spawns on the shed tile) got all the
  feed jobs but its reactive herd-glue preempted its plan every turn → 7/10
  animals went unfed.** Fixed by scheduling BUILD→PICKUP→PLACE *into* the plan
  and removing the reactive branch.
- **Unscheduled placement walks** made the farmer overrun its day (7 feed jobs
  planned, 2 executed). Fixed by scheduling the full place walk.
- **Overspend churn**: every buy checked the same starting cash → one morning
  could blow the bank. Fixed with a running cash budget (animals first, since
  the herd is the income engine).

## Results (measured)
| | vs PASS (10 seeds) | crops sustained | herd | weeds |
|---|---|---|---|---|
| v2 reactive | $66.3k | ~12 | 14 by d13 | some |
| **v7 planner** | **$61.9k** | **~20+** | 14 by d19 | **~0** |

- The planner holds **~2x the crops** with **zero weed losses** (every plant's
  water is on the schedule) and still runs the full 14-animal herd.
- Contested (v7 vs v2): 1W-3L, −$3.8k avg — the planner is competitive but not
  yet superior. The gap is herd SPEED (v7's herd reaches 14 about 6 days
  later, because placement is a scheduled farmer chore) and a few tuned
  parameters.

## The honest remaining gap (and the fix)
The architecture you asked for is done and demonstrably working. What's left
is **tuning, not architecture**: herd ramp timing, buy aggressiveness, the
crop value weights. That's exactly what the search harness is for — I've been
hand-sweeping these one at a time (3 hires → 4 hires +8 late raised $42k →
$64k), and a proper run on your 8-core desktop will find the rest.

Run it:
```
pip install kaggle-environments==1.32.6
python3 agent/decision_agent_v7.py          # ~$58k on seed 1
python3 scripts/search_params.py --population 32 --generations 300 --seeds 1,2,3
```
(To point the search at v7 instead of v2, edit `scripts/search_params.py`:
`import decision_agent_v7 as dv2`.)

## Next steps (in order)
1. Run the parameter search on v7 (your desktop) — closes the ~$4k solo gap.
2. Add `rules.py` fertilizer scheduling (fertilize strawberries only; it's the
   one crop where fertilizer pays +$268/tile) as a planned job.
3. Fold v7's timeline scheduler into v4's counter head, so the counter bot
   also plans its days.

## Files
`agent/decision_agent_v7.py` (the aware planner — this session's build),
`agent/decision_agent_v4.py` (the verified counter, still the safe submit),
`scripts/rules.py`, `scripts/sim.py`, `scripts/planner.py`,
`scripts/search_params.py`, `scripts/battle_contested.py`.
