# Kaggriculture Meta Study — 2026-08-08 (from live top replays)

Replays pulled with our Kaggle API token:
- 90615567: THUNDER $127,661 vs **Seb (allegedly) $139,143**
- 90697169: venks $141,686 vs **sleepyai.org $141,870** (highest observed)

Leaderboard today: "Seb (allegedly)" #1 (3213 rating). Our best live bot: v6.3 @ 617.8.

## The two proven $130k+ builds

### Build A — "Net Wheat Seller" (THUNDER / venks / sleepyai — identical code)
- 3 quadrants (NE d7, SW d11; never SE), 14 animals (8 cow / 6 sheep)
- Day 0 h1: HIRE×5, BUY_ANIMAL COW 2 + SHEEP 2, BUY_SEED WHEAT 7 + MELON 12, BUY_PRODUCT WHEAT 5, then +1 wheat h3, h5
- Ramp: +1 cow d3, d5, d8, d9; +2 sheep d7; +2 sheep d11
- Wheat engine: 108-110 wheat seed bought over the game, sells 274-285 wheat (NET SELLER)
- Big batch wheat dump day 5 (25 units), day 9-10, day 25-29 (86-95 on final day)
- Fertilizer sold daily: 4/day early → 14/day at 14 animals (210 total). Never holds.
- Melon: 12 planted d0 → 60 units sold d10; 2nd wave sold d20-22
- Strawberry: waves sold d17-29, batches of 14-57/day
- Milk sold every 1-3 days in batches of 6-24; wool batches 4-32
- Hires: 259-260 total (5-14/day, 9-10 on day 29)
- Endgame: d29 sell-all incl. 86+ wheat; weeds_end 17-20 (they stop farming late)

### Build B — "Seb" (4-quad cow-heavy)
- 4 quadrants: NE d4, SW d6, SE d10. 20 animals (13 cow / 7 sheep). 303 hires (12/day steady)
- Day 0 h1: BUY_SEED MELON 3 + WHEAT 12, BUY_ANIMAL COW 2 (h1), SHEEP 2 (h2); wheat bought 1-2 units every 2 hours
- Buys wheat for feed (~8-15/day late), sells only 76 wheat total
- Fertilizer: sells 298 daily batches of 4-25. Milk 298, wool 150
- Cows bought through day 13; sheep through day 11
- Ends with 45 weeds (abandons crops late for pure animal economy)

## Economics decoded (why CARE is the engine)
- Fed+CARED animals bank yield: cow = 2 milk/2d = 1/d, sheep = 3 wool/3d = 1/d steady state.
  CARE doubles output for one action/day. All top bots do it.
- 14 animals ≈ 200 milk + 150 wool + ~210-300 fertilizer + 4-6 wheat/day feed demand.
- Fertilizer = 1/animal/day FREE. Sold daily it is $15-25k per match.
- Fertilizer ON MELONS: +2 melons (≈$500 base value) for a $100 input — best use after daily sells.
- Wheat: fertilizing wheat is net-NEGATIVE (+2 wheat ≈ $50 < $100 fert sale). Never.
- Premium goods (strawberry/melon/milk/wool) crash to $1 on glut (above_target > 1).
  Town shops drain them back up. Pace sales with observed price; never hold past day 27.

