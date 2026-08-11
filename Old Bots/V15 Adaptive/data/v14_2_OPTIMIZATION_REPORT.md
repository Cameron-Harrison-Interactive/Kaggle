# v14.2 StepSaver — Wasted Steps Optimization

**Date:** 2026-08-09  
**Base:** HI_AgriBot_v14.1_TerminalSweep (v26 + TerminalSweep, 159k solo)  
**New:** HI_AgriBot_v14.2_StepSaver  
**Fixes missing `_v26_shed_access` bug + 2 runtime optimizers**

## What you observed in watch.py (screenshots verified)

### 1. Watering handoff — girl in NE quad passes thirsty crop
- Step 514 demo (day 21): hand at `[3,8]` waters empty `None`, hand at `[2,7]` waters empty, while thirsty tiles at `(7,0)`, `(0,2)` etc wait. Meanwhile a far male on top row walks 6 turns to water one CU1 wheat.
- Engine audit over 720 turns (seed 1, self-play):
  - total WATERs 1002, **wasted 426 (42.5%)**
    - 88 on empty/non-plant (water on `None`/weed)
    - 89 duplicate same-tile same-day (second worker waters same CU1)
    - 338 early CU0 waters (kept — these are yield-window waters for wheat, not waste)
  - moves 2868, waters 1002 → 2.81 moves/water
  - Our first aggressive optimizer tried to redirect all 515 “wasted” (including early CU0) → collapsed to $9k (crops -8, weeds +6, animals 12→5 by day 18, starved).

### 2. Far animal — cow at fence line (3,0)
- Day 21 turn 10-11: hand picks up COW at shed `[4,4]`, walks 6 steps north to `[3,0]` (dist to shed 5), `BUILD_PASTURE` then `PLACE` there.
- Dist to nearest shed-access tile: 5 (>3 threshold = far). That cow then needs 3×/day walks of +4 each vs central pasture (6,4) etc → ~12 extra steps/day × 9 remaining days ≈108 wasted steps.

## Optimizers added (safe, local, no tape rewrite)

All run **after** `_weed_repair_action`, before `_rank_sell_slots`. No market logic touched. Falls back to original on exception.

### A) `_shed_access` fix
Missing `_v26_shed_access` caused TerminalSweep to `except`→fallback to base every time at step 718. Now correctly defined (`_is_shed_adjacent`). Alone gives +5k vs v14.1_backup on seed 1 (102570 vs 97505).

### B) `_water_optimizer` (conditional, safe)
```python
thirsty = CU1 and not watered_today (must-water-today or dies tonight)
empty waste = WATER on not-PLANT → PASS
dupe waste  = WATER on watered_today or second worker on same thirsty → PASS
pass waste  = MOVE/PASS standing on thirsty AND not already reserved
           → only convert to WATER if:
               - no animal-needy within 3 tiles (fed_today/cared_today/fertilizer)
               - not carrying WHEAT (tender with feed)
```
- Keeps early CU0 wheat waters (yield bonus during day 2-4 window) → avoids collapse.
- Fixes the exact girl-pass case only when safe: girl at `[x,y]` thirsty, no nearby hungry animal, no wheat → `WATER` instead of `EAST`. Far male’s empty-water freed → `PASS`, not forced to walk 6.

Result (water only, seed 1): **+5224 vs v14.1** (102844 vs 97620), 0 extra weeds, 0 animal loss. Self-play 103k vs 97k.

### C) `_pasture_optimizer` (centralizes build/place)
```python
dist = Manhattan to nearest shed-access (4,4),(5,4),(4,5),(5,5)
if BUILD_PASTURE and dist>3:
   → step toward nearest empty `None` tile with dist≤3 (or PASS if none)
if PLACE and dist>3:
   → step toward nearest empty PASTURE with dist≤3 (or toward build site)
if carries COW/SHEEP/GOOSE and MOVE increases dist and dist≥2:
   → redirect toward central pasture/build
```

Result (pasture only, seed 1): **+2156 vs v14.1** (99844 vs 97688).

### Combined v14.2 (water conditional + pasture):
- Seed 1: **99870 vs 97762 (+2108 WIN)**, day 13-18 keeps 53 crops, 0 weeds, 12 animals (vs water-aggressive which dropped to 46c/7w/5a)
- vs starter: 130k vs 3.5k (smoke pass)
- Self-play: 100048 vs 97548

**Trade-off:** combined is +2.1k, slightly less than water-only +5.2k because pasture redirects occasionally compete with water proximity check. Still strictly beats v14.1 and fixes both user complaints. Keeping both is preferred for #1 push (far cow is user’s #2 complaint). If you want max raw score, water-only variant is in `/tmp/test_cond_water_only.py`.

## Screenshots mapped

- `Screenshot 2026-08-09 144311.png` etc (day 19 turn 10-22, day 22 turn 11/17): those are steps 354-358 and 539-545. Audit shows at 514 `waters at [(2,[3,8]), (3,[6,0])]` — the two empties are exactly the wasted waters you saw. Our optimizer now turns those two `WATER` at `[3,8]`/`[2,7]` (None) into `PASS`.
- Day 22 cow at `[3,0]` → now at step 514-515 the `BUILD`→`MOVE toward (4,2)` and `PLACE`→`MOVE toward (4,2)` instead of fencing, keeping the cow central.

## Artifacts

- `agent/main.py` → version `HI_AgriBot_v14.2_StepSaver`
- `submit/HI_AgriBot_v14.2_StepSaver.tar.gz` (23,392 bytes, sha 6f8c30…) — ready for you to post, **do not auto-submit**
- This report: `data/v14_2_OPTIMIZATION_REPORT.md`

## Next incremental steps (if you want more)

1. Run `watch.py` with v14.2 vs v14.1 (`python scripts/watch.py 1 agent/main.py` vs backup) to visually confirm girl now waters and cow stays central.
2. If combined score plateaus, try water-only variant for ladder (it scores higher raw but leaves far cow). We can make v14.3 that only centralizes *future* pastures after day 15 (keep early far pasture but move later ones).
3. Tune thresholds: animal-needy radius 3→2, shed dist 3→4, or allow early CU0→thirsty redirect within same quadrant only.

No Kaggle submit was done — you post when ready.
