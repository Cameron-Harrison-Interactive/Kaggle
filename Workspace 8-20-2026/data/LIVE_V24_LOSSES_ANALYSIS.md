# v24 Losses — Fine-Toothed Comb (2026-08-14)

Forensic pass over **ALL 83 live episodes of HI_AgriBot_v24_WheatGuard**
(submission 55505953): 83 games, **42 W / 41 L / 0 T (50.6%)**
(refreshed 2026-08-14 evening; the 2 latest games — 93075665, 93084842 —
are both wins with 0 escapes vs old-family opponents).
Avg win margin +$15,459; avg loss margin −$30,736.
All replays downloaded via the Kaggle API, fingerprinted, and deleted after analysis.

---

## 1. The two holes the user saw — quantified

### Missing animals: COW escapes on day 9-10
| | |
|---|---|
| Losses with our escapes | **28 / 41** |
| Wins with our escapes | 1 / 40 |
| Escape animals | **89 COW, 2 SHEEP** |
| Escape days | 72 on day 9, 19 on day 10 |
| Our end animals | losses 10.1 vs wins 12.9 |

Cows are bought day 7-8 (milk engine); on day 8 our shed wheat runs to ~2,
the tape's fixed `SELL WHEAT 2` empties it, ~10 animals compete for ~4 wheat
(PICKUP only works shed-adjacent — the shed IS the feed buffer), and the cows
that go **2 consecutive days unfed escape** (engine rule:
`consecutive_unfed >= 2` → escape, structure remains).

### Missing crops: 61 vs 63 plants
| | |
|---|---|
| Mean max crops | losses 61.2 vs wins 61.8 |
| Failed wheat seed buys day 7-8 | **22-30 of 41 losses**, 1 of 40 wins |
| Failed strawberry seed buys day 7-8 | 28-30 of 41 losses, 1 of 40 wins |
| Day-11 strawberry wave | losses ~53 plants, wins ~61-63 |

## 2. The exact root-cause chain (proved on episode 93065463, the user's example)

v24 vs **Debmalya** (live: LOSS 73,153 vs 140,872). The opponent's full
action sequence was extracted from the replay and replayed locally against
v24 on the same seed → **reproduced live EXACTLY (73,153 / 140,872)**.
The same game vs an idle opponent (PASS control) = **177,574**.
→ the opponent's market orders alone cost us **$104,421**.

Step-by-step:

1. **d0h0 — the one-seed clamp.** The market resolves both players' queues
   **by slot index, unit-by-unit in lockstep**; every BUY_PRODUCT unit quotes
   the post-purchase price. Debmalya's `BUY_PRODUCT WHEAT 11` (slot 0)
   inflates the wheat price our 14-unit buy pays mid-order (+~30 coins).
   Our opening queue is a knife-edge budget:
   `WHEAT 14 + HIRE×4 + COW 1 + SHEEP 4 + MELON 5 + WHEAT 5`.
   With 30 fewer coins, the tail `BUY_SEED WHEAT 5` clamps to **3**.
2. **d0h16 — the missing tile.** The tape plants 5 wheat tiles on day 0;
   with only 4 seeds (+1 bought d0h1) the 5th `PLANT WHEAT` no-ops.
   **Tile (0,0) stays empty for the whole game** → wheat field = 4 tiles
   instead of 5 → −20% wheat output forever.
3. **d8 — the feed crunch.** Wheat stock 2 vs 11 in the control. The tape's
   fixed `SELL WHEAT 2` empties the shed. 10 animals (6 cows + 4 sheep)
   against ~4 wheat → 4 cows unfed 2 days running.
