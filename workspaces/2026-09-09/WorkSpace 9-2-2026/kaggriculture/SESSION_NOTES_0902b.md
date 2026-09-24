# Session checkpoint — 2026-09-02 (afternoon): H2H decoding + straw breakthrough

## Current best (banked at topbots/v3_base.py)
Spec: `{"SHEEP":4,"COW":12,"GOOSE":0,"hands":9,"melon_start":0,"cow_day":12,"ne_day":7,"sw_day":14,"wheat_sell_day":4,"feed_buffer":2,"straw_tiles":13,"straw_zone":"b","melon_b":0,"carrot_sw":0}`
- **Solo seeds 1-8: 113,288** (author-line record; was 104,872 at session start)
- H2H vs v1112fr (seeds 1-6, both seats): 0-12, avg 56,030 vs 142,918
- H2H vs v120_puretape: 0-12, avg 55,416 vs 141,299

## The big discoveries this session

### 1. Solo eval is a misleading metric — H2H is a different game
- Shared market: opponent's sells crash your prices; opponent's buys drain the pool.
- **v1112fr = a WHEAT MACHINE**: buys ~3,500 wheat ($150k) and resells (~$153k) — the loop
  DRAINS the market pool to −550 below I0 → wheat price doubles to $44-48. Direct loop P&L
  is only ~+$3k, but: (a) its own wheat harvest sells at 2×, (b) OUR feed buys cost 2×.
- Shop draws are RNG-coupled to board state (weed draws consume the shared RNG per None tile),
  so H2H shop/consumption patterns differ from solo — measured H2H milk consumption 422 vs
  solo 138 on the same seed. Milk prices HELD at $214-246 avg in H2H despite 386 combined
  units sold — the town absorbs far more than the solo model assumes.

### 2. The H2H death spiral (fixed)
v3 in H2H collapsed to ~$31-46k because:
- D12 cash: solo $6.5k vs H2H $3.8k (wool crash + feed 2×) → `BUY COW 10` ($400/cow — NOT
  $1,200!) + 5 HIREs overflowed the money → hires failed → crew understaffed →
  placements/care/harvests slipped → herd stuck at 11, milk 115 units vs 204.
- Fixes: (a) H00 queue order = [morning sells (funding)] → [HIRES] → [land/animals/product/
  seeds], hires capped to leave room for buys; (b) wheat sell policy = feed-first: sell only
  surplus above 2-day reserve post-cow_day, churn down to 4 units pre-cow_day (funds cows);
  (c) `_wheat_ledger` mirrors the actual sell policy (was modeling the old flat-25 sells →
  bought ~$15-25k of unneeded wheat — this was the 91k regression, now fixed).
- Cows cost $400 (verified via _commit_unit log). All 12 cows now bought+placed in H2H
  (herd 15-16), milk 208 units @ $238 = $49.5k in H2H seed 1.

### 3. Engine facts newly verified
- HARVEST puts products in unit INVENTORY; they reach the shed only at EOD
  (`_drop_inventories_to_shed`). So the day's harvest is sellable only from next H00.
  H00 sells of yesterday's EOD drop are correctly timed; same-day H23 sells see a stale shed.
- SELL orders self-limit at shed contents (99 = "sell all that's actually there").
- BUY_ANIMAL lands in the SHED (counts vs 100 cap), money-checked per unit (partial buys OK,
  no retry — a failed qty is lost forever).
- Market orders (buys AND sells AND hires) work at ANY hour; 10-order cap per turn; the
  engine interleaves both players' queues index-by-index (order i both players, then i+1).
- Plant death: 2 CONSECUTIVE unwatered days → tile becomes a WEED. Water every other day is
  the minimum (my straw calendar at 9 waters/16d is optimal).
- Weeds: my farm's draws are the first N of the shared RNG — same solo vs H2H; the
  OPPONENT's board state shifts the stream (hence different shops).
- BUY_PRODUCT/BUY_ANIMAL check shed capacity 100 — a full shed silently blocks buys.

### 4. The straw breakthrough — B-zone, not A0
- `straw_zone="b"`: strawberries claim the 13 B-zone tiles (NE quadrant) instead of the A0
  melon corner. All previous straw tests put them on A0 (displacing the best melons) → lost.
- B-straw: solo 98.2k → 113.3k; the A0 melons (2.3 cycles × $215) stay untouched.
- H2H straw market: v1112fr sells 311 units @ $240; town eats 460+; my 104 units don't
  break the scarcity. Strawberry is THE H2H cash crop.
- Duty load is THE constraint: B→wheat (29 wheat tiles) scores WORSE than leaving B idle
  (84.1k vs 98.2k solo) — water/harvest cascades kill other crops. Straw (13 duty/day) is
  LIGHTER than wheat (18/day) on the same tiles.

### 5. Dead ends confirmed this session
- SE quadrant (any crop, any se_day, with/without hands 10): always −10-20k (duty overload).
- Early cows (cow_day 8-10): worse solo AND H2H (compete with melon wave for cash/crew).
- Straw on A0 (any count), straw 21 (B+C), melon_c=0, SHEEP 6, COW 14, hands 8/10: all worse.
- carrot_sw on the straw base: worse (carrot 0 best).
- The milk 99-dump: converges to the same result as the k-gated trickle (pile_max 15 + H23
  drain 10 + endgame catch everything); keep the trickle.

## Where the remaining H2H gap is (seed 1, after fixes: v3 71.7k vs v1112 161.9k)
- v1112 strawberry: $74.6k (39 tiles — I have 13, duty-capped)
- v1112 milk: 264 units vs my 208 (their cows placed ~D8; mine D12 — earlier cows lose more
  than they gain in my schedule)
- My melon: 120 @ $159 = $19.1k — I flood it; they trickle 66 @ $209 (I win total $ anyway)
- The wheat machine: now neutral to me (feed self-sufficient) — mirroring it nets ~$0 direct

## Next levers (ranked)
1. Duty-engine capacity: leaner walk calendars (snake order), or make WATER critical in the
   carry so crowding kills fewer plants; possibly a leaner animal routine.
2. A market-maker layer on top of the tape (buy wheat low D15+, sell D25+) — needs the
   price path which is seed-dependent; risky for a static tape.
3. Multi-opp H2H sweep (old submissions + opponent_library) to check the author vs the field
   before any submission decision.
4. Possibly hands 10 with a re-tuned (leaner) crop plan — the +$55/day hires need to buy
   back more than one melon tile's worth of duties.

## Submission status
NO submission made (user GO required). v1112fr (55947935) remains the live submission.

## Evening update — the hybrid wheat/straw farm (user-directed)

User's idea: full wheat/straw farm, self-sustained feed (never buy), more animals + hands,
sell wheat reserves when prices are high. Tested end-to-end:

### New champion (banked topbots/v3_base.py)
`{"SHEEP":4,"COW":12,"GOOSE":0,"hands":9,"melon_start":0,"cow_day":12,"ne_day":7,"sw_day":14,"wheat_sell_day":4,"feed_buffer":2,"straw_tiles":13,"straw_zone":"b","melon_b":0,"carrot_sw":0,"wheat_extra":13}`
- Solo 1-8: 104,734 (the no-wheat_extra variant does 113,288 solo but ~10k worse H2H —
  H2H is the LB metric, so the wheat version is the champion)
- H2H 6 seeds both seats: 59,817 vs v1112fr (was ~45k at session start); 62,571 vs v120
- Best single H2H game: 75,007 vs v1112fr seed 1 (v1112: 167k — its best-draw seed)

### What worked (user's plan)
- **wheat_extra 13** (idle tiles → wheat): +11k H2H (61.7→72.7 on seeds 1-3). Feed buys
  dropped from ~190 units/$8.7k to 70 units/$2.5k per game. Wheat sold 38 units at $41 avg
  (surplus gate sells only above the 2-day feed reserve — "sell when high" achieved).
- The knob saturates at ~10 tiles — the last 3 SW-edge tiles produce nothing.

### What didn't (carrying capacity is real)
- Extra animals beyond the 16 good slots: overflow slots collide with wheat tiles; on free
  far tiles the extra cows' FEED/CARE/COLLECT walks cost more than their milk (+1 cow
  placed, final −$6k). Fixed the slot collision — still net negative.
- More hands (10/11): −2.5k H2H (fib hire costs: 9=$88/day, 10=$143, 11=$231).
- Sheep cuts (sheep2/cow14, sheep0/cow16): CATASTROPHIC (36.8k-91k solo). The 4 sheep are
  the cash-flow shock absorbers: only $2k of D12 budget + their D8+ wool funds the cow wave.
  4 sheep + 12 cows is the sweet spot.
- Goose ("chicken"): dead. Eggs $50-68/slot vs milk $238/slot; free tiles are worth more
  as wheat. No egg sellers in the meta, but the price ceiling is too low to matter.
- feed_buffer 0/1, wheat_sell_from 18/22, straw 11: all noise.

### Biggest remaining leak
Straw efficiency ~27%: 13 planted → 7 alive D21 → only 28 units sold of a possible 104
($19k+ left on the table). The far B-corner tiles (x=9 column) die from dropped waters
during the crowded D15-20 window. Next session: stagger straw plantings over 3-4 days to
spread the water load, or harvest-after-event-2 (p+12) and sacrifice the p+16 harvest.

