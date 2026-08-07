# Top-2 Bot Decode — Episode 90563851 (Chloe vs Raj Aryan)

**Replay:** `Kraggriculture/replays/episode-90563851-replay.json` (30 MB, 720 steps)
**Final scores:**
- 🥇 **Chloe (p0): $94,063**
- 🥈 **Raj Aryan (p1): $94,034**
- Difference: **$29** — the two bots are effectively the same strategy/lineage.
- Our current best: **v5.8z5f = $69,203** → they beat us by **~$25,000 (36%)**.

Both bots run **identical build orders, identical counts, nearly identical actions**.
This is the meta at the top. We should copy it, then find an edge.

---

## 1. The strategy in one sentence

**14 animals (8 cows + 6 sheep) on 3 quadrants, all cash from milk/wool/fertilizer,
small melon+strawberry patches farmed by the daily crew, and NO geese, NO carrots,
NO tomatoes, NO chickens/coops.**

## 2. Final board (turn 720)

```
Unlocked quadrants : NW, NE, SW         (never bought SE)
Pastures           : 14 total (8 with COW, 6 with SHEEP)
Coops / geese      : 0
Crops left standing: 0                   (all dug/harvested by endgame)
Shed inventory     : 0 across all goods  (everything sold)
```

## 3. Exact build order (both bots, identical)

| Day | Cash start | Actions |
|-----|-----------:|---------|
| **0** | $3,000 | **Hire 5 hands. Buy 2 SHEEP + 2 COWS ($1,800). Buy 7 wheat seed + 12 melon seed. Buy 2 wheat.** End cash $105. |
| 1 | $105 | Build & populate 6 pastures (4 cows? actually 2 cow + 2 sheep placed; 2 pastures empty until next animals). Buy wheat for feed throughout. Sell 2 fertilizer. |
| 2 | $14 | **Hire 4 more hands.** Aggressive wheat buying/feeding. End $175. |
| 3 | $175 | Hire 5, **buy 1 more cow**, sell 4 fertilizer. End $62. |
| 4 | $62 | Hire 5, buy wheat seeds (7), sell fertilizer. End $298. |
| 5 | $298 | **Buy 1 more cow** (now 4 cows, 2 sheep). Sell wheat surplus + fertilizer. End $970. |
| 6 | $970 | Hire 4. End $1,015. |
| **7** | $1,015 | **BUY_LAND #1 (NE, $1,000). Buy 2 more sheep + 2 more cows. Buy 8 strawberry seed. Sell 12 wool.** End $291. |
| 8 | $291 | NE quadrant: build 6 more pastures (12 total, 6 cows / 4 sheep once placed). Hire 9. End $2,332. |
| 9 | $2,332 | **Buy 2 more cows (8 total).** Sell first 6 milk + 4 wool. Hire 10. End $2,022. |
| 10 | $2,022 | First big melon harvest sells ($12-melon order + 6×3). End $10,561. |
| **11** | $10,561 | **BUY_LAND #2 (SW, $2,000). Buy 2 more sheep (6 total, final count). Buy 12 melon + 23 strawberry seed. Sell 30 melon.** End $11,221. |
| 12 | $11,221 | Final 2 pastures built → **14 animals total (8 cow / 6 sheep) for rest of game**. |
| 13+ | climbing | Pure economy: milk every 2 days, wool every 3 days, fertilizer daily, rotate melon/strawberry patches with the hired crew. |
| 20 | $35,242 | Massive strawberry wave (sold 16+6 in one day). |
| 29 | $86,805 | Final cash-out: sell 45 wheat, all milk/wool/fertilizer. End **$94,063**. |

Hands per day ramp: 5 → 9 → 9 → 10 → 10 → 13 → 14 → 13 → 14 → 14 (capped at 14
because 5 fib-hires/day × the schedule; hands re-hired fresh every day).

## 4. The labor model (Day 0 micro, decoded)

All 5 hires happen on **hour 1** (first turn of the day — cheapest, and they spawn
on the shed-edge tiles). Then:

- **Farmer** stays near shed: PICKUP 2 cows → BUILD_PASTURE → PLACE COW, repeats for
  the second cow. Farmer owns the first two cow pastures at `(4,3)` / `(3,4)`.
- **Hand A** (spawned `(5,4)`): moves north, builds pasture at `(4,2)`, plants wheat
  and melon up the `x=4` column.
- **Hand B** (spawned `(4,5)`): runs west to column 0, planting melons up the left
  edge — this is the melon column.
- **Hand C** (spawned `(5,5)`): PICKUP 2 sheep, builds pasture at `(4,3)`/`(3,3)`,
  PLACE SHEEP, then **FEED + CARE every day** (the dedicated animal hand).
- **Hand D / E** fill the remaining pasture + wheat/melon columns.

Key labor traits:
1. **One hand is the permanent animal tender** — feed + care + collect fertilizer
   every day, standing among the pastures.
