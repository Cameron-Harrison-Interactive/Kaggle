# R52 — "FIX THE WORKERS": MEASUREMENT ROUND (09-15)

Working file: `war/astra_live20_10.py` (= v29, ref 56243015, PENDING — **untouched**).
Nothing in `submit/` was modified this round. All new files live in `war/`.

---

## 0. A RULES FACT THAT REFRAMES EVERYTHING

From the competition page (Evaluation → Ranking System):

> "The actual coin difference in a match does not affect the rating change —
> **only the win, loss, or tie outcome matters**."

**We have been optimizing the wrong objective.** Every panel number in the
playbook (tetsu −92,680, elite −98,292, v21 −3,942) is a *coin margin*. The
ladder only counts W/L. From here on the primary gate is **win rate**, with
coin margin as a diagnostic only.

---

## 1. NEW TOOLS (permanent)

| file | what it does |
|---|---|
| `war/walk_probe.py` | attributes every MOVE step to the op it was walking to → moves/op per op type |
| `war/labor_probe.py` | per-day decomposition: OP / MOVE / PASS / SHED + care & fert coverage |
| `war/standing_probe.py` | per-day crew / plants / animals / weeds / dirt / cash curve |
| `war/gate.py` | 6-seed solo gate runner, multi-bot comparison |

---

## 2. THE LABOR CENSUS (v29, seed 42 — the numbers the model must beat)

```
unit-hours total   7576
  productive OP    2181   28.8%
  MOVE             3408   45.0%   <-- 1.56 moves per productive op
  PASS             1634   21.6%
  SHED              353    4.7%
```

Ops actually executed in 30 days: WATER 761 · HARVEST 405 · FEED 342 ·
COLLECT_FERT 245 · **CARE 202** · PLANT 166 · **FERTILIZE 19** · DROP 26.

Coverage vs theoretical (17 animals × 30 days = 510 animal-days):
- **CARE 202 = 40%** — the care bonus (cows +2, sheep +3 per production) is 60% unclaimed
- **FERT collected 245 = 48%**
- FERTILIZE effectively dead (19/season)

### Walk attribution — where the 3,365 moves go

| op | count | moves | moves/op | % of walking |
|---|---|---|---|---|
| WATER | 743 | 1152 | 1.55 | 34.2% |
| FEED | 342 | 721 | 2.11 | 21.4% |
| HARVEST | 378 | 520 | 1.38 | 15.5% |
| COLLECT_FERTILIZER | 232 | 391 | 1.69 | 11.6% |
| PLANT | 166 | 237 | 1.43 | 7.0% |
| PICKUP | 323 | 78 | 0.24 | 2.3% |

**Hypothesis killed by measurement:** shed round-trips are only **4.4%** of
walking (147 moves). The waste is *inter-stop travel inside the band*, not
shed logistics. Do not spend effort on shed routing.

Late-game (d21-28, 14 workers): ~103 productive ops + 185 moves out of 336
unit-hours → **55% of every worker-day is walking.**

---

## 3. THE CREW DEATH-SPIRAL (the biggest structural bug found)

The crew is sized by `build_plan`'s "smallest n with `dropped == 0`", and
`dropped` counts **only must-work** (unfed animals, ripe harvests, dying
plants). Care, fert collection and routine watering are invisible to it.

**Therefore: every routing improvement shrinks the crew.** Measured (seed 5):

```
                 d12  d13  d14  d15  d16  d17
v29    crew      13   13   14   14   14   14
       plants    35   53   62   62   70   73
       cash     6.5k 5.7k 0.9k 1.5k 3.5k 3.7k

merge  crew      10   10   12   10   10   13
       plants    30   30   26   30   30   30
       cash     1.3k 1.1k 1.0k 1.7k 3.6k 1.7k
```

Fewer hands → fewer plants tended → less cash → land/herd buys fail →
fewer quads → the work-based floor falls again. **A self-reinforcing
collapse.** This is why 7 previous "labor family" measurements came back
negative: the mechanism may have been fine, the crew feedback destroyed it.

---

## 4. EXPERIMENTS (6-seed gate: 42 / 5 / 101 / 202 / 303 / 777)

Baseline v29 = 94,426 / 97,952 / 101,359 / 95,515 / 108,729 / 89,381 = **97,894**

| variant | mechanism | avg | Δ |
|---|---|---|---|
| `live20_12` | R52a merged animal sweep (one traversal, not two) | 80,192 | **−17,701** |
| `live20_13` | R52b crew floor (cap 14) alone | 93,736 | −4,157 |
| `live20_16` | R52b crew floor (cap 13) alone | 96,792 | −1,102 |
| **`live20_15_c13`** | **R52a + R52b (cap 13)** | **101,312** | **+3,418** |

Per-seed: 42 **+4,821** · 5 **+8,946** · 101 **+1,930** · 202 **+7,767** ·
303 −2,394 · 777 −559. (4 up, 2 down; median +3,375)

Floor calibration matters and is sharp: divisor 6 → 78,486, divisor 7 →
80,192 (the floor stops binding and the spiral returns); cap 14 → 99,925,
**cap 13 → 101,312**, cap 12 → identical to cap 13.