## Our failure history (from STATUS.md / OUR_MATCHES_ANALYSIS.md)
1. v6.1: no DIG weeds, too few crops, feed-wheat sell bug → 4-12 live record.
2. v6.3: fixes above; robust but low crop fill (7-11 crops vs winners' 40-55).
3. v6.5: lane routing + feed-help; mean $94k local, but crop-fill after expansion still weak.
4. v7.x/Quant: market-adaptive buys, retry-land, sells-last (good ideas), but still
   hand-coordinated roles; converging jobs; no fertilizer-on-crops; no sale pacing.
5. v6.2/v6.6 Seb-style attempts: animals died at 16-20 scale; strict routes broke.

## Requirements for v8 (Field Marshal)
- 100k+ per match; every plantable plot filled daily; ZERO animal escapes; ZERO weed-outs;
  every fertilizer unit collected and sold (or converted on melons); full cash-out by turn 720.
- Central job-board with utility scoring (no converging), market-aware sale pacing,
  opponent-aware supply forecasting, fertilizer-on-melon, wheat-ring feed engine.

---

## Round 3 — Ryan Shan $153,185 decode (episode 91116281, pulled 2026-08-08)

Highest single score seen. Same THUNDER/Chloe/sleepyai lineage, executed with
a bigger strawberry engine:

- Day 0: HIRE 5, COW 2 + SHEEP 2, WHEAT seed 7 + MELON seed 12 (the meta opening)
- **Day 7: BUY_LAND (NE) + COW 2 + STRAWBERRY seed 19 in one hour-1 batch**
- Day 8-9: +1 cow each
- Day 10: COW 2 + SHEEP 2 + MELON seed 12 (wave 2)
- **Day 11: BUY_LAND (SW) + SHEEP 2 + STRAWBERRY seed 23**
- Days 12-27: small wheat-seed top-ups almost every day at HOUR 3 (avoids the
  hour-1 order cap), totaling ~109 wheat seed
- Hires: 10-14/day late (11 on day 29); 260 total
- Crops: hits **61 crops (100% of plantable tiles)** day 12-23, holds 54-60
  until day 27, then clean cash-out (crops 29→4, everything sold)
- Sold: STRAWBERRY **320**, WHEAT 305 (net wheat seller +39), MILK 214,
  FERTILIZER 212, WOOL 148, MELON 144

### Lessons adopted in v8.2
1. Strawberry waves bought in big batches at land unlocks (ticks 18-28 all fire);
   our cash curve buys them days 8-13 instead of 7/11. Result: +$1.9k/match in
   self-play, weed-outs -40%.
2. Wheat ring widened to shed-distance 3 mid-season → net wheat buying down in
   contested play (we bought 193 wheat live vs v8.0; the goal is net-seller).
3. The $150k builds hold 55-61 crops ALL season. Our gap is planting/watering
   throughput: lane-based crop workers are the remaining upgrade path.

### Live results so far (submission 55361265, v8.0 Field Marshal)
- 91131124: Nosiru $47,097 vs Jacob Joy $15,391 — WIN
- 91134600: Nosiru $51,868 vs Ash0666 $45,164 — WIN
- Rating: 617.8 (v6.3) → 707.1 (v8.0)

---

## Session 2026-08-08 (evening) — experiment log

Everything measured in self-play (contested mirror = ladder-like) and vs starter.
Champion stays **v8.2** (self-play $60.2k, starter ~$96k, 0 escapes).

| Experiment | Self-play | Verdict |
|---|---|---|
| SW/NE land gate (buy only when quads ~full) | $50.5k | REVERT — NW/NE never reach the fill threshold, land never bought, −$2k+ land lost forever |
| Fertilizer sell pacing (hold when price <55) | $54.3k | REVERT — early fertilizer cash funds the day 2-8 ramp; holding stalls it |
| Strawberry fertilize w/ reserve-6 | $55.4k | REVERT — same float problem |
| Strawberry fertilize surplus-gated | $55.4k | REVERT — no gain; revisit once crop count >40 |
| Lane-based crop workers (serpentine, strict) | $59.1k, min +$7.5k | REVERT — robust but peak crops fell 28→26; starter −$6k |
| Lane workers (soft, no penalty) | starter $88.4k | REVERT — worse still |

### Key learnings
1. **The early economy floats on fertilizer sales.** Any fertilizer hoarding
   before day ~15 costs more than the crop boost returns at current scale.
2. **Land gates are wrong when fill is labor-bound** — the fill must come from
   labor changes, then land naturally gets used.
3. **The 30-crop ceiling is watering LABOR, not routing.** Lanes change how
   workers walk but not how many crops 13 units can keep alive. Breaking past
   ~30 needs a watering-strategy change (e.g. deliberate alternate-day watering
   for hardy crops, or more planting when wheat-ring food is secure).
4. Seb replay price check: milk holds $200+ ALL game; strawberries crash day 25
   ($222 → $59) so sell waves BEFORE day 24; fertilizer decays $94 → $2.
5. watch_match.py now renders downloaded Kaggle replays visually
   (data/watch/match.html) and opens the browser.

### Next research candidates (untested)
- Alternate-day watering doctrine for wheat (hardy, one-time) to free labor for
  premium crops; water only cu>=1 wheat unless surplus labor.
- Denser early planting: day 0-2 the meta has 17-19 crops; we hit ~12-15.
- Melon wave 3 in SW once SW labor is proven.

---

## Session 2026-08-09 — the coverage & market-brain breakthrough

### Diagnosis: 57% of all turns are WALKING
Instrumented a mid-game day: of 296 unit-turns, 170-182 are movement, only
~100 are work actions. Workers chase the single nearest job and criss-cross
the farm. This (not seeds — seed bank never hits zero) is why crops cap at
~28 despite 55+ being labor-feasible on paper.

### The winning combination (v8.3 "Field Marshal II")
Measured over 6 seeds vs starter + 3 seeds self-play:
1. **Water doctrine for ongoing crops** — strawberries/tomatoes get NO yield
   from daily watering (rules), so water them survival-only (tier 5 when cu=0).
   Frees real labor.
2. **Strong fill boost** — plant jobs bumped 3 tiers when crops<26, 2 tiers
   when crops<36 (through day 25).
3. **Market brain** — sells now read (a) market inventory vs I0 (sell into
   scarcity), (b) 24-turn price momentum (get ahead of crashes), (c) the
   opponent's build every turn (animal-heavy opp → dump milk/wool faster;
   crop-heavy opp → dump produce faster).
4. Crisis gate — planting throttles to zero if urgent watering piles up.

Results: self-play **$69,364** (was $60,246), peak crops **34.5** (was 28.5),
0 escapes. Weed-outs ~17/match (each ~$50 of seed; net +$10k/match — top bots
shed late crops too: Ryan Shan ended with 19 weeds).

### Market-brain note
In mirror self-play the brain is ~neutral (opponent is identical), but live
opponents vary wildly (Jacob Joy crop-only, Ash0666 wheat-churn 3000 units,
cow-heavy Seb-style). The brain is built for THOSE matches. Watch the live
episodes to confirm it's dumping ahead of opponent crashes.

### Still open
- True lane-sweep crop workers (v5.8z5f-style routes merged into the job
  board) is the path from 34 to 55+ crops. The 57% walking overhead is the
  lever. Done carefully — animals/survival passes must stay untouched.

---

## Session 2026-08-09 (late) — v9.0/v9.1 increments

1. **Seed demand prediction** (user catch: ~30 seeds dead at turn 720):
   - scan_farm now counts `soon_empty` (one-time crops ~1 day from harvest)
   - seed buys gated by demand = empty_tiles + soon_empty; buy windows close
     ~2 days before each crop stops being plantable (wheat d19, straw d11,
     melon d12, tomato d9)
   - leftovers 34 → ~21/match
2. **Tender count measured**: 4 tenders caused duty-overlap ESCAPES in
   self-play; 3 tenders = same income with 0 escapes; 2 tenders loses ~$9k
   contested. Cap set to 3 (frees the 4th hand for planting).
3. **Movement audit**: workers walk 58-64% of turns, tenders 47-51%.
   Crop-worker lane sweeping (route-following, v5.8z5f style) remains THE
   lever for 55+ crop coverage. Animal redistribution alone can't fix it —
   tender walking is dominated by shed trips (wheat pickup / produce drop).
4. **Versioning**: submit/ tarball name now derived from agent VERSION
   exactly (HI_AgriBot_v9.1_FieldMarshalII.tar.gz); old bundles auto-removed.

---

## Session 2026-08-09 (coverage push) — the decisive coverage experiments

Pulled 8 live v8.3 replays (submission 55361265, rating 812.5, 4W-4L in the
sample). **Every loss was a coverage loss**: winners held 40-58 crops while we
held 27-30. LitvinKA (58 crops, beat us $108k/$75k): WATER=58/day, move 47%,
hire 5/day early then 12, burst-fill 30->57 in 2 days.

### Experiments (all head-to-head, several seeds)
| Build | Peak crops | Result vs v9.1 |
|---|---|---|
| v9.1 job board | 31-33 | champion |
| serpentine lane sweep | 27 | lost 0-4 (rigid sweep starved) |
| lanes + priority harvest | 37-41 | lost 0-4, self-play $58k vs $69-76k |
| job board + 13 workers + freer planting | 37-38 | lost 0-4 |

### THE key insight
**More crops is NOT free.** Forcing 37-41 crops made the bot LOSE every
head-to-head, because our watering/movement efficiency (58% walking) can't
sustain them — extra crops weed out and thin the labor. Our profitable crop
ceiling is ~33 at current efficiency. The live winners hold 55+ because they
ALSO have ~47% movement + tight watering. Coverage only pays once movement
efficiency is there.

