# SESSION 104 — TOURNAMENT OF CHAMPIONS & THE HYBRID QUEST (Session 42, day 3)

*"Try variations of what we have used and find the absolute best winner of them all
and make one hybrid; keep the v11 and the goose bot."*

---

## 1. THE VERDICT

**v11 (tetsu_r5_v11_adapeak2) is the absolute winner — unbeaten 50-0 in local H2H
across every challenger we have ever built or recovered.** The submission gate
(beat v11 local H2H) remains **unpassed**. No new submission is justified; v11
stays the live champion. Goose lineage (W4) and the hybrid (v20) both stay
alive in `topbots/` per standing orders.

## 2. FINAL BATTLE TABLE (H2H, seeds 10007-11 × both seats, 10 games)

| ↓ vs → | v11 | v18.8 | v19 | v15 | v20 | W4 |
|---|---|---|---|---|---|---|
| **v11**   | — | **10-0** | **10-0** | **10-0** | **10-0** | **10-0** |
| **v18.8** | 0-10 | — | 6-4 | — | 9-1 | 10-0 |
| **v19**   | 0-10 | 4-6 | — | — | 9-1 | 10-0 |
| **v15**   | 0-10 | — | — | — | 9-1 | 10-0 |
| **v20**   | 0-10 | 1-9 | 1-9 | 1-9 | — | 10-0 |
| **W4**    | 0-10 | 0-10 | 0-10 | 0-10 | 0-10 | — |

H2H average scores: v11 $94-172k (near its $146k solo even under attack);
tapes $90-130k; v20 ~$65k vs v11 / $80k vs tapes / $118k vs goose; W4 $30-34k
(vs everything — v11's flooding destroys the goose's premium-selling model).

**Hierarchy (fully transitive): v11 ≫ v18.8 ≥ v19 > v15 > v20 > W4 > v7e.**

## 3. SOLO LADDER — W-VARIATION MATRIX (seeds 10007-16 ×2, goose chassis)

| bot | change | MEAN | verdict |
|---|---|---|---|
| v7e | baseline | $83,116 | — |
| **v7v_W4_SE_quad** | **SE quad (d≤22, $>4200)** | **$92,025** | ★ **goose champion (+$8.9k)** |
| v7v_W8 (W4+melon d9-12) | blueprint melon wave 2 | $90,946 | min $33k — unstable |
| v7v_W9 (W4+wheat40) | wheat engine 40 | $85,534 | worse than W4 |
| v7v_W1a (wheat56) | wheat engine 56 | $84,625 | mild alone, negative with SE |
| v7v_W6 (W4+wheat56) | combo | $84,349 | wheat steals quad cash |
| hybrid_v22 (W4+4 cows d0-4+feed) | early milk engine | $88,288 | board can't carry early herd |
| hybrid_v21 (W4+full v11 opening) | full blueprint port | $83,250 | strb 17 vs 29; weeds ×4 |
| v7v_W5 (geese 8) | geese + coop | $80,636 | unstable (min $36k) |
| v7v_W2 (strb fert 150) | single-lever fert | $79,585 | FERT-PIPELINE law again |
| v7v_W7 (W4+hire ramp 14) | blueprint hires | $76,594 | cash starvation (see §5) |
| v7v_W1b (wheat56+strb20) | strb cap cut | $53,847 | poison — strb needs 33 |

Tape/hydra chassis (solo): v18.8 $147,826 mean (seed 10011: $167,913);
**v20/v20b/v20c identical $167,913 on 10011** (head is provably inert vs passive).

## 4. THE MARKET, FULLY DECODED (engine/kaggriculture.py — this is the session's gold)

- **MARKET_I0 = 10,000 units** — the price pivot, shared by BOTH players (one
  inventory per product). Below I0: shortage premium; above: crash.
- **Price curves per product** (base / above-func / crash speed):
  WHEAT 25 log slow; CARROT 35 sqrt; TOMATO 60 sqrt; **STRB 120 LINEAR ~$2/unit**;
  **MELON 250 QUADRATIC (0.01/unit²: +50 units ≈ −$25, +100 ≈ −$100)**;
  EGG 50 log slow; **MILK 160 LINEAR ~$2.1/unit**; **WOOL 200 QUADRATIC (0.058/unit²)**;
  FERT 100 linear slow (0.2/unit).
- **Lockstep execution**: both players' same-item sells commit unit-by-unit at
  IDENTICAL per-iteration prices (quoted pre-commit, interleaved). You cannot
  out-order a simultaneous dumper — you can only sell into lines/times the
  opponent isn't flooding.
- **Sales at $1 add no supply** (floor dumping is free); BUY_PRODUCT quotes at
  post-buy inventory so buy/sell round-trips net zero (no arb vs yourself).
- **Town demand**: shops unlock every 3 days (with replacement, MAX_SHOP_INSTANCES),
  each instance drains 12 units/day of its product (6 if paired); town center 1/day.
  Late-game drains ≈ EGG18/WHEAT37/MILK12 per day → the whole game competes for a
  shared demand budget of a few hundred units per product.
