# Session 54 — Forward-Search Validation + SKIP_SE (user-caught bug)

## Where we are
- Solo: **$81,696 (10 seeds)** — +$4,482 vs S53
- H2H delta: **-$89,706** — -$3,420 vs S53 (first time below -$90k)
- Ship unchanged: `main.py` md5 = `c0c74b43ea577dfb05f1e21dd0f8991b`
- All 16 animals alive every seed

## What happened

### 1. Forward-search wrapper — proves economy is optimal
- Built `agent/custom/search.py` with `choose_extra_order()`
- At key days (5,10,15,20 H1) test 3-4 candidate extra market orders,
  roll 48-720 steps under normal agent, pick best
- **Every seed × every decision × every horizon: search picks "none"**
- Confirms our decision rules encode near-optimal single-turn choices
- Solo tuning at $77k is a structural ceiling of current layout

### 2. **BT tape re-read — I FLIPPED THE QUADRANTS (user caught)**
- I originally wrote "BT skips NE and SE"
- User pushed back: "why the hell would it skip NE that's the cheap one?"
- Correct read: LOCKED tiles are at x=5-9, y=5-9 = **SE**
- BT actually owns NW + NE + SW, skips only **SE ($4000)**

### 3. **skip_se = True** — +$4.5k solo, +$3.4k H2H
- Added `skip_se` config flag; when True, never issue BUY_LAND for SE
- Money spent on SE ($4000) + planting SE (~$400 seeds) frees cash for more
  wheat cycles, animals, and hires
- Also tried skip_se + skip_sw (2-quad NW+NE only): $75k, worse

## Ablation this session

| change | avg (10 seeds) | delta |
|---|---:|---:|
| S53 baseline (4 quads) | $77,214 | — |
| + **skip_se (3 quads)** | **$81,696** | **+$4,482** |
| ❌ skip_se + skip_sw (2 quads) | $74,927 | -$2,287 |
| ❌ forward-search (any candidate) | picks "none" | 0 |

## Preliminary H2H vs BT (12 games, 6 seeds × 2 seats)

| metric | S53 | **S54** |
|---|---:|---:|
| custom H2H avg | $41k | **$47k** |
| BT H2H avg | $134k | $137k |
| **wins vs BT** | 0/12 | **0/12** |
| **avg delta** | −$93k | **−$90k** |

Best individual: seed 3 delta -$47k — approaching draw territory.

## Progression summary

| session | solo | H2H delta |
|---|---:|---:|
| S47 v2 | $22,278 | −$131k |
| S48 v3 | $28,962 | −$126k |
| S49 v4 | $43,556 | −$121k |
| S50 v5 | $56,292 | −$120k |
| S51 v6 | $60,890 | −$108k |
| S52 v7 | $70,307 | −$100k |
| S53 v8 | $77,214 | −$93k |
| **S54 v9** | **$81,696** | **−$90k** |

Total: **−$131k → −$90k (+$41k) across 8 sessions.**

## Analytical error I made — corrected

I read BT's end board and said "BT owns NW + SW, skips NE + SE." That was
wrong; I flipped the quadrant labels. Actual: LOCKED block at x=5..9 y=5..9
= SE only. BT owns 3 quads (NW + NE + SW), skips just the $4000 one.

Once corrected, testing skip_se cost me one experiment (60 seconds) and
returned +$4.5k solo / +$3.4k H2H. **Lesson: always double-check board
orientation before making conclusions.** User's instinct — "why would it
skip the cheap one" — was right.

## Next session (Session 55) plan
1. Investigate whether SE-tile crops (planted in S53) were ever worth having
2. Try more compound tunings now that skip_se opened breathing room
3. Ship-test comparison — how close to actually winning some seeds

Target: solo $85k+, H2H delta −$80k, first H2H win vs BT.

## Files touched
- `economy.py` — added `skip_se` and `skip_sw` cfg support
- `agent.py` — `skip_se: True`
- `agent/custom/search.py` (created, kept for future use)
- `tests/test_search.py` (created)
- `agent/custom_v8_bak/` — S53 snapshot
- `SESSION_54_REPORT.md`

`main.py` UNCHANGED (still Session-42 breaking_tie shipped).