### Therefore
- **Ship v9.1 (flexible job board)** — wins every coverage-variant duel, proven
  live (812 rating). Escapes 0, peak 33, leftover seeds 21, mean $96k.
- The path to 55+ crops is **movement efficiency first** (tight watering routes,
  clustered planting, less shed back-tracking), THEN coverage. Rigid lane
  sweeping alone is worse than the adaptive job board.
- Tender cap stays 3 (4 caused duty-overlap escapes, 2 starved animals).

---

## Session 2026-08-10 — movement-efficiency audit (episode 91157559 + 7 experiments)

Lost to Andrew Markley $36k/$67k in the episode the user flagged. Full audit:

### Walk decomposition (our side, 720 turns)
- 57% of turns are movement; 4282 walk tiles
- 83% of walking is walk-TO-work (1483 runs, avg 2.4 tiles), 14% shed runs,
  only 2% aborted (job stolen mid-walk) — churn is NOT the problem
- Workers NEVER idle (PASS=0): every walk is "real" work demand

### Andrew's real advantage (decoded from the same replay)
- WAGES: he pays $2,062 total, we pay $6,938 — flat 8 hires/day vs our ramp
  to 12 (fib 9th-12th hire costs $34-144 EACH per day)
- WATER: 597 actions vs our 883 despite 52 crops vs our 34 (~4 waterings per
  crop vs our ~7)
- Opening: COW×2 only day 0 (no sheep!) → $1000 cash buffer → sustains hires;
  sheep bought d10-18 off fert income; land d8/d10/d11 (3 expansions incl SE)
- His economy is ANIMAL-centric: crops are low-maintenance filler

### Experiments run (all measured, file at v9.1)
| variant | result |
|---|---|
| alternate-day watering (skip ongoing cu=0) | peak 36-40, move 56%, lost duel 0-4 |
| lean crew (9 hands) | $76k — worse |
| lean + alt-water combo | $86k + escapes — worse |
| 8-hire opening rebuild | COLLAPSE: day-1 cash $3, 77 escapes (engine fires all hands nightly; re-hire needs morning cash) |
| anti-herding job score | no movement change |
| Andrew-model replica (10 hands, SE land, delayed sheep) | move 49%! but $18k + 33 escapes (labor starvation) |

### Conclusions
1. v9.1 is a measured local optimum: every structural change loses head-to-head
   or collapses. Ships as-is (proven live: 812 rating).
2. Movement floor for a fully-loaded crop+animal economy ≈ 55-57%. The 49%
   proof exists but needs Andrew's whole economy (flat 8-9 hires, delayed
   sheep, 3 lands, filler crops) rebuilt as ONE coherent build — piecemeal
   porting breaks the cash/feeding balance every time.
3. <40% movement likely requires dropping crop-yield watering (duel-negative,
   live-uncertain); 20% is physically unreachable with full labor utilization.
4. ENGINE FACT (learned the hard way): all hands are fired nightly — daily
   re-hiring is mandatory; any opening change must leave day-1 morning cash.

---

## Session 2026-08-10 (cont.) — TOP-LEADERBOARD decode (ep 91184077: #2 HealthStone beat #1 Seb)

Leaderboard: Seb 3213.6, HealthStone 3190.1, Sebastian Mateus 3149.7. We ~812.

### HealthStone (winner) full decode — the real top-meta
- **peak 59 crops, move 49%** (avg walk 1.95 tiles/run), $58k vs Seb $43k
- **PLANTED 180 crops** (WHEAT 130, STRAWBERRY 33, MELON 17) vs our 123
- WATER 847 (≈4.7/crop — he alternate-days strawberries, staggered wheat waves)
- **wages $7,845 — MORE than us**; hiring [3,0,3,3,3,3,4,7,9,9,9,10,10,10,10,10,14,14,13,14,12,...]
- day0 opening: SHEEP x4 + COW x1 (animals-first), only 3 hires; land d6(NE)/d10(SW)
- crew peaks 15 units d16-19; 14 animals (cow-heavy); PASS=791 (tolerates idle)
- CARE only 219 (we do 310) — spends fewer actions on animals, more on crops

### Port attempts ALL lost to v9.1 head-to-head (0-4 each):
full HealthStone replica (escapes/low plant), Andrew model, hybrid (our early +
his surge+alternate-water). Peak crops hit 38-43 but income DROPS — our execution
can't sustainably support >33 crops yet.

### Pathfinding verdict (user asked about A*/Theta*/Dijkstra)
NOT the lever. The board has no movement obstacles (locked tiles passable,
workers walk over crops/pastures), so Manhattan-greedy is already the optimal
path length. Our 2.4 tiles/run vs HealthStone's 1.95 is a JOB-DENSITY/COUNT
difference, not sub-optimal routing. Better pathfinding saves ~0%.

### Real gap to top
Execution quality, not any single number: they plant 180 & keep 59 alive because
their plant-throughput + watering-reliability + assignment make extra crops
PROFITABLE. Until our core sustains >33 crops profitably, copying their
economy/coverage loses. Next frontier: raise the profitable-crop ceiling.

---

## v10.0 "Field Marshal III" — THE VALUE ENGINE (what the user asked for)

User directive: stop porting numbers; build an adaptive agent that reads the
game and chooses by value. Built and shipped.

### Architecture
Every economic job now carries a gold-expectancy VALUE computed from live state:
- _water_value: one-time crops = price x yield-gain; ongoing = future-tick value
  x risk (0.9 at cu=1, 0.12 routine) — alternate-day watering EMERGES from the
  math instead of being copied
- _care_value: CARE only exists when it doubles a product landing within 1 day
  (cut wasted CARE 310 -> 260)
- _plant_value / harvest values: lifetime gross minus seed cost, live prices
- _water jobs below a worker-turn's opportunity cost (12g) aren't even queued
- Survival reordered: FEED (value 1500, tier 0/1) beats slack watering; ongoing
  cu=1 watering is tier 2 (has a day of slack) — fixed day-28 feed squeeze
- Hiring is VALUE-DRIVEN: hire while backlog_value/hands x 9 > fib cost x 1.15,
  with an early floor. No day schedule.

### Results (6 seeds starter): $92.4k, 0 escapes, peak 38-39 crops (v9.1: $96k,
peak 33). Self-play $67.8k ~ competitive. Mirror duels still favor v9.1 — that
bias is symmetric price-crash, and LIVE losses were all coverage losses, so the
coverage build is the live bet. Shipped as
submit/HI_AgriBot_v10.0_FieldMarshalIII_ValueBrain.tar.gz

