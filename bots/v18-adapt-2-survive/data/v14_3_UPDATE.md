# v14.3 FeedFix + HarvestPass

**Base:** v14.2 StepSaver (+2108 vs v14.1 on seed1)
**New:** v14.3 FeedFix (+1350-2108 range, still winning)

## Your watch.py observation
- Both left wheat on field (v14.2 left 7, v14.1 left 9 at step 720, each yield 2, planted day26). Not a bug — those wheats planted day26 become harvestable day28-30, price at end is $1-5, leaving 5-9 is < $100. v26 tape intentionally leaves late wheats to focus on selling high-value (milk/wool/straw/melons).
- Winner 8c/4s (12 animals) with 1 cow escape day23: our v14.2/14.3 ends 11 animals +2 cows in shed (blocked far placement). Far pasture at (3,0) built day21 is the one you flagged. Our optimizer now:
  - **keeps far BUILD** (so pasture count stays 14) but **redirects PLACE** at far → step toward central empty pasture if one exists, else keeps far (fallback). At day21 central has no empty (all 12 pastures full), so we leave far empty and keep 2 cows in shed — that's 11 placed +2 in shed =13 total vs 14 placed. Net -1 animal but +$2k because walking saved > milk lost. If you want max animals, we can force far placement (keep original) — tell me.

## What changed in v14.3
1. **Feed/Collect guard** (safe): only converts `PASS` on animal tile with `fertilizer_available` → `COLLECT` or `consecutive_unfed==1` + wheat in inv → `FEED`. No WATER/MOVE stolen, so no crop death. Did not change animal count in test (still 11) because those PASS cases never occurred.

2. **Harvest pass-only** (day≥27 only): `PASS` on plant with `yield>0` and not thirsty → `HARVEST`. Reduces end wheat from 7→5 on seed1. Very conservative — does not touch `WATER` on thirsty (so weeds stay 1 vs 2).

Combined keeps 99k vs 97k win. If you want zero wheat left, we can make it `MOVE`→`HARVEST` too, but that will steal from water and risk weeds (we saw 18 weeds when we did).

## Recommendation
- Watch v14.3 vs v14.2: `python scripts/watch.py 1 agent/main.py` vs backup — check if cow still at fence line. If you want that far cow placed centrally, we need to free a central tile earlier (DIG a weed/wheat day20) — I can add that as v14.4.
- For #1 push, v14.2 already beats v14.1 by ~2k mean and fixes your two screenshots. v14.3 is same with slightly cleaner end field. Pick one to post.

No submit done — tarball `HI_AgriBot_v14.3_FeedFix.tar.gz` ready.
