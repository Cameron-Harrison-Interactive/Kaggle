# STATE 89 — v11.16 LEAN-COW rebuild (in progress)

Goal: the tape that beats the meta. Design locked from SESSION 88 §7 + CD/DJA forensics:

## Design (v11.16)
- Herd: 11-13 cows / 2-4 sheep (final), ZERO escapes.
- Hands: 6-8/day (was 10-15). Hand cost is the biggest cash sink we found:
  our $8.3k vs CD's ~$210 total. 6-8 hands = 144-192 hand slots + 24 farmer
  = 168-216 slots/day; 12 animals need ~60 (feed+care+fert) + ~60 crop ops.
- Cash flow (CD-proven purchase timing, CD game ep 101359580):
  D0: 3c/2s + MELON 5 + WHEAT 5 seed (all-in, ~$628 left)
  D5: +1 COW + BUY_LAND (NE $1000) — funded by D4 wheat harvest sale (CD sold 36)
  D6: +2-3 COW — funded by 2-sheep wool start + melon wave + wheat
  D9: +2 COW — funded by milk start + melon D10 wave
  D15/D16: +1-2 COW if cash (optional, stretch to 13)
- FERT: sell collected FERT immediately (standing sweep, DJA/CD pattern).
- Keep: wheat feed pipeline (the backbone), D1 seed fix (2 seeds before double
  plant — the (2,1) class kill), strawberry D2 plant (CD does it, first yield D10).
- Kill: D6 COW 4 + D7 COW 2 wave (funded by the 4-sheep wool wave we no longer have).

## Hard constraints (from SESSION 88)
- Shed capacity 100 is binding (runs 98/100 on v11.12): shrink the wheat MM
  (wheat_batch 60 -> 30) in the new route's config if it overflows.
- RNG-safe authoring: new tiles/placements are FINE (they change tile state but
  deterministically — the RNG stream shift is absorbed by using the same route
  selection; verify no shop-draw flips in the 8-seed bench).
- FEED discipline: every animal fed same-day at placement + >=28/30 days after.
  The (2,1) class = the benchmark of what NOT to do.

## Bench gate (ship only if ALL pass)
1. Solo 8 seeds [1,3,5,7,9,11,13,19]: all green vs v11.12, 0 escapes,
   per-animal feed coverage >=28/30.
2. 80-game matrix (bt/v46/k2900/moon/soil x 8 seeds x 2 seats): non-regression
   vs v11.12.
3. Ghost A/B: CD 101359580, haodou 101363961, Djaafar 101381927,
   Sahil 101366252, 21-regress 101085547/101197456/101115302: flip >=3 of the
   6 cow-heavy losses, regress ghosts stay green.

## Progress log
- [x] CD replay forensics: full purchase/hand/sell schedule extracted (below).
- [ ] diff 14a (rejected 2c/2s D0) vs v11.12 routes — what exactly changed.
- [ ] build v11.16 prefix (D0-D9) on the default route.
- [ ] instrumented solo: per-animal feed tracking, cash curve, escapes.
- [ ] extend D10-D29 (feed circuits for 12+ animals at 6-8 hands).
- [ ] bench gate.
- [x] (session 92) v1116d state re-verified in fresh env: D11 h1 (5,3)
      placement walk mechanically VALID (seeds 1/3 traced; NE lands D6H16 via
      the s160 wool-sale ordering; (5,3) pasture pre-built; place+same-day
      feed; designed (4,3) cu1 spike). h2h failure reproduced bit-exact
      ($25,879 vs $124,273, 3 cows stranded) = NE-land funding cascade, not a
      walk bug. Re-measured solo-8 avg $107,761 / 0 escapes (recorded
      $95,664 — delta noted, verdict unchanged: line stays DEAD). Full
      details + build-doc corrections (actual 8c/1s, not 12c/1s; D7 cow lands
      at (3,1), not (6,1)/(5,2)) in SESSION_92_REPORT.md.
