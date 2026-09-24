# SESSION 88 — the execution pass, fully measured: the night window is a coordination game (REJECTED) + the real lever is the cow-first build

## 0. Live state (2026-08-29 ~01:00 UTC, fresh pull)

- v11.12 (sub 55829084): **2256.9** (up from 2246.8 at session start; holding ATH).
- v11.13 (sub 55829890): **1754.7** (up from 1739.5; still climbing).
- **Decision: HOLD the pair. No post.** The session's built variant (v11.15 night
  window) passes solo but FAILS the 80-game field matrix. Per session-87 doctrine
  (churn is the enemy, pair at ATH), nothing marginal ships.

## 1. What was attempted

The user directive (verbatim, carried from the start of the tape project):
"route the whole game start to finish making us a new tape that beats the metas…
all location and making sure nothing is wasted no passing always working and
keeping things fed / watered following the rules as a guide."

Executed as the session-86 §8 "execution pass" on the current 11c/4s build:
measure every execution lever on the bit-exact engine, build the winners, bench
them (solo 8 + 80-game matrix + ghosts). The build is a pure market-order retiming
(`_ref/build_v1115.py`, artifacts quarantined in `topbots/rejected/`).

## 2. Engine market mechanics (measured, kaggle_environments 1.32.7)

- `price(inv) = base ± target·base/f(T)·f(|inv−I0|)`; I0=10000, floor $1.
  Selling adds to inventory (price down); buying removes it (price up).
  **Sales at $1 do NOT increase market supply.**
- The TOWN absorbs every step: every 4 steps each unlocked shop consumes its
  products (1, or 2 for single-product shops), every 24 steps the town center
  consumes 1 of every product EXCEPT FERTILIZER. Absorption rates ≈
  MILK 18-19/day, STRAWBERRY 15-24/day, WHEAT 7-13/day, WOOL 12×(yarn shops)/day,
  MELON 1/day, **FERT 0** (monotone decline all game).
- FERTILIZER is produced on ANIMAL tiles: `fertilizer_available=True` is set on
  every animal tile at the daily refresh (`_daily_refresh_animals`). Max
  collectable = herd size per day. 11c/4s → ~15 fert/day → ~380-400/season.
- Shed capacity 100 (all items, one pool). Market BUY/animal BUY block at ≥100;
  EOD unit-inventory drop discards overflow. **Measured EOD shed load in the
  mid-late game: 78-98/100.**
- Hands are deleted at EOD (`farm["hands"] = []`); re-hired each day. HIRE cost
  = fib(n-th hire of the day): 1,1,2,3,5,8,13,21,34,55 | 89,144,233,377,610.
  The tape's 11-15 hands/day is structural: hands 10+ ARE the crop engine
  (D26 default: 25 WATER + 8 HARVEST + 8 PLANT by the marginal hands;
  over-10 hire cost $5.3k default route buys a $15-20k D29 harvest wave).
- Interpreter order per step: unit actions → market → town consume → EOD at
  (step+1)%24==0. So H00 market orders CAN sell the previous day's dropped stock.

## 3. The meta's night window (measured from the top-60 harvest)

TOP_LADDER_LIBRARY.json: **every 11c/4s team at 2527-2765** (Mingkang YAN 2765,
SJY321 2725, SCNU 2731, Janus 2679, prvsiyan 2677, peikopon 2658, ebisu_ya 2708,
Joseph Adamski 2622, Omer Faruk 2626, Ueddy 2604, Zyy7390 2599, YJR 2598, Arda
Ceylan 2589, senkin13 2588, G!vIOne 2583, PrasadChopade213 2582, CroDoc 2574,
Yizuki 2570, Izzoudine 2570, Dude and Destroy 2564, DeeperNet 2559, Terry Luo
2547, Lenin Goud 2542, Timbydude 2539, GIN 2531, iwance 2529, Will 2527) sells at
**H22/H23/H00/H02** with h1_share 1-2%, max_hands 15, fert_sold ~397. Our v11.12
tape sells mid-day (top hours H05/H09/H13/H17/H21).

