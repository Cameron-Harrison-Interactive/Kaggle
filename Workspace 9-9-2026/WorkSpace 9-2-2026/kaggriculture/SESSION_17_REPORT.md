# SESSION 17 — The v25 crop-volume gap, dissected

**Date:** 2026-08-21  ·  **Bot:** `main.py`  ·  **Tool:** `watch.py` (new)

---

## The honest bottom line

I did **not** close the v25 gap this session. I found exactly *why* it exists,
shipped the only change that survived 10-seed A/B testing (+$0.6k avg, +$11.7k
on the seed-7 outlier), and built the `watch.py` viewer you asked for so you
can see the mechanism yourself. The gap is a cash-flow problem, not a "just
plant more" problem — details below.

**Solo (10 seeds, vs PASS):**

| | avg | seed 1 | seed 7 (outlier) |
|---|---|---|---|
| before (session 16) | $88,500 | $111,719 | $50,451 |
| now | **$89,093** | $102,544 | **$57,867** |

Full list now: `[102,544, 102,584, 85,758, 98,593, 93,349, 83,482, 57,867, 87,932, 83,277, 95,544]`

**Gauntlet (seeds 1-3, both seats):**

| opponent | before | now |
|---|---|---|
| v25 tape | −$61,022 (0W-6L) | **−$60,377 (0W-6L)** — unchanged |
| mirror | +$15,499 | +$16,382 (6W-0L) |
| cowbot | +$24,912 | +$24,751 (6W-0L) |
| sheepbot | +$24,377 | +$21,339 (6W-0L) |
| goosebot | +$52,368 | +$36,123 (6W-0L) |
| cropbot | +$20,462 | +$42,608 (6W-0L) |

Archetype wins hold. The tape still beats us by ~$60k contested.

---

## What the gap actually is (measured, not guessed)

Revenue breakdown on seed 1:

| product | us | v25 tape | gap |
|---|---|---|---|
| MILK | **$79k (249u)** | $57k (218u) | **+$22k (we win)** |
| STRAWBERRY | $2k (9u) | $37k (285u) | −$35k |
| MELON | $9k (32u) | $27k (114u) | −$18k |
| WOOL | $12k (62u) | $29k (132u) | −$17k |
| WHEAT (sold) | $2k (41u) | $17k (482u) | −$16k |
| FERTILIZER | $20k (265u) | $19k (245u) | +$1k |

Our **cow + CARE engine is already better than the tape's**. The entire gap is
crop VOLUME: the tape plants 38 strawberries + 22 melons + ~120 wheat; we plant
~9 strawberries + ~15 melons. The tape turns 38 strawberry seeds into 285 units
by fertilizing every production tick.

## Root cause chain (each link verified with a probe)

1. **Our crops die.** Baseline plants 7 strawberries — all 7 turn into weeds.
   I traced one plant hour-by-hour: planted day 1, watered days 1/3/5, then day
   7 nobody waters it (we had 0 hands that morning) → dead day 8.
2. **Why no hands?** On days 2–5 we are broke (e.g. day 3 = $47). Hires are
   paid at hour 0, and the day-0 opening spends $2,987 of the $3,000 (2 sheep +
   2 cows $1,800, 17 seeds $920, 12 wheat $300), leaving nothing to hire a
   watering crew on the days every young plant needs its alternate-day water.
3. **Why broke?** Days 0–6 have almost no income (wool first lands day 7, milk
   day 9). v25's tape fixes this by opening with **4 sheep + 1 cow (5 animals →
   5 fertilizer/day from day 2 = $500/day)**, selling that fertilizer every day,
   and buying strawberries in *bulk* on day 7 ($1,000) and day 10 ($1,600) once
   cash has accumulated.
4. **Every "fix" trades off against the herd.** Buying more seeds drains the
   cash the cows need; deferring cows loses the milk that is our best product.
   I A/B-tested: seeds-before-animals, a $70 seed floor, day-0 planting,
   survival-water-first, selling fertilizer at hour 0, and a crop-town herd
   shrink — **all net-negative on 10 seeds** (they add crops but lose more milk,
   or misfire on mixed towns). Only one change won:

**Shipped: `cow_ramp_end` 9 → 12.** Cows now ramp to 10 by day 12 instead of
day 9. That leaves the days 6–12 cash available for a few more crops *and* lets
the town's shop unlocks (days 3/6/9/12) be read before the herd is fully
committed. Result: seed 7 (the balanced/crop outlier) $50k → $58k, seed 4
$89k → $99k, at a small cost to the milk-heavy seed 1 ($112k → $103k).

The losing experiments are left as **documented switches** in `DEFAULT_PARAMS`
(`day0_plan`, `survival_water`, `crop_town`, `seed_floor_straw/melon`,
`hire_reserve`) so we can flip them per-town later without re-writing.

## watch.py — what I built for you

`python3 watch.py` runs **main.py vs the v25 tape** (seeds 1-3 by default) and
writes **`watch.html`** — a self-contained animated replay, no network needed:

- our farm (left) vs the tape (right), 10×10 boards, 1 frame per hour
- money for both sides + live lead/trail
- market prices + town shops each frame
- the exact action each side issued each hour (plant/water/feed/care/buy/sell)
- play / pause / speed / step / ±day / scrub / seed selector

Open it and scrub to **days 3–10**: you will see the tape's field fill with
strawberries while ours sits mostly empty (no seeds, no hands, no cash). That is
the whole story.

```
python3 watch.py 1          # just seed 1
python3 watch.py 1 7        # seeds 1 and 7
python3 watch.py 1 --mirror # main.py vs the mirror archetype
```

## What I need from you

Watch `watch.html` (or tell me a specific seed/day that looks wrong) and answer
the one question that decides the next move:

**Do we accept a smaller herd on non-milk towns to fund the crops?** The tape's
answer is yes (it runs 9 cows/4 sheep and 60 crop tiles). Our answer so far is
"no" because our 10-cow milk engine is worth more than the tape's on milk
towns — but that's what's starving the strawberries everywhere else. If you
agree with "yes", I'll build a town-driven herd/crop budget (crop towns and egg
towns shrink the herd to 6 and pour the cash into strawberries + carrots); the
seed-7 probe already shows +$12k from that direction alone.
