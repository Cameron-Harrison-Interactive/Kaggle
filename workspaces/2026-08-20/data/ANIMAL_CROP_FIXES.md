# Why we were losing animals & missing crops — and the fixes (2026-08-14)

## Question 1: "We keep losing animals — why?"

**Found it. Every single game loses the (7,4) cow on day 22.** Traced
hour-by-hour in the v20 tape vs PASS:

```
d8h12  worker builds a PASTURE at (7,4)
d8h13  places a COW there
d9-19  a tender FEEDs + CAREs it daily (milk harvested d16/d18/d20)
d20    the late-wheat wave RE-ROUTES the tender away from (7,4)
d20+21 cow unfed 2 consecutive days  ->  ESCAPES end of d21
```

It happens vs PASS too — it is NOT the opponent, NOT the second tape. The
cow cost $400, made ~3 harvests, then died. Every game, both seats.

### FIX (v22 "NoEscapes"): surgical, no recompile — DONE & GATED
1. Remove the d8h12 BUILD_PASTURE on (7,4). The d8h13 PLACE then fails and
   the cow rides to the end-of-day shed drop.
2. The tape's OWN d21 construction wave builds two new pastures at (7,3)
   and (3,0) and FEEDS both — it picks the shed cow up and re-homes it FED.
3. Skip the d18h1 COW buy ($400 stays in the bank, no cow strands in the
   shed).

**Measured (PASS, seed 1, both seats):**
| | escapes | seat0 | seat1 |
|---|---|---|---|
| v20 (live) | **1 every game** | $170,031 | $162,093 |
| **v22 nocow** | **0** | **$177,930** (+7,899) | **$167,288** (+5,195) |

Contested (seeds 1-2, both seats, 4 games each): vs v20/tetsu within the
mirror coin-flip noise band; **vs rayk +20,952 (ctrl +14,388) = +6,564**;
vs kaito +16,455 (ctrl +17,538, inside noise). SHIP.

`submit/HI_AgriBot_v22_NoEscapes.tar.gz` is packaged and smoke-tested
($147,853 vs starter, up from v20's $136,485). READY TO POST.

## Question 2: "Missing a bunch of crops — is it the second tape?"

No. **v20 has no second tape** — since v20 the seat0 tape plays both seats
(that was the s0s1 fix). The missing crops have two concrete causes:

1. **Failed seed buys under cash pressure (the real cascade).**
   Even in the pristine reference, 24 PLANT orders fail because the seed
   batch hasn't arrived yet (the tape plants waves with just-in-time
   seeds — the reference reward already bakes this in). In LIVE games the
   opponent (same lineage) sells into the same market windows, our sells
   earn less, and MORE BUY_SEED orders fail for lack of cash — e.g. the
   d6h18 BUY_SEED STRAWBERRY 2 fails at $170 < $200, which delays the
   whole d7 strawberry wave = the visible missing row mid-game.

2. **The SE quadrant is LOCKED on purpose** (the meta study says never buy
   SE; 3-quadrant farms are the proven optimum). If the replay shows SE
   empty, that's by design, not a bug.

### FIX (testing now): CashRank runtime layer
When the tape's buy orders would fail for lack of cash this turn, move our
SELLs to the front of the market queue — the engine resolves our queue in
order, so the sells fund the buys in the same step. Zero movement, zero
desync; it only fires when cash is actually short (preserves the reference
otherwise). Battery running: ctrl / labor / cashrank / labor+cashrank.

## Question 3: "We are still losing"

Two things going on:
1. **The escapes + seed failures cost real coins every game** — v22 fixes
   the escape outright (+$7.9k seat0) and cashrank attacks the cascade.
2. **The ladder got stronger**: the top-50 all run our economy family
   (kaito's wheat-flood meta = our tape's economy; tetsu plays our seat0
   tape verbatim). Mirror games are coin flips, so rating gains need
   (a) a raw economy edge — v22's +$7.9k is exactly that — and (b) volume.
   The remaining known edges: melon4 compiler search (rayk +$3.4k, needs
   your machine) and the three-fer full run.

## Files
- `agent/main_v22_noescapes.py` + `submit/HI_AgriBot_v22_NoEscapes.tar.gz`
- `scripts/nocow_fix.py` (the fix + gate; feed74 compile variant REJECTED:
  -$4.9k PASS, escape remained — the tender injection conflicts with the
  saturated route)
- `scripts/brain_v21.py` gains the `cashrank` layer (battery running)
- `data/nocow/ledger.jsonl` + `report.json`
