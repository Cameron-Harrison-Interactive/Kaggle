# KAGGRESSURE — GAME MECHANICS & PLAYBOOK
**Everything verified from the engine source (envsrc.py). Written 2026-09-09 after the v48 reactive-brain build. This file is the permanent memory — read it before building anything.**

---

## 1. CORE LOOP
- Board **10x10**, tiles indexed `tiles[y][x]`. **30 days x 24 hours = 720 steps.** Score = final money.
- Each turn submit `{"farmer": [op], "hands": [[op], ...], "market": [orders]}` — **max 10 market orders/turn**, usable from h+1.
- Quadrants: NW (start, 25 tiles) -> NE ($1000, d5+) -> SW ($2000, d9+) -> SE ($4000, d12+). All 100 tiles buyable by d14.
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
| WHEAT | 10 | d2 | d4 | - | 6 | no |
| CARROT | 20 | d2 | d3 | - | 4 | no |
| MELON | 80 | d10* | d12 | - | 6 | no |
| TOMATO | 50 | d8 | - | 1d | 4 | yes |
| STRAWBERRY | 100 | d10 | - | 2d | 4 | yes |

(*our head uses a d6-12 window for melon; engine table says first 10 / max 12 — harmless.)

**WATER — the #1 killer mechanic:**
- `watered_today` resets at EOD. If watered -> `cuw=0`; else `cuw+1`. **`cuw >= 2` -> the plant DIES and the tile becomes a WEED.**
- So every plant must be watered **at least every other day, forever, including ongoing crops**. Elite bots (Ken Qian $101k) water everything DAILY. A water miss cascades: dead plant -> weed -> DIG needed -> tile idle.
- Watering is also required for the fertilizer bonus (below).

**ROT (non-ongoing only):** `max_lifespan_step = (planted + max_yield_day + 1) x 24`. After mls, **yield -1 every 2 HOURS** (12/day) until 0 -> tile becomes WEED. Harvest non-ongoing crops on their window day, no later.

**HARVEST:** allowed once `age >= first_yield_day`. Ongoing: harvest any time yield >= 2 (takes ALL yield_units, tile keeps producing). Non-ongoing: harvest at `yield >= max_yield` or `age >= max_yield_day` (takes all, **tile clears -> must replant**).

**FERTILIZE:** costs 1 FERTILIZER from inventory, sets `fertilized_until_day = day+2` (3 days inclusive). **On a production day, a watered + fertilized tile yields +2 instead of +1.** Only worth it on MELON/STRAWBERRY. Fertilizer sources: animal COLLECT_FERTILIZER (free) or BUY_PRODUCT.

**PLANT — ATOMIC VALIDATION (engine rule):** if the TOTAL number of `["PLANT", crop]` orders across all units in one turn **exceeds the seed count, ALL of them are dropped to PASS.** Nine stacked units demanding CARROT with 2 seeds = zero plants. -> The brain must keep a **per-hour plant budget per crop** and decrement as it assigns.

## 4. ANIMALS
| animal | cost | structure | first_yield | interval | max_held | product |
|---|---|---|---|---|---|---|
| GOOSE | 300 | COOP | d4 | 1d | 4 | EGG |
| COW | 400 | PASTURE | d8 | 2d | 6 | MILK |
| SHEEP | 500 | PASTURE | d6 | 3d | 6 | WOOL |

- **BUY_ANIMAL -> animal lands in the SHED.** Then: unit `["PICKUP", animal, 1]` at a shed tile -> walk to empty tile -> **`["BUILD_COOP"]` / `["BUILD_PASTURE"]` — FREE** (no money!) -> stand on structure -> `["PLACE", animal]`.
- **FEED: 1 wheat/day. `consecutive_unfed >= 2` -> animal ESCAPES** (structure remains empty; the money is gone). Feed every day, no exceptions.
- **CARE (free, 1/day): if cared AND fed -> +1 bonus yield on the next fed production day.** Care is pure profit.
- COLLECT_FERTILIZER when the animal's flag is set -> +1 FERTILIZER into unit inventory.
- Animal HARVEST: takes all yield_units (we harvest at >=2 goose / >=3 cow-sheep for pacing).
- Empty structures can be re-PLACEd with a new animal — no rebuild needed.
- **USER DIRECTIVE: 15-20 animals, full routing, ZERO escapes. Structures are free -> animals are early-game cash.**