Mechanics: for absorption-dominated items (milk/strawberry/wheat) the price
RISES through the day and peaks at H22-H23; the meta dumps at H23/H00 after the
peak. Against same-build meta bots the night curve is the live curve; H22 (one
hour ahead of their H23/H00 wave) also gets the pre-their-dump price.

## 4. v11.15 night window — built, benched, REJECTED

Change: move SELL {MILK, STRAWBERRY} from H05..H21 into H22→H23→H01→H02 (same
day first, then next day; H00 is full of HIREs). Market orders only — no
tile-state change → RNG-safe (routes cannot flip). Default route: 501 units
moved, zero cap conflicts.

Bench (bit-exact engine):
- **Solo 8 seeds: ALL GREEN, +$321/seed avg** (+409/+411/+769/+287/+108/+376/+4/+204),
  0 escapes, herds identical.
- CD ghost (ep 101359580, seed 1364649034, we seat 1): us 137,251 (+273 vs
  v1112's 136,978); margin −2,207 vs v1112's −1,768 (the ghost also gains —
  entangled price paths; treat as noise per session-86).
- **80-game field matrix (bt/v46/k2900/moon/soil × 8 seeds × 2 seats): −$546/game
  (19+/61−), escape delta −1.** By opponent: bt −182, k2900 −123, moon −150,
  soil −253, **v46 −2,024** (v46 seed 7/11/19: −$2.8k/games, 3 win→loss flips).
- Milk-only variant (v11.15m): solo all green +$236/seed; v46 still −$508/game
  (16/16 negative).

**Verdict: the night window is a COORDINATION strategy, not a free lunch.**
Intraday price curves are opponent-dependent: vs a passing opponent the curve
rises (absorption > our sells) → night is best; vs a mid-day-selling opponent
(v46 class) their dumps push the intraday price down → night is the TROUGH.
No universal intraday schedule exists. On the ladder at #199 most opponents are
non-meta mid-day sellers → net negative. Fails the field-matrix gate.
Quarantined: `topbots/rejected/v1115_exec.py`, `v1115_milk.py`,
builder `_ref/build_v1115.py`.

**When the night window WOULD be the right ship:** after our pair climbs into
the 2400-2800 band where opponents are mostly the same-build meta (night
sellers). Keep the artifacts; it is a ~+$300-500/game edge vs meta opponents
and −$500 vs non-meta. A future route-gate could select it reactively — but
that is runtime code (new risk class) and not worth it at current rating.

## 5. Levers measured and closed (do not retry)

| lever | measurement | verdict |
|---|---|---|
| FERT front-load to H00 | wash-to-negative: own early units depress all later FERT prices (0.2/unit × ~250 later units); D1-D3 H00 shed stock is 0 (tape's early FERT sells are SAME-DAY collection — first attempt broke D1 strawberry-seed funding, −$80 at D1H17) | closed |
| Milk D22-D23 → D24 hold | infeasible: D23 EOD shed 78/100; holding 49 milk overflows → ~$10k milk discarded | closed |
| Strawberry D24 → D26 hold | infeasible: D24 EOD shed 98/100 | closed |
| Strawberry same-day → H23 | solo +$49/seed (noise: ±$200 per seed; windows are 2-4, not 7) | closed |
| Hire trims (>10/day) | marginal hands are the crop engine (25W/8H/8P on D26); $5.3k buys the D29 wave | closed |
| Wheat MM volume | net wash: US $136.8k buy / $141.1k sell; CD runs the same pattern ($94k/$56.6k). The "wheat edge" (3,402 sold) = 3,311 bought + 438 grown | closed |
| D0 cow-swap (14a/b1/c/d/e1) | sessions 86-87: catastrophic/flat | closed |
| DJA standing-sweep FERT | "2,935 FERT sold" = intended order volume, not commits (max collectable = herd size/day ≈ 350-400/season; our 397 already ≈ max) | artifact, closed |

## 6. Where the gap actually is (measured, CD + DJA games)

- **CD game (ep 101359580, −$1.8k vs #1):** both players run near-optimal
  execution; the gap = build. CD 16 cows → 36 milk on D27 (us 8) and 335 milk
  total (us 337 ≈ tied on milk VOLUME but CD's is earlier and better-timed);
  D24: CD 12 melons @123 vs us 11 @139 (we got better prices, they got more);
  D13-D14: CD's days are pure sell days (spend <$1k), ours interleave the MM
  cycle (wash, but ties shed capacity). Same-build vs CD: our D21-D23 clawback
  wins; D27 is the margin (−$6.5k).
- **DJA game (ep 101381927, −$10.2k):** DJA 6c/8s from a D0 2c/2s cow-leaning
  opening; bigger melon wave (66 vs 48 on D10 ≈ $5-6k); all-day FERT sweep
  (sells collected fert immediately, every hour — the right call on a monotone
  declining price, worth ~$200-400); consistent late-game tempo (D21 +9.5k,
  D23 +5.8k, D27 +5.0k, D29 +8.8k). Gap = build + melon count + sweep cadence.
- **The 2257→2800 "gap"**: the 27 same-build teams at 2527-2765 prove the build
  reaches that band; the residual tape edge (night window) is a ±$0.5k
  coordination swing, not the driver. The driver of OUR rating vs theirs = game
  volume at the top + the cow-heavy mid-band losses (meryol/cheezyp/Lucien class,
  ~−$13-22k each) which only a bigger animal build fixes.

## 7. Next build (the real lever): CD-style full cow-first rebuild

Scoped in session 86 §10, de-risked in session 87, now with this session's
numbered constraints:

1. **D0-D3:** COW-first opening (2c/2s D0 + 2c D2 per the 14a edit set — the
   D0 sheep cut is FATAL to the wool engine, so the cow-first build must fund
   cows from D1-D3 headroom, not D6 wool: CD's D5 cash = $30, all-in animals).
   Final herd target 12-16c/3-4s.
2. **Feed scale-up is the hard part:** 12-16 animals need ~14 hand-fed FEED
   slots/day; our D5+ circuits are 6 hands/4-5 FEEDs. CD runs 12 hands for 16
   cows. This is hand-choreography authoring per route, verified per-animal
   per-day ≥28/30 fed on all 8 bench seeds (the (2,1)-class discipline).
3. **Shed capacity is the binding constraint (NEW this session):** the current
   tape runs the shed at 98/100. A bigger animal build (more milk/wool) + the
   MM wheat cycle WILL overflow. The rebuild must either (a) shrink the MM
   volume (wheat_batch 60 → ≤30 or disable in the mid-game), or (b) sell milk
   daily-in-shed like the meta (they never hold >~20 milk — the H00 sweep does
   it for free). Expect to give up ~$1-2k of MM wash revenue for shed headroom.
4. **Bench gates (all must pass):** solo 8 all-green (0 escapes, per-animal feed
   coverage), 80-game matrix vs v11.12 non-regression, ghost A/B vs CD +
   haodou + Djaafar + Sahil (must flip ≥3 of the 6) + the 21-regress ghosts
   stay green.
5. **Ship:** post retires v11.13 (weaker-rated active); floor = v11.12's rating.
   Only after the pair has ≥48h of v11.12 at ATH so the floor is solid.

Estimated effort: multi-day (route authoring × 5 suffixes + verification).
Do NOT ship anything else in the meantime (churn doctrine).

## 8. Artifacts

- `topbots/rejected/v1115_exec.py` + `v1115_milk.py` + `_ref/build_v1115.py` —
  the night-window execution pass (rejected on the field matrix; keep for the
  future meta-band route gate).
- `/tmp/cd_instr2.json`-style instrumentation + `_ref/run_isolated.py`
  (v1115/v1115m registered, paths pointed at rejected/).
- This report. The bench logs for the 80-game matrix are in
  /tmp/matrix1115.json + /tmp/matrix1112.json (re-derivable via run_isolated).

## 9. Bottom line for the user

The execution pass is DONE as a measurement, not a ship: every lever on the
current tape was quantified on the bit-exact engine. The tape is already near-
optimal for the 11c/4s build (0.4% farmer PASS, 6% hand PASS, feed/water
discipline holds, market maker wash-neutral, sells at the right times for the
opponents we actually face). The meta's one real tape edge — the night window —
is a coordination swing (±$0.5k) that is net-negative at our current ladder
position, and it is quarantined with the evidence for the day we climb into the
meta band. The gap to 2800+ is the BUILD (16 cows, melon count, sweep cadence),
which is scoped in §7 as the next dedicated build. The live pair (v11.12 2256.9
+ v11.13 1754.7) holds the team ATH and both are still climbing — holding is
the correct play today.

## SESSION 89b ADDENDUM — sell-peak move benched, REJECTED (cash-flow risk)

The execution-pass "sell-band tuning" lever was benched this session:
- Naive "move all morning sells to the peak hour (H17)" variant (v1115_sp): **−$120k/seed** (catastrophic). It starved the midday buys that the morning sells fund. REJECTED (quarantined in topbots/rejected/v1115_sellpeak_catastrophic.py).
- The hands are re-hired daily (per-day hands); the over-10 hands (idx>=10) do CROP work (WATER/HARVEST/PLANT/DIG/FERTILIZE), not FEED (only 2 FEED actions D10-D29 on the default route). So the fib hire cost is the price of getting the crop work done — the meta (same 11c/4s build) also hires 10-15 hands/day. The fib cost is NOT a differentiator.
- The cash curve is tight early (D0-D9: $62-$1,700) and abundant late (D10+: $2,700+). Moving early-game sells is risky (starves the purchases); moving late-game sells (D10+) is safe (cash is abundant) but those sells are already concentrated in the peak hours (H17/H21/H22/H23).

Conclusion: the sell-peak move is a modest, cash-flow-risky lever. The naive version breaks the cash flow. A surgical version (only move sells that don't starve same-day downstream buys) is complex and the edge is modest (a few hundred dollars per game).

The real gap vs the meta (CD +$9k D13-D20, +$9.3k D27) is PRODUCTION (more cows), not sell-timing. The cow-first rebuild (the 2800->3000 swing) is the real lever, but it's a multi-day build (sessions 86-87 judged it dead in any tractable form; it requires a full cash-flow rebuild + scaled feed choreography for 12-16 animals).

Given the context budget, the next step is a SURGICAL sell-peak move (only move sells that don't starve same-day downstream buys) OR the cow-first rebuild (multi-day). The user should decide which direction to take.

## SESSION 89c ADDENDUM — over-10 hands are load-bearing (crop work), not a lever

Finding: the over-10 hands (idx>=10) do CROP work (WATER/HARVEST/PLANT/DIG/FERTILIZE),
not FEED (only 1-2 FEED actions D10-D29 on the default route, 0 on yarn_second).
They are load-bearing for the D26-D29 crop replanting (carrot/wheat). They can't be
removed. The over-10 fib cost is the price of getting the crop work done.

The meta (same 11c/4s build) also hires 10-15 hands/day (same build, same crop work).
So the over-10 fib cost is NOT a differentiator. The meta also pays the fib cost.

Conclusion: the over-10 hands are a load-bearing cost, not a lever. The real lever
is the cow-first rebuild (more cows), which is a multi-day build (sessions 86-87
judged it dead in any tractable form; it requires a full cash-flow rebuild +
scaled feed choreography for 12-16 animals).

The D27 gap (CD +$9.3k vs our +$2.8k) is a PRODUCTION gap (CD has 16 cows, we have
11 cows). It's a BUILD gap, not a sell-timing gap. The sell-timing gap is modest
(a few hundred dollars per game) and cash-flow-risky.

Given the context budget, the next step is the cow-first rebuild (the 2800->3000
swing), which is a multi-day build. The user should decide whether to continue
in this session or start a fresh session.
