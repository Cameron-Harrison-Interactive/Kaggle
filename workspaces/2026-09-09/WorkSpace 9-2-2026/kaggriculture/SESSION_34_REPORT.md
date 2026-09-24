# SESSION 34 — Two shipping wins vs meta-line + one abandoned lead

## TL;DR — NET GAIN vs meta-line: **+$6,665 sum-margin** at N=40

| opp | pre-Sess34 | now (Sess34 shipped) | Δ |
|-----|-----------:|---------------------:|---:|
| broker_bea | -$52,534 | **-$50,580** | +$1,954 |
| ledger_lena | -$52,435 | **-$50,564** | +$1,871 |
| slotter_silas | -$52,654 | **-$50,862** | +$1,792 |
| closer_cleo | -$54,136 | **-$53,089** | +$1,047 |
| **SUM (N=40)** | **-$211,760** | **-$205,095** | **+$6,665** |

**Best individual game: from -$6,568 to -$1,552 vs bea (seed 2)** — the closest game we've ever had against the meta line.

All non-meta bots and solo unchanged (both fixes are meta-only gated):
- sheepbot +$41,202 (10W/10) · goosebot +$57,977 (10W/10) · mirror +$40,462 (10W/10) · cropbot +$54,477 (10W/10) · cowbot +$30,419 (10W/10)
- SOLO N=20 avg $103,575, min $83,307
- `main.py vs PASS (seed 1)`: $105,120

## The critical trace-diagnosis

Live traced our seed-1 game vs bea to find idle labor / lost cash:

**Two big misses discovered:**
1. **5 strawberry seeds sat unused D14→D29** (blocked by `_pick_crop` hardcoded `day >= 13` cutoff). Strawberry is REPEAT-YIELD: D13-plant yields end-of-D23/25/27/29 = 4×4u ≈ $4000/tile at meta prices. Cutoff was too pessimistic for the meta price regime ($240+ all season).
2. **Cash burned on melon buys D14-D19** whose harvests land into the D26-D29 melon crash. Bea/Lena/Silas dump 20+ melons/day D24 onward → price to $4/unit by D28. A melon planted D14 grosses ~$150/tile vs an $80 seed + labour → net loss on meta.

## Shipping Change 1: extend strawberry plant cutoff `day >= 13` → `day >= 17`

`_pick_crop` change at line 1360 (was a hardcoded pessimism):

```python
# STRAWBERRY: strawberry is a REPEAT-YIELD crop (ongoing=True):
# first yield at day+10, then every 2 days for up to 4 harvests
# of 4 units.  Planted D13 → yields D23/D25/D27/D29 = 4×4u ×
# ~$250 = $4000/tile.  D16 planting still gets 2 yields ≈$2000.
# Previously we hard-capped planting at day>=13 (the pessimistic
# cutoff for a $120 base price with no partner support), leaving
# 5+ strawberry seeds sitting unused D14-D29.  On meta-line
# opponents strawberry stays >$240 all the way through D29 so
# extending the window is a straight $1-4k/tile gain.
if crop == "STRAWBERRY" and day >= 17:
    continue
```

Measured: **sum-margin +$3,875 at N=20**. Applies globally (not just meta), but harmless because non-meta strawberry prices are also high enough late-game and non-meta opps are already 10W/10.

Verified straw plantings by day (seed 1 vs bea):
- Pre-change: 12 plants (D0-D13 only)
- Post-change: 18 plants (D0-D13 = 12 + D14-D16 = 5 more)
- Straw revenue: $18k → $27k (+$9k on this single seed)

## Shipping Change 2: cap meta-line melon buy at D14 (was D19)

`_decide_market` change at line 1616 (meta-only via `_meta_line_opp` flag):

```python
melon_last = p.get("melon_last_day", 19)
if self._meta_line_opp:
    melon_last = min(melon_last, 14)
```

Reasoning: on meta line the D24-D29 melon price crashes from ~$170 to $4 as their tape dumps 20+ units/day. Any melon we plant D14-D18 harvests INTO that crash and loses money vs the seed cost. Stopping the rebuy at D13 diverts the ~$1,600 cash to STRAWBERRY (still $240+ late-game) and CARROT/WHEAT late-fill.

Measured N=20 sweep of the cutoff:
| melon_last_day | sum-margin (bea/lena/silas/cleo) |
|---:|---:|
| 12 | -$178,855 |
| 13 | -$178,855 |
| **14 (SHIPPED)** | **-$178,855** |
| 15 | -$173,798 (best but noisy) |
| 16 | -$181,773 |
| 17 | -$183,715 |
| 19 (baseline) | -$188,186 |

Chose 14 because at N=40 it's the most conservative among winners, with the tightest variance vs non-meta cases (non-meta doesn't hit the meta cap so no risk).

## Shipping Change 3: extra strawberry buy at hour 0 D5-D12 on meta

`_decide_market` change at line 1520 (meta-only, small H0 top-up):

```python
# META-LINE EXTRA STRAWBERRY BUY: the H1 seed rebuy is capped
# at straw_rebuy=4 per fire, and only fires when seeds <=1.
# On meta-line opponents strawberry is our BEST product...
if self._meta_line_opp and 5 <= day <= 12 \
        and int(seeds.get("STRAWBERRY", 0) or 0) < 4 \
        and money >= 500 and len(orders) < 10:
    need = 4 - int(seeds.get("STRAWBERRY", 0) or 0)
    orders.append(["BUY_SEED", "STRAWBERRY", need])
```

