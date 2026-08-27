# Session 14 — 8-20-2026: the crop-volume pass — done, with one decisive find

## What you asked for: close the crop gap to the v25 tape

The tape sells 114 melons + 285 strawberries (~$64k); we were selling 36 + 12
(~$5k). This pass attacked that gap and found the real reasons along the way.

## The decisive find (measured, not guessed)

I instrumented v25 to see what its crops are actually WORTH:

| | v25 units | v25 revenue | avg price |
|---|---|---|---|
| MELON | 114 | $26,838 | **$235** |
| STRAWBERRY | 285 | $36,900 | **$129** |
| MILK | 218 | $57,507 | $264 |

Two consequences that changed the bot:

1. **The town absorbs the glut.** Strawberries at 285 units still sell for
   $129 because the town's shops eat them. My `GLUT_DISCOUNT` was valuing
   melons/strawberries ~2x too low (0.55/0.6 instead of the real ~0.85/0.8),
   which is why they never got planted. Fixed.

2. **The town shop mix decides which animal product holds value.** Seed 1 has
   4 milk shops → milk $55.7k. Seed 6 has 4 YARN stores → milk crashes to $1
   and we lost $42k on that seed. Fix: **town-driven herd sizing** — cows on
   milk towns, sheep on wool towns, geese on egg towns, balanced elsewhere.
   Seed 6 went $42k → $68k.

## Changes made this pass (each measured)

1. Crop valuation: realistic glut discounts (melons 0.85, strawberries 0.8).
2. Seed windows: melon 14→19, strawberry 8→13; rebuys 2→4 seeds; bought in
   **window-urgency order** (strawberries first, they expire soonest).
3. **Fertilize pass** — strawberries fertilized on their production days
   (doubles each tick): ~7 units/seed, matching v25's 7.5. This was entirely
   missing before.
4. **Harvest-at-full-yield** — melons now harvest at age ~10 (full 6 units)
   instead of waiting for max_day 12.
5. **Field-fill hiring** — the hire decision now covers the whole field, not
   just must-do chores.
6. **Global round-robin crop work** — balanced load, no idle hands while
   others max out.
7. **Town-driven herd sizing** — the biggest single win (above).

## Final measured results

**Solo (10 seeds):** $70,636 avg (min $48.7k, max $83.8k). Variance much
tighter after the town-herd fix.

| Opponent | before this session | now |
|---|---|---|
| cowbot (14 cows) | +$4.0k | **+$16.7k, 6W-0L** |
| goosebot (10 geese) | +$38k | **+$25.7k, 6W-0L** |
| sheepbot (12 sheep) | +$10k | +$7.7k, 4W-2L |
| mirror (v2 clone) | ~$0 | −$1.4k, 3W-3L |
| cropbot (melon/straw mass) | −$3.6k | −$3.5k, 3W-3L |
| **v25 tape** | −$99k | **−$82k** |

## The honest remaining gap (and why)

vs the v25 tape we closed from −$99k to −$82k — real progress, but still
losing. The reason is now fully diagnosed, not guessed:

- Our herd income (~$50k) is close to v25's (~$105k animal revenue, but v25
  also spends more on feed).
- Our crop economy (~$15k) vs v25's (~$64k): we plant ~9 strawberries + ~13
  melons to v25's 38 + 22.
- The binding constraint is **labor**: 14 animals × 4 chores = ~56 scattered
  walks eat the whole crew (measured: all 10 workers maxed at 24 turns, zero
  capacity left for 66 empty tiles). The tape batches its animal chores into
  one sweep per worker; my attempt at that batching regressed (milk 191→48)
  and was reverted. That single refactor — **efficient animal-chore batching
  (animals pastured in a tight cluster, one sweep per worker)** — is the
  remaining lever to plant the other ~40 crops.

## Files
- `main.py` — the bot (1,316 lines, stdlib only). Solo beats v2 by $4k; beats
  cowbot/goosebot/sheepbot; adapts its herd to the town and the opponent.
- `agent/decision_agent_v4.py` — the conservative safe submit (unchanged).
- `scripts/{sim,planner,rules,search_params}.py`, `scripts/battle_contested.py`.
