# SESSION 109 — CD's Goose Recipe + Mirror-Fix Diagnosis (no submissions)

**Time:** 2026-09-06 ~08:30 UTC · User directives: CD wins with geese → build it; "we know
their moves, why aren't we fixing them?"

---

## Crop Dusta's actual recipe (verified from profile + live replays)

CD (#4 live, 2869.8) plays a **goose-heavy, wheat-trading, morning-batch build**:

| Lever | CD's values | Our v4b class |
|---|---|---|
| herd | **7 goose / 3 cow / 1 sheep** (ramp d7-14) | 9 cow / 8 sheep, no geese |
| EGG | **208u sold** (log-curve safe volume product) | 0 (no geese) |
| wheat | **buys 2,028 → sells 2,382** (market-making) | 303u sold, no trading |
| sells | **morning batch H02** (pre-dump) + H06/H09 | h3/h7/h19/h22 (crowded windows) |
| carrot | 79u sold (the uncontested niche) | 2-9u |

The user's instinct is right: geese/egg + wheat trading + H02 + carrot = the differentiation
levers that beat the mirror crowd.

## Why we keep losing to same-metas forks (the diagnosis)

1. **The frozen tetsu policy can't be perturbed**: v12 (−$4.3k), v13 (0-10), v14 (−$50k on
   8 tapes) — every market-overlay on the compiled class collapses its coupled economy.
2. **Seed sensitivity is NOT the cause**: v4b on live-range seeds (662M-1.7B) scores
   $109-174k solo, robust. The failures are opponent-driven portfolio crashes.
3. **The coin-flip mechanics**: mirror-fork collisions crash both sides to $43-77k; margins
   decided by micro-deltas (wool 196u vs 107u; melon sold $169 early vs $19 late — JOSHNA
   fork beat the route 106047657 by $20.8k exactly this way).

## What was built & falsified tonight (kept for the record)

- **goosebot v8 "differentiator"** (sheep fix + night band + carrot 16 + adaptive
  strb-cap): solo $95-107k (+$30k) but H2H 0-4 vs v7e/v4b/route — chassis loses mutual.
- **goosebot v9 "CD-faithful"** (7G/3C/2S + coop infra + wheat dip-buy + H02): solo
  $58-77k, wheat trading works ($88-95k wheat revenue!) but **no coops built in time**,
  geese never arrived; H2H 0-4.
- **goosebot v10 "tetsu opening"** (v9 + d0 all-in HIRE5/COW2/SHEEP2/MELON12/WHEAT7 + feed
  stock 22): d10 money **$268 vs tetsu class $16.2k** — the from-scratch labor planner
  can't match the compiled choreography. **From-scratch goose line closed 3x tonight.**
- **route2900 melon-early overlay**: +$0 on all 9 tapes (never fires; blob's melons leave
  shed at h12-17, not h1-3; melon timing is a labor-level blob issue).

## The CD-archetype chassis we already own

**Hamburger (public notebook)** = CD's archetype available ready-made:
- solo **$150,074** (seed 10061), wheat trading **buys 967 → sells 1,042**
- MILK $45.6k @ premium, WHEA $45.2k, STRA $39.7k, FERT $15.9k, MELO $13.4k, WOOL $7.1k
- herd 8C+5S, crops 40 STRB + 9 MELON + 3 WHEAT (strb-heavy)
- BUT locally 0-10 vs v4b (−$32k/game) and 0-10 vs route (−$21k/game)
- NOTE: local H2H ≠ live ratings (law): the route is 0-10 vs v4b locally yet its class
  rated 3044 live. Hamburger's live class = CD-adjacent = our next slot candidate.

Also: **v16-rc5 premium = the same notebook as the 2900 route** already live (identical
census: 24W/33S/4M, 8C+4S, milk $29.2k @ $243, wheat 594u, wool $19.3k).

## Live status (final for this session)

- **v4b-fixed (56047687): 1957.6 and climbing** toward its 2526.5 class
- **2900-verbatim (56048083): 1233.2**, recent live form 3W-3L (incl. tie $109.5k vs a
  route twin, loss $20.8k to JOSHNA-class fork — the fork beat the route via wool
  volume+timing edge). Extracted the JOSHNA tape → analysis/loss_tapes/106047657.json
- Both actives in good health; no submissions made (user's directive).

## Next-session priorities

1. Decide tomorrow's slot with convergence data: v4b-fixed's final vs 2900-verbatim's
   ceiling (its twins + fork losses suggest it may converge lower ~2000-2400).
2. If swapping: **hamburger (CD archetype, $150k solo, entrypoint `agent` = last ✓)** is
   the ready next candidate.
3. Deeper tuning candidates (market-layer-only, on hamburger this time — its source is
   readable, unlike tetsu): the wheat dip-buy timing + egg sell band + carrot scale.
4. The 'JOSHNA fork' tape is persisted as a strong-fork benchmark for future gates.
