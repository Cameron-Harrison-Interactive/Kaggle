# HealthStone (#1, teamId 16672202) — study from top-5 wins

Pulled 2026-08-09 via Kaggle API (`competition_team_submissions` + `competition_list_episodes` + `competition_episode_replay`).

## Submissions
| sub id   | public | note |
|----------|--------|------|
| 55341106 | 3235.5 | peak ladder |
| 55342943 | 3060.2 | secondary |

## Top-5 wins analyzed
| episode  | seat | HS $   | opp $  | opponent |
|----------|------|--------|--------|----------|
| 90927489 | 1    | 154931 | 38009  | pooja sandali |
| 90972620 | 0    | 152270 | 141933 | OceanMix |
| 90909860 | 0    | 151412 | 66058  | Axit |
| 90942713 | 0    | 140853 | 137973 | Auxileon |
| 91456308 | 1    | 140596 | 139954 | Elzandi Irfan Zikra |

## Fingerprint / build
- **Open t1:** HIRE×3, BUY_ANIMAL SHEEP 4 + COW 1, BUY_SEED MELON 5 + WHEAT 5 (sheep-first, not cow-first meta)
- **t2:** BUY_SEED CARROT 1
- **Land:** BUY_LAND day **6** (NE, step ~150) and day **10** (SW, step ~242) — earlier than Build-A d7/d11
- **Animals end:** ~9–10 cow + 4–8 sheep (13–17 total); hires ~285–295
- **Crops:** wheat engine + heavy strawberry (plants ~28–38, sells **222–320**) + melon (sells **78–190**)
- **No tomato** in any of the five wins
- **Net wheat:** buys product wheat heavily (293–397) AND sells 430–480 wheat
- **Fertilizer sold:** 250–317
- Final cash-out day 29 crops→0

## Counter experiments (local, seed1 unless noted)

| variant | vs 14.5 | vs HS tape | HS tape vs us | verdict |
|---------|---------|------------|---------------|---------|
| **v15 base** | **103017–97409 WIN** | **146117–78340 WIN** | 66529–132002 WIN | **KEEP** |
| full tom-melon tape swap (straw→tomato seeds/plants/sells) | 94943–134813 **LOSS** | 94771–74986 WIN | — | **REJECT** (−$50k abs, fails 14.5 gate) |
| hybrid (seed+plant only, sells stay straw) | 48030–139332 LOSS | 47448–76227 LOSS | — | REJECT |
| aggressive HS hedge (rewrite straw buys d3+, max_conv 3–4) | 62506–138140 LOSS | ~72k WIN fragile | HS wins seat0 | REJECT |
| light plant convert p90/p80 | = v15 | = v15 | = v15 | no-op (hedge rarely fires) |
| market dump attack overlay | = v15 | = v15 | = v15 | no-op (already selling) |

### Multi-seed v15 vs HS tape
| seed | v15 seat0 vs HS | HS vs v15 seat1 | margin us |
|------|-----------------|-----------------|-----------|
| 1 | 146117–78340 | 66529–132002 | +68k / +65k |
| 2 | 77329–44328 | 57932–106977 | +33k / +49k |
| 3 | 102149–59809 | 48565–96634 | +42k / +48k |
| 4 | 41175–25082 | 34451–63911 | +16k / +29k |
| 5 | 89422–51385 | 58883–117453 | +38k / +59k |

**v15 wins 10/10 seat matchups** against the extracted HS tape.

## Why tom-melon failed
Tomato peak yield/age ≠ strawberry. Rewriting PLANT/BUY_SEED/SELL on the v15 choreography desyncs harvest/pickup/sell timing; scripted SELL TOMATO qty never matches real shed, and early seed rewrite starves the straw cash engine that funds mid-game. Absolute money drops ~$50k even when the match is still a “win” vs a weak HS tape replay.

## Note on tape fidelity
Live HS hits $140–155k. Local HS tape vs starter ≈ $94k (weed RNG, no live adaptive). Beating the tape is necessary but not sufficient vs live #1 — still the right regression target for anti-HS work.

## Artifacts
- `hs_seat0_tape.json` / `hs_seat1_tape.json` — action tapes
- `hs_seat0.b85` / `hs_seat1.b85` — zlib+b85 compressed
- `scripts/opp_healthstone.py` — embedded-tape opponent for local tests
- `analysis.json` — per-episode economy stats
- `meta.json` — episode ids / seats / rewards

## Decision
**Ship continues on v15 AdaptivePortfolio.** HealthStone counter-tape research retained for regression; no portfolio swap until a candidate **beats v15 vs 14.5 AND improves margins vs HS tape**.

## v16 AdaptiveMemory note
HS open silhouette == our backbone (sheep-first). Classifier labels HS as `mirror`.
No HS-specific sell overlay is live (would false-fire on 14.5). Beating HS live is
already the backbone job; further HS edge needs a counter that passes keep-gate
without relying on early sheep counts alone.
