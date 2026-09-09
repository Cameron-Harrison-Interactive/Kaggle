# SESSION 86 — (2,1) class root cause: D1 seed-cash fragility (NOT tape desync) + v11.12 seed fix (SHIP)

## 1. ep 101085547 forensics — the real causal chain (verified 6/6 escape episodes)

Loss: −$13,000 vs Chakrabhuana V Deva (cow-first: 13 productive animals vs our 11 + 3
stranded). Rank 471→1259 was rotation (SESSION 85 §2); recovered to **#1162 @ 1651.7
as of 21:14** (fresh leaderboard pulled; from the 1259/1615.8 low at 19:48).

**Correction to SESSION 85's forensics.** The "1-step desync consuming the feed slot"
was a misread, from two harness facts discovered this session:
1. The framework records `steps[k]['action']` = the action the agent generated in
   response to step **k−1** (the state struct is mutated in place; the action field
   carries into the recorded post-state). The live tape ran **perfectly on schedule**
   — every farmer/hand/market action equals `tape[step]` (checked exhaustively).
2. `run_isolated.py`'s `make_ghost` had the same off-by-one (replayed the opponent 1
   step behind, distorting price paths). **Fixed**: ghost now returns `A_s = tape[s+1]`.
   Session 80–85 ghost A/Bs ran the opponent 1 step behind: directionally useful, not
   exact. The field matrix (real bots) was unaffected.

**The actual chain** (all 6 harvested (2,1)-escape episodes show the identical
signature — 101085547, 101115302, 101033101, 101124429, 101058279, 101051430):
1. Opponent front-loads wheat buying (Chakrabhuana: ~38 WHEAT product buys D0–D1)
   → wheat price +10–15% vs the solo price path.
2. D1H00 tape `['BUY_PRODUCT','WHEAT',5] + ['BUY_SEED','WHEAT',1]` consumes ~$164 of
   $167 → **$0–11 left** (solo path: $19+).
3. D1H01 tape `[..., ['BUY_SEED','WHEAT',1]]` → the 2nd seed buy **fails (funds)**.
   Seeds = 1 (verified: seeds_w=1 at D1H09 in all 6 episodes).
4. D1H09: h0 AND h1 both `PLANT WHEAT` → 2 requests vs 1 seed → the engine's
   **atomic PLANT rule drops BOTH** → the (1,1) and (0,2) wheat plants never exist
   (verified: (1,1) empty at D5H09 in all 6; pass control plants both).
5. D5H08: h1 `HARVEST @(1,1)` → nothing. D5H12: h1 stands ON (2,1) with **0 wheat**
   → FEED no-op. Cow unfed all of D5.
6. D6: same chain for the h2 feeder. Cow unfed all of D6.
7. D7H00: `consecutive_unfed=2` → **(2,1) COW escapes**.
8. Downstream: the broken D7-morning wheat choreography also breaks the EOD cow-drop
   re-placement loop (5 cows dropped D7, only 2 re-placed by D9 → 3 stranded to game
   end). **The re-stranding is not an independent bug in this game — it is the same
   root cause one wave later.** Under v11.12 all 4 dropped cows re-place by D9.

Engine rules that shape this (kaggle_environments 1.32.7, verified against the
interpreter source; local engine reproduces the live game bit-for-bit, 0 mismatches
over 719 steps):
- FEED acts on the tile UNDER the unit, costs 1 WHEAT, no-op if `fed_today`.
- Animals escape at daily refresh when `consecutive_unfed >= 2`.
- Hands + unit inventories **reset every EOD** — the D5 feed wheat must be carried
  fresh from a D5-morning harvest (the D1-planted (1,1) crop is the pipeline source).
- Atomic PLANT validation: if total PLANT requests for a crop in a step exceed
  available seeds, ALL of that crop's PLANTs are dropped.
- **New risk channel found**: `_spawn_weeds` consumes `rng.random()` once per EMPTY
  tile before the daily shop draw. Any change to farm tile state (e.g. this fix's
  +1 D1 wheat plant) shifts the shop-draw RNG stream and can flip the route at
  s153/s216/s160 (yarn_second / yarn_third / bakery_capital). Measured once in the
  solo battery (seed 5: −$17.9k route flip); net across the 80-game matrix still
  positive. Inherent to this engine; applies to every tape change.

