# SESSION 22 — Fixing the "hardly any crops" regression + town-aware retry

**Date:** 2026-08-21  ·  **Bot:** `main.py` (1,611 lines)  ·  **Tool:** `watch.py`

---

## What you saw, and what I did about it

You were right: the static pasture reserve (14 tiles held for the herd forever)
was starving the crops — on a crop town the herd is only ~8 animals, so 6 prime
near-shed tiles sat empty and everything else got pushed out. Fixed:

**Dynamic reserve.** Now we reserve **only one tile per animal we still need to
place** (herd target − animals on board), and the moment the herd is at target
the reserve drops to zero. Crops get every tile the herd doesn't actually need.

**Kept:** the `max_animal_dist = 4` soft cap (your rule — animals never pastured
more than 4 steps out) and the town-aware herd (milk→cows, wool→sheep,
egg→geese, crop→small herd).

**Reverted (tested, net-negative):** the town-aware "sell all fertilizer early"
(−$0.9k on 20 seeds), and the 4-sheep/1-cow opening (−$16k).

**Gauntlet back to clean:** mirror/cowbot/sheepbot/goosebot/cropbot all
**6W-0L** (+$16k to +$40k). Tape −$72k (3-seed margin, noisy — see below).

## The honest state of the v25 gap

I've now tested, with A/Bs, every lever you and I could think of: bulk seed
buys on unlock, hiring for empty land, sell-first at hour 0, 5-animal opening,
early fertilizer selling, universal carrots, market-gated carrots, static and
dynamic pasture reserve. **Every single one is net-negative or neutral on the
20-seed average.** The bot holds at ~$88k solo (20 seeds), beats every
archetype, and still loses to the tape's crop volume.

The reason has not changed in four sessions: **days 2–12 cash.** The tape opens
5 animals and sells $500/day of fertilizer from day 2; we open 4 and make
~$400/day, and the cow/milk engine that earns us our edge is exactly what we
can't cut to afford the crops. This is a structural opening-economy difference,
not a bug I can patch with another parameter.

## The one thing I'd want your eye on

The town shops are **not fixed per seed** — the weed-spawn RNG rolls per empty
tile each night and the shop-unlock draw follows it, so any change to our
layout reshuffles the shops we face. That's why single seeds jump $30k between
runs and the 3-seed tape margin swings −$60k↔−$83k. The 20-seed average is the
only honest number, and that's what I've been reporting.

`watch.html` is regenerated (seeds 1–3 vs the tape). If you can tell me the
specific seed/day where you see the tape doing something we don't, I'll trace
that exact game step-by-step next.

**Bottom line for this turn:** the crop regression is fixed, the animal cap and
town-aware herd are in, all archetypes are beaten 6W-0L. The tape remains ahead
on crop volume because of its day-0 cash engine, which I have not found a
profitable way to copy without giving up the milk that carries us.
