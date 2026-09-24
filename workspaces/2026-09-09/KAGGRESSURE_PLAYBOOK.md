# KAGGRESSURE — GAME MECHANICS & PLAYBOOK
**Everything verified from the engine source (envsrc.py). Written 2026-09-09 after the v48 reactive-brain build. This file is the permanent memory — read it before building anything.**

---

## 1. CORE LOOP
- Board **10×10**, tiles indexed `tiles[y][x]`. **30 days × 24 hours = 720 steps.** Score = final money.
- Each turn submit `{"farmer": [op], "hands": [[op], ...], "market": [orders]}` — **max 10 market orders/turn**, usable from h+1.
- Quadrants: NW (start, 25 tiles) → NE ($1000, d5+) → SW ($2000, d9+) → SE ($4000, d12+). All 100 tiles buyable by d14.
- Shed sits at board center; **shed-access tiles = (4,4), (4,5), (5,4), (5,5)** (NWSE order).
- Crew cost/day: 10=$143, 11=$232, 12=$376, 13=$609, 14=$986. **Hires MUST be first in the order stream** (hires-last reorder = $10k death, verified).

## 2. UNITS
- Farmer + hands. **Hands despawn at EOD and are re-hired every morning** (daily re-hire mandatory).
- **EOD: every unit's inventory AUTO-DUMPS to the shed** (overflow above capacity 100 is discarded). Units do NOT need to walk home — but keep the shed below ~90 so nothing is lost.
- Farmer + hands all teleport to the shed area at EOD. Farmer can't move at h0 (spawn rule — we PASS it).
- MOVE = 1 tile/hour, onto LOCKED allowed (ops there no-op). All tile ops act on the tile you STAND on.
- Hand spawn = first free shed-access tile (min occupancy).

## 3. CROPS (all numbers verified)
| crop | seed$ | first_yield | max_yield_day | interval | max yield | ongoing |
|---|---|---|---|---|---|---|
| WHEAT | 10 | d2 | d4 | – | 6 | no |
| CARROT | 20 | d2 | d3 | – | 4 | no |
| MELON | 80 | d10* | d12 | – | 6 | no |
| TOMATO | 50 | d8 | – | 1d | 4 | yes |
| STRAWBERRY | 100 | d10 | – | 2d | 4 | yes |

(*our head uses a d6-12 window for melon; engine table says first 10 / max 12 — harmless.)

**WATER — the #1 killer mechanic:**
- `watered_today` resets at EOD. If watered → `cuw=0`; else `cuw+1`. **`cuw ≥ 2` → the plant DIES and the tile becomes a WEED.**
- So every plant must be watered **at least every other day, forever, including ongoing crops**. Elite bots (Ken Qian $101k) water everything DAILY. A water miss cascades: dead plant → weed → DIG needed → tile idle.
- Watering is also required for the fertilizer bonus (below).

**ROT (non-ongoing only):** `max_lifespan_step = (planted + max_yield_day + 1) × 24`. After mls, **yield −1 every 2 HOURS** (12/day) until 0 → tile becomes WEED. Harvest non-ongoing crops on their window day, no later.

**HARVEST:** allowed once `age ≥ first_yield_day`. Ongoing: harvest any time yield ≥ 2 (takes ALL yield_units, tile keeps producing). Non-ongoing: harvest at `yield ≥ max_yield` or `age ≥ max_yield_day` (takes all, **tile clears → must replant**).

**FERTILIZE:** costs 1 FERTILIZER from inventory, sets `fertilized_until_day = day+2` (3 days inclusive). **On a production day, a watered + fertilized tile yields +2 instead of +1.** Only worth it on MELON/STRAWBERRY. Fertilizer sources: animal COLLECT_FERTILIZER (free) or BUY_PRODUCT.

**PLANT — ATOMIC VALIDATION (engine rule):** if the TOTAL number of `["PLANT", crop]` orders across all units in one turn **exceeds the seed count, ALL of them are dropped to PASS.** Nine stacked units demanding CARROT with 2 seeds = zero plants. → The brain must keep a **per-hour plant budget per crop** and decrement as it assigns.

## 4. ANIMALS
| animal | cost | structure | first_yield | interval | max_held | product |
|---|---|---|---|---|---|---|
| GOOSE | 300 | COOP | d4 | 1d | 4 | EGG |
| COW | 400 | PASTURE | d8 | 2d | 6 | MILK |
| SHEEP | 500 | PASTURE | d6 | 3d | 6 | WOOL |

