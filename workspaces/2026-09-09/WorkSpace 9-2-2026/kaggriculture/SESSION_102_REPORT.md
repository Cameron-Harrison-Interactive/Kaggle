# SESSION 102 — building the new tape: author bring-up, 6 engine-contract bugs fixed

Goal: stop tuning v1112fr, get the *generated* tape line (spec -> full 720-step
tape) working so a composition search can actually run. Status: author went from
**bankrupt** to a solvent but small farm. Not competitive yet; the remaining
defects are now identified with evidence rather than guessed at.

Trajectory on seed 1 (spec: 4 sheep / 12 cows / 0 geese):

| state of the author | final cash |
|---|---|
| as inherited (`tape_author.py`, regenerated) | **$0** — bankrupt ~D16, hires stop |
| + H00 reserved for the market (bug 1) | $4,073 |
| + batched placements, spatial routing (bugs 2-3) | $17,442 |
| + land days sequenced to income (bug 4) | $11,015 (exposed bug 5) |
| + 10-order cap / late-hire lead (bug 5) | $15,523 |
| + feed supply = 1 wheat per animal per day (bug 6) | **$26,869** |

Reference: v1112fr = $179,265 on the same seed; the hand-repaired `v120_puretape`
(same design lineage) = $178,457. So the *design* can reach ~$178k; the generator
currently realises 15% of it.

## Bugs found and fixed (all engine-contract, all verified by replay)

1. **H00 belongs to the market.** Orders commit at the END of the hour they are
   issued, and a hand hired at H00 only exists at H01. The author's routes started
   real work at H00, so every unit lost its first action and D0 `PICKUP SHEEP`
   ran before the sheep existed. Fix: every unit route now starts with a PASS.
2. **Animals were bought at H01** (same hour as the pickup) — pickup always failed.
   Fix: `BUY_ANIMAL` moved into the H00 block.
3. **One shed trip per animal.** Placement cost ~8 actions each and overflowed the
   day (200+ actions/day dropped). Fix: one shed trip per unit, batched
   `PICKUP <kind> n`, then build/place/feed nearest-first.
4. **Land days were fixed at D5/D6** and unaffordable ($1,000 with $300 in hand),
   so NE/SW stayed LOCKED all game — 75 locked tiles, and every duty on them was a
   no-op the units still walked to. Fix: `ne_day`/`sw_day` are spec knobs, and melon
   batches, the SW wheat block and animal placements all derive from them.
5. **The 10-orders-per-turn cap silently ate the buys.** With 12 hands, H00 was
   12 HIREs, so BUY_LAND/BUY_SEED/BUY_ANIMAL were truncated away. Fix: buys are
   emitted first, hires fill the remaining H00 slots, the overflow hires at H01 —
   and those hands get a 2-hour lead-in so their walk stays in sync.
6. **Feed starvation.** Wheat purchases were a fixed 4-10/day for 16 animals, so
   FEED failed and animals escaped (D20 census: 1 cow + 1 sheep alive of 16).
   Fix: buy `n_animals + 2` wheat per day.

Also: duty assignment is now a spatial snake partition (contiguous zone per unit)
instead of round-robin, which cut walking enough to triple output on its own.

## Remaining defects (measured, next block)

* **SW is never funded** — at $2,000 it needs the melon wave, which is late; the
  farm runs the whole game on NW+NE (50 tiles locked).
* **Animals still escape** — D29 census shows empty PASTUREs; the per-unit wheat
  pickup happens once per day before duties, so a unit with more feeds than carried
  wheat starves its tail-end animals.
* **Wheat piles up unsold** (88-96 units in the shed at D29) — the sell schedule is
  a fixed `SELL WHEAT 4`/day; it needs to track production.
* **Melon cycles lose tiles to weeds** (5-6 WEED tiles standing at D29) — the
  author DIGs only on plant day.
* Best hands setting so far is 8; higher counts starve cash because the sell side
  is too weak to pay the fib ladder.

## Tools

`_ref/tape_author2.py` — spec-driven author. `TAPE_SPEC` env:
`{"SHEEP":n,"COW":n,"GOOSE":n,"hands":n,"ne_day":d,"sw_day":d,"ramp":[...]}`,
GOOSE/coop/egg support included. `TAPE_VERBOSE=1` prints per-day dropped actions.
`_ref/sweep_comp.py` — builds and scores any list of specs (~1 s/game).
`_ref/diag_tape.py` — per-day cash / hands / shed trace for a spec.

The composition sweep is written and runs; it stays parked until the author clears
a solvency gate (default spec ≥ $150k on seeds 1-3), otherwise it would just rank
broken farms.
