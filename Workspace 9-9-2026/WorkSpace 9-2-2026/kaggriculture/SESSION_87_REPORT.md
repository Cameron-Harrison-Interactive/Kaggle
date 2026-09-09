# SESSION 87 — v11.14 cow-first: all tractable variants benched DEAD; the wool-engine law; HOLD the pair

## 0. Live state (2026-08-28 ~19:50 UTC, fresh pull)

- **Team #199 @ 2246.8 — all-time high** (above the old 1994.5 v11.7 peak).
- Active pair: v11.12 (sub 55829084, **2246.8**, holding the ATH) + v11.13 (sub
  55829890, **1739.5**, still climbing from 600; ~14h old).
- Both winning (v11.12 48W-33L, v11.13 51W-22L at last audit; no escapes since
  the v11.12 (2,1) class kill). Games every ~4 min.
- **Decision: HOLD the pair. No post today.** (Session-86 ship decision stands;
  every variant benched this session is negative — there is nothing to ship.)

## 1. What was attempted this session

The unfinished work from SESSION 86 §9/§10: the v11.14 cow-first rework
("next ship = the full cow-first rework once benched green"). Three variants
were designed, built, and benched on the bit-exact local engine
(kaggle_environments 1.32.7, 8-seed solo battery, per-animal per-day feed
coverage audited — `verify_v1114.py`).

### 1a. v1114e1 — 1c/3s D0 (the (4,4) sheep → cow). REJECTED, quantified.
5-edit tape: s0 (COW 1 + SHEEP 3, MELON 5, WHEAT 3), s1 PICKUP COW 1,
s2 PICKUP SHEEP 3, s4 PLACE COW, s24 WHEAT 3. No new feed circuit needed
((4,4) is fed daily + HARVESTed every 3 days by existing walks — verified).
Bench (8 seeds): **default seeds −$7.6k…−$16.4k; yarn seeds −$17.4k…−$58.5k.
Zero positive games.**

Root cause (traced step-by-step, seed 9):
- Engine ANIMALS table: SHEEP first_yield D6, interval 3, **max_held 6**,
  +care bonus. A cared D0 sheep yields **6 wool at D6** (1 base + 5 pending
  care bonuses), then 4 per harvest → **~34 wool/season ≈ $6.8-8.5k**.
  A D0 cow yields ~27-33 milk ≈ $4.9-6.6k. **The D0 sheep is worth ~1.3-1.5x
  the D0 cow in gross** — the "cow-heavy meta" is funded differently (below).
- The (4,4) sheep is the **D6 wool cash wave**: v1112 D6H09-D6H15 sells
  ~16-20 wool for ~$3.3-4.5k in one day (s153 SELL WOOL 6 = +$1,285 on
  seed 9). Converting (4,4) to a cow zeros that wave → D6 cash −$1,300.
- The D6 cash collapse then **breaks the D6-D8 cow wave**: D6H13 `BUY COW 4`
  buys only 3; D7H00 `BUY COW 2` fails entirely → **2 cows lost**
  ((6,3) D7 + (6,4) D8 ≈ $7-9k) + NE `BUY_LAND` fails (D6H16, $1,000).
- The same cascade is worse on the yarn suffixes (their whole midgame is
  wool-funded): seed 13 (yarn) = −$58.5k.

### 1b. v1114b1 — (3,3) D3 cow (D2H22 buy, D3H02 place, 20-slot D9-D29
feed circuit). REJECTED on architecture before full bench.
- The D3/D4/D5 walks + D9-D29 circuit were fully authored and
  geometry-verified (every step checked against sim positions; D14/D18/D19/
  D23 collateral (2,1)/(3,1) gaps all isolated = safe; no 2-consecutive-unfed
  day for (3,3) = no escape).
- **The D7 wall**: (3,3) is unfed on D6 (no unit visit; v1112 D6 walk kept
  intact for the wool wave) and must be fed on D7 or it escapes at D8.
  No hand carries wheat to (3,3) on D6/D7 (full scan: every D6/D7 hand
  visit has w=0 — hands are crop-circuit at that hour). The only source is
  the farmer's D7 walk: a 6-slot detour (W N FEED E E E) that **displaces the
  (5,2) D7 cow placement** (22 slots for 4 cow-places + 1 (3,3) feed; the
  4th cow can't fit — verified: D7EOD shed carries the 4th to D8 where no
  placement slot exists → dead shed cow ≈ $2.5-3k + $400 cost).
- Net: (3,3) cow ≈ +$1.6-2.8k (milk from D11) − (5,2) cow ≈ −$2.5-3k −
  $400 purchase − (3,3) melon loss (v1112 plants a melon there D6H04,
  ~$200) ≈ **break-even to negative**, for 20 cascade-risky hand edits.
  Not shippable.
- Full build kept at `topbots/v1114b1_cowroute.py` (builder:
  `_ref/build_v1114_full.py`) — usable as the D9-D29 (3,3)-circuit reference
  if a future build reuses the tile.

