# SESSION 20 — "Fill it all like v25": the animal-spread and fill-speed tests

**Date:** 2026-08-21  ·  **Bot:** `main.py` (1,580 lines)  ·  **Tool:** `watch.py`

---

## The honest bottom line

I chased your "SW full by day 10 / fill it all" observation to the ground this
session. I measured the animal spread, tried five different fixes for it and
for fill-speed, and **every one of them lost money on the 10-seed average** —
so I reverted them. The bot is unchanged at **$95,183 avg** (still +$7k over
session 16), and the reason is now precisely identified:

**Filling fast is a cash problem, and every brute-force way to fill faster
steals cash from the herd and loses more than it gains.** The one thing that
actually fixes it is the early-cash engine (below).

| experiment | 10-seed avg | verdict |
|---|---|---|
| (current state) | $95,183 | keep |
| animals near shed (farthest-first) | $93,923 | revert |
| animals near shed (reserve 12/16/8 tiles) | $88.7k / $90.3k / $89.9k | revert |
| bulk seeds on unlock + hire-for-field | $81,204 | revert |
| sell products at hour 0 (before hires) | $74,007 | revert |

## What I measured

**Your animal-spread hunch was real.** At day 15 our animals sit at Manhattan
distances `[0,1,1,2,2,3,3,4,4,4,4,4,5]` from the shed — a third of the herd at
distance 4–5. Why: the planting pass plants the near-shed tiles FIRST, so the
crops take the good ring and every later pasture gets pushed out.

But fixing it lost money: forcing animals into the near ring just pushed the
crops out, and crops need a water every other day (plus daily bonus-window
water for melons/wheat), so the crop walk-penalty outweighed the animal
walk-savings. It's a genuine zero-sum placement trade, not free money.

**The fill-speed problem is real and is exactly the cash bottleneck.** On seed
3 we unlock NE ~day 12 and it takes until ~day 17 to fill, then SW ~day 17
sits mostly empty until ~day 22 — precisely what you saw. I tried:

- buy seeds in **bulk** the moment a quadrant opens (6 melons + 12 wheat), and
- hire the hands to plant the empty land immediately (instead of only when
  seeds are already in hand).

Both made the field fill ~2 days faster — and both lost money, because the
bulk spend + the extra hires came straight out of the herd ramp (milk/wool),
which is our best income. Same story with selling at hour 0 to fund waterers:
the hour-1 buyer just spends the freed cash on cows.

## Why v25 fills SW by day 10

It is not planting speed — it is **money**. The tape opens with **5 animals on
day 0 (4 sheep + 1 cow)** → 5 fertilizer/day = **$500/day from day 2**, sells
it all, and buys strawberries in bulk on days 7 ($1,000) and 10 ($1,600). That
income stream is what lets it buy the seeds AND hire the hands to fill NW→NE→SW
by day 10. We open with 2+2 animals, so our days-2–9 income is ~$400/day, and
everything downstream (fill speed, land timing, crop volume) runs ~5 days
behind the tape.

## The next move (the real one)

I've now isolated it to one decision, and I'd like your call before I spend the
turn on it:

**Rework the opening + early cash:**
1. day 0: 4 sheep + 1 cow (5 animals) instead of 2+2;
2. sell fertilizer every day from day 2 (we already collect it — just sell
   instead of holding a reserve while there are no strawberries to fertilize);
3. buy strawberries in bulk on days ~7 and ~10 (let cash accumulate, then dump
   it into seeds) instead of the 1-at-a-time rolling rebuy.

Risk: fewer cows day 0 means less milk on milk towns. I can make the opening
town-aware later, but the first pass is blind (shops don't unlock until day 3).

Say **go** and I'll build it and A/B it against the current $95,183.

`watch.html` is regenerated (seeds 1–3 vs the tape) if you want to look at the
animal spread and the NE→SW fill gap yourself.