## 5. SHED & LOGISTICS
- `["PICKUP", item, n]` and shed ops only work **standing on a shed-access tile**.
- **`["DROP"]` (bare) dumps the ENTIRE unit inventory into the shed.** `["PLACE", item, n]` at a shed tile drops just that item.
- Shed capacity **100** (all items combined). Keep morning sells running so EOD auto-dump never overflows.
- Seeds live in `private.seeds` — never pass through shed or inventory.
- Unit inventories: `obs.private.inventories` = list per unit (index 0 = farmer, then hands).

## 6. MARKET & PRICING — THE REVENUE LEVER (all verified this session)
- **Market inventory starts at I0 = 10,000 per item -> price = base exactly.**
- **Every SELL adds +1 to that item's market inventory (if price > $1) -> pushes price DOWN. Every BUY removes 1 -> pushes price UP.**
- Price curves (above_func x above_target = how fast price cliffs as you over-sell past I0):

| item | base$ | sell +25 over I0 | +50 | +100 | daily safe cap |
|---|---|---|---|---|---|
| WHEAT | 25 | $22 | $22 | $21 | ~100+ (log, gentle) |
| EGG | 50 | $44 | $43 | $42 | ~100+ |
| CARROT | 35 | $29 | $27 | $23 | ~60 (+400 -> $12) |
| TOMATO | 60 | ~$52 | ~$47 | ~$40 | ~60 |
| **STRAWBERRY** | 120 | **$72** | **$24** | **$1** | **~25-28** |
| **MILK** | 160 | $108 | **$55** | **$1** | **~40** |
| **WOOL** | 200 | $164 | **$55** | **$1** | **~40** |
| **MELON** | 250 | $244 | $225 | **$150** | **~40 (+200 -> $1)** |

- **Selling past the cap floors the price at $1 — the extra harvests are worth nothing that day. Sell the overflow tomorrow.**
- Scarcity side (inventory below I0): premiums — wheat -100 -> $35, strb -100 -> $204, melon -100 -> $290.
- **Town consumption drains inventory continuously (the "daily reset"):** unlocked shops consume 1-2 units of their products **every 4 steps**; town center consumes 1 of every product every 24 steps. Shops unlock every 3 days. Oversold items recover toward base/premium within a day or two.
- **USER ARBITRAGE RULE: if a price drops well under base (e.g. wheat < $15), BUY IT ALL — our buying + town consumption restore the price, then sell into the rebound. Applies to every crop.**
- **VERIFIED FAILURE: hourly dump-selling of the whole shed lost ~$7k on 3 seeds** (melon/strb/milk cliffs). The reactive brain out-harvests the tape (992 vs 700 animal ops, 939 vs 683 waters) but *earned less* because it dumped past the cliffs. **Sell pacing >= farm output.**
- Morning-batch selling is correct: EOD auto-dump means yesterday's harvests are in the shed at h0; the morning sell list (repeated hourly ONLY in hours the plan leaves empty — NEVER clobber the plan's buy orders) converts them.
- Market orders execute in lockstep per-unit between both players. PRICE_FLOOR = $1.

## 7. THE REACTIVE BRAIN (v48) — ARCHITECTURE & EVERY TRAP THAT COST US
Design (user-mandated: "a brain that thinks, not a tape"):
- `agent()` keeps a per-player session; replans the market at h0; **every hour re-parses the REAL obs** (unit positions, inventories, tiles) and decides each unit from where it actually is.
- **Sticky per-unit tasks**: unit commits to one target (walk -> act); task invalidates the hour it's done or no longer needed; 10-hour age cap. Claims dedupe targets within the hour. This killed the thrash (units were flip-flopping between targets every hour, 50-60% of hours walking).
- On-tile ops first (standing on work = do it), then shed logistics, then candidate selection by priority ladder.

**Priority ladder (current):** feed 100 > survival-water 96 (unwatered since yesterday — dies tonight) > urgent harvest 85 (non-ongoing past window, rot-watch) > prod-day water 80 > place animal 78 / care 78 > harvest 75 > routine water 68 > plant 62 (dist <= 14) > fert 55 > weed 45+2/weed > build 72 > shed-drop 85 when carrying >= 2 sellables.

