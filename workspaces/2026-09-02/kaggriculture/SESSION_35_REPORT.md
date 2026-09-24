# SESSION 35 — Field density fix (your "empty dirt spots" callout)

## You watched the replay and called out: "we have empty dirt spots the whole game"

**You were right.** I traced our seed-1 game vs bea and measured field utilization per day:

| day range | tiles owned | plants | EMPTY | utilization |
|-----------|:-----------:|:------:|:-----:|:-----------:|
| D0-D12 (NW only) | 25 | 13-17 | 0-8 | 68-100% |
| D13 (buy NE) | 50 | 16 | **25 fresh empty** | 50% |
| D14-D17 | 50 | 21-30 | 6-15 | 66-84% |
| D18 (buy SW) | 75 | 29 | **31 fresh empty** | 55% |
| D19-D23 | 75 | 25-37 | 21-37 | 49-64% |
| D24-D29 | 75 | 5-14 | **41-57 EMPTY** | **23-35%** |

By D25-D29 **more than HALF the field is dirt.**

## Root cause

We had **too much land, not enough production**. The 3rd quadrant (SW) unlocks at D17 and adds 25 more tiles, but:
1. Meta-line opponents out-plant us so heavily that our workers can't keep up with watering + animal chores + replant across 3 quadrants
2. After D18 (`terminal_day`) the main hour-1 buy block STOPS — so no new WHEAT seeds get bought. Melons and wheat get harvested and the tiles go dirt with nothing to replant

## Shipping Change 1: cap meta-line at 2 quadrants (NW + NE)

Line 1710 in `_decide_market`:

```python
# Session 35: on meta-line opponents, cap land expansion at 2 quadrants.
# Bea/Lena/Silas out-produce us so heavily that a 3rd quadrant just
# leaves 25-60 EMPTY tiles from D18-D29 — the workers can't keep up.
# Skipping SW keeps our 50 tiles densely filled (util 74-84% D18-D24
# instead of 32-64%) and saves $2000 that goes to seed rebuys.
if quad in ("SW", "SE") and self._meta_line_opp:
    continue
```

Measured N=40: **+$7,679 sum-margin** (bea/lena/silas/cleo). US absolute avg: $55k → $59k.

## Shipping Change 2: late-game wheat replant keeper

Line 1728 in `_decide_market`, fires at hour 6 (no market conflicts):

```python
# LATE-GAME WHEAT REPLANT KEEPER (Session 35, meta only)
# After terminal_day (D18) the main hour-1 buy block stops.  But crop
# tiles empty as harvests finish (plants D19→D25 goes 37→6).  The
# harvest->replant loop needs WHEAT seeds in the shed to keep tiles
# filled; without them, the field goes to dirt D24-D29.
if hour == 6 and self._meta_line_opp and day >= 18 and day <= 25:
    wseeds = int(seeds.get("WHEAT", 0) or 0)
    n_empty = len(board.get("empty_set", set()))
    if wseeds < 4 and n_empty >= 4 and money >= 200 and len(orders) < 10:
        n = min(4, n_empty - wseeds)
        orders.append(["BUY_SEED", "WHEAT", n])
```

Additional **+$1,052 sum-margin N=40** on top of the 2-quad cap.

## Combined result vs meta-line (N=40)

| opp | pre-Sess35 | after Sess35 | Δ |
|-----|-----------:|-------------:|---:|
| broker_bea | -$50,580 | **-$48,586** | +$1,994 |
| ledger_lena | -$50,564 | **-$48,446** | +$2,118 |
| slotter_silas | -$50,862 | **-$48,737** | +$2,125 |
| closer_cleo | -$53,089 | **-$50,595** | +$2,494 |
| **SUM (N=40)** | **-$205,095** | **-$196,364** | **+$8,731** |

**Best game ever: -$761 vs lena, -$962 vs bea** — closer than any Session 34 result.

**US absolute money: from $55k → $59.5k avg** (+$4.5k in absolute earnings each game).

## Field utilization comparison

Same seed 1 vs bea:

| day range | BEFORE (3 quads) | AFTER (2 quads + wheat keeper) |
|-----------|:----------------:|:------------------------------:|
| D18-D23 | 49-65% util (21-37 empty tiles of 75) | **72-82% util** (4-8 empty of 50) |
| D24-D29 | 23-35% util (41-57 empty of 75) | 36-72% util (6-32 empty of 50) |

## Non-meta bots + solo unchanged (both changes are `_meta_line_opp` gated)

- sheepbot +$41,202 (10W/10) · goosebot +$57,977 (10W/10) · mirror +$40,462 (10W/10) · cropbot +$54,477 (10W/10) · cowbot +$30,419 (10W/10)
- SOLO N=10 avg $101,417 · `main.py vs PASS seed 1: $105,120`

## Cumulative gain across Sessions 33-35 vs meta-line

| session | sum-margin (N=40) | Δ |
|---------|------------------:|--:|
| pre-Session 33 | -$218,436 est | — |
| after Session 33 | -$211,760 | +$6,676 |
| after Session 34 | -$205,095 | +$6,665 |
| **after Session 35** | **-$196,364** | **+$8,731** |
| **TOTAL** | | **+$22,072** |

## Also tried (measured, not shipped)

| attempted | outcome |
|-----------|---------|
| Late-game WHEAT+CARROT fill at H1 (before shipped version) | -$10k (displaced sells at slot cap) |
| Same but at H6 with big batches (8 seeds) | -$46k (extra labor cost > yield) |
| terminal_day 24/26/28 on meta | -$25k to -$62k (too many buys) |
| NW ONLY (1 quadrant, no NE) | -$32k (severely underscaled) |
| Cow herd +2 on meta | -$14k |
| Sheep herd +2 on meta | -$15k |
| Goose ramp to 4 on meta | -$6k |
| Extra wheat batch 6 on top of keeper | -$0.8k |
| Add CARROT fill D22-D25 | -$0.5k |

## Structural findings from the deep trace

**Workers are BUSY not idle late-game:**
- D21 with 3 quads: 14 workers, 27 empty tiles, only 6 wheat seeds available
- Planner would hire more workers if seeds available, but seed BUY was gated by `terminal`
- Each worker's day is 24 turns; animal chores (PICKUP+FEED+COLLECT+CARE) alone consume ~8 turns/worker across shed round-trips
- Leaves ~16 turns/worker × 14 workers = 224 crop turns/day, minus movement
- 3 quadrants × 5 tiles per quad-row wide × walking cost eats the rest

**The 2-quad cap:**
- 50 tiles is exactly what our worker pool can maintain at high density
- Bea has 12+ workers all game (we peak at 14 late); her tile count is 75 but her worker density per tile is higher earlier due to different opening
- Skipping SW = save $2000 land + labor for extra tiles
- The wheat keeper fills the SW hole via replant of NW+NE harvests

## Ideas for next session

1. **Adaptive quad decision** — buy SW only if avg worker slack > 5 turns/day
2. **Preferentially replant with STRAWBERRY** (higher $/tile) instead of wheat when strawberry seeds available late
3. **Move the wheat keeper earlier** — currently H6, might benefit from H3 or H12 depending on when the harvest+replant loop needs to see it
4. **Investigate why absolute US money jumps but margin doesn't close as fast** — Bea's ceiling scales with land too

## Files
- `main.py` (2 shipped changes marked `Session 35`)
- `watch.html` refreshed (vs V25 tape)
- `SESSION_35_REPORT.md` (this file)
