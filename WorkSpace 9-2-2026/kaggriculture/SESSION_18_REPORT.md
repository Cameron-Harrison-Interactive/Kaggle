# SESSION 18 — Land-gate + town-herd (the user's two directives)

**Date:** 2026-08-21  ·  **Bot:** `main.py` (1,545 lines)  ·  **Tool:** `watch.py` → `watch.html`

---

## The honest bottom line

Both of your directives are in, and the bot is better for them.

**Solo (10 seeds, vs PASS):**

| | avg | seed 1 | worst seed |
|---|---|---|---|
| session 16 (baseline) | $88,500 | $111,719 | seed 7 $50,451 |
| session 17 (cow ramp) | $89,093 | $102,544 | seed 7 $57,867 |
| **now** | **$96,399** | $107,573 | seed 7 $81,316 |

Now: `[107,573, 107,944, 101,094, 94,610, 105,994, 87,043, 81,316, 90,084, 89,844, 98,487]`

**Gauntlet (seeds 1-3, both seats):** mirror/cowbot/sheepbot/goosebot/cropbot all
still **6W-0L** (+$15k to +$42k). The v25 tape is unchanged at **−$63k (0W-6L)** —
that gap is still the crop-volume economy, not these fixes.

---

## 1. Land: unlock one quadrant at a time, only when the field is full

You were right. Two real bugs + one policy, all fixed:

- **The land loop could buy NE + SW + SE in a single turn.** It used a frozen
  `unlocked` snapshot, so once the cash was there it dumped $7,000 on three
  quadrants in one hour — quadrants we could not possibly fill. Fixed: each
  buy adds the quadrant to the working set, so SW is gated on NW+NE being
  full and SE on NW+NE+SW being full.
- **"Full" is now measured, not assumed.** The old gate fired at 50% occupancy.
  New rule: a quadrant is bought only when the land we own is ≥90% used —
  **crops + pastures** on a milk/wool/egg town (the herd *is* the economy
  there), **crops** on a crop town (weeds count as empty). On top of that the
  buy needs `land_price + $250 buffer + $600` in cash, so the expansion can
  buy its own seeds and hands.
- Result: seed 1 (milk town) now stops at 2 quadrants and still makes $107.6k
  (milk pays the bills; it was never going to fill SW/SE anyway), and crop
  towns unlock as they actually fill. No more throwing $4,000 at SE while NW
  sits empty.

## 2. Herd follows the town (smaller herd on non-milk towns — approved)

The shop list is read every day and the town is classified four ways, then the
herd is built to match, within the 14-animal cap:

| town | signal | herd | crops |
|---|---|---|---|
| milk | milk shops ≥ 12/day, ≥ wool & egg | cows up to 12, fast ramp | seed floor high |
| wool | 2+ yarn stores (24/day) | sheep up to 10, cows 4 | — |
| egg | bakeries/brunch dominate | geese 6, cows 4 | seed floor low |
| crop | crop shops ≥ 18/day, no dominant animal | cows 6, sheep 2 | seed floor low, seeds first |

On a crop town the freed cow-cash now buys strawberry/melon/carrot seeds
(seed floor drops from $450 to $300), and on a milk town the cows ramp fast
again so we don't lose the one product that pays best there.

---

## What I verified along the way (so you don't re-derive it)

- The town shop mix is **not fixed per seed** — shop RNG shares the weed RNG,
  so our own play changes which shops unlock. "Seed 7" is a different town
  under different bots. The only honest metric is the 10-seed average.
- The tape still wins because it opens with **5 animals on day 0** (4 sheep +
  1 cow → 5 fertilizer/day = $500/day from day 2) and buys strawberries in
  bulk on days 7 and 10. Our cow engine is worth more on milk towns, so we
  keep it — the remaining −$63k is crop *volume*, which needs the day-0/early
  cash rework, not the land or herd changes.

## Watch it

`watch.html` (regenerated with the new bot) replays **main.py vs the v25 tape**
seeds 1-3, hour by hour, with money/prices/shops/actions. Note the land now
unlocks quadrant-by-quadrant instead of all at once.

```
python3 watch.py 1          # seed 1 only
python3 watch.py 1 --mirror # vs the mirror archetype
```

Next lever, when you want it: the early-cash engine (day-0 opening + fertilizer
selling + bulk strawberry buys) — that's the one thing standing between us and
the tape's crop volume.
