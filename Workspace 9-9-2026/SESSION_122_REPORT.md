# SESSION 122 — The 2900 Build Begins: Engine Fully Decoded, v28 Harvest Moon v0.1 Alive

**Date:** 2026-09-07 late night UTC · Directive: "We should be hitting the 2900 bracket. We need to win."
**No submissions made** (per standing rule). Router 2550.2 (rank 200/8087), v16 1915 bleeding 10W-16L.

## What happened
1. **v16 diagnosed:** last 26 games 10W-16L; all 5 decoded beaters are router-class (~280 hires, 9C/8S herds).
   The twin army owns the field (244 teams in 2400-2600 band); any non-router blob bleeds. Slot-B twin candidate
   built and gated (0W-3L-17T = exact control mirror) but held; user redirected to the 2900 target.
2. **The elite class decoded from live replays** (ymg_aq 2955: 11W-3L vs top-10, +60k blowout of 3Jeonghoon):
   tomato is the uncontested scarcity rocket ($531/unit day 28 — nobody in the meta grows it), milk $230 late,
   wheat carry $29→$49, wool $1 without YARN (they starve sheep deliberately), endgame liquidation = $92k in final 6 days.
3. **Engine source fully decoded** (exact price curves, crash thresholds, shop-drain rates, feed/care/fert mechanics,
   random shop unlocks). See analysis/ELITE_ENGINE_DECODE_0907.md — this is the moat.
4. **v28 "Harvest Moon" built from scratch** (topbots/v28_harvest_moon.py): market brain + reactive labor planner.
   Debugged through 8 iterations: animal-pipeline deadlock, feed starvation, cash-flow death spiral, PLANT atomic
   validation, walking waste. Solo: $2k → $23k (seed 101). Anatomy: milk from d8, tomato waves d13+, $3-4k/day late game.

## Where v28 stands vs the 2900 class
- ymg: $166k (vs 3Jeonghoon's $106k). v28: $6-23k solo. Gap = 5-8×, causes identified and ranked:
  1. Late-feed bug: cows die after d23 (8→4) — each dead cow loses $150-250/day of $230 milk.
  2. Early cash thin: herd completes d18 vs ymg d7 (missing the wheat intraday float + geese scaling).
  3. Labor efficiency ~50% walking (needs mower zoning).
  4. Tomato scale 22 vs their staggered waves + fert coverage.

## Next session plan
Fix late-feed; add wheat float; scale tomato+fert; re-test solo ($50k+ target) → H2H gates (router, v16, ant-tape, ymg-tape extraction) → 100k+ → then submit with explicit go.

## Live
Router 56079632: 2550.2 (all-time best). v16 56069472: 1915 (falling; replace candidate ready). Top LB: ymg_aq 2955.6.
