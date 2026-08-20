# Adapt-2-Survive (v18)

## Product rule
**Routing is frozen** (notebook-strict dual-seat tape + WEED repair).  
**Only crops / animals / purchases / sell ranking change per match.**

```
exact route labor (MOVE/WATER/PLANT positions)
        +
Adapt-2-Survive:
  classify opponent → mode
  rewrite PLANT crop types + seed buys
  optional skip late BUY_ANIMAL
  rank existing SELL slots
  terminal liquidation
```

## Opponent modes
| Mode | Detection | Adaptive response |
|------|-----------|-------------------|
| `anti_seb` | SE unlock / early multi-quad + wheat | sensors; sell rank |
| `anti_buildA` | melon≥10 d0–2 cow-led | skip BUY_ANIMAL after d14 if herd≥13 |
| `anti_straw` | straw_flood family **and** market glut | wider tomato window (d6–14), stronger convert |
| `default` / `mirror` | everyone else | v15 tomato thresholds only (d7–13, inv>10050 or px<100) |

## What is legal
- Change `PLANT X` → `PLANT Y` (same worker, same tile)
- Append `BUY_SEED TOMATO` when glut
- Drop `BUY_ANIMAL` late vs Build-A when already full
- **Permute** existing SELL slots (`_rank_sell_slots`)
- WEED DIG + replay

## What is illegal (never)
- MOVE/WATER path changes
- plant-on-empty
- create/resize SELL quantities except behind-dump (disabled; failed keep-gate)
- water_optimizer overlays

## Keep-gate (local)
| Matchup | Result |
|---------|--------|
| vs 14.5 seeds 1–5 | **5/5 WIN** (d −283..+8) |
| vs HS | **+1.8k** vs pure v15 |
| vs Seb | **+4.8k** vs pure v15 |
| starter | **$136,485** |

## Failed experiments (do not revive)
- Market SELL holds/dumps vs mirrors: −7k to −49k
- Aggressive tomato on opp straw count alone: −8k to −49k
- Runtime water coverage steals: −30k to −85k