**THE SEVEN TRAPS (each was a real $30-70k bug — never reintroduce):**
1. **Atomic PLANT validation** -> per-hour plant budget (see 3).
2. **Water candidates for already-watered tiles** -> units claim them, arrive, PASS forever (task never invalidates because cuw stays >= 1 until EOD). Candidate filters must EXACTLY match the on-tile branch: only `_water_due()` (returns False when watered today).
3. **Animals counted as "sellables"** -> the cow yo-yo: unit PICKUPs a cow, cows are "inventory", DROP dumps it back, repeat 3,569 times. Animals only leave inventory via PLACE.
4. **Wheat shuffle** -> every unit at the shed grabs feed wheat whenever ANY animal is unfed. Fix: global `feed_room = unfed_animals - wheat_currently_carried`; pickup only if feed_room > 0, quantity = min(feed_room, 4).
5. **BUILD on shed tiles** -> the 4 shed-access tiles are the logistics corridor; structures there jam everything (a unit carrying an animal standing on an occupied structure can neither build nor place — permanent deadlock).
6. **Hourly dump-selling** (see 6) and **clobbering plan buy orders with sells** (`if not mkt and hour >= 1` guard is mandatory).
7. **Hires must be first** in the flat order stream (see 1).

Other engine facts: shed ops resolve before the LOCKED guard (they work from locked shed tiles); `_quadrant_of`: y<5=N, x<5=W; `["HARVEST"]` takes ALL yield_units; PASS is the safe no-op.

## 8. STRATEGY PLAYBOOK (user directives 09-09)
1. **PREDICTIVE PIPELINE (next build):** we choose every planting, and grow times are deterministic — so the brain KNOWS its harvest calendar every morning: units per crop arriving today/tomorrow, which tiles free today. Use it to:
   - **Pre-sell**: the morning sell list covers yesterday's arrivals + today's EOD arrivals (paced under the 6 caps).
   - **Pre-buy replacement seeds BEFORE plots free** so every plot refills same-day. **Every plot always filled.**
   - **Pre-route hands**: day's work list (water/feed/care/plant/harvest/dig) laid out at h0, executed reactively hour by hour.
2. **15-20 animals**, feed pre-covered (wheat in NW+NE quads sized to feed + surplus), zero escapes, zero emergency runs. Coops/pastures FREE — animals are early-game cash.
3. **NO TOMATOES** — too water/labor hungry for the value (notes + user).
4. **Arbitrage:** buy any crop well under base (wheat < $15), sell into the rebound after town consumption restores price (see 6).
5. **Hire freely while daily output >= 2x hire cost** (crew 14 = $986/day -> need ~$2k/day revenue before adding the last hands).
6. Fill every tile from d8+ (bounded: strb <= d19, melon <= d22, wheat <= d26 — later sows can't pay back).

## 9. BUILD STATE (as of this file)
- **topbots/v46_snap_77k.py (v46c)** — tape control. 10-seed solo **$88,685**; live 591.1.
- **topbots/v48_brain.py** — reactive brain, crew 11-12. **3-seed $82,086** (404: $91,563 / 101: $76,585 / 202: $78,110); 10-seed $73,537. Contains all 7-trap fixes + SELL_CAP table.
- **topbots/v48_fullfarm.py** — brain + crew 14 + bounded fill. 10-seed $67,324 (crew 14 alone didn't pay — labor wasn't the bottleneck; sell pacing + pipeline were).
- **topbots/v47_fullfarm.py / v47b_wheatfill.py** — tape full-farm probes, SUBMITTED 09-09 (3 quota slots left). v47r_region = failed region router (dead end).
- Benchmark tooling (volatile /tmp): `solo_any.py` (PASS opponent, +18% scale), `h2h.py` (`timeout 1700 python3 /tmp/h2h.py A.py B.py <seeds> swap`), `envsrc.py` = engine source. Rebuild recipe in session memory.
- Standing rules: 10-seed benches only (chaos is +/- $5-12k/seed); LOCAL != LIVE; env.run only (manual stepping breaks twins); bash timeout <= 1800s; kaggle slug `kaggriculture`; quota 5/day, 3 left, lifetime 70; token KGAT_174ebff7462e0b34526c2936d51a2fc0 (nosiru).

## 10. NEXT STEPS (in order)
1. Build the **predictive pipeline** on v48: harvest calendar (deterministic from plantings) -> paced morning sells under the caps + seed pre-buys before tiles free.
2. Scale animals to 15-20 with feed pre-coverage from NW/NE wheat; verify escape count = 0.
3. Add the arbitrage buyer (wheat < $15 rule, all crops).
4. Re-bench 10-seed vs v46c; H2H vs twin; only then submit (quota 3 left).
5. Read ladder episodes for v47/v47b probes.
