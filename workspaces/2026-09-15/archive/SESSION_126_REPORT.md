# SESSION 126 — 2026-09-08 ~17:00 UTC
## Fight run: Edits 0-20 vs Champion. Labor rework: isolated every lever. Architecture ceiling found.

**User order: keep working, do not post. Fight Edits vs Our Champion.** No submissions made.

## THE FIGHT (as ordered)

- v28.18c ("Edits") vs tt_router_938 ("Champion"), 20 seeds, seat-swapped: **0-20. Edits $28.1k mean vs Champion $144.5k.**
- After the labor rework (v28.21): 10 seeds: still **0-10, $32.8k vs $139.5k.**
- Asymmetry: Champion loses 26% of solo money in H2H; we lose 61%. Its tape labor runs 58 tiles; our planner saturates at ~45.

## LABOR REWORK — every lever isolated (3-seed A/B, exact-text variants)

| variant | mean | verdict |
|---|---|---|
| v1 = v28.18c baseline | $75.1k | reproduces |
| + pickup 18 (engine has NO cap) | $52.7k | **POISON: one worker hoards all wheat, feeding serializes, herd starves** |
| + hands DROP at >=12 | $79.4k | **WIN +$4k** |
| + hands 15 (fib $1,973/day) | $72.8k | neutral-negative |
| + tile-sticky locks (animal tiles, hands only) | $58.8k | **LOSES: overrides feed-sacred globally** |
| + dist-0 score bonus (+3 at current tile) | $79.4k | keep (better tail: 87.3k) |
| + fertilize-all-crops | $79.4k | zero effect — labor never reaches wheat tiles |
| + strb 20 / wheat 20 / geese 6 | $67-73k | all NEGATIVE — planner ceiling ~45 tiles confirmed |
| + present-price gates (wool/strb) | no change | gates read the present; crash comes AFTER commitments are sunk |
| + predictive flood gates (I_wool/I_strb trend) | +$1.5k H2H | noise-level |

**v28.21 (current build): solo $66.2/84.7/87.3/84.4/73.6k = $79.2k mean (5 seeds). H2H vs champion: 0-10, $33k.**

## ARCHITECTURE CONCLUSION (the honest one)

The reactive planner has hit its ceiling: 55% walking (60-67% late-game), 82-95% utilization at 45 tiles, and every scale-up is net-negative. The champion's advantage is not its economy logic — it's RECORDED, OFFLINE-OPTIMIZED LABOR (tapes: near-zero wasted steps at 58 tiles).

**The 2900-class path: our own tapes.** Record v28.21's play, then offline-optimize the action sequences (tree_lock_harness methodology — but on OUR economy, not the public TT kernel), with feature-based routing for opponent adaptation (record vs PASS/router/self, route like the champion does every 144 steps). That is where the 3x labor efficiency lives. This is the next major build; not a same-day patch.

## NEXT SESSION PLAN
1. Tape recorder: run v28.21 vs {PASS, router, self} on N seeds; store per-step farmer/hands/market actions.
2. Playback agent + fidelity check (must reproduce solo money to the cent).
3. Route table: features -> tape, like the champion (its _features = money/prices/inventories/both farms).
4. Offline optimization pass on the tapes (walking elimination first).
5. Gates: solo >= $140k, H2H >= 60% vs champion BEFORE any submission talk. No posts without explicit user go.

## FILES
- topbots/v28_harvest_moon.py = v28.21 (solo $79.2k mean; H2H 0-10 vs champion)
- topbots/tt_router_938.py = champion (unchanged, live as 2483 + resubmit 56100058 climbing)
- /tmp VOLATILE: h2h.py (any-vs-any, seat-swapped), solo_any.py (abs paths ok), diag_any.py, v1..v11 variant files
