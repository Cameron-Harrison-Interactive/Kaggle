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

## TURBO MODE — thousands of variants/hour (NEW)

`scripts/supersearch_turbo.py` is the brute-force engine built for your PC.

**Speed tricks:**
1. **Full cartesian grid** — crop x hires x animals x sell x water x fill x
   early = ~thousands of combos, all brute-forced (the security-code search).
2. **Cache** — every compiled variant saved by hash to
   `data/supersearch/cache/`; re-runs are instant.
3. **Post-only fast path** — sell shifts/splits and carrot swaps never touch
   labor, so they're applied to the cached base tape in milliseconds (no
   recompile).
4. **Fast gate** — every variant first fights just v18 + v14.5 on 1 seed
   (~15s); only the top-K finalists get the full winner suite. THIS is what
   makes thousands/hour possible.
5. **Multiprocessing** — one worker per core (`--procs`, default all cores);
   each worker loads the engine once.

```powershell
cd Z:\Kaggle\Works\kaggriculture

# big overnight run (all dims, all opponents):
python scripts\supersearch_turbo.py --seeds 1,2,3 --opps all --finalists 20 --build-agent

# focus a dimension (e.g. hunt the missing-row fix):
python scripts\supersearch_turbo.py --dims fill,early,water --seeds 1,2,3 --opps all --finalists 15 --build-agent

# or the wrapper:
.\scripts\turbo.ps1 -Seeds "1,2,3" -Opps all -Finalists 20 -BuildAgent
```

Outputs: `data/supersearch/ledger_turbo.jsonl` (every variant: gate score +
economy + missed-water audit), `champion_report_turbo.json`,
`champion_seat{0,1}.json`, and `agent/main_v19.py` with `--build-agent`.

**Throughput — REAL numbers (measured):**
The gate phase is dominated by MATCHES (each variant fights 4 gate matches,
~7s each), so throughput ≈ (cores) x (3600 / 28s) ≈ 650-700 variants/hr per
~5-8 busy cores. Your 667/hr reading is normal for the gate phase.
- Grid is now **10,800 variants** (crop4 x hires3 x animals5 x water5 x
  fill3 x early3 x feed4), so at ~667/hr that's ~16h first run; at
  10-16 cores it scales ~linearly (use `--dims` to focus).
- The rate is printed live every 25 variants with ETA.
- FULL suite battles (finalists) are the slow tail: 20 finalists x 7 opps x
  3 seeds x 2 seats ≈ 840 matches ≈ +1-2h.

**Why the SELL dimension was REMOVED (important lesson):**
BOTH sell_shift and sell_split break the shed-capacity choreography — goods
sit in the 100-cap shed, later harvests are discarded, economy collapses
(verified: sell-6 -> $5.5k, sell+6 -> $47, sell+12 -> $1.5k, split -> $0
vs $168k base). The tape's sell timing is already optimal + terminal sweep.
The search fights over the levers that work: **crops, hires, animals,
water/routing, fill, early, feed**.

### NEW: feed dimension (the escaped-cow bug)
Every match (both seats, all seeds) loses the SAME cow at (7,4): the tape
stops feeding it after day 19 AND its feeder runs out of wheat on days
13/16/17 (all workers pick up wheat in the same 2-3 morning steps and drain
the shared shed, so the last feeder gets shorted). Measured vs PASS (seed1):
- fr0 off:          $167,978, cow escapes day 18  (the bug)
- fr1 full repair:  $156,179, cow day 22 + new day-28 escape (worst)
- fr2 rebalance:    $166,863, cow survives to day 22 (-$1.1k shed friction)
- fr3 extension:    $156,227 (extension steals water walks -> weeds, worst)
The search now fights all 4 modes vs every winner on multiple seeds to find
which (if any) nets a win CONTESTED — vs-PASS deltas don't tell the whole
story because the shed friction hits differently in mirror matches.

IMPORTANT: if you re-run after this update, delete the old cache first:
  Remove-Item -Recurse -Force data\supersearch\cache, data\supersearch\cache_records

## The "missing row" (found + being searched)

Your leaderboard observation is real. Replaying v18, the NE quadrant rows
y3/y4 (x7-8) sit EMPTY until day 12 (workers walk past from day 8) and there
is a permanent corner weed at y3x9 that is never dug. Two NEW search
dimensions target it:
- **early** (`--dims early`): moves very-late PLANT anchors to the first time
  a worker stands on the tile (fixes "planted d20-28 though walked since d10").
- **fill** (`--dims fill`): plants wheat on never-planted tiles workers visit
  repeatedly.
In the sandbox test, `early_plant=8` won the gate vs v18 (+654 avg, 0 missed
water) — the search now hunts the exact count/combination.
