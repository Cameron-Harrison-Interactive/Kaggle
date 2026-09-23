# R58 — The SW strawberry test: they are the money, not the problem

**Date:** 2026-09-15
**You said:** "SW should never have strawberries. That is for late-game carrots... and then the rest wheat as end game wheat is always 40+, and we can run wheat or carrots with only 2 workers, right?"

**I tested it. It costs us a fortune, and I think we should not do it. Here are the numbers.**

---

## The two tests

| Variant | What SW grows | Result |
|---|---|---|
| **R58** ban strawberry in SW (fall through to argmax) | whatever the scorer picks | **−4,275** |
| **R58b** SW = carrot when live, else wheat all game | carrot / wheat | **−23,047** |

R58b per seed: 71,563 / 82,048 / 80,418 / 89,240 / 81,683 / 66,861 — down on **every** seed, by 20–33k.

---

## What this tells us

**SW strawberries are not the problem. They are the money.**

Yes, SW is where every one of the ~4/game strawberries dies before yielding (103 of 187 deaths total). But:

- Most of those SW deaths are at **age 16–17**, i.e. *after* full yield — they are end-of-life plants, not failures.
- The total-loss deaths cost roughly **$2–4k/game** (seed money + a few tile-days).
- The SW strawberries that **do** survive are worth **$20,000–33,000 per game.**

So the deaths are a 10% tax on SW's best crop. Pulling the crop to avoid the tax costs ten times the tax.

Wheat is the reason R58b collapsed: it is a $40–50 crop with 5 ops. Filling 25 SW tiles with it instead of a $200–316 strawberry throws away the quad.

---

## Where your instinct was right

**"There should be no reason we can't cover them. We have a bunch of wasted working hours."** — I agree, and the measurements say the same thing from the other side: the crop is worth keeping, so the fix is to **tend it properly**, not to remove it.

**"You're adding the fert without fixing the routing for after."** — This is correct and it is my bug. I appended `FERTILIZE` to the plan and left the route untouched, so nothing guarantees the worker comes back to collect the doubled units. Engine L800 caps standing units at `max_yield = 4`, so:

```
event 1 -> 2 units
event 2 -> 4 units
event 3 -> min(4, 4+2) = 4   <-- no gain
```

**If the harvest doesn't land between ticks, the fertilizer is free money.** That is a routing fix, not a crop fix, and it is the right next piece of work.

**"The bot needs to measure the carrot market."** — Correct. `carrot_target` only fires when the **opponent** has 20+ standing carrots, so it is **0 in every solo game** and the carrot lever is invisible to our own testing. That gap is real.

---

## Revised plan

1. **Keep strawberries in SW.** Do not ship R58/R58b.
2. **Fix the post-fert route** — after `FERTILIZE`, the follow-up harvest must be scheduled and the worker's remaining route re-sequenced, so the doubled units actually get collected before the 4-unit standing cap binds. Then re-run the R57 ratchet.
3. **Give SW a bigger share of the existing 13 hands** (rebalance across quads, not add a hand — the 15th hand measured −4,079). This is the "wasted working hours" you're pointing at.
4. Make the carrot call **price-driven** rather than opponent-count-driven, so it is live in solo and testable.

---

## Standing status

- **v31 (`submit/v31_champion.py`) still NOT SUBMITTED** — no Kaggle credentials in the sandbox. +370 (seed-leak fix), fully validated.
- You're right that +370 doesn't win matches. Nothing this round beat the baseline either; the honest run of results is below.
- Do not retry: extra cows (**+0**), 15th hand (**−4,079**), fert-all (**−8,106**), gate-all-fert-on-water (**−10,910**), SW no-strawberry (**−4,275**), SW wheat/carrot (**−23,047**).

## Files

| File | What |
|---|---|
| `war/astra_live20_28.py` | R58 SW strawberry ban — **−4,275** |
| `war/astra_live20_29.py` | R58b SW carrot/wheat — **−23,047** |
| `war/astra_live20_27.py` | R57 paired WATER+FERT + ratchet (**−2,591**); needs the routing fix first |
