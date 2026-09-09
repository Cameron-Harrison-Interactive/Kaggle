# SESSION 93 REPORT — v1116d re-verified; adaptive tomato lever built, measured, shelved

Date: 2026-08-31. Predecessor: SESSION_92_REPORT.md (v1116d state + D11 walk
verification) and the SESSION_90/91 verdicts (cow-first dead; live pair holds).

## Task 1 — v1116d current state (the D11 h1 (5,3) placement walk): DONE

Full details in SESSION_92_REPORT.md. Recap: the walk is mechanically valid
(seeds 1/3 traced step-by-step: NE lands D6H16, (5,3) pasture pre-built,
place+same-day feed, designed (4,3) cu1 spike); the h2h failure reproduces
bit-exact ($25,879 vs $124,273) = the NE-land funding cascade, not a walk bug.
Re-measured solo-8: avg $107,761, 0 escapes (recorded $95,664 — delta noted,
verdict unchanged).

## Task 2 — the adaptive tomato lever (the session-91 "next build"): BUILT, MEASURED, SHELVED

### Ground truth (3 top-16 replays re-downloaded via kagglesdk, token in
### fetch_replays.py; kept in /tmp/eps2 per convention)

| game | tomato shops D15 | tomato price D1->D29 | verdict |
|------|------------------|----------------------|---------|
| peikopon 100841489 | 3 (4 by D18) | $60 -> $474 (D29H15 $522) | PREMIUM (they sold 145u D29 = +$18.5k) |
| William Diment 100882715 | 2 | $60 -> $131 | no premium |
| CD goose 100939868 | 1 | $60 -> $76 | no premium |

Engine price model decoded (kaggriculture.py, verified): price = base +
amp*f(I0 - inventory), TOMATO: base 60, I0 10000, T 200, hinge f(u)=
u+8*max(0,u-1)^2, amp 24. Town burn (verified to within 1 unit/day on all 3
replays): 6 units/day per PIZZA_SHOP/FARMERS_MARKET instance + 1/day town
center. => the premium is a pure function of the public shop list: **the
trigger needs no price inversion — count the shops.**

### Build: v1122 = v11.12 + `_TOMATO_MOD` (builder `_ref/build_v1122_tomato.py`,
### tape `topbots/rejected/v1122_tomato.py`)

Route-agnostic, detection-based, zero new walk choreography:
- Trigger: >= 3 tomato shops during D12H01-D17H01 (decision latched).
- D17H01: BUY_SEED TOMATO 12.
- D18: the W-column replant triplets (DIG/HARVEST -> PLANT WHEAT -> WATER,
  same unit) get PLANT WHEAT -> PLANT TOMATO (7 tiles on default; D18-only —
  the D19 triplets mostly miss the same-day water and die, measured 4/5).
- Replacement feed (the converted waves were the herd's endgame feed):
  dynamic budget 15/tile+20, 14/day cap, D20H01-D28H01, cash/slot-guarded;
  CARROT 30*planted/9 at D27H01. (Buying only through D24 was measured to
  leave the D27-D29 crunch unfunded: 2 animals escape at cu>=2.)
- D26/D27: the replant cycle's own HARVEST at our tiles retargeted to WATER
  (HOLD the yield on the tile — a D26/D27 pickup overflows the near-full
  shed, cap 100: measured 9-12 units discarded at EOD D27).
- D28: the cycle's HARVEST (WATER->HARVEST fallback) takes the accumulated
  ~3 units/tile into the shed the D28 mega-sell just emptied.
- D29H17: SELL TOMATO (full shed count), H17-H23 price-peak window.

### Measured (process-isolated, engine 1.32.7)

ZERO-DIFF when the trigger is off — bit-exact vs v1112 to the dollar:
solo seeds 1/3/5/7/9/11/13/19, ghost goose ($89,615/$80,237), ghost peikopon
current-v1112 game ($98,117/$90,673). (Side note: the premium in that game
is RNG — the current v11.12 doesn't reproduce the recorded p0's shop draws,
and already beats the recorded p0's $86,405 in the matchup.)

FORCED-ACTIVE (trigger bypassed; mechanism works end to end — 7-12 tiles
planted, 100% D18 survival, 0 escapes, 18-21 units sold at the D29 peak):
- peikopon ghost, real prices (peak ~$130): $94,7xx vs $98,117 = **-$3.4k**
- solo seed 1, boosted TOMATO price curve (peak ~$575): $176.7k vs $179.3k
  = **-$2.6k**

### Why negative (full cost stack, all measured — see the quarantine README)

Revenue 18 x ~$575 = ~$10.4k (boosted) vs costs: replacement feed ~$4.4k +
seeds $600 + **wheat-MM suppression ~$2-4k** (the steady 14/day feed buys
flatten the wheat price and kill v11.12's wheat market-maker cycle, ~680
units of round trips over D20-D26 in the baseline) + lost late-strawberry
replants ~$1.2k + 6 units never sold (3 on field at EOD, 3 unharvested)
~$3.4k. Negative in every measured configuration, including the extreme
premium.

### Verdict

**SHELVED (measured negative).** The 12-tile endgame conversion is
structurally ~breakeven at best: the no-new-walk variant that the session-91
spec pointed at does not clear the feed+MM+capacity cost stack. The real
peikopon play ($18.5k/145u) is a D8-D12 30+-tile early farm with dedicated
choreography — the fragile class that cost $65k/game on cow-first. Not
pursued. The trigger + burn model, shed-capacity dynamics, and force-active
testing pattern are documented in the quarantine README for any future
early-farm build.

## State

- LIVE PAIR HOLDS: v11.12 (2256.9) + v11.13 (1754.7). Nothing shippable this
  session — same outcome as 90/91, with one more lever measured dead.
- Quarantined: rejected/v1116v1a-v1e, rejected/v1121_tomato (static),
  rejected/v1122_tomato (adaptive) + READMEs.
- run_isolated.py: v1116d/e -> rejected/ paths; v1122 -> rejected/ (do not
  ship).
- /tmp/eps2 now has 5 gate replays (7 in sessions 90/91 minus the 2 already
  in _ref): 100841489, 100939868, 100882715 + 101359580, 101381927
  (re-download: python3 _ref/fetch_replays.py <eids>).
- Remaining levers (unchanged, priority order): (1) rating catch-up — the
  current tape beats the recorded 3000-tier strategies, let it accumulate
  matches; (2) meta-episode loss mining at scale (ghost bench vs ~300
  recorded games; the 3 loss archetypes now have replays in /tmp/eps2);
  (3) seed-19 endgame carried-items leak (~$26/game, bundle with #2).

## Tools added this session (_ref/)

build_v1122_tomato.py (builder), trace_1116d_d11.py (D11 walk trace). Test
harnesses kept in /tmp this session: test1122_forced.py (force-active
monkeypatch pattern), trace_tom.py / trace_fill.py / diffcash.py / diffmkt.py
(unit-flow, shed-capacity, and cash-diff tracing).
