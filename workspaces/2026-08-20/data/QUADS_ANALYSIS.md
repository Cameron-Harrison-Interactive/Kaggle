# The Quad Question — land analysis & SE-flood experiment (2026-08-14)

User's idea: "open up the 4th quad? Or even just running 2 quads?"

## Engine land rules
- LAND_ORDER = ["NE", "SW", "SE"]; LAND_PRICES = [1000, 2000, 4000].
- Our tape: NE at d6h16 ($1k), SW at d10h0 ($2k). **SE ($4k) never bought.**

## Measured tile utilization (v25 vs idle, seeds 1 & 3 — identical shape)
| day | quads | plants+animals used | free |
|---|---|---|---|
| d9-10 | 2q | 48/50 | 2 |
| d12-27 | 3q | **74-76 / 75** | **1** |

**The farm is at 99% capacity for 16 straight days (d12-27).** The tape
buying SW at d10h0 is what keeps the d11 strawberry wave alive; and the
d20-26 wheat flood buys ~84 seeds (~$840) with only 1 free tile to plant
them on — seeds we pay for and never use. (This is the same mechanism as
the v24 "missing crops" losses, but self-inflicted: the tile budget is the
ceiling, not the seed budget.)

## Phase 1 tests (tape edits, PASS seeds 1-3 both seats)
- **2 quads (drop SW)**: seed1 −$28,323 / −$51,308 (7 escapes); seed2
  −$44,240 (7 esc); seed3 −$36,868 / −$22,958 (7 esc).
  → the strawberry wave + flood starve; escapes. **2 quads = catastrophic.**
- **SE unlock only (no planting program)**: seed1 −$6,532/−$396; seed2
  −$2,614; seed3 **+$9,432 / +$11,307**.
  → land alone is mostly a dead $4,000; the +9k on seed3 is rng-stream
  drift (more unlocked tiles → more weed draws → different shops/weeds for
  the whole game), i.e. a seed-lottery re-roll, NOT a reliable edge.
  (We NEVER key on that: adaptation must come from observable state.)

## Conclusion so far
- The tile ceiling is real and is THE reason our d20 flood wastes ~84 seeds.
- Opening SE only pays if we ALSO plant it. The tape's choreography never
  enters SE, so the SE program needs the compiler: unlock SE at d12h01
  ($4k), plant 12-24 wheat tiles d20-22, daily water, harvest d26,
  rebuild ONLY d20-29 (splice d0-19 = byte-identical, feeding safe).
- Expected: +~$4-7k gross wheat at the d27-29 flood prices vs $4k land.
  Shed cap (100) is the second constraint — d28-29 sells drain ~200 units,
  and the terminal sweep monetizes whatever survives the cap.

## Phase 2: compiler SE-flood variants — BUILT, TESTED, CLOSED

Added a full `se_flood` variant to the route compiler (unlock SE at d12h01,
plant N wheat tiles d20-22, daily water, harvest d26-27, rebuild ONLY
d20-29 with splice). Two engineering bugs fixed along the way (inverted
splice semantics; global-vs-local anchor hours), then the anchor-placement
debugger gave the answer:

**The tape's d20-27 labor is FULLY PACKED.** Per-day recorded anchors:
d19 166, d20 164, d21 156, d22 124, d23 185, d24 143, d25 149, d26 168,
d27 120 (15 workers x 24 steps = 360 slots/day; anchors alone eat ~half,
walks ~150 more). Every worker's last anchor lands at h21-23 and the
mid-day gaps are all smaller than the round-trip to even the nearest SE
tile (verified gap-by-gap: need d_in+d_out+2 >= gap; best available gap
is 5-7 steps vs required 7-10). → **0 of 24 SE tiles placeable.** The
compiled variant plays byte-identical to land-only (reward 138,827,
animals 13, 0 missed water).

## FINAL VERDICT — the answer to "open the 4th quad?"
1. **Your instinct was right: land IS the binding constraint.** The farm
   runs at 74-76/75 tiles for 16 straight days (d12-27); the d20 flood
   buys ~84 wheat seeds that have no tile to go to.
2. **But the economy is TRIPLE-constrained**: tiles (99% full) + labor
   (d20-27 fully packed, no feasible windows) + shed (80-96/100 through
   the flood). Opening SE without re-planning all three is a dead $4,000
   (tested: −$2.6k..−$6.5k; the +$9k on seed 3 is rng-lottery drift, not
   strategy — new weeds/shops from the unlock shift the whole game).
3. **2 quads is catastrophic**: −$28k..−$51k + 7 escapes — the SW buy at
   d10h0 is exactly what keeps the d11 strawberry wave alive.
4. **The real fix is an economy redesign, not a land purchase**: the +$30k
   gap to the #1 player is precisely this — their economy plans land,
   hands, feeding AND shed-cycling together from day 0. That is the
   commitment/ledger planner project (the "Shabby Farm" class). The
   compiler's anchor machinery cannot express it on a saturated tape
   (proven end-to-end: every approach tested, every one gated, all
   rejected with numbers).

---

## Addendum (2026-08-15): the "drop 1-2 animals to free hands" experiment

User's Holy Grail idea, tested in both halves with the engine as judge.

### Animal map of the v25 tape (seed 1): where the herd lives
- 4 sheep d0; cows placed d0, d5, d6, d7×3, d8 — and **two cows bought
  d8/d12 that SIT IN THE SHED for 9-13 days and are only placed at d21**
  ((3,0) and (7,3) pastures) → 0-1 milk total (first yield = day+8 = d29).

### Half 1 — drop the buys (choreography untouched)
| Variant | PASS seeds 1-3 both seats | Contested (v20/kaito, seeds 1-2) |
|---|---|---|
| Drop d12 cow | **−$1,962 .. −$2,717** | mixed |
| Drop d12 + 1× d8 cow | **−$3,539 .. −$4,868** | ±$1-3.6k, no consistent edge |
| Drop d5 cow (early milk cow) | **−$4,819 .. −$13,759** | — |

Mechanism (traced step-by-step, seed 1): the drop is NEUTRAL through
d29h0 (+$147 — the $400 saving ≈ the cow's in-game value), then the
final 3 steps invert it: the terminal sweep sells **27 vs 15 wheat** and
the drop run ends with **12 wheat stranded in the shed** (worthless —
reward = money only). The late cows' shed slots + d21 placements are
load-bearing for the flood's final sell chain. The early cow is even
more valuable (milk d13-29 ≈ 9 units × $45 ≈ $405 vs the feed wheat's
real flood-time opportunity cost). **The animals are priced in — every
one of them.**

### Half 2 — free the hands (choreography pruning, offline gap analysis)
- Pruning one cow's ENTIRE daily choreography (66-70 FEED/CARE/COLLECT
  anchors removed from the record):
  (2,4) cow → SE windows 0/24 PLANT, 3/96 WATER
  (5,4) cow → **2/24 PLANT, 9/96 WATER**
- The freed labor sits at the cow's tile near the shed at hours that
  don't form SE-sized windows; a 2-tile SE program (≈$228) can't pay
  for the $4,000 land anyway.

### Verdict
Dropping animals loses at every point (late: −$2-5k; early: −$5-13.8k;
freed labor: 2/24 windows). The economy is a coupled system — milk,
feed wheat, shed slots, and the end-game sell chain all interlock, and
the compiler's local optimum prices every piece. Single-axis edits are
closed for good; the only measured big win stays the wheat opening
(v25). The remaining Holy Grail path is the portfolio search: coherent
multi-axis redesigns (herd mix, field size, shed cycling) evaluated by
the ledger — the build already started in scripts/ledger_planner.py.
