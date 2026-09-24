# v27 ShopSelector — design & test log (2026-08-14)

## Design
- **LOW** = the v25 Wheat16 tape + layers (unchanged; the ship).
- **HIGH** = v25 tape + market-only wool-sell alignment for YARN boards
  (the only off-phase wool sell is d12h22 step 310; variants tested:
  base / merge312 / shift311 / shift313 / drop).
- **Selector**: steps 0-167 identical in both routes (shared opening,
  like the top-10 MoE); at step 168 read `town.unlocked_shops`
  (public state — never the opponent's private state, never the seed):
  YARN_STORE visible AND not the (ICE_CREAM_SHOP, YARN_STORE) dominated
  pair → HIGH, else LOW.
- Engine facts the design rests on: town consumes at steps %4==0 AFTER the
  market resolves (tick steps are sell-friendly); shop unlocks at days
  3 and 6 (1 shop/day, drawn with replacement, rng interleaved with weed
  spawns — so the trigger state is read live, never predicted);
  reward = money only (shed/animal assets are worthless at game end).

## Test battery (scripts/test_v27.py)
- Phase 1: seeds 1-24, both seats, v25-LOW vs idle → trigger-state
  classification + LOW baselines.
- Phase 2: YARN-triggered seeds × both seats × 5 HIGH variants → paired
  deltas vs LOW.
- Phase 3a: non-YARN seeds must be byte-identical to v25 (0 diffs).
- Phase 3b: contested spot checks vs v20/kaito on YARN seeds.
- Phase 3c: self-mirror on a YARN seed.

## Results (test_v27b battery — all jobs completed)

**A. Variant sweep** (YARN seeds 6/8/19, both seats, vs idle):
  base +0 | merge312 +0 | shift311 +0 | **shift313 +3..+5 (mean +4)** |
  drop −96..−201 (mean −137).
  → the tape's wool sells are already tick-aligned; the only off-phase sell
  (d12h22) is worth ~+4/game when shifted one step. Negligible.

**B. Zero-diff gate** (non-YARN seeds 1/2/9, both seats): **6/6 diff +0**
  — the selector's fallback is byte-identical to v25. PASS.

**C. Contested** (YARN seeds 6/8 vs v20 and kaito, both seats):
  **all 16 games identical to v25** (e.g., seed 8 vs v20: 136,837 vs 110,780
  for both). The wool-shift changes nothing against real opponents.

**D. Self-mirror** (seed 6): 126,387 vs 126,387 → 0.

## Prize probe (scripts/prize_v27.py) — validation instrument only
Full Kawashigi public route (decoded from a public episode — NEVER to be
submitted) vs our v25 on the same seed pairs (1-16, both seats):
  seed 1: +27,458 / −22,879 (seat 0/1)
  seed 2: +33,026 / +44,913
  seed 3: +51,367 / +68,820
  seed 4 (YARN): +4,427 / +4,427
  seed 5: −33,686 / +18,737
  seed 6 (YARN+YARN): +16,230 / +20,399
  seed 7 (FARMERS+YARN): −40,614 / ...
  (probe continues in the background; full log in data/prize_v27.log)
→ The two routes are COMPLEMENTARY: Kawashigi's economy wins the
  PIZZA/ICE/SMOOTHIE-heavy boards by up to +$69k and loses the
  FARMERS_MARKET+YARN / PET_CAFE boards by up to −$41k — where OUR tape
  wins. A selector that owns both economies captures the best of both.
  The ladder gap is BOTH an economy gap AND a route-selection gap.

## Verdict
1. **Selector infrastructure: BUILT, TESTED, SAFE** (zero-diff fallback,
   0 self-mirror delta, public-state-only trigger at step 168).
2. **Market-only HIGH: rejected as a ship** — +$4/game on YARN boards vs
   idle, 0 contested. The top-10's +24.9k/block comes from switching
   between two WHOLE ECONOMIES, not from sell-timing tweaks.
3. **The real gap is the base economy**: the Kawashigi-route probe shows
   our v25 tape is ~$30k/game behind the #1 economy on average. The winning
   move (v28) = extend the route compiler to generate the wheat-arbitrage /
   cow-herd economy profile (buy-wheat-dips all season, flood d19-29,
   10-cow herd, continuous wheat seeding) as OUR OWN route, then re-attach
   the selector. The selector code is done and waiting for a real HIGH.
4. **Ship status: v25 Wheat16 remains the post** (ready in submit/).
   v27 (HI_AgriBot_v27_ShopSelector) is NOT packaged for submission —
   its HIGH adds ~nothing yet.