### Next tuning targets
1. weed-outs ~20/match (v9.1 ~17) — recover the $3.6k starter gap
2. value-based land buys (SE when marginal tile value > $4k)
3. market brain sell-timing already live; watch v10 live replays vs diverse bots

---

## Session (exploits + attack mode) — v10.1 shipped

### Exploits found & shipped
1. **Day-29 stop-feed/stop-water** (engine: escapes/weed-outs only process in
   end-of-day refresh, which NEVER runs after turn 720; final-night production
   uncollectable): +$600/match, 0 escapes. Reserve sold to 0 days 28-29.
2. **Town shop support**: shops consume products every 4 turns propping prices.
   paced() now raises sell_at +0.10 per shop consuming that product (hold, don't
   dump into rising demand): **+$1.5k/match** (starter x3: $97.8k vs $96.3k).
3. **Detailed opp reading**: cows/sheep/strawberry/melon counts from public farm.

### Attack mode (built, armed, situational)
- Dumps a product when opp exposure >= 2x ours AND >= 8 units of it (MILK/WOOL/
  STRAWBERRY d12-24/MELON d15-24).
- Tested vs STRONG cow-heavy opp (our own bot with 14 cows): dump is ~neutral —
  because we run ~10 cows ourselves, dumping milk hurts us too. Attack only pays
  with real exposure asymmetry (i.e., when OUR build dodges their market first).
- Adaptive build dodge (pivot targets when opp lopsided): flipped 1 of 4 matches,
  net neutral — mid-game pivot costs offset gains. Shelved; revisit with day-0/1
  reading once opponent purchases are visible earlier.
- Baseline vs cow-heavy: 1-3, -$1.1k margin. The gap is small; execution speed
  (coverage) remains the dominant lever against specialists too.

### Next exploit candidate
Town CENTER tick timing (consumes every 12 turns, 2x after d10, 4x after d20):
sell right AFTER ticks (inventory removed -> price up), hold before. Also:
opp money is public — gate our land/animal timing on their cash.

---

## FULL SUBMISSION REVIEW (user request) + v10.3 PathfinderPrime

### Live ladder of our own submissions (2026-08-09)
| sub | build | rating | matches | live verdict |
|---|---|---|---|---|
| v5.8z5f | lane routes | 520 | - | historical |
| v6.0-6.3 | meta tests | 462-609 | - | research |
| Quant v8.0 | crude quant | 591 | - | rejected by user |
| v8.3 | Field Marshal | 771-789 | 32 | solid base |
| v9.1 | +seed demand/tenders | 752 | 23 | slightly regressed live |
| **v9.5 Pathfinder** | strict sticky + full water | **835** | 22 | BEST live |
| v10.0 ValueBrain | value gates | 779 | 12 | regressed vs Pathfinder |

### What v10.0 was doing WRONG (found via live replay audit)
- Value-engine watering gates (skip wv<12, alternate-day ongoing) cut live
  coverage: v10.0 peaked 34 crops avg live vs Pathfinder's 50
- Theory said routine ongoing-watering is low value; reality: tier-2 window
  is fragile under load, crops miss it and weed out. Pathfinder's tier-5
  idle-time watering was FREE (workers had PASS turns anyway) and safe.
- v10.0 had one 70%-movement loss; Pathfinder steady 44-45% in its wins.

### Pathfinder bugs we fixed in v10.3
- Duplicate paced() sell block: MILK+WOOL orders issued TWICE per turn,
  eating the 10-order cap -> later sells (wheat) silently dropped. Removed.
- price_at()/batch_revenue() dead code (kept, harmless).

### v10.3 PathfinderPrime = Pathfinder core + proven upgrades
Endgame exploit (day-28/29 feed/water stop, reserve dump), town-demand
support, detailed opp reads, armed attack mode, dup-bug fix.
LOCAL RECORDS: starter x6 $101,264 mean (first $100k+), peak 43.8 crops,
self-play $74k, 0 escapes. Shipped.

---

## Session "more" — coverage push failed, strawberry fert WON

### Coverage push (all measured, all REJECTED)
| variant | peak | weed-outs | income |
|---|---|---|---|
| v10.3 champion | 43.8 | 151 | **$101,264** |
| +crew 14-15 + NE d6/SW d10 | 58.2 | 242 | $88,953 |
| +strawberry seed waves | 57.5 | 256 | $85,291 |
| +water triage by value | 56.5 | 234 | $83,236 |
| +16 crew d14-24 | 56.5 | 232 | $82,462 |
Reached 58-62 crops (HealthStone zone!) but watering never held: weeds
doubled, income -$12-18k. 16 crew proved LABOR is NOT the bottleneck.
Reverted everything to v10.3.

### WINNER: JIT strawberry fertilizing (v10.4) — NEW RECORD $102,916
- FERTILIZE a strawberry when its 3-day window covers 2 ticks (age 10-13)
- Gain ≈ 2 ticks x 3.5 units x ~$120 = ~$800 per fert
- HOLDING fert for it killed the early ramp (-$4.5k). The fix: sell all fert
  as usual, BUY just-in-time d15-23 when fert price has crashed (fp<=160).
- 21 fertilize actions executed in one match, +$1.7k starter, self-play
  $72.2k (mirror-only dip — nobody mirrors a fert program live).
Shipped: HI_AgriBot_v10.4_PathfinderPrime.tar.gz

### Still queued for the top push
1. Town-center tick timing (sell after consumption bumps)
2. SE quadrant when flush (nobody at top did it; Andrew did, 4-quadrant)
3. Live-verify strawfert vs diverse opponents (fert economics differ live)

---

## Session (user's endgame-push ideas, validated vs HealthStone-vs-Seb replay 91184077)

### Confirmed from the #1-vs-#2 replay
- HealthStone keeps all 14 animals within 5 tiles of the barn (9 in NW)
- Seb runs SE quadrant: 9 strawberries + 3 melons there
- Prices: MELON $236 d16 -> $84 d20 -> $7 d25 (dump early!); STRAW $205->161,
  crashed d25 ($47) when both dumped, recovered $93 d29; TOMATO $71->95 rising
  ALL month; MILK crashed ($74->$17, both players animal-heavy)

