# SESSION 21 — Early-cash test, animal placement cap, and the RNG discovery

**Date:** 2026-08-21  ·  **Bot:** `main.py` (1,608 lines)  ·  **Tool:** `watch.py`

---

## The honest bottom line

You said "go ahead and try it" — I tried the whole early-cash play, and the
numbers said no. The animal placement cap you asked for is in and working.
One big discovery this session explains a lot of the noise we've been chasing.

**Solo 10 seeds:** ~$91.8k (moves ±$4k with any code change — see RNG note).
**Solo 20 seeds:** ~$87.6k, animal-cap on/off within ~$500 (neutral).

---

## 1. The early-cash engine — tried, failed, reverted

Built exactly as agreed and A/B'd each piece:

| change | 10-seed avg | vs base $95.2k |
|---|---|---|
| 4 sheep + 1 cow opening | $79.0k | −$16k |
| sell all fertilizer days 2–8 (alone) | $81.3k | −$14k |
| both | $79.0k | −$16k |

**Why it fails for us:** the tape's whole economy is 5 animals + crops; ours is
**10 cows + CARE = $79k milk**, which is our single best asset and the reason we
beat every archetype. Cutting the day-0 cows to fund sheep cuts milk on milk
towns (seed 1 drops $107k→$83k), and the extra sheep (wool every 3 days) never
catch up. Selling the fertilizer early also just recycles cash into the cow
ramp, and it lowers our total fertilizer price (fert is ~16% of our revenue).
Both are reverted; the switches (`open_sheep/open_cows`, `fert_early_day`) stay
in params if we want to retry per-town later.

## 2. Animal placement — soft cap shipped, verified

- `max_animal_dist = 4` (param): the herd is placed within 4 steps of the shed,
  falling back to a farther tile only if none is free inside the cap.
- `pasture_reserve = 14`: while the herd is still growing, the 14 tiles nearest
  the shed are kept clear of crops so the cap actually has room. Once the herd
  is full the reserve releases and the leftover near tiles get planted.

**Measured:** day-20 animal distances went from
`[0,1,1,2,2,3,3,4,4,4,4,4,5]` (max 5) to `[0,1,1,2,2,2,3,3,3,3,4,4,4,4]`
(max 4). Your "no further than 4 steps" rule is now enforced.

The params are there for the "animal type changes" case you mentioned: if a
bigger/slower animal ever needs more room, `max_animal_dist` is the one number
to bump.

## 3. The RNG discovery (this is important)

The town shops are **not fixed per seed**. `_spawn_weeds` rolls the RNG once
per empty tile each night, and the shop unlock draw happens *after* that on the
same stream. So **the number of empty tiles we leave each day shifts which shops
unlock** — every code change (placement, reserve, anything) reshuffles the towns
we face.

What that means for testing: the 3-seed tape margin is very noisy (it has swung
−$60k ↔ −$83k this session while solo stayed $88–96k), and single-seed "before
vs after" comparisons are meaningless. The 20-seed average is the honest number,
and on that the animal cap is neutral, the land gate + town herd are up, and the
early-cash engine is down.

**Gauntlet now (seeds 1-3):** mirror/cowbot/goosebot/cropbot 6W-0L,
sheepbot 5W-1L (one seat-1 game, likely a shop draw), tape −$82k (noisy band).

## 4. "Why only 8 crops in SW" — answered

Same root cause as everything else: **we unlock SW late (day ~17) because NW+NE
fill slowly, and they fill slowly because days 2–12 are cash-poor** — not enough
money for seeds AND the watering crew at the same time. The tape has $500/day of
fertilizer income from day 2; we have ~$400. Every fill-speed lever I tested
(bulk seeds on unlock, hiring for empty land, sell-first) spends the herd's
money and loses more than it gains. The only fix is real early income, and the
naive version (fewer cows) doesn't pay because the milk is worth more.

## Watch it

`watch.html` regenerated (seeds 1–3 vs the tape). Scrub days 12–20: you'll see
the land unlock one quadrant at a time and the herd staying within 4 steps of
the shed now.

**My recommendation for next turn:** instead of cutting cows for early cash,
make the opening **town-aware** — read the first shop unlocks (days 3/6) and
*then* decide sheep-vs-cow-vs-crop. That keeps the milk on milk towns and adds
the fertilizer stream on the rest.
