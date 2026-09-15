# SESSION 120 — Tree Retraining + Herd-Scale Authorship: Both Measured, Both Falsified

**Date:** 2026-09-07 ~20:40 UTC · **Directive:** (20:15) build both remaining upgrade paths, no submissions, gate vs our winners + the metas that beat us.

## What was run

**1. Tree-lock training harness** (router with `_TREES` replaced by forced leaves; 6 conditions × 6 opponents × 4 seeds, both seats):
opponent pool = router (twin), v16, hamburger, JOSHNA fork, keiz-tape, CD-tape — our winners + every meta class that beats us. Full table in `analysis/TREE_RETRAIN_RESULTS.json`.

| condition | vs router (twin) | vs v16 | vs hamburger | vs JOSHNA | vs keiz | vs CD |
|---|---|---|---|---|---|---|
| **baseline (verbatim)** | **0-0-4T** | 4-0 | 4-0 | 4-0 (+228k) | 4-0 (+514k) | 4-0 (+646k) |
| lock0 | 0-4 (−35k) | 4-0 | 4-0 | 4-0 | 4-0 | 4-0 |
| lock1 | 0-4 (−40k) | 4-0 | 4-0 | 4-0 | 4-0 | 4-0 |
| lock2 (7C) | 2-2 (−26k) | 4-0 | 4-0 | 4-0 | 4-0 | 4-0 |
| lock3 | 1-3 (−32k) | 4-0 | 4-0 | 4-0 | 4-0 | 4-0 |
| lock4 (8S) | 0-4 (−37k) | 4-0 | 4-0 | 4-0 | 4-0 | 4-0 |

**Tree retraining = FALSIFIED.** Any fixed tape loses to the shop-adaptive routing (the twin army punishes rigidity); every non-twin class is already 4-0 under *all* conditions → there are no flippable games on the routing layer. A retrained tree can at best reproduce verbatim's choices.

**2. Herd-scale tape authorship — killed at diagnosis, before surgery:**
- Router herd at d12 (seed 201): **9 COW / 5 SHEEP / 3 GOOSE = 17 animals.** Ant at same step: 7C/6S/3G = 16. The census "5C/4S/4G" was per-tape buys; the router *accumulates across switches* — **the router already runs an Ant-class herd.** There is no herd-scale gap to close.
- Empty tiles at d12: 4 → 0 by d14 (the tape claims them for wheat). Wheat ≈ $55/day/tile vs goose ≈ $15/day/tile → extra geese cannibalize higher-value wheat. Tapes are tile-optimal.
- **No gate can target Ant-class without hitting twins:** the router's herd IS the same class (9C/5S/3G vs Ant 8C/6S/3G). Any rival-herd branch fires on twins too → breaks the 17-tie symmetry (8.5 BT pts) for a ~1% egg play.
- Revenue attribution (router vs ant_tape): MELON/FERT/WHEAT/MILK 6-11k each, STRB/EGG small, WOOL ≈ 0 — no product gap to exploit. Router beats the Ant tape by **+$21k to +51k (avg +$38k, 5 seeds)**.
- Conclusion: the live losses to Ant/bharat are **context/seed** (their crash windows landing on our sell windows), not a class weakness an agent edit can fix.

## Verdict
The router is at a **measured local optimum** against the current meta: market layer (v24/v25), foreign tapes (v26), tree retraining, and herd scaling are all falsified with controls. Everything left either breaks twin ties (net negative BT) or targets a gap that doesn't exist. **Router stays verbatim. No submissions.**

Live: router 2540.8 (all-time best), v16 1909.1.

## Files
- `analysis/TREE_RETRAIN_RESULTS.json` — full lock table + diagnostics + verdicts
- `analysis/tree_lock_harness.py` — reusable harness (forced-leaf trees, tape opponents)