### 1c. 14a/14d (2c/2s D0, prior session). REJECTED (confirmed).
-44k…−91k on yarn suffixes (Sahil ghost +17.4k → −73.3k). The 1c/3s result
(1a) is the 1-sheep boundary: still −$7.6k…−58.5k. **Any D0 sheep cut is
dead.**

## 2. THE WOOL-ENGINE LAW (new, hard evidence — read before any cow-first
attempt next session)

1. **The 4 D0 sheep are the D6 cash engine.** Their D6 wool wave
   (~$3.3-4.5k in one day) funds the D6H13/D7H00 cow buys (COW 4 + COW 2 =
   $2,400) + the D6H16 NE `BUY_LAND` ($1,000). Cut any D0 sheep and the
   D6-D8 cow wave starves: each lost D6-D8 cow ≈ $3.5-4.5k (placed D7/D8,
   yields D15/D16+).
2. **Sheep > cow in gross per animal** (34 wool ≈ $7-8.5k vs ~30 milk ≈
   $5-6.6k, D0 placement). The cow-heavy meta (CD 16c, 2800-2900) does NOT
   run this economy: CD is all-in animals from D0 ("D5 cash = $30", minimal
   crops, 12 hands for 16 cows). It replaces the wool engine with brute
   animal scale — a different game, not an edit of ours.
3. **The D0-D5 prefix is load-bearing for all 5 suffixes** (14a/14d finding,
   now quantified for the 1-sheep case too). The tape's local optimum under
   this architecture is 11c/4s = what we ship.
4. Late-cow zero-sum swaps also dead: removing the D8 `COW 1` buy frees
   $400 but loses the D9 (3,1) cow (~$3k) — the D7EOD shed carryover is what
   places the D8 pair; every late-cow removal ≥ the D3 cow it would fund.

## 3. The only viable cow-first path (scoped for the next build)

CD-style **all-in rebuild** (SESSION 86 §10, now with the funding law):
- D0: all-in animals (3c/1s or 4c) + minimal crops — accepts the wool loss,
  funds cows from D1-D3 instead of D6 wool.
- D1-D3: animal buys (COW 2 at D2 needs the D0-D1 headroom: 3c/1s D0 leaves
  ~$445 at D0H00 vs $291 for 4-sheep — verified) → 12-14 animals by D4.
- **Feed scale-up is the hard part**: 12-14 animals need ~12 hand-fed FEED
  slots/day (CD's model). Our D5-D29 hand circuits are 6 hands / 4-5 FEEDs.
  This is a hand-choreography rebuild, not a tape edit.
- Gate: 8-seed solo (per-animal feed ≥28/30, 0 escapes) + 80-game matrix vs
  v11.12 (must beat, not match) + 6 cow-heavy ghosts (must flip ≥4).
- Risk: high (multi-day build; the 14a/14d cascade shows how fast this
  architecture fights back). Do NOT ship anything from this line until it
  beats v11.12 on the matrix — the pair is at ATH; churn is the enemy.

## 4. What NOT to do next session

- Do not re-attempt any D0 sheep cut (1a/1c: −$7.6k…−91k, quantified).
- Do not re-attempt the (3,3) D3 cow without a D7 feed source (1b: the D7
  wall is structural — no hand carries wheat there).
- Do not post to the ladder today/tomorrow-morning on a "marginal" patch:
  v11.12 is holding the ATH (2246.8) and v11.13 is climbing; a post retires
  one of the pair (last-2 rule) and drops the floor.
- Do not spend submission slots on A/B variants: 5/day, and the local engine
  is bit-exact (it caught every failure above without costing a slot).

## 5. Artifacts

- `topbots/v1114e1_cowroute.py` + `_ref/build_v1114e.py` — 1c/3s D0 (rejected,
  kept for the D6-cascade reference trace).
- `topbots/v1114b1_cowroute.py` + `_ref/build_v1114_full.py` — (3,3) D3 cow
  with the full D9-D29 circuit (rejected on the D7 wall; the circuit authoring
  is reusable).
- `_ref/verify_v1114.py` — the per-animal per-day feed/escape auditor
  (run: `python3 verify_v1114.py <variant>` — 8 seeds, cash delta vs v1112,
  escapes, feed coverage, cu_max).
- `_ref/dump_tape.py` / sim trace scripts — tape-walk + position + inventory
  tracing (the tool that caught the D6 wool wave and every geometry bug).

## 6. Bottom line for the user

The previous agent's "next ship" (v11.14 cow-first) is **not shippable in any
tractable form** — every variant that adds a cow either displaces an equal
cow (break-even at best) or breaks the D6 wool cash engine (−$8k to −58k/game
bench evidence). The live pair (v11.12 2246.8 + v11.13 1739.5) is at the
team's all-time high (#199). Correct play: **hold, let v11.13 converge
(~24h to its ~1900-2100 band), and run the CD-style all-in rebuild as a
dedicated multi-day build** — benched against v11.12 on the 80-game matrix
before it ever touches a submission slot.
