# v29 Planner — commitment/ledger economy planner (2026-08-15)

## What was built
`scripts/ledger_planner.py` — the Shabby-Farm-class planner core, grounded in
our own machinery:

1. **Engine model** (verified against kaggriculture.py): one-time crops yield
   via the WATER window (wheat +1/day watered on days 2-4 post-plant = 3
   units/tile; melon days 6-12, cap 6); one-time crops occupy their tile
   until HARVEST; ongoing crops (strawberry) produce via daily refresh;
   land NE/SW/SE = $1k/$2k/$4k; shed cap 100; reward = money only.
2. **Labor-gap model**: from the recorded v25 game, per (day, worker)
   anchor schedules → inter-anchor GAP lists. A new commitment needs a gap
   with d_in + ops + d_out ≤ free hours (the exact Phase-A contract of
   plan_day) — the check the se_flood experiment lacked.
3. **Ledger scaffold**: cash/seed/shed/tile replay with drop-and-rerun
   portfolio selection (the `Ledger` class) — to be wired to the search.

## Calibration results (the record IS the ground truth)
- Record: 63 wheat plants, 3,286 anchors, reward 145,359 (seed 1 seat 0).
- **Per-day labor report (corrected model)**: free steps/day across the
  whole crew, d12-29: only **~100-130 total** (d12 123, d16 133, d20 127,
  d26 107, d28 117) — and they're shattered into 1-4 hour shards between
  anchors. `data/ledger/labor_report.json`.

## Verdict 1 — the SE wheat machine (4th quad)
- **0 of 24 PLANT windows, 1 of 96 WATER windows** exist on d12-15 — the
  tape is packed every hour, on every day, even before the flood.
- Value math, even if plantable: 24 tiles × 3 wheat ≈ $3,900 gross − $4,000
  land − $240 seeds ≈ **−$280** one-shot; continuous replanting ≈ +$3.4k
  best case minus double water labor. Marginal at best.
- **Conclusion: SE pays only if the economy GIVES UP mid-game commitments
  to fund it — i.e., a portfolio search, not an addition.** That is exactly
  what the Ledger is for.

## Verdict 2 — where the +$30k really lives (wheat-stock trace, seed 1)
`data/ledger/wheat_stock.json` — per-day shed wheat, buys, sells, prices:
- **Wheat price is 35-40 ALL GAME** (flat sqrt regime) — the #1's edge is
  VOLUME, not price timing: 668 more units × ~$38 ≈ **$25k**.
- Our shed is **80-96/100 for 6 straight days (d20-26)** — we physically
  cannot hold more wheat for the flood. The #1 cycles the shed: sell big
  d19-23, buy trough d24-26, sell peak d27-29.
- Our cycle room: ~20-40 units × $3-5 margin ≈ **+$60-160/game** — real
  but small; the v28 lesson says blind buy/sell edits lose money, so the
  feed-safe ledger replay must verify any cycle before we test it.

## Verdict 3 — the binding constraint chain
tiles (99% full d12-27) → labor (shattered 1-4h gaps every day) → shed
(80-96/100 through the flood) → thin margins. **Any single-axis edit is
dead; only a coherent economy redesign (portfolio) moves the needle.**

## Next build (the actual planner search)
1. Wire the Ledger replay: cash + seeds + shed + feeds (feed wheat =
   day-start stock + buys − sells − day-end stock, from the record).
2. Portfolio search: candidate commitment sets = drop N low-value
   mid-game commitments (late strawberry cares, low-yield melon replants,
   duplicate waters) → fund SE program + shed-cycle; filter by labor gaps
   + feed safety + cash; keep survivors.
3. Compile survivors via se_flood/splice machinery; run the standard
   gates (PASS + keepgate + contested + replay spots).
4. Only a variant that beats the gates ships. v25 remains the post until
   one does.
