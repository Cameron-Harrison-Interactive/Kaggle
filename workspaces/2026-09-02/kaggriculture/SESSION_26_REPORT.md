# SESSION 26 — Planner-depth trick + strawberry hold

**Total (Session 26): +$4,800 / 20 seeds ($97,641 start-of-25 → $105,482).**
Solo `main.py` vs PASS (seed 1) = **$108,078** (up from $97,976 pre-session).

Two independent wins, both principled once you understand them:

1. **`open_melon_seed: 5 → 10`** — the "planner-depth" trick.  Only 4 melon
   seeds actually reach the shed on day 0 (10-order market cap), but telling
   the DAY-0 PLANNER we have 10 melon seeds makes it allocate labor for a
   fuller melon pipeline.  The 6 "phantom" melon plans absorb into more
   watering / faster tile-fill for other crops once the physical 4 seeds run
   out.  Verified: **+$1,967 on 60 seeds** (33/60 wins).
2. **`hold_straw_until: 22`** — strawberry price rises monotonically from
   ~$210 (day 11) to ~$334 (day 29) because town shops eat strawberries
   faster than we produce them.  Holding the (small, ~4-8 unit) strawberry
   stock until day 22 nets **+$957 on 60 seeds** (**59/60 wins**).  We can't
   hold milk/egg (shed capacity 100 overflows fast) or wool (price DROPS from
   $206 to $124 across the game — a monotonically-falling curve).

---

## PART 1 — the planner-depth trick

### Discovery method

Traced day-0 seed inventory after the market cap dropped extra seed lines.
`open_melon_seed=10` and `open_melon_seed=5` result in the SAME physical
seed count (4 melons at hour 2 — because the hour-1 fallback order is
`BUY_SEED MELON min(request, remaining_stock)` = 4), yet solo scores differed
by +$3,620 on seed 1.

The mechanism (traced through `_derive_day_plan`):

```python
plan_seeds = dict(seeds)
if p.get("day0_plan", False) and day == 0:
    for crop, key in [("MELON", "open_melon_seed"), ...]:
        plan_seeds[crop] = seeds[crop] + p[key]   # <-- LIE to planner
```

The planner then runs `_try_plan` with `plan_seeds`, choosing worker
count and job schedule as if 10 melons were coming.  Only 4 actually arrive,
so `_pick_crop` runs out of melon after 4 plants and re-routes the remaining
scheduled work to other crops (wheat/carrot in the same tile positions), OR
those hands do more watering.  The re-routed labor happens to be net-better
than what the "honest" plan produces.

### Measured (40 seeds vs PASS)

| open_melon_seed | avg      | min     | Δ vs 5 |
|-----------------|----------|---------|--------|
| **5 (old)**     | $95,906  | $60,412 | 0      |
| **10 (new)**    | $97,613  | $65,324 | **+$1,706** |
| 12              | $96,651  | $34,210 | +$744  |
| 14              | $97,845  | $61,103 | +$1,938 |
| 15              | $97,994  | $52,463 | +$2,087 |
| 20              | $96,142  | $46,551 | +$235  |
| 25              | $93,050  | $55,630 | -$2,856 |

Went with `10` (not the peak `15`) because:
- **Safer MIN**: 15 has min $52k, 10 has min $65k
- **60-seed stability**: `10` is +$1,967, `14/15` drop off to +$1,912/+$1,411
- **Head-to-head**: `14` regresses vs sheepbot (19W → 16W), `10` doesn't

The `open_melon_seed=10` value is a genuine parameter choice — passing 10
"schedules" the labor but the actual melon count in shed is still 4.  We
don't over-request seeds (we never ATTEMPT to plant more than we have because
`_pick_crop` respects the depleted virtual seeds counter after each planned
plant).

## PART 2 — strawberry hold-until

### The mechanic

Every day, town shops that demand STRAWBERRY consume 1 or 2 units per
consumption tick (hours 0,4,8,12,16,20).  A typical 2-4 shop mix eats
~10-30 strawberries/day.  We produce fewer than that (only 6-9 strawberry
plants because of the labor bottleneck).  So the STRAWBERRY market inventory
drifts LOWER every day → the price drifts UP:

```
day  STRAW price (seed 1)
 11   $212
 15   $236
 20   $266
 22   $277
 25   $291
 29   $307  <-- 45% higher than day 11
```

If we sell 4 strawberries on day 12 at $212 = $848, but hold them and sell
day 22 at $277 = $1,108 — that's $260 more per 4 units.  Scaled across 30-60
strawberry units per game, this compounds to ~$1k/game.

### Verified (60 seeds vs PASS)