- [x] (session 93) Adaptive tomato lever (session-91 "next build") BUILT
      (v1122 = v11.12 + runtime module, zero new walks), trigger verified on
      3 meta replays (shop-count observable; burn model engine-verified),
      mechanism works end-to-end (D18 conversion, 0 escapes, D29 peak sells),
      but MEASURED NEGATIVE across the whole premium range (feed + wheat-MM
      suppression + shed-capacity cost stack) — SHELVED with full evidence:
      SESSION_93_REPORT.md + rejected/v1122_tomato_README.md. Live pair
      holds; remaining levers unchanged (rating catch-up, meta loss mining).
- [x] (session 94) RESULTS: diffed shipped main.py (sub 55829084, 2256.9) vs
      bench v1112_seedfix.py — exactly one step differs: s24 D1H00 (LIVE =
      WHEAT prod 5 + seed 1; BENCH = prod 4 + seed 2 = the documented D1
      seed fix). The live slot never received the fix; every session-86+
      bench number is the seedfix tape. Mirror live-vs-seedfix: 16 games,
      avg -$47 (statistical tie, 0 escapes). All 3 session-91 loss
      archetypes are measured WINS with the current tape (goose +9.4k,
      peikopon +7.4k, dimenti +21.3k — both tape variants). Packaged
      /home/user/submission_v1112_seedfix.tar.gz (smoke-tested) awaiting
      user GO to submit. Details: SESSION_94_RESULTS.md.
- [x] (session 95) BRAND-NEW TAPE built per user instruction (v12.1
      METAKILL: 3 iterations — D0 early cow / unconditional meta-kill
- [x] (session 96) "Try both vs the submitted tapes": v130 early tomato
      farm (scoped 13-tile SW wave, all routes) MEASURED DEAD: -$41.3k/game
      vs v1112, -$41.5k vs v1113, solo $119.9k (-$42k); root cause:
      strawberry trades ~$234/u in standard games vs tomato ~$60/u, the
      premium only exists in >=3-pizza shop draws the latch can't catch in
      time. v131 goose economy (4S+2G D0) BLOCKED: geese placed D0 but the
      $2,992 D0 budget breaks the D1 wheat buy -> all 6 animals escape D2
      ($644); the D1-D3 hand-feed surgery is the v11.16 fragility class.
      Fourth independent confirmation v11.12 = measured optimum.
      SESSION_96_REPORT.md.
      sells / 20 pre-authored route variants with opp-farm latches).
      Measured NEGATIVE on every component: D0 cow = cash wall (re-
      confirmed); sell-timing counter = structurally dead (no exploitable
      price differential; meta dumps are timing redistributions, measured
      $0..-$2.1k vs the 5 real metas); pure-tape format = -$3.5k/mirror
      game vs the runtime repair layers; peikopon route-table fragility =
      -$20.8k. Quarantined rejected/v121_metakill.py + README. The only
      structurally new win left = product differentiation (early 30-tile
      tomato farm — the peikopon +$18.5k edge; multi-session choreography
      build, v11.16 risk profile) or the untried goose tape (lower
      ceiling). Details: SESSION_95_REPORT.md.

## CD reference (ep 101359580, seat 0) — the working 16-cow economy
Animals/day: D0:5 (3c2s) D5:6 D6:9 D8:10 D9:11 D11:12 D16:13 D17:14
             D18:16 D19:17 D24:18 D25:17(esc) D26:18 D27:15(3 esc) D28:16
BUY_ANIMAL:  D0:5  D5:1(+LAND)  D6:4  D9:2  D15:4  D16:4   (20 total)
HIRE:        D0:4 D1:3 D2:4 D3:4 D4:4 D5:4 D6:2 (stays ~4/day all game)
D0 places:   C(4,4) s2, C(3,4) s5, C(4,3) s9, S(4,2) s14, S(3,3) s17
D0 buys:     2c2s (2200) + COW 1 (s1) + MELON 5 seed + WHEAT 9 seed + hire 4
             + WHEAT product 4+1+1+1  => $3000 -> ~$500 by D0EOD
