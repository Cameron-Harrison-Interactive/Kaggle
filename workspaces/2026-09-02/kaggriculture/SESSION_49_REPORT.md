# Session 49 — Custom Bot v4: Melon + Emergency Wheat Buy (multi-session, NO SHIP)

## Where we are
- **Session 47 v2**: solo $22,278 avg
- **Session 48 v3**: solo $28,962 avg (+$6,684)
- **Session 49 v4**: solo **$43,556 avg (10 seeds)** — **+$14,594 (+50%) vs S48**
- Ship unchanged: `main.py` md5 = `c0c74b43ea577dfb05f1e21dd0f8991b` (Session-42 breaking_tie)
- **All 11 animals alive on every seed (10 seeds tested). Zero errors.**

## What changed this session

### 1. Melon crop (NE row 0 + SW row 6 + SE row 6 = 15 tiles)
- New `MELON` role in `plan.py`, `desired_crop_for()` returns MELON
- **NE row 0 unlocks D0, plant D1, harvest D13** — captures 1 full cycle
- SW/SE rows planted right after land unlocks (D11-D12)
- Melon = 6 units × ~$250 base = ~$1500/tile, ONE-time harvest, no fertilizer needed
- Bought at $80/seed, capped at 3/turn, only up to D17
- Sells continuously (highest sell priority)

**Impact of melon alone**: +$14k avg vs S48 baseline. Also incidentally accelerates SW/SE unlocks from D13/D18 → D11/D12 because early melon sales generate cash.

### 2. Emergency wheat buy from market
- When shed wheat < `current_herd × 2` AND money > $200, buy 3-days worth of wheat from market
- Prevents late-game (D25-D29) starvation cliffs: seed 5 previously lost 10 animals D29→D30 because production dipped below feed consumption
- Cheaper to buy wheat @ $25 than lose a $500 sheep

### 3. Late-game wheat reserve bump
- D25+ reserve raised from `current_herd × 10` to `current_herd × 15` and `planned × 5`
- Keeps big feed buffer during end-game field productivity dip

### 4. Region-specialization: TRIED, REVERTED
- Full experiment: `_home_quad_for_unit()` assigns hands to NW/NE/SW/SE by index
- `_region_bias()` adds ±bonus to task scoring based on task's quadrant vs hand's home
- **All tunings hurt**: BONUS=1500/PENALTY=300 → $5.3k avg (animals starved), BONUS=600/PENALTY=0 → $22.3k, BONUS=200/PENALTY=0 → $22.3k
- Root cause: region bias adds friction to legitimate cross-quad work (an SE-home hand walking 12+ steps to feed a NW animal)
- **Kept the infrastructure** (unit_home computation, `_region_bias`) but set `REGION_BONUS = 0` for now. Available for future targeted experiments.

## Ablation this session

| change | avg (5 seeds) | delta |
|---|---:|---:|
| Session 48 baseline | $29,604 | — |
| + melon in SW row 6, SE row 6 | $32,700 | +$3,096 |
| + melon NE row 0 too | $46,403 | +$16,799 (seed 5 lost 10 animals) |
| + emergency wheat buy + higher D25+ reserve | **$44,809** | +$15,205 (all animals safe) |
| **10-seed final** | **$43,556** | **+$14k vs S48** |
| ❌ region bias (all tunings) | $16-22k | -$8 to -$14k |
| ❌ straw seeds buy 10/turn (up from 3) | $28,684 | -$1k (cash spikes hurt) |
| ❌ melon on 2 SW+SE rows | $17,466 | -$15k (crowded out wheat feed) |

## Preliminary H2H vs BT (12 games, 6 seeds × 2 seats)

| metric | Session 47 | Session 48 | **Session 49** |
|---|---:|---:|---:|
| custom H2H avg | $14,000 | $15,916 | **$23,853** |
| BT H2H avg | $145,032 | $142,062 | $145,348 |
| **wins vs BT** | 0/12 | 0/12 | **0/12** |
| **avg delta** | −$131,033 | −$126,146 | **−$121,495** |

+$8k H2H improvement, but still 0/12 vs BT. BT solo $150k, ours $44k — gap closing but production ceiling still ~3x.

## Root diagnosis of remaining gap

BT/Ryo achieve $150-170k solo from:
1. **Bigger herd**: 8 cows + 12 sheep + geese (~20 animals) — needs more pastures + coops
2. **Bigger wheat field**: 30-40 wheat tiles + heavy feed rotation
3. **More hires**: 11-12/day funded by early production revenue
4. **Continuous market pressure**: sells every hour to move inventory

Our current bot has 5 pasture + 4 coop slots per north quad = 11 max animals. To match meta:
- Need MORE pasture/coop capacity (double up, or use more of NE row 3 for pastures)
- Need bigger wheat production so more animals eat without starving
- **Doubling the herd doubles fertilizer output → doubles strawberry production**

## Next session (Session 50) plan

1. **Grow the herd**: expand pastures to 8 (add SW row 8 as PASTURE)
2. **Bigger wheat field**: replace some NW crop with... actually NW row 3/4 already dense. Move animals to SW row 8 (freeing NW row 3 for more crop).
3. **Boost hires**: dynamic hiring — hire as many as $$ allows, cap 15/day
4. **Add continuous market maker** — an idle-sell that fills unused market slots each hour

Target: solo $60-80k, H2H delta down to -$80k.

## Files touched
- `plan.py` — added MELON role, redistributed SW/SE rows, NE row 0 → MELON
- `tasks.py` — melon plant priority (72), MELON harvest fix (target=min(max_yield, 1+window_len))
- `economy.py` — melon seed buy, melon sell priority, wheat emergency BUY_PRODUCT, D25+ reserve bump
- `assigner.py` — region infrastructure added (BONUS=0 keeps it inert), documented for future work
- `agent/custom_v3_bak/` — snapshot of Session 48 code (regression checkpoint)
- `SESSION_49_REPORT.md`

`main.py` UNCHANGED (still Session-42 breaking_tie shipped).
