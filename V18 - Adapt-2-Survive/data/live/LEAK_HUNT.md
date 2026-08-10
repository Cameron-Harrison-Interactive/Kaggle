# Leak Hunt — v16.1 losses + experiments (2026-08-10)

## v16.1 ladder record (sub 55391953)
**15 wins / 3 losses** (one incomplete excluded from W/L if needed)

| Ep | Us | Opp | Margin | Opp name | Archetype |
|----|-----|------|--------|----------|-----------|
| 91490622 | 102264 | 113666 | **-11402** | COLD | Build-A melon12, zero weeds, endgame dump |
| 91486929 | 70517 | 76610 | **-6093** | Jonathan Roy | **Carrot engine** + dense crops + more hires |
| 91491642 | 118456 | 123409 | **-4953** | Patrick Joël | Build-A melon12 (same family as COLD) |

v16.5 (55392793) on board @ ~1249 — still early.

---

## Loss anatomy

### 1) Jonathan Roy (−6k) — carrots ARE real
- Open: cow3/sheep2, **carrot 5**, melon 4, wheat 3
- **84 carrots sold** all season @ $29–40 (plant→harvest→sell→rebuy loop)
- 64 crops d11 vs our 57; 313 hires vs 266
- We had **animal deaths** (5→4 early, finished 9 animals vs normal 13)
- More PASS than us (1912 vs 844) but still won on **sell mix + midgame cash**
- Race flip: d10 we +$4.5k → d11 they jump to $5885 → d15 we −$8k forever

### 2) COLD (−11k) and 3) Patrick (−5k) — Build-A endgame, NOT carrots
- Open: cow2/sheep2, melon 12, wheat 7 (classic Build-A)
- Zero/near-zero weeds all game; 14 animals; 60 crops held
- Melon 144 vs our 102; straw 313 vs 284
- **We were ahead at d20–d25**, lost d27–d29 on their cash-out volume
- Same pattern both losses: midgame win → endgame loss to cleaner Build-A

---

## Experiments vs our bot (14.5 keep-gate)

### A) FEED on PASS when unfed + wheat in hand
- Local: **0** opportunities (never holding wheat while PASS on unfed animal)
- Score: **d=0** (no-op)
- Verdict: need **pickup wheat** path or tape feed fix, not PASS→FEED alone

### B) Carrot via opening (cut melon / cut feed-wheat)
| Variant | Result |
|---------|--------|
| MELON 5→4 + CARROT 4 open | **47k vs 143k (−56k)** disaster |
| MELON 3 + CARROT 5 | **57k (−46k)** disaster |
| Drop BUY_PRODUCT WHEAT + CARROT 5 | **13k (−90k)** animals starve |

Cutting the open for carrots **destroys** the bot. Melon open is load-bearing.

### C) Soft carrot after first cash (buy d2–d5 when money≥$200–350)
| Config | Wins vs 14.5 | Mean Δ vs v15 | Notes |
|--------|--------------|---------------|-------|
| buy d2 q3 $200, max 3 plants | 4/5 | **+1629** | s1 **+11.7k**, s3 **−4.3k**, s5 LOSS |
| buy d3 q2 $250, max 3 | 4/5 | +1681 | same pattern |
| buy d4 q2 $300, max 2 | 4/5 | +1681 | same |
| buy d5 q3 $400 | 5/5 | −1592 | s3/s5 big red |

**Verdict: PROMISING but FAIL keep-gate.** Seed1 loves carrots (+$12k); seed3 hates them (−$4k). Not shippable until seed-stable (likely needs **offline tape slots**, not runtime PASS plant).

### D) Endgame sell reorder (premium before wheat d25+)
- Mean **−18** vs v15, still 3/3 wins on quick test
- Too small / slightly negative — not the COLD leak (they out-produce, not just out-order)

---

## Leak ranking (what actually costs ladder games)

| # | Leak | Est. impact | Fix type |
|---|------|-------------|----------|
| 1 | **Build-A endgame** (more melon/straw, 0 weeds, 14 anim) | −5k to −11k | Offline tape: more melon wave / cleaner SW water — NOT runtime path |
| 2 | **Jonathan carrot midgame cash** | −6k | Soft carrot runtime is seed-unstable; compile 2–3 carrot slots into tape d0–d8 |
| 3 | **Animal deaths under contest** (loss1 finished 9 anim) | large when it hits | Tape feed reliability / don't PASS when unfed if wheat available in shed (needs PICKUP) |
| 4 | Straw crash dumps (earlier audit) | −40k in bad metas | Family-gated hold — still fails mirror keep-gate |
| 5 | Corner weeds d24 | small | Coverage limit; DIG on PASS already helps |

---

## What we will NOT do (reconfirmed)
- Cut melon open for carrots
- Runtime path rewrites / plant-on-empty fill-all
- SE unlock / SW animal mirror

## What to try next (priority)
1. **Offline route_compiler**: add 2–3 NW carrot tiles to seat tapes (plant d0, harvest d3–8, stop) without reducing melon 5 — fund by shaving 1 wheat seed or accepting $80 open cost only if money curve allows in compiler sim
2. **Build-A endgame**: second melon wave already on tape — audit why COLD gets 144 melon sold vs our 102 (harvest/water timing on melon tiles)
3. **v16.5 watch**: same backbone; expect same 2 matchup types until tape changes

## Ship
Still **HI_AgriBot_v16.5_StrictAdaptive** (keep-gate ≡ v15). No carrot/endgame patch merged.