| hold_straw_until | avg      | min     | Δ vs 0 | wins  |
|------------------|----------|---------|--------|-------|
| 0 (sell immediately) | $97,948 | $50,139 | 0     | 0/60 |
| 20              | $98,634  | $51,291 | +$685  | 56/60 |
| 21              | $98,770  | $51,462 | +$822  | 58/60 |
| **22 (new)**    | **$98,906** | **$51,650** | **+$957** | **59/60** |
| 23              | $97,958  | $51,825 | +$10   | 39/60 |
| 24              | $97,935  | $52,038 | -$13   | 39/60 |

**59 out of 60 seeds win.** Extremely consistent.  Peak at 22 because that's
the day AFTER the last town-tick-caused inventory drop that still has time to
be re-filled by our end-of-day dump.

### What we CAN'T hold (measured)

- **WOOL**: Price DROPS from $206 to $124 over the game (wool is one of the
  few products the town doesn't demand heavily).  Any hold loses money.
- **MILK / EGG**: Volume too high (200+ milk units over 30 days).  Shed cap
  100 overflows in <15 days.  Any hold loses HUGELY (~-$40k for milk).
- **MELON**: Price actually drops mid-game as we and the opponent dump.
- **FERTILIZER**: Price monotonically drops.

## Solo progression (all vs PASS)

| session | change | 20-seed avg | 60-seed avg | seed 1 |
|---------|--------|-------------|-------------|--------|
| Start of 25 | (pre-fix) | $97,641 | ~$96,000 | $97,976 |
| 25.1: `open_hires=7, day0_plan=True` | +$3,041 | $100,682 | -- | -- |
| 25.2: `sell_hour=21` | +$1,196 | $101,878 | -- | -- |
| **26.1: `open_melon_seed=10`** | **+$1,967** | $104,480 | $97,948 | $106,832 |
| **26.2: `hold_straw_until=22`** | **+$957** | $105,482 | $98,906 | $108,078 |

**Total gain: +$7,841 / 20 seeds, +$3k / 60 seeds.**

## Head-to-head impact

(10 seeds × 2 seats = 20 games per opponent)

| opp | pre-session 25 | end of 26 |
|-----|----------------|-----------|
| tape_v25 | 0W ours=$34,434 | 0W ours=$33,683 (still contested) |
| sheepbot | 20W margin=+$17k | 19W margin=**+$23k** |
| goosebot | 19W margin=+$45k | 19W margin=+$45k |
| mirror | 16W margin=+$16k | 17W margin=**+$23k** |
| cropbot | 20W margin=+$48k | 20W margin=**+$50k** |
| cowbot | 19W margin=+$21k | **20W** margin=**+$30k** |

Margins are up across the board even where win-counts wobble by 1 seed.
The MIRROR margin jump (+$7k) is the most important — that's the direct
"our bot vs a clone of ours" match.

## Why we still can't beat the tape (honest analysis)

Same-seed trace vs tape (seed 1):

```
       ours-final  tape-final  delta
sold WHEAT      34    470     -436  ($15k gap)
sold STRAW      35    285     -250  ($60k gap)
sold MELON      67    114      -47  ($12k gap)
sold WOOL       66    132      -66  ($14k gap)
sold MILK      231    218      +13  ($3k advantage)
sold FERT      245    245        0
```

We are AHEAD on milk (our herd is efficient), but massively behind on WHEAT,
STRAWBERRY, MELON, WOOL — the CROP+SHEEP economy.  Tape hires **10-14 hands
per day from day 10+** while we max at 8-10 (our planner already decides on
labor by need; forcing more just wastes money).

Attempted this session (all NET-NEGATIVE on 40 seeds):
- `late_hires=10/12/14`: -$2k to -$11k (planner already knows what it needs)
- `open_sheep=3/4`: -$5k to -$16k (extra animals drain cash w/o proportional
  wool demand vs PASS)
- `straw_last_day=15/17/20` + bigger rebuys: -$1k to -$11k (labor limited)
- `melon_rebuy=6/8`: -$8k (cash tied up in seeds we can't water)
- Land-gate relaxations: -$2k to +$300 (SE never worth unlocking with our
  labor bandwidth)

The tape's strategy is **only economic BECAUSE the opponent doesn't fight
back** — when you make US hire+plant that aggressively vs PASS, the extra
labor cost + crop-death from over-planting eats the extra revenue.  Against
the tape specifically, its predictability (pre-compiled route) means we could
front-run its dumps... but its production dwarfs ours enough that even that
doesn't close the gap.

## Files

- `main.py` (1691 lines) — 2 param changes + 6-line hold_straw code addition.
  Prints `$108,078` on seed 1 vs PASS.
- `watch.html` — regenerated (seeds 1/2/3 vs V25 tape).