### Implemented (v10.5): MEAN $101,226 (neutral vs v10.4 $102,916, live-positioned)
- Melon hard-dump day >= 16; PLANT_UNTIL melon 17 -> 13 (no more d26 melons
  into a $7 market)
- Strawberry waves extended to day 16, target 44 (funded by melon money)
- Late tomato wave d12-17 (the stable riser)
- Strawfert program (v10.4) carries the endgame ticks

### REJECTED with data
- SE quadrant: even conservative gate (d16-20, cash>=5500, crops>=40) ->
  $33k + 78 escapes. 4th quadrant overwhelms our watering/feeding capacity.
  Unlocks only when coverage engine improves.
- Endgame sheep rush: wool prices d20-29 were $18-61 in the top replay; a
  day-23 sheep ($500 + ~$150 feed) returns ~$130 wool + $30 fert = net LOSS.

---

## ROMAN ROZEN NOTEBOOK STUDY — the 3044-rated architecture (code page find)

Pulled kaggle.com/code/romanrozen/strong-barnyard-economist (public score 3044.6).
Architecture = PRECOMPUTED 720-turn season route (zlib blob) + 4 thin runtime
layers: weed-repair (DIG + replay route), demand-aware sell ranking, clone
preemption (sell 1-3 turns before a mirror-opponent's scripted premium sale,
repay quantity later), terminal liquidation.

### Local run of their agent: $168,316 mean (we: $101k)
peak 61 crops, move 44%, weed-outs 22 (we: 151), 0 escapes.

### Their season blueprint (decoded from the blob)
- Planting: d0 melon12+wheat7 | d7 STRAWBERRY 19 | d10 melon 12 | d11 STRAW 23
  | d20-27 WHEAT WAVES (up to 23/day at d27!) — wheat cycles to the last day
- Sells: MELON day 10 (60 units! ~$240) + d20-22; STRAW d17-27 spread, big
  dump d23 (77) ahead of the d25 crash; FERT daily drip all season (248 total);
  WHEAT held for d28-29 spike (109 sold day 29 ~$53); first WOOL clip d7 ~$200
- Animals: 8 cows + 6 sheep, CARE 308 / FEED 300 / COLLECT 296 = same as ours

### Port attempt (v10.6): full blueprint LOST (-$4k). Bundle isolation:
market-timing-only (melon d11 dump + early wool) = NEUTRAL locally, shipped as
v10.6 for live price positioning. Planting side (wheat-to-d27, mega strawberry
batches) regressed because it needs scripted-route execution precision to water
the extra load — our job board weeds out (151 vs their 22).

### CONCLUSION: the path to top scores is the ROUTE architecture itself —
precomputed season plan + repair layers. Not more job-board tuning.

---

## v11 ROUTE ENGINE R&D (agent/routebot.py) — first build session

Architecture: season script (v10.6 market brain kept) + persistent route beats
(MEM route_phase, position-derived rejoin) + survival overrides + housing duty.

### Rounds
1. $24 — helpers missing, bare ["PLACE"] invalid (needs kind), housing block
   stole all units (22 retrying PLACEs/turn). Fixed: PLACE+kind, duty cap 2.
2. $33k, peak 45-48 crops(!), weed-outs 52-60 — coverage arrived but beat
   watering frequency (~1 visit/8 turns) can't hold crops alive.
3. Global nearest-watering hybrid: $23k — watering monopolized every unit,
   planting collapsed to peak 27-31. Beats and global watering conflict.

### Conclusion (matches every coverage experiment this project)
Watering frequency is THE crop ceiling. RR's 61 crops / 22 weed-outs come from
an OFFLINE-OPTIMIZED route (each crop hit exactly when needed), not from
runtime logic. Runtime-only route engines regress vs v10.6's job board.

### Next step to win: offline season optimizer
Hill-climb scripted season plans in simulation (plant waves, hire curve, sell
days as genes), embed the best as a blob + RR-style repair layers (weed repair,
clone preemption). routebot.py is the runtime skeleton for that blob.
v10.6 remains the live champion ($101k local).

---

## OFFLINE SEASON OPTIMIZER — v10.7 NEW RECORD $107,621

Built scripts/optimize_season.py: patches planner template with candidate
strategy vectors, scores 3-seed simulations (escapes penalized $5k each),
hill-climbs neighbors (~25 trials).

### Findings
- v10.6 parameters were already near-optimal: search space mostly flat or
  regressing (cows 12: -$8.5k; pb_high 1: -$4k; sheep 4: -$1.3k)
- Coverage configs confirm the ceiling again: peak-51/56-crop vectors lose
  $4-10k (h3=14, ne=6+sw=10)
- WINNER (+$4k on 3-seed search, +$6.4k confirmed on 6 seeds):
  hire 13 days 7-11 (was 12), keep 12 days 21-26 (was 11), SW land day 10
  (was 11). Nothing else moved.

### v10.7 final numbers
- Starter x6: $107,621 mean (v10.6: $101,226) — NEW RECORD
- Self-play x3: $73,525 (v10.6: $72,245)
- 0 escapes, peak 46.5 crops, wo 154
Shipped: HI_AgriBot_v10.7_PathfinderPrime.tar.gz

---

## v12 PATROL ENGINE R&D — definitive result: naive patrol LOSES to job board

Built agent/patrolbot.py: quadrant-serpent patrol segments (ping-pong), tender
corridor, adaptive survival overrides, drop-first, v10.7 market brain on top.

| iteration | peak crops | weed-outs | income | movement |
|---|---|---|---|---|
| patrolbot r1 | 66 | 33 | $52k | 67% |
| + tender protection | 64 | 35 | $51k | 69% |
| + cap@52 crops | 54 | 28 | $59k | 67% |
| + drop-first | 54 | 29 | $55k | 68% |
| **v10.7 job board** | **46.5** | **26** | **$107k** | **52%** |

### Conclusion (definitive)
- Patrol adaptively reaches 60-66 crops (coverage ceiling BROKEN at plant level)
- BUT naive patrol walks 67%+ (ping-pong traverses empty/done tiles, override
  repositioning) vs job board's 52% -> earns HALF
- RR's 44% movement is NOT from naive patrolling; it's from an OFFLINE-
  OPTIMIZED route (min walking subject to water/harvest deadlines = VRP with
  time windows). Runtime-only patrol cannot replicate it.
- Adaptive job board (v10.7) remains our champion. patrolbot.py/routebot.py
  kept as R&D. The forward path is a real offline route optimizer, not
  hand-tuned patrol.

---