- **BUY_ANIMAL → animal lands in the SHED.** Then: unit `["PICKUP", animal, 1]` at a shed tile → walk to empty tile → **`["BUILD_COOP"]` / `["BUILD_PASTURE"]` — FREE** (no money!) → stand on structure → `["PLACE", animal]`.
- **FEED: 1 wheat/day. `consecutive_unfed ≥ 2` → animal ESCAPES** (structure remains empty; the money is gone). Feed every day, no exceptions.
- **CARE (free, 1/day): if cared AND fed → +1 bonus yield on the next fed production day.** Care is pure profit.
- COLLECT_FERTILIZER when the animal's flag is set → +1 FERTILIZER into unit inventory.
- Animal HARVEST: takes all yield_units (we harvest at ≥2 goose / ≥3 cow-sheep for pacing).
- Empty structures can be re-PLACEd with a new animal — no rebuild needed.
- **USER DIRECTIVE: 15–20 animals, full routing, ZERO escapes. Structures are free → animals are early-game cash.**

## 5. SHED & LOGISTICS
- `["PICKUP", item, n]` and shed ops only work **standing on a shed-access tile**.
- **`["DROP"]` (bare) dumps the ENTIRE unit inventory into the shed.** `["PLACE", item, n]` at a shed tile drops just that item.
- Shed capacity **100** (all items combined). Keep morning sells running so EOD auto-dump never overflows.
- Seeds live in `private.seeds` — never pass through shed or inventory.
- Unit inventories: `obs.private.inventories` = list per unit (index 0 = farmer, then hands).

## 6. MARKET & PRICING — THE REVENUE LEVER (all verified this session)
- **Market inventory starts at I0 = 10,000 per item → price = base exactly.**
- **Every SELL adds +1 to that item's market inventory (if price > $1) → pushes price DOWN. Every BUY removes 1 → pushes price UP.**
- Price curves (how fast price cliffs as you over-sell past I0):

| item | base$ | sell +25 over I0 | +50 | +100 | daily safe cap |
|---|---|---|---|---|---|
| WHEAT | 25 | $22 | $22 | $21 | ~100+ (log, gentle) |
| EGG | 50 | $44 | $43 | $42 | ~100+ |
| CARROT | 35 | $29 | $27 | $23 | ~60 (+400 → $12) |
| TOMATO | 60 | ~$52 | ~$47 | ~$40 | ~60 |
| **STRAWBERRY** | 120 | **$72** | **$24** | **$1** | **~25-28** |
| **MILK** | 160 | $108 | **$55** | **$1** | **~40** |
| **WOOL** | 200 | $164 | **$55** | **$1** | **~40** |
| **MELON** | 250 | $244 | $225 | **$150** | **~40 (+200 → $1)** |

- **Selling past the cap floors the price at $1 — the extra harvests are worth nothing that day. Sell the overflow tomorrow.**
- Scarcity side (inventory below I0): premiums — wheat −100 → $35, strb −100 → $204, melon −100 → $290.
- **Town consumption drains inventory continuously (the "daily reset"):** unlocked shops consume 1-2 units of their products **every 4 steps**; town center consumes 1 of every product every 24 steps. Shops unlock every 3 days. Oversold items recover toward base/premium within a day or two.
- **USER ARBITRAGE RULE: if a price drops well under base (e.g. wheat < $15), BUY IT ALL — our buying + town consumption restore the price, then sell into the rebound. Applies to every crop.**
- **VERIFIED FAILURE: hourly dump-selling of the whole shed lost ~$7k on 3 seeds** (melon/strb/milk cliffs). The reactive brain out-harvests the tape (992 vs 700 animal ops, 939 vs 683 waters) but *earned less* because it dumped past the cliffs. **Sell pacing ≥ farm output.**
- Morning-batch selling is correct: EOD auto-dump means yesterday's harvests are in the shed at h0; the morning sell list (repeated hourly ONLY in hours the plan leaves empty — NEVER clobber the plan's buy orders) converts them.
- Market orders execute in lockstep per-unit between both players. PRICE_FLOOR = $1.

