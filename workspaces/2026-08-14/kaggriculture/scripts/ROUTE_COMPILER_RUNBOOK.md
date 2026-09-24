# Route Compiler v19 — Local Runbook

Run this on YOUR PC (it needs `pip install -U kaggle-environments` and the
`kaggriculture/` folder from the workspace/GitHub).

The compiler rebuilds the 719-step seat tapes with **100% water coverage**:
- Market orders, hires, seed buys, sells, PLANT tiles, HARVEST/FEED/CARE/
  PICKUP/PLACE/BUILD steps are kept **verbatim** from the v18 tape (the
  proven economy is untouched).
- Every plant is watered on its planting day and then daily (or every-other-
  day with `--water-eod`), using the workers' spare steps as round-trip water
  excursions from their hold positions.
- Result (verified in sandbox): identical money vs PASS ($167,978 / $155,325)
  but **62 max crops** (was ~52) and **1 weed at d15** (was 8-9), on seeds 1-5.

## Quick start

```bash
cd kaggriculture
pip install -U kaggle-environments

# 1) Compile both seats + validate vs PASS (about 1 min):
python3 scripts/route_compiler_v19.py --seats 0,1 --validate

# 2) Auto-fixer loop — recompile N times with parameter jitter, keep the
#    champion by keep-gate score vs v18 (this is the "1000 games" search):
python3 scripts/route_compiler_v19.py --seats 0,1 --iterations 20 \
    --seeds 1,2,3,4,5 --keepgate --validate

# 3) Battle a saved tape without recompiling:
python3 scripts/route_compiler_v19.py --tape data/tapes_v19/champion_seat0.json \
    --keepgate --seeds 1,2,3,4,5

# 4) Build agent/main_v19.py from the champion tapes:
python3 scripts/route_compiler_v19.py --build-agent
```

## Options

| Flag | Meaning |
|------|---------|
| `--seats 0,1` | which seats to compile |
| `--seed N` | reference seed used to record the base tape (labor is seed-invariant; 1 is fine) |
| `--seeds a,b,c` | seeds used for keep-gate battles vs v18 |
| `--iterations N` | auto-fixer loop count; jitters water policy (daily / every-other-day) and RNG, keeps the best tape per seat as `champion_seat{0,1}.json` |
| `--keepgate` | after compiling, battle each seat tape vs v18 on the given seeds (both seats) |
| `--validate` | run the compiled tape vs PASS and report reward / max_crops / weeds_d15 / weed-days |
| `--water-eod` | every-other-day watering instead of daily (fewer waters, less yield bonus) |
| `--build-agent` | inject champion tapes into a copy of submit/main.py -> `agent/main_v19.py` |
| `--tape PATH` | skip compiling; test/keep-gate a saved tape |

## Outputs

```
data/tapes_v19/route_v19_seat{0,1}.json        compiled 719-step tapes
data/tapes_v19/route_v19_seat{0,1}_report.json per-run metrics (water done/missed per day)
data/tapes_v19/champion_seat{0,1}.json         best tape found by the auto-fixer
agent/main_v19.py                              ready-to-package agent (VERSION set)
```

## How the recompiler works (architecture)

1. **Record reference** — run v18 vs PASS on the reference seed; capture the
   719-step tape + full observation history.
2. **Extract** — plant database (tile, crop, planted day), labor anchors
   (PLANT/HARVEST/FEED/CARE/COLLECT/PICKUP/PLACE/BUILD/FERTILIZE/WATER with
   their exact steps + tiles), day-start spawns and mid-day hire spawns.
3. **Water schedule** — every plant must be watered on its planting day
   (CU starts at 1 -> weeds that night otherwise) and then daily
   (`--water-eod` for every-other-day).
4. **Day planner** — Phase A reserves, for every anchor, its walking steps
   AND hold steps (PASS in place) so workers never drift off the reference
   trajectory (drifting was the failure mode of every runtime water overlay).
   Phase B fills genuinely free steps with **round-trip water excursions**:
   leave the hold position, water a nearby plant, return before the next
   anchor walk (never breaking PICKUP->FEED inventory chains).
5. **Validate** — replay vs PASS: reward must equal the reference (economy
   intact) and weeds must drop to ~0-1/day.
6. **Keep-gate** — battle each seat's compiled tape vs v18 on both seats;
   only a positive average delta is kept as champion.

## Known limits (read before you promise anything)

- The compiled tape keeps the v18 **economy** exactly: same buys/sells/hires.
  More crops = more harvested units, but SELL quantities are fixed by the
  tape, so surplus sits in the shed (terminal sweep sells it at step 718).
- Seat 1's economy is inherently weaker than seat 0's (~$155k vs $168k vs
  PASS) — the compiler preserves that; it cannot fix the seat-1 opening.
- Contested matches (vs v18) are volatile on seat 1; the auto-fixer's
  keep-gate picks the best variant across seeds.
- If keep-gate still fails after iterations, the next lever is relaxing
  PLANT/HARVEST anchors (with seed-buy adjustments) — out of scope for this
  version of the script.
