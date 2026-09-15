# SESSION 118 — The #1's Model, Read — And How Our Current Fares Under It

**Time:** 2026-09-07 ~16:05 UTC · User: "Go ahead and read it and see how it fairs vs our current."

---

## What the #1's kernel actually is

3Jeonghoon's (#1, 2848.7) notebook = a full market-settlement reconstruction toolkit:
unit-by-unit fill accounting, partial fills, the market-queue mechanics ("corresponding
positions in both players' order lists process together; a sale quotes before adding the
unit; floor sales add no inventory"), and per-product supply curves. Its demo agent is
deliberately simple — **0-12 vs our pair (−$77-97k/game)**, as the notebook itself states.
The value is the MODEL.

## The model's core table (computed on our engine — the strategic map of the game)

| product | base | units → half price | units → $1 | price at I0+T |
|---|---|---|---|---|
| **WHEAT** | $25 | **>1500 (never)** | **>1500** | $20 (80%) |
| **EGG** | $50 | **>1500 (never)** | **>1500** | $40 (80%) |
| FERTILIZER | $100 | 249 | 494 | $60 |
| CARROT | $35 | 231 | 843 | $10 |
| TOMATO | $60 | 136 | 530 | $24 (40%) |
| MELON | $250 | 113 | 159 | **$1** |
| STRAWBERRY | $120 | **32** | **63** | **$1** |
| MILK | $160 | **39** | **77** | **$1** |
| WOOL | $200 | **43** | **60** | **$1** |

**Wheat and eggs are the only uncrashable products.** Strb/milk/wool/melon floor at tiny
volumes — a single farm's production crosses their cliffs alone.

## How our current fares under the model

- **v16 (blob): structurally mirror-fragile.** Its pillars — strb ~200u, milk 177u,
  wool 100u, melon 60u — are ALL past their $1 cliffs at our own production volume.
  It survives on drip-selling + town drain, but any twin dumps the same four products
  simultaneously → both floor → the $37-77k crash games. That's the measured 55 losses.
  Only its wheat ($41k) and fert ($11k) lines are model-sound.
- **TT router: model-correct by construction.** 3-5 geese (the EGG floor) + 24 wheat
  (the WHEAT floor) + adaptive routing of the crashable tail. Live evidence: **1745.5
  in ~40 minutes** after going active (v16/v4b needed ~4 hours to that level).
- **v16: 1939.2 and climbing** — still our floor.

## The model's directive (next tuning, in order)

1. **More geese** on the router's profile (CD ran 7G — eggs at 80% price retention,
   $300 animal, yields from d4 daily — the best riskless asset in the game).
2. **Tomato over melon** ($24 vs $1 at volume) — router's tapes decide this.
3. **Volume discipline on strb/milk/wool** — sell early, sub-cliff dribbles only.
4. The market-queue law kills any "order consolidation" idea (per-unit quotes update
   within orders too — the split doesn't matter; checked against the notebook's
   replay mechanics).

## Live board
- 56079632 TT router: **1745.5 @ 40min**, climbing fast
- 56069472 v16: 1939.2, climbing (our floor)
- 2 slots in reserve today
