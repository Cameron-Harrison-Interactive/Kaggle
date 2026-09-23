# R62 — NW scripted animal route (KEEP)

One change, NW only. Other quads untouched.

## What we did

The two NW animal workers now walk a **fixed route**:

- 6 animals packed on the tiles next to the shed (3 per worker).
- Walk the row once. At each animal: feed, then care, then harvest, then collect fert.
- No mid-row dump to the shed (that walk was eating the hours care needs).
- Empty holes fill first (workers already spawn at the shed), then the row.
- Extra animals go to NE. We only keep in NW what these two workers can finish in 24 hours.

## Why

Seed 42, old route: care 40%. Full care through day 7, then the herd hit 8 and care fell to 1–3 out of 8 for the rest of the season. Morning installs and shed dumps used the day; care was last and got cut.

The rules pay a care bonus only if the animal is fed **and** cared the same day, and that bonus is cashed on the next production day. Missing care is missing milk/eggs/wool.

## Numbers

NW care on seed 42: **40% → 95%**. Bonus on production days: **44% → 93%**. Opening cow no longer escapes (day 0 is 4/4 fed and cared).

Solo vs pass (same 6 seeds as always):

| seed | old (v31) | new     | delta   |
|------|-----------|---------|---------|
| 42   | 99,557    | 106,805 | +7,248  |
| 5    | 107,248   | 105,412 | −1,836  |
| 101  | 103,629   | 103,140 | −489    |
| 202  | 103,592   | 118,807 | +15,215 |
| 303  | 106,905   | 108,079 | +1,174  |
| 777  | 89,162    | 118,810 | +29,648 |
| AVG  | 101,682   | **110,176** | **+8,493** |

Head-to-head vs our own v31, both seats, all 6 seeds: **12–0**, median +37k. Wins are what the ladder counts.

Two solo seeds are slightly down. Both still win the head-to-head. Net is not a 370-coin tick.

## Not done yet (still NW)

- Water is already landing on the tiles that need it.
- Fert on NW wheat/melon almost never beats **selling** the fert (wheat extra is 2 units, melon already hits its cap if watered). That check is next, not stacked on this change.
- NE / SW / SE routes are unchanged.

File: `war/astra_live20_34.py`. Not posted. Say the word if you want it submitted.