2. The other hands plant in **vertical columns**, not scattered. Each hand owns a
   column, walks up it planting then back down watering.
3. Hired hands are issued a single action each turn — there is no long-horizon
   planner visible, just a state-machine per hand based on its tile.
4. They plant **melon and wheat in the first wave**, strawberry only after day 7
   once NE is bought and the crew is bigger.

## 5. The economy

Total units sold over the match (Chloe):

| Product | Units | Notes |
|---------|------:|-------|
| FERTILIZER | 233 | ~8/day × ~28 days from 14 animals — **$23k+ at ~$100** |
| WHEAT | 828 | surplus wheat traded back to market (also bought 980) |
| MILK | 237 | 8 cows × ~0.5/day × ~25 production days |
| STRAWBERRY | 313 | big batches day 17, 21, 24, 26 |
| WOOL | 164 | 6 sheep × ~0.33/day |
| MELON | 144 | two batches (day 10/11 and day 21/23) |

**Revenue pillars:**
1. **Fertilizer is free money** — every surviving animal makes 1 per day. 14 animals
   × ~28 days ≈ 392 produced; they sold 233 (rest used on crops). At ~$100/unit that
   is **~$23,000** pure profit.
2. **Milk** ($160 base) from 8 cows every 2 days — steady premium income.
3. **Wool** ($200 base) from 6 sheep every 3 days.
4. **Melon + Strawberry patches** are planted with the fertilizer boost and cashed
   out in 2–3 synchronized waves (premium crops hit hard when timed).
5. **Wheat** is bought/sold dynamically to keep animals fed without over-producing.

## 6. Why this beats our v5.8z5f

| Our bot | Top-2 bots |
|---------|-----------|
| Crop-first, no animals | 14 animals = primary income |
| Buys all 3 lands by day 11, uses NE/SW/SE | Buys only 2 lands (NE day 7, SW day 11), **never SE** |
| Hires 8 max | Hires up to 14 hands/day |
| Sells on static price gates | Sells fertilizer daily + synchronized premium-crop waves |
| Melon crash risk (premium glut to $1) | Uses fertilizer to double melon yield in tight waves so the glut is brief |
| Wastes labor on tomato/strawberry lifecycle (weeds/decay) | Animals produce indefinitely for 30 days |
| Brain .pkl is fake | No ML — pure state machine, and it wins |

## 7. What we can copy now (v6.0 "Seb style" / "Chloe clone")

1. **Day-0 opening script**: HIRE×5 on hour 1; BUY_ANIMAL SHEEP 2, COW 2; BUY 7 wheat
   seed, 12 melon seed; BUY 2 wheat.
2. **Pasture placement**: 6 pastures in NW around the shed on days 0–1; 6 more in NE
   days 7–8; 2 more in SW days 11–12. Total 14.
3. **Animal count ramp**: 2 cows + 2 sheep (d0) → +1 cow (d3) → +1 cow (d5) → +2 cow
   +2 sheep (d7) → +2 cow (d9) → +2 sheep (d11). Final 8 cow / 6 sheep.
4. **Land timing**: NE on day 7, SW on day 11. **Skip SE entirely.**
5. **Dedicated animal hand**: FEED, CARE, COLLECT_FERTILIZER, HARVEST milk/wool each
   day. Every animal fed every day (never let `consecutive_unfed` reach 2).
6. **Column planters**: remaining hands plant in vertical columns (wheat for feed,
   melon d0 wave, strawberry after d7).
7. **Daily fertilizer sell** of surplus (not used on crops); use a portion to boost
   the melon/strawberry wave.
8. **Endgame cash-out**: by day 29 sell everything, dig empty structures not needed,
   ensure shed is empty because **unsold inventory = $0**.

## 8. Where we might find an edge (to beat 94k)

- They hire **5 hands on day 0** but only need 4–5 tasks; could optimize hand count
  day-by-day to save Fibonacci hire costs.
- They never buy SE ($4k); perhaps a late SE buy with strawberry/melon is +EV if
  crew can service it. Needs testing.
- Their wheat BUY/SELL churn looks like a feedback loop, possibly exploitable to
  manipulate the wheat price upward before a big sell.
- Melon price crashes to $1 on gluts — better batch timing / waiting for town
  consumption ticks could raise per-unit price.
- They use no geese; geese produce eggs daily at $50 and are cheaper ($300) but
  require coops and wheat feed — possible if a hand has spare cycles.
- Final day: they had 0 shed but structures still standing. DIGging is free and
  doesn't refund, so irrelevant; but any last-milk harvest on turn 719 matters.

## 9. Other episodes available

Same leaderboard/submission can be pulled once episode IDs are known:
```
kaggle competitions replay <EPISODE_ID> -p Kraggriculture/replays
```
If we want to see whether the #1 strategy has variety, pull 3–5 more matches from
Chloe's / Raj Aryan's submission history. We have the CLI authenticated now.