- **H2H law**: whoever sells a line FIRST captures its premium; the follower's
  scheduled dumps land at the floor. v11 liquidates its entire shed EVERY HOUR
  (the 2M-order pattern) — pure first-mover. Tape schedules arrive late → $3-18
  strb/milk. Wool/wheat/egg stay in shortage premium all game (both bots net
  sellers of strb/milk/melon/fert, so those crash).
- **HANDS ARE FIRED NIGHTLY** (`farm["hands"] = []` in `_end_of_day`) — every bot
  rehires daily; hire cost = $1×fib(nth hire today): 12 hires ≈ $376/day, 14 ≈ $986/day.
- v11 endgame: shed empty by step 718, 9 sells posted — **v11 already terminal-sweeps
  perfectly** (wrapper add-on worth ~$3; option (a) is dead).

## 5. v11's OPENING, DECODED FROM INSTRUMENTED SOLO (seed 10011, $145,887)

| day | money | build |
|---|---|---|
| 0 | $27 EOD | HIRE 5, COW 2 + SHEEP 2, WHEAT 7 seeds, MELON 12, BUY wheat 22 feed |
| 2-4 | $93-160 | +1 cow, strb seeds 4, carrot 3, wheat top-ups 5 |
| 6 | $615 | **NE quad**, 8 hires, cows 6, strb 12 tiles |
| 8 | $726 | cows 9 ✓, sheep 4, strb 20, 10 hires, **buying 21 feed-wheat** |
| 10 | $16,209 | sheep 8 ✓ (17 herd), 11-12 hires, wheat→12, **buying 40 feed** |
| 12 | $20,799 | **SW quad (3 total)**, strb 33 ✓, wheat 24 |
| 16-28 | $42k→$138k | wheat 25→41, 12 hands steady, continuous selling |

**Why v11 wins H2H (all three, inseparable):**
1. **Early economy**: 9 cows by d8 = ~$720/day milk from d6 — revenue DURING
   setup funds strb-33 + 3 quads by d12. W4 has a 12-day revenue drought
   ($594 at d8); v21's herd-first port starved strb (17 vs 29) and quadrupled
   weeds — the goose job board saturates at ~4-5 hands' worth of animal labor.
2. **First-mover selling** (§4).
3. **Route quality**: W4 and v11 have the SAME late-game rate (+$67k over d20-28);
   the whole $53k gap is days 0-20. Roman Rozen's law confirmed again: path to
   the top = route architecture, not job-board tuning.

## 6. THE HYBRID QUEST — WHAT WAS BUILT AND WHAT IT PROVED

- **hydra v20** (`topbots/hydra_v20.py`): v18.8 tape body + race-liquidation
  market head (sells-only, d12+, buys/labor untouched) + terminal sweep.
  Solo EXACTLY $167,913 (head inert vs passive ✓). H2H vs v11: 0-10 but +$20k
  over bare v18.8 ($65k vs $45k avg). **Best tape-lineage bot we have.**
- **v20b** (liquidation from d4, wheat keep 16): solo intact, H2H net WORSE —
  early cash breaks the tape's buy-skip choreography (v13.1 law applies any day).
- **v20c** (adapeak window d4-11, ≥90% base only): bit-identical to v20 — the
  tape has ~no shed stock before d12; **zero early production is structural**.
- **v21/v22** (v11 opening on goose): §3 — chassis can't carry it.
- **v11 + terminal sweep wrapper**: dead — v11 already sweeps (§4).

**The hybrid conclusion**: v11's H2H moat = early-economy route + first-mover
selling + compiled route quality. None of the three can be grafted: the tape's
labor is frozen (desync law), the goose's board saturates, and v11 is compiled.
The ONE hybrid that beats v11 must be a NEW compiled-route bot with v11's
opening and better market timing — i.e., a route compiler on our decoded data
(v26 lineage / Roman Rozen architecture). That is the next frontier, not a patch.

## 7. STANDING STATE

- Live submission: **v11** (2456.0, ~#547 of 7,720). Fresh slots: 5, unused. Gate unpassed.
- Keep-alive: `topbots/tetsu_r5_v11_adapeak2.py` (champion, DO NOT MODIFY),
  `topbots/v7v_W4_SE_quad.py` (goose champion $92,025), `topbots/hydra_v20.py`
  (tape champion), `topbots/history/` (recovered eras), `topbots/v7v_*` (matrix).
- One meta-caveat worth a decision later: the local gate (beat v11) is stricter
  than the live LB (Bradley-Terry vs a mostly-public-bot pool). v18 hit 2739 live
  in August while losing to v11 locally. If we ever want to hunt rating rather
  than certainty, a pool-simulation gate (vs tape-like public bots) is the
  refined test — but per standing rule, v11's gate governs submissions.

## 8. FILES

- New: `topbots/hydra_v20.py`, `hydra_v20b.py`, `hydra_v20c.py`,
  `topbots/hybrid_v21.py`, `hybrid_v22.py`, `topbots/v7v_W{4,6,7,8,9}_*.py`
  (W6/7/8/9 built this session; W1a/1b/2/5 prior), `scripts/build_hydra_v20.py`,
  `scripts/build_hybrid_v21.py`.
- Untouched: v6/v7/v11 sources, all CHAMPION_* masters, engine/.
- Seeds burned this session: none fresh (ladders reuse 10007-16; H2H 10007-11).
