# SESSION 113 — "Just Fix It" — I Did. Here's What the Fix Revealed.

**Time:** 2026-09-06 ~21:40 UTC · User: "If you know what they're doing, why aren't you
just fixing it instead of changing the whole damn thing?"

---

## What I did tonight (the surgical fix, built and gated)

**v16 = v4b + premium-window liquidation** — the elite sell-hour fix with the CORRECT
mechanism this time (v14's "night premium" turned out to be a bug: it only *removed* sells
and held to shed-cap; it never sold at the premium at all). v16 only ADDS sells at better
hours, never holds/removes/buys.

**Gate results (same-context A/B, the law respected this time):**

| Gate | Result |
|---|---|
| 9 fork tapes (v4b already wins all) | +$236 avg, 6/9 positive, 0 flips — noise |
| **v4b's 8 REAL live loss opponents** (katlun, curiosity, Lauresowe, Pavlo, 인공저능연구소, hidenov, WQAAAA, Zyy7390) | **−$19 total. A perfect wash.** |

## Why the fix is a wash — measured, not assumed

Instrumented the WQAAAA mirror-crash game. Milk price by hour across the whole game:
**h0=$71, h1=$73, h7=$68 … h23=$66 — FLAT.** The h1 "premium" does not exist in mirror
games. The milk timeline: $186 (d8) → $133 (d10) → $45 (d13) → $9 (d14) → **$1 permanent
(d15+)**. Both twins produce identical volume; supply crosses demand; the floor is
permanent. There is no window to sell into because the twin fills every window too.

**The top-10's edge is not WHEN they sell — it's WHAT they produce.** keiz (2857):
tomato+wheat. Jesse Bullard: milk+wool. Complementary portfolios → both sides keep their
premiums ($111-126k each). Mirror portfolios → both crash ($37-45k each). The elite
"sell-hour discipline" is a symptom of owning a differentiated portfolio, not a lever.

## So "just fixing it" and "changing the whole thing" are the same job

The portfolio (9C/8S herd, 33 strb, 12 melon, 24 wheat) is baked into the compiled blob's
labor plan. Six surgical mechanisms now tested on it: add-sells (v12, −$4.3k), swap-herd
(v13, 0-10), delay-sells (v14, −$50k — bugged), add-buys (v15, −$66k), melon-timing
(never fires), premium-liquidation (v16, wash — root cause measured above). **You cannot
retune the portfolio of a black box. To change what we farm, we must own the labor code.**

That's what tomorrow's build is — and it's NOT a departure from our winner: same build
recipe (the tetsu/elite chassis), same market engine, but our code: graft the proven
720-step labor route, then swap the portfolio to the differentiated elite mix
(wheat-fert loop + tomato/carrot niche) and the premium sell windows. "Our main winner,
fixed" — at the only level where the fix exists.

## Midnight (00:00 UTC, ~2.3h) — unchanged, both slots to our winners

1. **v4b** (2526-class verbatim) — tars verified, ready.
2. **v11** (exact live-2322.5 agent) — ready.
3. 48h undisturbed. 3 slots in reserve for the labor-graft when it gates.

## Live refs
- 56058935 hamburger (824, grinding, capped by twins — confirmed by tonight's mechanism)
- 56048083 2900-verbatim (1217, stalled — displaced at midnight)
- 56047687 v4b-fixed (2079, displaced today — resubmit ready)
