# SESSION 96 REPORT — "try both vs our other tapes that are submitted": both tried, both dead/blocked

Date: 2026-08-31. User instruction: try both of the session-95 candidates
(the early tomato farm + the goose economy tape) against the submitted
tapes (v11.12 sub 55829084/resubmit 55917889 + v11.13 sub 55829890).

## Candidate 1 — v130 early tomato farm: BUILT, MEASURED DEAD

Scoped build on the v12.0 pure-tape platform (builder
`_ref/build_v130_tomato.py`, tape now `topbots/rejected/v130_tomato.py`):
the full strawberry program (all plant/sell/seed ops, all 5 routes)
converted to tomato — 13-tile SW wave (D10-D11) + the D2 plants, sells
D10-D29. (The session-95 full spec is 30+ tiles D8-D12 with dedicated
walks — a multi-session build; this scoped version tests the same
portfolio thesis on the existing walk geometry.)

Measured (process-isolated, engine 1.32.7):
- Solo-8: $119,878 avg (vs $162,949 v120 platform, $161,459 v1112) = **-$42k**
- vs v1112 (submitted), 8 seeds: -$21.7k to -$58.8k, **avg -$41.3k/game**
- vs v1113 (submitted), 8 seeds: -$16.7k to -$58.8k, **avg -$41.5k/game**
- peikopon premium ghost: -$20.8k (route table picked yarn + 3 D10
  escapes — the pure-tape platform has no repair layer)

Root cause (measured, not hypothesized): in a standard game the STRAWBERRY
program trades at ~$234/u — its D16-D21 revenue is $36.6k — while the
TOMATO program trades at ~$60/u ($11.7k same window). The "product
differentiation edge" only exists in shop-draw premium games (>=3
PIZZA_SHOP/FARMERS_MARKET draws: peikopon $60->$474). Three independent
failures: (a) the premium latch can't fire before the D10-D11 plant
window (2nd pizza shop draw lands D9-D23), (b) the pure-tape platform
costs ~$3.5k/mirror game vs the runtime repair layers (session 95), (c)
in the one premium game the platform's D10 route fragility ate the edge.

Verdict: dead at this scope. The full 30-tile D8-D12 farm is a
multi-session choreography build with the v11.16 risk profile, and this
session's scoped measurement says the portfolio thesis (tomatoes replace
strawberries) loses ~$40k/mirror game in the standard pool it would face.

## Candidate 2 — v131 goose economy: BUILT (2 iterations), BLOCKED on D0-D3 feed geometry

Scoped build (builder `_ref/build_v131_goose.py`, tape now
`topbots/rejected/v131_goose.py`): D0 = 4 SHEEP (wool funding engine kept
— the 2-sheep alternative is arithmetically dead, v1a wall) + 2 GOOSE at
(3,3)+(3,2) coops on h0's walk (crops shifted: (2,2) wheat, (2,3) melon),
egg sells D5+ H01, v120's full 11-cow ramp verbatim. The full session-95
spec (7-9 geese D0) is unbuildable on the v120 slot budget (8+ animal
circuits = 32+ slots vs the 48 farmer+h0 slots including crops).

Iteration record (all sim-measured):
- v1: farmer H00 PICKUP GOOSE no-ops (same-step market commits AFTER
  unit actions — measured); h0's goose FEED no-ops (h0 carries no wheat);
  sheep buy dropped by a market rebuild bug. Geese escaped D1.
- v2: sheep buy fixed; **both geese placed D0 at (3,3)+(3,2)** ✓ and all
  4 sheep placed ✓, but: the D0 budget ($2,992 spend) leaves $22 at
  D0EOD, so the D1H00 WHEAT prod 4 buy ($40) FAILS -> the D1 feed chain
  has zero wheat -> all 6 animals unfed D1 -> **all 6 escape by D2** ->
  final $644.
- The goose D1-D3 feed needs hand-walk surgery: the trace shows a hand
  walking (3,3)->(3,2) on D1 AND D2 (the exact goose tiles), but (a) the
  hand carries no wheat there (needs a shed-adjacent PICKUP inserted +
  a walk re-sync), (b) the position/action pairing in the ad-hoc traces
  is off-by-one (untrusted for surgery), (c) each insertion derails the
  unit's downstream walk by 1-2 hours (measured in v1: one such derail
  mis-placed a placement). D3 geometry not yet traced.

Verdict: blocked on the same D0-D3 feed-geometry fragility that killed
v11.16 cow-first. The expected egg revenue (+$2-4k if it worked) is below
the surgery risk. A full-spec goose tape (7-9 geese, new platform) is a
multi-session build; nothing to ship.

## Results summary (the answer to "give me some results")

| build | vs submitted v11.12 | vs submitted v11.13 | solo | status |
|---|---|---|---|---|
| v130 tomato farm | -21.7k..-58.8k (avg -41.3k) | -16.7k..-58.8k (avg -41.5k) | $119.9k avg (-$42k) | MEASURED DEAD |
| v131 goose economy | n/a (broken tape) | n/a | $644 (all 6 animals escape D2) | BLOCKED (feed geometry) |
| v12.1 metakill (s95) | -$3.5k/mirror + $0..-$2.1k vs metas | — | $148.6-159.9k | MEASURED DEAD (s95) |
| v11.12 (submitted) | — | — | $161.5k | THE MEASURED OPTIMUM |

Fourth independent confirmation (after v11.16, v11.21/22, v12.1) that
v11.12's 4-sheep/11-cow/strawberry-wheat economy is the local optimum:
every structurally new portfolio tried loses $3-60k/game to it. The
submitted pair (v11.12 55829084 + fresh 55917889, v11.13 55829890) is the
best tape this team has produced by measurement, and the only shippable
asset.

## State

- Quarantined: rejected/v130_tomato.py, rejected/v131_goose.py (plus all
  prior). Harness entries updated to rejected/ paths.
- LIVE PAIR HOLDS. Resubmit 55917889 (session 94, per user GO) is
  accumulating matches.
- run_isolated.py: fixed a corrupted dict line (live1112/v1113 entries
  merged — v1113 KeyError, repaired this session).
- Remaining honest options, in order: (1) let the live pair accumulate
  (the current tape beats the recorded 3000-tier metas: +$7-21k/game on
  the 3 archetype ghosts, session 94); (2) a full-spec 30-tile early
  tomato farm as a committed multi-session choreography build (v11.16
  risk profile, session-95 spec); (3) nothing further — v11.12 is
  locally optimal on every axis tried.
