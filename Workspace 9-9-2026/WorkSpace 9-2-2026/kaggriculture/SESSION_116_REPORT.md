# SESSION 116 — PASS-Mining Falsified; The Remaining Path Is Named

**Time:** 2026-09-07 ~07:00 UTC · User thesis: "We should beat everyone under 2800 —
some of them run the same bots as the top-5 band."

---

## The thesis, validated with the top band's own games

Pulled the 6 highest-scoring episodes from the 09-06 dataset (avg 3014-3018 = the
2990-3017 class): **HowardLeeTW vs 沒有道歉 沒有道歉** ("no apology" — sibling team of #1
"我都先道歉"/"I apologize first"; the top band is one camp running variants — exactly the
twin dynamic you called).

**The 3000-class recipe (ELITE_DECODE_0907.md):**
- Crops: strb 20-40 + wheat 6-21 + **tomato 2-18** + **melon 0-2** (we: 0 tomato, 12 melon)
- Herd: **adaptive per game** (17S+5C / 12C+5S / 11C+4S / 10S+11C) — we: fixed 9C/8S
- Selling: **dribble** (36-58 wheat sells, 25-65 milk sells/game) — we: batches
- Mutual games: both sides $115-128k via complementary portfolios; our mirrors: both crash

## Hour-one live (the A/B running)

21W-3L combined. v4b took both real losses (July's 11-cow build $89.8k; 我的AI是豆包's
fork $104k); v16's only loss was a crash coin-flip. Ratings ground through the
twin-heavy 1400-1600 band: v4b 1578 / v16 1445 and climbing. 48h commitment holding.

## PASS-mining: falsified by measurement

The engine mechanics are now fully mapped (engine source): every plant must be watered
within every 2-day window or it becomes a WEED; tomato is ongoing i1 (+1u/day after d8,
$50 seed); mined crops need plant→water→harvest→drop-at-shed→sell, all hand ops.
Then the measurement that kills it: **hands PASS only on occupied tiles — zero
bare-tile PASSes across the entire game** (bare tiles: 6-28/day d7-25, but no idle unit
ever stands on one). The tape's spare turns are spatially unreachable for new planting.

## The chassis map is now complete — every door tested

| Chassis | Result |
|---|---|
| tetsu compiled blob | market-additive only; v16 = the one working fix (live now) |
| hamburger trace: crop swaps | falsified ×2 (lifecycle class; ripening-timing desync: −43% strb volume) |
| hamburger trace: PASS-mining | falsified (0 bare-tile PASSes) |
| elite tapes (keiz) | falsified (56% fidelity; herd starves — adaptive cash/feeding) |
| goose from-scratch | falsified ×3 (labor planner) |

## The remaining path — named and specified

**The trace-derived labor planner.** Hamburger's 720-step trace IS a readable spec of a
$150k labor plan: when to build/hire/plant, watering rosters, harvest cadence, hand
routes. Deconvolve it into a parameterized plan (crop→schedule tables), then regenerate
the same plan for the ELITE portfolio: tomato instead of melon, tuned herd, our dribble
sell layer. That is "our main winner, fixed" at the level that beats the sub-2800 band —
and every piece of it (engine laws, target portfolio, sell layer) is now measured.

Next session: extract the plan structure from the trace (per-position op timelines),
build the generator, gate solo → tapes → live.

## Live refs
- 56069471 v4b control (1578) · 56069472 v16 treatment (1445) — both climbing, 48h hold
- 3 slots remaining today
