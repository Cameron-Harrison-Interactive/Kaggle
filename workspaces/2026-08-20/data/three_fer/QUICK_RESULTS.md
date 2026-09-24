# Three-fer QUICK — results (v20 base, run in sandbox 2026-08-14)

4 candidates × (2 PASS + 6 v18-gate + 6 v20-gate + 6 tetsu games) = 80 games.
Elapsed 4.9 min on 2 cores (≈2-3 min on your 3700X with 8 procs).

## The table

| variant | PASS seat0/seat1 | animals | v18 gate | v20 gate | tetsu | verdict |
|---|---|---|---|---|---|---|
| **BASE** (v20 verbatim) | $167,978 / $162,093 | 13/13 | +1,156 (2/6) | +482 (2/6) | +503 (4/6) | control |
| **px** (x-first walk, days 0-27) | $167,978 / $162,093 | 13/13 | +1,156 (2/6) | +482 (2/6) | +503 (4/6) | **identical to BASE** |
| **esp** (straw preempt d17/23) | $165,264 / $159,728 | 13/13 | +1,333 (4/6) | +729 (4/6) | +750 (4/6) | **rejected** |
| **px+esp** | $165,264 / $159,728 | 13/13 | +1,333 (4/6) | +729 (4/6) | +750 (4/6) | **rejected** |

## What it means

1. **px is a FREE cosmetic change.** The x-first staircase rewrite produces
   byte-different replays with *identical* outcomes (PASS, every gate, tetsu —
   all exactly BASE). If you want the bot to "not look like a clone" in
   replays, px costs nothing. But it also earns nothing — so by the strict
   ship gate it stays "no" (gate requires an improvement, not a tie).

2. **esp loses the trade.** The d17/23 straw preemption sells before the peak
   and costs −$2,714 seat0 / −$2,365 seat1 on PASS. It gains +247 avg vs tetsu
   and +228 vs v18 in mirrors — inside the lockstep coin-flip noise band.
   Bad trade. Rejected by the gate exactly as designed.

3. **The walker variants (w1/w2/w1d27) are in the FULL catalog only** — the
   diagnose shows 7 plants / 14 units still unharvested at turn 720 (row 8-9
   wheat planted d26, yield 2 each). Those are the walker's targets. Run the
   full 48 on your machine if you want the walker verdicts too:
   `scripts\run_three_fer.bat`

4. Gate math sanity: mirror duels are coin flips (seat-tax locks in 2-4
   losses per 6 regardless of bot), so "0 losses vs v18/v20" can only pass
   for a variant with a REAL contested edge. None of the four has one.

## Bottom line

**SHIP=NO. v20 stays live.** The only actionable nugget: if you want the
anti-clone look, px is safe to apply cosmetically (it passed PASS + animals
and ties BASE everywhere) — but it changes no coins. The full run on your
machine is still worth doing for the walker (w1/w2/w1d27) and (7,4)-feeder
(e74) verdicts, which need more games than this sandbox can chew.
