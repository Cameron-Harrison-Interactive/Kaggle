# Session 58 — Priority Tuning Sweep (no ship, waiting on v10.5 ladder)

## Where we are
- Ship: **v10.5 on Kaggle** (submission 55748620 from S57, pending final score)
- In dev: **v10.7** — solo $80,113, H2H BT **-$74,102** (20-seed avg)
- All 16 animals alive every seed
- User said: no shipping others' work; tune while we wait

## Priority sweep methodology

Ran 4-seed × 2-seat H2H vs BT for each priority value across:
- CareTask: {50, 55, 60, 65, 70, 75}
- FertilizeTask: {82, 85, 88, 92, 95}
- HarvestAnimalTask: {55, 60, 65, 70, 75, 80}
- CollectFertTask: {45, 50, 55, 60, 65, 70}
- PlaceAnimalTask: {65, 70, 75, 80, 85}
- WaterTask urgent: {80, 85, 90, 95}
- WaterTask in-window: {75, 80, 82, 85, 88}
- MIN_MELON_PRICE: {80, 100, 120, 150, 200}
- straw price gate: {0, 100, 120, 150, 180}
- wheat_emerg_buy_threshold: {1, 2, 3, 4}x herd
- wheat_reserve multiplier: {5, 7, 8, 10, 12, 15, 20}x herd

## Winners

| param | was | now | H2H BT delta change |
|---|---:|---:|---:|
| CareTask.priority | 60 | **65** | +$4k |
| FertilizeTask.priority | 88 | **85** | +$4k |
| WaterTask.in_window | 82 | **80** | ~= |
| MIN_MELON_PRICE | 100 | **80** | ~= |
| straw price gate | 120 | **0** (always sell) | +$0.5k |
| wheat_emerg_buy_threshold | 2x herd | **1x herd** | +$3k |

## Full H2H progression

| session | solo | H2H BT | notes |
|---|---:|---:|---|
| S47 v2 | $22,278 | -$131k | |
| S53 v8 | $77,214 | -$93k | |
| S55 v10 | $80,007 | -$87k | shipped |
| S57 v10.5 | $80,007 | -$87k | shipped, awaiting |
| **S58 v10.7** | **$80,113** | **-$74,102** (20-seed) | best ever |

## H2H vs all opps (12-seed avg)

| opp | S55 | S57 | **S58 v10.7** |
|---|---:|---:|---:|
| BT | -$87k | -$87k | **-$79k** |
| V41 | -$120k | -$115k | -$111k |
| moon | -$90k | -$90k | -$88k |
| soil | -$120k | -$116k | -$111k |
| amey | -$90k | -$90k | -$88k |
| multiroute | -$90k | -$90k | -$88k |

Best individual matchup: **BT delta -$74k on 20 seeds** (was -$86k).

## What made the difference

The priority tuning revealed CARE at 65 (not 60) beats WATER competition on
key days. FERTILIZE at 85 (not 88) balances better with FEED/WATER —
apparently 88 was TOO high causing hands to fertilize plants when higher-EV
work was available.

## Failed experiments this session

- Reduce cash reserve to 20 (tested via sweep, worse)
- Skip SW rows 7-9 CROP (lose solo $500)
- NW row 0 = CARROT (cash drain, -$6k solo)
- BUY_PRODUCT fert opportunistically (creates own glut)
- BUY_PRODUCT wheat + BUY sheep D0 (blows cash, solo drops $30k)
- Skip animals until SW unlocked (kills fert output)

## Next actions

- Wait for v10.5 ladder score (should stabilize in next 12-24 hours)
- If ladder result > breaking_tie 1862, ship v10.7 with these tuning gains
- Continue H2H tuning of remaining priorities
- If v10.5 does poorly on ladder, we know solo != H2H doesn't translate

## Files
- `agent/custom/*` — v10.7 tuning applied
- `agent/custom_v107_bak/` — snapshot
- `agent/custom_v105_bak/` — v10.5 snapshot (what's on Kaggle)
- Ship unchanged: `main.py` = v10.5 candidate (from S57)