**The two mechanisms only work together.** The routing gain frees hours;
the floor stops the planner from converting freed hours into fewer hires.
Ablation: floor-only −1,102 vs floor+merge +3,418 → the merge is worth
**~+4.5k** once the crew cannot shrink.

### H2H panels

| panel | v29 | c13 |
|---|---|---|
| vs v21 (10 seeds) | **3-7**, median −3,942 | **6-4**, median +7,229 |
| vs tetsu (11 seeds) | 0-11, median −92,680 | 0-11, median −109,369 (mean −6,350 worse) |

Mixed: c13 flips the v21 matchup from losing to winning, but regresses vs
tetsu. Not promoted yet — **and coin margin is the wrong gate anyway** (§0).

---

## 5. WHAT THIS MEANS FOR THE LONG-HORIZON MODEL

The measurements say the current architecture is not fixable by patching:

1. **The day is planned greedily, one day at a time.** Every "which crop /
   which tile / how many hands" decision is an argmax on today's board. The
   crop calendar (wheat d2-4, melon d10-12, strb ticks at +10/12/14/16) is
   fully deterministic — a 30-day plan is computable and we do not compute it.
2. **Crew size is derived from today's must-work**, which is why it
   oscillates and collapses. Crew is a *30-day capital investment*.
3. **Routes are a fixed serpentine**, not searched. 1.55 moves/op on water
   is the cost of that.
4. **Volume is decided without the price path.** More output from more hands
   crashes the shared market; c13 gains +3.4k solo but −6.4k vs tetsu for
   exactly this reason. A long-horizon model prices the volume it creates.

The prize the census puts on this: care 40% → ~100% plus the walking tax
≈ **$8-20k/season** on the current asset base, and it is the same gap the
elite tape closes with offline-searched routes (58 tiles / 0 weeds / 11-12
crew vs our 45 tiles / 5-45 weeds / 14 crew).

**Recommendation: stop patching; build the long-horizon planner.** It is our
own model — a lookahead optimizer over the season (crop calendar, capital
schedule, crew schedule, price path), not a copy of anyone's action tape.

---

## 6. THE LONG-HORIZON MODEL — `war/horizon.py` (built this round)

Standalone, stdlib-only, no engine import, no I/O, no RNG. Run it:

```
python3 war/horizon.py           # calendars, care prize, price cliffs, labour
python3 war/horizon.py --plan    # model-optimal planting schedule per day
```

Transcribed from `intel/engine_kagg_1327.py` (not from the playbook's
summary, not from memory). It values an action by what it will actually
produce, on the day it will actually produce it, at the price the market
will actually pay.

### Two engine corrections found while building it

1. **Non-ongoing crops start at `yield_units = 1`, not 0**
   (`_new_plant`: `"yield_units": 0 if cd["ongoing"] else 1`). So wheat is
   1 + 3 waterings = **4 units**, carrot 1 + 2 = **3**, melon caps at 6 by
   age 10. The playbook's "3-4 units" for wheat is the base-1 effect.
2. **Ongoing crops tick at ages 9/11/13/15, harvestable at 10/12/14/16.**
   Units land at END of day `planted + first_yield - 1 + k*interval`, so the
   WATER + FERTILIZE must land on the TICK day — the day *before* the units
   can be picked up. `needs_water()` in the live bot already does this
   correctly (`tick = first - 1`) — **verified, no bug there.** Two previous
   rounds (R40, R41) tried to capture the tick bonus and failed; it was
   never a timing bug, it was labour capacity.

### The care prize, quantified by the model

| animal | interval | units/season no care | with daily care | multiplier |
|---|---|---|---|---|
| GOOSE | 1 | 26 | 51 | **x2.0** |
| COW | 2 | 11 | 31 | **x2.8** |
| SHEEP | 3 | 8 | 29 | **x3.6** |

Measured coverage today: **care 40%, fert 48%.** We are leaving roughly
60% of the animal leg on the table — this is the $8-20k/season prize.

### Labour, priced

Measured 1.56 moves per productive op → **9.4 real ops per worker per day**.
Crew 14 = 131 ops/day for $609/day of wages. Every crop in the model now
carries its full op cost, so decisions can be ranked by **$/op** (the real
binding constraint) instead of $/tile.

### Status — and the honest limitation

`--plan` currently ranks melon first for d0-19 at flat base prices:

```
day   crop    fert    net$  units   $/op
0     MELON          1420      6  157.8
...   MELON          1420      6  157.8
20    TOMATO  +fert   310      6   44.3
22    CARROT  +fert   120      4   24.0
```

**That answer is wrong and the model knows why:** it is pricing on a flat
price path. Melon is the best crop per tile and the worst crop in volume
(squared glut, 3.6; R47 measured the 30-tile wave at −9.6k). The model is
missing the one thing that makes it *long-horizon*:

> **the price path our own supply creates.**

Next step: give `price_of` a real projected path — own projected volume,
town drain (6 drain events/day per shop instance + 1/day town centre), and
opponent supply — so the schedule becomes volume-aware. That is the
difference between a per-tile argmax and a season plan, and it is exactly
what the current `crop_score`'s hand-tuned 0.65 supply factor is fudging.