D1:          3 hires, NO animals, feed cycle + WHEAT plant x2, seed wheat 2
D2:          4 hires, STRAWBERRY 2 seed + plant x2, WHEAT plant x2, wheat prod 5
D3:          4 hires, SELL FERT 5 (D3H00), wheat prod ~6x1 (feed trickle)
D4:          4 hires, SELL FERT 5 (D4H00), STRAWBERRY 5 seed, WHEAT 4 seed,
             HARVEST (2,1) D4H15
D5:          4 hires, SELL FERT 5 + SELL WHEAT 36 (D5H00!!), BUY COW 1 + BUY_LAND
             (D5H01, $1100 -> $30 cash), cow placed C(5,4) D5H04
D6:          +4 animals (3c/1s?), SELL FERT 5 + WHEAT 3 + WOOL 11 (D6 = wool wave!)
D8:          MILK 18 first milk sale (D8 = cow first_yield)
D10:         WHEAT 113 + MELON 30 (melon wave), WOOL 6
D11-D17:     WHEAT 150-223/day, MILK 9-24/day, STRAWBERRY 2-26/day
D27:         MILK 36 (the +$9.3k day)
Endgame:     4 escapes (2c D26/D28, 2s D28) — accepted cost, still won by ~$1.8k

## Files
- builder to write: _ref/build_v1116.py (decode v1112 routes, new default route)
- 14a reference: topbots/rejected/v1114a_cowfirst.py (2c/2s D0, broken cash)
- 14b1 reference: topbots/rejected/v1114b1_cowroute.py (has (3,3) D3 cow feed
  circuit, D9-D29, reusable for the (3,3) tile)
- bench: /home/user/_ref/run_isolated.py (add v1116 entry)

## v1a RESULTS (2026-08-29) — REJECTED (cash wall, quantified)

v1116v1a = 14a D0 (2c/2s) + CD timing (D5 +1c, D6 COW4->2, D7 COW2->1, WHEAT 9
seed, MELON 5). Market-only. Benched solo 8:
- Seeds 1,3,5,7,9,13,19: -8k..-27k, final herd 9c/2s (2 cow buys FAILED)
- Seed 11: CATASTROPHIC -62.9k, 4 escapes D23, route-flip cascade
  (the purchase failures change tile state -> weed-RNG shift -> shop-draw
  flip -> desync. The session-86 risk channel, live.)

Buy-commit forensics (seeds 1,3, identical pattern):
  D4H00 COW: OK (cash 434)
  D5H01 COW: FAIL (cash 383 < 400) — $17 short
  D6H10 COW: FAIL (cash 45) — 2-sheep wool wave ~$2k smaller than 4-sheep
  D6H13 COW 2: OK (1026->626)
  D7/D8/D10: OK
