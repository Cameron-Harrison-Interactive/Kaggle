# Session 55 — Herd rebalance for H2H (solo down, H2H up)

## Where we are
- Solo: **$80,007 (10 seeds)** — DOWN $1,689 vs S54 ($81,696)
- H2H delta: **-$86,698** — UP $3,008 vs S54 (-$89,706)
- Ship unchanged: `main.py` md5 = `c0c74b43ea577dfb05f1e21dd0f8991b`
- **All 16 animals alive every seed. Zero errors.**

## Key insight this session

**Solo tuning and H2H tuning ARE DIFFERENT problems.**

Testing herd allocations with skip_se in effect:

| herd | solo avg | H2H delta |
|---|---:|---:|
| 4/6/6 | $81,964 | -$87,596 |
| **5/5/6** | **$80,007** | **-$86,698** |
| 6/4/6 | ~$79k | -$88,248 |
| 3/7/6 | $82,695 | -$93,204 |
| 2/8/6 | $81,922 | (not tested — variance high) |

3/7/6 has best solo ($83k) but WORST H2H (-$93k). 5/5/6 has middling solo but best H2H.

**Why**: more sheep = more wool competition. We steal wool inventory space from BT, forcing their wool prices down. More cows = more milk market share for us in solo (no competitor), but no competitive edge in H2H.

Selected 5/5/6 for the H2H optimization.

## Wheat seed cap (+$100)
Capped `target_wheat_seeds` at 25 (was unbounded up to field_size).
Saw seed 1 had 38 unused wheat seeds sitting = $380 wasted.
Effect: +$100 solo, +minor H2H.

## Cash reserve loosened
`cash_reserve = 100 if day==0 else 20` (was 200/50). Frees a tiny bit more
cash for early animal buys. +$268 solo.

## Ablation this session

| change | avg (10 seeds) | delta |
|---|---:|---:|
| S54 baseline (4/6/6, skip_se) | $81,696 | — |
| + wheat seed cap 25 | $81,797 | +$100 |
| + cash reserve tighter | $81,964 | +$268 |
| + herd 3/7/6 | $82,695 | +$700 solo but H2H -$5k |
| ❌ herd 4/7/6 (buys sheep can't fit) | $66,558 | -$15k |
| ❌ herd 2/8/6 (max cow) | $81,922 | ~0 |
| ❌ Water pri default 40→65 | $81,045 | -$700 |
| ❌ Wheat pri 40→42 | $70,548 | -$11k |
| ❌ Wheat batch=4 pickup | $73,272 | -$8k (drop threshold interact) |
| ❌ SW row 6 no melon | $78,020 | -$4k |
| ❌ Straw seed cap 3→5 | $80,166 | -$1k |
| ❌ region bias 500 | $75,814 | -$6k |
| + herd 5/5/6 (final) | $80,007 | -$1.7k solo but +$3k H2H |

## H2H vs BT progression

| session | custom | BT | wins | delta |
|---|---:|---:|---:|---:|
| S47 v2 | $14k | $145k | 0/12 | -$131k |
| S48 v3 | $16k | $142k | 0/12 | -$126k |
| S49 v4 | $24k | $145k | 0/12 | -$121k |
| S50 v5 | $27k | $146k | 0/12 | -$120k |
| S51 v6 | $28k | $144k | 0/12 | -$108k |
| S52 v7 | $37k | $138k | 0/12 | -$100k |
| S53 v8 | $41k | $134k | 0/12 | -$93k |
| S54 v9 | $47k | $137k | 0/12 | -$90k |
| **S55 v10** | **$52k** | **$139k** | **0/12** | **-$87k** |

**Total closing: -$131k → -$87k over 9 sessions (+$44k).**

Best individual H2H: seed 3 delta -$57k (approaching draw range).
Seed 6 delta -$73k (was -$130k earlier).

## Diagnostic finding this session

SW rows 7-9 (wheat tiles) NEVER get planted — 15 tiles sit empty entire game.
Confirmed via tracing: hands have 116 tasks vs 10 units, so PLANT@40 always
loses to WATER/FEED/HARVEST/FERT/CARE/COLLECT_FERT. Not fixable without
region-specialized routing (which itself hurt each time tried).

## Next session (56) plan
1. Focus on H2H-specific tuning
2. Consider **ship-test** — send v10 to Kaggle and see how it performs on ladder
3. Try more subtle strategies: what if we don't unlock SW either (2-quad
   dense play)?
4. Better care+feed sequencing (ensure care+feed same turn to bank bonus)

Target: solo $80k+, H2H delta -$80k. First H2H win becomes plausible.

## Files touched
- `agent.py` — herd 4/6/6 → 5/5/6, cash reserve 200/50 → 100/20
- `economy.py` — wheat seed cap 25
- `plan.py` — attempted removals, all reverted
- `agent/custom_v9_bak/` — S54 snapshot
- `SESSION_55_REPORT.md`

`main.py` UNCHANGED (still Session-42 breaking_tie shipped).