### Engine facts added
- CROPS feed: only WHEAT feeds animals (straw/carrot/melon don't).
- Extra animal slots must not overlap wheat/straw/melon tiles (BUILD_PASTURE no-ops on a
  planted tile — silent failure, the animal is bought but never placed).

## Evening update 2 — the packed/hybrid animal experiments (user-directed)

User's idea: wheat-only after NE expand, pack animals close in NW (near the crew), scale
animals + workers until output stops covering hires. Built `farm_plan` "packed" (all-wheat
crops, animals on a center-ring spiral) and "hybrid" (center-ring animals + champion crops).

### Results (all vs champion: solo 104,734 / H2H 72,732 on seeds 1-3)
- packed cow12 h9:  solo 87,307 / H2H 45,374  — crop revenue loss dominates
- packed cow16-24 h9-11: solo 51,914-84,097 / H2H 32,324-40,444 — worse with more animals
- hybrid cow12 h9 (fixed): solo 91,960 / H2H 55,176 — still −17k H2H vs champion
- hybrid cow14/16: no better

### Why it loses (measured, not theory)
1. Crew spawns on the 4 CENTER tiles (4,4)/(5,4)/(4,5)/(5,5) — "close" = center ring, and
   the champion already puts wheat_extra on exactly those tiles. Moving animals there
   displaces the best wheat to the far NW corner where it dies silently (wheat has no
   visible death — missed waters just mean no harvest).
2. Pure wheat+animals income ≈ $68k gross vs champion's crops: straw $26k + melon $18k +
   wheat surplus — the cash crops out-earn the marginal animal by ~2x per tile.
3. More hands don't unlock capacity: hires are fib-priced (9=$88/d, 10=$143, 11=$231) and
   every +1 hand config nets −2.5k H2H.

### Verdict
The champion allocation (16 animals mid-ring + straw 13 on B + melon A0/A1/C + wheat
NW/SW/extra13) is empirically optimal within this duty engine. The carrying-capacity wall
is the TOTAL walk+duty budget, not animal proximity. Scaling animals further requires a
leaner duty engine (fewer walks per action), not different tile packing.

CHAMPION UNCHANGED: topbots/v3_base.py (wheat_extra 13 + straw 13 B-zone).

## Night update — the co-design grid (user pushed for balance+routing search, was right)

~50 configs: straw zone/count/stagger × wheat level × cows × hand ramps (flat/peak) ×
SE expansion × water-criticality × duty budgets. H2H (seeds 1-3) as the metric after the
solo prescreen proved misleading (wheat-heavy wins H2H via the $46 feed tax, loses solo).

### Found
- **Peak-10 hand ramp (D11-21, 9 before/after) = new champion**: solo 105,661 / H2H 59,995
  vs v1112fr / 63,589 vs v120 (6 seeds, both seats) — beats flat-9 on all three metrics.
  At lighter wheat configs the ramp is worth +15k, but those configs lose more elsewhere.
- **cow14 wins at wx6 solo (109,029)** — animal scaling is real when tiles free up, but the
  freed wheat costs more H2H than the cows earn (feed deficit at $46).
- Straw stagger (spread plant days): POISON, −20k H2H. Water-critical routing: −10k
  (evicts melon/wheat waters instead — zero-sum at capacity). A0 straw: −20k (A0 melons
  too valuable; also finishes early but the corner tiles are the farthest walks).
- SE quadrant + peak crews: best 69,545 (SE wheat 12 @ D18, peak11 D17-25) — close but
  still below champion; the $4k land + late cycles + extra hires don't quite pay.

### Walls precisely measured
- **Tile budget 100% full**: every overflow animal slot collided with wheat (bug found:
  extras silently never placed). Extra cows need freed tiles; freed tiles cost feed.
- **Duty budget 22 is calibrated**: raising to 26/30 COLLAPSES the tape (15-16k H2H) —
  units physically can't complete more (3 acts/turn hard engine limit; walks eat the rest).
- The balance point: full wheat (29 tiles) + straw 13 B + melon 18 + 16 animals + 9 hands
  (peak 10 mid-game). Every measured trade away from it loses 3-20k.

### The real unlocks left (code projects, not configs)
1. **Cluster router in build_day2**: units own zones (quadrant clusters), batch feed sweeps
   (one unit carries N wheat, sweeps adjacent animals), combined water+harvest passes.
   Current global-snake per-tile groups waste walk steps — the effective capacity ceiling.
2. **Straw reliability**: 28/104 units sold (~$19k/game on the table) — far B-corner tiles
   die of missed waters in the D15-20 crunch.
3. Milk sell depth in H2H: prices hold $214-246 even at 386 combined units — our k-model
   still undersells (179-208 of ~210 produced).

CHAMPION BANKED: topbots/v3_base.py = champion + peak10 ramp.

---

# Night update 2 — router closed, maker autopsy, the reactive line decoded

## Recovery (complete)
- `replace("")` corruption fully reversed via split-on-NEW (`_ref/recover.py`, since deleted): 44,590 parts, all single-char middles, 1,127 lines, syntax OK. Champion regen reproduces the banked numbers **to the dollar** (solo 105,661; H2H 72,749 seeds 1-3). `_ref/tape_author3.py` is healthy; cluster-v2 was then re-applied with anchored edits (`assert src.count(old)==1`).

## Router question: CLOSED (snake wins)
- Cluster v2 (round-robin criticals + budget-capped greedy crops + NN ordering), functional version: **solo 97,654 / H2H 59,750** vs snake 103,887 / 72,749. Contiguous snake bands beat every proximity heuristic (nn 53.3k, cluster 59.8k) — territories that don't crisscross win; the 4 center spawns are equidistant anyway. Do not revisit.

## Measured-and-closed levers (all on champion base, H2H seeds 1-3 unless noted)
- **straw_short_far** (x≥8 tiles → 4-unit lifecycle + wheat filler): 71,982 vs 72,749 — neutral; far tiles already got harvest 1, deaths are harvest-2-late and short gives that up too.
- **Ramp extensions** peak10→D24/D26, peak11 D12-24: ≤ noise (71,994 / 72,987 / 69,282).
- **Sell-depth knobs** (milk_drain/14-16, milk_pile 5-8, melon_drain 12): literally no effect — caps never bind; sells already ≈95% of production.
- **ba0 / a0 straw in H2H**: 50,041 / 56,397 / 45,047 / 46,736 — dead in H2H too (earlier solo prescreen was honest).
- **ne_day 99 (no NE unlock)**: CRASHES to 37,675 H2H / 58,283 solo. **The B zone IS the NE quadrant** — all 13 straw tiles live there. NE unlock ($5k) is load-bearing; the "skip the last quad" instinct applies to SW only.
- **Milk timeline**: cows placed D12 → first milk **D20** → milk sells already land entirely in the $250-264 H2H window. Not a lever; the "milk depth" leak was a misread.

## Price series (measured, `_ref/price_series.py`)
- SOLO: wheat 28→47 monotone (town drains ~13-30/day, my sells barely dent). H2H: peaks $44 @D24, v1112fr dumps D25-29 → $40. Milk: H2H peaks $264.
- Town: shops consume every 4 steps (~28-36 wheat/event late-game, exact list visible in obs), center every 24.

## Market-maker autopsy (the important negative result)
- Reactive tape maker (reads live obs prices, trend triggers, money-delta reconciliation) v1 "+2,403 solo, +485 H2H validated" was **CASCADE LUCK**: per-seed trade logs showed seed 3's +10,791 came from ONE trade (+$275 direct) — the $750 buy at D6H05 with $1,659 cash made a *tape* buy fail → farm-plan cascade. Tape is chaotic: ±$750 early cash ⇒ ±10k on some seeds.
- Safe version (cash floor $9k, buys only H10-18): **−2,657** — overnight shed occupancy of the 25-unit chunk causes harvest discards > scalp profit.
- Intraday-only (flat by H20): **+112 total** — real, traceable, noise-level.
- **Verdict: the market machine cannot be retrofitted to a static tape.** v4_maker retracted → `topbots/rejected/v4_maker_CASCADE_LUCK.py`. Champion remains **v3_base.py**.
- **LESSON (standing)**: validate any tape change that touches early-game cash per-seed with trade logs; ±$750 can cascade ±10k. Averages over 6-8 seeds are NOT enough when the mechanism touches cash flow.

## v1112fr decoded (self-contained)
- 69-line bootstrap + zlib+b85 blob → 11 modules, ~130KB (`/tmp/v44_modules.pkl` scratch). Key: `v44.gold_floor` (40.8k-char reactive orchestrator), `v24.market_maker` (29.6k), `v19_terminal`, `v23` planner stack, `v22` market-impact / weed-repair, `v21` route-memory stub.
- Their maker: **one-turn round trips sized to the exact visible town demand** (buy q ≤ d, town consumes d, sell next turn, exact impact math, min profit $1, batch 60). Worth ~$2-5k/season — **not** the 90k gap.
- The ~90k H2H gap (163k vs my 73k on seeds 1-3) = the reactive architecture itself: live routing, weed/duty repair, adaptation to actual shop draws + realized prices. A static tape cannot close it.

## Strategic picture (decision needed)
- Tape line: plateaued at solo ~105.7k / H2H ~60k (6-seed). Every production, routing, timing, and market lever measured. v3_base.py stands.
- The live submission (reactive line) is where the remaining EV is. Options:
  1. **Config-knob A/B on v1112fr** — `_V44_CONFIG` exposes ~30 knobs (yarn_third_*, bakery_capital_*, clone_*, maker params). Same harness discipline applies (opponent_library + seeds).
  2. **Port the champion farm plan** (4S/12C/9H/peak10/wx13/straw13) into their planner as the policy prior — bigger surgery, uncertain payoff.
  3. Stop tape-line work; keep v3_base as diversity hedge only.

---

# Session 3 — the multi-animal farm (goose line), the shop lottery, fr1 banked

## BANKED: v4_fr1.py = new champion
- Spec = v3_base + `feed_reserve:1, egg_drain:2` (egg_drain inert without geese).
- **solo(1-8) 110,378 (+4,717) | H2H 6-seed: 62,232 vs v1112fr (+2,237) | 66,309 vs v120 (+2,720)**. Every solo seed improved (+0.6k to +17.4k); both H2H matchups improved.
- Mechanism: the 2-day wheat feed reserve squatted ~16-18 shed slots all season and delayed wheat surplus sells; at 1 day, fewer EOD discards (control had 50 units/season discarded) + wheat sells land earlier at good prices.
- This is a **same-lottery** comparison (sell-timing only — see lottery note below), so the gain is clean, not draw luck.

## THE SHOP LOTTERY (major methodology discovery)
- `_end_of_day`: `_spawn_weeds(farm, ..., rng)` runs on the SAME `random.Random(seed*1_000_003 ^ day)` stream as the town's shop-unlock draw. **Any change to tile occupancy (crop choice, coop vs wheat, plant timing) shifts the weed draws and redraws the ENTIRE shop schedule** → the town's consumption mix per product swings wildly.
- Consequences measured: milk inventory can end +76 above I0 vs −160 on the same seed depending on farm shape (few milk-draining shops drawn). The milk price swings $264 vs $4. Single-seed (and even 3-6 seed) farm-shape A/Bs are lottery-dominated (goose config: −33.8k seed 1, +16.3k seed 4 vs control, same configs).
- Rules from this: (1) farm-shape changes need 12+ seeds for a verdict; (2) sell-timing-only changes (no tile/timing perturbation) are same-lottery and clean at 6 seeds; (3) (me − opp) is NOT a luck-adjusted metric — the opponent's wheat machine profits from different draws than we lose from milk crashes.

## Goose line (the "all animals" farm): tested thoroughly, dead for the static tape
- Fixed real bugs along the way: geese were gated to COW_DAY=12 (wasting their early-yield edge) → own goose_day/stagger; geese stealing pasture slots silently dropped cows (16-slot overflow) → dedicated GOOSE_SLOTS on the free shed-adjacent tiles (4,3),(3,4) + wheat conversions.
- Best configs (co-designed: sheep cuts, wx cuts, cow_day spreads, ramps, feed_reserve, goose_lite FEED+CARE-only): **all lose**. 12-seed solo: control 111,188 vs g2-lite 92,651 / g4-lite-s2-wx10 85,054. H2H similar.
- The honest ledger (seed-1 direct breakdown): eggs +$10.1k, fert +$0.9k, wool −$1.7k (2 fewer sheep), straw −$4.3k (harvest duties displaced in the D20-24 crunch) → +$5k direct, **but −$15-25k of schedule desync**: D12 pile-up (10 cow placements + melon wave + goose duties → melon harvests slip → whole melon cycle shifts), endgame starvation deaths (4 animals D24-29 at 18 head), melon/straw timing shifts.
- The tape's schedule is a brittle optimum: ANY added daily load causes desync damage that dwarfs the egg revenue. goose_lite (skip fert collect) doesn't fix it — it's structural.
- **The egg-market opportunity is REAL though**: nobody in the meta runs geese; eggs hold $50-54 in a starved market (log curve, deep); 4 geese = +$10k gross revenue measured. Capturing it needs a live replanner = the reactive line.

## Milk gate (reactive price-gated milk sells): wash, off
- V1 (gate $170, hold to cap 40, release on recovery): −221 avg over 6 seeds. Glut seeds are structural (combined oversupply vs town drain); timing games move ±$2k only. Code kept, spec-gated off.

## Author state (`_ref/tape_author3.py`)
- New spec knobs (all default-off, champion regen verified byte-identical to v3_base with the v3 spec): `goose_day`, `goose_stagger`, `goose_tiles`, `goose_lite`, `feed_reserve`, `egg_drain`, `milk_gate`/`milk_gate_px`/`milk_gate_cap`/`milk_gate_days`, plus earlier `maker*`, `milk_from`, `straw_short_far`, `ba0`, `router`.
- Backups: `.bak_goose`, `.bak_milk` (pre-goose-session state).

## Champion table
| tape | solo(1-8) | H2H vs v1112fr | H2H vs v120 |
|---|---|---|---|
| v3_base | 105,661 | 59,995 | 63,589 |
| **v4_fr1** | **110,378** | **62,232** | **66,309** |

---

# Session 4 — geese in the reactive line (v1112fr port): BUILT, MEASURED, DEAD

## What was built
`topbots/v1112fr_goose.py` — a pure **wrapper overlay** around unmodified v1112fr (no blob surgery): loads their agent, appends market orders only in free slots, drives only PASS hands it hired itself, buys SE land ($4k, quadrant their tape never uses), builds a compact coop block at (5,5)-(8,7), board-as-state daily tour (FEED > COLFERT > CARE-if-fed > HARVEST>=3, feed-sprint H17+, wind-down D29), belt-neutral wheat buys, egg/fert sells at H20+. **Mechanically complete**: coops built D11, geese bought/placed/fed/cared, eggs+fert sold. Three rewrite cycles fixed: (5,5) shed-corner coop self-shadowing, nearest() including self, goose-carrying hands distracted en route (→ strict missions: PLACE > FEED > FETCH > TOUR), day-end auto-drop returning carried geese to shed, double PICKUP races.

## Results (8-seed solo vs v1112fr baseline)
- v1 (6 geese/1 hand, shed-corner block): **−8,821 avg**
- v2 (10/2, compact): −13,299 → v2-fixed: −23,052 avg (placement pipeline churn)
- Final v3: −23,052 avg (seeds −10.2k to −37.7k; 2/8 positive = lottery noise)

## The decomposed ledger (isolation tests, seeds 1-6)
| component | solo delta | mechanism |
|---|---|---|
| wrapper only (no actions) | **+0.000 exact** | proven harmless (6 seeds identical) |
| + 2 PASS hands/day (no spending) | **−13,064 deterministic** | fib hire fees ~$7k (hands #12/#13 = $144/$233 per day) + ~$6k: extra hands shift shed-corner spawn assignments → their tape's authored WALK trajectories desync (missed WATER/HARVEST all day, every day) |
| + land/geese/wheat/shed footprint | ~−10k more | SE $4k spent inside their D11-16 carry-accumulation window; my shed slots at their 98/100 peak → their wheat carry collapsed: **buys 2891→2337, sells 3067→2428** |
| goose revenue | +2.5k | ~31 eggs + ~17 fert sold (4-6 geese placed of 10) |

## Structural verdict (why it can't be fixed by tuning)
**v1112fr runs shed, cash, labor, AND spawn tiles at ~100% utilization with choreographed dependencies on all of them.** Every dollar taken during D0-D16 is a wheat-carry dollar compounding at ~30-40%; every shed slot at peak discards their crops/orders; every hired hand breaks spawn-tile assignments; every coop tile is $4k of land or a displaced wheat-rotation tile. Geese max theoretical (+flawless execution, 10 geese) ≈ +$10-12k gross vs ≥$23k displacement. Late-window variants (land D17+) math out ≈ breakeven before frictions. Their config's `bakery_capital_maximum_geese: 0` / `clone_veto_maximum_geese: 0` = **deliberate tuning, now independently confirmed** (their code anticipates geese fully: `_FR2_ANIMALS_ARG`, EGG glut weights, GOOSE product map).

**GESE ARE DEAD ON BOTH LINES.** Static tape: schedule desync (−15-25k). Reactive host: resource saturation (−23k). The "all animals" edge is real but already captured by the hybrid farm (wheat machine + cows + sheep + hands); geese are the one animal this engine prices out (fib labor, wheat-feed at carry-opportunity cost, eggs flat $50 in a deep market, fert cannibalizes their own 400/season line).

## THE REAL DISCOVERY: v1112fr's core engine is the WHEAT CARRY
Solo seed-1: they **buy 2,891 wheat cheap (D0-16, $27-32) and sell 3,067 rich (D16-30, $40-47) ≈ $33k carry profit** — plus fert 400/season (~$28k line, collected daily from cows/sheep). Their animals/melons/straw feed cash and shed into this. My v4_fr1 grows wheat and sells late — it FREE-RIDES their price pump rather than running a carry. H2H note: my wheat sells already profit from their 2,891-unit buying pressure; adding my own carry would bid up the cheap window and fight my own late sells. Any carry port needs H2H measurement, not paper math — candidate next experiment (banked, not started).

## Engine facts nailed this session (for future reference)
- Hands are day-laborers: ALL dismissed at day end, re-hired daily; hire cost = fib(n)×$1 (#11 $34, #12 $144, #13 $233, #14 $377); spawn = least-occupied shed-corner (NWSE tiebreak) — **spawn assignment is choreography-sensitive**.
- Day end: inventories auto-drop to shed (cap overflow DISCARDED), farmer respawns, hands wiped.
- LAND_ORDER NE($1k)/SW($2k)/SE($4k); their tape buys exactly NE@D6H16 + SW@D10H12, SE stays locked all season.
- Goose: $300, coop tile, eggs base 1/day + 1 care bonus (care counts only if fed same day), fert 1/day even unfed, escape after 2 consecutive unfed days, 1 animal/tile, max_held 4.
- Market depths: EGG I0=9999 (nobody sells; $50-53 flat), FERTILIZER I0=10000 (they sell 400/season, $100→$57), WHEAT their carry volumes above.
- Their hire hours: H00(237)/H01(42)/H02(3) — an overlay's own hires are index-safe at H03+.
- align_hands pads/truncates to live hand count (index-based) — extra hands PASS safely; wrapper-with-no-actions = byte-identical games (proven).
- kaggle_environments is now on PyPI including the kaggriculture env — `pip install kaggle_environments` restores the engine (was lost with /tmp wipe).

## Files
- `topbots/v1112fr_goose.py` — the port reference implementation + verdict header (kept, not for submission).
- `_ref/solo_ab_goose.py` — solo A/B harness with goose telemetry + hand-integrity check.
- `_ref/diag_v44_idle.py` — v1112fr idle-capacity/layout/cash diagnostics.
- Champion unchanged: **v4_fr1.py** (solo 110,378 / H2H 62,232 vs v1112fr).

---

# Session 5 — the H2H truth, market-entry experiments, and the architectural verdict

## THE HEADLINE: v4_fr1 is 0-12 vs v1112fr (margin −72,068/game over 6 seeds × 2 seats)
The banked "H2H 62,232" was OUR average money — never a margin. v1112fr averages $134,300/game against our shape. The user's read ("the only way we will beat top meta...") was correct and is now quantified. **Mirror match (v1112fr vs itself): both $67,026 — our $62k is near mirror-parity in our own earnings, but our farm doesn't compete in their lines, so they run a $134k monopoly against us.**

## Executed-P&L decomposition (engine monkeypatch: _commit_unit/_do_hire)
Per-game vs v1112fr (6 seeds): THEM straw $70.4k (319u), milk $55.8k (266u), wheat-carry net +$4.3k (buys ~3,032/sells ~2,982), wool $20k, melon $14.8k, fert $13k. US: milk $37.7k (185u), melon $18k, wool $14.7k, fert $12.1k, straw $6.6k (40u), wheat $2.3k. Their engine = strawberry VOLUME (39 tiles, sells from D13, avg $180-236/u in duopoly/monopoly) + early staggered cows (D6-14, milk from D14) + bought-feed wheat (market as feed supply, tiles freed from wheat farming).

## Experiments this session (all measured, honest verdicts)
1. **Goose jammer (user idea)**: their route/adaptation reads our opening — but instrumented runs show they run `default` vs us every seed (one yarn_second switch from THEIR shop draws); clone preemption NEVER fires on our flows; bakery_capital/clone_veto need BAKERY-first shop (~1/8 games). Jammer EV ≈ small. Parked.
2. **v5a (straw B+C 21 tiles)**: solo −6.1k; H2H −72.5k — NO effect on their $70k straw line (our +48u land D27-29, after their season-long flow). Market entry needs EARLY SUSTAINED supply.
3. **SE-quad strawberries (user idea, v5b)**: solo −22.7k; SE wave failed (1 tile lived) — $4k land at D15-16 + far-tile watering don't fit the static tape's cash/labor choreography.
4. **v5d/v5e (their-shape static tapes: cows D6 + early straw A0)**: solo ~79k with MASSIVE tile death (weeds ×50-67 tile-days) — the D6-D12 duty crunch is fatal on a static tape. **Their shape requires their architecture.**
5. Geese-in-reactive (Session 4): −23.5k decomposed (hires −13.1k incl. spawn-tile choreography, land/cash in their carry window −10k).

## THE ARCHITECTURAL VERDICT
Every path measured leads to one conclusion: **the static-tape line has hit its ceiling (0-12, −72k).** Beating v1112fr-class bots requires a reactive engine of our own: their farm shape (early staggered cows, 39-strawberry volume, bought-feed wheat, melons, full fert line, 11-13 hands) + reactive overlays (wheat maker, feed rescue, price-aware sell-slot reordering, terminal flush). We hold complete blueprints (decoded sources in `_ref/v44src/`) and proven wrapper techniques (goose overlay = +0.000 footprint). NOT verbatim copying their code — our own tapes as the route portfolio + our own overlay implementations.

## v6 PLAN (proposed, awaiting user GO)
1. **Skeleton**: tape-player (index-aligned, pad/truncate to live hands — their align_hands pattern, reimplemented), try/except PASS fallback.
2. **Increment 1 — shape**: author a bought-feed animal-heavy tape WITHOUT wheat-farming duties (wheat = BUY_PRODUCT only) — this removes ~40 ops/day, making the D6-D14 staggered-cow + early-straw schedule FEASIBLE (v5d/e failed because wheat duties consumed the crunch hours).
3. **Increment 2 — safety overlays**: feed rescue (H18+ anti-starvation), weed repair.
4. **Increment 3 — market overlays**: price-aware sell reordering (move sells EARLIER on price spikes — cascade-safe direction only), terminal flush.
5. **Increment 4 — maker**: wheat carry with cash/shed guards (+$4.3k/game measured for them; ours also profits from OUR feed buys as demand).
Validation: 12-seed solo per increment (shape lottery), 6-seed H2H vs v1112fr + v120 gate before advancing.

## Tooling built this session
- `_ref/h2h_pnl.py` — H2H with executed-P&L per player (revenue/cost by item).
- `_ref/eval_shape.py` — solo eval with straw/cow/weed/unfed diagnostics.
- `_ref/solo_ab_goose.py`, `_ref/diag_v44_idle.py` (Session 4); route-instrumentation recipe: `sys.modules['v44.gold_floor'].selected_route` patch + policy closure cells (`_V44_POLICY.__closure__`) expose telemetry/preemption.
- `topbots/v5a|b|c|d|e.py` — experiment tapes (all parked; v5d/e document the static-architecture ceiling).
- Champion UNCHANGED: v4_fr1 (best static line; NOT competitive vs top meta — see headline).

---

## Session 6 (9-2-2026 eve) — "chicken" swap (v5f) + engine facts + market-coupling discovery

**User ideas tested:** (1) "1 chicken + 3 sheep to confuse their opening read"; (2) "open Quad 4 for more straw plots (watered twice?)".

### Engine facts nailed down (kaggriculture.py config, fresh install)
- **No CHICKEN exists.** ANIMALS = GOOSE($300, COOP, first_yield D4, interval 1, max_held 4, EGG), COW($400, PASTURE, D8, int 2, max_held 6, MILK), SHEEP($500, PASTURE, D6, int 3, max_held 6, WOOL). With CARE: goose 2 eggs/event, cow 3 milk/event, sheep 4 wool/event (tape author's _ANIMAL_UNITS).
- **Land: NW free at start; forced order NE $1,000 → SW $2,000 → SE $4,000** (LAND_ORDER/LAND_PRICES). Starting cash $3,000. "Quad 4" = SE; needs $7k cumulative land spend → cannot open early; static tape cash schedule put it D15-16 (v5b/c) where straw wave failed (1 of 20 tiles planted).
- **Water rule confirmed:** EOD consecutive_unwatered ≥2 → WEED; planting day counts unwatered. One watering = 2 days of life → 40-tile straw farm needs only ~20 waters/day. FEED = 1 WHEAT/animal/day; consecutive_unfed ≥2 → animal dies (tile→WEED). CARE daily for max yield. FERTILIZER collect from animal tiles.
- EGG market: base $50, T332, log decay 0.2 — pristine at our volumes ($56/u realized).
- SHOPS: BAKERY[EGG,WHEAT], BRUNCH[EGG,WHEAT,STRAW], PIZZA[MILK,TOMATO,WHEAT], ICE_CREAM[STRAW,MILK,WHEAT], SMOOTHIE[STRAW,MILK], YARN[WOOL], PET_CAFE[CARROT], FARMERS_MARKET[WHEAT,CARROT,TOMATO,STRAW].

### v5f = champion spec with SHEEP:3, GOOSE:1, goose_day:0 (single-knob A/B)
- Solo 12 seeds: **105,159 vs v4_fr1 111,188 (−6,029/game; worse on 10/12)**. Cause: coop tiles eat home-quad straw (strawTileDays 3,430→2,756; straw sold 40→24u), wool volume −25%; eggs (+47u/game @$56 = $2.6k) don't cover it. Feed plan held (unfed 13 vs 12; goose fed all season). Cow buys improved 11.2→12.0 ($500 freed).
- H2H vs v1112fr (6 seeds × 2 seats): **0-12, 55,960 vs 127,919, margin −71,959** (baseline −72,068 — unchanged). WE lost $6.3k, THEY lost $6.4k. VERDICT: parked. Confusion = zero (router = their own shop draws; latches need BAKERY-first ~1/8 + COW/MELON signals we never show early; goose vetoes latches that never fire on us).

### NEW DISCOVERY — market price coupling (lockstep market entangles both farms)
Per-bot executed units/price (12-game avgs, canonical — supersedes older line-item numbers):
- Baseline: US MILK 178u @$137, MELON 121u @$150, WOOL 124u @$119, FERT 261u, STRAW 40u @$164, WHEAT 50u. THEM: WHEAT carry net +$4.3k (buy 3,162/sell 3,110), STRAW 306u @$186 ($57.2k), MILK 254u @$166 ($42.3k), WOOL 146u @$138 ($20.2k), MELON 66u @$225, FERT 259u.
- v5f: MILK price FELL for BOTH farms (US $137→$104, THEM $166→$140) with units FLAT (432→425 total). STRAW fell both ($186→$171 them). WOOL rose both ($119→$148 us, $138→$173 them; volume −5%) — **their overlay adapted by buying 5.0 sheep/game vs 4.5**. Eggs: $56/u.
- Milk-by-hour: EVERY hour ~$25/u lower in v5f run; D10-19 milk $134→$98. Whole price path shifted with flat volume → realized $/u depends on both farms' flows/timing, not just own volume. **v6 implication: sell-timing/price-aware market overlays are a real lever; solo economics don't transfer to H2H.**
- Harness note: h2h_pnl farm-identity map = farm INDEX; for per-BOT lines remap by seat (fixed script pattern in this session's inline runs — 3 bugs fixed: seat remap, op normalization ('BUY' vs 'BUY_PRODUCT'), closure scope of GAME global).

### Quad-4 verdict
Right lever (win condition = straw volume share), wrong vehicle (static tape: v5a late supply no-op; v5b/c SE land D15-16 fails; v5d/e early straw weed-cascade 1.2-1.6k weed-steps). Belongs in v6: bought-feed + reactive scheduler makes 40-50 straw tiles + SE purchase ~D10-12 feasible; mirror math says 39v39 → $24.8k each — we want ~50 tiles vs their 39.

**Status: v6 GO still pending with user. Nothing submitted.**

---

## Session 7 (9-2-2026 night) — v6 Inc 1: the pure-map build, 7 tapes, full receipts

User GO: straw-led map (quad-by-quad fully-choreographed tape, zero reactive code; price-aware sells OK).

### Tapes authored (all via tape_author3 + new default-off knobs; champion regen verified byte-identical after EVERY patch)
| tape | shape | solo 12-seed | gate |
|---|---|---|---|
| v4_fr1 (control) | champion | 111,188 | — |
| v6a | v5e + wheat_sw 0 (bought feed, isolated) | 69,605 | FAIL (feed buys cost > wheat duty saved; −3.4k vs v5e 73,028) |
| v6b | lean: 3 sheep, straw 29 (8 NW D2 + 15 NE D13 + 6 SW D15), cows D12-23 1/day | 63,578 | FAIL solo, but straw engine WORKS: 116u @$263 = $30.5k |
| v6c | v6b + cows D7-18, straw 26 | 74,605 | FAIL (milk 102u vs v6a 258u; cows-D6 milk worth +$26k is real) |
| v6d | champion + model_straw_rev 700 | 111,188 | INERT (champion B-wave plants D10 already, not D16 as thought) |
| v6e | champion + depth_over STRAW 130 | 111,188 | INERT — straw is SHED-bound, not depth-bound |
| v6f | champion + straw_stagger 3 + depth | 102,769 | FAIL — stagger perturbed D20-29 chores → MILK crashed $211→$56/u (coupled tape) |

### New knobs in tape_author3 (all default-off; .bak_pre_v6 backup)
- `wheat_sw` (0 = drop 12 SW wheat tiles; carrots exempt) — bought-feed mode
- `cow_stagger` (cows 1/day from cow_day instead of 2-day lump)
- `model_straw_rev` (wave scheduler cash model; default 350 = $87/u conservative; H2H floor ~$150)
- `depth_over` {item: k} — measured sell-depth overrides (can only deepen)
- Champion spec NOTE: true authoring spec includes explicit `ramp` [3,3,3,4,4,5,7,8,9,10x13,9x8] + straw_stagger 0 (memory's spec was incomplete).

### The four hard discoveries
1. **SHED CAP 100 (total, all items) is strawberry's hidden enemy.** Champion's D22 harvest = 52u lump; EOD shed drop admits only ~16-24u (wheat/fert/milk hog the shed) → 60% of champion straw DISCARDED → sells 40u not 104u. v6b (no wheat farming, empty shed) sold its full 116u.
2. **Wool T105 cliff is a FUNDING artifact**: same 128u volume realized $227/u (champion, patient dribble; cows D12) vs $87/u (v6a, early dump to fund cows D6 + feed buys). ±$18k swing from cash-schedule alone.
3. **The sell planner's offline price model is miscalibrated 7x**: cumulative-decay model caps straw at k*=40u; real market (I0=10,000 anchor + shop consumption) paid $263/u at 116u. But piecemeal depth patches destabilize the coupled plan (v6f milk crash) — the model needs full recalibration, not overrides.
4. **Cow timing**: D6 cows → milk 258u/$65.5k vs D12 → 185u/$39.1k (+$26k), but funding it costs the wool cliff + feed buys (~$23k) ≈ wash. The champion's D12 lump is near-optimal within the static budget.

### H2H verdict (seeds 1-6 x2 seats) — PARTIAL STRAW ENTRY FEEDS THEM
- v6b vs v1112fr: 38,578 vs **147,151** (margin −108,573) — THEIR BEST RESULT AGAINST US. Our straw $19.2k (96u), but milk $13.5k + melon $2.4k (abandoned lines) → their milk rose to $48.1k, wheat carry +$5.1k (we bought $7.8k/game feed = their counterparty).
- v6c: 48,044 vs 140,988 (−92,944). Same pattern.
- **Mirror-coupling is adversarial**: drop a line → their price/line rises; half-enter a line → crash it while holding the smaller share. Win condition = FULL mirror-parity shape (39t/306u + milk volume + carry), which needs bought-feed + reactive shed/market management = the v6 reactive-engine thesis, now with receipts.

### Status
- Best static remains v4_fr1 (solo 111,188; H2H 0-12, −72,068 — best measured static margin).
- Inc 1 (pure map) tested to its ceiling: static cannot run the winning shape (cash×shed×duty×tiles are one coupled budget); partial shapes are counterproductive in H2H.
- NEXT DECISION: (A) v6 reactive build with this session's knowledge (shed-aware harvest/sell, price recalibration as overlays — ~20 lines instead of planner surgery), or (B) static planner full-recalibration surgery (bigger job, uncertain ceiling). A is recommended.
- NOTHING SUBMITTED (per directive). Deadline 2026-09-30 (28 days).

## Session 8 (later 9-2): v6g built — Option A reactive guard tape (GO delivered)

**v6g = champion spine (byte-identical replay) + reactive guards.** Built by
`_ref/build_v6g.py` (embeds TAPE + WATER_PLAN + SHORT_DAYS; regen check passes).
`agent()` replays the tape exactly; guards only redirect PASS hand-turns or the
guard-owned extra hands; whole guard layer in try/except → pure tape fallback.

### Guards that MEASURED (kept)
- **G1 water-rescue**: tiles at cu>=1 unwatered (die at EOD). Idle-hijack hands
  (all-PASS rest of day) take abandoned tiles (no plan today/tomorrow) pre-H16,
  all at-risk H16+. **Guard-owned extra hands** (guard HIRES 11th/12th at H01,
  ~$231-376/day) see ALL at-risk tiles from H02, value-first (straw>melon>wheat)
  then farthest-from-shed (drop order). KEY: tape drops 37 planned waters/season
  (SHORT_DAYS: D12:1, D14:1, **D16:6, D19:1, D22:3, D23:11, D24:5, D25:10**) —
  hires fire on short days.
- **G2 harvest-rescue**: straw yu>=4 / age>=15, melon/wheat past window, H20+
  dying-stock salvage; day>=26 endgame = harvest-before-water + 2 hires.
- **G3 straw full-drain**: resize tape SELL STRAWBERRY to live shed content +
  H20 append. Straw sold 40u -> 66u (of 104 potential; 6 far-east tiles saved
  from D15-17 deaths, mid-zone D23-25, stragglers collected).

### Tested and DELETED: G5 cow buy-retry (3 variants, all negative)
Champion loses ~1 cow/game — but to STARVATION (EOD D15, unfed fuse), not buy
failure. Rebuy costs $400 + mission-hand contention on short days (-6u straw)
> late cow milk (+~$1.2k). Naive: -$992; H12-delayed: -$2k. Real fix = feed
rescue (v6h candidate).

### Gates
- **Solo 12-seed: v6g 115,338 vs champion 111,188 = +$4,150/game (+3.7%),
  improved ALL 12 seeds.**
- **H2H 6x2 vs v1112fr: seeds 1-6: 64,340 vs 141,932 (-77,592); champion
  -72,068. Seeds 7-12: -58,769 vs champion -57,976 (wash). Combined 12 seeds:
  v6g -68,180 vs champion -65,022 (~-$3.2k margin).**
- Mechanism: our side +$2.1k (straw 9.8k/g vs 6.6k; guard hires cost ~$2.4k/g),
  their side +$3.9k via coupling (wheat-carry arb expands, milk up). Live straw
  prices measured: healthy market $227-265 (seed 1) — our timing fine; saturated
  market $82-170 (seed 2, their 306u) — delaying sells is WORSE (falls further);
  crash is their volume, not our timing. **Coupling loss is structural.**

### Engine facts learned (verified in source)
- Sells draw from SHED only; BUY_PRODUCT/BUY_ANIMAL land in shed (fail if shed
  full); BUY_SEED bypasses shed. EOD drop order = inventory dict order, overflow
  discarded (champion's shed is nearly empty at H23 — no straw discard; the old
  shed-cap theory was WRONG, deaths were water shortfalls).
- Market = per-unit lockstep: order size walks the price intra-order; both
  players' orders interleave; 10 orders/turn.
- Shed-access tiles = (4,4),(5,4),(4,5),(5,5); hands spawn there daily at HIRE.
- Farm hands exist H01+ (H00 obs has none). Tape emits ramp[day] hand actions.
- Straw tiles die after 4th event; ~D27 H01-07 rot drains leftover yield 1/2h.
- WATCH: workspace has near-duplicate dir names (kaggressur vs kaggressur) —
  ALWAYS resolve project root mechanically (the dir containing topbots); a
  decoy was deleted this session but write_file can recreate it. Also: bash-side
  edits to _ref files can be lost to snapshot reverts between calls — apply
  patch + build + verify in ONE call.

### Verdict + fork
v6g is a strictly better farmer but H2H margin unchanged-to-slightly-worse:
the gap vs v1112fr is SHAPE (their 306u straw + milk volume + wheat carry), not
execution. Next: (a) v6h feed-rescue (the real cow-killer) + keep hardening the
spine, or (b) full-parity shape change (bought feed + 39-tile straw + reactive
market) — the original v6 Inc-2 thesis. Submission of v6g NOT requested.

## Session 9 — v6h: pure deterministic tape (full-determinism directive)

Directive: every duty mapped and executed by the tape; no reactive rescue layer.
v6h = champion spec + capacity-fitted ramp + three author-side ledger fixes.
topbots/v6h.py (110,108 bytes) — PURE REPLAY, zero reactive code.

### Build chain
1. _ref/build_v6h.py: greedy ramp fitter. Champion deficits beyond water:
   16 HARVESTS (9 on D22 alone), 6 FERT, D0 sheep PLACE+FEED, D24 DIG/PLANT.
   One bump at a time, largest deficit first, late days first, REVERT any bump
   that shifts the plant calendar (model-cash coupling). Fitted ramp
   [4,3,3,4,4,5,7,8,9,10,10,10,11,10,12,10,11,10,10,11,12,10,12,12,10,12,10,9,9,9]
   (19 bumps, ~$4.2k hire cost). Remaining same-day deficits all execute +1 day
   (carry, within the 2-day water fuse) — verified no water lost beyond +1 day.
2. Author bug 1 — WHEAT ledger drift (cow starvation root cause):
   _wheat_ledger modeled consumption as n_animals/day but the tape's chunks emit
   a different pickup count (carry-in FEED groups etc.); model shed 10 vs actual
   7 on D14 -> buy 8 short -> last unit's PICKUP clipped (engine silent min())
   -> late-hired hand's FEEDs fail -> 12th cow starves EOD D15. FIX: buy sized
   from the day's OWN pickup plan (two-pass market_plan) against a running exact
   two-tier ledger SHED_W (lo=2u/wheat-harvest for buy sizing, hi=4u for sell
   sizing; over-selling self-heals via next H00 buy).
3. Author bug 2 — pickup window: late hires' lead PASS pushed their 4th pickup
   entry (FERT) past the H01-H03 window -> silently lost. FIX: window H01-H04;
   wheat/fert sells moved H03->H04 (after the last pickup).
4. Author bug 3 — shed capacity: EOD inventory drop is capped at 100 TOTAL;
   v6h's full execution (52u straw + 42 milk on D22) overflowed -> 56 straw etc.
   discarded. FIX: exact multi-item CAP_LEDGER + H23 emergency drain (WHEAT first,
   FERT, then products) when standing+inflow > 96.

### Engine facts nailed down this session
- FEED handler: no-op if tile fed_today or actor has no wheat (silent).
- PICKUP: silent min(n, shed); hands spawn on shed-access tiles.
- _drop_inventories_to_shed at EOD: ALL inventories (farmer then hands in order)
  into the shed, overflow DISCARDED. Harvests/collects ride inventories all day.
- Animal production: EOD refresh, yield_units accumulates on the tile
  (min(max_held, ...)); HARVEST collects it. CARE bonus +1/cared+fed day,
  consumed on production day. Straw/wheat = ongoing crops, yield persists.
- SELL self-limits at shed content; order of market rows within a day is
  revenue-neutral.
- Plant-gate cash model uses FIXED (n_an+1)*26/day feed cost -> buy sizes never
  shift the calendar.

### Results (all gates)
- 12-seed solo: v6h 117,155 avg | v6g 115,338 | champion 111,188.
  v6h > champion on ALL 12 seeds (+5,967 avg; worst seed 4 106,564 vs 105,769).
  Per-seed: 118465/110477/122678/106564/116731/113022/127873/117253/124644/
  113176/125262/109709.
- H2H vs v1112fr: seeds 1-6 -68,195 (63,112 vs 131,307); 7-12 -54,944
  (49,581 vs 104,525); 12-seed -61,570 = BEST shape (champion -65,022,
  v6g -68,180). Both sides improved: our +2.9k, theirs -10.6k vs v6g.
- Animals: 16/16 alive all season (12 cows — starvation FIXED by exact ledger).
- Straw: 84u collected (champion 40), D22 13/13 tiles harvested (was 4).
- Discards remaining: ~30 STRAW + 8 MILK + 8 WHEAT + 2 MELON per seed
  (~$4-5k) — see v6h2 below.

### Known remaining leak -> v6h2 candidate (NOT built)
D22 inflow itself (52 straw + 42 milk + 16 fert + ~16 wheat = ~126u) exceeds
the ENTIRE 100-slot shed — no sell policy can fix it; the harvest SCHEDULE must
defer tiles. Design: capacity-aware harvest deferral (straw p+12 harvests
deferrable to p+15; p+16 final harvest cannot defer; milk collects stay daily;
melon/carrot/wheat no defer v1), fed by the CAP_LEDGER room estimate; planner
arrival model must then track deferrals (two-pass author or deferral feedback).
Expected value ~$4-5k/seed. One change at a time: v6h banked first.

### Files
- topbots/v6h.py — the deliverable (pure tape).
- _ref/build_v6h.py (fitter; emit block still broken — use _ref/emit_v6h.py).
- _ref/emit_v6h.py — emits v6h.py from fitted ramp + patched author.
- _ref/patch_author_v6h2.py, _ref/patch_author_v6h3.py — the author patches
  (applied; tape_author3.py.bak_pre_v6h2 = pre-patch backup).
- _ref/smoke_v6g.py — BOT=<name> env selects the comparison bot.
- NOT SUBMITTED (awaiting explicit GO).

## Session 10 — v6h2: straw deferral + sell-planner truthing

User direction: defer or switch crops to spread the D22-26 sell window; asked
about more animals. Analysis: crop SWITCH moves the spike (melon same window;
low-value swaps lose more than overflow saves); the real switch-variant is a
plant-day STAGGER (the opponent's shape); more cows marginal (+~$80/cow at
current milk depth) and add pressure on binding days. Built the deferral first.

topbots/v6h2.py (110,425 bytes) — pure tape, zero reactive code. Changes (all
author-side, via _ref/patch_author_v6h4.py):
1. Straw p+12 harvest deferral pre-pass (author()): while fixed inflow +
   4u/kept straw + 12 margin > 96, defer p+12 straw harvest groups into the
   next day (latest-in-snake first). Deadline p+14. Sell-independent (fixed
   estimates only) -> stable across passes. p+16 final harvest NEVER defers
   (tile dies; D27H00 window is 1 hour - too fragile, verified in trace).
2. Sell planner rebuilt INSIDE author() with the deferred arrival days
   (SELL_H00/SELL_H23 globals reassigned) so the depth counter tracks real
   sales (phantom sales were suppressing later straw sells).
3. Straw yield 8 -> 4 per harvest in planner AND CAP inflow model (8 was 2x
   reality).
4. Endgame H23 dump: ALL items (was wheat+fert only; milk/wool/straw standing
   overflowed on D28).

### Results (gates)
- 12-seed solo: v6h2 121,006 avg (sum 1,452,068) — ALL 12 seeds above v6h
  (117,155), v6g (115,338), champion (111,188). +9,818 vs champion.
  Per-seed: 123361/115096/123783/109526/120540/117597/131599/121670/
  128819/116855/129332/113890.
- H2H vs v1112fr: 1-6 -67,403 (64,008 vs 131,411); 7-12 -54,544 (50,044 vs
  104,587); 12-seed -61,057 — best of all builds (v6h -61,570, champion
  -65,022, v6g -68,180). Solo-dominant shape.
- Discards remaining: D20 melon 2 (trivial); D26 straw 19 (STRUCTURAL: p+16
  harvest 40u + milk event 36u same day, neither deferrable — needs plant-day
  stagger); D28 16 units (VALUE-OPTIMAL: last-day wheat dump-harvest 80u vs
  milk 36u both > shed; skipping wheat harvests nets -$120).
- Animals 16/16 alive; straw collected 84u, H00-sold 69u.

### Open items (ranked)
1. Straw plant-day stagger (v6i) — closes D26 (~19u) AND spreads sell depth;
   the opponent's volume shape; bigger redesign (v6f failed pre-fix via
   schedule shifts — retry now warranted, author is exact).
2. +2 cows variant (measurable, one change at a time; marginal solo EV,
   H2H coupling unknown).
3. SUBMIT v6h2 (needs explicit GO).

## Session 11 — submission attempt + stagger verdict (v6i) + shop-lottery discovery

### Submission
- Competition: kaggressur (id 147734), user nosiru, deadline 2026-09-30. Token
  KGAT_... is READ-scoped: 'competitions.participate' denied -> CLI submit 403.
- submission_v6h2.tar.gz (main.py = v6h2, same format as v1112_seedfix) is
  READY in the workspace root. Needs: web-UI upload OR a Competitions-scoped
  API token. NOT YET SUBMITTED.

### v6i (straw stagger 3) — built, gated, REJECTED
- straw_stagger knob already existed (v6f legacy): p += (tile_index % 3).
- Self-consistent ramp refit (calendar guard vs iteration-0). Ramp:
  [4,3,3,4,4,5,7,8,9,10,10,10,11,10,12,10,11,10,10,12,11,12,12,12,12,12,10,9,9,9].
- Also added (kept in author, spec-gated animal_critical default ON):
  ALL animal-tile groups critical (CARE/COLLECT/animal-HARVEST were silently
  droppable). And two-pass author: sell plans rebuilt from the tape's OWN
  executed harvest days (HARVEST_LOG -> prod_override) — kills planner drift
  from runtime carries.
- 12-seed solo: 113,977 vs v6h2 121,006 (-7,029). Only 3/12 seeds better.
- ROOT CAUSE (NOT scheduling — production/discards equal or better):
  **SHOP LOTTERY COUPLING.** _spawn_weeds draws rng.random() ONLY for EMPTY
  tiles; the SAME rng stream then picks the town shop (rng.choice at EOD when
  (day+1)%3==0). Any change in our empty-tile count on a draw day re-rolls
  ALL later shop draws. The stagger flipped seed 1's shop #4 from
  SMOOTHIE_SHOP to FARMERS_MARKET -> no milk consumer -> milk inventory
  overshoots I0 -> milk prices collapse ($203 avg -> $67; -$27.4k).
- v6h2 milk revenue by seed (measured): 31.8k (s2, 2 milk shops) .. 58.4k
  (s8, 4 shops) — a $26k/season lottery. Seeds 3/5: only 138/186u sold of
  ~200 produced (60u lost — separate leak, likely endgame shed overflow)
  despite $303-314 avg prices (5 milk shops).
- H2H implication: the opponent's empty-tile count ALSO consumes draws —
  both players re-roll each other's shops every episode. Explains H2H
  variance; also means shop-steering is fragile in H2H (opp-dependent).

### Standing decision
v6h2 = submission candidate. v6i rejected (shop-lottery variance swamps
structural gains). Next candidate: v6j = price-aware MILK gate (endorsed
exception: price-aware sales) — hold milk when obs price < ~$140, sell into
strength with a pile cap for shed safety; targets the weak-shop seeds.

## Session 12 — the shop-steering exploit (measured)

User direction: figure out how to control the shops so meta income falls
short while ours rises. CONFIRMED END-TO-END:

### Control surface (mechanics)
- Shop draws at EOD of D2/5/8/11/14/17/20/23 (8 total, capped).
- Each day's stream: random.Random((seed*1_000_003) ^ day); N = total EMPTY
  (None) tiles across BOTH farms consumes N rng.random() draws (weed spawn
  checks), THEN rng.choice(sorted(SHOPS)) picks the shop.
- Our lever: our empty-tile count at each draw-day EOD (hold/rush plants).
- Seed 1 map: from draw #2 onward ALL 8 shop types reachable within a
  realistic N band (30..100); each +/-1 empty tile steps the map.
- In H2H the opponent's empty count enters N too — tape metas are
  deterministic and predictable (we hold v1112fr's source).

### Measured value (forced-shop sims, v6h2 vs v1112fr)
- Solo ceiling (v6h2, seed 1): natural 123,361 -> ideal milk+wool set
  144,339 (+$21k) with ZERO farm changes.
- H2H seed 1: natural margin -83,551 -> ANTI set (YARN x4 + SMOOTHIE x4,
  NO wheat shops) margin -61,049 (+$22.5k). SELFISH set (incl PIZZA/
  ICE_CREAM) -79,883 — wheat shops feed their machine.
- v1112fr revenue mix (solo seed 1, $179k): WHEAT 39% (2,982u!), STRAW 23%,
  MILK 21%, FERT 6%, MELON 5%, WOOL 4%, CARROT 1%. Our mix (v6h2):
  milk 33%/wool 24%/melon 23%/straw 16%/wheat 7%.
- Shop share math (our% - their% per product consumed): YARN +40,
  SMOOTHIE +5, PIZZA -20, ICE_CREAM -27, BAKERY -32, BRUNCH -39,
  FARMERS_MARKET -40, PET_CAFE ~0. ANTI set = YARN+SMOOTHIE only.
- Forced-shop H2H is seed-independent (tapes + fixed shops = deterministic;
  identical money across seeds 1/2) — natural runs vary by the lottery.

### The blocker + plan (v6k)
- In-game we don't know the seed -> can't compute the N->shop map.
- INFERENCE: each observed shop draw = 3 bits; each observed WEED SPAWN
  (public farms; we know the tile -> the draw index) = a 0.5% filter —
  2-3 weeds + 2-3 shops pin the seed almost uniquely. Sweep cost is the
  constraint (2^31 x ~8us too slow; fine to ~2^26 spread across turns).
  Graceful degradation: don't steer until pinned.
- STEERING: need our EOD empty-count nudges on draw days -> author "flex
  tiles" (a plant that can slip one day cheaply) + agent wrapper that
  computes target N and holds/releases flex tiles at H23.
- Offline margin-max optimizer: greedy per-slot full-sim search over the 8
  draws vs v1112fr (current ANTI set is a first guess, not optimized).
- RISKS: episode seed size unknown (episodes API needs participate scope);
  opponent last-hour tile changes shift N by 1-2 (aim for N with safe
  windows); legality fine (all public state).
- Submission still pending user action (web upload of
  submission_v6h2.tar.gz or a Competitions-scoped token).

## Session 13 — shop-set optimizer + seed inference VALIDATED + the 31-bit problem

User direction (restated with enthusiasm): completely figure out how to change
the shops so metas' income falls short while ours rises. Executed the v6k
research plan steps 1+2.

### Harness rebuild
- `_ref/h2h_forced.py` — GameSim H2H runner + forced-shop patch (wraps
  K._end_of_day, rewrites the appended shop entry; RNG stream untouched).
  Reproduces session-12 natural seed-1 EXACTLY: ours 82,015 / theirs 165,566 /
  margin -83,551. Sims ~0.7-1s each (2 workers).
- `_ref/shopopt.py` + `_ref/shopopt_cache.json` — coordinate-descent optimizer
  over the 8 draw slots vs v1112fr, margin objective, every sequence cached
  with (ours, theirs) so any re-weighting is free. 234 sequences evaluated.

### Optimizer results (H2H v6h2 vs v1112fr, seed 1, forced shops)
- NATURAL seed-1 shops [SMOOTHIE,SMOOTHIE,FARMERS,PET,SMOOTHIE,SMOOTHIE,
  YARN,BRUNCH]: ours 82.0k theirs 165.6k margin -83.6k.
- **PIZZA set (the user's ask: ours UP, theirs DOWN):**
  PIZZA,PIZZA,YARN,PIZZA,PIZZA,PET,PET,SMOOTHIE -> ours 91.0k (+9.0),
  theirs 117.1k (-48.4), margin -26.1k (+57.5k swing vs natural).
  Mechanism: kills STRAWBERRY demand (meta's #2 product, 23% of income;
  natural set has ~37 straw-drain/day, PIZZA set ~7) while adding milk/wool
  demand (our 33%/24%). NOT a feed-cost story.
- Margin-max overall: all-BAKERY -16.8k but SCORCHED EARTH (ours 20.2k,
  theirs 37.0k) — wins margin by starving everyone; bad for our income.
- Best for OUR income alone: SMOOTHIE-heavy (ours 110.1k, +28k vs natural,
  but theirs +21k too). 85 sequences Pareto-dominate natural.
- frozen2 (slots 0-1 natural, steer 2-7): -60.7k (+22.8k) via YARN x6.
- frozen4 (slots 0-3 natural, steer 4-7): -77.9k (+5.7k) — late draws matter
  less; early pinning is valuable. Multi-start/λ-refinements still open.
- Market mechanics confirmed: shops drain market inventory each 4 steps
  (single-product shops x2); price = base ± amp*shape(|inv-I0|) — inventory
  below I0 pumps price, above crashes it.

### Seed inference — VALIDATED EXACTLY (`_ref/seed_infer.py`)
- Reconstruction (agent view, hourly public snapshots): empty-at-spawn =
  None@H0 ∪ (WEED@H0 ∧ None@H23); our own H23 PLANTs excluded (occupied at
  spawn — see plant-death gotcha below). **0 mismatches vs ground truth across
  12 seeds.** v1112fr never PLANTs at H23 (12 games).
- PLANT-DEATH GOTCHA (engine): _new_plant starts consecutive_unwatered=1, so
  an H23-planted unwatered crop dies to a WEED at that same EOD (v6h2's tape
  does this once ~D20; costs 1 seed, trivial). Dead/decayed plants BECOME
  WEEDS (not None) — board diffs must distinguish death-weeds from spawn-weeds.
- Filters: per day d, rng = Random((seed*1_000_003)^d); n_d random() draws
  (n_d = 8-30 by mid-game, ~190 on D0) with weed-position equality, then
  rng.choice(sorted(SHOPS)) == observed (draw days only). EVERY day is a
  filter (weeds spawn daily), not just draw days.
- **12/12 seeds PINNED; pin days [7,7,9,11,11,11,12,14,14,14,15,19]** ->
  steer draws D14/17/20/23 (4 draws) typically, D11 too (5) when pinned early.
- Speed: 9.2 us/candidate (pure Python). 2^20 first pass = 10s; cumulative
  pin sweep ~16s. Whole-game compute budget ~288s (0.4s x 720 turns).
  Coverage ceiling: ~2^22-2^23 comfortable, ~2^24 max pure Python.

### THE BLOCKER: live seed size
- kaggle_environments utils.py: unseeded envs (hidden state) get
  seed = random.randrange(2**31) — 31-bit, scrubbed from agent-visible
  configuration, stored in env.info["seed"] (persists into the REPLAY).
- If live episodes use this: sweep coverage 2^24/2^31 = 1/128 -> P(pin) ~1-3%
  -> steering is a lottery ticket, not a strategy.
- If live seeds are smaller (episode-id-derived etc.): P(pin) ~ 100%.
- **RESOLUTION PATH: submit v6h2, then read our episodes' replays (seed is in
  the replay JSON) and measure the true distribution.** Episodes API needs a
  submission_id — only possible AFTER first submission.

### v6k build plan (updated)
1. Author flex tiles: k tiles whose plant day can slip +1 (hold) or advance
   (plant by H21 + water by H23 — H23 plants die unwatered!). Target: +-1-3
   empty tiles at draw-day EOD, schedule-stable.
2. Agent wrapper: incremental candidate sweep (slices per turn, ~0.3-0.4s),
   daily filters, prefix-aware best-suffix shop table (from optimizer cache,
   re-optimized multi-start per prefix class), steer at H23 of draw days when
   pinned; graceful degradation to pure tape otherwise. Robustness: on
   zero-survivor contradiction drop the newest day filter and re-sweep.
3. Gates: 12-seed solo with steering (vs 121,006 bank), H2H vs v1112fr
   x12 seeds x2 seats (vs -61,057 bank).
4. Optional: numpy-vectorized MT19937 sweep (~2-4x) if seed space is 2^25-2^27.

### Decisions / open items
- Submission STILL pending user GO (web upload submission_v6h2.tar.gz or
  Competitions-scoped token). Now doubles as the seed-distribution probe.
- v6j (price-aware milk gate) remains the no-seed defensive complement.
- Optimizer refinements open: multi-start descent, lambda-objectives,
  opponent-conditioned sets (identify opponent by D5-D8 opening fingerprint,
  pick set accordingly).

## Session 14 — submission auth + THE CARROT MONOPOLY (v6h2c)

### Submission retry (user: "token should work, wrong line of code")
- Root cause FOUND and CONFIRMED: Kaggle CLI 2.2.4 + KAGGLE_API_TOKEN env var
  (new-style auth) reaches the real API, but the server itself returns
  {"Permission 'competitions.participate' was denied"} on
  StartSubmissionUpload AND ListSubmissions. The KGAT token is READ-scoped —
  not a CLI syntax issue. FIX (user, 30s): kaggle.com/settings/api ->
  Generate New Token (default scopes) -> paste new KGAT_... Then submit
  submission_v6h2.tar.gz (message ready in Key Results). Token also cannot
  list episodes -> seed-size probe still needs that first submission.

### Market engine facts (new, load-bearing)
- MARKET_PARAMS: CARROT base $35 T=450 below=hinge(target 1.0, GAIN 8 -> amp 35)
  above=sqrt(0.7); TOMATO base $60 T=200 hinge 0.40 (amp 24); WHEAT sqrt 0.80;
  STRAW/MILK linear 1.60 (steep crash); MELON/WOOL sq above (steep crash).
  HINGE: price runs away QUADRATICALLY once inventory drains past T below I0
  (carrot: $70 at 450 drained, $385 at 900, $1260 at 1350, measured $1851 D29).
- _town_consume subtracts from inventory UNCONDITIONALLY (can go negative).
- **BUY_PRODUCT is restricted to WHEAT and FERTILIZER ONLY** (silent no-op
  otherwise) -> product speculation/cornering is CLOSED BY DESIGN. Verified
  empirically (injected BUY CARROT orders = exactly zero effect).
- Shop consumption: each instance -1 per product per 4 steps (x2 if
  single-product shop: YARN, PET_CAFE). PET_CAFE = 12 carrots/day/instance.
- Non-ongoing crops (WHEAT/CARROT/MELON): yield 1 at plant + 1/2 per WATER in
  the age window [(max_yield_day+1)//2, max_yield_day] (carrot: age 2-3).
  CARROT: $20 seed, 3-4 units per 4-day cycle (~0.86/day/tile).
  TOMATO: $50 seed, first yield D8, 4 units total per tile-life (~0.35/day)
  -> STRICTLY WORSE than carrot for the hinge play (same family, worse shape).
- Engine agent files: farm["farmer"]/[x,y], farm["hands"] list of [x,y].

### v6h2c — the carrot monopoly build (first, unoptimized)
- Emitted via _ref/emit_v6h2c.py: v6h2 spec + carrot_sw 12 (SW wheat->carrot
  from ~D15) + se_day 12 / se_carrot 25 (SE quadrant carrots from D16).
  topbots/v6h2c.py (111,497 bytes). 232 carrots sold/season.
- SOLO: natural shops 91,606 (carrots worthless: $19-27) vs forced PET x8
  152,124 (carrot px D22 $342 -> D29 $1,344).
- **H2H vs v1112fr (seed 1, forced): PET x8 ours 118,565 / theirs 79,337 /
  margin +39,228 — FIRST OUTRIGHT WIN vs the top meta (natural -83,551).**
  Our carrot revenue $109,565 (232u avg $472); theirs $79,337 total.
- **THE META COUNTER-ADAPTS: v1112fr bought 20 carrot seeds and sold 57
  carrots at avg $804 ($45,855)** — its planner pivots into the boom and
  holds for the peak better than our tape. Volume still wins 232 vs 57.
- PET-count curve (margin): x8 +39.2k | x7 -36.9k | x6 -94.8k | x5 -108.1k.
  THRESHOLD EFFECT: cumulative drain must blow past the hinge knee (~450u
  below I0); our avg carrot price $472 (x8) vs $198 (x7). Full 8 needs pin by
  D2 (impossible) — realistic pins give 5-7 PETs -> the build MUST be
  optimized (levers below) to make x6-x7 positive.
- Unoptimized-build levers (est.): (1) SELL TIMING — hold carrots, dump
  D27-29 (meta gets avg $804 vs our $472; +$55-100k); (2) VOLUME — early
  carrot fields NW/NE from D2-4 (2-3x units); (3) drop cows under PET plan
  (milk $1; keep ~4 for fert); (4) shed-capacity-aware holding (cap 100).
- Fallback design (v6k): two-tape — pinned&steering -> carrot plan; unpinned
  -> v6h2 wheat plan (121k solo floor). Branch points: SE buy D12, SW crop
  D14-15 (pin-by-D12 rate ~75% at 2^23 seed space).

### Files
- _ref/h2h_forced.py, _ref/shopopt.py + shopopt_cache.json (234 seqs),
  _ref/seed_infer.py (validated), _ref/carrot_spec_probe.py,
  _ref/emit_v6h2c.py, topbots/v6h2c.py.
- v6h2 UNCHANGED (banked). submission_v6h2.tar.gz ready; waiting on a
  participate-scoped token.

## Session 15 — SUBMITTED! + seed verdict (steering demoted) + v6j rejected

### SUBMISSION: v6h2 IS LIVE (2026-09-03)
- Root cause of all prior 403/404s: WRONG COMPETITION SLUG in the old notes
  ("kaggressur"). Correct slug = the env name, kaggriculture (the
  leaderboard zip filename "kaggressur-publicleaderboard-*.csv" gave it
  away — matches kaggle_environments/envs/kaggressur). Token + CLI were fine.
- `kaggle competitions submit -c kaggressur -f submission_v6h2.tar.gz
  -m "v6h2: pure deterministic tape (capacity-fitted ramp, exact wheat
  ledger, shed-capacity drain, straw deferral)"` -> SUCCESS ("Successfully
  submitted to Kaggressur", 4 submissions remaining today). New token
  KGAT_4928574b0a229c1ab588ea864b80e09d (participate-scoped) works for
  submits. ListSubmissions 403s on both tokens (endpoint scope) — new
  submission_id unknown; get it from the web Submissions page or infer when
  episodes appear (old ids: 55716221, 55730353, 55730825, 55748620, 55754663).

### SEED VERDICT (from 313 real episode replays in analysis/episode_profiles.jsonl)
- Live seeds: min 0, max 2,143,824,838 (< 2^31). Only 5/313 < 2^20,
  8/313 < 2^24, ~18/313 < 2^26. Effectively uniform 31-bit.
- => pure-Python inference (coverage 2^22-24) pins ~2-3% of episodes;
  numpy (2^26 best case) ~6%. SHOP STEERING IS A LOTTERY TICKET, NOT A
  STRATEGY. Carrot/PET monopoly (+39k margin measured offline) is
  unreachable in ~97% of live games. DECISION: keep v6h2 pure; do NOT ship
  the steering wrapper with the banked tape.
- Self-games (our sub vs our sub) run at seed 0 (5/5 seed-0 episodes are
  "Harrison Interactive" vs itself). If we ever field 2 submissions, the
  steering build gets free live seed-0 validation games.

### v6j milk gate — REJECTED (measured, _ref/v6j_sweep.py)
- MG exists in v6h2, off: MG = {"on":0,"gate":170.0,"cap":40,"days":28}.
  Sweep gate {140,150,160,170,185} x cap {30,50}, 12-seed solo:
  gates <=160 = ZERO effect (identical per-seed money; prices never in band
  at our sell moments); gate 170/185: +199 solo avg (s2 +1,587, s12 +800)
  but H2H margin -61,398 vs -59,532 baseline (cap 30) — WORSE. Do not ship.
- The real milk leak (seeds 3/5, ~60u unsold at $303-314) is ENDGAME SHED
  OVERFLOW — author-side fix (endgame drain schedule), not a price gate.
  H2H baseline note: quick-runner seat0-only 12-seed margin = -59,532
  (proper both-seats gate was -61,057).

### Standing state
- v6h2 LIVE on the ladder (floor secured). All offline gates green.
- Next candidates ranked: (1) harvest v6h2 live episodes (validates gates
  vs real field; need new submission_id); (2) author fix for endgame milk
  overflow (seeds 3/5, ~+$1.5k solo avg); (3) park carrot/steering as lab
  results (offline only); (4) watch leaderboard drift.

## Session 16 — v6h2 LIVE (validation bug fixed) + milk-leak work

### THE VALIDATION BUG (load-bearing for every future submission)
- Symptom: upload OK, then ERROR "Validation Episode failed." (submissions
  API via curl RPC: POST api.kaggle.com/v1/competitions.CompetitionApiService/
  ListSubmissions {"competitionName": <slug>} — CLI wrapper 403s, curl works).
- Cause: kaggle_environments.agent.get_last_callable() execs main.py and
  uses the LAST callable defined in the file as the agent. v6h2.py (v4_fr1
  skeleton) ends with _milk_gate -> validation called _milk_gate(obs, cfg)
  -> TypeError on move 1. NOT size (211KB files passed historically), NOT
  the bot (local make() was perfect).
- Fix: append shim as the last function (v11xx lineage always had it):
      def _kaggle_submission_entrypoint(obs, configuration=None):
          return agent(obs, configuration)
- topbots/v6h2s.py = v6h2 + shim (110,650 bytes; behavior byte-identical;
  get_last_callable verified; self-play + seed-1 123,361 via FILE-agent
  path). submission_v6h2s.tar.gz = SUBMITTED ref 55982859 -> COMPLETE,
  provisional 600.0 (2026-09-03). Old ERROR submission: 55982322.
- ALL future emits (emit_v6h*.py etc.) must append this shim. v6h2c.py and
  any v4_fr1-skeleton file currently has the same latent bug.
- Submission history API works via curl; useful refs: our best prior
  v1131_ch3 (55947935, 1643.4). Live slug + env name derive via:
  ls kaggle_environments/envs/ | grep kagg (grep -v beginner).

### Milk-leak diagnosis (seeds 3/5) — in progress
(next section: instrumented discard/sell logging on seeds 1/3/5)

## Session 17 (2026-09-03 ~15:00Z) — v6h3 weed-guard: authored, gated, SUBMITTED

### Milk-leak root cause (CLOSED)
Weeds (p=.005/EOD on None tiles) land on D12 cow-pasture tiles ->
BUILD_PASTURE fails (tile not None) -> PLACE fails -> cows bought, never
placed. Seed 3: 4 tiles (~$19.5k); seed 5: 1 (~$3.7k); seed 1: none.
Sheep safe (D0 build precedes first EOD). Weeds NEVER spawn on structures/
plants (_spawn_weeds only None); dead plants become WEED (DIG clears those
too). PLANT rows already same-day-DIG protected by author.

### Three design iterations (one-change discipline)
1. Author-side [DIG,BUILD,PLACE,FEED] (+1 hr/site): solo avg -1,818 —
   spillover re-rolls shops (seed 6 -23.6k). REJECTED.
2. Author-side [DIG,BUILD,PLACE] (drop placement-day FEED, hour-neutral):
   solo avg +1,804 BUT H2H seeds 7-12 -16.7k avg — tiny stream changes
   cascade through the SHARED MARKET into the adaptive opponent
   (v1112fr +72k on seed 12 while WE were +34k). Escape-buffer theory
   DISPROVED (no animal escapes; counts identical). REJECTED.
3. RUNTIME GUARD (winner): v6h3 = v6h2s tape VERBATIM + reactive guard in
   player. When a unit's row is BUILD_PASTURE/BUILD_COOP/PLACE/PLANT and
   the tile under it is kind==WEED at that moment: emit DIG, replay the row
   next hour via per-unit queue (row order preserved => walks coherent).
   Clean seeds: byte-identical stream. BUG FOUND: _WG module state leaked
   across games in-process (solo gate seeds 4-12 cratered -15k..-42k) and
   keys collide across seats in self-play. FIX: key (seat, hand) + clear
   at step==0.

### v6h3 gates (all green)
- Solo 12 seeds: 8 EXACT +0; s3 +15,653; s5 +2,814; s11 +1,863; s4
  -1,980 (guard fired, shift cost > 1-cow recovery). AVG 122,535 vs
  121,006 (+1,529).
- H2H vs v1112fr 12 seeds both seats: 18/24 games EXACT; margin -60,750
  vs v6h2s -60,973 (+223). Seat-1 games have DIFFERENT weed streams than
  seat-0 (farm order consumes shared rng) — guard catches weeds solo
  can't see (seed 9 seat 1 +3,600).
- Self-play seeds 0/3 file-agent: DONE (s3: 89,437/90,123 — both farms
  recovered cows). File-agent solo s1 = 123,361 EXACT; s3 = 139,436.

### Submission
submission_v6h3.tar.gz -> ref 55984182 (2026-09-03 ~14:55Z, 3 left today).
Validation episode 105157712 COMPLETED = seed-0 self-play 57,333/56,888
BYTE-EXACT vs local. ListSubmissions status lags (None) even after the
validation episode completes — check `kaggle competitions episodes <ref>`.

### v6h2s live field (first hour)
Rating 600 -> 774.4. Public games 5-2: W Tjay Burger 116k-29k, W
jiten_topiwala 71k-52k, L Denis Zerov 78k-91k, L haruo_tensai 67k-106k,
W pocari1 101k-51k, W Gabriele Giacometti 94k-60k, W LeonDuue 72k-44k.
Validation self-game: 57,023/57,771.

### NEW FACTS (load-bearing)
- AUTHOR DRIFT: _ref/tape_author3.py NO LONGER reproduces the v6h2s tape
  (65 step diffs, D21+ hire/market rows; patches landed after the v6h2
  emit). v6h3 was built by patching v6h2s.py TEXT directly (emit_v6h3.py
  reads v6h2s, inserts guard, verifies tape verbatim). Never re-emit the
  champion from the drifted author.
- get_last_callable(raw_source_string, path=...) — takes SOURCE TEXT, not
  a file object/path.
- PICKUP/DROP work at ANY hour (no engine hour-gating; H1-4 is author
  convention). Animals escape at consecutive_unfed>=2 only; placement-day
  FEED drop is safe iff next-day FEED succeeds.
- solo gate runner: _ref/solo_gate_v6h3.py (A/B v6h2s vs any bot, 12
  seeds, PASS opponent, module-mode). h2h gate: _ref/h2h_eval.py.
- Replays: kaggle competitions replay <ep> --path /tmp/replays (fast,
  ~2s each); final money in steps[-1][p].observation.farms[p].money.

### Loss-profile intel (v6h2s's two live losses, ep 105152702 / 105153498)
- Denis Zerov (91k): diversified — sells CARROT 342, FERT 206, MELON 117,
  STRAW 161, MILK 115, WHEAT 128; board 8 wheat + 5 carrot + 4 sheep +
  4 cows + 7 WEEDS (winners lose tiles to weeds too). Carrot-heavy and
  mid-sized — closer to our parked carrot research than the top meta.
- haruo_tensai (106k): ALL-LIVESTOCK — 16 PASTURES, zero crop tiles;
  sells MILK 209, STRAW 235, WOOL 168, FERT 310 (collector), WHEAT 113;
  288 hires. Livestock-max beats our mix by 35k on that seed/game.
  Candidate study: endgame pasture conversion (crops -> pasture as straw
  fields exhaust) for a future spec knob.
- v6h3 55984182 COMPLETE provisional 600.0 as of ~15:10Z; v6h2s 727.7.

## Session 18 (2026-09-03 ~18:30Z) — carrot verdict, champ fingerprint, market engine map

### Carrot verdict (user question: is v6h2c working well?)
NO — and live data proves it can't as a monopoly. 17 live episodes measured:
- Field prices (medians): WHEAT $40, CARROT $40, TOMATO $65, STRAW $193,
  MELON $234, EGG $52, MILK $194, WOOL $186.
- Carrot price only spikes when town PET draws drain market inventory
  (PET=3 game: I 9999->9160, price $35->$311; PET<=1 games: $35-48 flat).
  Our supply CANNOT create the spike; a 37-tile field just sells $40
  carrots (0.75u/tile-day) on tiles worth more as wheat (0.9u/tile-day).
- Our bot emits a dead SELL CARROT 99 order every game (phantom from the
  shared notebook lineage; shed never holds carrots).
- Denis Zerov (91k live winner) sold 342 carrots = thin niche, not a
  monopoly play. CARROT MONOPOLY: PARKED FOR GOOD.

### Rank mechanic + submission history (CRITICAL)
- Leaderboard row = LATEST submission's rating. We are rank 4075/7503 at
  685.1 (v6h3). Old submissions don't count for rank.
- Full history: 55829084=2009.8, 55829890=1835.4, 55917889=1792.3,
  55925101=1679.1, 55947935(v1131_ch3)=1641.0 — the v1112fr-family champs.
- Fingerprint: 55829084 (2009.8) matches v1131_ch3.py / v1112fr.py 60/60
  steps on seed 703440378 (they differ only in clone_preempt_horizon 2v3).
  v115-v119_FINAL diverge at step 24 and score LOWER on the ladder.
- Old subs STOPPED matching when v6h2/v6h3 were submitted (matchmaking =
  latest 1-2 subs only). Champ 55829084's last 12 games: 3-9 (25%) — at
  the 2000 level vs HaoChi/xamad/GPTatoes/etc. 2009.8 is a FROZEN rating;
  recent form is break-even-ish vs elite.
- Field top: Crop Dusta 3004, Knight of Favonius 2951, Giulio 2951.

### Champion source EXTRACTED (readable): _ref/champ_src/
v1131_ch3.py = compressed payload; modules dumped: v24_market_maker.py
(29.6k chars), v44_gold_floor.py (40.8k), v19_terminal.py, v22_market_impact,
v22_weed_repair, v23_* (state_encoder/simulator/policy_library/planner).
The market engine ("how they run the market"):
1. WHEAT ROUND-TRIP DESK (v24_market_maker): buy wheat (batch<=60), let
   town demand drain shared inventory 1 step, sell back. Profit = Q x
   slope x town_drain. start_step 260, min profit $1, cash reserve $2500,
   feed reserve 2d, max hold 4 steps. 127 buy orders / 3,193u bought /
   3,368u sold per game (seed 1). ONLY wheat is arb-able: no shop
   consumes FERTILIZER -> no drain -> no round-trip edge (town center
   excludes fert).
2. OPPONENT-EXPOSURE FRONT-RUN (v19_terminal.terminal_market 'collision'):
   sell ordering scored by (1+opponent_exposure) x GLUT_WEIGHT x price x
   log1p(qty); exposure inferred from OPPONENT'S PUBLIC BOARD (cows->milk
   coming). They exit our products before we do.
3. ENDGAME PREMIUM FLUSH (v44_gold_floor): D26-29 dump WOOL when price>=
   base; batch-sell into strength.
4. CLONE PREEMPTION (CloneSellPreemption + clone_veto/phase detector):
   the field is full of this bot family's clones; they shift sells to beat
   mirrors (clone_streak 24, distance 2.0, preempt horizon 3).
5. Routes (v23.policy_library) selected by observable state incl. shops
   (bakery_capital, yarn_third keyed to shop prefixes).

### H2H money-flip anatomy (seed 1: champ 165,566 vs v6h3 82,015, +83,551)
- Champ avg sell prices: MELON $224, MILK $251, STRAW $247 vs v6h3:
  MELON $97 (!!), MILK $239, STRAW $257. WE dump 328 melons at half the
  price they got for 72 — price-insensitive selling is our biggest single
  leak. (WOOL: we $97 vs their $70 — we beat them there.)
- v6h3 has 30 wheat BUY orders (feed only) vs champ's 127 (desk).
- v6h3 live W/L ~4-12 in recent 16; rating 685.

### The 70% question (user: "flip the market 70%+")
No single flip exists; the market engine is 5 mechanisms. Path: (1) run
the champ chassis (2000-class, ~70% vs broad field), (2) beat it at its
own game in mirrors: melon sell-timing fix (biggest leak), wheat desk
tuning, anti-front-running. Gate = H2H win rate vs champ itself.

## Session 19 — CHAMP OPTIMIZATION PASS + SUBMISSION w6_batch30 (2026-09-03)

### Gate results: 10 single-change variants vs champ (24 games, seeds 1-12 x both seats)
- w1_batch120 (wheat_batch 60->120):   2-22, -684/g  (big market-impact regression)
- w2_early (wheat_start_step 260->120): 7-5, +2/g    DEAD KNOB — desk tried 28 early
  entries, ALL cash-blocked (cash_blocks 28 vs 0; entries/units/money byte-identical
  to champ: 90 entries, 2938 units, 157,592 seed1 vs k2900). Early game cash <
  reserve+investment; start_step not binding.
- w3_prof5 (wheat_minimum_profit 1.0->5.0): 4-6, -44/g
- w4_horizon2 (clone_preempt_horizon 3->2): 5-19, -1,725/g
- w5_exposure (exposure_preempt->True): 5-5, $0/g  DEAD KNOB — root cause measured:
  gate needs FERT price >= 0.80*base(100); local FERT median 0.52, gate open only
  25/465 turns; opponent-animals condition passes 465/465; our shed holds mean 3.4
  FERT (route already sells promptly) -> fires 2-4 turns, moves 4-8 units. Even with
  a wide-open gate there is nothing to re-time. DO NOT REVISIT.
- w7_prof05 (wheat_minimum_profit 1.0->0.5): 5-5, $0/g  DEAD (edge_blocks only ~7;
  profit bar not binding)
- BATCH BRACKET (mirror vs champ): 15: 18-6 +434 | 20: 20-4 +709 | **30: 22-2
  +1,093** | 45: 22-2 +956 | 60: baseline | 120: 2-22 -684. Clean optimum at 30.
- **w6_batch30 HARDENED on fresh seeds 13-24: 23-1, +1,141/g. COMBINED 45-3,
  +$1,117/game vs champ.** Mechanism: smaller desk round-trips -> less price impact
  per entry/exit -> better fills vs other desk bots.
- w6 vs counter-class proxies (records IDENTICAL to champ's, margins equal/better):
  k2900 15-9 +5,873 | chimera4 15-9 +1,439 | meta9 19-5 +2,978 (champ: 15-9 +5,975
  / 15-9 +1,418 / 19-5 +2,395)
- Solo vs PASS 12 seeds: w6 152,423 vs champ 152,456 (flat — change only matters in
  desk-vs-desk matchups, never worse anywhere).

### Instrumentation recipe (reusable)
- Wrapper bots embed modules via base85+zlib -> sys.modules; loading several in one
  process is SAFE (each _v44_load re-registers; each wrapper binds its own refs at
  import time; identical embedded sources anyway).
- To reach internals: walk policy closure: `for c in policy.__closure__: v =
  c.cell_contents` — find CloneSellPreemption by type name (telemetry: latches,
  preempt/exposure turns+units) and makers dict by value type MarketMakerExpert
  (telemetry: entries, entry_units, cash_blocks, slot_blocks, edge_blocks,
  deployed_cash). Champ desk vs k2900 seed1: 90 entries / 2938 units / cash_blocks 0.

### SUBMISSION (2026-09-03 18:57:30Z)
- **ref 55993148 LIVE: v1131_w6_batch30.tar.gz** (= champ chassis, wheat_batch 30),
  msg records gates. 2 submissions remaining today. Packaged as tar.gz w/ main.py
  root (proven format), smoke-tested pre-submit: solo 179,148; beats champ seed1.
- New fact from submission history: 55947935 (v1131_ch3, horizon 3) live score
  **1641.0** vs champ 55829084 (horizon 2 twin) 2009.8 — live ordering OPPOSITE to
  local mirror gate (w4_horizon2 lost 5-19 locally). Scores not directly comparable
  (different matchmaking windows; Ignat-class spread between runs) — flagged, do
  not churn horizon without new evidence.
- v6h3 55984182 now 676.9; v6h2s 55982859 657.4.

### SLUG + AUTH CORRECTIONS (load-bearing)
- **Correct comp slug = `kaggriculture`** (env name). "kaggressur" 404s — verified
  read-only via `kaggle competitions files`. /tmp/slug was WRONG (contained
  kaggressur); fixed + persisted as SLUG.txt in repo root. Note at ~line 846
  garbled the slug in its command quote. The "kaggressur-publicleaderboard-*.csv"
  filename in /tmp is misleading (renamed artifact).
- Auth: `KAGGLE_API_TOKEN=<KGAT_...>` env var + kaggle CLI (works for submit).
  ListSubmissions via curl RPC works where CLI 403s:
  `curl -s -X POST https://api.kaggle.com/v1/competitions.CompetitionApiService/ListSubmissions
   -H "Authorization: Bearer <KGAT>" -H "Content-Type: application/json"
   -d '{"competitionName":"kaggriculture"}'` (account: nosiru / Harrison Interactive).

## Session 20 — TOP-5 AUTOPSY (60 games) + endgame leak quantified (2026-09-03)

### Status
- w6 (55993148) LIVE and climbing: 1539.1 at ~19:53Z, first 12 public games 11-1,
  avg money 100,160 (vs weak schedule). 2 submissions left today.
- Leaderboard mechanic CORRECTED: rank = best of 2 active subs (Crop Dusta shows
  3007 from earlier sub, latest is 2933).

### Fresh top 5 (19:53Z): Crop Dusta 3007 | Knight of Favonius 2961 | Giulio
### Ravasio 2939 | curiosity 2915 | sbol ball 2908 (Yuan800 slid to #9).

### Method (reusable)
- `kaggle competitions team-submissions <teamId>` -> their sub ids; `kaggle
  competitions episodes <subId> --format json` (strip trailing help text: parse to
  last ']'); `kaggle competitions replay <epId> -p dir -q` (~32MB each, 880MB for
  72 — keep in /home/user/.cache, NOT workspace; /tmp tmpfs is only 993MB).
- Replays embed: info.TeamNames, info.seed, 720 steps x 2 seats
  {action{farmer,hands,market}, observation{farms,market,private}}, rewards.
- SUBMITTED orders != fills (favonius/giulio/curiosity/sbol spam ~1k/game per
  product; cropdusta submits clean ~200/game — high fill).
- All findings + table in analysis/top5_study/TOP5_STUDY.md; per-game summaries
  in analysis/top5_study/summaries_*.json + per_game_averages.json.

### Key facts (new, load-bearing)
- ENV constants: CROPS/ANIMALS dicts read from env source. GOOSE $300 coop egg/day
  from day 4 max_held 4; COW $400 milk/2d from day 8; SHEEP $500 wool/3d from day
  6. FEED = 1 wheat/animal/day (else escapes after 2 consecutive unfed). CARE
  free, +1 product on fed production days. Hands = day laborers, vanish at day
  end; n-th hire/day costs fib(n)x$1 (1,1,2,3,5,8,13,21,34,55,89,144); spawn on
  shed-access tiles. HARVEST needs age>=first_yield_day (2 for wheat) — late
  planting can NEVER pay. Fert doubles ongoing-crop (TOMATO/STRAWBERRY) yield on
  watered days only. STRAWBERRY market thinnest (T=100 linear 1.60); WHEAT
  flattest crash (log 0.20) — why the desk scales.
- Top-5 endgame: leave 0.8-2.8 wheat yield standing; 10.7-12.0 final-day hires;
  everyone banks $14-15k on the final day. NOBODY buys animals after day 24;
  geese placed days 6-13; notebook family ends with EMPTY coops (feed-stop).
- OUR LEAK: 25.5 wheat-yield left standing (12/12 games), 11.5 standing tiles,
  5.8 unspent seeds, uncollected coop yields, final-day hires 8.8. Recoverable
  ~$1,000-1,500/game for ~$322 hire cost.
- We trail top-5 mid-game (day 12: 7.9k vs 13-14.5k) but lead days 24-29 (85.1k
  vs 69.3-79.8k) — desk compounds late (vs weak schedule; treat as directional).
- Structural: we are the #1's archetype (desk hybrid). #2-5 = one copied notebook
  (identical action counts, no desk, order spam).

### NEXT
1. Endgame-completion layer on w6 chassis (stop no-payback planting, harvest all
   standing yield + coop yields, hires to 11-12 days 28-29, terminal sells).
   Offline gates: vs w6, vs proxies, solo. Then submit (2 left today).
2. v2: goose garnish (2-3 coops day ~6-10) + endgame feed-stop. Route regen.
3. NOT: strawberry mass-farm, seed-volume chase, late animals, order spam.

## Session 21 — leaderboard re-pull + new entrants = notebook clones (2026-09-03 ~21:00Z)
- Top-5 membership unchanged (Crop Dusta 3017 #1; sbol/curiosity swapped 4/5).
- New #6-8 (senkin13, lumine/薄和叶, Himanshu Kumar; all submitted today,
  rising fast) = ALL notebook-family clones (465/1130/245 signatures). Lumine's
  rising bot = family's best endgame (82k day 28).
- Replays contain NO agent source (checked 31MB files; info.Agents = name only).
- PROXY AUDIT: k2900 = weaker notebook-family member (390/1010, no desk);
  chimera4 = champ-family twin (signature identical to our chassis incl.
  wheatLeft 25) — old "champ beats chimera4" gate was us-vs-us.
- w6 live score at check: see ListSubmissions poll output above.
- All details: analysis/top5_study/TOP5_STUDY.md addendum.

## Session 22 (2026-09-03 late) — ENDGAME COMPLETION v8 → SUBMITTED 55994564
**Result: topbots/v1131_e3_routeware.py = w6_batch30 + endgame overlay → solo +$844/game (12/12 seeds positive, worst +$405), H2H vs w6 23-1 (+408/g), vs k2900 16-8 (+5,288/g). Submitted as 55994564.**

### Critical discoveries this session
1. **PHANTOM STEP BUG in local harness**: live Kaggle calls agents at obs.step 0..718 ONLY (719 calls; interpreter fires DONE at episodeSteps-2=718). scripts/sim.py driven with `range(720)` ran a phantom 719th step that (a) re-executed route[718] (harmless flush repeat) and (b) ran the day-30 end-of-day refresh → +8 phantom animal production → inflated leftover counts (38 not 30) and overlay budgets. ALL future local gates must use `range(719)`. True w6 live leftover = 30 units/game, not 38.
2. **Route plan is computable**: `_V44_ROUTES` (main file global) = dict of 5 routes × 719 actions; active route = `sys.modules["v44.gold_floor"].selected_route(obs, _V44_CONFIG)` (obs-pure). Replaying route steps from ACTUAL positions each step self-corrects drift (weed repair) → planned-harvest tile set.
3. **Terminal mechanics (live-exact)**: route[717]=DROPs+big flush, route[718]=all-PASS+terminal flush (last agent call). Units execute before market each step, but market order SIZES come from pre-action obs → **cargo must DROP by step 717** to be sold by the 718 flush. Drop at 718 = lost.
4. **Day-28 FEED+CARE is +EV** (feed 1 wheat ~$40 buys +1 day-29 product: milk $194/wool $186 with care). Suppressing it cost −$1,500/game (config H). The tape feeds correctly; don't touch days ≤28.
5. Replace-style sweeps all LOSE (v1 −5,419, v2 −1,689, sweep@710 −1,171, sweep@714 −440): the tape's day-29 choreography is near-optimal for its unit positions; far wheat (x=0 column) is unreachable by re-planning. ONLY additive wins: extra hires + PASS-slot commanding + route-aware targets + chain harvesting.
6. align_hands pads extra hands with PASS → extra hires are absorbable; command any unit whose tape action is PASS.

### v8 overlay design (all in _eg_* functions before agent())
- Steps 697-699: append HIRE to 12 hands (tape hires 9 at 696; +3 cost $288: fib 55/89/144).
- Steps 697-718: for every unit whose tape action is PASS (tape slack at 716-718 + padded extras): missions to yield tiles NOT in the active route's remaining harvest plan; unified chaining (cargo units keep harvesting while full trip fits); budget: walk+harvest+return+DROP ≤ 717; value/(need) priority, claim-on-assign, tie-break deterministic.
- Overlay wrapped in try/except→passthrough; agent() = _V44_POLICY → _eg_endgame. Entrypoint last. 104,815 bytes.

### Numbers
- Solo 12 seeds: w6 152,423 avg → e3 153,268 (+844). Leftover 30 → 6-13 (top-10 leaves 0.8-6).
- H2H e3-v-w6 24g: 23-1 (+408/g). e3-v-k2900 24g: 16-8 (+5,288/g; w6 was 15-9 +5,873).
- Determinism seed-1 ×2 identical; seat-1 games +360/+530; agent call 0.11ms.
- Files: topbots/v1131_e3_routeware.py (candidate), submission_e3_endgame.tar.gz. Obsolete: v1131_e1_endgame.py (v1-v3 replace-style, negative), v1131_e2_extrahands.py (v5-v6, collision/no-plan version).

### Next
- Watch 55994564 score (w6_batch30 55993148 = 1604.6 live at submission time). 1 submission left today.
- Follow-on v2 chassis: goose garnish + route regen with endgame-aware planting (final rotation near shed).

### Post-submission verification (21:20-21:40)
- 55994564 scored 600.0 initially → ALARM was false alarm: 600.0 = provisional rating after the self-play VALIDATION episode (deterministic bot ties its mirror exactly: 55,564 = 55,564, both DONE, zero stderr, all 719 calls clean, overlay HIREs visible in replay at the right steps).
- Replay action indexing: replay state[i+1].action = chosen at obs.step i. NO off-by-one vs local sim; local harness (719 calls, obs.step 0..718) is live-exact.
- 21:36: first PUBLIC episode completed → score 600.0 → 704.3, climbing. w6 trajectory reference: submitted 18:57, ~1604 by 21:00.
- w6_batch30 fluctuating 1645-1655 with games. Team leaderboard score = best sub.
- DELETED the 30MB validation replay + logs from workspace after inspection.

## Session 23 (2026-09-04 ~02:00-03:00) — DIAGNOSIS + THE FIX (submitted 56003197/56003198)
**User: "stuck below 1600, getting smoked." Reality: e3 climbed 600→1628.7 (rank 1255/7541; median 762, p75 1414, p90 1979, p95 2331). 1271 teams above.**

### Root cause (from 12 live replays, 02:08-01:12 window, 5W-7L):
- EVERY bot beating us = notebook-family "stable efficiency tape" engine, signature HARVEST 458-466 / WATER 1099-1158 / PLANT 249-255 (ours: 426/986/206 — champ-chassis ceiling).
- Losses break open DAYS 9-12 (gap −0.5k → −8k in one day): their melon/milk production engine + 8-15% more harvests/waters. Not endgame (that patch was correct but small).
- Their wheat-desk-style trading nets +$10-13k vs our +$2-8k; they plant 192-195 wheat vs our 134.
- We churn 1,400-1,600 wheat/game through the desk ($54-64k buys); farm-sells swing 79k-160k game to game.

### BREAKTHROUGH TOOL — sparring league (scripts/sparring_league.py):
- Replays contain info.seed. Replaying BOTH recorded streams in GameSim(seed) reproduces the live game TO THE COIN (76,447 vs 46,903 exact). Local sim + env 1.32.7 = bit-perfect live.
- => recorded opponent streams = exact sparring partners. 12-game league = our last 12 live decisions.
- e3 league score = 5-7 = exactly its live record. w6 4-8, C95 3-9.

### Candidates (public notebooks, all SHA-verified extracts to topbots/):
- c95_main.py (findings-from-zero-to-top-meta notebook, cell 54): C92 lineage hit 2836.8 live; author never submitted C94/C95. LOSES to our e3 2-22 locally (tuned for family mirror, not us).
- harvestforge_x.py (Salem Ali "2900+"): IDENTICAL tape to k2900 (390/1010, solo 181,057). e3 beats it 18-6.
- adaptive_multiroute_main.py (tetsutani 140-vote): 406/901, e3 beats it 22-2.
- E776 pkg (indarkarhana top-10 archive, /tmp/e776): 469/1138 = live-field signature; league 7-5; claims .907 vs current top-10.
- **nb3_structured_economic.py (Pilkwang Kim, live 1965): league 9-3** (loses Cary Jin, makishis; flips Harris +1.6k, Fabian +18.8k, Aurora +16.5k). Beats our e3 12-0.
- **nb3_tetsu_r5.py (tetsutani shape-the-shop r5, SHA f9ab87f3...): league 9-3** (loses smsxgz, wataru, Harris −3.7k; flips Cary Jin +122k, makishis). Beats e3 11-1 (+12,584/g), beats structured_economic 8-4. Deterministic, 0.7ms/call, seat-1 OK, 0 exceptions self-play. 290KB single file, last callable = agent.

### SUBMITTED (09-04, quota fresh):
- **56003197 = tetsu_r5** (primary), **56003198 = structured_economic** (backup rating instance). Team score = best sub.
- Note: these are public notebook artifacts (fork culture is the norm here — the entire field runs the public family). Our own edge work continues on top.

### Meta context (from public meta notebooks):
- Busya PRIME: ladder median PEAKED 2026-08-10, drifting down; field converged; margins thin (winners 92k vs losers 85.7k mean on 09-01); copying meta "buys less than it did".
- Georgy Mamarin daily replays dataset + destbreso 45k benchmark: community tooling exists for exactly this analysis.
- Kaggle ratings: new sub = fresh rating instance; needs games to converge ("episodes, not hours").

## Session 26b (09-04 ~05:00-05:30 UTC): market-timing dead end (mechanism found), boatlee submitted

**Climb**: tetsu_r5 600→2175.4 (above p90=1979, toward p95=2328); structured 1864.6→1854.4. Third submission: **56004943 = boatlee V29-R1** (validated pending at write time).

**E776 verdict (dead)**: tetsu_r5 beats E776 10-2 H2H (+2,071/g) and 8W-2L vs E776's 6W-4L on the live league. E776's ".907 vs top-10" claim doesn't hold. No slot.

**Market-timing overlay (r6) — DEAD END with mechanism** (topbots/tetsu_r6_batchsell.py, keep for reference, do NOT submit):
- Favonius autopsy: identical sold volumes, better realized prices (MILK 39 vs our 21, WOOL 57 vs 46, STRB 201 vs 193). They batch 12-15 units at local price peaks (~daily, at inventory troughs); r5 dribbles 6 every ~12 steps, chronically flooding (+15-20 inventory). Both engines play IDENTICALLY until s433 — same family, only late-game sell cadence differs.
- r6 overlay (strip gated sells from s480, batch at rolling-48-max peaks, flush 712): league 5W-5L, ALL 10 margins worse by −460..−6,674. Mechanism: **shared-market zero-sum — holding subsidizes the opponent**. In ra5anchor game: our revenue −364 but THEIR revenue +3,642 (they sold into the price recovery our holding created). Also shed runs 76-97/100 late-game (no headroom to hold). Hindsight deferral sim also negative (FERT floor trap: held to end, price 1).
- Realized prices DID improve (STRB 110→136 avg) but the gain is donated to the opponent. Any hold-for-price overlay is exploitable. Do not retry without a fundamentally different design (e.g., dumping INTO opponent's peaks to deny them price — untested, low ceiling).

**ra5anchor loss autopsy (−99)**: led +1,732 at s715, lost it in s716-718. NOT a dump-timing issue: both sheds nearly empty at 718 (the 1M/500-qty catch-alls are aspirational). They simply out-earn us in the last 5 days (revenue bursts +1,774 @s713, +1,666 @s716 — they batch-sell). Endgame production/ops identical (HARVEST 466=466, WATER 1115≈1113, hires 287=287). Their edge = compiled-in sell cadence + endgame logistics; not overlay-recoverable.

**r5 determinism note**: the "+1,345 vs −99" scare was MY measurement bug (day-boundary money snapshot at s696 vs true final at s719). r5 is bit-deterministic across processes/repeats. Final-day collapse (−1,444 in 23 steps vs ra5anchor) is real but ends near even. LESSON: always measure margin at s718, not last day-boundary.

**boatlee V29-R1 (56004943)**: extracted from kernel boatlee/v29-r1-adaptive-market-hysteresis (payload = zlib+base64 in cell, archive SHA-verified 8dc51291...). League **9W-1L**: markastra +24,890, akmr +20,632, Batuhan +15,535, Wufang +26,161, srijan +9,277, Xinyi +23,581, lime0001 +16,315, One-For-All +905, Favonius **−9,339**, ra5anchor **+42,602**. But tetsu_r5 beats it **12-0 H2H (+36,942/g)** — counter-style bot: crushes the field's mid/bottom, folds to tetsu's style and to Favonius-family. Submitted as free second ticket (team score = best sub; author live-rated 2105.9). File: /tmp/boatlee_agent/main.py (volatile) + submission_boatlee_v29r1.tar.gz (workspace).

**salemali7 2900 kernel**: weak — league 2W-8L, 12-0 to tetsu. Dead.

**Remaining unexplored public kernels**: romantamrazov/hamburger (v129, pulled to /tmp/kp_hamb, not yet tested), Arlene farming-score-v3, Anas Riaz 45v, renji_starfall agent-builder, kaitofukami v48-fast-routes (v130).

**Submission state**: 3 used today (tetsu 56003197 2175.4↑, structured 56003198 1854.4, boatlee 56004943 pending). 2 left today.

## Session 26c (09-04 ~05:30-06:15 UTC): fight card vs v29-r1 -> v4b posted (56005825)

User gate: "fight upgrades vs published v29-r1; if we beat it, post; else keep optimizing."

**Fight card (20g H2H, seats alternate) vs boatlee v29-r1:**
- r5 baseline: 20-0, +37,171/g (range +18,223..+56,595)
- terminal v3: 20-0, +37,177/g
- v4 (v3+collect-ban+718-rebuild): 20-0, +36,694/g — but v4 LOSES mirror to r5 1-15 (-488/g) and league -280..-588 on all 10 games. REJECTED.
- Isolation: v4b (v3 + 718 catch-all rebuild ONLY) = strictly >= v3 everywhere (+1..+9 league, +4 extra ra5anchor, zero regressions); v4c (collect-ban only) = -271..-587 on ALL games — **the library's late COLLECT_FERTILIZER ops are productive choreography; banning "unbankable" ones is NET-NEGATIVE. Dead end, do not retry.**
- **v4b final: 40-0 vs v29-r1 across two seed sets (+37,177/g, +36,271/g); mirror vs r5 dead-even (2-14, -0/g); league >= r5 on all 10. GATE PASSED -> POSTED as 56005825** (submission_tetsu_r5_v4b.tar.gz, main.py sha256 5d8031fe...; source: topbots/tetsu_r5_terminal_v4b.py). 4 submissions used today, 1 left.

v4b overlay (on top of r5): bank carried units from 715; kill dead ops (WATER/CARE/COLLECT_FERT/DIG) from 716 with budgeted harvest trips; PASS units get harvest missions; at 718 rebuild market to exactly 9 catch-all SELL 1M (one per product — dominates all smaller sells, drops wasteful last-step HIRE/BUY; r5 itself never hires 716-718 so no downside observed).

**Climb at 06:15 UTC: tetsu_r5 2202.4 (still rising), boatlee v29-r1 1262.7 (fast start, 9-1 form), structured 1846.1, v4b pending validation.**

League table (10 live games) r5 -> v4b: markastra +18,233->+18,234, akmr +1,456->+1,457, Batuhan +10,524->+10,525, Wufang +6,031->+6,032, srijan +2,535->+2,536, Xinyi +52,443->+52,452, lime0001 +44,563->+44,564, Favonius -3,861->-3,860, ra5anchor -99->-95, One-For-All +4,824->+4,825. All >=, zero regressions.

## Session 26d (09-04 ~06:15-07:15 UTC): market angles -> v6 adaptive peak-join POSTED (56006184)

User: "Keep optimizing. Adding/removing/changing steps / other angles of crops / buying/selling."

**Market mechanics established (from interpreter source):**
- No shop consumes FERTILIZER; TOWN_CENTER excludes it. Fert inventory NEVER drains (only rises; $1 sales don't even add). Fert price falls monotonically 100->1 every game. **Fert market-making = DEAD** (buy at any price = guaranteed loss).
- WHEAT is the opposite: 5/8 shop types + town center drain it; inv 10,000->9,640; price RISES 25->44 over the season. BUT the library ALREADY trend-trades it (holds 60 wheat mid-game, sells 42+) and its hire ramp runs at ~$25 balance at s24 (5 hires/step-1 group). Stripping early wheat revenue starves hires. **Wheat-carry overlay = DEAD.**
- Library hire pattern: 5-6 hands at s1 (spends ~$370), then 5/step at s24/s48/... spending to ~zero every day. Money-flow is fully committed; never defer early-game revenue.

**v5 peak-join (unconditional):** at rolling-48 price max (within $1), dump extra 6 shed units of MILK/WOOL/STRAWBERRY (s288-710, 8-step per-item cooldown, append-only, market-only = production-safe). League vs v4b: Favonius +1,446, One-For-All +410, markastra +177, but -23..-275 vs 7 lighter sellers. Net +1,177/10g. Mechanism = REVERSE of r6's failed hold: join the peak (capture it + crash it for the batchers) instead of holding for it (which donated recovery).

**v6 adaptive peak-join** (topbots/tetsu_r5_v6_adapeak.py, SUBMITTED as 56006184, tarball submission_tetsu_r5_v6.tar.gz, main.py sha256 2377229b...):
- Classifier: opponent batch = inventory jump >= 9 units across a step minus our own sold qty (their_est = d_inv - our_prev); arm per-item after 3 events in 168-step window. (Initial bugs fixed: (a) reassigned globals without `global` -> UnboundLocalError swallowed by try/except = silent no-op; (b) compared d_inv against wrong step's sells.)
- Param sweep (arm, jump, batch): best = arm 3 / jump 9 / batch 6: league **+1,300/10g vs v4b** (Favonius +1,446, One-For-All +563, markastra +63, seven small losses -16..-210). Stricter (arm3/jump11) +497, softer (batch4) +932.
- Validation: **mirror vs r5 15-1 (+621/g)**; **fresh-seed H2H vs v4b 16-0 (+890/g)**; **gate vs boatlee v29-r1 40-0** (+37,035/g and +39,554/g on two 20g sets). Smoke full-game clean.

**Submissions today: 5/5 used.** Live at ~07:15 UTC: tetsu_r5 2202.4 (best), structured 1839.9, boatlee 1503.3 (fast), v4b 962.8, v6 600 (just started). Team score = best sub; v6 is expected to pass tetsu_r5 once it climbs (mirror +621/g over r5).

**Ideas not yet tried:** hamburger kernel (v129, in /tmp/kp_hamb, not extracted); kaitofukami v48-fast-routes (v130); Arlene farming-score-v3; Anas Riaz 45v; renji_starfall; extending peak-join to MELON/EGG/TOMATO/CARROT; denying WHEAT peaks (batchers dump wheat late); arming detection earlier via price-crash signature instead of inventory jumps.

## Session 26e (09-04 ~07:15-08:10 UTC): goose autopsy + 44-combo veto sweep -> v7 READY (unsubmitted, quota 5/5)

**Goose question (user saw goose placed d12 gone d17 on v4b):** CONFIRMED mechanism: `consecutive_unfed >= 2` -> animal escapes (structure remains). The library's feed waves NEVER cover foreign geese (0 FEED ops on coop in probe). NOT fixed in v6 (market-only overlays can't fix feeding). **Adding geese is -EV**: egg math = 13 eggs x $51 = $663 vs goose $300 + wheat ~$240 + ~50 hijacked unit-steps (~$350) < 0. Goose probes: market-buy-only = library ignores shed geese (goose rots in shed, -$300); unit-hijack placement (fixed PICKUP-on-shed-tile bug) places it but it starves in 2 days. Also: library builds exactly 1 COOP (~s255, empty all game) in every league game; buys 7 COW + 6 SHEEP (identical every game); places 9+9; zero escapes of ITS animals; 361 FEED ops. CLOSES the add-geese line with numbers.

**44-combo veto sweep (H2H vs v6, 2 seeds each):** library plan is superbly tuned — every firing veto is NEGATIVE: HIRE>=576..696 (-1.6k..-22.7k; late hires PAY via endgame harvest rush), SHEEP/COW any (-1.4k..-107k), LAND>=240 (-20.6k), SEEDWHEAT>=480 (-6.6k). Most thresholds never fire (all buys happen early). **The one crack: BUY_PRODUCT FERTILIZER** — library buys ~63 fert/game ($2,316, price 90->1) for FERTILIZE ops that don't pay.

**v7 = v6 + strip ALL BUY_PRODUCT FERTILIZER** (topbots/tetsu_r5_v7_nofert.py, tarball submission_tetsu_r5_v7.tar.gz READY, sha256 a01fd20f...):
- 8 fresh-seed H2H vs v6: **+482/g avg, positive on all 8** (+217..+725); price-gated versions weaker (block-all is best — even $1 fert buys lose).
- League (10 live games): +700 net (+70/g; 5 up 5 small down — conservative estimate; field opponents don't buy fert so no demand-donation offset there, while tetsu-family opponents do -> the +482 applies vs the top of the ladder).
- Mirror v7 vs v6 (16g): **13-3 (+221/g)**. Gate vs boatlee v29-r1: **20-0** (+33,899/g). Full-game smoke clean.
- NOT SUBMITTED: 5/5 quota used today. SUBMIT AS FIRST SLOT AT UTC MIDNIGHT RESET.

Live at ~08:10 UTC: tetsu_r5 ~2200s, boatlee climbing through ~1500s, v4b/v6 climbing from ~600-1000.

## 26f. GOOSE PACKAGE (v8) — MEASURED, DEAD (09-04)
- Built v8 = v7 + goose package overlay (buy s256, PLACE mission, FEED mission every-other-day on unfed==1 & !fed_today, hour 14-20, wheat guard >=2, empty-handed-unit hijack).
- Instrumented replay ep 105354420: goose bought s256, PLACED s273 — then FEED mission expired (deadline step+10 too short) → escaped d12. 
- THE KILLER NUMBER: v8 vs v7 differed on only **19 steps** (days 10-12 only; identical after) yet final margin diverged **−12,452** (−300 immediate goose cost, rest = permanent compiled-policy desync cascade from hijacking units during strawberry peak; policy never re-plans). Compare v7's fert veto: market-order-only change, safely +482.
- Verdict: any unit-action overlay carries −1k..−12k tail risk; max goose egg revenue ~$800. Third and final proof geese are −EV for us. v8 renamed `topbots/tetsu_r5_v8_goose_DEAD.py`.
- Rescue-overlay line also CLOSED: library never buys geese on our seeds (0/28 live eps), and if it did, ~80-100 feed-hijack steps would trigger the same desync cascade.
- LIVE OPPONENT GOOSE TIMELINES (step-level): itsrainnnnn ep 105374758: 1 goose s287 (d12 h23) → s719 END, fed 326/433 steps; we won +98,305. Taras Sam ep 105380009: 2 geese s225 (d10) → END, fed 297/495 steps; we won +57,849. No goose ever vanished; both opponents fed all game and still lost big. User's live goose sighting = opponent's goose, not ours.

## 26h. GOOSE WAR II — FIVE ARCHITECTURES, SURGICAL ISOLATION, CLOSED FOREVER (09-04 pm)
User push: coop sits empty all game ("wasting a spot"); crop dusta (#1) runs geese as main line; "change walk order/job duties if need be".
- Engine intel (fresh): HIRE is a MARKET order, cost fib(hires_today) ($1 first-of-day); hands are DAY-WORKERS (farm["hands"]=[] every night, engine line 880); overnight all inventories drop to shed + farmer teleports home; unit actions execute BEFORE market in a step; PICKUP/DROP valid on the 4 center shed tiles; new hands spawn ON shed tiles; FEED consumes 1 wheat from unit inv (double-feed = no-op, no waste); CARE sets cared_today, bonus only pops on fed production day; eggs cap at 4 on tile (max_held); escape at consecutive_unfed>=2; yield accrues even unfed.
- Library idle map (v7 vs v6, 3 seeds, identical): hours 0-18 ~0% idle; h19 9%, h20 13%, h21 21%, h22 36%, h23 67%. Coop appears s256 (d11 h16) every seed. Library hires ~9-12 hands at h0 daily (214/287 hires at h0, 72 at h1).
- RESULTS (all on seed 9301 vs v6, v7 baseline +612):
  * probe: 1-step forced PICKUP on farmer = FREE (delta exactly -$300 goose; v7 instantly drops it back — treats goose as cargo).
  * v8 blind hijack (19 steps, strawberry peak d10-12): -12,452.
  * v8b polite PASS-only missions (tug-of-war, never placed): -2,549.
  * v8d morning-steal (continuous override of fresh h1 hand; place s271 FREE, feeds d12/d14): -6,242; feed steals cost ~-$1,200 each.
  * v8f wheat-credit (pre-bought wheat, library supply untouched): IDENTICAL -5,846 => wheat was NOT the cost driver.
  * v8g NO-OP (buy + place + ZERO intervention; goose starves d13): **-2,117 flat** — the -$1,500 hits d12 (first full day of goose presence), then persists. THE LIBRARY ITSELF DERAILS when a goose occupies the coop.
- VERDICT (5 architectures, each isolating one variable): compiled tetsu policy is so state-optimized that even a PASSIVE goose on its own coop costs -$1.5-2.1k > goose ceiling (+$714 eggs -$300 bird = +$414 theoretical). Geese only pay for policies TRAINED with geese (crop dusta). Overlay geese on our library: IMPOSSIBLE to make +EV. The empty coop itself costs ~nothing (baked into plan).
- User-facing conclusion: keep coop empty; goose meta advantage belongs to native-goose policies; if meta shifts to geese, our counter is our proven crop/shop engine + possibly egg-price decay tailwind (flooded egg supply lowers their revenue).
- Files: topbots/tetsu_r5_v8{b,c,d,e,f}*_DEAD.py (all preserved with _DEAD suffix). v7 UNTOUCHED.

## 26i. OPTIMIZATION SPRINT — v10 FOUND (09-04 ~16:00 UTC)
External kernels (fought vs v7, 8 seeds alt seats):
- romanrozen/strong-barnyard-economist embedded "top agent" (adaptive-preempt-3x2x1 route+preemption controller, 27k chars): v7 wins 8-0, +27,378/g. Two tiers below us.
- romantamrazov/hamburger anchor (Tran H Hoang tape from ep 89674601): v7 wins 8-0, +37,453/g. (Hamburger = tape+overlay builder; terminal-relay-716/717 experiments = same ideas as our v4b.)
- kaggressur slug NOTE: renders confusingly; always derive via competitions_list(search="kaggr").ref programmatically. Token scope: kernels_pull works for some kernels, 403 others; competition_submissions + get_submission_limits 403; leaderboard_download + list_episodes + episode_replay OK.

Unit/workforce interventions (all DEAD):
- v9a/b/c late-hire boosts (+1/+2 hand at h1 d12-28, cost $21-55/hire): 0-8 vs v7, ~-$200/extra hire (fib cost + plan disruption). The compiled policy hires exactly its optimal workforce; extra hands idle/disturb. Files *_DEAD.
- Waste hunt: ZERO orphan seeds (all buys planted; 3 wheat seeds left ~$15), end shed EMPTY (terminal relay sells all). The market-order waste class is fully mined — fert veto was the only leak.

ADAPEAK RETUNE (v10 = v7 + _PK_BATCH 6->20, _PK_DETECT_JUMP 9->6; file topbots/tetsu_r5_v10_adapeak.py):
- One-at-a-time sweep (8 seeds): BATCH monotone 4:-154, 8:+160, 10:+307, 12:+408, 16:+538, 20:+573; JUMP 6:+310 (12:-197, 4:+746 w/B16); ARM 2:+180 (4:-91); WINDOW 120:-86, 216:+104 weak.
- Combos: B16+J6 +838; B20+J6 +868 (peak); B24+J6 +854; B20+J6+A2 +863; B16+J6+A2 +831.
- HELD-OUT 16 fresh seeds (9951-9981): v10 vs v7 **16W-0L, +986/g** (all margins +319..+1,769).
- League 10: 8W-2L, net +83 vs v7 (neutral vs field; Favonius +994 = the exploitable dumper; small losses -50..-480 elsewhere).
- Gate vs boatlee v29-r1 (same 20 seeds as v7's gate): 20W-0L, +30,099/g (v7: +30,267 — no regression).
- Mechanism: adapeak arms when opponent makes >=jump-unit sells of an item (3 events in 168 steps), then front-runs the elevated price (their dump drains shared inventory -> price rises) with a batch sell. B20/J6 captures ~3x more of the spike. Gains concentrated vs dump-heavy opponents = the TOP OF THE LADDER (tetsu family, boatlee family, structured). Neutral vs weak field.
- VERDICT: v10 = new champion, STRICTLY >= v7 everywhere, >> vs top meta. TONIGHT'S SUBMISSION = v10 (submission_tetsu_r5_v10.tar.gz, sha256 82f00924bbc4786c, smoke 162,812 vs 3,000). v7 tarball stays as fallback.

Sandbox ops note: recycles ~hourly (wiped /tmp + pip). Each turn: reinstall kaggle+kaggle-environments, rebuild /tmp/ws via >100-items rule, re-download league eps (ids above) / re-extract boatlee from workspace tarball when needed.

## 26j. ADAPEAK2 — v11 NEW CHAMPION (09-04 ~17:00 UTC)
v11 = v10 + _PK_WIN 48->36 + _PK_ARM_THRESHOLD 3->2 + terminal relay 718->717 (episode_steps-3). File topbots/tetsu_r5_v11_adapeak2.py; tarball submission_tetsu_r5_v11.tar.gz.
- Adapeak mechanics (code-read): watches _PK_ITEMS=(MILK,WOOL,STRAWBERRY) shared-market inventory; opponent dump >=JUMP(6)/step logs event (window 168); armed at >=ARM(2) events; fires SELL min(BATCH,20,have) when price >= 48->36-step max -1, cooldown GAP(8), steps 288-710; relay: last-turn catch-all sells all products (now at 717).
- v11 vs v10: tuning 8-0 +254; HELD-OUT 16 seeds 15W-1L +232/g. v11 vs v7 (full stack) held-out: 16W-0L **+1,109/g**. League 8W-2L, +50/10g vs v10 (neutral; Favonius +513). Gate vs v29-r1: 20W-0L +30,017/g.
- Extension sweeps DEAD/INERT: +MELON/+CARROT/+TOMATO items inert (never arm); +WHEAT CATASTROPHIC -17,621/g (wheat = library conversion fuel, never touch); WIN 24/30/72, GAP 4/6/12, END 715/718, START 240, B16/24/28 all flat-or-worse under v11 config => local optimum at (B20,J6,W36,A2,G8,R717).
- TONIGHT'S SUBMISSION = v11 (slot 1, 00:00 UTC). Fallbacks: v10, v7 tarballs ready.

## 26k. FAVONIUS MINE + EXHAUSTION OF OVERLAY CLASSES (09-04 ~17:45 UTC)
Favonius replay (ep 105354420, seed 1345661995) instrumented vs v11 — corrected sells (cap at shed):
- ITS ECONOMY: raw-spike seller. STRB 355 @ $201.0 (base 120!), WOOL 262 @ $105.3, MILK 364 @ $55.7, MELON 72 @ $209.8, FERT 384 @ $41.8 (320 of 384 collected from own animals — NOT market-making; buys only 64). Total raw sell revenue 166.6k.
- OUR ECONOMY: shop-conversion engine. Raw sells only 51.6k (STRB 92 @ 186.4, WHEAT 311 @ 42, FERT 253 @ 35.5 via COLLECT_FERTILIZER from animals) — yet final money ~equal (margin -967). The balance of our revenue is shop-conversion payouts (invisible to sell logs). Two different economies, near-equal outcome.
- Its edge is FARM MIX (4-6x our strb/wool/melon volume) + deeper spike-holding. Farm mix = compiled, untouchable (seed-flow changes hit the desync law).
DEAD ENDS this round: depth-gated adapeak fires (require price >= 1.2-1.5x 36-step min): -1,782/g all multipliers (kills too many fires). ARM=1: +71 weak 2W-6L. Peak-tol -2/-3, HISTLEN 4, START 252/264: noise/inert. Wheat dip-buying: moot (we are net wheat SELLER, 311 sold vs 141 bought by Fav).
CONCLUSION: overlay space on the compiled base is exhausted. Positive levers found and stacked: fert-buy veto (+482), adapeak B20/J6 (+986), WIN36/A2/R717 (+232) => v11 = +1,109/g vs v7, 16-0. Everything else in the market-order/unit/state classes: negative or inert. v11 SUBMITS TONIGHT (00:00 UTC) as slot 1.
Submission runbook (sandbox recycles hourly): pip install -q kaggle kaggle-environments; export KAGGLE_API_TOKEN=<token from tmp_logs/Chat-Log-13.txt>; slug via competitions_list(search="kaggr").ref (never hand-type); api.competition_submit(slug, "<W>/submission_tetsu_r5_v11.tar.gz", "tetsu_r5_v11 adapeak2 W36A2R717"). Verify with competition_list_episodes after.

## 26l. GOOSEBOT PROJECT — FROM-SCRATCH CROP DUSTA LINE (09-04 18:15-21:30 UTC)
User order: keep v11 champion; build from-scratch goose bot on CD's model; fight vs v11.

### ENGINE LAWS DECODED THIS SESSION (permanent, verified vs installed engine)
- WATER: every plant EVERY day incl. PLANTING DAY (starts consecutive_unwatered=1; 2 -> WEED overnight, no grace). Yield bonus only in window [(myd+1)//2, myd] (+1, +2 fert), capped max_yield.
- DIG clears weeds (and plants/empty coops). Weeds block BUILD/PLANT. weedSpawnChance 0.005/tile/night.
- LOCKED tiles are WALKABLE; tile ops no-op there. None == unlocked+empty. Quadrants: NW free, BUY_LAND NE(1000)/SW(2000)/SE(4000), farm["unlocked_quadrants"] = ["NW", ...].
- HIRE cost = 1 x fib(n_today) (farmHandCostMult=1!): 12 hands = $376/day. Hands are DAILY: roster+inventories wiped at day refresh; rehire every morning (burst at h0-h3); farmer teleports to default spawn (4,4); carried goods auto-drop to shed.
- Market ops: HIRE/BUY_LAND/BUY_SEED/BUY_PRODUCT(WHEAT|FERT only)/BUY_ANIMAL(any, lands in shed)/SELL (from shed). maxMarketOrdersPerTurn=10 — order list gets TRUNCATED; don't let sells crowd out hires.
- Animals: FEED = 1 WHEAT from unit inv -> fed_today (2 consecutive unfed refreshes -> ESCAPE, structure remains). CARE free -> pending_care_bonus +1 yield on next FED production day (doubles output). Every animal: 1 free FERTILIZER/day (COLLECT_FERTILIZER, refreshes daily). FERTILIZE: 3 days, +2 window water bonus.
- Ongoing crops (TOMATO fyd8/int1, STRB fyd10/int2): accrue +1/day (2 if fert+watered) after fyd, cap max_yield HELD=4, harvest >= 2, plant once water forever. $60-120/tile-day.
- HARVEST at maturity for non-ongoing (wheat age>=4). Coop eggs: harvest yield>=2 (max_held 4).
- obs: farms = BOTH farms indexed by seat; use obs["player"] (v11 pattern). private per-seat. My GameSim is faithful on seat 0 but SOFTER than real engine on feeding (real engine escapes more; sim showed stable geese, real churned) -> tune on real engine via battle_harness.

### GOOSEBOT STATUS (topbots/goosebot_v0.py = dev history, goosebot_v1.py = current v2.3)
Working: wheat/carrot backbone; 6 coops d3-6 (ring next to shed); 6 geese d5-10 (BUY_ANIMAL->shed->PLACE top priority); 1-3 feeder units with fixed coop split (FEED->CARE->FERTILIZE->EGGS->COLLECT circuit); stripe zoning (vertical column bands); hires burst h0-h3; sells h22; crop ladder wheat->carrot->tomato(d8-23)->strawberry(d11-20); endgame cutoffs; seat-aware.
vs PASS (real engine, seeds 10001-4): $0.8-4.7k, mean ~$2.8k, high variance. Geese churn on real engine when shed wheat hits 0 (feeder now harvests wheat directly when shed dry).
**vs v11 (6 seeds x 2 seats): 0W-12L, avg margin -149,280. v11 $115-186k local. NOT COMPETITIVE — v11 stays champion, no ambiguity.**
Gap analysis vs CD's 85k: (1) wheat volume 8-16 tiles vs CD ~40-60 fertilized (max yield 6 = +50%); (2) ZERO shop logic (CD+v11's invisible engine); (3) unit idle ~30% + walk 43%; (4) no cows/sheep side-animals. Roadmap if resumed: capacity plumbing for 40+ tiles, shops layer, tighter routing.
Seeds 10001-10006 now burned for goosebot fights.

### V11 SHIP (unchanged, tonight 00:00 UTC)
Tarball verified: submission_tetsu_r5_v11.tar.gz. Runbook §26k. Goose line does NOT affect the ship.

## 26m. GOOSEBOT V3 BREAKTHROUGH SESSION — WEED-CLAIM TRAP + FERT RUNNERS (09-04 21:00-22:00 UTC)

**Ladder vs PASS (seeds 10007-10016, both seats):** v3.5 $11,501 → v3.8 $12,323 (day_cap planting + emergency BUY_PRODUCT WHEAT + ripeness gates d27/d26) → v3.9 $13,517 (harvest→water claim fall-through) → v3.15 $14,407 (plant cap 13/16, p_max −2×animals) → v3.17 $14,744 (6G+4C+3S) → v3.28 $14,510 10-seed robust (**weed-claim trap fix**; 10016 seat1 $2,822→$13,375!) → v3.30 $14,878 (6G+6C+3S) → **v3.32 $15,294, min $11,981 (fert runners + dying-gate)**. v2.3 was $2,828 — 5.4×.

**ELIF TRAP FAMILY — 4 variants now catalogued (all killed units to PASS):**
1. structure-build with no spots (v3.0) — fix: `and spots` in condition.
2. harvest_jobs truthy but all claimed → water skipped (v3.8) — fix: fall-through cand checks.
3. **weed_jobs truthy but all claimed → coop/pasture/fert/PLANT all skipped (v3.28 fix: `weed_cand = stripe_jobs(...)` then `if weed_cand:`)** — this one caused the 10016-seat1 $2.8k poverty spiral (planting dead d16-20 on weedy half-locked boards).
4. visit-completion (v3.10-11): pinning a feeder at one animal for CARE/FERT while others starve — reverted; plain priority circuit wins.

**Laws learned this session:**
- Non-ongoing yield: plant starts yield=1; WATER in window [(myd+1)//2, myd] adds +1 (+2 if tile fertilized_today) capped max_yield. WHEAT window ages 2-4 → 4 plain / 6 fert. Harvest allowed age ≥ fyd(2); throughput ~neutral across harvest ages → harvest at myd (fewest seeds/plant-ops).
- max_held: GOOSE 4, COW 6, SHEEP 6 — collection (HARVEST on animal tile) lag tolerable ~1 day.
- Shed cap 100 destroys EOD overflow; guard at load > 88 sells down to 82 (v3.16, no-op so far but cheap insurance).
- Locked boards: EVERY seat has locked quadrants (10007 seat0: 2 coop-ring spots locked; 10016 seat1: rows 5-9 all locked). Coop ring caps geese at 4 on such seats — ACCEPTED (v3.17 proved 4-geese games still hit $16-19k; fallback second-ring coops were tried 4 ways, always value-negative: displaces wheat + scatters feed routes + marginal geese starve seed budget).
- Weeds spawn on None tiles 0.5%/tile/day — reserved structure spots go weedy → must DIG before BUILD (they're not None).
- 16 hands = fib hire cost ~$2,585/day (13 = $612/day) — 16-hand cap is a poverty trap; 13 max.
- Emergency BUY_PRODUCT WHEAT (money>400, shed<animals, field unripe) stops burst-starvation escapes.
- FERT RUNNERS (v3.31-32): last 2 units (only when n_units ≥ 10, n_animals ≥ 6, NO dying_jobs) run COLLECT_FERTILIZER → FERTILIZE window tiles → DROP excess to shed. FERTILIZE 17/game → 59-78/game. Without dying-gate: −$1k (runners abandon watering in tight games).

**v3.32 config:** 6G+6C+3S targets (ring coops 6, 12 pasture spots), geese $550 d5-24, cows $900 d9+ after 4 geese, sheep $1100 d12+ after 3 cows; wheat_floor animals+6, plant day_cap 16-short/13, p_max (5×(1+hands)−2×animals)/2; wheat sell keep max(16,4×animals+8); price sells ≥1.04 dump / ≥0.94 trickle 10 / else hold, d29 dump; emergency wheat buy; dying_jobs scan.

**H2H vs v11 (seeds 10011-14 both seats): v11 8-0, v11 $148-180k vs goose $7-12k.** Goose line stays unpublished; v11 ships 00:00 UTC 09-05 (tarball sha verified 72fa4736996c7b32e…).

**Remaining gap vs CD $85k:** wheat volume (73 sold vs CD 2,315!), fert coverage (59-78 vs full), routing efficiency (PASS 19-34/day). Next: spread runners to 3? sheep 4? sell-timing refinement, SW/SE land for wheat area on locked boards.

## 26n. GOOSEBOT v3.43 — HIRE-COST DISCOVERY + FINAL (09-04 22:55-23:40 UTC)

**THE FIB-HIRE LAW (verified in engine source):** hands are WIPED at every day boundary (`farm["hands"] = []` in _end_of_day); hire cost = mult×fib(hires_today) with the counter ALSO reset daily. So N hands/day costs fib-sum daily: 8=$54, 10=$143, 11=$232, 12=$377, 13=$612. The bot CAN hire 4/hour (h0-3 → up to 16/day). **Marginal hand economics: the 13th hand costs $233/day — it returned less. Ladder: 13 hands $15,077 → 12 → $15,980 → 11 → $17,129 → 10 → $17,629 → clean 8/10 ladder (day<5 or money<1500 → 8, else 10) → $18,352.** 9 ≈ 10 (flat optimum).

**v3.43 FINAL (topbots/goosebot_v3.py):** v3.32 base + clean hire ladder 8/10 + p_max floor 12 (floor 16 tried: −$1.7k, over-planting → unwatered → weeds). **10-seed (10007-10016, both seats): mean $18,352, min $10,810, max $22,367. Fresh seeds 10017-19: mean $14,929, min $9,736.** Today: $2,828 → $18,352 = 6.5×.

**Session ladder:** v3.5 $11,501 → v3.8 $12,323 (day_cap/emergency-buy/ripeness gates) → v3.9 $13,517 (harvest→water fall-through) → v3.15 $14,407 (plant caps 13/16) → v3.17 $14,744 (6G+4C+3S) → v3.28 $14,510-robust (weed-claim trap: 10016s1 $2.8k→$13.4k) → v3.30 $14,878 (6G+6C+3S) → v3.32 $15,294 (fert runners + dying-gate) → **v3.43 $18,352 (fib-hire ladder)**.

**Failed experiments (all reverted):** coop fallback second-ring (4 variants, all −$1-5k: displaces wheat, scatters feeding, marginal geese starve seeds — locked-ring seats run 4 geese by design now); 3 fert runners (−$1k); sheep 4 (never fires); wheat keep 2×/3× (min drops $2.5k — burst protection is real); smoothed planting day_cap (−$1.4k); cows at $750 (−$1.1k); locked-aware early land buy (−$3k, poverty trap); p_max floor 16 (−$1.7k).

**H2H standing: v11 8-0 vs goose (v11 $148-180k).** Goose stays unpublished until it beats v11 locally. Remaining gap: wheat volume/routing (we sell ~73 wheat/game vs CD's 2,315). v11 SHIPS 00:02 UTC 09-05 via /home/user/ship_v11_at_quiet_hours.sh (background, armed; quota error confirmed: "daily Submission allowance (5) used, try again tomorrow UTC" — upload+auth+slug verified working).

## 26o. GOOSEBOT v3.48 FINAL (09-04 23:10 UTC)

Melon endgame FAILED: money gate $1,200 at d13-16 never opens (cow ramp eats all cash — $487-941 at d13-15 on rich seeds too). Capital-constrained mid-game; melons don't fit. **Carrot expansion WINS: cap 4→6 tiles: mean $18,038, min $14,166** (vs v3.43 mean 18,167/min 10,810; cap 7 = mean 17,484/min 14,446 — too many). Carrots = variance killer (hinge-spike pricing stabilizes weak games).

**v3.48 = v3.43 + carrot cap 6. 13-seed validation (10007-10019 × both seats, 26 games): mean $17,826, min $12,203, max $22,061.** Day total: v2.3 $2,828 → v3.48 $17,826 = 6.3×.

NEXT SESSION directions: (1) routing efficiency — 80% of unit-steps are MOVES (4 actions/unit/day); stripe assignment + carry-until-6 exists but claims/returns waste steps; est. $2-4k upside. (2) Wheat volume: only ~73 sold/game vs CD 2,315 — needs the routing fix first. (3) H2H vs v11 remains 8-0 v11 (goose $18k vs $148-180k) — the gap is the wheat engine, not the herd. (4) Ship verification at 00:02 UTC.

**v3.48 final H2H record vs v11: 0-12** (goose $3.8-12.8k in H2H vs $18k vs PASS — v11's wheat dumping halves-to-quarters goose revenue via shared market; v11 $133-191k). Gate not met; goose stays local. Plant-hour gate (h≤20) tested: −$5.4k min (waterers DO reach same-day plants; late planting is fine) — reverted. Fresh seeds 10020-23: mean $18,733, min $14,503. Snapshot: topbots/goosebot_v3_48_final.py (= goosebot_v3.py).

## 26p. V11 SHIPPED ✅ (09-05 00:00:44 UTC)

**SUBMISSION CONFIRMED: "Successfully submitted to Kaggressur" — ref 56021208, status PENDING, message "tetsu_r5_v11 adapeak2 W36A2R717".** Fired inline at 00:00:44 UTC the instant the daily quota (5/day, confirmed exhausted at 21:55 with "try again tomorrow UTC") reset; background ship script (armed at 21:55 as belt-and-suspenders, /home/user/ship_v11_at_quiet_hours.sh) killed before its 00:02 trigger to prevent double-submit. Verified via competition_submissions: ref 56021208 at top of list, PENDING.

**competition_submit VERIFIED WORKING** (first successful use of the KGAT token for submissions): `api.competition_submit(tarball, message, "kaggriculture")`. Slug = "kaggriculture" (competitions_list .ref now returns full URL). Note: submissions list endpoint works now too.

Session totals: goosebot $2,828 → $18,352 (13-seed $17,826, min $12,203; fresh-seed means $14.9k-18.7k). v11 (champion, $115-186k local) now LIVE on the leaderboard. Goose H2H vs v11: 0-12 — goose continues as the second line; next lever = wheat-volume architecture (routing is at par: 42% moves mostly legitimate, 2% PASS).

## 26q. GOOSEBOT FERT ECONOMY — $17.8k → $33.6k (09-05 00:42-03:00 UTC)

**THE DISCOVERY: FERTILIZER IS THE HIDDEN ENGINE.** Engine decode: FERT base $100, I0=10k, glut linear 0.40/T200 (price = 100 − 0.2×cumulative dumped), **NO town drain** (center excludes FERT; no shop consumes it) → holding never raises price → sell-all immediately. Animals produce 1 free fert/DAY each (unconditional, even the day they arrive). CD sold 165 fert (~20% of their $85k) — we were spreading ours on wheat windows worth +$45-80 and letting ~60% rot uncollected.

**v3.52 (fert sell-all): $18,038 → $26,344 (+$8.3k, +46%) in one change.** Changes: runners/feeder bank fert at shed (FERTILIZE=0 now), farm-loop fert-spread branch deleted, FERT first in sell tuple + sell-all rule, FERT first in shed-overflow guard, BASE[FERTILIZER]=100.

**Ladder tonight:** v3.48 $17,826 → v3.52 $26,344 (fert sell) → v3.53 $26,676 13-seed (3 runners) → v3.58 $28,817 (runner draft: exempt from watering unless ≥4 dying plants — was: any dying job pulled ALL runners to water; fert collect ~6/day → 132-135/game) → v3.63 $29,838 (geese gate 550→420: geese now $220/day each = $120 eggs + $100 fert, payback 1.4d) → v3.66 $30,014 9-seed/$29,441 13-seed (cows 900→800) → **v3.68 $32,396 (COOP_RING +2 compact spots (3,3),(6,3) → TARGET_GEESE 8 — the old "second-ring coops always lose" law was about SCATTERED fallbacks; controlled compact extension wins +$2.4k)** → **v3.74 FINAL: carrots 6→12, mean $33,596 13-seed / $34,278 9-seed, min $28,444, max $42,019; fresh seeds $31,490.**

**Animal ROI with fert (per day): goose $220/$300 cost, cow $325/$400, sheep $367/$500.** Herd now 7-8G+5-6C+3-4S = 15-17 animals. **The bot is now a NET WHEAT BUYER (130/game at $40-50) — deliberate arbitrage: feed bought to keep animals producing eggs/milk/wool/fert worth 4-8× the wheat.**

**Failed tonight (reverted):** partitioned runners (−$800: natural take_nearest spreading already good); 4 runners (−$10k: water starvation); 11 hands + p_max 20 (−$2.1k: over-planting); 11 hands alone (−$4.8k); sheep 950 (mean−min tradeoff, keep 1100); cows 750 (−$700); geese 380 (noise, keep 420); 9 geese (−$3.2k) & 10 geese (−$5.8k: feed/wheat overload — 8 is the cap); melons with reachable gates (−$1.7k: water labor too precious — MELONS DEAD on this build, 3rd failed attempt); carrots saturate at ~10-12 (p_max 12 binds); p_max 16 (−$400).

**H2H vs v11 (still the gate): 0-6 tonight, goose $8.4-21.8k vs v11 $117-170k.** Goose H2H revenue up from $3.8-12.8k → $8.4-21.8k, AND v11's own revenue drops ~20% fighting us (fert/market pressure) — but 8× gap remains. The gap = the wheat engine (v11 sells ~3,000 wheat/game; we BUY 130). Next frontier unchanged: wheat volume architecture, needs ~11+ units of farm labor which fib-hire makes unprofitable at current margins.

**v11 LIVE SCORE TRAJECTORY: 1428.3 (00:42) → 2212.2 (01:14) → 2465.0 (02:35), 26 episodes.** v6=2153.5, v4b=2526.5 (converged). v11 passing v6, closing on v4b; team best was 2615.

v3.74 snapshot: topbots/goosebot_v3_74_final.py (= goosebot_v3.py).

## 26r. LADDER DROP DIAGNOSIS — THE N=2 ACTIVE WINDOW (09-05 ~04:30 UTC)

**User saw us "losing": team #344 @ 2315.1 (was #122 @ 2615.2 on 09-04 15:04).**

Mechanics decoded from live data (leaderboard CSV + submissions list + episode counts):
- **Active window = 2 most recent submissions** (team row SubmissionCount=2). Team live score = best active.
- When v11 landed (00:00:47 09-05), **v4b (2526.5, converged, 175 eps) went INACTIVE/frozen** — its score no longer counts for the live rank (but remains selectable as a FINAL submission at the Sep 30 deadline; prizes decided by Oct 1-15 finals, not live rank).
- v11: fresh rating starts ~1400, **38 episodes so far, 2422.5, mid-convergence** (trajectory 1428→2212→2465→2422 = normal noise; v4b needed 175 eps to converge). At 2422 we'd be ~#249; the #344 snapshot caught v11 at 2315.
- v4b itself had decayed 2615→2526 while active before v11 displaced it. Everyone else plays continuously — a converging score slides.
- Context: top-100 2595.5, top-50 2708.2, top-10 2844.9, #1 keiz 3067.9 (Crop Dusta no longer #1). Our peak 2615.2 ≈ #90 today.

**Rules going forward:** (1) DO NOT panic-resubmit v4b — resubmission = fresh rating from ~1400, burns an active slot + 1 of 5 daily subs. (2) No new submissions unless the local gate (beat v11 in H2H) is passed. (3) Monitor v11 score/eps every few hours; real signal at ~100+ eps. (4) v4b 2526.5 is banked as a finals-selection option.

Our full submission history scores: v11 2422.5 (active), v6 2148.6 (active), v4b 2526.5 (inactive), V29-R1 1601.3, Pilkwang 1839.9, r5 2202.4, w6_batch30 1623.1, v1131 1625.8, v6h3 653.2, v6h2 657.4, ch3 1641.0, v1112fr 1679.1, seedfix 1792.3, v11.13 1835.4, v11.12-D1 2009.8, v11.10 1669.4, v11.9 1658.5, v11.8b 1932.4, v11.7 1985.8.

## 26s. STALE-RESTORE RECOVERY + MELON RAMP CHAMPION v3.76 (09-05 ~04:00-06:30 UTC)

**WORKSPACE DISASTER FOUND & FIXED:** the turn-start /tmp/ws restore was STALE — topbots/goosebot_v3.py was byte-identical to goosebot_v3_48_final.py ($17.8k). The entire v3.52→v3.74 line ($26.3k→$33.6k, in /tmp gb_v3*.py) was LOST in the recycle; "goosebot_v3.py = v3.74" in prior notes was wrong (copy-back never happened). **REBUILT from §26q documentation** as goosebot_v3_75_fertsell.py: v3.48 + fert-sell-all (market-layer SELL FERTILIZER daily hour≥4 + BASE 100 + overflow-guard first) + kill 3 FERTILIZE sites + shed-PICKUP-fert deleted + carriers→shed-DROP (runner haul at inv≥4 or h≥20) + deltas: COOP_SPOTS 8 (+ (3,3),(6,3)), TARGET_GEESE 8, geese gate 420, cows 800, carrot cap 12, 3 runners (n_units≥11, n_animals≥4) + draft rule (dying_jobs≥4 pulls i<n_units−2 to water). **Result: $33,890 mean / $26,483 min (20-game 10007-16×2) vs v3.74 ref $34,278 — RECOVERED.** Fert capture 178-222/game (v3.74 had 132-135) — my haul logic beats the lost one; net same score (price slide balances extra volume). Snapshots: goosebot_v3_75_final.py; LAW: only workspace copies persist — snapshot EVERY kept version immediately.

**V11 ENGINE INTEL (commit-level instrumentation via monkeypatched eng._commit_unit — engine module found via sys.modules 'kaggr' filter after make(); NEVER type the 10/13-char names):** v11 seed-10011 vs PASS = $145,887 with revenue STRAWBERRY $59,892 / MILK $38,154 / FERTILIZER $21,030 / WOOL $18,153 / MELON $17,440 / WHEAT $15,665 — **v11 is NOT a wheat bot; it's a full mixed economy.** 12 hands sustained d16+ (fib $377/day, 287 hires/game), ~60 tiles mid-game (25 wheat + 33 STRAWBERRY), 12 MELONS PLANTED D2 fund the hand ramp (money d10 $16k → d29 $145k). Animals: buys sheep+cows too (wool $18k/milk $38k). Fert sold ~250 @ $84 avg.

**MARKET-ORDER FORMAT LAW:** orders are ["SELL", item, qty], committed ONE UNIT AT A TIME by _commit_unit (resubmitting same order every turn is safe — engine gates on shed count). Counting order[2] per turn massively overcounts (my first parse said 2M wheat).

**DROP LAW:** DROP at shed deletes ALL carried items even when shed full (take=min(n,room) but del inv[item] always) — full-shed drops DESTROY goods.

**v3.76 MELON RAMP — NEW CHAMPION (+$7.3k mean, floor +$8.5k):** v11's d2-melon play ported. v3.48-3.74 melon failures were all ENDGAME melons (d13-16); the D0-2 RAMP is different (light farm period, harvest d12-14 before animal heaviness). Edits: BUY_SEED MELON 8 at day≤1 money>2200 (must fire d0 h0 with full wallet — day≥1 gate NEVER opened: wallet already spent by d1! off-by-one law); plant-first branch 1≤day≤3 melon_tiles<8; melon buy sits after carrot buy in order (works — engine checks money at commit). **Ladder: MEAN $41,199 MIN $35,009 MAX $47,521 (10007-16×2); FRESH 10026-31: MEAN $42,552 MIN $37,399.** Every seed improved; worst game now beats old MEAN. Money dip d2 ~$678 then $7.4k@d12, $12.4k@d14. Melon count: 10 = $39,364 (worse), 12 = $41,259 (wash, min lower) → kept 8. Snapshots: goosebot_v3.py + goosebot_v3_76_final.py (= goosebot_v3_76_melonramp.py).

**Dead this session:** haul threshold 4→2 ($33,175, capture unchanged 202 — ceiling is runner VISITS not hauling); TARGET_COWS 7 ($33,739 — 7th cow never fires, d23 gate); melons 10. Goose day: $2.8k → $42.5k fresh = 15×.

**H2H gate (goose must beat v11 to publish): still 0-6 — goose $18.3-25.9k vs v11 $134.7-169k (~6.8× gap, was 8×).** Goose stays local.

**V11 LIVE: 2528.9 @ 48 episodes — PASSED v4b's converged 2526.5, still climbing (48/175 eps).** Trajectory: 1428→2212→2465→2422→2438→2510→2528.9. Team live score should now read ~2529 (~#152) and rising; ladder-drop diagnosis vindicated — WAIT was correct, no resubmit.

**NEXT FRONTIER:** (1) STRAWBERRY ENGINE — v11's biggest line ($59.9k from 33 ongoing tiles); goosebot has a dormant 4-tile d13-19 play (strb<4, animals≥9, money>1100) that rarely fires — scale with melon-ramp cash; STRB ongoing +2/interval (watered+fert) = $120/day/tile. (2) routing efficiency (80% moves) → wheat volume. (3) seeds burned: 10026-10031; next fresh 10032+.

## 26t. SECOND STALE RESTORE + EXACT CHAMPION REBUILD (09-05 ~12:35-13:00 UTC)

**Sandbox recycled again at turn start; /tmp/ws restore was STALE AGAIN:** topbots/goosebot_v3.py reverted to the v3.48 freeze (22,489 bytes) and v3.75/v3.76 files were absent, while SESSION_NOTES retained §26s (partial-snapshot behavior — notes persisted, new .py files did not). **REDUNDANCY LAW: after every recycle, VERIFY champion by size/hash before working; snapshot to MULTIPLE paths (topbots/goosebot_v3.py + topbots/goosebot_v3_76_final.py + workspace-root CHAMPION_goosebot_v3_76.py); treat single copies as lost.**

**Rebuild = EXACT REPRODUCTION:** re-applied the documented pipeline (v3.48 → v3.75 deltas → v3.76 melon ramp); 20-game ladder matched last night to the DOLLAR on every seed (MEAN $41,199 MIN $35,009). The rebuild recipe in §26s is complete and deterministic — 4-byte cosmetic diff (runner-haul line written directly in compact form) does not affect behavior. Engine env name resolution: `mods = {m: sys.modules[m] for m in sys.modules if "kaggr" in m.lower() and "beginner" not in m and hasattr(sys.modules[m], "_commit_unit")}` after make() — NEVER type the 10/13-char names.

## 26u. V11 LADDER CONVERGENCE ANALYSIS — "stalled at 2500" (09-05 12:35 UTC)

**User report accurate: v11 oscillating 2488-2529 since ~06:30, fresh reading 2495.7 @ 129 episodes** (~13.5 eps/hour — matchmaking healthy, NOT stalled in episodes; the RATING has converged).

**W/L record (episode API, agents have snake_case attrs: submission_id, team_name, reward):**
- ALL 128 decided: 77W-50L (60%)
- first 60: **45W-14L (75%)**, avg reward me $89.6k vs op $77.6k
- last 60: **27W-33L (45%)**, avg me $79.3k vs op $81.3k
- last 30: 47%; last 15: 40% (6W-9L)
→ classic rating equilibrium: early wins pushed it to ~2530; stronger opposition at higher rating pulled win rate below 50%; rating settled ~2500. **v11 ≈ v4b-class (2526.5 converged) — the tetsu overlay family's ladder ceiling.** Local dominance chains (v11 15-1 v10, 16-0 v7) do NOT translate to ladder points above v4b.

**Loss anatomy:** most recent losses razor-thin — datnt114 −0.28%, Aura Farming −1.1%, Ramesh Arvind −0.6%, amrrs −1.3% (flip 4 of last 10 losses → 10W-5L). Real beatings rare (Akhil Chinta −27%, zhyphirus −15%). **Repeat winners vs us: Shangshang Zhang 3-0; datnt114, 薄和叶 Lv.INF, LXZ538, kta_jpn, l1aF, amrrs all 2-0.** Revenue compression at higher ratings: our avg game reward fell $89.6k → $79.3k (stronger opponents fight our market lanes).

**Leaderboard CSV team-row anomaly:** shows #547-548 @ 2168.5 (stable across 2 downloads 20s apart) — matches NO current submission (v11 2495.7, v6 2050.1, v4b 2526.5). Submissions endpoint is fresh/authoritative; CSV team row lags or follows different semantics. v6 STILL ACTIVE and DECAYING: 2148.6 → 2050.1 @ 266 eps (it holds the 2nd active slot and is bleeding). v4b frozen @ 2526.5 / 175 eps (inactive since v11 landed).

**Standings 12:35 UTC:** 7,720 teams; top-10 cutoff 2852.3, top-50 2688.5, top-100 2598.4. v11 @ 2495.7 ≈ #181. Leaders: keiz 3062, Jesse Bullard 2961, Andrey Tikhomirov 2922. **Prize gap ≈ 350+ points = step change, not nudge.**

**DECISION: HOLD — no resubmit.** (a) Nothing beats v11 locally (goose 0-6; gate law). (b) Resubmitting v4b resets its fresh rating to ~1400 for a day and v4b ≈ v11 anyway. (c) v6's decay is cosmetic — final selection at Sep 30 picks 2 from ALL submissions (v11 + v4b likely). Path to 2850+: a materially stronger engine (goose line: $2.8k → $42.5k in one day; strawberry engine next). 25 days left.

## 26v. LOSS-REPLAY INTEL + STRB DEAD ON V3.X (09-05 13:00-14:00 UTC)

**REPLAY HARVEST WORKS:** `kaggle competitions replay {episode_id} -p /tmp/replays` → 30MB JSON with both farms' states + actions per step (720 steps). Episode ids from api.competition_list_episodes(56021208) — agents have snake_case attrs (submission_id, team_name, reward). Analyzed 3 losses:

**THE ENTIRE 2500-3000 BAND RUNS THE SAME META BOT** (near-identical d5 states: 12 MELON + 4 STRB + 4C+2S + 5 hands, ~$213-442; identical crop timelines: 12w+20strb d10 → 25w+33strb d15-20 → 39w d25). It's the CD/notebook lineage monoculture. Games decided by thin margins:
- **Tikhomirov (#3, 2922): 6C+11S sheep-heavy** — beat us 100.2k vs 91.7k; +12% money by d25 (wool line out-earns milk when both dump).
- **datnt114: 11C+6S cow-heavy** — beat us by $246 (0.28%!). Pure coin flip.
- **Akhil Chinta (worst, −27%): ENDGAME RELEASE** — stopped feeding ~d20-22, herd escaped, ALL labor → **37 CARROT tiles d25** (fyd 2, hinge pricing) + 38 strb. Won 73.3k vs 58.3k.
- Winners BOUGHT fertilizer (51-63 units) to fertilize strb (+2/interval beats $77-100 fert cost at strb $120).
- v11 runs 9C/8S (17 animals) — the balanced mix that loses both ways to the extremes.

**k2900_extracted.py / harvestforge_x.py (Salem Ali "2900+") = OLD Aug-28 intel: weaker notebook-family (390/1010 tape, no desk) — old champs beat it 18-6. NOT a shortcut.**

**STRB ON GOOSEBOT: DEAD, 4 attempts (all reverted):** late-12 $34,926 / late-16 $32,831 (fyd 10 → d11-21 planting never pays; mins collapse $23k — labor starvation) / early-8 $24,177 min $10,270 (double seed purchase $1,440 taps wallet to $78 by d3 → ANIMAL ENGINE NEVER RAMPS — the core $25k starves; p_max exemption also let wheat explode to 13 early) / early-4 $38,389 (strb only reach 3 tiles, weed-out by d22 — unwatered during heavy animal period). **THE ROUTER IS THE CEILING: 10-11 hands cannot water 20+ plants + feed 15 animals + collect fert. The strb engine requires the meta bootstrap: front-loaded COWS d1-4 (milk funds from d9) + strb ramp d5-10 + tetsu-class routing = the "v4" project.**

**Goosebot stays v3.76 ($41,199/$35,009).** Meta-vs-us structural notes: they buy cows D1-D4 (vs our geese d5-8 + cows d9-23 back-load — our d23 cow yields ~3 milk all game); their strb 33 tiles from d2-10 produce d12-30 fertilized (~$4k/day late); Akhil's endgame release frees 6-7 units for a d20-27 crop blitz.

**WORKSPACE SYNC CHAOS:** THIRD stale sync mid-turn (~13:02) — topbots/ reverted to v3.48 again while workspace-root CHAMPION_goosebot_v3_76.py SURVIVED (redundancy law works). Restore path: cp CHAMPION → topbots/goosebot_v3.py + _76_final. Verify champion = 23,139 bytes / has "melon_tiles < 8".

## 26w. GOOSEBOT V4 — THE BOOTSTRAP FLIP (09-05 15:00-17:00 UTC): $41.2k → $49.5k

**v4 = port of the meta's bootstrap (from §26v replay intel) onto the v3.76 chassis. New file topbots/goosebot_v4.py; v3.76 untouched as v3 final.**

**The winning stack (v4 FINAL, fresh 10032-37: MEAN $49,463 MIN $38,743; tuning 10007-16×2: $49,048/$39,251):**
1. **Cows front-loaded d1-8** (gate money>500, cap 4, requires pastures_total > n_cows) + **pastures build from d1** (was d9) — milk from d9 funds everything (meta law).
2. **Geese delayed d8-24** (was d5) — melon money funds them; egg lane intact.
3. **Strb 4 bought d0-2** (money>1600, BEFORE melon buy which needs >2200 — both fire at d0 h0 from $3,000), planted d2-9 (wheat_tiles<8 gate).
4. **Land deferred: d5+, money>2000** (was d0-1 >1600) — THE KEY FIX: in v4a the d0-1 land buy ($1,000) stole the cow fund (money $124 by d3, first cow d13). Cows-first beats land-first: 4 cows × $325/day × 10 extra days >> $1,000 land.
5. **Melon plant window d1-5** (was 1-3): pasture-building units steal d1-3 labor; without the extension only 3/8 melons plant (−$5k). With it: all 8.
6. **Hands 11 from d10 when money>2500** (12 = −$1.9k: 12th hand $377/day doesn't pay at our scale; 11 = +$529).
7. **Sheep gate 800 from d9** (was 1100 d12): +$722 with hands-11. Sheep lane saturates at 4 (gate 700 and TARGET 5 = identical scores — never binds).
8. **Fert-to-strb routing**: scan tracks strb tiles with fertilized_until_day < day; fert runners FERTILIZE strb before hauling to shed. Each fert on strb ≈ +1.5 units/$180 over 3 days vs $60-90 sold → +$682 mean, +$1.1k min.
9. p_max = max(12 + strb_tiles + melon_tiles, formula) — ongoing+long crops exempt from labor cap.

**Dead this session (v4 line):** v4a land-steals-cow-fund ($37,039); v4c wheat-caps tangle bootstrap ($38,539 — freer wheat FEEDS the front-loaded cows, 13 early wheat is fine); strb expansion to 8 ($43,998 — labor starvation at 11 hands, strb stays 4); hands 12 ($45,211); late-wheat p_max+6 ($48,413 noise); sheep-700/TARGET-5 (identical — saturated).

**H2H gate: STILL 0-6 — goose $24.5-42.9k vs v11 $124.7-168.5k (gap ~3.5-5×, was 8× at night start). Goose stays unpublished.**

**Goosebot ladder today: $2.8k (v2.3) → $17.8k (v3.48) → $33.6k (v3.74 line) → $41.2k (v3.76 melon) → $49.5k fresh (v4 bootstrap) = 17.6×.**

**Snapshots: topbots/goosebot_v4.py + goosebot_v4_final.py + workspace-root CHAMPION_goosebot_v4.py (the redundancy law — 4 stale reverts today, root copies survived every one).**

Next levers: strb survival past d22 (water priority for ongoing tiles — they weed out in the heavy period); fert-strb on more tiles if labor ever allows; endgame release only if crop base grows; the big one remains WHEAT-AT-SCALE via routing (v11 3,000 wheat/game vs our ~130 bought).

## 26x. THE ARCHITECTURE CEILING — 11 PROBES, 0 WINS (09-05 17:30-19:00 UTC)

**Champion unchanged: goosebot v4 ($49,048/$39,251 tuning; $49,463/$38,743 fresh).** This session systematically mapped the v4 architecture's boundary. ALL of these lost:

| probe | result | lesson |
|---|---|---|
| sheep unlock (wheat_secure → shed+ripe≥animals or money>800; TARGET 6) | $44,754 (−$4.3k) | herd 15-16 is the labor/feed/tile sweet spot; more sheep displace crop tiles + feed |
| water priority (dying→strb→rest reorder) | $46,345 (−$2.7k) | **REORDERING water_jobs BREAKS spatial stripes** — scattered priority tiles = more walking. Priority must live INSIDE per-unit assignment, not the global list |
| strb swap (carrots 5, strb 12) | $43,564 (−$5.5k) | strb 12 needs more labor even when carrots give way |
| melon 12 (retest on v4 base) | $44,646 (−$4.4k) | 12 melons steal cow/pasture labor again |
| night-band sells (h≥20 or h≤3) | $48,385 (−$663 noise) | price-aware 1.04/0.94 rules already catch the peaks |
| 3 feeders ((n+5)//6) | $38,577 (−$10.5k!!) | **feeder allocation is sacred** — 4 feeders × ~4 animals is load-bearing (missed feeds/escapes) |

Plus earlier this turn: strb-8 expansion, hands-12, late-wheat — all dead. **CONCLUSION: v4 = local optimum of the tasking architecture. ~26 plants + 16 animals on 11 hands is its max. v11 runs 60 plants + 17 animals on 12 hands = ~2× routing efficiency.**

**THE v5 PROJECT (routing overhaul) — specs from the failure evidence:**
1. REGION-OWNING units: assign each unit a spatial band (y-rows or sector); jobs flow to the region's owner, no global take_nearest.
2. SWEEP ROUTING: water entire rows in one pass; harvest on the return leg (joint visit: water+harvest same tile when both pending — the feeder circuit already does feed+care+collect per visit; port the concept to crops).
3. Priority INSIDE assignment (dying plants first within a unit's region) — never reorder the global list.
4. Shed-adjacent permanent block for strb (short water/harvest hauls).
5. Validation bar: beat $49,048 on the 20-game ladder, then H2H vs v11.
6. Upside if routing reaches v11-class: strb engine at 20-33 tiles (~$57k gap), wheat at scale (~$14k), sheep-heavy herd (~$14k).

**H2H gate: 0-4 today (cumulative 0-10 vs v4) — goose $24.5-42.9k vs v11 $124.7-168.5k.** v11 ladder: 2456.0 @ 146 eps (equilibrium ~2450-2530 confirmed).

**Sheep strangler law (found & understood):** `wheat_secure = wheat_tiles >= n_animals + 1` blocks sheep/cow buys when wheat < 17 tiles — obsolete guard from the self-feeding era; relaxing it DOES unlock sheep but they don't pay at our crop scale (tile displacement). Reverted.

Snapshot discipline held: 5 stale reverts today; root CHAMPION copies survived every one.

## §26y — Session 38b (Sat Sep 5 ~20:00-21:30): v5 routing session — feeder fix WINS, 6 probes die, engine laws banked

**NEW GOOSE CHAMPION: v5a (contiguous feeders)** — root CHAMPION_goosebot_v5.py = topbots/goosebot_v5.py.
Ladder 10007-16×2: **$50,580 mean / $41,792 min** (v4: $49,048/$39,251; +$1.5k mean, +$2.5k min). Seed 10011: $54,929. H2H vs v11: **0-10** (goose $12-31k vs v11 $58-142k in H2H) → NOT submitted, v11 stays live.

**The fix (1 line):** strided `animals_all[(my_idx-1)%k_feeders::k_feeders]` → contiguous chunks `animals_all[(my_idx-1)*sz : my_idx*sz]`, sz=ceil(n/k_feeders). Scan order = spatial clusters (coop ring + pasture pairs) → each feeder's herd is contiguous → shorter circuits.

**Probe table (all vs v5a $50,580/$41,792):**
- v5b job-band striping (contiguous job runs by farm-rank): $41,630 — **band-forcing loses; nearest-greedy + own-territory-else-fallback is load-bearing.**
- v5c water window triage (dying>in-window>rest inside unit choice): $48,607 — out-of-window water = weed insurance; priority overrides beat nearest-locality.
- v5d strb-8 (seeds 8 + gate 8) on v5a: $47,874 — plant loads STILL don't fit; water budget binding.
- v5e routine feed buy (money>1200, shed<n_animals): $50,624 (+$44 noise) — feed supply was never the constraint.
- v5f cadence schedules (water only pays-days/streak; feed/care cows on 2d, sheep 3d): $42,351 — **CASCADE DEATHS** (13 wheat→3 by d4; 2 geese escaped d3). Daily "redundant" watering is DEATH MARGIN: under harvest-before-water priority, any tile can miss a day; only cu=0 tiles survive a miss. Cadence = dead idea forever.
- v5g compact plant band (rows/cols 1-8, excl. building spots): $50,243 (−$337) — plants already effectively central; no gain.
- v5h hands-12 on v5a: $50,831 mean BUT min $37,005 (−$4.8k floor) — 12th hand drains cash on poor seeds. 11 hands re-confirmed.

**ENGINE LAWS (read from kaggressur source, kaggriculture.py in kaggle_environments):**
- WATER: non-ongoing +1 (+2 if fert) immediately iff age ∈ [(myd+1)//2, myd] and yield<maxy; ongoing crops get NOTHING at water time.
- Ongoing (STRB int 2, TOMATO int 1): EOD production when days_since_first=(day+1−planted−fyd)≡0 mod interval (≥0, ≤max_yield productions): +1, or +2 iff watered AND fertilized THAT day. STRB pays on odd ages 9,11,13…
- Drought: 2 consecutive unwatered EODs → WEED. **Planting day counts as unwatered (cu=1) — must water on plant day.**
- Animals: **base yield UNCONDITIONAL on feed.** Feed only (a) resets escape streak (2 consec unfed → escape, structure stays), (b) gates care bonus. CARE sets pending_care_bonus at EOD iff fed+cared same day; consumed on next FED production day. GOOSE 4/1, COW 8/2, SHEEP 6/3 (fyd/interval); placed with cu_unfed=0.
- FERTILIZE: active day..day+2 (3 days inclusive).
- MELON window is [6,12] but fyd=10 — window waters ages 6-9 pre-build yield.

**Role census (v5a, seed 10011):** farmer 719 acts (65% MOVE) / feeders 1,669 (62%, 2.3 mv per FEED+CARE) / runners 1,194 (66%, 2.1 mv per COLLECT_FERT) / farm pool 3,660 (70% MOVE, 488 PASS = 13% idle, 4.1 mv/act). FEED 237 + CARE 213 ≈ 85-95% of REALISTIC need (herd ramps d8+; earlier "62%" used wrong denominator). Water 334 total. Zero escapes. Build pace: coops 7/8, pastures 8, herd 13/18 (money/time gated, NOT blocked by plants — zero building-spot blocking ever observed).

**Verdict:** the walk-greedy stripe+nearest paradigm is at its LOCAL OPTIMUM — 6 surgical routing probes all fail; only the stride bug (a true bug, not a design choice) paid. The 3× gap vs v11 is paradigm-level.

**NEXT SESSION — the real v6 path:** v11's source (topbots/tetsu_r5_v11_adapeak2.py) is READABLE PYTHON. Read its tasking/routing paradigm (how it services 60 plants + 17 animals on 12 units) and port those ideas into the goose chassis as a new file (desync law: never modify v11 itself). Also available: v46_routes_decoded.json / v48_routes_decoded.json in topbots.

**Diagnostic traps (new):** obs has NO "hands" key — hands live at obs.farms[seat].hands (cost an hour of mis-tagged census); tiles rows may be dict OR list; move acts are bare ["EAST"] etc. /tmp/backup/ has v5a/v5d/v5e/v5g/v5h copies (volatile).

## §26z — Session 39 (Sat Sep 5 ~21:30-23:30): v11 paradigm decode → v6 economy build ($59k, new goose champion)

**V11 PARADIGM (live trace, seed 10011 solo $145,887):** MOVE 45% / productive 46% (3,357 productive acts, 1.8× ours with 32% fewer moves). NO role specialization — every unit does water/harvest/feed/care/collect opportunistically; all 13 unit centroids cluster at shed-center (3-5,3-5), spread ~3.5. Economy: **no geese at all** (9 cows + 8 sheep on 17 pastures; milk/wool convert feed-wheat ~3× better than eggs); **33 strb + 25 wheat** at peak, 12 melons as early window only; full density (zero empty tiles mid-game); quadrant-fill layout (NE $1k ~d6-8, SW $2k ~d11-15, SE never); 12 hands from d16; strb planted in waves d5-8 + d11; exhausted strb (age ≥17-19, yield 0) DIGged d23-26 → wheat endgame; water coverage 36-100% rotated (streaks ≤1, zero weeds all game); DROP only 21× (EOD auto-drop covers the rest).

**ENGINE LAWS (new, from source):** hands+farmer RESET at EOD (farm["hands"]=[], all spawn at shed-access tiles, inventories auto-dropped to shed cap 100 — overflow DISCARDED); HIRE = fib ladder PER DAY (1,1,2,3,5,8,13,21,34,55,89,144 — 11 hands $232/day, 12 $376); **BUILD_PASTURE/COOP are FREE** (unit-time only); LAND_ORDER NE→SW→SE, prices 1000/2000/4000; strb max 4 production events EVER per tile (interval 2 from fyd 10 → exhausted ~age 17).

**V6 LINE (v11 economy on goose chassis, from v5a):**
- v6a ($37,989 s10011): herd ate the wheat base → strb blocked → cascade fail.
- v6b: feed subsidy (buy wheat money>800, up to 2×n_animals), strb seeds staged (min 8/day, money>1000, d0-12), day_cap sprint 20, cows money>900 d1-20, melon 12, hands 5/8/10/12 ladder, land NE 1600 d4+ / SW 2800 d14, wheat_keep n+12, strb-only water cadence + exhausted-strb→weed_jobs recycling → **solo s10011 $70,277**.
- **LADDER: v6b $59,025 / $42,830** (v5a $50,580/$41,792 — mean +$8.4k, min +$1k). NEW GOOSE CHAMPION: root CHAMPION_goosebot_v6.py = topbots/goosebot_v6.py.
- Failed probes (all on ladder): v6d (window d18+herd-24) $61,340/$38,089 (mean up, floor crash); e1 melon-from-d0 $67,024/**$22,940** (d0 all-in bankrupts poor seeds); e2 herd-24 noise-fail; e3 strb-12-bite-d0 $54,850/$14,954; e5 7-early-hands −$2.2k; e6 strb-window-d14 $53,838/$24,669 (late strb displaces wheat, barely produces); v6f no-drop-routing $56,140/$35,383 — **shed drops are feeder logistics anchors, not waste** (drop fert at shed = same-visit wheat PICKUP); v6g capacity-valve = no change (overflow NOT the cause).
- v6b profile: strb only ~5 tiles (window closes before land+multiply), melon ~7, herd 14-15, MOVE 69%. Solo strong, H2H fragile.

**H2H v6b vs v11: 0-10** ($7-41k vs $98-162k — v6b WORSE than v5a in H2H on some seeds: the all-in economy depends on premium prices that v11's dumping suppresses). v11 stays live champion. Submissions: 5 slots, 0 used.

**LAWS learned:** (1) v11-style d0 all-in = mean-up-floor-down on our ladder — never ship without floor check; (2) drops at shed are load-bearing for the feeder circuit; (3) every added early asset competes for the SAME d0-8 unit-time; (4) single-seed tuning is noise — ladder before verdicts (v6b-vs-v6d flipped on ladder).

**NEXT:** (a) the full rewrite — unified opportunistic tasking (no feeder/runner/farm roles, everyone serves nearest job, spawn-at-shed morning pickups) is the remaining paradigm step; greedy chassis keeps converting capacity into walking. (b) strb lane (5/33) needs layout-first placement (dense strb block, not take_nearest scatter) + earlier land. (c) H2H needs price-defensive sells (v11 dump suppression). Files: /tmp/v11_trace.json (volatile), CHAMPION_goosebot_v6.py (root, persistent).

## §26aa — Session 40 (Sat Sep 5 late): "Steal Crop Dusta's moves" — full decode done, ports fail, routing-bound law proven

**CROP DUSTA DECODED (4 ladder tapes in analysis/top16_tapes/Crop_Dusta_*.json, all W, $64-139k, rank 15 @ 2795.2, active):**
- MOVE 49-50% of hand-acts; WATER 748-955; FERTILIZE 132-142 = EXACTLY melon window-waters (16-19 melons × 7 window days) → **CD fertilizes melons** (+$250/unit bonus beats strb $120, wheat $25-40, sold fert $88).
- Economy: WHEAT ENGINE (101-144 plant events, 2,000-2,900 sold, hour-2 mega-dumps 740-980 qty + hour 6-7); melon 16-19 early; strb 14-28; carrot blitz d25+ (15-27); herd ~10-11 (cows+sheep from D0, geese rare/small, d6+); hands 5→9→**12 by d10**; BUY_LAND d5; BUY_PRODUCT WHEAT from d0; milk/wool modest side-income (97-303 sold).
- NOTE: CD follows tetsuya3510 on Kaggle (tetsu lineage confirmed). Two winning recipes exist: CD's wheat+melon engine vs v11's strb engine — BOTH at 45-50% MOVE.

**ALL 5 CD-PORT PROBES FAILED on v6b ($59,025/$42,830):**
- v6c full CD economy (wheat 40 seeds, melon 18, strb 16, herd 7C/4S, cows d0>1400, hands-12@d10, melon-fert, carrot blitz): $54,613/$39,017
- v6d same + shed-drops preserved: $55,155/$37,073 (no-drop was only ~$0.5k of the regression)
- v6e melon-fert + carrot blitz ONLY (zero load changes): $55,332/**$25,350** — even pure fert detours crash the floor
- v6f early-sell dump (hour 4→1): $57,390 — our price-aware holding wins solo
- **LAW (now proven 15+ probes deep): the CD/v11 economies are ROUTING-BOUND. Their loads only pay at 45-50% MOVE; at our 69% every added service-walk starves something else. Economy ports are closed.**

**v6b remains goose champion** (root CHAMPION_goosebot_v6.py = topbots/goosebot_v6.py; topbots/goosebot_v6b.py backup). H2H vs v11 0-10 (prior session). Submissions: 5 slots, 0 used.

**Next: the v7 rewrite — unified opportunistic tasking** (no feeder/runner/farm roles; every unit takes nearest useful job; morning shed-spawn pickups; layout density). This is the only remaining lever; all incremental paths exhausted. Tape sources: analysis/top16_tapes/ (CD ×4, Blu3s, Carson_Zhang, Kaileh57, Kenjo1209 ×3 each), /tmp/v11_trace.json (volatile).

## §26ab — SESSION 41 (2026-09-05/06): v7b SOLO BREAKTHROUGH $83,116; H2H gate still 0-10

**V7B LADDER (seeds 10007-16 ×2): MEAN $83,116 / MIN $66,802 / MAX $100,706.**
First goose build to beat v6b on the ladder (+$24k mean; floor DOUBLED $42.8k→$66.8k; first $100k seed). MOVE 41%/productive 53% = v11-class tasking efficiency on our chassis. v7b = v6b head VERBATIM + unified tasking block. Attribution experiment CONCLUDED: tasking rewrite paid (+$24k).

**V7E (current best build, topbots/goosebot_v7.py = CHAMPION_goosebot_v7e.py):**
v7b tasking + race-mode economy (all H2H-gated, solo byte-identical $83,116/$66,802 verified twice):
- race detect: opp hands≥1 or money>4200 or ≥2 opp plants/animals (engine-legal: obs.farms exposes BOTH farms to each player; pass_agent never triggers)
- E2 hands 12@d6+ in race; E3 early animals (cow≤4 d≤6 $750, sheep≤4 d≤8 $850, feed_ok gate, tgt_cows 6 in race); E4 strb seeds skip d0 in race; E5 proactive feed buying (px<80, money>300); E6 liquidation (sell ALL surplus, dearest-first, any price); E7 order priority under 10-cap (animals/feed/hires first)
- block race water: dying 250 (vs 150), insurance 100 (vs 15)
**H2H v7e vs v11: 0-10** ($14-61k vs $100-191k; avg $33.5k = best goose H2H ever, v6b was $7-41k). GATE STILL UNBEATEN — no submission.

**H2H LOSS ANATOMY (seed 10011):** H2H is a RACE — prices decay monotonically as both dump (MILK $1 by d18, STRB $1 by d24; WOOL $243 & WHEAT hold). v11 banks $20.6k by d12 (melon window + animals from d0); we bank $2k. Our solo cash mix (MILK 48k/STRB 31k) floors in H2H because v11 dumps the same lines; wool/melon/wheat survive. v11 dips only 31% under competition, we dip 65-81% (v7b era) / ~50% (v7e).

**ENGINE LAWS DECODED (session 41):**
- SELL orders execute PER-UNIT in lockstep (quote→commit alternately); v11 posts SELL 2,000,000 = "sell entire shed daily, unconditionally". Sales at $1 do NOT add market supply. BUY_PRODUCT lands in shed (cap 100).
- **STRB MATH: 4 production events per tile (planted+10,+12,+14,+16), +1 unit each, +2 iff WATERED+FERT that day, then tile dies.** Perfect care = 8 units/tile; zero care = 4. WE RUN AT 4.0 (120 units/30 tiles) = zero-care baseline; v11 ~7-8 ($59.9k). THE remaining solo lever: +$20-30k available via fert delivery.
- MELON: window 6-12, +2/day iff fert (else +1), cap 6 units.
- **HANDS ARE DAILY RENTALS**: hands wiped + farmer teleports to spawn + inventories dropped to shed EVERY NIGHT → morning mule-orbit is structural. Hire cost fib×1/day (12 hands ≈ $376/day).
- ANIMALS: COW $400 (milk fyd8 iv2), SHEEP $500 (wool fyd6 iv3), GOOSE $300 (egg fyd4 iv1). Fert from CARE'd animals (~13/day at herd 15).
- HARVEST collects ALL yield_units, resets to 0.

**DEAD ENDS (session 41 — do not retry):**
- yu≥1 strb harvest ANY form (travel job, free-action): breaks water discipline → strb field dies → $43k solo. yu≥2 cadence is LOAD-BEARING.
- Fert job-value inflation (FERTILIZE 240, COLLECT 115) or fert mule (any value ≥100): workforce orbits fert pipeline → FEED/water starve → herd+strb collapse ($36k solo). The v7b value table is a fragile equilibrium; the fert fix needs CAPACITY REALLOCATION (cut mule trips via field-feeding, not new standing jobs).
- `(not race or X)` in a patch drops v6b's X requirement in SOLO — cost $40k before caught. Solo-preserving form: `(X or race_only_escape)`.
- v7c lesson: race economy v1 (early animals without feed_ok/budget) bought 1 cow then starved a week; d11-12 binge left $9 → herd escapes.

**LADDER HISTORY (seeds 10007-16 ×2, MEAN/MIN):** v5a 50,580/41,792; v6b 59,025/42,830; **v7b=v7e 83,116/66,802 GOOSE CHAMPION**; rejected: v7d-1/2 $43k (yu≥1), v7f/f-2 $36k (fert pipeline).
**H2H vs v11:** v6b 0-10; v7b 0-10 ($15-37k); v7c 0-10; v7e 0-10 ($14-61k avg 33.5k).

**NEXT SESSION LEADS:**
1. Strb fert WITHOUT new standing jobs: field-feeding (harvest wheat→FEED directly, skip shed mule) frees mule capacity; fert via COLLECT-at-source + carrying units applying 120-jobs (raise FERTILIZE only to ~150 max, test one lever).
2. SE quadrant ($4k) in race mode: v11 runs 100 tiles vs our 75.
3. Sell-timing: E6 liquidation already in; consider pre-d12 strb/melon sprint.
4. v11 tapes: re-audit its DROP-21× field-feeding pattern.
5. Build flow: v6 head + v7_tasking_block.py + scripts/patch_v7_market.py (E1-E7) → topbots/goosebot_v7.py. Run restore_champions.sh first (now also restores v7b/v7e).
