# SESSION 108 — Replay Watch + Tuning Falsifications (no submissions per user)

**Time:** 2026-09-06 ~07:45 UTC · Directive: "Keep working on tuning and winning, watch the
replays, do not submit anything right now."

---

## Live convergence (both actives healthy, winning form)

| Submission | Score trajectory | Recent form (replay-verified) |
|---|---|---|
| v4b-fixed (56047687) | 600→820→1026→1139→1889.9→**1930.9** | 5W-1L (loss −$206 mirror coin-flip vs Selene) |
| 2900-verbatim (56048083) | 600→**1244.2**→**1159.2** (noise) | 4W-1L-1T (loss −$291; TIE exact $67,790 vs Bina Salama) |

## What the replays revealed

1. **The route-twin epidemic:** ropeadope and Bina Salama run the SAME "2900" notebook we
   submitted (identical herd 8C+4S, crops 24W/33S/4M; Bina byte-identical revenue). Route
   twins cap its rating via ties/coin-flips.
2. **Route vs tetsu locally: 0-10, −$14.7k/game** — yet its class rated 3044 live.
   Population-mix ≠ pairwise dominance: Roman Rozen's rating came from beating the rest of
   the pool, not the tetsu crowd head-on.
3. **Live product prices (12 games, d8-27):** wheat flat $40-42 all 24 hours (permanent
   glut — no hourly premium); milk h01 $124.9 vs h08 $114.6 (+9%); wool h01 $114.7 vs h16
   $105.3 (+9%); strb ~$156-165 (spread $7-9); carrot $45-46 flat.
4. v4b sells milk at h7 — the trough. The pool dumps h2-h8; h0-h1 is the freshest window.

## Tuning experiments (all falsified tonight — recorded for the record)

- **goosebot v8 "differentiator"** (v7e + sheep-buy fix + night-band sells h1 + carrot 16
  seeds + adaptive strb-cap 18/opp-strb≥20): solo **$95,859 / $107,201 (+$30k over v7e)**
  — all four patches worked economically — **but H2H 0-4 vs v7e, 0-4 vs v4b, 0-4 vs route.**
  The goose line's labor throughput loses every contested game. **Line closed as a
  competitive chassis (again, now decisively).** Sheep-fix insight: v7e's herd census was
  14C+1S — sheep never scaled because cows grab every pasture slot.
- **v14 night-premium overlay** (v4b + hold MILK/WOOL sells for h0-h1, shed-cap protected):
  **−$50,346/game avg, 8/8 disasters on loss tapes.** The compiled economy is coupled to
  its sell timing (its cash flow, hires, buys are all compiled around that timing).
  Every market-overlay path on the frozen tetsu class is now exhausted.
- **Wheat h1-h2 overlay:** dead on arrival — live wheat is flat $40 around the clock.

## Standing assessment (path to 2950+)

- Neither market overlay nor from-scratch goose nor naive portfolio surgery can beat the
  compiled class. The remaining live levers: (a) convergence data from both actives
  overnight; (b) route-family variants (v27 $120k solo / hamburger $165k solo — entrypoints
  verified) as alternative slot candidates if live data shows the route family handles the
  tetsu crowd better than local H2H suggests; (c) the elite wheat-fert loop requires a
  compiled/route-class volume base we don't have the source for.

## Artifacts

- `topbots/goosebot_v8_differentiator.py` (falsified, kept for reference)
- `topbots/tetsu_r5_v14_nightpremium.py` (falsified, kept for reference)
- Live: v4b-fixed 56047687, 2900-verbatim 56048083 (both climbing)
- Quota: 1 remaining today (reserve) — no submissions made this session per directive
