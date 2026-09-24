# Adaptive Memory — how "self-learning" works under Kaggle rules

## Hard constraint (why the bot cannot literally retrain itself)
After you submit a tarball, Kaggle runs a **frozen** Python file:
- **No disk writes** that persist to the next match
- **No network**
- **No weight updates** that survive episode end
- Process memory dies when the episode ends

So the bot **cannot** "lose to Seb on Monday and remember Tuesday."
What *does* work is the human+offline loop you asked for:

```
pull TopN ×5 replays  →  decode fingerprints  →  bake into agent memory tables
                              ↓
              within each live match, every turn:
              read opp farm + market  →  classify family  →  apply SAFE counter
```

That is **adaptive play**, not online gradient learning. Same end goal on ladder
(fight Seb twice → win both) because the Seb fingerprint was baked in before submit.

## What v16 ships
| Layer | Status | Notes |
|-------|--------|-------|
| v15 route backbone | ON | 719-step seat tapes, water optimizer, tomato hedge, terminal sweep |
| Within-match memory | ON | per-seat `_MEM`: price hist, opp daily snaps, money curves, family scores |
| Family classifier | ON | `seb` (4-quad SE unlock), `buildA` (melon-12 open), `mirror` (3-quad sheep-like = us/HS) |
| Family sell counters | **ARMED but no-op** | prior top-ups cost −$2k–$5k vs v15; re-enable only after keep-gate |
| Tomato hedge | ON | pure v15 (glut-gated); HS seed-rewrite **rejected** |
| Tape swap portfolio | OFF | tom-melon full swap lost vs 14.5 and −$50k abs |

## Keep-gate (non-negotiable before any counter goes live)
1. vs `main_v14_5` seed1: **WIN** and score ≥ v15 − 500
2. vs HS tape seeds 1–3: no regression > 2k mean
3. vs Seb tape: still WIN both seats
4. max turn time < 3s (currently ~0.5ms)

## Why HS ≠ separate family yet
Our backbone **is** sheep-first (4 sheep / 1 cow by day1) — same open silhouette as
HealthStone #1. Early animal counts cannot separate HS from 14.5/self. Distinguishing
HS needs later signals (land d6 vs d7, straw pace, melon waves) or opening-order
side-channels we do not observe (we only see opp farm tiles, not their market orders).

Classifier today:
- **Seb** → SE quadrant + high wheat early + high animals (clear)
- **Build-A** → 8–12 melon open cow-led (clear)
- **mirror** → 3-quad sheep-like (us, HS, 14.5) — treat as default backbone

## Offline research loop (continue 1 team ×5)
1. Pull team last/top 5 episodes via Kaggle API
2. Extract seat tapes → `scripts/opp_<name>.py`
3. Decode fingerprint into `_update_memory` scores
4. Prototype counter in `_market_adapt` or plant overlay
5. Run keep-gate matrix; **keep only if pass**
6. Rebuild tarball `HI_AgriBot_vN_...tar.gz` — you submit

## Proven regression opponents (local)
- `scripts/opp_healthstone.py` — HS top wins tapes
- `scripts/opp_seb.py` — Seb top wins tapes
- `agent/main_v14_5.py` — keep-gate mirror

## Scores (v16 ≡ v15, seed1)
| Matchup | Score |
|---------|-------|
| vs 14.5 | 103017 – 97409 WIN |
| vs HS tape | 146117 – 78340 WIN |
| vs Seb tape | 153505 – 1196 WIN |
| vs starter | 131485 – 3505 WIN |

## 2026-08-09 late — Elzandi #3 + care experiments
- Elzandi peak = Build-A melon-12 (see `data/elzandi/ELZANDI_STUDY.md`).
- PASS→CARE/FEED steal: FAIL keep-gate (−$300–$800, seed5 loss). Disabled.
- PASS→COLLECT_FERTILIZER only: score-neutral (d=0), left enabled as free upside path.
- Ship = v16.1 AdaptiveMemory ≡ v15 money + memory/classifier + fert-idle steal.
