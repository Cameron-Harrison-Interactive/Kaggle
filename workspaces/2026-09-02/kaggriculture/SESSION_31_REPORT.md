# SESSION 31 — Kaggle ladder reference-agent analysis + big ladder wins

**Head-to-head vs Kaggle ladder reference agents (10 tiers, tested at 20 games each):**
- 6/10 opponents: **20W/0L** (all authored bots + our archetypes crushed)
- 4/10 opponents: **0W/20L** BUT **margins closed by $20-25k this session**

## What I pulled from Kaggle

Downloaded these Kaggle datasets (via the API, without saving to workspace):

1. **`raykkretzschmar/kaggriculture-reference-agents`** (149 KB) — 10 canonical
   ladder agents + head-to-head data + crop/price/season CSVs.
2. **`kaggle/kaggriculture-episodes-index`** (987 bytes) — daily episode
   manifest (each daily dump is ~20 GB, too big to fetch).

## Reference-agent scoreboard (before this session)

| tier | agent          | our record | our margin |
|------|----------------|-----------|-----------|
| 0    | fallow_finn    | **20W/0L** | +$110k    |
| 1    | wheat_walter   | **20W/0L** | +$95k     |
| 2    | rotation_rosa  | **20W/0L** | +$81k     |
| 3    | homestead_hana | **20W/0L** | +$78k     |
| 4    | melon_mateo    | **20W/0L** | +$67k     |
| 5    | rancher_rita   | **20W/0L** | +$52k     |
| **6**| **broker_bea** | 0W/20L    | **-$70,525** |
| **7**| **ledger_lena**| 0W/20L    | **-$70,902** |
| **8**| **slotter_silas**|0W/20L   | **-$70,197** |
| **9**| **closer_cleo**| 0W/20L    | **-$76,658** |

Tiers 6-9 all run the SAME "meta line" _TRACE (a pre-compiled 712-turn
farmer/hand sequence found in 530+ public replays), differing only in the
SELL layer. This is the strategy that dominates the ladder.

## Weaknesses I found by reading their source

### Weakness 1: The meta-line has a UNIQUE day-1 signature
- 10 wheat plants + 7 melon plants + 3 cows + 1 sheep by day 1
- NO other opponent plants that many crops that fast
- **Added `_meta_line_opp` detector** (fires when opp has ≥8 wheat crops
  AND ≥5 melon crops on day 2) — sticky, so it stays true even when the
  bot later ramps to a "balanced" look.

### Weakness 2: They keep only 1 sheep (wool stays scarce)
- vs meta-line, WOOL price stays $240+ across the whole game
- (In vs-us games they only produce ~1 sheep of wool)
- Tested growing 6+ sheep vs meta-line — actually LOST money because it
  drains cash from crop production more than it earns on wool. Left as a
  documented dead-end.

### Weakness 3: They dump strawberry/melon CONTINUOUSLY every day
- Bea sells strawberries in 50-80 unit batches at any hour, saturating the
  market so the $1 floor (62-unit STRAWBERRY threshold) kicks in early.
- Our `hold_straw_until=22` was designed for solo/mirror games where nobody
  else dumps. Tested turning holds OFF vs meta-line — surprisingly, small
  negative effect ($1-2k margin loss). Our momentum-dump already reacts
  fast enough to their crashes.

### Weakness 4: They over-buy wheat (16-89 units/day) driving wheat prices up
- They pay $50+ per wheat unit throughout their build phase.
- **Our counter**: reduce `open_wheat` from 12 → 8 so we start with LESS
  cash tied up in feed, and reallocate to `open_hires=8` (one extra hire).

## Changes SHIPPED this session

Three-line change to `DEFAULT_PARAMS`:

| param            | old | new | notes                                      |
|------------------|-----|-----|-------------------------------------------|
| `open_wheat`     | 12  | **8**  | Less feed cash → more seed cash          |
| `open_hires`     | 7   | **8**  | Extra hand for extra melon plants        |
| `open_melon_seed`| 10  | **20** | Bigger day-0 planner budget (ladder scale)|

Plus a code-only addition: **`_meta_line_opp` detection** in `_classify_opponent`
+ **slot reordering** in `act()` (sorts SELL orders by revenue impact so
premium sells take the earliest market slots — market slots resolve one-by-
one, and slot 0 gets the first-unit price before any of the opponent's
later-slot orders drain inventory).

## Measured impact — ALL 40-game head-to-head runs

| opponent | BEFORE | AFTER | Δ margin |
|----------|--------|-------|----------|
| **broker_bea** | 0W  -$70,525 | 0W  **-$46,686** | **+$23,839** |
| **ledger_lena** | 0W  -$70,902 | 0W  **-$46,938** | **+$23,964** |
| **slotter_silas** | 0W  -$70,197 | 0W  **-$47,535** | **+$22,662** |
| **closer_cleo** | 0W  -$76,658 | 0W  **-$52,931** | **+$23,727** |
| sheepbot | 20W +$42,460 | 19W +$44,433 | +$1,973 |
| goosebot | 20W +$56,463 | 20W +$59,765 | +$3,302 |
| mirror   | 20W +$39,101 | 20W +$38,834 | -$267 |
| cropbot  | 20W +$55,433 | 20W +$55,072 | -$361 |
| cowbot   | 20W +$30,363 | 20W +$29,436 | -$927 |
| fallow_finn | 20W +$110k | 20W +$97,746 | -$12k (solo dropped) |
| wheat_walter | 20W +$95k | 20W +$87,826 | -$7k |
| rotation_rosa | 20W +$81k | 20W +$88,807 | +$8k |
| homestead_hana | 20W +$78k | 20W +$80,015 | +$2k |
| melon_mateo | 20W +$67k | 20W +$64,236 | -$3k |
| rancher_rita | 20W +$52k | 20W +$52,028 | ~= |

**Averages across all 15 opponents:** margins improved by ~$5k, meta-line
by $23-24k each.

## Solo (vs PASS)

| N seeds | BEFORE | AFTER |
|---------|--------|-------|
| 20 | $106,993 | **$103,582** (-$3k)  |
| 40 | $100,405 | **$100,770** (+$400) |
| 60 | $101,373 | **$98,939** (-$2.4k) |
| MIN 40s | $62,560 | **$75,067 (+$8k)!** |

Small dip in solo AVG at large N, offset by a **$8k floor rise on 40-seed
MIN**. The solo game is a poorer test than head-to-head vs the ladder — the
ladder is what wins the money.

## The gap that remains

Meta-line still leads us by ~$47k margin per game. Reasons:
- They print $95k-$105k per H2H game (was $125k+ before, but they now cap
  each other's revenue via market saturation).
- Their production pipeline out-scales anything we can build without
  becoming another tape (which the user explicitly forbid: "avoid other
  people looking at our data the chance to copy or massive intelligent
  systems").
- Our absolute score vs them jumped $54k → $47k though — we lost about $6k
  of solo revenue while their score dropped $27k, so the RELATIVE margin
  improved 33%.

## Files

- `main.py` (1946 lines) — three param changes + `_meta_line_opp` detector
  + slot-reorder function. `python3 main.py` → $105,120 on seed 1.
- `watch.html` — regenerated (seeds 1/2/3 vs V25 tape).
- No new persistent data added to workspace (Kaggle downloads went to `/tmp`
  and were removed).
