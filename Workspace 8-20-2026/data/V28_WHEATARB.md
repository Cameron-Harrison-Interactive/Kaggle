# v28 WheatArb — build & test log (2026-08-14)

## Design
HI_AgriBot_v28_WheatArb (agent/main_v28_wheatarb.py) = v25 Wheat16 + a
market-only wheat-arbitrage scale-up toward the #1 player's profile:
- d8-15: BUY_PRODUCT WHEAT quantities x MULT (dip buys; shed has ~50-80
  headroom there per live traces)
- d13/16/17/18 h0: SELL WHEAT bumped proportionally to drain the extra
  stock at the mid-flood prices (feed-safe by construction: shed ends with
  MORE wheat at d13 than the base tape)
- everything else byte-identical; MULT swept in {1.0, 1.25, 1.5, 1.75, 2.0}

## Why this shape
Profile diff vs the #1 route (decoded public episode): same hires (266 vs
277), same cows (9 vs 10), we buy MORE wheat seeds (147 vs 135) — the gap
is pure arbitrage volume: they buy 522 wheat (vs 245) at the d8-11 and
d22-26 troughs and sell 1,138 (vs 470) at the d19-29 peaks. The d22-26 leg
needs shed room we don't have (shed 80-96/100 through the flood — the
melon4 lesson), so v28 scales only the d8-15 leg.

## Test battery (test_v28.py, 41 jobs + mirror — all done)

**A. PASS sweep (seeds 1-3, both seats, vs idle):**
  mult 1.0  : mean  +0     esc 0   (control sanity ✓)
  mult 1.25 : mean −6,044  esc 3   REJECT (feed timing breaks)
  mult 1.5  : mean −475    esc 0   (neutral)
  mult 1.75 : mean −1,783  esc 0
  mult 2.0  : mean −2,224  esc 0

**B. Contested (seeds 1-2 vs v20 + kaito, both seats, mult 1.5):**
  ALL 8 games NEGATIVE: −1,039 / −1,037 / −4,185 / −4,468 / −6,957 /
  −7,208 / −8,627 / −9,195, several escapes.
  → our extra dip-buys raise the wheat price the opponent's mid-game sells
  collect, and our extra mid-flood sells depress our own prices: the
  scale-up subsidizes the opponent's arbitrage.

**C. Recorded-replay spots:** mixed (v28 88,022 vs v25 104,326 on the
  Debmalya replay → −16k; +12k on 93061726). NOTE: the C baseline column in
  the log is invalid (opponent-call-counter reuse bug in job_c) — use the
  regression_v26 suite numbers for v25 baselines instead.

**D. Self-mirror (seed 1, mult 1.5): 106,275 vs 106,275 → 0.**

## Verdict: REJECTED
The v25 tape's arbitrage is already at the local optimum of its economy
class. Every scale-up loses (worst when contested). The +$30k/game gap to
the #1 economy lives in the FULL economy design — wheat-field size, shed
cycling through the flood, feed allocation — which requires the compiler to
generate economy variants with new choreography (the v28-full project),
not market-order edits. v25 Wheat16 remains the post.