## v13.0 REPLAY — the meta architecture, shipped ($164k local)

Studied 6 community notebooks + meta-analysis "Two Private Bots Beating
Kaggriculture's Public Meta" (revanthtambisetty, 2026-08-09 snapshot):
- Public meta = kaitofukami v23 (Azelearn route), 3 of top-5 run it, band 3117-3131
- Rank #1 Seb "counter_meta": 14 hires day 0, $500+ cash cushion days 1-5,
  4 quadrants, 20 animals (9 cows/11 sheep) — beats the meta band
- Rank #2 HealthStone "sheep_first_hybrid": 3 hires, 4 sheep day 0, CARE
  compounding (sheep 3-day cycle banks up to +3 units per clip)

### v13.0 = Azelearn route backbone + our overlays
- Route: public meta season plan (719 turns, embedded b85 blob)
- Overlays: weed-repair w/ action replay, attack-mode dumps, momentum escapes
- Survival lesson: do NOT override route movement (first version pulled units
  off the choreography -> $16k). The route IS the survival plan.

### Numbers
- Starter x3: $164,483 (bare route $166,225, v10.7 $107,621)
- Head-to-head vs v10.7: WON all 3, margin +$52,640 avg
- vs cow-heavy specialist: +$157k crush
- Mirror self-play: $69k (symmetric crash — clone preemption is the fix, next)
- 0 escapes everywhere, peak 61 crops, weed-outs 23

Shipped: HI_AgriBot_v13.0_Replay.tar.gz

### Next (in order)
1. Clone preemption overlay (sell ahead of mirror-route opponents — 3 of top 5)
2. Counter-meta optimizer: Seb's #1 strategy (14 hires, 4 quads, 20 animals)
   executed by our adaptive runtime — the build that actually beats the band
3. PR #1394 regime: engine balance change coming; v23 carries the Khanh route
   for it — we must detect regime + carry both routes too

---

## v13.1->v13.3: preemption lessons + sell-ranking parity

### Preemption findings (measured, not assumed)
- Early-window preemption (day 6+) BROKE the route: sold wool d6 -> injected
  cash into the deliberately-broke days 1-6 -> scripted wheat buys that should
  FAIL succeeded -> drained d7 batch cash -> cows+strawberry seeds rejected ->
  escape + -$22k. The route is razor-thin cash choreography; NEVER shift cash
  timing in days 0-11.
- Hardened preemption (day 12+, cash>=400 guard, robust repayment): starter
  clean but vs bare v23 margin -$3,461 (worse than no preempt -$1,935).
  Preemption as tuned is NET NEGATIVE vs clones. Shelved for re-tuning.
- Ported v23's _rank_sell_slots (impact-scored SELL ordering): closed gap to
  -$945 (v13.3) / -$770 (pure route+repair+ranking). Residual = weed-repair
  detail.

### v13.3 SHIPPED = route + weed repair + sell ranking + gated overlays
(attack mode + momentum escape stay — verified dormant vs clones, active vs
lopsided builds). NO preemption.
- Starter x3: $164,483, 0 escapes
- vs bare v23: within ~$1k (band parity)
Next for #1: counter-meta (Seb build: 14 hires d0, 4 quads, 20 animals) and/or
preemption re-tuned to the big dump turns only (d17/d23 strawberry).

---

## v13.4+ / COUNTER-META DECODED (the real #1 play)

### Leaderboard is Bradley-Terry win/loss, NOT dollars
Seb #1 final rewards are only $38-71k (below our $164k) yet he leads. The
ladder rewards head-to-head WINS. Our goal = WIN matches, esp. vs v23 forks.

### Seb counter_meta opening (data/seb_counter_meta_opening.md), decoded:
- d0: HIRE x7 + BUILD_PASTURE, BUY 2 COW, seeds 12 WHEAT + 3 MELON
- d0: BUY 2 SHEEP + 2 WHEAT seeds (=14W+3M total), PLACE sheep+cows into
  FOUR pastures built during day0 (t01,t05,t07,t18..t22)
- ALL-WHEAT early planting (melon only the initial 3, NO strawberry opening)
- Wheat drip-buy BUY_PRODUCT WHEAT:1 every turn t06-t23 (feed economy)
- FEED/CARE cadence on animals; CARE banks sheep bonus
- Cash cushion: never below ~$100, ends d0 at $564 (the "$500+ days1-5")
- d1: HIRE x7 more (14 hires first 48h), BUY 1 COW, COLLECT+SELL fertilizer
  drip (2,1,1) — monetizes fert immediately
- Final: 9C+11S (20 animals), 4 quadrants. Wins attrition vs v23 mirror dumps.

### Why counter-meta beats v23 forks head-to-head:
v23 mirrors crash each other with synchronized melon/strawberry dumps.
Counter-meta is wheat-heavy + fert-drip + cash-cushioned, doesn't depend on
the premium dump, so it survives the price war and wins on coverage/animals.

### Next: construct the full 719-turn counter-meta route (offline optimizer)
using this opening spec + mid-game fingerprints. This is the path to #1.

---

## COUNTER-META GREEDY PROTOTYPE (scripts/counter_meta.py) — findings

Built a live greedy counter-meta farm. Plateaus at ~$5-8k solo (needs ~$40-100k).
Root causes, measured:
- Walking dominates: ~70-80% of unit-turns are movement/PASS on a 5x5 farm.
  Greedy per-turn job reassignment causes target-switching; fixed with two-pass
  commitment (committed units act first) which HELPED a lot.
- Crop watering is the hard constraint: plants die after 2 unwatered days.
  With N hands you can reliably water ~2x N crops. Over-planting -> weed_outs.
  A planting governor (cap = ~2.2x hands) + feed-gap forcing got escapes to 0.
- Greedy caps out because it can't choreograph paths. Every top bot (Seb,
  HealthStone, v23 forks, RR, boatlee) is a RECORDED ROUTE, not live greedy.
- Key engine facts learned: 10 market slots/turn (each HIRE=1 slot); animals
  buy->shed->PICKUP->PLACE on free pasture; tile["animal"] is a kind string;
  fertilizer is free high-value income (collect it); shed access = 4 inner corners.

### Best configs hit: esc=0, ~10-11 animals, ~100 fert, $6-8k. NOT shippable.

### Correct path to #1 (decision):
Rebuild a v10.7-GRADE adaptive agent (sticky roles, role-gating, planting
governor, hire curve) but with counter-meta strategy (wheat-heavy feed economy,
9C+11S, cash cushion, no synchronized premium dumps, sell wheat into v23 demand).
v10.7 reached $107k live, proving adaptive agents CAN be competitive — the crude
greedy prototype just lacks that machinery. This is a multi-session build.

