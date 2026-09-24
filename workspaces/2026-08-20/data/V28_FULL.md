# v28-full — compiler economy-variant search (2026-08-14)

## Goal
Generate a wheat-machine economy variant ON the v25 tape using the route
compiler's variant machinery (the "v28-full" project), with hard gates.

## Machinery used (route_compiler_v19)
- record_reference: records the v25 agent's live play vs PASS (all runtime
  layers baked into the recorded tape), extracts plants/anchors/spawns.
- FAST-PATH variants (no movement rebuild — the proven tape is patched):
  leftover_harvest (harvest end-game wheat with idle labor), sell_split,
  idle_water (water with idle steps), feed_buffer, feed_stagger.
- REBUILD variants (movement re-planned by plan_day):
  early_plant (move late SW-strip wheat PLANT anchors to their first visit —
  the "missing row planted a month late" fix), plant_fill (new wheat on
  visited-but-empty tiles), feed_repair.

## Gates
- PASS (validate_tape, seeds 1-2, both seats): reward >= v25_base − 1000,
  animals_alive >= 12, missed_water <= base + 2.
- keepgate vs v25 raw tape (identical wrapper, seeds 1-2 both seats):
  wins >= 5/8 AND avg >= +500.
- Survivor battery: seed-3 PASS + contested v20/kaito (>= 7/8 not worse
  than v25 by > 500) + 3 recorded-replay spots (sum >= −1500).

## Results (all 10 variants tested, search completed)

| variant | recompile | PASS | keepgate | verdict |
|---|---|---|---|---|
| F_lh1 | no | ok | 3/8, +120 | reject |
| F_lh3 | no | ok | 3/8, +120 | reject |
| F_split | no | FAIL | 0/8, −22,162 | reject |
| F_lh1split | no | FAIL | 0/8, −22,162 | reject |
| F_idle | no | ok | 3/8, +120 | reject |
| R_early4 | YES | FAIL | 0/8, −50,455 | reject |
| R_early6 | YES | FAIL | 0/8, −50,270 | reject |
| R_early4lh | YES | FAIL | 0/8, −50,455 | reject |
| R_fill2 | YES | ok | 3/8, +120 | reject |
| R_all | YES | FAIL | 0/8, −38,922 | reject |

**SURVIVORS: 0**

Failure mechanisms (verified in the per-game stats):
- sell_split: the split batch lands 6 steps later on an empty shed →
  wasted order slots → −22k.
- early_plant family: PASS reward −41k AND **animals 13 → 7** — moving the
  PLANT anchors makes plan_day rebuild the day plans, and the rebuilt
  movement breaks the FEED/PICKUP choreography (the herd starves while the
  workers do the new plant/water jobs). Watering itself stays perfect
  (missed water 0) — the fragile part is FEEDING.
- plant_fill / leftover_harvest / idle_water: pass every gate but beat v25
  by only ~+120 avg (3/8 wins) — end-game wheat is already collected by
  the tape, idle units rarely stand on useful tiles.

## Verdict
The route compiler's economy-variant machinery, exercised end-to-end with
hard gates on the v25 tape, cannot beat the proven tape:
- fast-path surgery = noise (+120)
- any movement rebuild = broken feeding = −40k..−50k

This is the same conclusion the supersearch / three-fer / melon4 tracks
reached: **v25 is a strong local optimum of its architecture** (tape +
guards). The measured +$30k/game gap to the #1 economy needs a
fundamentally different generator — a Shabby-Farm-style commitment/ledger
planner or a full search over economy structure (herd size, feed routing,
shed cycling) — i.e. a multi-day offline build, not a compiler-flag sweep.
v25 Wheat16 remains the post. All evidence saved in data/v28full/.
