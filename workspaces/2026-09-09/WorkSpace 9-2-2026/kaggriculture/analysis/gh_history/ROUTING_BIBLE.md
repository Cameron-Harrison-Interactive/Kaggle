# Routing Bible (Chat-Log-5 + live 55391953)

## Absolute rules (every path rewrite that broke keep-gate)
| Idea | Result | Source |
|------|--------|--------|
| Block locked SE walks | −45k collapse (tape paths SW via SE) | Chat-Log-5 |
| Block locked shed exits | 100k→25–55k | Chat-Log-5 |
| SE unlock (4th quad) | −9.5k vs 14.5 | Chat-Log-5 |
| SW animal mirror | −17k | Chat-Log-5 |
| MOVE→PLANT / auto-fill all empties | 18 weeds, score 0 / −15k to −44k | Chat-Log-5 + v16.4 tests |
| Water path rewrites (MOVE→WATER freely) | −30k to −85k | v16.3 experiments |
| Idle PASS→PLANT (straw/melon/any) | −15k to −44k seed steal | v16.4 |
| Idle PASS→PLANT wheat-only reserved | still −10k to −23k | v16.4b |

## What IS allowed (proven)
1. **Tape backbone** — full 719-step seat routes, never spliced mid-game
2. **`_water_optimizer`** (v14.5/v15) — empty/dupe WATER→PASS; PASS/MOVE on CU1 thirsty→WATER only if no hungry animal ≤3 and not carrying wheat
3. **`_weed_repair_action`** — DIG then replay intended plant/build
4. **`_tomato_hedge`** — market-only crop *choice* (BUY_SEED tomato + convert PLANT straw→tomato under glut). Does **not** move workers.
5. **PASS on WEED→DIG** / **PASS on animal+fert→COLLECT** — standing-tile only
6. **Sell ranking** / terminal sweep — market only
7. **Adaptive memory** — classify opp family; must not rewrite paths

## Live ep 91481479 (you linked)
- Us seat0 **$78,819** vs D S S Kumar **$65,761** — WIN
- Water d11–d25 solid (your observation matches: weeds=0 through d20)
- SW corner weeds appear **d24** (endgame stretch), not pathing into locked tiles
- SW empty strips after unlock = **tape plant order**, not a bug to “fix with pathing”
- Adaptive tomato_acts=0 this match (no straw glut trigger) — plant mix is tape

## Live portfolio (55391953, 7 scored)
| Ep | Us $ | Opp $ | Notes |
|----|------|-------|-------|
| 91480578 | 149747 | 87889 | Best — seat1 |
| 91478765 | 141311 | 56674 | |
| 91477855 | 141264 | 19871 | Melon-only opp |
| 91483319 | 98119 | 88359 | |
| 91479665 | 92038 | 22513 | |
| 91482398 | 82018 | 39936 | |
| 91481479 | 78819 | 65761 | Contested |

Corner weeds d13 (NW 0,0/1,0) still appear on some wins when CU1 water is missed — water optimizer helps but cannot invent multi-step routes to far corners without desync.

## Adaptive scope (user directive)
**ONLY** change: crops / animals / buy-sell timing (market + plant *type* on existing PLANT verbs).
**NEVER** change: walk paths, unlock order, land timing beyond tape, plant positions.
