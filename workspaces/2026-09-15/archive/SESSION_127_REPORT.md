# SESSION 127 — Tue 2026-09-08 ~18:15 UTC
## "Use the tapes we built" → what the tapes actually gave us

**LIVE:** 56079632 router **2483.7** (peak 2550.2) · 56100058 resubmit climbing · quota 3 left, lifetime 70.
**NO POSTS this session** (per mandate). All gates local.

---

## What was tested (in order)

| # | Experiment | Result | Verdict |
|---|-----------|--------|---------|
| 1 | **Verbatim elite-tape replay** (keiz, same seed, vs PASS) | **$35,455** vs $81,546 original | FALSIFIED — death cascade instrumented |
| 2 | Tape + late-day feed safety layer | **$35,106** | FALSIFIED — cascade starts at money (d10), not feed |
| 3 | **v30** full elite-schedule port on v28 engine | $4.6k/$70.9k/$4.1k → fixed → $65.1k mean | Underperforms — their schedule assumes their labor |
| 4 | **v31** = v28.21 skeleton + engine-agnostic elite deltas | **$79.5k mean** (76.6/81.0/91.7/78.6/69.4) | **INSTALLED — parity + elite patterns embedded** |
| 5 | v31 H2H vs champion (10 seeds, seat-swapped) | 0-10, $32.3k vs $140.2k | Champion still untouchable |

---

## The tape autopsy — exactly why foreign replay dies (this is the asset)

Instrumented daily (money/herd/unfed/shed/carry) on keiz_105559878:

1. **d10:** our money diverges −$600 from taped money (no opponent = different market fills). Small.
2. **d10→12:** the tape's next BUY fails (insufficient cash). One missed buy.
3. **d12→15:** the animal/seed that buy would have placed is absent → taped PLACE actions target empty tiles (silent no-ops) → **placement shifts**.
4. **d15→17:** taped FEED/PICKUP actions land on tiles that no longer hold what the tape expects → **9 animals unfed all day, herd 13→10→4→0**, shed wheat 24 stuck (no pickup).
5. Result: $35k, stable but crippled.

**Why the safety layer failed:** by d15 the tape's hands are *busy doing wrong-position work*, not idle — there are no spare PASS-slots to redirect, and the money/placement divergence upstream means every downstream labor op misses. You cannot patch layer 4 when layers 1-3 are already broken.

**Conclusion (3rd falsification, final):** foreign tapes are **schedule gold, playback poison**. Their value is the decoded day-by-day plan, not the action stream.

## v30 crash — root-caused & fixed

The $4k collapses were **over-hiring**: our formula sized hands from tiles (22 tiles → 10 hands, $143/day fib) while cash was $26 (d0 all-in spends $2,840 of $3,000). Hands hit 0 by d8, weeds ate the farm. Elites run **4-5 hands until revenue starts**. Fix (early-hands cap 5 pre-d8 + animal-buy cushion $600 pre-d10) → $62-68k stable. But their 58-tile/zero-waste schedule can't run on our 45-tile/55%-walk planner → below our $79k.

## v31 — elite deltas that ARE engine-agnostic (new build, topbots/v31_elite_delta.py)

On v28.21: **fert dump-all** (keep 2, not 12 — frees ~$700/day), **carrot late waves d22-26** (6/day, target 10 late), **melon 12 at d0**. Solo $79.5k = parity with v28.21, better tail, simpler. H2H unchanged (0-10) — expected: these are economic deltas, the gap is labor.

---

## Where this leaves the fight

The tape work confirmed the binding constraint from a 4th independent angle: **labor efficiency**. Elites run ~58 productive tiles; our planner wastes 55% of steps walking and caps at 45. Every economic schedule we port onto it lands at $65-80k solo and $30k H2H. The champion's taped action streams never waste a step.

## Next (concrete, in order)

1. **Mine top16_tapes.tar.gz** (21 agents, still unmined) — extract day-schedules, cluster archetypes, find one structurally different from ours (e.g. Dusta's wheat trading desk).
2. **Record OUR OWN tapes** (v31 self-play, all seeds) + offline optimization (tree_lock harness) — the only tape architecture that survives replay, because the tape's market/placement assumptions match our agent. Optimize the walk graph, not the plan.
3. If labor gap closes → re-run the elite schedule port (v30 line) on the faster planner.