SHIP ARTIFACT REMAINS v13.3_Replay ($164k solo, band-parity vs v23 forks).

---

## COUNTER-META BUILD v2 — decisive head-to-head result

### Progress this round (real machinery gains):
- SAME-DAY WATERING fix: planted crops start consecutive_unwatered=1 and die
  THAT NIGHT if not watered same day -> made age-0 watering priority 0.5.
  weed_outs 47 -> 0-9.
- Planting governor (don't expand when dry plants exceed watering capacity).
- Two-pass commitment + tier-nearest job selection + role momentum (cut walking).
- Fert economy unlocked: 200-280 fert/game (~$20k). Placement gated on feeding.
- Solo result: $15-20k, 0 escapes, 10-13 animals. Up from $2k.

### DECISIVE head-to-head vs bare v23:
  seed1: US $4,759  vs v23 $94,644   LOSS
  seed2: US $6,410  vs v23 $165,678  LOSS
  seed3: US $6,138  vs v23 $120,623  LOSS
  margin: -$121,213

### Conclusion:
The greedy counter-meta produces ~10% of v23's output. NO strategy compensates
for a 10x production gap. Seb's counter-meta makes ~$57k head-to-head (bigger
cash-cushioned build: 4 quads, 20 animals, $500+ cash days1-5) and THAT is what
beats v23. To win we need $100k+ production WITH counter-meta strategy.
The blocker is farm PRODUCTION EFFICIENCY (walking/coordination), which recorded
routes solve and live-greedy cannot reach.

### Next lever to try: Seb's DECODED 48-turn opening (proven trajectory) replayed
exactly, then hand off to adaptive planner for midgame.

---

## ALL-IN PRODUCTION PUSH — definitive ceiling established

### Architectures tried (all converge to ~$10-18k):
- Wheat+fert greedy engine ............ $15-18k (best, 0 escapes)
- High-value melon/strawberry ......... $4-12k (displaced feed wheat)
- Big workforce (14/day multi-hour) ... $4k (idle hands burn wages)
- Demand-driven hiring ................ $9-10k
- Alternating-day watering ............ $9-12k (weed_outs rose)
- Spatial zones / role momentum ........ no effect (72% walking persists)
- Day-level spatial queue ............. walking 72%->56% but broke animals ($3k)
- Hard role specialization ............ broke feeding (20 escapes)

### Key unlocks found (real progress, saved in counter_meta.py):
- Same-day watering fix (planted crops die that night if not watered).
- Animal pipeline unclog: designate() capped pasture pipeline at 2 -> only 9
  pastures built while 14 animals idled in shed. Fixed -> 14-15 animals, 246 fert.
- Multi-hour hiring (10 slots/turn, hire across h0/h6/h12) enables 14/day.

### The wall: live-greedy caps ~$15-18k. v23 = $100-165k. Gap is PATH
CHOREOGRAPHY efficiency (recorded routes), not strategy. The counter-meta
STRATEGY is sound and working; the farm EXECUTION can't reach competitive
production via live greedy. Head-to-head we lose by ~$120k (production gap).

### Conclusion: #1 requires a RECORDED counter-meta route at $50-100k. That
needs an offline route optimizer/choreographer, not a live agent. v13.3 (already
posted) remains the competitive artifact at band-parity with the v23 forks.

---

## META SHIFT 2026-08-09 evening + v14.0 (portfolio fork)

### Ladder moved again today (Kaito v25/v26 notebooks):
- Top-30 snapshot 2026-08-10: v23 exact 15 teams (ranks 3,4,13,15,18-29);
  v25 HIRE5 sheep-first 9 teams (5,7-9,11,12,16,17,30); HIRE4 sheep-first 2
  (6,14); v23+wheat 2 (10,25); HealthStone HIRE3 (rank 1); Seb HIRE6
  wheat-heavy (rank 2).
- v25 = THUNDER THUNDER sheep-first route: 48/50 dev, 30/30 vs v23 family.
- v26 = seat portfolio (seat0: Yubo WANG, seat1: Gbining): 24/25 strict
  future. Its stated BIGGEST WEAKNESS = Seb HIRE6 wheat-heavy counter.
- v26 routes already wheat-heavy: sell 446-459 wheat (Azelearn: 271),
  146 wheat seeds, 9-10 cows + 4-6 sheep, 2 land, still dump strawberry ~285.
  => The meta is converging toward Seb's wheat economy; pure Seb counter
  (20 animals, 4 quads, no premium dumps) remains unreplicated publicly.

### v14.0 SHIPPED (submit/HI_AgriBot_v14.0_Portfolio.tar.gz, sha 5f22a37c...)
Fork of kaitofukami v26 with attribution (explicitly permitted).
- Solo: $136-176k; beats v13.3 head-to-head both seeds (+$9k, +$11k).
- Daily submission limit (5) blocked upload at turn end -> post tomorrow.
- v26 routes decoded to data/v26_route_seat0.json / seat1.json for study.

### Loss analysis (v13.3 @ 1772.6): lost to chengyeh2 -17979, raykkretzschmar
-21356, chae young -12931, Howon Kang -11996, kaggle bot -11601. Pattern:
meta-vs-meta market wars + newer route families. Replay API broken (returns
random episodes). Cash-guard experiment on v13.3 FAILED (route's wheat drip
buys are essential choreography; guarding them starves animals -> 12 escapes;
reverted).

### Next: counter-meta route optimizer. Assets: v26 route templates (strongest
public choreography), Seb opening tape (data/seb_opening_tape.json), decoded
Azelearn blueprint, counter_meta.py live engine ($15k, all engine knowledge).

---

## ENDGAME PREMIUM PUSH — user hypothesis CONFIRMED (+18%)

User observation (watching Kaito matches): endgame could use more
melon/tomato/strawberry. Tested:
- No meta route touches TOMATOES (seed $50, ongoing daily production from
  d+8, $60 base, PIZZA_SHOP/FARMERS_MARKET demand, empty market -> price vacuum).
- Azelearn/v26 end with wheat spike (85 wheat d29 ~ $2.2k) — low value.
- A/B on live engine (3 seeds): baseline $15,241 vs tomato(6 slots d9-14) +
  late-melon(d15-17 on wheat tiles) = $17,944 (+18%), best seed +28%.
