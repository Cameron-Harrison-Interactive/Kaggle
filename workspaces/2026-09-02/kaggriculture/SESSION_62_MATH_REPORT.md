# SESSION 62 — The Math of First Place (and the honest result)

## Bottom line
Today produced **exact engine math** that reframes the whole game, and a
**dead-end ledger** proving which "obvious" fixes are traps. Every behavioral
change tested was noise or negative on proper benches, so the shipped build
stays v1011 (spy version, solo $97,508 / H2H avg −$61,225 — reproduced to the
cent). The one true gap to first place is now measured, not guessed:
**the routing/assignment engine**.

## 1. Corrected market crash math (engine MARKET_PARAMS, exact)
price = base − amp·shape(inventory − I0), floor $1. Net units sold to hit $1:

| item | floors at | revenue to floor | price@100 | price@300 |
|---|---:|---:|---:|---:|
| WOOL | **58** | $7.7k | 1 | 1 |
| MILK | **75** | $6.0k | 1 | 1 |
| STRAWBERRY | **61** | $3.7k | 1 | 1 |
| MELON | **157** | $26.2k | 150 | 1 |
| FERTILIZER | **494** | $24.9k | 80 | 40 |
| CARROT | 866 | $10.7k | 23 | 15 |
| TOMATO | 537 | $11.1k | 35 | 16 |
| EGG | never (log) | $113k+ | 42 | 40 |
| WHEAT | never (log) | $57k+ | 21 | 20 |

## 2. Town shops are the demand engine (live in obs.town)
Every 4 steps each shop consumes 1 of each product (×2 single-product);
town center 1/day of everything except FERTILIZER (zero demand, ever).
Shops unlock D3+ (1 per 3 days, max 8). **The seed's shop RNG decides which
items pay.** Seed-1 example: 6/8 shops bought strawberry → straw drain 36/day
→ BT sold 303 straw at ~$100. Zero YARN_STOREs → BT sold exactly 59 wool
(= the 58-unit floor point — their bot stops there; we sold 110, 51 past it
at $1-10). `spy.shop_drain(town)` implements the drain model.

## 3. Production mechanics (engine-verified, several were news)
- **CARE+FEED same day banks +1 to next production**: cared sheep 4×, cows
  3×, geese 2× output.
