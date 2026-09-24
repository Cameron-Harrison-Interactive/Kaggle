# Coverage Analysis — tong00 / Roman losses (2026-08-10)

## Records
- **v16.1** (55391953): **20W–4L** — new loss tong00 −11k (ep 91495290)
- **v16.5** (55392793): **11W–1L** — first loss Roman Tamrazov −11k (ep 91496106)

## Your read is correct

| Observation | Live data |
|-------------|-----------|
| NW great until ~d14 then wheat dies | (0,0)(1,0) NW wheat → WEED d13 after CU miss |
| NE/SW should mimic NW | They don't — tape never recompiled for 3-quad water density |
| Opp has near-perfect coverage | tong00/Roman hold **100%** plants, **0 weeds** through d20 |
| We tank coverage | Us **87%** d15, **5–8 weeds**, SW corners dry |
| Strict pattern needed | Opp alternates **55–59 WATER days** vs our **23–36** |

### vs Roman (v16.5) water/day
| Day | Us WATER | Roman WATER | Us cov | Roman cov |
|-----|----------|-------------|--------|-----------|
| 11 | 36 | **55** | 100% | 95% |
| 12 | 42 | 20 | — | — |
| 13 | **23** | **50** | weeds start | 100% |
| 15 | 29 | **59** | **87%** | **100%** |

We **MOVE off unwatered plants 46–56 times/day**. Roman: 0 PASS on dry crops.

## Why runtime "just water more" fails

| Patch | Keep-gate |
|-------|-----------|
| MOVE→WATER any dry plant | **−30k to −85k** (route desync) |
| PASS→WATER any dry + MOVE on critical | **−35k**, water counts *fall* (desync skips later tape WATER) |
| PASS→WATER only | still **−33k** |

**Mechanism:** staying one extra turn to water shifts the worker off the 719-step tape. Later scripted WATER/PLANT hit wrong tiles → net coverage worse.

v15 `_water_optimizer` (empty/dupe→PASS; PASS/MOVE→WATER only on CU==1 if safe) is already Chat-Log-5 optimum for *overlays*. It cannot create Roman's visit schedule.

## What "strict pattern" actually means

Roman/tong00 don't magic-water — their **route visits every crop on a cadence** (heavy water days 50–59 alternating with light 14–20). After 3-quad unlock our tape still uses a path built for thinner boards. NE/SW never got NW's revisit density.

**NE/SW cannot mimic NW at runtime without rewriting the route.** That requires **offline tape recompile**, not adaptive overlays.

## Adaptive crop swaps
Right differentiator *after* coverage. Swapping straw→tomato at 87% coverage does not beat 100% coverage Build-A. Fix visit pattern first (compile), then adaptive.

## Ship decision
- Reverted experimental coverage water → **v16.5 ≡ v15 water** (keep-gate 103017)
- No 16.7 ship
- Next real work: **route_compiler** alternating-day water for NE+SW (mirror NW)

## Action order
1. Offline recompile water routes for 3-quad full coverage
2. Keep ladder on v16.5 until new tape passes keep-gate
3. Then adaptive crop swaps on top of solid coverage
