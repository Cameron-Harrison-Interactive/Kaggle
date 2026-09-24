# Adaptive v20 — session report (2026-08-14)

## SHIP: YES — HI_AgriBot_v20_Adaptive

**The adaptive version is found and working.** It is the v19 compiled routes
(62 crops, full water coverage) with ONE change: **the seat1 Gbining tape is
replaced by the v19 seat0 tape** (single-tape-both-seats — the structure the
whole top meta uses: tetsu, kaito, rayk all do exactly this).

## Final numbers (finals battery, 9 opponents × 3 seeds × both seats)

| vs | v19ctrl | **v20 (s0s1)** | seat1 detail (ctrl → v20) |
|---|---|---|---|
| v14.5 | 4-2, +1,388 | 4-2, **+1,565** | s1: -971 → **-616** |
| v15 | 4-2, +1,388 | 4-2, **+1,565** | s1: -971 → **-616** |
| v18 | 2-4, -404 | 1-5, **-220** | s1: -1,070 → **-703** |
| kaito (THUNDER#1) | 6-0, +13,432 | 6-0, **+14,330** | s1: +12,938 → **+14,735** |
| rayk | 6-0, +10,546 | 6-0, **+13,836** | s1: +9,102 → **+15,682** |
| tetsu | 1-5, -807 | 0-6, **-616** | s1: -1,065 → **-683** |
| seb | 6-0, +130,977 | 6-0, **+133,518** | s1: +123,294 → **+128,377** |
| healthstone | 6-0, +54,001 | 6-0, **+50,298** | s1: +59,863 → +52,457 (only regression) |
| cowbot | 6-0, +150,188 | 6-0, **+153,752** | s1: +146,529 → **+153,655** |
| **sum** | **+360,709** | **+368,028** | **+7,319** |

PASS economy: seat0 $170,031 (unchanged), seat1 **$155,325 → $162,093**.
Animals: 13/13 (no new escapes). Per-turn cost: 0.27ms avg / 3.0ms max
(limit 1000ms). Seed-1 mirror tax vs tetsu/v18 seat1: -5,475 → -1,457.

## What the search rejected (keep-gate = the science)

- **race-market preemption (rayk port)**: safe but inert on our tape — our
  tape sells at harvest time, the shed is empty at trigger (same finding as
  v18.8 CrashDump / v18.6 ClonePreempt). Kept in the codebase, off by default.
- **tetsu tomato overlay (th)**: -$12,392 vs v19. Dead on v19 too.
- **seat1 opening splice (drop the 5th hire)**: inert (+$5 PASS).
- **s1sp_w (trim 20 wheat-product buys)**: seat1 PASS $144,109. Dead —
  the feed chain is load-bearing.
- **melon4 (+4 melons, rayk-style)**: the naive compile swaps opening
  strawberries and collapses the economy (seed-buy cash timing is knife-edge
  at d0-d3). The compiler now supports `crop_swap_min_day` + seed windows +
  sell bumps — hand it to your local compiler run (it needs the multi-hour
  search your 3700X does).
- **three-fer (v18 base, 36 variants)**: all rejected — v18 is locally maxed.

## The meta map (from the tape analysis)

tetsu plays **our seat0 tape on both seats** (seat0/seat1 PASS scores match
ours exactly). kaito = single melon-heavy tape. rayk = single tape + 4 more
melons + the market race layers. The whole top meta is one tape family;
the differentiators are the seat1 tape and the market layers.

## Files

- `agent/main_v20_adaptive.py` — the shippable agent (VERSION
  HI_AgriBot_v20_Adaptive)
- `agent/main.py` — updated to v20 (v18 backed up as
  `agent/main_v18_live_backup.py`)
- `submit/HI_AgriBot_v20_Adaptive.tar.gz` — packaged, main.py at root,
  smoke-tested ($136,485 vs starter)
- `scripts/adaptive_v20.py` — the search/battery (self-test, gate, finals,
  build-agent)
- `scripts/adaptive_v20.ps1` + `scripts/run_adaptive_v20.bat` — Windows
  runners (the .bat avoids the PowerShell execution-policy block that
  stopped the three-fer last session)
- `data/adaptive_v20/ledger.jsonl` + `report.json` — full records

## Next steps (ordered)

1. Submit v20; watch it live vs the field (the user posts to Kaggle).
2. Run the melon4 compile locally: `--with-melon4` (needs `crop_swap_min_day`
   tuning for the seed buys — see the README above).
3. If the live mirror losses persist, the only remaining lever is a
   distinctive-path recompile (same economy, different walk) — three_fer's
   path styles exist but never beat the keep-gate on their own.
