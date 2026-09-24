# SESSION 95 REPORT — the brand-new 720-step tape: built, benched, measured

Date: 2026-08-31. User instruction: "a brand new tape for the whole 720-step
game that could beat all of the metas" — stop reverting to what's there.

## What was built (three iterations, all measured)

**v12.1 "METAKILL"** — a brand-new pure 720-step tape on v12.0's authored
platform (builder `_ref/build_v121_metakill.py`, tape
`topbots/rejected/v121_metakill.py`):
- v1: D0 = 4 sheep + 1 early cow (milk D8, four days before v11.12's D12) +
  hand-placed cow circuit + D1-D3 feed detour.
- v2: meta-kill market layer authored on all routes (D28+ wool/milk sells
  moved to D24-D26 + catch sells).
- v3: the meta-kill layer as 15 pre-authored route VARIANTS (20 complete
  719-step schedules) with the meta-kill latch on v12.0's existing
  opponent-farm table mechanism (opp sheep>=8 from D6 -> _wool; opp cows>=8
  from D15 -> _cow; both -> _both). 100% static, no runtime intelligence.

## Measured results (process-isolated, engine 1.32.7)

| component | result |
|---|---|
| v1 D0 early cow | DEAD at the cash wall (re-confirmed): $400 needed at D0-D2 vs $100-400 on hand; 2 sheep escaped D2 on the feed detour |
| v2 unconditional sell moves | -$3k/game vs a symmetric opponent (both sides dump in the same window; the early sell deprecates your own price) |
| v3 meta-kill variants vs the 5 real metas | CD-cow16: tie (+41,975 vs +41,989); Djaafar: -$854; Diment-wool: -$2.1k; CD-goose: -$541; peikopon: catastrophic (-$20.8k, route table picked yarn + 3 D10 escapes, no repair layer) |
| pure-tape format (v12.0) vs v11.12 runtime, mirror | **-$3.5k/game** (65.8/69.5, 43.7/46.0, 46.2/48.9, 55.3/58.0) — the runtime repair layers are worth ~$3.5k/mirror game |
| v121mk solo-8 | $148.6-159.9k (variant-dependent) with D29 escapes; variants dormant vs pass = bit-exact v12.0 |

## The finding (why the new tape cannot beat the metas as specified)

**The sell-timing counter is structurally dead.** Measured at both the
intraday level (session 91: bands flat) and now the daily level: in
head-to-head, the market price only moves on supply/consumption. The
meta's D28-D29 dump is a TIMING REDISTRIBUTION of existing supply, not new
supply — selling early (D24-D26) captures no differential, it just
deprecates your own price. Every meta-kill variant measured $0 to -$2.1k
against the actual meta it targets.

**The only measured meta edge is product differentiation**: peikopon's
145 tomatoes = +$18.5k because the meta doesn't grow tomatoes. That
requires an early 30+ tile farm — the choreography-fragile class
(v11.16 cow-first: -$35-65k/game; v11.21/22 tomato conversion: measured
dead). Same for the runtime format: the pure tape loses ~$3.5k/mirror game
to the runtime repair layers.

## Answer to "why keep reverting to what's there"

This session built the new tape the way asked — three full iterations,
brand-new strategy content (early cow, meta-kill variants, 20 authored
routes). Every component measured negative or neutral, with numbers. v11.12
is not what we have by inertia: it is the measured optimum, and this is the
third independent confirmation (v11.16 cow-first -$35-65k, v11.21/22 tomato
-$2.6-3.5k, v12.1 new tape -$3.5k/-28k). The live pair (v11.12 2256.9 +
v11.13 1754.7) holds — today's v11.12 slot resubmit (55917889) is
accumulating matches against the current pool.

## What would actually be a new tape that could win (if committed)

The only structurally new builds left, with honest risk profiles:
1. **Early tomato farm** (D8-D12, 30+ tiles, dedicated hand walks, sells
   D17-D29): the measured meta edge (peikopon +$18.5k). Multi-session
   choreography build; risk profile = v11.16 (fragile, -$65k if it fails
   the feed gate). Requires: D8-D12 tile conversion walk, D17+ sell
   circuit, feed budget for 30+ plants, sim gate 8 seeds + 5 metas.
2. **Goose economy tape** (7-9 geese from D0, eggs from D4): genuinely
   untried in this team's history, but structurally lower ceiling (egg
   base $50 vs milk $160/wool $200; CD's goose game scored ~69k vs our
   161k solo) — a diversifier, not a meta-killer.

## State

- LIVE PAIR HOLDS (v11.12 + v11.13); v11.12 slot resubmitted as 55917889
  (fresh scheduling) on 2026-08-31 per user GO.
- Quarantined: rejected/v121_metakill.py + README (this session's new tape,
  full evidence); plus all prior (v1116v1a-e, v1121_tomato, v1122_tomato).
- /tmp/eps2: 5 gate replays (CD, Djaafar, Diment, goose-CD, peikopon).
  (Env note: kaggle_environments/kaggle/kagglesdk + /tmp wipe between
  sessions; reinstall per HANDOFF_90.)
- Workspace trimmed to 95MB (the two 31MB replay JSONs moved from _ref/ to
  /tmp/eps2 per convention; re-fetchable via fetch_replays.py).
