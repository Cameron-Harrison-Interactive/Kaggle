# SuperSearch Compiler — Local Runbook (Windows PowerShell)

This is the brute-force "guess the security code" search. It reuses the v19
water-coverage compiler and tries EVERY combination of:

| Dimension | Variants tried |
|-----------|----------------|
| **crop**    | base / carrot2 / carrot3 / straw+8 / straw+16 / tomato6 / melon6 |
| **hires**   | x0.8 / x1.0 / x1.2 daily HIRE counts |
| **animals** | 13 / 12 / 11 / 10 animals, or +1 late cow (shed-cash play) |
| **sell**    | shift -6 / 0 / +6 / +12 steps, or split big batches |
| **water/routing** | daily vs every-other-day vs switch@d10/d14 cadence, x water priority: nearest / highest-value crop first (melon>straw>tomato>wheat) / youngest first — the movement schedule is REBUILT per variant (BFS pathing + anchor-first + round-trip excursions), so every variant gets its own watering route |

Every variant is validated with a **missed-turn audit**: the replay counts any
plant that ever reaches `consecutive_unwatered >= 2` (a real "missed a turn"
that would have weeded). The compiled base currently scores **0 missed turns**
across seeds 1-5.

Every variant is compiled for BOTH seats, then **fights every winner we have**
on your chosen seeds x both seats. It only keeps a champion that beats
EVERY opponent (losses == 0) with avg delta >= threshold.

## IMPORTANT — PowerShell gotcha (the error you hit)

`\` line continuations do NOT work in PowerShell. Run everything on ONE line:

```powershell
cd Z:\Kaggle\Works\kaggriculture

# quick sanity (vs v18 only, 1 pass, crops only):
python scripts\supersearch_compiler.py --seeds 1,2 --opps v18 --iterations 1 --validate --dims crop

# real run #1 (vs all OUR winners, 3 passes, validates, builds agent):
python scripts\supersearch_compiler.py --seats 0,1 --seeds 1,2,3 --opps ours --iterations 3 --validate --build-agent

# real run #2 (vs EVERYTHING incl. top-player proxies — long, ~6h):
python scripts\supersearch_compiler.py --seats 0,1 --seeds 1,2 --opps all --iterations 3 --validate --build-agent
```

Or use the wrapper (same thing, no typing):

```powershell
.\scripts\supersearch.ps1 -Seeds "1,2,3" -Opps ours -Iterations 3 -Validate -BuildAgent
```

## Options

| Flag | Meaning |
|------|---------|
| `--seats 0,1` | seats to compile (both) |
| `--seeds a,b,c` | seeds used in the battles vs each opponent |
| `--opps v18` | just v18 (fast sanity) |
| `--opps ours` | v14.5, v15, v18, v18.5, v18.6, v18.7, v18.8 (all our winners) |
| `--opps all` | ours + tetsu, kaito/TT, rayk, opp_seb, opp_healthstone, opp_cowbot, strawflood |
| `--iterations N` | search passes over the grid (1 = one pass; 3+ recommended) |
| `--dims a,b,c` | only search these dimensions (crop,hires,animals,sell) |
| `--threshold N` | min avg $ delta vs EVERY opponent (default 200) |
| `--validate` | also replay each candidate vs PASS (reward/weeds/crops report) |
| `--build-agent` | write the champion into agent/main_v19.py (VERSION=HI_AgriBot_v19_SuperSearch) |

## What you get (all in data/supersearch/)

| File | Contents |
|------|----------|
| `ledger.jsonl` | **every** variant tried: scores vs every opponent + its SELL ledger |
| `champion_seat{0,1}.json` | the champion tapes (best combo found) |
| `champion_report.json` | final report incl. `beats_all_no_sweat` verdict + sell ledger |

## The SELL LEDGER (the "sell days amount" you asked for)

Written for every variant and in the final report. Example (compiled base,
seat0):

```
FERTILIZER   total  245 first_d 2 last_d29 batches 52 avg_batch 4.7
MELON        total  114 first_d10 last_d22 batches 17 avg_batch 6.7
MILK         total  218 first_d 9 last_d29 batches 32 avg_batch 6.8
STRAWBERRY   total  285 first_d14 last_d27 batches 17 avg_batch 16.8
WHEAT        total  459 first_d 5 last_d29 batches 40 avg_batch 11.5
WOOL         total  132 first_d 6 last_d28 batches 13 avg_batch 10.2
```

Upload the ledger + report to GitHub when it finishes and I'll review the
sell days / batch sizes / price timing for the next tuning pass.

## Runtime expectations (local PC)

Per variant ≈ (opps) x (seeds) x 2 seats x ~7s per match + ~10s compile.
- `--opps v18  --seeds 1,2`  : ~45s per variant
- `--opps ours --seeds 1,2,3`: ~3.5 min per variant  (3 passes ≈ 3.5h)
- `--opps all  --seeds 1,2`  : ~6.5 min per variant (3 passes ≈ 6h)

If a pass finds no improvement it stops early. Run it overnight, upload the
results, and I'll do the review + next tuning.

## Known state (as of the sandbox build)

- The compiled BASE route is currently the champion: identical economy to
  v18, 62 max crops (was ~52), ~1 weed at d15 (was 8-9), **0 missed water
  turns** (audited), seat0 beats v18 (+208 avg), seat1 carries the known
  seat-1 opening gap.
- Water variants (cadence/priority) all tie on reward vs v18 because the kept
  reference WATER anchors already cover yield-critical days — excursions add
  margin. The search still tries them every pass in case a combo with other
  dims changes the labor balance.
- Crop swaps (carrot/straw/tomato/melon) were ALL rejected by the search —
  each loses vs v18 (wheat feed is load-bearing; late-crop swaps starve cash).
- `beats_all_no_sweat` is False until a combo fixes seat1's gap — that's the
  search's job to find (extra cow, sell shifts, or hire scaling might do it).
