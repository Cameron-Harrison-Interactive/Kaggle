# SESSION 128 — Tue 2026-09-08 (evening)
## Top-16 meta cracked + engine source decoded + the walk gap quantified

**LIVE:** 56079632 router **2483.7** · 56100058 climbing · quota 3 left, lifetime 70. **NO POSTS** (mandate holds).

---

## 1. THE TOP-16 IS ONE NOTEBOOK FAMILY (72 tapes mined → analysis/TOP16_MINED_0908.json)

60+ of 72 top-16 tapes are the **same build** (one public kernel, like the TT army):
- **Herd: 6 COW + 1 SHEEP** (or 5C/5S). Geese 0-1. No tomato (22 of 24 agents: zero tomato seeds).
- **Crops TOTAL: 22 wheat, 13 strb, 2 melon, 2 carrot seeds** for the whole game (we plant 100+).
- **Land: #2 at d6, #3 at d10-11** (3 quads, ~49 tiles max — small farm).
- **Wheat desk**: BUY_PRODUCT WHEAT 38-236 units/game, sell late (Dimenta: buy 38 early, **dump 345 on d26-29**; Dusta: 150-250/day round-trips d11-21).
- H2H vs each other: **$100-140k each side.** The $139-141k leaders (Ryo c9/s5, Dusta c7/s13 desk-205, Subramanya c12/s13 desk-236) just run the same core bigger.

## 2. ENGINE SOURCE FULLY DECODED (kaggressu…/kaggressu.py — read directly)

- **TOWN DRAIN = the price engine**: every 4 steps each unlocked shop drains its products (6×/day, ×2 single-product shops); new shop every 3 days up to 8; town center drains 1 of everything daily. All prices rise all game unless players flood supply. **Shops visible in obs.town — future drain is computable.**
- **Zero-spread round-trips**: BUY quotes at post-buy inventory → intraday desk cycling nets exactly ZERO. Desk profit = overnight appreciation only, **bounded by shed cap 100 ≈ $2-3k/game**. The #1's "1123 wheat carry" is mostly zero-sum cycling + squeeze; not replicable past shed cap.
- **End-of-day force-drop**: ALL unit inventories dropped into shed up to 100; **overflow DISCARDED**. Hands can't warehouse overnight.
- **CARE bonus**: care+feed same day → pending +1; production day adds 1+pending. **Full care = 3x cows (1.5 milk/day), 4x sheep.** We're already at ~1.9/day bursts (coverage largely working).
- **BUILD_COOP/PASTURE free** (empty tile → structure). Animals must be PLACE'd on matching structure from shed.
- Our animal placement is already tight (cluster at shed, spread 10). Geese sit at cap 4 for days (harvest ≥3 threshold) — but fixing costs more walk than eggs are worth.
- **Market obs is full-info**: obs.market = {inventory, prices} live every step.

## 3. H2H price matrix vs router (analysis/H2H_PRICE_MATRIX_0908.json)

Vs US the router crashes NOTHING (mirror crashes need two routers dumping): prices rise smoothly — milk 160→310, strb 120→246, wheat 25→46, wool 200→239, melon recovers 76→118 after d11 dump, **fert crashes 100→29** (both flood it), carrot flat 36. Net inventory drift: WHEAT −402, MILK −297, STRB −224, FERT +355, EGG +142.
**Router makes +$10k/day steady from d12; we burst $12.6k at melon-dump then go broke to d20** ($367 at d15) — asset purchases eat everything; our labor converts inputs at half their rate.

## 4. THE WALK GAP (final quantification)

Same op mix, same hand counts, similar PASS rates. Per productive action: **we walk 2.7 steps, elites walk 1.3.** Per day: we complete 56 productive ops, elites 103 (43% of unit-steps vs our 23%). This is pure routing/choreography — the taped-labor moat.

## 5. Builds tested this session

| build | change | solo 5-seed mean | verdict |
|---|---|---|---|
| v32.0 | aggressive hold (no daily sells) | $72.9k | **FALSIFIED** — held inventory starved sheep buys; assets beat appreciation |
| **v32.1** | v31 + d26 dump window + take-profit + milk desk (dormant) | **$79.7k** | **INSTALLED — new best own build** |
| v33 | fixed index-based sectors | $73.9k | FALSIFIED — hands walk back to assigned wedge |
| v33b | no sectors (pure nearest) | $74.9k | FALSIFIED — position-based sectors are a tuned win |
| v34 | CARE prio 0 + goose harvest ≥2 | $76.5k | FALSIFIED — care starves watering; goose trips cost more than eggs |
| v32.1 H2H vs router | 10 seeds | 0-10, $32.5k vs $140.2k | market layer = noise in H2H |

**Every planner perturbation loses — v28.19's labor tuning is a genuine local optimum.** The remaining labor gain is not reachable by parameter tweaks.

## 6. The one path left (next session)

**Offline tape optimization of our own choreography**: record v32.1's labor on seeds (task set is fixed by our own build), compute the optimal routing offline (the 2.7→1.3 gap is worth ~+$25-40k/game), replay optimized labor with live market brain + planner fallback on invalid actions. This is the tree_lock methodology applied to our own tapes — the only architecture that survives replay (assumptions match our own agent).