## 2. v11.12 seed fix (tape-level, all 5 routes, one line)

`step 24` (D1H00) market: `['BUY_PRODUCT','WHEAT',5] + ['BUY_SEED','WHEAT',1]`
→ `['BUY_PRODUCT','WHEAT',4] + ['BUY_SEED','WHEAT',2]` (default / yarn_first /
yarn_second / yarn_third / bakery_capital — the D0–D1 opening is identical across
routes; first route divergence is s88+).

- 2 seeds guaranteed before the D1H09 double plant → atomic rule a no-op on every
  observed price path. ~$19 cheaper at live prices, ~$16 at solo prices.
- D1H01's `BUY_SEED WHEAT 1` kept as the LAST order (fires only if cash remains →
  3rd seed for later replants).
- Cost: one fewer wheat product carried to the D5 sell window (~$33).

### Bench A — ghost A/B (fixed harness; live seed + live opponent tape)

| ep (opp) | v1110 margin (esc) | v1112 margin (esc) | swing |
|---|---:|---:|---:|
| 101085547 (Chakrabhuana V Deva) | **−13,025** (1 + 3 stranded; ≈ live −13,000) | **+25,528** (0; 0 stranded) | +38.5k |
| 101115302 (Bernardus) | −19,904 (1) | −18,954 (0) | +1.0k |
| 101033101 (Shinichiro Yoshida) | −8,738 (1) | +14,521 (0) | +23.3k |
| 101124429 (ИТМОНИ AI B2B 67 SaaS) | −9,289 (1) | +21,664 (0) | +30.9k |
| 101058279 (Muhammed Ashiq Abdul Khader) | −5,701 (1) | +24,032 (0) | +29.7k |
| 101051430 (Auto Fermers) | −14,655 (1) | −703 (0) | +14.0k |

