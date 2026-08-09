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
