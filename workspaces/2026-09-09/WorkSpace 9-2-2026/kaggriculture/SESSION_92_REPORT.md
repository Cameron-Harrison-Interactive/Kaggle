# SESSION 92 REPORT — v1116d state verification: the D11 h1 (5,3) placement walk

Date: 2026-08-31. Predecessor: SESSION_90_REPORT.md (+91 addendum; cow-first line
declared dead, v1116d/e quarantined in rejected/).

Task: verify the current v1116d state in the freshly reinstalled environment,
specifically the validity of the D11 h1 (5,3) placement walk (the last new
mechanism in build_v1116d.py), before recording the continuation.

## Setup notes

- Reinstalled `kaggle` + `kagglesdk` (kaggle_environments 1.32.7 was present).
- `run_isolated.py` VERSIONS: v1116d/v1116e entries pointed at the old
  `topbots/` paths after the session-90 quarantine move; fixed to
  `topbots/rejected/v1116v1d.py` / `v1116v1e.py`.
- New targeted trace: `_ref/trace_1116d_d11.py [seed]` (per-step h1 position +
  action, tile deltas on the walk's tiles, shed COW, cash, unlocked quadrants,
  D6 land timeline, full-game herd/escapes). Process-isolated, one agent load.

## Verdict: the D11 h1 (5,3) walk is MECHANICALLY VALID (default-route seeds)

Traced in full on seeds 1 and 3 (both draw default; both end 8C/1S, 0 escapes):

1. **NE land IS unlocked by D11 in solo** — bought D6H16 (s160): the
   `SELL WOOL 6` moved to s160 by v1c fires BEFORE the `BUY_LAND` in the same
   step (v1c's deliberate ordering works). land: [NW] -> [NW,NE] at s160;
   SW unlocked D10H12 -> [NW,NE,SW] by D11H0.
2. **(5,3) is a pre-built empty PASTURE at D11H01** (built by v11.12's D7
   circuit; visible as 'p' in D10H0/D11H0 layouts).
3. **The walk executes exactly as scripted** (seed 1, cash $4,640->):
   h1 spawns (4,5) H01 PICKUP WHEAT 5 -> H02 FEED (4,5) [D10-pair cow]
   -> H03 PICKUP COW 1 (shed 0->1 from the D11H01 buy, consumed)
   -> H04 E (5,5) -> H05 N (5,4) [pass-through over the D6-cow tile,
   walkable] -> H06 N (5,3) -> H07 PLACE COW (PASTURE -> COW fed=False)
   -> H08 FEED (fed=True, same-day) -> H09 W (4,3) -> H10 N (4,2)
   -> H11 FEED / H12 CARE / H13 COLLECT_FERT -> H14 E (5,2)
   -> H15 FEED / H16 CARE / H17 COLLECT_FERT -> H18 S (5,3)
   -> H19 FEED (no-op, already fed — as designed) / H20 CARE / H21 COLLECT_FERT
   -> H22 W (4,3) -> H23 N.
4. **(4,3) takes the designed cu1 spike** (its D11 FEED was dropped for the
   detour; recovers D12H02, cu1 -> fed). Matches the build comment exactly.
5. Engine semantics confirmed (kaggriculture.py): movement onto LOCKED tiles
   IS allowed; tile operations (BUILD/PLACE/FEED/PLANT...) no-op on them.
   So the walk is valid *as a walk* even with NE locked — only the
   PLACE/FEED silently no-op (see below).

## The h2h failure is the funding cascade, NOT a walk bug (reproduced bit-exact)

v1116d vs v1112, seed 1, seat 0, re-run this session:
`cash $25,879 vs $124,273, herd 4C, shed {COW 3, SHEEP 1}, escapes [3]`
— identical to the session-90 forensics line. Chain (unchanged): D2 sheep
feed miss under market pressure -> no wool -> D6H16 NE land fails -> (5,3)
pasture never builds -> the D11 walk still walks, but PLACE/FEED no-op ->
the cow strands in the shed (with the D10 pair: 3 stranded). The walk
question is answered: **it is valid; what kills it in h2h is NE-land funding.**

## Re-measured v1116d solo bench (fresh env, process-isolated, vs pass)

| seed |  1     |  3     |  5     |  7     |  9     |  11    | 13     | 19     | avg     |
|------|--------|--------|--------|--------|--------|--------|--------|--------|---------|
| $    | 116611 | 122213 | 124380 |  96770 | 116327 |  61059 | 119180 | 105546 | 107761  |
| herd | 8C/1S  | 8C/1S  | 8C/1S  | 4C/3S  | 8C/1S  | 4C/3S  | 8C/1S  | 8C/1S  | escapes 0 |

- 6 seeds (1,3,5,9,13,19) = default route with the (5,3) D11 placement;
  seeds 7,11 drew yarn suffixes (4C/3S sheep economy — their D11 circuits are
  the suffix's own, not the default h1 walk).
- **Delta vs the session-90 record**: re-measured avg $107,761 vs recorded
  $95,664 (+$12.1k). The current rejected/ tape is whatever was last written
  before quarantine; the recorded bench may have benched an intermediate
  state. Direction and verdict unchanged: ~-$54k/game vs v11.12's $161.5k
  solo avg, 0 escapes. No conclusion depends on the delta.

## Build-doc inaccuracies found (for the record; do not "fix" the quarantined tape)

1. build_v1116d.py header claims "final default herd: 12c/1s placed".
   Measured: **8c/1s**. The D6 COW 1 buy FAILS in solo too ($93/$21 cash at
   s154 < $400); the D8 COW 1 buy fails ($96 at D8H0); the D7 COW 2 buy yields
   only 1 of 2. Effective wave: D7(1) + D10 pair(2) + D11(1).
2. Header claims the D7 farmer circuit "placed D7H04/H09 at (6,1),(5,2)".
   Measured: the surviving D7 cow sits in the shed D8-D9 and is placed at
   **(3,1)** by D10H0 (v11.12's actual D7/D9 placement geometry).
3. The (6,1)/(5,2)/(5,4)/(6,4) pastures are built but stay EMPTY all game
   (their buys failed) — confirmed in D10/D11 layouts.

## Implications

- Nothing changes: the cow-first line stays DEAD (measured -), the live pair
  (v11.12 2256.9 + v11.13 1754.7) HOLDS, nothing to ship.
- Useful reference for future builds: the h1 D11 detour is a PROVEN
  place+same-day-feed circuit pattern (spawn at the shed-adjacent corner,
  3-step approach, PLACE, FEED, re-join the original walk with one dropped
  FEED -> accepted cu1 spike). Reusable if a future tape funds NE land earlier
  (the only h2h wall left on this walk is D6H16 cash).
- Tooling: run_isolated.py v1116d/e now resolve to rejected/; trace added.

## State

- LIVE PAIR HOLDS (v11.12 + v11.13). Quarantine unchanged (v1116v1a-v1e in
  rejected/). Next levers per the session-90/91 verdict stand: rating
  catch-up (let the current tape accumulate matches), meta-episode loss-mining
  at scale, adaptive tomato replant as the only measured >$2k lever.