v1110 reproduces every live loss (same escape, same stranding, margin ≈ live).
v1112: **0 escapes in all 6** (including the D11/D15 cluster in 101033101 — later
feeds share the same D1-seed pipeline), 4 of 6 flip to wins. Ghost margins include
fixed-opponent-tape artifacts (the ghost's own earnings move with the price path) —
treat swings as an upper bound; the field matrix is the conservative gate.

### Bench B — 80-game field matrix (v1112 vs v1110 head-to-head, real bots)

| opponent | avg margin delta/game |
|---|---:|
| bt (breaking tie) | −7 (16×0) |
| v46 | −27 |
| k2900 | **+5,222** |
| moon | +979 |
| soil | **+3,777** |
| **total** | **+$1,989/game over 80 games** (nonzero 80/80) |

Escapes on the field: v1112 saves the moon/seed-7 (2,1) escape (+$3,012 game).
v1112 takes one new escape (k2900/seed-5, **day 29** endgame, not the (2,1) class;
−$2,036 game) — a late-feed edge to watch, not a regression of the fixed class.

Solo vs pass: avg −$2,234 — 7 of 8 seeds within ±$28 of v1110; seed 5 alone is
−$17,876, fully explained by the empty-tile RNG route flip (§1, risk channel):
v1110 → yarn_second, v1112 → default on that shop config. Net matrix is positive
despite it.

## 3. SHIPPED — v11.12 live as sub 55829084 (posted 2026-08-28 00:04 UTC)

User standard: "subs should not be losing anything before rating 2000" → full loss
audit of all 31 losses across v11.9 (50W-16L, +$11.2k/game) and v11.10
(47W-15L, +$8.4k/game) drove an early ship instead of waiting for tomorrow:

| loss class | count | total | status |
|---|---:|---:|---|
| (2,1) COW D7 escape (incl. cluster 101033101) | **8** | **~$111k** | **killed by v11.12** (ghost-verified 0/8; 2 of the 8 lost as late as 22:19Z today) |
| production-dominance (cow-heavy opps: meryol −21.8k, cheezyp −16.4k, Lucien −13.5k, Yohanes −11.2k, Shree85 −8.7k) | 5 | ~$72k | → v11.13 cow-heavy route (below) |
| close games (<−$7k, mostly −$2…−5k; one −$50) | 18 | ~$76k | noise floor; terminal-tactics only |

Note: the two big v11.10 losses of the evening (ep 101197456 −$20,826,
101211075 −$12,926) are the (2,1) class with the identical signature — the class
was still bleeding live until v11.12 went in.

Ship mechanics: posting retires **v11.9** (last-2 rule; active pair now
v11.10 + v11.12). Team floor = v11.10's rating for a few hours; v11.12 starts at
600 and converges (v11.9 took ~3h to 1615, ~24h to its peak). Expected net:
class-free sub in the pair within hours, floor recovers past current level
tomorrow. `numToday` read 0 before posting → if any slot friction appears, the
same file ships on tomorrow's 5 fresh slots (no code change needed).

## 5. REGRESSION AUDIT (user: "bot has been losing a lot more since your changes")

Head-to-head A/B, all four live versions on IDENTICAL games (local engine,
bit-identical to live; 80-game field matrix x4 + solo):

**Code archaeology:** the tape was NEVER different across v11.7→v11.8b→v11.9→
v11.10. Every change was runtime overlay in `v44.gold_floor`:
- v11.7→v11.8b: +`_apply_feed_rescue` (rescue v1, wheat-blind dispatch)
- v11.8b→v11.9: +`endgame_premium_flush` (dormant in all loss ghosts)
- v11.9→v11.10: rescue v1 → rescue v2 (wheat-aware, H18+ dispatch)

**8 biggest live-loss games, all versions ghost A/B:**

| game | v117 | v118b | v119 | v1110 | v1112 | v1113* |
|---|---:|---:|---:|---:|---:|---:|
| 101033101 Shinichiro | −19.5k e3 | −21.4k e3 | −21.4k e3 | −8.7k e1 | +14.5k | +15.1k |
| 101135940 Lucien | −13.5k e1 | −13.5k e1 | −13.5k e1 | −16.2k e1 | −0.3k | −0.3k |
| 101176917 meryol | −21.8k | −21.8k | −21.8k | −21.8k | −21.7k | −21.7k |
| 101106157 cheezyp | −16.3k | −16.3k | −16.4k | −16.4k | −16.5k | −16.4k |
| 101170080 Yohanes | −7.1k e1 | −7.1k e1 | −7.1k e1 | −11.2k e1 | +10.2k | +9.0k |
| 101078834 Shree85 | −8.7k | −8.7k | −8.7k | −8.7k | −5.5k | −5.5k |
| 101197456 Triston | −10.4k e1 | −10.9k e1 | −10.9k e1 | **−20.8k** e1 | +6.1k | +6.5k |
| 101211075 Lucien | −5.9k e1 | −5.9k e1 | −5.9k e1 | **−13.0k** e1 | +29.0k | +29.5k |

* v11.13 = v11.12's tape + v11.7's gold_floor (all rescue layers removed).
`topbots/v1113_norescue.py`, build: `_ref/build_v1113.py`.

**80-game field matrix (identical games, 5 real opponent bots x 8 seeds x 2 seats):**

| version | bt | v46 | k2900 | moon | soil | avg/game | escapes |
|---|---:|---:|---:|---:|---:|---:|---:|
| v11.7 | +10,108 | +920 | +1,680 | +9,544 | +1,365 | **+4,723** | 6 |
| v11.8b | +10,067 | +654 | +1,457 | +9,411 | +1,143 | +4,546 | 6 |
| v11.9 | +10,067 | +653 | +1,458 | +9,412 | +1,156 | +4,549 | 6 |
| v11.10 | +9,792 | +559 | +1,242 | +8,966 | +939 | +4,300 | 1 |

Solo vs pass: all four $163.6–163.7k (identical). The rescue layers' net EV on
this matrix is **−$423/game** (hijack cost > escapes avoided); on the ladder
against the new cow-heavy meta they're much worse (below).

Findings:
1. **User was right that a fixer layer regressed games:** rescue v2 (v11.10)
   regressed 4 of these 8 by −2.7k…−10.4k vs v11.7 — it dispatches, fails to
   save the cow, AND hijacks hand-hours. v11.10 is the worst of the stack here
   AND the worst on the matrix. Layers removed in v11.13.
2. **But v11.7 is not the golden standard:** it loses all 8 (worst-including
   3 escapes vs Shinichiro). The 2k era never faced these cow-heavy opponents.
3. **v11.12/v11.13 are best in all 8** — the tape fix does the work; the rescue
   layers are ≈0 value once the root bug is fixed (ghost totals: v1113 +16.3k vs
   v1112 +15.8k vs v1110 −114.2k).
4. meryol/cheezyp (−16…−22k, no escapes, every version) = the cow-heavy meta
   gap → v11.13 cow-heavy route (section 4), NOT a regression.

**Live check:** v11.12 (sub 55829084) posted 00:04Z, verified, **4-0 in its
first 4 public games** (00:07–00:19Z), games every ~4 min.

Ship plan (after matrix confirms): let v11.12 build a rating floor for 1-2h,
then post v11.13 (no-rescue, same tape) — retires v11.10 (weakest), floor =
v11.12's rating, and the ladder runs the cleanest version. Cow-heavy route
(v11.14) next, benched against the 5 production-loss ghosts.

## 4. Next: v11.14 — cow-heavy route variant (pure tape/route work, no code)

Target: the 5 production-dominance losses (opponents running 8c/5s: milk 835 vs
333, strawberry 748 vs 422, melon 232 vs 72 in 101085547).

Economics (engine config): COW $400, first yield D8, MILK every 2d (base 160) →
a cow placed D1 earns ~11 yields over the season; SHEEP $500, first yield D6,
WOOL every 3d (base 200) → 8 yields. Our default route buys its first cows on
D6 (they first yield D14) — vs opponents opening 1 COW on D1. The counter is an
EARLY cow, not a crop change.

Design (new route variant, selected at step 0 by shop draw like the others —
no opponent reactivity, no runtime code):
- s0: `BUY_ANIMAL SHEEP 4` → `BUY_ANIMAL COW 1 + BUY_ANIMAL SHEEP 3` (frees $100).
- s1: `PICKUP SHEEP 4` → `PICKUP SHEEP 3`; hand h0 (spawns (4,5) D0H01) detours
  through the shed to `PICKUP COW 1` (h0's s1/s2 moves re-pointed).
- s4/s9/s14: PLACE SHEEP unchanged; the 4th early slot (s21 PLACE SHEEP) →
  `PLACE COW` on the s20-built pasture (cow lands ~D0H21, fed by the s22 FEED
  slot; yields from D8 ✓ full season).
- Feed coverage for the early cow D1–D3: the D1 farmer FEED slots (s25/s30/s34)
  already cycle the shed; verify the cow's tile is on the D1–D3 FEED path (if
  not, re-point one s27–s31 hand FEED — the (2,1)-class discipline from §1
  applies: the cow needs a same-day feed at placement, v11.12's D1 seed fix
  keeps the wheat supply intact).
- D4+: existing D4/D6/D7 cow buys unchanged → end herd ~9c/3s (vs 4s-heavy
  today), matching the 8c/5s meta while keeping our wheat edge.

Bench gate (ship only if ≥ v11.12 on both):
1. Ghost A/B vs the 5 production-loss opponents (101176917 meryol, 101106157
   cheezyp, 101135940 Lucien, 101170080 Yohanes, 101078834 Shree85): must
   materially close the margin.
2. 80-game field matrix vs v11.12: must not regress (the close-game noise
   floor is the budget).
Also queued behind v11.13: EOD re-stranding hardening (redundant morning place
slots) and a day-29 endgame feed top-up if it recurs.

## 6. LADDER RESEARCH — "know everyone, drop them first" (user directive)

User: post at will + research the whole leaderboard; revive the session-61/62
plan ("know their sell timing, sell before them").

**Built this session:**
- `TOP_LADDER_INTEL.md` — all top-60 teams profiled from **their own public
  episodes** (new API path: team -> public subs -> episodes -> replays; scripts
  `_ref/harvest_top.py` + `_ref/harvest_top_replays.py`, library
  `_ref/TOP_LADDER_LIBRARY.json`, re-runnable).
- Cross-referenced the 278-opponent library (who we've faced, our W-L, their
  sell hours) against the fresh leaderboard.

**THE META (this is why we lost today's big games):**
- **55/60 top teams are COW_HEAVY.** Dominant final herd: **11c/4s (24 teams)**,
  then 9c/4s. Cows yield MILK every 2 days from D8; our first cows were bought
  D6 (first yield D14) — the 835-vs-333 milk gap, now explained.
- **They sell at NIGHT: H22/H23/H00/H02 (43/40/38/23 votes). Our tape sells at
  H01** — the old meta, one night late on the scarcity price curve.
- Only 9/60 are strictly cow-first on D0; the rest load cows D1-D4.

**v11.14 counter (pure tape, two edits, per the intel doc):**
1. D1-D3 cow injection so we end 9-11c/3-4s (match the block).
2. Move race-item SELLs (MILK/WOOL/STRAW/MELON/FERT) from H01 into H22-H00,
   one hour ahead of their H23/H00 wave. (Sell orders are market-level — no
   hand-hour cost, unlike the rejected rescue layers.)
Gate: ghost A/B vs the 6 cow-heavy losses must flip to wins + 80-game matrix
non-regression. Build after v11.12/v11.13 stabilize (no churn while both
climb).

**Live state at report time:** v11.12 (sub 55829084) **13W-0L**, v11.13 (sub
55829890, no-rescue) 1W-0L, both playing every ~4 min. Team ~#1050 @ 1689 and
climbing; floor rises as both converge.

## 7. LOSS AUDIT @ #198 (user: "shouldn't lose to anyone under 2000") + CROP DUSTA GAME

### Loss profiles (fresh data, all games to date)
- **v11.12 (sub 55829084): 81 games 48W-33L.** 32 of 33 losses vs opponents rated
  >=2000 (the 2200-3021 band — losing to better teams is the correct profile).
  Only sub-2000 loss: Kaito Fukami (1831, −$2.5k close game).
- **v11.13 (sub 55829890, no-rescue): 73 games 51W-22L** (better win rate).
  16 of 22 losses vs currently-sub-2000 opponents, all in its 01:31-04:39Z
  early-climb window. Three worst analyzed (zero escapes in all — the (2,1)
  class is dead):
  - haodou092 (−$11.7k): COW-FIRST opening (COW as 1st buy; cows from D0 → milk
    from D8). 478 milk vs our 337 with only 7 cows vs our 11.
  - SahilKumarTolani (−$10.9k): opp 10c/4s cow-first; we ran the 6c/10s route
    variant that shop config; we sold $95k MORE than them and still lost =
    over-trading (bought ~$106k more, converted less by game end).
  - Djaafar (−$10.2k): opp 6c/8s; we out-milked them (337 vs 267) and out-sold
    them; loss = late-game wave + trading, no escapes.
  - NOTE: the "fert factory 2,935" scare was a standing-order-count artifact —
    actual max fert held: 30 (opp) vs 24 (us). No fert class. Ruled out.
- Common thread of ALL big losses (incl. #1): **early-cow builds beat our
  D6-cow opening on the milk/production wave.** Mid-band is full of cow-first.

### Crop Dusta game (ep 101359580, v11.12 vs #1 @ 3021, −$1,773)
- CD build: **16 COWS**, cow-first from D0 (COW,COW,SHEEP,SHEEP,COW,COW...),
  sells concentrated H02/H01 (night band), 1,431 wheat.
- CD had 4 endgame escapes (2 cows D26/D28, 2 sheep D28) and still won.
- Money: we led D5-D9; CD's wave took +5k→+9k D13-D20; we clawed back to
  −3k by D21-D26 (our mid-late game is strong vs #1); CD's D27 day (+$9.3k vs
  our +$2.8k) = the whole margin. Our 11 cows MATCHED their 16 on milk
  (337 vs 335) — the gap is build scale + late wave, not feed efficiency.
- Their older profile (ep 100939868) showed a 7g/3c/1s goose build — CD mixes
  builds; the 16-cow one is the one that beats our current tape.

### v11.14 (rebuilt scope): COW-FIRST route, not just "cow-heavy"
1. D0-D1: COW-first opening (COW, COW, SHEEP, SHEEP...), cows placed D0-D2
   (milk from D8, full season) — matches CD and the mid-band cow-first block.
2. End herd target 12-14c/3-4s (the 11c/4s block is the FLOOR of the top 60;
   #1 runs 16c).
3. Keep the wheat edge (our 3,408 wheat sold vs CD's 1,431 — it works).
4. Sell band: race items into H22-H02 (CD's own band), one slot ahead.
Gate: ghost A/B vs CD (101359580) + the 3 mid-band losses must flip; 80-game
matrix non-regression. Post retires v11.13 (weaker-rated of the actives);
floor stays at v11.12's rating.

## 8. v11.14a (cow-first D0 swap) — REJECTED (quarantined in topbots/v1114a_cowfirst.py)

Tried the surgical 2c/2s D0 opening (cows into the existing D0 placement slots,
sheep pickup moved to the s6 CARE slot). Benched before any post:

- Solo 8 seeds: −$7.8k…−$87.0k vs v11.12 (5 of 8 badly negative; one D23
  mass-escape in the yarn variant).
- Ghost A/B (the 6 real loss games): wins only Djaafar (−10.2k → +2.0k);
  Crop Dusta −1.8k → −16.0k; haodou −11.7k → −31.8k; Sahil +17.4k → −73.3k;
  and it re-broke the (2,1) class (two regress ghosts: +25.5k → −39.4k,
  +6.1k → −52.6k with 3 escapes).

Diagnosis: the tape's cash flow is deeply sized around the $2,000 4-sheep D0.
Swapping $200 of it into cows cascades: D1-D7 purchases starve, the feed
pipeline (which funds off the D4-D7 wheat/melon cash) collapses, and the (2,1)
fix's protection is moot when the whole wave desyncs. A PARTIAL cow swap is not
a valid edit; cow-first requires a full cash-flow rebuild (CD's D5 cash = $30:
all-in animals, minimal other crops, scaled feed choreography for 14-16 animals).

**KEY REFRAME (from the top-60 harvest):** 24 of the 60 top teams run OUR exact
11c/4s build and sit at 2800-2900 (Blu3s #8, tetsuya #7, SCNU, G!vIOne, peggy...).
We run the same build at 2257. **The build is not the ceiling — execution is.**
#1's 16c is the 2900→3000+ tier, not the 2250→2800 gap.

Revised v11.14 plan (in order, each benched on the 80-game matrix + ghosts):
1. **Execution pass on the current 11c/4s route** (the 2250→2800 gap):
   sell-band tuning (race items later into the H20-H02 scarcity window — in the
   CD game our top sell hours were H22/H18/H14/H10 while CD packed H02/H01;
   price rises as shared inventory drops intraday), D10-D20 tempo (CD took
   +$9k there), D27 late wave (their +$9.3k day vs our +$2.8k).
2. **Full cow-first route** (new 6th route, ~12-16c, full cash-flow rebuild +
   scaled feed choreography) — the 2800→3000 swing. Bigger build; after #1.

## 9. v11.14 full cow-first route — DEIGNED & DE-RISKED (authoring = next block)

### D2-D3 tape reality (corrected — earlier "dormant template" claim retracted)
An initial sim dump (buggy: loop started at si=48 without stepping the sim, so it
re-emitted the D0 opening under D2 labels) suggested a dormant D2-D3 placement
template. A clean probe (agent output vs route index, fresh sim) disproves it:
the real s48-s95 (identical in all 5 routes) is a pure FEED / PICKUP_WHEAT /
CARE / COLLECT_FERT 5-hour farmer cycle over the 4 D0 animals, plus D2 wheat
buys/sells. There is NO dormant placement infrastructure. The cow-first build
therefore requires authoring new pickup/build/place slots AND extending every
daily feed cycle (D2-D29) from 4-5 animals to 12-14 — the larger surgery
session 85 warned about, now precisely scoped.

### Cash-flow math (from the CD game, measured)
- Our D0-D9 sells $8.4k vs CD $11.6k; we sell $79k MORE total yet lose —
  spend $141.7k vs their $60.5k. Milk: $33.3k/11 late cows (4.6x ROI) vs their
  $51.1k/16 early cows (8x ROI). The lever = cows earlier, funded by cutting
  melons (7->5) + shrinking the D6 cluster (COW 4 -> 2), NOT by cutting wheat
  (the feed backbone) or strawberries (the $35k line).

### v11.14 build spec (slot-level, to be authored + verified next block)
Base: v11.12 routes. Final target: 12c/2s (was 11c/4s).
1. D0: COW 2 + SHEEP 2, MELON 7->5, WHEAT 4->3 [the 14a edits — validated:
   both cows place at (4,4)/(4,3) D0 and feed clean D0-D8]
2. D2H00 (s48 M): + BUY_ANIMAL COW 2 (funded by the D0 savings + D1 fert sells;
   verified headroom: s48 has 3 orders, cap 10)
3. D2 placement + daily-cycle extension (the authoring work, per-route in sim):
   - D2: farmer cycle gets +PICKUP COW 2 (needs a shed-adjacent slot: s48-s52
     window, farmer at (4,4)), +2 walks, +2 BUILD_PASTURE, +2 PLACE COW —
     target tiles (3,4) and (3,2) (both empty, adjacent to the existing farm
     and to each other's walk); the 4 existing FEED/CARE/COLLECT_FERT slots
     must be preserved (a dropped slot = unfed day = the class we just killed)
   - D2-D29: every daily FEED/CARE cycle (farmer 5-hour cycle + the D5+ hand
     FEED waves) gains +2 animal coverage — the 2 new cows must be fed >=28/30
     days; candidate slots per day identified in sim (h2/h3 hand waves on D4-D6,
     farmer cycle on D2-D3)
   - COLLECT_FERT coverage for the 2 new cows from D10 (fertilizer line)
4. D6H13 (s157 M): COW 4 -> 2 [frees $800; 2 late cows still placed by the
   existing s160/s173 choreography — verify both still place]
5. UNTOUCHED: wheat pipeline + step-24 seed fix + (1,1)/(0,2) plants, (2,1) D4
   cow + its feed slots, D7 buys, sell schedule, all hand crop choreography.

### Verification harness (built: _ref/v1114a_verify.py — extends to v11.14)
Per-seed asserts: (a) all 12 cows placed with placed_day (2x D0, 2x D2, 1x D4,
7x D6-D7), (b) zero escapes D0-D29, (c) every animal fed >=28/30 days,
(d) D4 (2,1) cow fed D4-D8 (the class regression check), (e) final cash vs
v11.12 delta. Gate: 8-seed solo all-green + 80-game matrix non-regression +
ghost A/B (CD + 3 mid-band) flipped.

## 10. CORRECTED v11.14 DESIGN — full route rework (the only safe cow-first path)

### Measured criterion data (219-ep harvest; user: "shouldn't lose to anyone <2000")
- v11.9: vs sub-2000 opponents 39W-10L (80%); vs 2000+ 2W-2L
- v11.10: vs sub-2000 17W-7L (71%); vs 2000+ 3W-1L
- The sub-2000 losses are exactly the COW-FIRST opponents (Shinichiro −21.4k,
  Bernardus −19.9k, Chakrabhuana −13.0k, Shree85, cmasch, Nagamatsur...). The
  sub-2000 band is full of cow-first builders who beat our 4-sheep opening.
  The criterion gap == the cow-first gap. One build fixes both.

### Design (full rework, no slot edits)
1. **Default prefix D0-D5 rebalance to ~4-6 cows by D2**: D0 2c/2s + D2 2c
   (the prefix is shared, so this is the single D0-D5 economy for all games).
2. **Every suffix rebalanced** (default, yarn_first/second/third, bakery_capital):
   - default suffix: D6-D7 cow buys trimmed 8 -> 5-6 (total 12-14c final,
     3-4s) — the 11c/4s block is the floor of the top 60; target its ceiling.
   - yarn suffixes: sheep economy kept, but D0 2c/2s means their wool line
     starts at 2 sheep — late sheep buys (D7/D9) must be +3-5 to restore the
     wool revenue that funds the wheat line (the Sahil cascade fix).
   - bakery_capital: evaluate its cow-check gating against the new prefix.
3. **Feed-coverage verification (the hard part)**: the D2-D4 farmer cycle is
   24/24 slots packed and already covers 4 animals; 6+ animals need hand-assisted
   feed loops (CD runs 12 hands for 16 cows — the 11c/4s block is
   farmer-feed-limited, which is why it tops out where it does). Every animal's
   daily FEED must be sim-verified >=28/30 days (a gap = the escape class).
4. **Bench gates (all must pass)**: solo 8 seeds all-green (0 escapes, per-animal
   feed coverage), 80-game field matrix vs v11.12 non-regression, ghost A/B:
   the 6 cow-heavy loss games (CD, haodou, Bernardus-class, Sahil-NCTRL must be
   ~0 delta, (2,1) regress games stay green).

### Ship decision (2026-08-28)
HOLD the live pair (v11.12 48W-33L / v11.13 51W-23L, both winning streaks,
team #195 @ 2257 — best state to date, above the old 1994.5 peak). No marginal
patch ships today (churn was the problem). Next ship = the full cow-first rework
once benched green. The D0-swap variants (v1114a/v1114d) are quarantined in
topbots/rejected/ with the bench evidence.