4. **end of d9 — the escapes.** 4 COW escape (invisible in PASS).
5. **d10h0-h1 — the cash cascade.** The day-10 budget is a fibonacci
   **hire ladder**: hire costs within a day grow
   5,5,10,15,25,40,65,105,170,275,445,720… The tape hires 7 at d10h0
   (cost 165) and **7 more at d10h1 (cost 4,765!)** before the seed wave.
   With cash already short (wool/milk sells landed at prices depressed by
   the opponent's interleaved sells), the d10h1 queue clamps:
   4 hires → `MELON 9` clamps to 7 → `STRAWBERRY 7` clamps to **0**.
6. **d11 — the missing strawberry wave.** 53 plants vs 61 — permanent.
7. **d11+ — opponent pulls away** (lead starts day 11-16 in 34 of 41
   losses), and at d27-29 both sides flood wheat; the smaller economy
   ends $67k-$104k behind.

**One missing seed → one missing tile → missing crops AND missing animals.**

The opponents that beat us are overwhelmingly **first-mover wheat buyers**
(d0h0 BUY_PRODUCT WHEAT 4-14 — our own trick, now the whole meta:
22 of 41 beating opponents buy 11-14) or the old family (d0w 5-6),
flooding 195-267 wheat at d27-29 (one outlier: "Excluding" floods 740 —
a wheat-maximizer variant).

## 3. Engine facts that make this possible (verified in source)

- Market = **slot-indexed lockstep**: order *i* of player 0 interleaves
  unit-by-unit with order *i* of player 1; both quote the same pre-commit
  inventory each round. First-mover buys are a **price weapon**.
- `_do_hire`: **fibonacci ladder within a day** (reset at day rollover):
  5,5,10,15,25,40,65,105,170,275,445,720,1165,1885… — late-day hire batches
  are brutally expensive; the tape's 14 hires/day pattern is a budget
  knife-edge.
- **FEED pulls wheat from the worker's inventory; PICKUP only works
  shed-adjacent** → the shed is the feed buffer; selling the buffer =
  starving the herd.
- Animals escape after **2 consecutive unfed days** (structure remains).
- Weed & shop RNG is `random.Random((seed*1_000_003) ^ day)` — deterministic
  per seed+day, identical no matter what the opponent does. All opponent
  influence flows through the **market interleave** (prices + our own
  affordability), never through our RNG.

## 4. v26 = v25 + two hole fixes

Built as `HI_AgriBot_v26_FeedGuard` (agent/main_v26_feedguard.py):

- **Fix A — opening clamp immunity (tape edit, d0h0):**
  `[…, BUY_SEED MELON 5, BUY_SEED WHEAT 5]` → `[…, BUY_SEED WHEAT 6, BUY_SEED MELON 5]`
  Wheat seeds land before melon seeds, with +1 slack, so a first-mover
  opponent can no longer clamp our wheat seed purchase → the 5th wheat
  PLANT always lands → no missing tile. Cost: 10 coins (the melon tail
  absorbs it in tight games).
- **Fix B — FeedReserve guard (runtime layer, days ≤ 13):**
  If shed wheat ≤ live animal count, drop `SELL WHEAT` orders entirely.
  The ~60-120 coins forgone beats 4 escaped cows (400 each + milk chain).
  Healthy games are byte-identical (shed wheat >> animals → 0 PASS delta:
  PASS control 179,418 unchanged).

**Rejected during development (do not retry):**
- SeedFirst runtime reorder (move BUY_SEED ahead of HIRE when cash short):
  hurt badly (−$24k on the Debmalya replay). The tape's hires-before-seeds
  at d10h1 is compiler-deliberate: 4 extra hands beat the strawberry wave
  (60 plants but −$14k at d25 without the hands). One trigger point,
  verified: d10h01.

## 5. Verification status (v26) — VERDICT: REJECTED

- PASS control seed 683512016: 179,418 (v24 PASS was 177,574) — guard is
  0-delta in healthy games, W6 slack is real.
- Debmalya replay: 103,642 vs v25's 104,326 (−684).
- **Full 81-episode live regression suite** (every episode replayed
  seat-correct vs the recorded opponent): v25 40/81 wins, v26 40/81 wins,
  2 outcome flips (1 each way), **total margin delta −$109,090
  (−$1,347/game)**. The tape-level W6 slack displaces a melon seed in
  healthy games and the feed-reserve guard trims wheat sells without
  preventing escapes (esc counts identical to v25 on the suite).
  → **v26 rejected. v25 (qty-16) remains the champion.**
  Results: data/regression_v26/results.json. v26 source kept for history:
  agent/main_v26_feedguard.py.
- The replay suite also proved the methodology: recorded-opponent A/B runs
  reproduce live exactly (episode 93065463 matched live to the coin).