- Baked into counter-meta route spec: melons d15-17 -> harvest d27-29;
  tomatoes d9-14 -> daily harvests d17-29 into unsaturated market.

Links user watched: sub 55375888 = Kaito's leaderboard submission (not ours);
replay API still returns random episodes (one WAS a Kaito match they LOST
$33k vs $38k — even Kaito loses sometimes). v14.0 still not posted (daily
5-submission limit hit) — post HI_AgriBot_v14.0_Portfolio.tar.gz tomorrow.

---

## ROUTE OPTIMIZER v1-v5 — built, working, but hit the ceiling

Built scripts/route_gen.py (records tape + telemetry) and route_eval.py
(replays + audits + head-to-head). Optimizer loop confirmed working — each fix
compounds: v1 $10.0k -> v3 $12.8k -> v5 $13.8k (0 escapes, 189 fert).

Fixes landed: market slot budgeting (buys before hires), endgame premium push
(tomato vacuum + late melon), animal placement committed-targets (killed the
94-pickup/10-place bounce), parallel placement, feed buffers.

### DECISIVE head-to-head vs v26 (current meta):
  us $9,373 vs v26 $126,517 avg -> LOSS by $120k.
The greedy planner's farm (12 animals, ~15 crops, ~60% of unit-time walking)
cannot reach competitive production. Recorded top routes are HAND-CRAFTED
choreographies ($100-165k); greedy re-deciding can't match that efficiency.

### Honest ceiling: greedy route ~$14k. Competitive needs $50-100k+.
Paths: (a) research-grade planner (many sessions), (b) adapt a strong public
route (v26) toward counter-meta at the market layer (hard: crop mix is baked
into choreography), (c) hold v14.0 and wait for a meta edge.

---

## OPTIMIZER BUILD PHASE COMPLETE — final assessment

### Infrastructure built (persists for future sessions):
- scripts/route_gen.py   — records tape + telemetry from any planner
- scripts/route_eval.py  — replays tapes, audits, head-to-head vs any opponent
- scripts/route_compiler.py — spec-driven compiler (layout/economy/scheduler)
- scripts/counter_meta.py — best live planner (all engine knowledge)

### Results (8 iterations):
- BEST counter-route: data/counter_route_best.json = $13.5k vs starter,
  0 escapes, 12 animals, 189 fert, endgame push included.
- Animal scaling solved (pipeline bounce fixed: committed pasture targets,
  5-carrier test placed all 20) BUT 20 animals bought 179 feed-wheat and
  NET MONEY FELL ($9.9k): fert gains eaten by feed cost. More animals only
  pay when wheat is self-grown at scale.
- Strategy variants all land $13-14k: the pie size is set by SCHEDULER
  EFFICIENCY (60-72% of unit-time walking), not crop/animal mix.
- Compiler chunk-scheduler broke feeding (escapes) — crop/animal time-critical
  logistics don't tolerate spatial batching. Zone-penalty patch crashed (bug)
  and was reverted cleanly.

### Decisive conclusion:
Competitive needs $50-100k+. Closing the 4-7x gap requires solving
choreography efficiency: a daily route planner (watering/feed scheduling as
VRP-with-deadlines), which is a research-grade build for future sessions.
SHIP ARTIFACT REMAINS: submit/HI_AgriBot_v14.0_Portfolio.tar.gz (post it —
daily submission limit blocked upload).

---

## v14.1 TERMINAL SWEEP — beats v26 head-to-head (measured)

Source: andrewsokolovsky "Kaggriculture: Breaking the Tie" notebook (today).
Grafted its route-agnostic Terminal Sweep onto our v26 base (all helpers
already present).

What it does: at step 718 (penultimate turn), banks every unit's carried goods
into the shed and liquidates the whole shed, ranked by price impact. Recovers
value the fixed route otherwise leaves stranded in unit inventories.

Measured (vs bare v26):
  5 seeds: v14.1 wins 3/5, mean margin +$1,115 (was negative pre-sweep).
  Solo: $136-176k maintained.

Ready artifacts (blocked by 5/day submission limit — post tomorrow):
  submit/HI_AgriBot_v14.0_Portfolio.tar.gz   (v26 fork, baseline)
  submit/HI_AgriBot_v14.1_TerminalSweep.tar.gz  (RECOMMENDED - beats v26)

The "clone queue duel" variant was held back by its own gate (recorded losses);
only Terminal Sweep promoted. Remaining #1 lever: Seb wheat-heavy counter route
(needs the VRP choreography planner — future session).

---

## TRADE MODEL + V26 BLUEPRINT DECODED (this session)

### v26 production blueprint (the $160k target), decoded from route tape:
SELLS: fert 245, wheat 459, wool 132, milk 218, melon 114, strawberry 285
BUYS:  10 cows + 4 sheep (14 animals), 146 wheat seeds, 19 melon seeds,
       38 strawberry seeds, 2 LAND (3 quadrants), and **234 feed-wheat bought**.
=> TRADE ECONOMY: buys feed-wheat, dedicates land to high-value strawberry/melon
   + wheat-for-sale. NOT self-feeding. Hires ramp [4,1,2,3,3,3,4,7,...14] — LOW
   early (saves market slots + cash for seeds/animals), high mid/late.

### Greedy planner pivoted to trade model (strawberry-heavy):
- $13.5k (wheat/fert baseline) -> $17.7k (strawberry trade model) = +31%.
- Buys-first demand hiring beats hires-first ($5.2k) because 10 hires fill all
  10 market slots and starve seed/animal buys. Lesson: 10-slot cap forces a
  buys-vs-hires budget; v26 schedules both across h0/h6/h12 with low early hires.

### THE WALL (confirmed across all generators):
- greedy planner: $13-18k   - sweep compiler: $0.6-2k   - target: $160k
- Gap is COORDINATION EFFICIENCY (pre-planned paths vs greedy re-deciding,
  60-72% of unit-time walking). Strategy/crop-mix changes give +30%, not +900%.

### Competitive artifact: v14.1 (v26 + Terminal Sweep) beats bare v26 head-to-head
(+~$1.1k, 3/5 seeds). It climbs past the v26 basin. Whether it beats Seb's
counter-meta (which counters premium-dump strategies) is unproven.

### Path to #1: a true counter-meta route needs NEW choreography (wheat-heavy,
20 animals, 4 quadrants) at $60-100k production. Requires solving the
coordination problem (VRP-style day planning) — research-grade, not yet achieved.