---

## 7. SHIPPED — v30, ref 56262741 (2026-09-15 21:18 UTC)

`submit/v30_champion.py` = `war/astra_live20_15_c13.py` packaged
(`war/package_v30.py`): debug log stripped, `kaggle_entry_agent = agent`
appended, provenance header prepended.

**Acceptance gates, all green:**
- stdlib only (`math`, `collections`); no file I/O, no network; 115,236 bytes
- exact-match vs the dev build on all 6 gate seeds (to the dollar)
- self-play validation: DONE / DONE on seeds 5 and 777, 720 frames each
- latency: mean 1.4 ms / p99 5.8 ms / max 132 ms against a 1,000 ms actTimeout

**Tracked pair is now v30 + v29** (v28 at 549.4 drops out of tracking).

### Ladder reality check — read this before the next round

First publicScore pull for the v27-v29 line:

| sub | publicScore |
|---|---|
| v46c | **591.1** |
| v20 | 582.4 |
| **v21** | **571.0** |
| v23 | 562.6 |
| v25 | 561.8 |
| v26 | 556.2 |
| v27 | 555.5 |
| v28 | 549.4 |
| **v29** | **519.6** |

**The line has drifted DOWN since v21 while every solo number went UP.**
v29 is the worst of the nine. Solo score is a screen, not a proxy for
rating — and rating is decided purely by win/loss. Whatever v30 does, the
next round has to be judged on W/L against the archetypes we actually meet
on the ladder, not on solo gold.

---

## 8. THE MARKET WAR MODEL (`python3 war/horizon.py --war`)

The user's doctrine, made arithmetic. The market inventory is SHARED, so a
unit we sell does two things at once: it earns us its price AND it lowers the
price of every unit they sell afterwards. So the objective is not our
revenue — it is **(our revenue) − (their revenue)**.

`marginal_war_value(item, ...)` walks the shared market day by day with the
engine's exact price function and measured town drain, then decomposes
+1 unit/day of our supply into `us_gain`, `denial`, and `differential`.

Opponent profile = the cow-heavy class that beats us (Sutee 17 animals/$85k,
Someswararao 15 cows, Ali Alghaithi 10 cows + 5 sheep). Drain = the measured
ladder consumption (milk 22/day, wool 22/day, strb 7/day, wheat 6/day).

```
  item         us/day  them/d  us_gain    denial   DIFF/op  verdict
  MELON           2.0     2.0     4856      1315     12342  harvest quietly
  WOOL            2.0     3.0     7269        63      7332  harvest quietly
  MILK            3.0     6.0     7571       894      7054  harvest quietly
  STRAWBERRY      3.5     4.0       89      3526      6025  PUSH — they depend on it
  WHEAT           6.0     6.0      630        11      2137  harvest quietly
  EGG             4.0     4.0      1210       104      1877  harvest quietly
```

**THE HEADLINE: strawberry denial is a 40:1 trade.** +1 unit/day of our
strawberries earns us **$89** and costs them **$3,526**. We are sitting at
the anchor where the gradient is steep ($1.92/unit) and they run the bigger
factory, so the price damage lands mostly on them.

**The opposite is true for milk and wool, and this is the counter-intuitive
one.** Town drain (22/day) keeps both in permanent DEFICIT — the price
gradient below the anchor is only ~$0.22/unit versus $2.10 above it. So:
- +1 milk/day earns us **$7,571** (30 units at ~$252 as the price rises to
  $331 — matching the ladder's measured "milk closes $197-331 in 26/27 games")
- and denies them only **$894**

Milk and wool are OUR harvest, not a crash target. Adding volume there hurts
us far more than them. This is the same conclusion R51 reached from the
replay data, now derived from the price function instead of observed.

### First-seller race (confirms "sell first before they profit")

```
  MILK        first $7,571 | second $7,476  -> being first worth $95/unit/day
  STRAWBERRY  first $   89 | second $  -106 -> being first worth $195/unit/day
```

Selling at h0 before their dump lands is worth $95-195 per unit per day. The
morning dump is not a style choice; it is priced.

### What this changes

1. **Strawberry is the denial weapon**, not milk or wool. The current
   `strb target = min(45, max(33, opp_strb))` mirror is pointed the right
   way — the model now says why, and prices the marginal tile.
2. **Do not chase milk/wool denial.** Harvest them. This contradicts §8b
   rule 3 (sell max daily on all of them is still right for us, but adding
   volume expecting denial is not).
3. **The differential, not our gold, is the objective.** Every allocation
   decision should be ranked by `DIFF/op`, and the model can compute it live
   from `obs.farms` (we already read their tiles and animal count hourly).

### Honest limitations

Supply rates and drain are estimates lifted from the ladder replay analysis,
not per-match measurements — the model is a marginal analysis around a static
profile, not a full game simulation. Wiring it live means replacing
`THEIR_PROFILE` with the hourly `obs.farms` census the bot already performs,
and replacing `OUR_PROFILE` with the projected output of the current plan.
That is the next build.
