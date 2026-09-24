# SESSION 24 — "Fill NW on day 0-1" — tested hard, and the honest answer

**Date:** 2026-08-21  ·  **Bot:** `main.py` (1,640 lines)  ·  **Tool:** `watch.py`

---

## The honest bottom line

You're right that v25 fills NW way before us — but I've now proven *why* we
can't copy it without losing money, and the numbers are consistent across
three different attempts.

**Solo (20 seeds): $97.6k** — best ever. **0 escapes.** SW unlocks.

| opening / day-0 plan | 20-seed avg |
|---|---|
| current (2 sheep + 2 cow, plant day 1) | **$97,641** |
| day-0 plant, 4 hires | $88,154 (−$9.5k) |
| day-0 plant, 6 hires | $95,999 (−$1.6k) |
| 5 animals day 0 (4 sheep + 1 cow) | $84,435 (−$13k) |
| 3 sheep + 2 cow | $90,404 (−$7k) |

## Why we can't "fill NW day 0-1" like v25

Filling NW on day 0–1 means planting ~17 crops on day 0. Those crops then need
a watering crew on days 2–4 — and days 2–4 are exactly when we are broke
(the day-0 opening spends $2,987 of $3,000, and no income lands until
fertilizer day 2 / wool day 7 / milk day 8). So the day-0 field **dies** on
days 2–4, and the seeds are wasted. I confirmed this twice (with the old code
and again after the hire fix): day-0 planting is net-negative even when the
crew actually shows up.

The tape only gets away with it because its **5-animal opening makes
$500/day of fertilizer from day 2**, which pays for the waterers. And when we
try the 5-animal opening, we lose **$13k** — because cutting the day-0 cow cuts
milk, and our whole edge is the 10-cow + CARE milk engine ($79k milk, vs the
tape's $57k).

So the slower ramp is not a bug — it is the correct price of the economy that
earns us +$10k solo over where we started and beats every archetype. v25's
fast ramp and our strong milk are two sides of the same trade, and we can't
have both with $3,000.

## What IS fixed and working this session

- **Phantom workers** (the big one): the plan was assuming 14–16 workers but
  only ~9 could be hired (10-order market cap). Hires now carry over to hour 1.
  This was silently eating ~40% of our jobs late-game — the empty field at day
  25 and the animal escapes.
- **Wheat pickup**: a worker now picks up wheat for its whole animal slice
  (was capped at 5) — **0 animal escapes across 20 seeds**.
- **SW unlocks** (land gate 0.9 → 0.8, crop-town cutoff 15 → 19).
- **Late fill**: wheat + carrots keep the field at ~24 crops through day 26.

## Gauntlet

cowbot/sheepbot/goosebot/cropbot **6W-0L**. Mirror 4W-2L (+$7.8k, two games by
$3–7k — the town-herd betting small-herd on two mixed towns). Tape −$73k
(3-seed, noisy).

`watch.html` is regenerated — you can see the full crew now, SW unlocking, and
the animals staying fed.

**If you want the ramp matched anyway**, the only lever that does it is the
5-animal opening, and it costs $13k on average — happy to ship it if you want
to trade milk for ramp, but the numbers say keep what we have.
