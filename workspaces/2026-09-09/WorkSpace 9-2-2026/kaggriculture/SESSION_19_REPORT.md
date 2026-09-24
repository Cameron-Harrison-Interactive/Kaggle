# SESSION 19 — Land readiness + the carrot test

**Date:** 2026-08-21  ·  **Bot:** `main.py` (1,569 lines)  ·  **Tool:** `watch.py` → `watch.html`

---

## The honest bottom line

Your day-17 SW complaint is addressed, and I tested the carrot idea like you
asked. One of them stuck; one of them the numbers say no to.

**Solo (10 seeds):** baseline $88,500 → **$95,183** now
`[107,573, 107,944, 101,094, 94,610, 105,994, 87,043, 69,157, 90,084, 89,844, 98,487]`

**Gauntlet (seeds 1-3, both seats):** all archetypes still 6W-0L; v25 tape
unchanged at −$62k.

---

## 1. "SW unlocked at day 17 and sat empty" — fixed

Two things were wrong and both are fixed:

- **The land loop could still buy multiple quadrants in one turn** on a crop
  town, because the crop-fill check ignored the `unlocked` set. Now a
  just-bought quadrant counts as 25 empty tiles, so SW genuinely waits until
  NW+NE are full, and SE waits until NW+NE+SW are full.
- **A `_land_ready` gate** was added: a crop town only expands while it holds
  seeds to start filling the new land the same day, and an animal town expands
  freely (the herd fills its own land with pastures + feed, no seeds needed).

Verified on the replay: land now unlocks one quadrant at a time, and at the
moment of unlock we're holding melon + wheat seeds to plant it immediately —
no more buying 25 tiles and staring at dirt.

## 2. Carrots for early cash — tested, and the honest answer is no (for now)

I ran exactly your idea: buy carrots day 0, chase them through day 11, and
boost them in the crop chooser for the first 8 days (two 3-day rounds before
the first cow milk). Result on 10 seeds:

- universal carrots: **$84,082** avg (vs $96,399 without) — clearly worse
- market-gated carrots (only when the town eats them / price has risen):
  **$94,260** avg — still slightly worse

Why: carrots are cheap but they still need **watering** on their bonus days,
and our early game is exactly when we can't afford the hands to water
(everything is going into feed + hires on days 2–5). Adding 6–10 carrot plants
early just pushed the water load over the edge — more melons/strawberries
died. On a milk town they also displaced feed wheat, forcing wheat *purchases*.

So I kept the **carrot-town** version that was already there (Pet Cafe /
Farmers Market → carrots chased hard) and reverted the universal rush. The
carrot idea becomes correct the moment we fix the early watering crew — it's
the same cash bottleneck as the v25 gap, not a separate problem.

## 3. What I found while tracing your day-17 replay

The land is now filled on unlock, but I can see on the replay that around
days 15–17 a batch of the newly-planted crops turns to **weeds**. That is
dehydration: we expanded, planted, and then couldn't afford enough hands to
water all of it on the cash-poor days. This is the *same* root cause as the
v25 crop-volume gap — it all funnels into one thing:

**Early watering crew.** Days 2–5 (and right after each land unlock) we are
broke at hour 0, so we hire no hands, so the plants we just put down die.
Fix that and everything downstream (carrots, fill-speed, strawberries, the
tape gap) unlocks at once.

## Watch it

`watch.html` is regenerated with the current bot. Scrub days 11–18 and watch
the land unlock one quadrant at a time with seeds in hand.

```
python3 watch.py 1          # seed 1 only
python3 watch.py 1 --mirror # vs the mirror archetype
```

**Next move I'd suggest:** rework the hour-0 cash so the watering crew always
exists — sell yesterday's production at hour 0 *before* paying hires, and
reserve wheat+hires ahead of animals/seeds. I prototyped this once and it
regressed (it fed the hour-1 cow-buyer extra cash); with the town-herd and
land gate now in place I think a careful version of it lands. Say go and I'll
build it.
