# Session 53 — Custom Bot v8: 6 cows + wheat-heavy south

## Where we are
- **S47 v2**: solo $22,278
- **S48 v3**: solo $28,962 (+$6,684)
- **S49 v4**: solo $43,556 (+$14,594)
- **S50 v5**: solo $56,292 (+$12,736)
- **S51 v6**: solo $60,890 (+$4,598)
- **S52 v7**: solo $70,307 (+$9,417)
- **S53 v8**: solo **$77,214 (10 seeds)** — **+$6,907 (+10%) vs S52**
- Ship unchanged: `main.py` md5 = `c0c74b43ea577dfb05f1e21dd0f8991b`
- **All 16 animals alive on every seed. Zero errors.**

## What changed this session

### 1. **BT tape analysis** (setup for wins)
Instrumented BT solo shed-delta count:
| item | us S52 | BT | gap |
|---|---:|---:|---:|
| WHEAT | 136 | 879 | -743 (~$18k) |
| FERT | 109 | 323 | -214 (~$21k) |
| STRAW | 82 | 187 | -105 (~$15k) |
| WOOL | 82 | 183 | -101 (~$20k) |
| MILK | 116 | 150 | -34 (~$5k) |
| MELON | 108 | 6 | +102 (~$25k advantage) |
| EGG | 193 | 0 | +193 (~$10k advantage) |

Insight: BT dominates wheat/fert/wool. We over-index on melon/egg.

### 2. **6 cows instead of 5** (+$1k)
Herd 4/6/6=16. Milk = $160/unit is best animal ROI.

### 3. **Remove SW/SE row 8 melon → wheat** (+$5.7k)
Biggest win: SW row 8 + SE row 8 were MELON. Converted to CROP wheat:
- Wheat tiles: 40 → 50
- Melon tiles: 25 → 15
- Better feed reserve + more wheat surplus to sell

Melon at row 8 planted D11-D13 → single harvest D23-D25 with declining prices.
Meanwhile wheat at row 8 cycles 4x through end-game.

### 4. **NW/NE tap-drop hand economy** (analyzed, kept as-is)
BT does 91 fewer DROP + 154 fewer PICKUP than us. Tried batch=6 wheat and
threshold=8/10 — both collapsed (immediate-drop loops or shed starvation).
Kept batch=3, threshold=6.

## Ablation this session

| change | avg (10 seeds) | delta |
|---|---:|---:|
| S52 baseline | $70,307 | — |
| + cow 5→6 (herd 4/6/6) | $71,538 | +$1,231 |
| + **SW/SE row 8 melon → wheat** | **$77,214** | **+$5,676** |
| **10-seed final** | **$77,214** | **+$6,907** |
| ❌ cow 6→7 sheep 4→3 | $67,886 | -$4k |
| ❌ SW row 8 → PASTURE | $53,686 | -$18k (starved variance) |
| ❌ NW row 0 → STRAW | $51,720 | seed collapse |
| ❌ NE row 0 melon → wheat | $28,689 | catastrophic (no cash) |
| ❌ SW/SE row 6 melon → wheat too | $71,043 | slight regress |
| ❌ Wheat PLANT priority 45 | $56,122 | -$21k (starved water) |
| ❌ Wheat PLANT priority 72 dynamic | $17,283 | catastrophic |
| ❌ Wheat PICKUP batch=6 | $2,186 | infinite drop loop |
| ❌ DROP threshold 6→8 | $59,972 | -$17k |
| ❌ Hires_target 8 early | $52,613 | -$25k |
| ❌ 2 land buys per day | $74,754 | -$3k |
| ❌ Goose 6→7 | $72,256 | -$5k |

## H2H vs BT

| metric | S47 | S48 | S49 | S50 | S51 | S52 | **S53** |
|---|---:|---:|---:|---:|---:|---:|---:|
| custom H2H avg | $14k | $16k | $24k | $27k | $28k | $37k | **$41k** |
| BT H2H avg | $145k | $142k | $145k | $146k | $144k | $138k | $134k |
| **wins vs BT** | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | **0/12** |
| **avg delta** | −$131k | −$126k | −$121k | −$120k | −$108k | −$100k | **−$93k** |

**First time below -$95k.** Best-seed delta -$54k (getting close). 

Some seeds show custom hitting $60k H2H — approaching BT $110k territory.

## Progression summary

| session | solo | H2H delta | key win |
|---|---:|---:|---|
| S47 v2 | $22,278 | −$131k | scheduler |
| S48 v3 | $28,962 | −$126k | strawberry + fert |
| S49 v4 | $43,556 | −$121k | melon + emergency wheat |
| S50 v5 | $56,292 | −$120k | CARE priority |
| S51 v6 | $60,890 | −$108k | fert-fix + multi-buy + stickiness |
| S52 v7 | $70,307 | −$100k | PLACE priority + cow-heavy herd |
| **S53 v8** | **$77,214** | **−$93k** | **BT tape analysis + wheat-heavy south** |

Total closing across 7 sessions: **−$131k → −$93k = +$38k**.

## Root diagnosis of remaining ~$60k solo gap

BT solo $150k, us $77k = $73k. Diagnostic:
- BT sells 879 wheat @ $25 = $22k. We sell ~$3.4k in wheat. Gap $18k.
- BT sells 323 fert @ $100 = $32k. We sell $11k. Gap $21k.
- BT sells 183 wool @ $200 = $37k. We sell $16k. Gap $21k.
- BT sells 187 straw @ $150 = $28k. We sell $12k. Gap $16k.
- BT sells only 6 melon. We sell 100+ @ $200 = $20k. Our advantage.

Biggest remaining lever: **more wool** (need more sheep or better care). Can't add more pastures without hurting cash flow. Sheep target is 4.

## Next session (Session 54) plan

1. **Forward-search wrapper** — proven at +$1.5k solo in S46; base is much stronger now (from $22k to $77k)
2. **Investigate wool gap** — 183 vs our 82. 4 sheep × 10 productions × 2 units (care) = 80. Getting max already! Would need more sheep tiles.
3. **Try 5 sheep + 5 cow** more carefully with tuning
4. **Consider consolidating**: current bot is complex. Consider shipping-test at some point

Target: solo $85-95k, H2H delta −$80k.

## Files touched
- `plan.py` — SW/SE row 8 MELON → CROP (10 wheat tiles gain)
- `agent.py` — cow_target 5 → 6
- Tests: many failed, many documented above
- `agent/custom_v7_bak/` — snapshot of Session 52 code
- `SESSION_53_REPORT.md`

`main.py` UNCHANGED (still Session-42 breaking_tie shipped).