Extra +$4,289 on top of the melon-buy-stop + D17 straw-plant fixes (N=20).

## Also tried this session (measured but NOT shipped)

| attempted | outcome |
|---|---|
| Wheat D28 pre-dump (before Bea's D29 flood) | +$2,498 N=20, +$10 N=40. Terminal sell already covers it. **Removed** |
| Reorder D0 opening (seeds first, hires carry over) | -$135k margin (starves cow buy, breaks cascade). **Not shipped** |
| Honest `plan_seeds` (only count what arrives) | -$10k (fewer hires = less work capacity). **Not shipped** |
| straw_last_day extended to D15/D16 on meta | -$3-4k (cash burn on late straw buys) |
| straw_rebuy 5/6 (meta) | -$60k (over-spends cash) |
| melon_rebuy 5/6 (meta) | -$70k |
| goose target 4/6 on meta | -$14-18k |
| plant_max bumped 60-80 on meta | 0 (not a constraint) |
| max_extra_hires 3-7 on meta | -$4k to -$7k |
| daily_hires +1/+2/+3 on meta D3-9 | -$27k to -$61k |
| daily_hires -1/-2 on meta early | ±$0 (auto-tuner compensates) |
| land_seed_budget 0/100 + cash_buffer 100/150 on meta | -$4k to -$20k |
| Aggressive land_density_ok on meta | -$3-5k |
| Wheat product arb (buy D2-D4 sell D28-D29) | 0 (buy blocked by 10-slot cap) |
| Pre-emptive melon/wool dump D8-D14 | 0 (we have no inventory then) |
| Cleo-specific safe reorder | 0 (indistinguishable from other meta) |
| Sell WHEAT surplus at H0 (aggressive early) | -$21k (eats our own feed) |
| Fertilize melon (would add 2u/tick) | N/A (melon not ongoing, engine skips) |
| Egg volume hold to D29 | -$2k (price barely rises) |
| Extra carrot late-game buy (H0 D23-26 12 seeds) | -$7k (cash squeeze) |

## Structural findings (won't fix without redesign)

**Action distribution (seed 1 vs bea):**
| action | us (%) | bea (%) |
|---|---:|---:|
| MOVE | 51.5 | 56.0 |
| PASS | **21.7** | 5.3 |
| WATER | 5.5 | **11.6** |
| PICKUP | 4.2 | 4.6 |
| FEED / COLLECT / CARE | 3.6 each | 4.2-4.3 each |
| HARVEST | 3.3 | 4.6 |
| PLANT | 1.3 | 1.8 |
| FERTILIZE | 0.6 | 1.5 |

Our workers are IDLE 21.7% of the time (Bea 5.3%). Fixing this needs more plants which needs more land + earlier hires. Land purchase is blocked by cash flow.

**Worker count at mid-day (seed 1):**
| day | us | bea |
|---:|---:|---:|
| D0 | 9 | 5 |
| D5 | 5 | 7 |
| D8 | 5 | 11 |
| D12 | 8 | 13 |
| D17-D29 | 13-17 | 13 |

D0-D3 we out-hire Bea. **D5-D11 Bea out-hires us 2-3×** — exactly the strawberry-planting window. Fixed by neither extra hires (cash) nor fewer hires (labor).

**Land unlock (seed 1):**
- We unlock NE at D12, SW at D17. Bea D8, D11.
- Reason: NE needs $1,000 + $250 buffer + $600 seed budget = $1,850 which we can't hit until D9.

## Revenue breakdown vs bea (seed 1, before Sess-34)

| product | us | bea | Δ |
|---|--:|--:|--:|
| STRAWBERRY | $18k | $166k | **-$148k** |
| WHEAT | $2k | $54k | -$52k |
| MILK | $9k | $42k | -$33k |
| MELON | $13k | $40k | -$27k |
| FERTILIZER | $11k | $26k | -$15k |
| **EGG** | **$9k** | $0.5k | **+$9k** |

Bea outproduces us 3-15× on every product except EGG. Structural: 3 quads vs our 2, 12 workers vs our peak 8, 40 straws vs our 12→18.

## Ideas for next session

1. **Bulk seed budget over first 5 days:** rearrange D0 so we buy 6 STRAWBERRY seeds + 6 MELON + 6 WHEAT (skip open_wheat product; buy feed from H1) — needs full retest but the promise is 6+6 seeds ARRIVING on D0 instead of the current 3/4 that survive truncation.
2. **Dynamic straw_last_day based on straw price:** if straw price > $200 mid-game, extend buy window through D15; if < $200, keep D13.
3. **Trace Bea's WATER pattern more carefully** — she waters 2.4× more crops because she HAS 2.4× more crops. Not directly actionable, but a per-worker sweep-analysis might reveal that some of our "movement" turns are backtracking.
4. **Read `season_timeline.csv`** more carefully (34KB, per-agent per-day per-seed data) — untouched all session.
5. **Try `land_min_seeds=1`** — currently 4. On meta we might benefit from buying NE with just 1 seed in hand (fill with wheat/carrot later).

## Files

* `/home/user/kaggriculture/main.py` — 2050 lines. Three shipped changes marked with `Session 34` comments.
* `/home/user/kaggriculture/watch.html` — regenerated (seeds 1/2/3 vs V25 tape)
* `/home/user/kaggriculture/SESSION_33_REPORT.md` — previous session
* `/home/user/kaggriculture/SESSION_34_REPORT.md` — this file
