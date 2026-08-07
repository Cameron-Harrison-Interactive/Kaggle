# Two Winning Builds — Decoded from Replays

Replays pulled (Kaggle CLI authenticated):
- `episode-90563851-replay.json` — **Chloe $94,063 vs Raj Aryan $94,034**
- `episode-90565430-replay.json` — **Chloe $128,549 vs THUNDER THUNDER $137,060**
  (THUNDER wins; same shared market, so absolute scores depend on opponent.)

## What is IDENTICAL across all four bot-instances (the proven meta)

- 8 cows + 6 sheep, 14 pastures, zero geese/chickens/coops.
- Quadrants NW + NE + SW; **never SE**. Land buys day 7 (NE) and day 11 (SW).
- Day-0 opening: 5 HIRE, BUY_ANIMAL SHEEP 2 + COW 2, BUY_SEED WHEAT 7 + MELON 12,
  plus a few BUY_PRODUCT WHEAT.
- Animal ramp: +1 cow d3, +1 cow d5, +2 cow/+2 sheep d7, +2 cow d9, +2 sheep d11
  (final 8 cow / 6 sheep).
- Crop layout (tiles, not counts by seed): 7 wheat + 12 melon in NW; after NE opens
  day 7 add strawberry (reaches 19, then 42 with SW); melon held at 12.
- Same total sells: ~237 milk, ~164 wool, ~144 melon, ~299-313 strawberry,
  ~208-233 fertilizer.
- Endgame: all crops harvested/dug, 14 animals standing, shed empty, last-day
  wheat dump (91 wheat sold day 29 by THUNDER).
- Hires: ~259-277 HIRE orders over the game (roughly 9-14 hands/day).

## How THUNDER ($137k) beats Chloe ($128k in that match)

The difference is early cash flow and wheat self-sufficiency:

| Metric | Chloe | THUNDER |
|--------|------:|--------:|
| Wheat bought from market (whole game) | 980 | **264** |
| Wheat sold to market | 828 | **279** (net seller) |
| Wheat seed bought | 92 | **110** |
| Fertilizer sold | 233 | 208 (keeps more for crops) |
| Total hires | 277 | **259** (cheaper labor) |
| Cash end of day 6 | $970 | **$1,714** |
| Cash end of day 11 | $10,561 | **$16,593** |
| Cash day 21 | $38,221 | **$61,178** |

### THUNDER's wheat engine
1. Plants 7 wheat day 0 (same as Chloe) but **reseeds/expands wheat more**
   (110 seed vs 92) and **keeps more fertilizer on crops** (sells 208 vs 233),
   so wheat yields are higher.
2. On day 5 it **dumps 25 wheat in one hour-1 order** (~$700) then buys back only
   4 units across the day for feed — a net positive cash swing.
3. Day 10 another 22 wheat sold; day 11 it has $16.5k to fund the SW land +
   sheep + 14 hires without stalling.
4. Hires fewer hands total (259 vs 277), saving Fibonacci labor cost, but still
   reaches 14 hands on the critical day-11 expansion.

### Net lesson
The base animal build (8c/6s, 3 quads) is necessary but not sufficient. The
margin at the top comes from:
- **Grow your own wheat feed; be a net wheat seller, not buyer.** Buying 980 wheat
  costs roughly $25-30k over the game; growing it costs seed + labor and the
  surplus sells.
- **Use fertilizer on your own crops** (especially wheat and the premium waves)
  rather than selling every unit.
- **Big batch wheat sell early** (day 5) to front-load expansion cash.
- **Trim hiring** — 9-11 hands is enough most days; save the expensive fib hires
  (13/21/34) for expansion days 7 and 11.

## Tuning targets for our v6

1. Aim for **net wheat seller**: BUY_PRODUCT WHEAT only to top up feed shortfall;
   plant enough wheat (target 7-10 tiles always in ground, reseed day 4/8/12...).
2. **Fertilize wheat and premium crops**: FERTILIZE when standing on a wheat/melon/
   strawberry plant and fertilizer is in inventory, instead of selling all fert.
3. **Batch-sell wheat early** when shed wheat exceeds a rolling feed reserve
   (e.g. sell surplus at hour 1 in one order to capture price before it drifts).
4. **Hire 9-11 hands normally, 14 on days 7 and 11** — don't max hires every day.
5. The v6 must first achieve survival (all 4 day-0 animals live, land buys fire,
   animal ramp completes by day 11). Then apply the wheat/fertilizer optimizations.
