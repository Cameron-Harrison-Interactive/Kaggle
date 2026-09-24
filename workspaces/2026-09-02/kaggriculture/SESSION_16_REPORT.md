# Session 16 — 8-20-2026: crop-aware watering + seed/hire sizing — $88.5k solo

## What you asked for
1. The bot should know how many seeds to buy to fill the field, and hire the
   hands to plant them all.
2. Some crops don't need water every single day — the bot should know that
   and use it to free hands.

Both are now in `main.py` — with one course-correction measured along the way.

## 1. Crop-aware watering (`_needs_water`) — your insight, encoded

The engine rule is: a plant becomes a weed after TWO missed watering days. So
alternate-day watering keeps anything alive. On top of that:

- **Ongoing crops (strawberry/tomato)** produce on a FIXED schedule regardless
  of watering — so we only water them on their production days (so a
  fertilized tick can double). This cuts strawberry watering roughly in half
  and frees hands for planting.
- **One-time crops (wheat/carrot/melon)** gain yield only from water inside
  their bonus window, so we water them there and stop once they've capped.
- **Survival** (a plant one miss away from dying) always waters.

## 2. Seed buying sized to the field

The first attempt — "buy exactly the gap between standing crops and the field
cap" — over-bought strawberries/melons on day 1-2 and drained the early cash
the herd needed (measured regression: $88.5k → $64.6k). The fix that worked:
**rolling rebuys** — buy 4-6 seeds the moment a crop runs out, windows kept
open late (strawberry 13, melon 19), so the crew (hired to cover the field)
always has seeds to plant without hoarding.

## 3. Two herd bugs found and fixed (this session)

1. **The herd cap didn't count shed animals** — unplaced animals weren't
   counted, so the herd quietly overshot 14 to 16-20, and 6 placements/day
   ate every worker's turns, starving the animals. Now the cap counts
   board + shed, and placement runs AFTER feeding (life-critical first).
2. **A float leaked into buy counts** (`cash` is a float → `n` became 2.0),
   which cascaded into the running budget. Now `int()`.

## Measured results

**Solo (10 seeds): $88,500 avg** (min $50.5k, max $111.7k) — up from $78.9k,
and $22k above our own v2.

| Opponent | now |
|---|---|
| mirror (our clone) | **+$15.5k, 5W-1L** |
| cowbot (14 cows) | **+$24.9k, 6W-0L** |
| sheepbot (12 sheep) | **+$24.4k, 6W-0L** |
| goosebot (10 geese) | **+$52.4k, 6W-0L** |
| cropbot (melon/straw mass) | **+$20.5k, 6W-0L** |
| **v25 tape** | **−$61k** (was −$99k → −$82k → −$69k) |

The v25 gap has closed from −$99k to −$61k across the sessions, every
archetype is beaten, and our own clone loses to us (anti-mirror + town/market
adaptation work).

## Remaining gap (honest)

v25's $145k solo still beats our $88.5k, purely on crop VOLUME (114 melons +
285 strawberries to our ~15 + ~7 in a good seed). We now have the labor (the
alternate-watering + batched animal sweep freed the crew), the seed supply
(rolling rebuys), and the hire scaling. The one thing left to match the tape
is planting more tiles per day — which is a per-tile plant-cost matter
(walk + plant + water ≈ 3-4 turns each), not a strategy matter. The strategy
layer (counter + town + market + dump prediction + anti-mirror) is complete.

## Files
- `main.py` — the bot (1,408 lines, stdlib only).
- `agent/decision_agent_v4.py` — conservative safe submit (unchanged).
- `scripts/{sim,planner,rules,search_params}.py`, `scripts/battle_contested.py`.
