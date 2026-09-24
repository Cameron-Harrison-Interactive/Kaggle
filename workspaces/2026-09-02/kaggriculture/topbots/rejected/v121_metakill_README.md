# v121_metakill — the brand-new 720-step pure tape with authored meta-kill
# route variants (session 95, 2026-08-31). MEASURED NEGATIVE — quarantined,
# do not ship.

## What it is (the user's ask: a brand-new 720-step tape that beats all metas)

v12.0's pure 720-step tape (5 authored routes, no runtime controller) plus,
for each route, three pre-authored meta-kill VARIANTS (20 routes total, each
a complete 719-step schedule — only the market layer differs from the base):
  * <route>_cow : D28+ MILK sells moved to D25H01/D26H01 + self-limiting
    catches D28H01/D29H01 (sell milk before cow-metas' late cow wave)
  * <route>_wool: D28+ WOOL sells moved to D24H01/D25H01 + catches
    (before wool-factory dumps)
  * <route>_both
Route selection extends v12.0's existing table mechanism (_pick_route
opponent-farm latch): opp sheep >= 8 from D6 -> _wool; opp cows >= 8 from
D15 -> _cow; both -> _both. 100% static: no runtime logic beyond the
authored lookup table.

## Measured (process-isolated, engine 1.32.7)

Component decomposition (each tested independently):

1. PURE TAPE FORMAT (v12.0) vs v11.12 runtime, mirror 4 seeds:
   -$3.5k/game (65.8/69.5, 43.7/46.0, 46.2/48.9, 55.3/58.0). The runtime
   repair layers (feed rescue, weed repair, sparse controller) are worth
   ~$3.5k/mirror game. Solo-8: v120 $162.9k vs v1112 $161.5k BUT 6/8 seeds
   with D29 escapes (the pure tape has no endgame feed rescue).
2. META-KILL SELL VARIANTS vs the real metas (v121mk vs v1112 baselines):
   CD-cow16 101359580: +41,975 vs +41,989  (tie)
   Djaafar 101381927:  +31,363 vs +32,217  (-$854)
   Diment-wool 100882715: +19,226 vs +21,324 (-$2.1k, _wool latched)
   CD-goose 100939868:  +8,837 vs +9,378   (-$541)
   peikopon 100841489:  -20,801 vs +7,444  (-$28k; route-table picked the
                              yarn route in that draw and the pure tape
                              escaped 3 animals D10 with no repair layer)
   => the sell-timing counter is worth ~$0 to -$2k in every meta game.
3. EARLY-ANIMAL D0 (v12.1 v1 attempt): a D0 cow is unaffordable ($400 at
   D0-D2 vs $100-400 on hand — the cash wall, re-confirmed; the v1 build
   escaped 2 sheep D2 on the feed detour). 89 sessions + this session say
   v11.12's first cow at D4 is the funding optimum.

## Why the sell-timing counter is structurally dead (the finding)

In head-to-head the market price only moves on supply/consumption. The
session-91 measurement (intraday bands flat) now extends to the daily
level: selling milk/wool at D25-D26 instead of D28-D29 captures NO price
differential — the meta's D28-D29 dump is a timing redistribution of
existing supply, not new supply. Our early sell just deprecates our own
price. The only meta edge = PRODUCT DIFFERENTIATION (grow what the meta
doesn't: peikopon's 145 tomatoes = +$18.5k), which requires an early 30+
tile farm — the choreography-fragile class (v11.16 cow-first lost
$35-65k/game; v11.21/22 tomato conversion measured dead).

## What to keep

* The measurement that the pure-tape format costs ~$3.5k/mirror game vs the
  runtime controller — do not ship a pure tape while the runtime exists.
* The meta-kill variant authoring pattern (pre-authored market variants +
  table latches) is reusable if a future tape ever grows a differentiated
  product that needs meta-timed selling.
* The _pick_route rewrite (base + variant suffix) is correct and tested;
  the v3 route-priority fix preserved v12.0's early-return semantics.

Builder: _ref/build_v121_metakill.py. Test harness entry: run_isolated.py
"v121mk" (points here, quarantined).