- **FERTILIZER: 1 per animal per day, guaranteed** (~$40-100 each; fert is
  the herd's real product — animal product floors fast, fert cap is 494).
- **Ongoing crops (straw/tomato): +1 per production event, +2 only if
  watered AND fertilized that day; only 4 production events per plant**
  (then dies → replant cycle).
- **HANDS RESET DAILY** (`_end_of_day` clears hands). Crew must be re-hired
  every day. Cost is fib×1: a 12-hand day = **$376 total** (hands are cheap).
- **HIRE orders are capped at 10/day** by the order-slot limit (n_hires<10 +
  10-order queue): effective crew max = 10 hands + farmer.

## 4. Per-visit labor economics (what a worker-hour is worth)
MELON ~$100/visit (no shop dependency) > SHEEP $94 (YARN) / $22 (no YARN) >
COW $81 > STRAW $57 (with shops) > GOOSE $36 > CARROT $25 > WHEAT $16.
With fert included every animal gains ~$17/visit regardless of shops →
**fill structures; shops tune only sheep↔cow ratio and crop mix.**

## 5. Dead-end ledger (all measured, never retry)
| experiment | bench | result |
|---|---|---:|
| wheat reserve herd×10→×3 + sell-all | solo 5-seed | **−$79k** (starvation spiral) |
| wheat plant priority 40→55 | solo 5-seed | −$39.7k (seed 2: $148!) |
| 14 hands (hire window H1-H2) | solo+H2H | −$16.5k solo, −$19.5k H2H |
| collect-fert 55→68 | 3-seed / 5-seed | +$2k / **−$3.7k** (3-seed benches are noise) |
| harvest-animal 65→72 | 3-seed | −$3.5k |
| ongoing-crop water 80→64 | 3-seed | −$5.4k |
| straw harvest 68→74 | 5-seed | −$0.3k (kept: H2H racing) |
| drain-sized herd (day pacing) | 5-seed | −$5k |
| day-1 straw shop gate | 5-seed | −$5k (skips early plantings) |
| ratio-herd 3/7 (no yarn) + geese 8 | H2H | −$4.4k avg |
| crew_first / hire reorder | 5-seed | −$0.3k to −$3k |

**Meta-lesson: per-seed variance is ±$10k. 3-5 seed benches mislead; use
10+ seeds or H2H-only decisions.** (v1011 vs "current" on seeds 1-5: −$4k;
on fresh seeds 6-15: statistical tie $88,707 vs $88,629.)

## 6. THE GAP to first place (measured, not opinion)
1. **Routing engine**: our bot uses 4,501 moves vs BT's 3,625 for equal
   task counts; 477 PASSes; 35 idle tiles late-game; PICKUP/DROP overhead
   2.5× BT. Extra workers make it WORSE (congestion) — the assigner, not
   the crew, is the ceiling. A smarter assigner (batched trips: carry feed
   for 3 animals + collect fert on the same walk; drop-on-the-way; less
   shed ping-pong) is the single highest-value rewrite.
2. **Mid-game tempo**: winners hold $53.6k at D20 vs our ~$26k — direct
   consequence of (1).
3. Everything else (market math, sell timing, herd) is now at/near optimal
   for v1011's production rate.

## Ship status
- `agent/custom/` = v1011 restored (identical to built candidate earlier).
- `main.py.candidate` = 74,985 bytes, md5 ce8df9f0..., smoke-tested
  ($97,276 seed 1 / $95,384 seed 7, state resets across episodes).
- `agent/custom_v1012_experiments/` = today's full experiment tree.

---

# SESSION 63 ADDENDUM — Routing dead-ends mapped (the local optimum proven)

Work continued on the routing engine. Both surgical fixes measured, both
dead ends — and WHY is now understood:

## Drop-elimination experiments (the DROP 135 vs BT 9 gap)
| variant | solo 10-seed | H2H (BT/moon/soil avg) |
|---|---:|---:|
| v1011 baseline | $92,150* | **−$62,981** |
| nodrop-v1: forced-drop threshold 6→99 + PASS-on-empty-shed | **$94,464 (+$2.3k)** | −$70,352 (−$7.4k) |
| nodrop-v2: v1 + remove idle-drop loop | $83,344 (−$8.8k) | −$82,444 (−$19.5k) |
*seeds 1-10 blended

**Why both fail — the mid-day drop system is load-bearing twice over:**
1. **FEED supply chain**: field wheat reaches the shed only via idle-carrier
   drops; without them, wheat sits in hands all day and animals starve
   waiting for shed PICKUPs (v2's −$11k solo = starvation cycles).
2. **H2H sell race**: mid-day drops → same-day sales → selling BEFORE the
   opponent's dumps. H0-only sales lose that race by a day (v1's −$7.4k).

So DROP 135 + threshold 6 is not waste — it's the current architecture's
way of doing both jobs. The walking cost is the price, not the bug.

## 14-hands confirmation (crew size)
hires_target 14 with H1-H2 hire window: −$16.5k solo, −$19.5k H2H.
Congestion, not crew. Effective cap stays 10 hands + farmer (order-slot
limit: 10 market orders/turn).

## Where this leaves the gap
v1011 is a measured local optimum of THIS architecture (single-task
greedy assignment + micro-shed-detours). The remaining +$40-60k that
separates us from the top lives in a route-based executor: multi-stop
plans per trip (feed A→feed B→collect fert C→drop once), planned as a
route with total-walk minimization, with shed stops scheduled when the
CARGO (not an arbitrary threshold) warrants it. That is a rewrite of
executor.py + assigner.py around a Plan object (ordered stops, cargo
manifest), not a parameter change. Estimated: 1-2 focused sessions.
Everything else — market math, sell timing, herd, priorities — is at or
near optimal for our production rate.

## Ship state
`agent/custom` = v1011 (diff-verified pristine). `main.py.candidate`
= 74,985 bytes, md5 ce8df9f0fea6366e5f3dcd52ab7aff1f, smoke-tested.

## Compound AnimalServiceTask (feed+care+collect per animal, one visit)
Replaces 3-4 round trips/animal with 3-4 standing hours on the tile.
Measured seed 1: **$72,074 vs $97,176 (−$25k)**. FEED completions fell
386→223 and 1,753 urgent-feeds spawned: hard-coupling per animal
serializes service and starves the rest while units stand on CARE/COLLECT
phases. Separate per-chore tasks give the assigner the global interleave
(feed-sweep everything, then care-sweep) that keeps 15 animals fed.
**The routing win must come from batched ROUTES (multi-stop plans with
global scheduling), not per-tile coupling.**

## Session conclusion
Six routing/economy variants built and measured today; all negative or
noise. v1011 is a robust local optimum of the single-task greedy
architecture. Ship candidate unchanged (md5 ce8df9f0...). Next major step
remains the route-planner rewrite (executor + assigner around ordered
multi-stop plans with cargo manifests — 1-2 sessions, spec'd above).

---

# ROUTE CAMPAIGN — FINAL VERDICT (definitive, with trace evidence)

Built the complete route system across 6 iterations: geographic clustering,
committed multi-stop plans (pickup → feed → care → harvest → collect →
drop), tile-state self-invalidating stops, daily rebuild, bootstrap gating,
zombie-route elimination, ownership suppression. All code preserved in
agent/custom_v1012_experiments/router.py.

## The decisive trace (v6, seed 1, D7)
- 2 route walkers own 9 animals serially: ~1 stop per 4 hours,
  4/9 fed by H16, cares incomplete at H20.
- 8 free units PASS all afternoon (suppression removed their tasks).
- Bisect: routes-only $90,820 | suppression-only $95,930 (inert) |
  both $110 (catastrophe).

## Why routes lose — the arithmetic
Feeding N animals: task pool = N parallel units × 1 feed ≈ 2h total.
Routes = 2 serial walkers × N/2 feeds ≈ 15h. The pool's parallelism IS the
optimal schedule for this task graph; serial routes can't match it. The
measured move-overhead vs top bots (4,501 vs 3,625) is NOT fixable by
route planning — it lives in per-task shed detours (PICKUP/DROP), which
routes still perform (one pickup per unit per day ≈ same as the pool's
chained batch-3 pickups).

## CLOSED: the routing question
Both directions now measured to ground:
1. Route planner (6 variants) — inferior (serial vs parallel).
2. Every priority/threshold/batch/herd tweak — noise or negative.
v1011's parallel task pool with chained carry-matching is the right
architecture. Remaining upside requires production-rate gains (faster
field cycles, more wheat throughput), not labor scheduling.

---

# SESSION 64 — Wheat-throughput campaign (8 experiments, all measured)

| experiment | solo avg | verdict |
|---|---:|---|
| discard hypothesis (shed pinned by wheat hoard) | — | **disproven** — zero discards, shed never full |
| W1: 4-day live buffer + slot-guaranteed buy backstop | $38,434 | ❌ herd death |
| W2: value-ranked watering (melon 86 / straw 82) | $90,248 | ❌ −$5.7k |
| W1+W2+endgame reserve combined | $42,203 | ❌ herd death |
| F1: suppress unfedable FEED tasks | $97,508 | inert (never fires) |
| F2: unlock SE quad (25 tiles) | $87,171 | ❌ −$10.3k (reconfirmed) |
| evening-only planting window (H16+) | $93,221 | ❌ −$4.3k |

## The wheat gap, finally understood
Top bots sell ~486 wheat vs our 3 because they PRODUCE ~2x (184 plants vs
96). Not inventory policy. Our attempts to convert buffer→cash die because
the 10-15-day wheat buffer is VARIANCE INSURANCE for a field whose output
is labor-capped and intermittent (measured: wheat tiles hit 0 at D16 while
the herd kept growing — the old buffer absorbed exactly that; a 4-day
buffer cannot, so animals starve D18-21). Selling insurance at $20/unit
against $300-500 animal deaths is EV-negative, every time.

## Definitive state after ~45 measured experiments (sessions 62-64)
v1011 is the production frontier of this architecture:
- labor-saturated (every reallocation: negative),
- market/sell timing optimal (spy + H0 volley),
- priorities at a measured local optimum,
- buffer = necessary insurance,
- routing: parallel task pool beats all route plans (serial),
- more land / more crew / more plants: all negative.
Remaining upside requires a different planner, not a patch. Ship candidate
unchanged: md5 ce8df9f0fea6366e5f3dcd52ab7aff1f.

---

# SESSION 64b — THE PLANNER'S FIRST COMPONENT SHIPPED (v11.0)

## What finally worked
A value-and-deadline-aware planning layer on top of the (undefeated)
reactive pool: **market-aware work selection**. The pool always fills every
unit but can't see the market; the planner reads live market pressure and
skips work whose marginal product sells at $1:
- CARE on sheep once wool supply >= +50 over I0 (floor at 58) — the care
  bonus produces $1 wool; fert (the real product) doesn't need care.
- CARE on cows once milk >= +65 (floor 75). Geese: never skipped (egg
  price is log-shaped, never floors).
- FERTILIZE on strawberry/tomato once their markets floor — the fert unit
  is worth more sold than buried as +1 straw at $1.

Signature: **inert when markets are healthy (solo: +$237, noise), strictly
positive under shared saturation (H2H: +$657, all four opponents
improved).** First change in ~50 experiments to improve both benches.

## Standard bench (4 opps x 4 seeds x 2 seats)
| build | BT | V41 | moon | soil | avg |
|---|---:|---:|---:|---:|---:|
| v1011 | -61,295 | -55,958 | -71,704 | -55,944 | -61,225 |
| **v11.0 (PLN1)** | **-60,517** | **-55,227** | **-71,135** | **-55,395** | **-60,568** |

Solo(10): $92,391 vs $92,154 (neutral by design).
Melon retirement + straw-harvest skip (PLN2) benched WORSE than PLN1 —
not shipped.

## Ship
- main.py = main.py.candidate: 75,873 bytes, md5 043648d193981358e53d3acd05ca76b9
- smoke: seed1 $97,276 / seed7 $95,384, state resets across episodes
- snapshot: agent/custom_v110_market_planner/
- Submitted to Kaggle (4 submissions remaining today).

## Planner roadmap (next components, same additive pattern)
1. Crop rotation by market: retire dead-market crops to wheat EARLY
   (melon retire benched slightly negative as a water-skip; needs the
   DIG+replant path done properly).
2. Herd mix by live shop drain (code exists in spy.shop_drain; solo-negative
   alone, revisit INSIDE the planner where labor is freed by skips).
3. Deadline-aware watering (P1: noise-neutral; keep for free).

---

# SESSION 65 — Copy + overlay campaign (the engine gap closed)

## Ladder reality check
- v11.0 (custom + market filter): **643.5** — custom architecture ceiling
  confirmed on the real ladder despite +$657 local H2H.
- Our BT submission's real record vs the field: 46W-45L (91 games) —
  mid-pack BT-family.

## Overlay on BT (all measured, all negative)
| overlay | solo | mirror vs pure BT |
|---|---:|---:|
| H0 full volley + spy pre-sell + dead-dump | −$18k | **0/8 wins, −$21k** |
| endgame liquidation | nothing to liquidate | BT leaves shed empty |

WHY (the real economics): BT *paces* sales — as the marginal supplier,
dumping at H0 crashes your own price; spreading sales lets town drain
sustain prices. Our "front-run" insight was right for our hoarding custom
bot, wrong for BT which already paces, front-runs, liquidates, and tracks
opponent money internally. Append-only orders cannot beat its controller.

## Who beats BT (from 91 real episodes)
1. BT-family mirrors: decided by $600-900 margins (Orig_lab +$664 etc.).
2. The Napier/Khanh/CroDoc profile (non-BT): **13-15 hands, herd 16,
   fert ~284-300 (kept on fields, not sold), D10 $13k / D20 $45.9k tempo,
   finals $126-140k.** An engine we don't possess.

## Shipped
- **v11.1 = pure BT engine** (identical code to the 2191.2 submission;
  only a comment header differs). Submitted — expect ~2100-2200 band.

## Next build (the real hybrid)
Rebuild the custom bot's BUILD to the winning non-BT profile — crew 13-15,
herd 16, fertilizer kept on fields (not dumped), D20 tempo $45k+ — with
our spy/sell systems on top. Their parameters + our intelligence.

---

# SESSION 66 — The top-10 map (replay intelligence)

## Discoveries
1. **Kaggle serves ANY episode replay** (`kaggle competitions replay <id>`)
   and ANY submission's episode list — the whole ladder's behavior is
   harvestable, not just our own games.
2. **The top is a two-bot mirror war**: all 8 of #1 Crop Dusta's recent
   games are vs #2 Ryo Hasegawa, coin-flip margins. Same engine family
   (near-identical D0: BUILD_PASTURE + 4-5 HIREs + 2 COW/2 SHEEP + melon/
   wheat seeds; both open BUY WHEAT 4 first = Kaito-line signature).
   Their exact tape is a PRIVATE MUTANT (not in any pulled public notebook;
   fingerprinted: BT, V46, V48, K2900, moon, amey, multiroute, soil, v41
   all fail step-0).
3. Public notebook meta (pulled + benched locally):
   - **V46 "Adaptive Shop Guard" (public 2560.4)**: beats BT 8/8 (+$8.5k),
     beats V48 mirror, beats K2900. LIVE as our v11.2.
   - V48 "Fast Routes" (39/46 vs top-10 claim): sha-verified authentic,
     identical solo to V46 ($183,807 — same lineage), loses V46 mirror 0/8.
   - K2900 "2900+": beats V46 6/8 BUT loses to BT 0/8 (−$9.9k) — counter-
     meta specialist, too risky while BT-family is thick in the mid-band.
4. Overlays on smart engines: DEAD (proven twice — BT −$21k, V46 −$23k
   mirror; they pace sales deliberately; front-running crashes own price).

## Live state
- v11.1 (BT) = 1340.3 and v11.2 (V46) = 1315.2, both mid-convergence
  (expect V46 line ~2500 band once enough games resolve).
- 2 submissions remain today.

## Top-10 plan (ranked)
1. Let v11.2 converge; verify the band it settles in.
2. Kaito-line mutant hunt: pull remaining kaitofukami/prvsiyan/hamburger/
   boatlee kernels; fingerprint each vs the top-2 replays (we have their
   full action streams).
3. If the tape stays private: build the counter — K2900's V46-beating core
   hardened vs BT (its 0/8 loss is the blocker), or V46 + mirror-margin
   tuning from the top-2's episode corpus.

---

# SESSION 67 — Engine fully cracked (source + tapes + mutation pipeline)

## While v11.2 climbs
1. Pulled 7 more public kernels — none match the top-2's private tape.
2. V46 config sweep (8 knobs): ALL identical results to the cent — the
   config is a facade; the brain is the tape payload.
3. Ghost sparring (replaying #1/#2 recorded streams as opponents):
   invalid — ghosts collapse to no-ops once play deviates.
4. **DECODED THE ENGINE COMPLETELY**:
   - `_V44_MODULES` decompressed: 3,249 lines of readable source in
     `topbots/payload_src/` (gold_floor router, MarketMakerExpert,
     simulator, planner, policy library, terminal scripts).
   - Tapes decoded: `topbots/v46_routes_decoded.json` — 5 routes x 719
     pre-scripted full-game action dicts (default / yarn_first /
     yarn_second / bakery_capital / yarn_third), selected by visible
     shops. This IS "running tapes."
   - Found the mirror weapon: `CloneSellPreemption` — detects tape-
     following opponents via public-farm match and front-runs their
     future SELL slots. And `MarketMakerExpert` (852 lines) = the
     sell-pacing brain that beat our overlay twice.
   - **Mutation pipeline verified**: decode -> edit JSON -> re-encode ->
     splice; round-trip build plays identically to the cent
     (176,813/185,745/188,863). Saved as topbots/v46_editable.py.
5. Ladder: v11.2 at 1500.4 mid-convergence (last check).

## Next queue (highest EV first)
1. Tape mutation lab: mirror-bench tape variants (sell-step timing, buy
   quantities); transplant experiments with #1/#2 replay streams.
2. Source-level surgery now possible: wire SPY into MarketMakerExpert /
   CloneSellPreemption at the real integration point (the append-overlay
   failure is obsolete — we own the code).
3. Rebuild tapes with their own machinery (v23.simulator + planner).

---

# SESSION 68 — First custom mutation SHIPPED (v11.3)

## The tape genetics lab
- V48 vs V46 tape diff: default/yarn_second/bakery_capital IDENTICAL;
  V48 adds yarn_fast + farm_fast tapes and a rewritten yarn_third.
- True shop-regime seed map (empirical, 60 seeds): yarn_first 6 seeds,
  yarn_second 9, farm_first 4, yarn_third/bakery_cap 0 (rare), default 45.
  (Earlier benches used no-trigger seeds — that's why every swap looked
  inert. Scenario-aware benching is now mandatory.)
- Read + ported V48's route gates from its extracted router source.

## chimeras benched (vs V46-stock, trigger seeds x 2 seats)
| variant | result |
|---|---|
| chimera2 (yarn_fast as yarn_first) | +374 avg, zero losses, 12 games |
| chimera4 (yarn_fast + farm_fast + ported gates) | **+690/game avg on trigger seeds, zero net losses; BT guard 8/8 +8,662** |

## Shipped
- **v11.3 = chimera4** (114,610 bytes): V46 engine + V48's two fast tapes
  with ported gates (incl. FARMERS_MARKET exclusion from yarn_second/
  third eligibility). Smoke: seed1 $176,813 (identical to stock on default
  seeds), seed19 $169,722, seed5 $105,004; state resets across episodes.
- Submission 55801300 pending; 1 slot left today; v11.2 still converging.

## Next (top-10 push)
1. yarn_third rewrite + bakery_capital: need trigger seeds beyond 60 (scan
   61-150) — V48's yarn_third differs on 489 steps; untested.
2. Build NEW tapes with their own machinery (v23.simulator/planner) —
   generate improved route candidates instead of grafting only.
3. Wire SPY into CloneSellPreemption at source level (real integration
   point for our opponent-intel).
4. Watch v11.2 vs v11.3 convergence; keep best.

---

# SESSION 69 — Top-player reference campaign (NO submissions, lab only)

## Transplants: definitively dead
Crop Dusta's and Ryo's full 719-step tapes (from their real mirror) run
through V46's wrapper:
- solo vs PASS: CD $30-37k, Ryo $71-79k (real: ~$90k each)
- ON THEIR OWN SEED in their own matchup: CD $0 (!), Ryo $78k.
The wrapper is not a replayer: build_sparse_planner compiles tapes into
plans and terminal_market/MarketMakerExpert rewrite market actions, so a
foreign tape never executes verbatim. Tapes are only meaningful inside
their native engine. Copying the #1 requires their wrapper code, which
replays cannot yield.

## What the #1 actually does (extracted reference profile)
| metric | Crop Dusta #1 | V46 default |
|---|---|---|
| wheat bought / sold | 2,219 / 2,273 | 245 / 326 |
| fertilizer sold | 162 (rest on fields) | 400 |
| hires D0-D5 | 4/day steady | 2-3/day |
| sell hours | H2/H6/H10 morning | H17-23 evening |
| herd | 6 sheep / 9 cows | 4 / 11 |
Their economy: INPUT SUBSTITUTION — buy feed wheat cheap (log curve,
never crashes), keep fertilizer on fields (doubles watering yield), sell
own wheat at volume, sell mornings. Wheat volume IS the edge (+$45k of
wheat revenue vs ours).

## Naive CD-profile mutations of V46's tape: both negative
- M-C wheat-feed buying (BUY WHEAT 5 / 6 steps): solo $42-68k vs $176k
  stock (order-slot displacement + cash drain; catastrophic).
- M-A/B hire front-load + herd shift: -$7k avg (mild negative).
Tapes are co-optimized with their wrapper; surface edits regress. Saved
in mutants/.

## Next real lever
The wrapper's NATIVE wheat machinery: v44_gold_floor source contains an
exposure/market-maker path (lines ~590-645, 'exposure_preempt',
'wheat_market_maker' flags) that our config sweeps showed inert — the
real activation condition needs a source read (likely coupled to
clone_preempt_horizon / MarketMakerExpert config). If activated, it is
the authors' own implementation of exactly the #1's wheat strategy.

---

# SESSION 70 — Dormant wheat weapon decoded + ACTIVATED (not posted)

## Why the flags were inert
1. wheat_market_maker=True alone: still no trades — kill-switch is
   `wheat_minimum_profit = 25.0` (dataclass default; NOT in the config
   dict literal, so config sweeps never touched it). Realistic wheat
   round-trip edges are $1-5/batch -> entry mathematically impossible.
2. exposure_preempt: needs opponent >=8 animals + fert price >=80% base
   + non-clone -> rare; inert in our benches by design.

## Activation matrix (all vs stock)
| variant | solo | mirror |
|---|---|---|
| W3 uniform gates (profit 1.0, batch 60) | +922/-123/+15 | [+4993,+480,+469,-79,-8187] = net NEGATIVE |
| batch 120/200, profit 0.5 | same | worse |
| **W9 asymmetric (normal 1.0 / mirror 25)** | **gains kept** | **[+303,0,0,0,+404] zero losses** |

W9 = one-line source edit (split mirror_minimum_expected_profit onto its
own config field — clearly the intended design; the build hardcoded it
equal) + config injection. vs BT: 10/10, +$9,145 (stock: +$8,795).

## Status
- Saved: topbots/w9_wheat_maker.py (md5 in workspace), scripts/bt_guard.py
- SUBMISSION-READY. Not posted per instruction.
- Queue when posting resumes: W9 (or W9 + chimera4 grafts combined —
  both are independent strictly-not-worse upgrades; combine + rebench
  before shipping).

## Combo test (W9 + chimera4 grafts)
vs BT 10/10 but +$8,319 — the fast tapes (tuned for stock mirrors) LOSE
~$4k/game vs BT on yarn-trigger seeds (seed 19: 2961/4276 vs stock's
7830/6885). Graft/maker interaction is negative vs the field's second-
biggest family.

## SHIP DECISION (when posting resumes)
**W9 alone** (topbots/w9_wheat_maker.py, md5 642558d4...):
- strictly-not-worse vs stock in mirrors (zero negative deltas)
- +$350/game vs BT beyond stock (10/10)
- solo gains kept (+922 best seed)
chimera4 remains live as v11.3; W9 will be posted as the next submission.

---

# SESSION 71 — W9 tuned to optimum and SHIPPED as v11.4

## Knob sweep on W9 (10 variants, panel-benched)
| variant | verdict |
|---|---|
| batch 30/90/150 | equal-or-worse (90+ kills seed-5 mirror edge) |
| start 72 | +$15 solo, loses +$404 mirror edge -> rejected |
| cash 1000 / horizon 4 / feed 1.0 | inert (gates never bind) |
| mirror gate 12 | opens -448 hole on s29 -> rejected |
| hold 8 | invalid kwarg (MarketMakerConfig-only) |
**W9 base (batch60, p1.0/25) is optimal in this space.**

## Shipped
- v11.4 = W9 (91,351 bytes, md5 642558d4...): smoke seed1/7/19 =
  $177,631/$139,302/$168,968, state resets OK across 3 games.
- Ladder at submit: v11.3 = 2135.6 climbing.

## Live fleet
- v11.2 (V46 stock) - converging
- v11.3 (V46 + fast grafts) - 2135.6 climbing
- v11.4 (V46 + wheat maker asymmetric) - pending
Max-score rule: best of the three counts.

---

# SESSION 72 (pre-reset lab) — v11.5 candidate built: W9y

## Closed dead-ends this session
- yarn_third swap: NO trigger seeds exist in 1-160 (gate needs specific
  3-shop prefixes at step 216+; only false positive seed 142) — untestable.
- exposure_preempt: inert at ALL price ratios (0.80/0.60/0.45) — the gate
  never opens on our panel (latch/future-slot constraints). Closed.
- Top-2 drift check: NONE — #1's opening is 59/59 steps identical across
  seeds and days (pure deterministic tape; engine unchanged).

## yarn_first tape genetics
- V46 yarn_first vs V48 yarn_fast: common 130-step prefix, then ~128
  scattered micro-diffs (DIG vs PLANT order, seed buys). Segment splicing
  = one parent or the other (no clean hybrid); segment-level greedy
  breeding is the future tool.
- Fresh yarn seeds 61-160: 16 yarn_first, 6 yarn_second, 15 farm_first.

## v11.5 CANDIDATE: W9y = W9 + yarn_fast tape (yarn_first slot only)
| bench | result |
|---|---|
| default seeds [1,3,5] | identical to W9 (deltas match to the dollar) |
| yarn seeds [19,29,61,62,69] x2 seats | +356 avg, no net-negative seed |
| vs BT 10 games | 10/10 +9,145 (identical to W9) |
Saved: topbots/w9y_candidate.py (91,639 bytes). SUBMIT AT RESET.

## Fleet
v11.2 / v11.3 (2135.6+ climbing) / v11.4 (pending) live; v11.5 queued.

---

# SESSION 73 — farm_fast REJECTED; W9y confirmed as v11.5 (final)

## New ladder intel from user
ONLY THE LAST 2 SUBMISSIONS stay active. The fighting pair after next
post: v11.4 (W9) + v11.5. v11.2/v11.3 retire at current scores.

## farm_fast isolated graft: REJECTED
- farm seeds [5,18,26,52]: +668 avg (seed 26 +2,469 both seats) — the
  good part replicated.
- BUT seed 3 (default class) collapses: -16,437/-4,372 = **-$20.8k net**
  (W9y was +303 there), and BT seed-19 edge degrades to [2961,4276] from
  [8244,7254]. The V48 farm tape through V46's wrapper is destructive in
  contexts the farm panel doesn't cover. Do not graft farm_fast.

## W9y final validation (the v11.5 build)
| class | games | result |
|---|---|---|
| default seeds [1,3,5] | 6 | identical to W9 (net +303/+404 W9 deltas) |
| default seeds [8,9,11,12,13,14] | 12 | avg +207, zero negatives, seed 9 +1.3k both seats |
| yarn trigger [19,29,61,62,69] | 10 | +356 avg, no losing seed |
| vs BT | 10 | 10/10, +9,145 (identical to W9) |
| solo | - | = W9 (+922 best seed) |
STRICTLY-NOT-WORSE everywhere measured. topbots/w9y_candidate.py
(91,639 bytes, md5 73c7668d...).

## At reset
cp topbots/w9y_candidate.py main.py -> smoke (kaggle_environments, 3 seeds
+ state reset) -> submit "v11.5: W9 + yarn_fast graft".
Fighting pair: v11.4 (W9) + v11.5 (W9y) — max-score between them.

---

# SESSION 74 — The melon medic campaign (Yaroslav-game fix attempt)

User's idea: endgame straw tiles -> melons (straw $1, melon $212+ in that
loss). Confirmed economically correct. Six engineering iterations to
capture it:

| iteration | design | result on seed 1705979935 |
|---|---|---|
| naive swap (D17-19 wheat->melon) | tape crop swap | 157,030 vs base 160,594 (5/12 melons harvested by residual choreography) |
| medic v1/v2 (PASS+adjacent scan) | runtime patch, wrong return anchor / 1-tile range | never fired |
| medic v3 (transactions, walk-to-target) | latch units across steps | never fired (PASS slots absent at need hours) |
| medic v4 (borrow MOVE units, ripeness fix) | full service machinery | ALL 12 melons harvested but 120,795 (-36k cascade) |
| medic v5 (1 borrow, dist<=3) | minimal borrowing | identical -36k (single deviation still cascades) |
| medic v6 (cascade-free: on-tile PASS only) | zero-displacement | never fires (no unit ever PASSes on a melon tile) |

## Engine facts learned (logged for the breeding project)
- One-shot crops (WHEAT/CARROT/MELON) are PLANTED with yield_units=1 —
  young-harvest checks must threshold, not just >0.
- MELON thirst: dies after 2 unwatered days; the wheat-window watering
  D19-21 keeps swapped melons alive only briefly; they weed out D22-24.
- The tape has ZERO spare labor D17-29: PASS never co-occurs with melon
  adjacency; every borrowed MOVE cascades ~3x the melon gain.
- Melon ceiling on freed straw tiles: 12 tiles x ~4 units x $212 =
  ~$10.5k/game — real, but capturable only via offline no-op-slot
  analysis (the greedy patcher project), not runtime.

## Ship state
- v11.5 candidate remains W9yt3 (untouched by this line of work).
- All medic variants saved in topbots/ (wm_medic*).

---

# SESSION 75 — Polish campaign (post-melon)

## Tested and closed this session
| idea | result |
|---|---|
| dedicated melon worker on empty tiles | DEAD: zero empty near-shed tiles D18-26; hands 92-100% utilized (0-8% no-op) — no real estate, no spare labor |
| EGG market-maker (2nd maker, log curve) | solo identical (never fires — egg demand only ~12/day); mirror = pure variance ±$8.5k seat-swaps, avg exactly 0.0. REJECTED |
| early liquidation L715 (terminal dump at 715-718 vs 718 only) | solo -16 (noise); mirror 8/10, +$22-43 clean both-seat edges on 3/5 seeds, avg +50. ACCEPTED |

## v11.5 FINAL = W9ytL (topbots/v115_FINAL_w9ytL.py)
= W9yt3 + L715 early liquidation:
- wheat maker (asymmetric gates: 1.0/25, batch 60)
- yarn_fast graft
- exact-tie micro-dose breaker
- pre-dump liquidation (715-718)
Validation stack: 44+ games strictly-not-worse vs stock & BT 10/10 +9,145;
L715 adds clean mirror edges. Ready to post on user's go.

## Fleet
- v11.4 (W9) live climbing; v11.5 ready (last-2 rule: v11.4 + v11.5 fight).

---

# SESSION 76 — THE USER'S "SELL BEFORE THEM" SYSTEM DELIVERS: v11.6

The engine's own dormant CloneSellPreemption (fingerprint-matches clone
opponents, reads THEIR tape's future SELL slots, moves our sells ahead)
was shipping with batch=10. Knob sweep in mirror matchups:

| knob setting | mirror avg (5 seeds) |
|---|---:|
| baseline batch 10 | +273 |
| **batch 25** | **+1,241 (all five seeds positive)** |
| horizon 5 | −5,426 (too aggressive) |
| active 80 | −3,902 (too early) |
| all four | −10,872 |

## v11.6 = v11.5 + clone_maximum_batch 25
- solo: identical to the cent (preemption only fires vs clones) ✓
- mirror vs stock (8 seeds): [+1806,+1737,+1004,+774,+882,+22,+374,+1165]
  **avg +970, zero negatives** ✓
- vs BT (5 seeds x2 seats): avg +18,327 — doubled the v11.5 edge (+9,145) ✓
  (BT is tape-family adjacent -> detection partially fires)
This is the biggest single-knob win since the wheat maker. The ladder's
top is family-vs-family mirrors; preemption is built exactly for them.

---

# SESSION 77 — v11.6 SHIPPED + full field validation

## Shipped: 55806809 (v11.6)
Fighting pair now: v11.6 + v11.4 (last-2 rule).

## Round-2 knob sweep: ALL SATURATED
batch 40/60 = +1,234 (vs 25's +1,241 — queue maxes ~1-2k); phase_batch,
detect_start, terminal_rule: flat/negative. v11.6 = config optimum.

## v11.6 vs FULL LOCAL FIELD (8 games each)
| opponent | record | avg delta |
|---|---|---:|
| BT | 8-0 | +10,452 |
| moon | 8-0 | +9,137 |
| amey | 8-0 | +9,137 |
| multiroute | 8-0 | +10,896 |
| v41 | 5-3 | +3,946 |
| soil | 2-6 | +1,076 |
soil remains the hard matchup (its fert-heavy build) but still net positive.
39-8 aggregate vs the field.

## Ladder at ship
v11.4 = 1,865.3 climbing; v11.6 = 600 start (10 games in, converging).
Both active. v11.6 carries: wheat maker, yarn graft, tie micro-dose,
early liquidation, clone preemption batch 25.

---

# SESSION 78 — Soil autopsy + v11.6 early ladder form (no posts per user)

## Soil matchup autopsy (the one losing H2H, 2-6)
Money-curve: we LEAD every game through D13-20. The loss is a single
structural event: soil's SECOND MELON WAVE.
- D10 wave: us 30 @ $226-272 (we win the queue), them 81 @ $232-250
- D20 wave: THEM 129 melons @ $140-224 (~$22k week). US: ZERO — our tape
  has no second wave (only 4 D11 tiles landing D21-24 into their crash
  @ $81-101).
Root cause = route allocation, worth +$15-20k/game. NOT market timing.

## Opportunity scan for wave-2 (breeding rig prerequisite)
Plant window D6-12: hands touch empty tiles 64 times — 34 already
PLANTING, 1 PASS total. The tape fills everything it touches. A second
melon wave requires GENERATING new choreography (re-timed water+harvest),
not patching. This is the tape-breeding rig's first target, spec'd with
exact numbers.

## v11.6 first ladder games
- vs fecrescencio22: WIN +$137,940
- vs Nikunj Pahwa:   WIN +$57,538
2-0 start, margins enormous.

## Status
No posts (user hold). v11.6 + v11.4 active on ladder. Breeding rig =
the remaining big rock: v23.simulator (extracted, 190 lines) + mutation
loop + opportunity scanner (built this session).

---

# SESSION 79 — Full replay audit (143 games) -> THE MIRROR GATE FIX (v11.7)

## Complete ladder record harvested
113W-22L-8T across v11.6/v11.4/v11.3. Loss taxonomy:
- micro-losses <=$1k: 7 (production coin-flips; market timing already maxed)
- close losses $1-8k: 13
- big losses: 2 (lucaskna -19k, Shuichi -13k)
- ties: 8 (7 on v11.3 = no dose; 1 on v11.4 = predates dose; NOT a bug)

## THE FINDING: our big losses are to OUR OWN FAMILY with BIGGER WHEAT MAKERS
lucaskna (+19k): identical 4s+11c herd, wheat machine 2,333 sold.
Yizuki top-10 (+7.7k): same family, similar volumes.
Our mirror gate 25.0 DISARMS our maker vs clones — tuned in session 70
against maker-less stock, where it prevented -8187. But it costs us the
wheat-trade war vs maker-equipped clones (the actual top of the ladder).

## THE FIX: the gate is now REDUNDANT — L715 absorbed the catastrophe
Gate matrix (10 games each cell):
| gate | vs stock | vs maker-clone |
|---:|---:|---:|
| 25 | +620 | +280 |
| 5 | +842 | +572 |
| 1 | +898 | +650 |
gate 1.0 DOMINATES everywhere. The old -8187 catastrophe (seed 5, vs
stock) now nets +774 at gate 1.0 — the early-liquidation system fixed
the failure mode the gate was protecting against. Gate has been costing
~$300-400/game vs every opponent class.

## v11.7 = v11.6 + mirror gate 1.0 (md5 bb62548d...)
- solo: identical to the cent (gate is H2H-only) ✓
- vs BT: 10-0, +9,164 ✓
- mirror vs stock: 8-2, +898 (vs v11.6's +620) ✓
- vs maker-clone: 8-2, +650 (vs +280) ✓ — DIRECT COUNTER to the
  lucaskna/Yizuki loss class
READY. Not posted (user hold).

---

# SESSION 79b — v11.7 SHIPPED

Smoke: seed1=$177,616 seed7=$139,282 seed19=$170,261, state resets OK.
Fighting pair now: v11.7 + v11.6 (last-2 rule).
3 submissions remaining today.

v11.7 = the full stack (wheat maker, yarn graft, tie dose, early
liquidation, clone preemption batch 25) + mirror gate 1.0 = full maker
aggression against every opponent class.

---

# SESSION 80 — THE ESCAPE BUG CONFIRMED + v11.8b (feed rescue)

## User was right: animals ARE escaping (my first audit was blind)
Tile-level audit (totals masked it — escapes coincided with new placements):
- v11.7 full set: 6 escapes, ALL 6 LOSSES, identical signature:
  COW@(2,1) placed D4 -> unfed D5+D6 -> escapes D7. ~8% of games.
- v11.6: 1 more (I NEED A TEAM HIT ME UP).
- Root cause: tape's D5-D6 feed schedule doesn't cover the newly placed
  cow when hire timing shifts on the live engine (1.32.7 — pricing curves
  changed: CARROT/TOMATO/EGG below-supply now hinge-shaped, shifting
  early revenue/cash/hire timing). Never reproduces locally vs stock.

## Fix: v11.8b = v11.7 + death-window feed rescue (weed-repair pattern)
- Fires ONLY at hour >= 20, streak >= 1, unfed (the tape legitimately
  feeds late; v11.8 eager version cost -85k solo — rejected).
- Dispatches nearest unit (walk <= 3) to FEED. Bounded transaction.
- Validation: solo [+1667, -97, -48] net positive; mirror 8-2 +717
  (v11.7: +898, noise); BT 10-0 +9,123 (v11.7: +9,164).
- Insures ~8% of games currently worth ~-$5-13k each.

## User's 16th-animal question — data says no
The only 2 games in our history with 16 animals were BOTH losses
(Anaconda -183, Goldian -1,706). Feed schedule at capacity is exactly
why the (2,1) cow starved; a 16th mouth raises escape risk, not revenue.

## Ladder: v11.7 = 1,990.0 and climbing (9h in). v11.8b READY, holding
for user's post command.

---

# SESSION 81 — The 1990 stall: diagnosed + v11.8b shipped

## Why stuck at 1990 (9h in)
1. Game scheduling slowed to a trickle: v11.7 games at 11:35, 11:31,
   10:07, 09:03, 08:03 (~1/game/hr vs 4-min cadence when fresh). Rating
   can't converge without volume.
2. Notebook-author reality check (current ratings, not titles):
   - Reyhan Ksatria (ShopGuard "2560" notebook): 436 NOW — stale peak
   - Salem Ali ("2900+"): 1752 — below us, dead lead
   - Kaito Fukami (v48, our engine's weaker public sibling): #190, 2283
   => Our stack has PROVEN headroom to 2283+ (we bench above v48's line).
3. Only 438 teams between us (1990, #478) and 2600.

## Action: v11.8b SHIPPED (2 subs remaining today)
= v11.7 + death-window feed rescue. Fixes the (2,1) D7 escape class
(6/72 games, all losses). Fresh submission = fresh scheduling queue.
Active pair: v11.7 (1990 floor) + v11.8b (should converge higher).
Smoke: seed1 $179,283 / seed19 $169,050, resets OK. md5 0f6e9b67...
