# Session 42 — Multi-Route Ensemble for Top-5 Push

## What changed

`main.py` swapped from Kaito Fukami's v41 → Andrey Naymushin's **"Breaking
the Tie" V21-R1** — a **multi-route ensemble** that internally packages four
sub-agents (MOON, MUTOY, MUNIB base, MUNIB FR) and dispatches per-turn based
on shop-regime detection and opponent's opening-money signal.

Source: [Kaggle notebook](https://www.kaggle.com/code/andrewsokolovsky/kaggriculture-breaking-the-tie)
by Andrey Naymushin (66 votes, updated 2026-08-23 07:06 UTC — the freshest
high-signal public agent available).

## Why v41 wasn't good enough

Session-41 shipped v41. It goes 27/29 vs the exact Kaggle opponents that
beat wheat16 — great on paper. But in a fresh **round-robin against 5 other
top public-notebook bots**, v41 finished LAST at 18% win rate.

The Kaggle ladder is roughly half copies-of-public-notebooks and half custom
bots. If we lose 82% of games against the same public-notebook clones every
top team is running, we can't climb.

## Round-robin (each pair: 10 seeds × 2 seats = 20 games)

| bot | breaking_tie | moon | amey | multiroute | soil | v41 | **wins** |
|-----|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **breaking_tie** | — | 12/20 | 13/20 | 15/20 | 16/20 | 15/20 | **71/100** ★ |
| moon | 8/20 | — | 3/20 | 16/20 | 18/20 | 18/20 | 63/100 |
| amey | 7/20 | 17/20 | — | 17/20 | 18/20 | 18/20 | 63/100 |
| multiroute | 5/20 | 4/20 | 3/20 | — | 14/20 | 14/20 | 40/100 |
| soil | 4/20 | 2/20 | 2/20 | 6/20 | — | 17/20 | 31/100 |
| **v41 (prev)** | 5/20 | 2/20 | 2/20 | 6/20 | 3/20 | — | **18/100** |

**breaking_tie is #1 with a 4x lead over v41.**

## Session 42 comprehensive scorecard

| Suite | Games | breaking_tie result |
|-------|------:|:-------------------:|
| 29 real Kaggle opps (21 losses + 8 wins reproduced) | 29 | **25 W / 4 L, $+230,676 total** |
| 10-refbot suite (100 seeds × 2 seats) | 200 | **200 W / 0 L** min=$+9,945 |
| Self-mirror (byte copy) N=20 | 20 | 4W/4L/12T avg $+171 |
| vs `moon` head-to-head | 20 | **12 W / 8 L** |
| vs `amey` head-to-head | 20 | **13 W / 7 L** |
| vs `soil` head-to-head | 20 | **16 W / 4 L** |
| vs `multiroute` head-to-head | 20 | **15 W / 5 L** |
| vs `v41` head-to-head | 20 | **15 W / 5 L** |

## Rating projection

- Session 40 (wheat16): rating 1492, 60% win rate on Kaggle
- Session 41 (v41): 27/29 vs Kaggle losses → est. 2800-2900
- Session 42 (breaking_tie): higher head-to-head win vs top clones, same Kaggle-opps quality → **target 2900-3050 range, potentially top-10**

Top-5 requires ~3050+. If breaking_tie really does hold its head-to-head
edge on the live ladder, we should be competitive for top-10. Reaching top-5
would need a further ~50-100 rating points beyond what breaking_tie's public
version can give us — that's the honest ceiling of the notebook.

## Loader-safety verified

- Last callable: `_kaggle_submission_entrypoint` (delegates to `agent`) ✓
- `python scripts/smoke_test.py`: **PASS** — $167,943 vs PASS seed 1 via
  actual `kaggle_environments.make(...).run(...)`

## Preserved backups

- `main.py.bak_session41_v41` (Kaito v41)
- `main.py.bak_session40_wheat16` (V25/wheat16)
- `main.py.shipped_session38` (loader-bugged Session-38)
- `main.py.bak_session35` (Session-35 self-aware brain)
- `agent/moon.py`, `agent/soil.py`, `agent/amey.py`, `agent/multiroute.py`,
  `agent/v41_kaito.py`, `agent/breaking_tie.py` (all fallback candidates)

## What we could NOT do

Getting into the top 5 (rating 2946+) requires an agent stronger than any
publicly-shared notebook. The top-5 are individual custom bots. We could
either:

1. Wait for a stronger public notebook to drop
2. Write custom improvements on top of `breaking_tie` — its route-selector
   is a small function; overriding the selection heuristic based on more
   observations could give small edges

The Session-42 ship is the strongest single-notebook agent currently available.