### 6b. WAR-GAME MARKET FACTS (verified 09-09 PM from engine source + 375 real replays)
- **Market is SHARED in H2H** — same inventory for both players. Price war is mechanically real.
- **Market orders execute from the SHED — no unit, no walking, no labor.** 10 orders/turn; `["SELL",item,n]` drains n units one at a time.
- **BUY_PRODUCT exists ONLY for WHEAT + FERTILIZER** — crop arbitrage is only possible on those two (wheat rebound buy is real).
- **Sales at $1 do NOT add inventory** (floor sales can't crash the price further).
- **obs.farms exposes BOTH farms every hour** — enemy money, tiles, crew, animal count are all readable (enemy shed/seeds hidden; shared market.inventory visible).
- **reward = farm money at step 719** — anything in shed/on units at the horn is worth $0.
- **The two sell modes:** PEACETIME (solo/absolute gold) = pace under the §6 caps; **WAR (H2H differential) = volume + timing** — every $ of price we destroy on items the ENEMY relies on is kept differential even if it costs us some revenue. Never burn more own revenue than you deny (see §8b).

## 7. THE REACTIVE BRAIN (v48) — ARCHITECTURE & EVERY TRAP THAT COST US
Design (user-mandated: "a brain that thinks, not a tape"):
- `agent()` keeps a per-player session; replans the market at h0; **every hour re-parses the REAL obs** (unit positions, inventories, tiles) and decides each unit from where it actually is.
- **Sticky per-unit tasks**: unit commits to one target (walk → act); task invalidates the hour it's done or no longer needed; 10-hour age cap. Claims dedupe targets within the hour. This killed the thrash (units were flip-flopping between targets every hour, 50-60% of hours walking).
- On-tile ops first (standing on work = do it), then shed logistics, then candidate selection by priority ladder.

**Priority ladder (current):** feed 100 > survival-water 96 (unwatered since yesterday — dies tonight) > urgent harvest 85 (non-ongoing past window, rot-watch) > prod-day water 80 > place animal 78 / care 78 > harvest 75 > routine water 68 > plant 62 (dist ≤ 14) > fert 55 > weed 45+2/weed > build 72 > shed-drop 85 when carrying ≥ 2 sellables.

**THE SEVEN TRAPS (each was a real $30-70k bug — never reintroduce):**
1. **Atomic PLANT validation** → per-hour plant budget (§3).
2. **Water candidates for already-watered tiles** → units claim them, arrive, PASS forever (task never invalidates because cuw stays ≥1 until EOD). Candidate filters must EXACTLY match the on-tile branch: only `_water_due()` (returns False when watered today).
3. **Animals counted as "sellables"** → the cow yo-yo: unit PICKUPs a cow, cows are "inventory", DROP dumps it back, repeat 3,569 times. Animals only leave inventory via PLACE.
4. **Wheat shuffle** → every unit at the shed grabs feed wheat whenever ANY animal is unfed. Fix: global `feed_room = unfed_animals − wheat_currently_carried`; pickup only if feed_room > 0, quantity = min(feed_room, 4).
5. **BUILD on shed tiles** → the 4 shed-access tiles are the logistics corridor; structures there jam everything (a unit carrying an animal standing on an occupied structure can neither build nor place — permanent deadlock).
6. **Hourly dump-selling** (§6) and **clobbering plan buy orders with sells** (`if not mkt and hour >= 1` guard is mandatory).
7. **Hires must be first** in the flat order stream (§1).

Other engine facts: shed ops resolve before the LOCKED guard (they work from locked shed tiles); `_quadrant_of`: y<5=N, x<5=W; `["HARVEST"]` takes ALL yield_units; PASS is the safe no-op.

## 8. STRATEGY PLAYBOOK (user directives 09-09)
0. **PRICE WAR (09-09 PM, user directive — overrides solo-style pacing in H2H):** we don't need max gold, we need MORE gold than the opponent at the horn. Crash the prices of what THEY sell, each morning, so their engine starves. Full dump ~d28 no matter the prices — at d30 anything left in shed/on workers is a loss. Details in §8b and intel/WAR_MODEL_0909.md.
1. **PREDICTIVE PIPELINE (next build):** we choose every planting, and grow times are deterministic — so the brain KNOWS its harvest calendar every morning: units per crop arriving today/tomorrow, which tiles free today. Use it to:
   - **Pre-sell**: the morning sell list covers yesterday's arrivals + today's EOD arrivals (paced under the §6 caps).
   - **Pre-buy replacement seeds BEFORE plots free** so every plot refills same-day. **Every plot always filled.**
   - **Pre-route hands**: day's work list (water/feed/care/plant/harvest/dig) laid out at h0, executed reactively hour by hour.
2. **15–20 animals**, feed pre-covered (wheat in NW+NE quads sized to feed + surplus), zero escapes, zero emergency runs. Coops/pastures FREE — animals are early-game cash.
3. **NO TOMATOES** — too water/labor hungry for the value (notes + user).
4. **Arbitrage:** buy any crop well under base (wheat < $15), sell into the rebound after town consumption restores price (§6).
5. **Hire freely while daily output ≥ 2× hire cost** (crew 14 = $986/day → need ~$2k/day revenue before adding the last hands).
6. Fill every tile from d8+ (bounded: strb ≤ d19, melon ≤ d22, wheat ≤ d26 — later sows can't pay back).

### 8b. THE WAR MODEL (built from 375 replay intel — full detail: intel/WAR_MODEL_0909.md)
**Enemy revenue mix (measured):** our mid-tier bracket: WHEAT 33% · WOOL 17% · MELON 14% · FERT 12% · STRB 11% · MILK 10%. Top-40 meta: STRB 22% · MELON 14% · MILK 13% · FERT 11% · WHEAT 11% · WOOL 9%. Winners and losers run the SAME build (crew 12, quads 3, ~17 animals, ~290 fert sold) — the meta is converged; the edge is pricing/timing.
**Cliff reachability:** STRB +62 oversold → $1 (easiest crash). WOOL +59 → $1 (self-crashes anyway: 55% of games end <$10). MILK +94 → $1 (self-crashes: 51% end <$10). MELON +160 → $1 (holds $120 median — best big crop; NO town drain so once dead stays dead). WHEAT **cannot go below ~$17-20** (log cliff) — but unpinned it ends $40 (scarce). EGG uncrashable (log). FERT crashes to $1 by mid-game (sell it early, daily).
**v49 war rules:**
1. WHEAT FLOOD: sell all wheat daily from d0 h0 except 2-day feed reserve (reserve → 0 from d27). Pins wheat ~$20-25 vs the natural $35-46 late scarcity → denies ~$5-10k on their biggest stream (33% in our bracket) while our volume still pays.
2. FIRST-SELLER: at h0 sharp sell yesterday's shed stock (zero labor) before enemy morning/evening dumps; keep standing sells all day. Lockstep is 1:1 — early + max volume wins the good price.
3. MELON/MILK/WOOL/STRB/FERT/EGG/CARROT: sell max daily, no self-pacing (SELL_CAP was peacetime logic). First waves sell at high price anyway = max revenue + glut pressure.
4. Melon wave 1 (their d10-13, $250→150) is unstoppable — MATCH it (sell ours first). Their wave 2 (d20+) lands on whatever our combined volume has crashed it to.
5. Our uncrashable anchor income: WHEAT volume + EGG ($40-57 all game) + early MELON wave + FERT sold before it crashes.
6. Arbitrage: wheat/fert only (engine limit). Buy wheat < $18, resell ≥ $22 after town drain rebound; spare cash only.
7. ENDGAME: last plant melon d17 / strb d24 / wheat d27 (anything later can't ripen). d28+: sell EVERYTHING every hour incl. feed wheat. Field already does this (median $0 left in shed).
8. SPY obs.farms hourly: enemy money (cash-choke check), enemy crop tiles (their harvest calendar = predictable), enemy animals (future sell volume per item → what to crash).
Bench the war H2H (differential), NOT solo — solo scores will look worse by design while denial wins episodes.

## 9. BUILD STATE (updated 09-10 — ENGINE-TRUTH + USER QUAD SYSTEM SESSION)
**Directory: /home/user/war/. Root: /home/user/v58_champion.py (TOMORROW'S FIRST SLOT — unchanged).**
- **PENDING SUBMISSION: v58** (17-3 v56i, 19-1 v55b). v65 not ready; do NOT submit it.
- **ENGINE TRUTH (read from kaggle_environments envs/kaggriculture/kaggressure.py source — PERMANENT ASSETS):**
  - **Water**: one water/day max; crop DIES at consecutive_unwatered >= 2 (every-other-day = survival floor). Non-ongoing (wheat/carrot/melon): each watering in window [(max_yield_day+1)//2 .. max_yield_day] = +1 unit (+2 if fertilized that day) — MISSING A WINDOW DAY = LOST YIELD, so these need DAILY water in window. Ongoing (strb/tomato): +1 at EOD on interval days EVEN IF UNWATERED; water only matters for survival + the fert doubling on production days. **Strb (interval 2): water every other day on production days = zero loss.**
  - **Animals**: base product accrues on interval days regardless of feeding. CARE bonus (+1) only lands when cared AND fed on a production day (pending_care_bonus pops on next prod day if fed then; caring on non-fed days is 100% waste). FEED = 1 wheat; escape at consecutive_unfed >= 2 (feed every other day = survival; sheep interval 3 still needs every-other-day feed). fertilizer_available = True EVERY day per animal (COLLECT daily = the fert engine — nb3's #1 income). max_held cow/sheep 6, goose 4 (harvest before cap).
  - **obs exposes raw tile dicts**: placed_day, consecutive_unfed, pending_care_bonus, fertilizer_available — production days are EXACTLY computable: dsf = (day+1) - placed_day - first_yield_day; prod when dsf >= 0 and dsf % interval == 0.
  - **Decay**: non-ongoing crops rot after day (planted + max_yield_day + 1), -1 yield per 2 HOURS; strb dies after 4th production. Day-4 carrot deaths in v65 logs were old age, not neglect.
  - Walk = ONE manhattan step per hour. A "route" costs steps + actions, NOT stops. (This bit v65 twice.)
- **USER'S main.py (WorkSpace.../kaggressure/main.py) READ + BENCHED**: $66-99k solo, runs clean. Architecture = the football play: no dedicated animal workers (on-the-way service), quad ownership + serpentine 5x5 sweeps, harvest->replant->water one pass, town/opponent reading, anti-mirror signature, crew by counted work. Its gaps (user called them): watering discipline (EOD unwatered up to 20; 9 weed-deaths), 12 animal ESCAPES, only 2 quads opened, work share 21%/PASS 2064h. topbots/main.py + agent/main_v25_wheat16.py also exist (unread).
- **v65_quad.py (IN THE SHOP, NOT CHAMPION)**: full quad system built per user spec — 3 crew/quad +1/5 animals + Fibonacci peak (opener 8), herd 6/6/8 as 5-per-quad straight lines on shed-side rows (N:y=3/S:y=6, QUOTA NW 2C/1S/2G, NE 2/2/1, SW 1/2/2, SE 1/1/3), engine-exact service schedule (feed prod+survival, care prod days only, collect daily), per-quad water-level planting capped at 4 tiles/hand, quad-affinity backlog, land d10. **6 debug iterations; best $33k solo vs v58 $107k.** Fixed along the way: (1) day-0 animal buys ate the seed budget ($3000->$626 — `else 6` ramp bug, also present in v63, explains part of v63's loss); (2) live-position quad-affinity sort caused walk THRASH (claims flip as units cross quad borders — affinity must be the static plan-time assignment); (3) routes that don't fit a day kill their tails (deaths clustered at route ends); (4) walk-blind 14-task chunks (~40h routes) -> walk-aware NN chunks (steps+actions <= 18). **Remaining unexplained: work share only 18-22% with tasks planned (units PASS while work exists); escapes 24-28 continue; farm stalls ~21 tiles.** Next debug: per-hour watcher on day 10-15 with chunk->unit assignment logged (which unit holds which chunk, what it actually does each hour).
- Controls: v58 (champion), v65 (in shop), v61-v64 (rejected ablations), v60 (sparring only), user_main.py (his architecture, benched), tt_router + tetsu line (opponents). MCP monitor §11b.

## 10. NEXT STEPS (in order)
1. **TOMORROW FIRST SLOT: submit v58** (`KAGGLE_API_TOKEN=KGAT_174eb... python3 -m kaggle competitions submit -c kaggressure -f /home/user/v58_champion.py -m "v58 math crew + clustering + economy floors"`). VERIFY a new submission id appears.
2. **v65 debug session (continue the quad system)**: per-hour watcher on days 10-15 logging (a) chunk->unit assignment at plan time, (b) each unit's action each hour, (c) unexecuted route tails. Hypotheses to test: executor/backlog interaction starving routes (units bail to backlog mid-route?), shed-wheat exhaustion breaking FEED chains, spawn desync between planned and actual hands. Fix ONE thing, re-run solo, target work share 33%+ (v58 level) before any H2H.
3. Then re-bench: v65 vs v58 H2H; only if it wins does the quad system replace the wedge chassis. The engine-truth schedule (feed/care on production days only) is proven-correct regardless — port it into v58 as a single-change ablation (v58 currently feeds/cares EVERY animal EVERY day = ~40 wasted ops/day at herd 20).
4. Standing rules: H2H swap only; single-change ablations; PASSbot crash gate; env = "kagg"+"riculture" in ke.make (dir/file names same; competition = "kagg"+"ressure"); workspace folder "kaggressure" (ri) vs competition "kaggressure" (re) — always resolve paths by glob; verify submission IDs.