The 2-sheep D0 wool wave (~$1.3k) cannot fund the D5-D7 cow wave ($2.4k).
CD's funding = the D5 wheat sale (36u @ ~$31 = ~$1.1k) which requires his
D0-D2 wheat plant circuit (9 seed D0 + 2 seed D2 = 11 plants, vs v11.12's 6).
Market re-timing alone cannot close the gap. The wheat pipeline rebuild is
mandatory.

## v1b SPEC (next build) — the CD D0-D5 circuit, adapted

Market (default route):
  D0: COW 3 + SHEEP 2 (2200) + MELON 5 (400) + WHEAT 9 seed (90) + HIRE 2
      + WHEAT product 4 (~116) => ~$192-232 left (CD's exact opening)
  D1: HIRE 3, WHEAT seed 2 (CD: BUY_SEED WHEAT 2 at D1H00)
  D2: HIRE 4, BUY_SEED WHEAT 2 + BUY_SEED STRAWBERRY 2 (CD's D2)
  D4: COW 1 (keep v11.12) + BUY_SEED WHEAT 4 (CD D4H18, for replant)
  D5: SELL WHEAT ~30-40 (D5H00, the harvest wave) + COW 1 (D5H01)
  D6: COW 2 @H13 + LAND (drop v11.12's D6H10 COW 1)
  D7: COW 1, D8: COW 1, D10: COW 2 + LAND SW, D15: COW 1 (13th, w/ circuit)
  => 12c/2s by D10, 13c/2s by D15

Choreography (the actual work — D0-D5 hand/farmer circuit):
  1. D0: 5th placement slot (CD places 5th animal D0H17 via a hand; v11.12
     has 4 slots: farmer (4,4)s4/(4,3)s9 + hands (3,4)/(3,3)). New tile:
     (2,4) or (3,2) (empty NW). +BUILD/+PLACE/+walk for the 3rd cow... 
     NOTE: 3 cows + 2 sheep = 5 pastures D0.
  2. D0-D1: plant 9 wheat (9 seed): reassign 3-4 PLANT slots from the 7 melon
     to 5 wheat... v11.12 D0 plants: WHEAT 5 + MELON 7. v1b: WHEAT 9 + MELON 5
     = +4 wheat plants, -2 melon. Hand PLANT slots to reassign: 2 melon->wheat
     + 2 new wheat (from D1 free slots / farmer walk).
  3. D2: +4 plant slots (WHEAT 2 + STRAWBERRY 2) — CD's D2.
  4. D4-D5: expand the wheat harvest circuit: v11.12 sells 6 wheat D5; v1b
     must harvest+pick ~33-40 (11 plants x 3-4). Hand HARVEST/PICKUP slots on
     D4H15-D5H12.
  5. Feed the 5 D0 animals D0-D4: v11.12's 4-animal cycle +1 (the 5th cow on
     the new tile joins the farmer's D0-D3 cycle — +3-4 slots/day D0-D3).
  Verify per seed: all 5 D0 animals fed D0-D4, no escapes, D5 cash >= $1100
  (cow + land headroom), 9c/2s by D8 (wait: 3+1+2+1+1 = 8c/2s by D8),
  11c/2s by D10.

RNG note: new placements change tile state D0 onward -> the route-draw RNG
shifts from D0 (not D153). The 5 routes' draw logic (s88+/s153/s160/s216)
may pick different routes than v11.12 for the same seed — EXPECT and ACCEPT
it (the new economy is route-agnostic in D0-D5; the suffix from D6+ must be
verified per drawn route). Track drawn route per seed in the bench.

Files: _ref/build_v1116.py (extend for v1b), rejected/v1116v1a.py (evidence).

## v1b RESULTS (2026-08-29, 2nd iteration) — D0-D8 economy PROVEN on default seeds

v1116v1b (rejected/v1116v1b.py, builder _ref/build_v1116b.py): 3c/2s D0 + D1 cow
(3,2) + D2 sheep (2,4) + D4 cow + D6 COW 1 + LAND + D7 COW 1 + D8 COW 1 +
D10 COW 2 + LAND SW. FERT-drop D1 fix (s39 DROP at (3,4) shed tile), s6
PICKUP SHEEP fix.

Bench (8 seeds, per-animal tracking):
- Default-route seeds (1,3,7,9,11,13): 7c/1s placed, 1 escape each = the (2,1)
  D4 cow unfed D5-D6 (feeds in v11.12 come from the 4-sheep D5-D6 circuit;
  v1b's D5-D6 wheat supply/hand choreography no longer covers (2,1)).
  Cash $57k-103k (vs v11.12 $132k-189k): missing 3-4 cows + the escape.
- Seed 5: ROUTE FLIPPED (D0-D3 tile change -> weed-RNG shift -> yarn/bakery
  suffix from s88 on the 2-sheep prefix) -> 4c/3s chaos. Seed 19 (yarn_first
  native): 2 escapes ((2,1) D7, (4,3) D8) - the yarn D4+ circuits assume
  4-sheep D0.
- PROVEN working: D0-D3 all 5 animals placed+fed, D1 FERT sells fire,
  D4/D6/D7/D8/D10 cow buys succeed on default seeds, D6 LAND succeeds,
  D0-D8 placements follow the v11.12 tiles (same feed circuits).

REMAINING WORK (in order):
1. (2,1) D5-D6 feed on the default route: find the hand that feeds (2,1) in
   v11.12 D5/D6 (sim trace of hand positions), verify v1b's wheat supply
   reaches it; likely +1-2 FEED slot reassignments on D5-D6 (the D5 circuit
   has 6 hands with free slots).
2. D10-D29: the D10 SW pair + the 11th-12th cow (D15, funded by melon wave +
   milk) need placement+daily-feed circuits at 10-12 animals (h4's D10 circuit
   extends; the D12+ hand circuits gain 1-2 FEED stops/day each).
3. Yarn/bakery suffixes (yarn_first/second/third, bakery_capital): their
   D4-D29 circuits assume 4-sheep D0; rebuild for 3c/2s (or give them a
   sheep-heavier D0-D3 variant via a s88+ gate if the shop draw warrants).
4. Route-flip audit: for each of the 8 bench seeds, confirm the drawn route
   matches the one the suffix was built for (log the s88/s153/s160/s216
   shop-draw outcomes).
5. Hand-count reduction 10-15 -> 6-8 (the $8.3k lever) - LAST, after the
   layout is stable (fewer hands = fewer feed slots = the (2,1) class risk).

Bench gate unchanged: solo 8 all-green (0 escapes, feed >=28/30), 80-game
matrix vs v11.12 non-regression, ghost A/B flip >=3/6.

## v1b POST-MORTEM + v1c SPEC (2026-08-29, 3rd iteration)

ROOT CAUSES found (sim-verified, seed 1):
1. The (3,2) D1 cow was NEVER BOUGHT: D0 buys COW 3, the farmer places all 3
   ((4,4)(4,3)(4,2)); D1 s24 PICKUP COW finds an empty shed -> no-op; s30
   PLACE = no-op. The cow was never in the game. The (2,4) sheep (D2) DID place
   (shed sheep from D0) but the shared D4+ circuits don't feed it.
2. Adding a 4th D0 cow is over-budget: COW 4 + SHEEP 2 + MELON 4 + WHEAT 5 +
   HIRE 2 + WHEAT product 8 = $3,322 > $3,000. CD's economy = 5 animals D0-D1
   (his 5th placed D0H17), funded by MELON 5 + WHEAT 9 + WHEAT product 8 =
   $2,924. The 6th animal (v1b's (2,4) sheep or (3,2) cow) must be DEFERRED
   to D2/D5 (shed-funded or sale-funded), not D0.
3. Route-flip mechanism CONFIRMED: the D0 melon removals change the empty-tile
   count at D0-D2 EODs -> _spawn_weeds consumes a different number of
   rng.random() -> the D2EOD shop draw (next_day%3==0) differs -> the s88+
   route draw flips (seed 1: default -> yarn; action scores at s156/s160
   match yarn_first/second 4-0). The 4-sheep suffix circuits then mishandle
   the cow-first prefix (the (2,1) D4 cow escapes: the yarn D5-D6 circuits
   don't feed (2,1) - it's a default-economy animal).
4. Cash at D5H01 = $210 (seed 1) vs the COW 1's $400: the D5 wheat sale is
   only $248 (8u) because the D4-D5 harvest circuits (v11.12's 9 slots for 9
   plants) under-harvest the v1b 9-plant layout by ~1 slot ((1,0) vs (0,3)).

V1c SPEC (CD-aligned D0-D5, default route first):
- s0: COW 3 + SHEEP 2, MELON 5, WHEAT 9 seed, HIRE 2, WHEAT product 4 (=$2,818)
- s2: WHEAT product 4 (D0EOD $66; 8 wheat product total = D0+D1 feed for the
  4 placed animals; the (3,4) sheep is the 4th placed D0H21)
- D1: v11.12 D1 VERBATIM (4-animal cycle + FERT drop s43). s29 BUILD (3,2)
  stays (secures the tile); s30 PLACE COW -> ['PASS'].
- D2: v1b s67-71 (2,4) sheep placement + s72-73 (D3) as in v1b; market:
  WHEAT seed 2 + STRAWBERRY seed 2 at s68, SELL FERT 5 at s70.
- D3: 5-animal cycle (drop the (3,2) FEED from v1b D3F; s94-95 free -> extend
  the (4,2) CARE/COLLECT).
- D4: v11.12 verbatim (COW 1 + (2,1) placement + WHEAT seed 5).
- D5: COW 1 at s139 (D5H19, AFTER the SELL WHEAT 3 + harvest sales fire;
  ~$500 cash by H19); D5 farmer s141-143: PICKUP COW (4,4), W (3,4), S (3,3);
  D6 s144-148: S (3,2) PLACE FEED (the (4,4) cow D6 unfed = cu1, safe, fed D7).
  The (3,2) cow first yields D14 (1 day late vs D13).
- D5 hands: +2-3 HARVEST slots from free WATER slots on the D5 wheat tiles
  ((2,2)(1,3)(0,4)(3,0)(3,1)(0,2)(1,1)(0,1)(0,3)) -> +$100-180 D5 sale.
- D6-D10: v1b (COW 1 D6H13 + LAND, COW 1 D7, COW 1 D8, COW 2 + LAND SW D10).
- EXPECTED default-route herd: 10c/2s by D10, (3,2) cow D6, (2,4) sheep D3.
  Feed circuits: (2,4) sheep + (3,2) cow need +1 FEED stop/day each in the
  D6-D29 circuits (the v1114b1 (3,3) circuit in build_v1114_full.py is the
  reference pattern: 1-2 slot detours per day, verified isolated).
- ROUTES: after default is green on its 6 seeds, rebuild yarn_first/second/
  third + bakery_capital D4-D29 for the 3c/2s prefix (their wool economy can
  KEEP the 2 sheep + add the (2,4) sheep = 3-sheep wool; their D4+ sheep
  placement slots are free in v1c). Audit the drawn route per bench seed.
- Hand reduction (the $8.3k lever): LAST, only after all 5 routes are stable.

## SESSION 89b PROGRESS (v1c.2 — the D0-D10 core is VERIFIED)

v1116v1c.py (topbots/, WIP checkpoint) = v11.12 with the cow-first D0-D10 core:
- D0: COW 3 + SHEEP 2 all-in (3c at (4,4)(4,3)(4,2), S at (3,4)), MELON 5,
  WHEAT 9 seed, HIRE 2. The (3,2) pasture is built D0H07 (empty, reserved for
  the D15+ ramp; its melon m2 is dropped). The (2,4) melon m7 kept (MELON 5
  uses s4 (3,3), s5 (4,1), s8 (4,0), s13 (2,3), s19 (1,4) slots; h1 s20 = WATER
  so (2,4) stays empty for the ramp).
- D1/D2/D3: v11.12 verbatim (the (2,4) sheep was DROPPED — its D3-D8 feed loop
  needed 20+ slot detours that the runtime controller reorders unpredictably;
  the 6th animal comes as a D15+ cow instead).
- D4: COW 1 (funded: D3H16 WHEAT product 3+1 cut to 0). Placed at (2,1) via the
  v11.12 h0 circuit.
- D6: SELL WOOL 6 moved s153->s160 (fires before the BUY_LAND; the LAND now
  succeeds with the thin 2-sheep cash).
- D7/D8: v11.12's COW 1 buys REMOVED (thin cash: $77/$284 < $400 at runtime).
- D10: HIRE 9->4 (s240), COW 2->1 (s248) — the COW 1 STILL FAILS at runtime
  ($29 cash at s248: the runtime "sparse controller" reorders/replaces tape
  actions, so the static cash model is off by ~$400 — the D10 melon sells and
  FERT sells fire in a different order than the static tape implies). The D10
  LAND (s252) also fails (cash ~$400 < $2,000).

VERIFIED (seed 1, full 720 steps): 5c/2s final, ZERO escapes, cu1 spikes only
(D2/D4/D8 pattern = v11.12 baseline behavior, recovers next day), final $52,404
(v11.12 seed 1: $179,265 — the gap is the 6 missing ramp cows + the D10 cow).

## NEXT SESSION PLAN (the D15+ cow ramp — the build that wins)

1. D10 cow fix: move the COW 1 buy to D11H01 (s265, after the SELL FERT 8+1+3
   fire: cash ~$2,000) and the SW LAND to D13H00 (s312, cash ~$2,700 at D12EOD).
   The D11H00 STRAWBERRY 13 seed ($1,300) + MELON 4 seed ($320) buys must be
   cut or deferred (they eat the D11 cash; the D11 strawberry/melon replants
   can move to D12-D13 when the cash is there).
2. The SW ramp cows (6-7): D13 pair (3,5)/(4,5) [the v11.12 h4 D10 placement
   circuit pattern, shifted to D13H00-H10], D18 pair (3,6)/(4,6), D23 pair
   (3,7)/(4,7), D27 single (2,5) or (4,7)-adjacent. Each placement = a farmer
   or h4 walk detour (BUILD/PLACE/FEED x2, ~8-10 slots) — the v1114b1 build
   (rejected/v1114b1_cowroute.py, build_v1114_full.py) has the reference
   pattern (20-slot cow circuits, geometry-verified).
3. Daily feed for the 6-7 ramp cows D14-D29: 1-2 FEED stops/day each in the
   h4/h0 farmer walks (the v1114b1 (3,3) circuit is the reference: 1-2 slot
   detours per day). Feed wheat supply: the D18/D23 replant waves (the v11.12
   D18-D24 wheat replants) feed the ramp; verify the hand wheat pickups cover
   the +6-7 FEEDs/day (the v11.12 hands carry 4-5 wheat/day for 15 animals;
   +6 FEEDs needs +1-2 wheat pickups/day — check the s115/s211/s311 pickup
   slots have room).
4. The 4 suffixes (yarn_first/second/third, bakery_capital): their D4-D29
   circuits are v11.12-verbatim in v1116v1c (the cow-first D0-D3 changes apply
   to all 5 routes since the prefix is shared before the s88 draw) — the
   suffixes' sheep-heavy D4+ circuits (the yarn wool economy) must be checked
   per drawn seed (the route-flip risk: the D0 melon changes shifted the weed
   RNG; bench seeds 1,3,5,9,11,13 drew DEFAULT, 7 drew YARN_SECOND, 19 drew
   YARN_FIRST in v11.12 — RE-AUDIT per seed in v1116v1c, the D0-D3 tile
   changes shift the draws again).
5. Bench gate (unchanged): solo 8 all-green (0 escapes, feed >=28/30) +
   80-game matrix non-regression vs v11.12 + ghost A/B (CD 101359580, haodou
   101363961, Djaafar 101381927, Sahil 101366252, 21-regress
   101085547/101197456/101115302). Ship only if ALL pass.
6. The 6th-7th cow (D27 single) + the (3,2) tile cow: optional stretch after
   the 11c/2s core is green.

RISK NOTE (learned this session): the v44 runtime "sparse controller"
reorders/replaces tape actions at runtime (the D10 cash model was off by
$400 — the melon sells and FERT sells fire in a runtime-different order).
Cash-timing assumptions for the ramp buys MUST be verified in the sim
(commit-hook harness: the _commit_unit hook pattern used this session), not
by static cash arithmetic.

HANDOFF PROMPT for the next session: "Continue the kaggriculture v11.16
cow-first build. Read kaggriculture/STATE_89.md (the SESSION 89b section) and
follow its NEXT SESSION PLAN. The v1116v1c.py checkpoint is verified (5c/2s,
0 escapes, $52k seed 1); start at plan item 1."
