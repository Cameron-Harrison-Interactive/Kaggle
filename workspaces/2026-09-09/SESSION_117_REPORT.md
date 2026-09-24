# SESSION 117 — The Losses, Read. The System, Shipped.

**Time:** 2026-09-07 ~15:20 UTC · User: "Read the losses and find out why. I'm asking for a
system that allows us to beat the ladder because we need the win."

---

## PART 1 — Why we lose (193 games read: 138W-55L; v4b 69W-27L, v16 69W-28L)

**Loss mode split: 39 "outrun" + 16 "crash coin-flips".**

- **39 losses = our own fork family** (S31-38 strb / W22-24 wheat / C6-11+S5-13) out-executing
  us on the IDENTICAL portfolio. We score $78-146k (good!) — they score slightly more.
- **16 losses = mutual-destruction mirrors** — both <$70k, often decided by <$1,500
  (worst: −$46, −$53).
- **In losses our wheat collapses $41k → $27k and strb $20k → $4-6k** — the fork takes
  the premiums; we take the floors. Mirror games are a 50/50 by construction.

**The beater profiles (every one holds a premium product we don't run):**

| Cluster | Build | Beats us via |
|---|---|---|
| **C9G3S5** (Kobe, nanare, Moshel, mgoto51004, hinemos…) | 9C+**3 geese**+5S, S33/W24 | **eggs** (mild crash, daily yield from d4) |
| Sheep-weights (Subramanya N, 4eta…) | C2-4+S8-13, some **tomato** | wool $21k / tomato premiums |
| Cow-weights (Pascal, Miaohua Zhang…) | C11-16 | milk $26-30k windows |

## PART 2 — The system (found, gated, submitted)

The C9G3S5 cluster runs a **public kernel**: Thomas Tschinkel's "93.8% Win Rate Public
State Router" (30 votes). Not a fixed tape — a **market-driven router over five public
tapes** with day-6/day-24 switch points: portfolio adaptivity without owning labor code.

**Gate results:**
- Solo: **$168,031** (highest we have ever measured; hamburger $153k, v4b ~$140-164k)
- Build: 24 wheat + 33 strb + **9C/5S/3G — the exact beater profile, herd adapts by state**
- **H2H vs our live pair: 16-0.** Router beat v4b 8-0 (+$230,266) and v16 8-0 (+$231,260)
  — +$28.8k per game. The most dominant H2H we have ever measured.

**📢 SUBMITTED 56079632** (displaces v4b control 1867; keeps v16 1935 — our better agent).
**Actives now: v16 (1935, climbing) + TT router (fresh).** 2 slots left today.

## Also: the #1 published their playbook today

3Jeonghoon (#1, 2848.7) posted "From Orders to Actual Trades" — an analysis kernel with
their exact market model (`price_of(item, inventory, params)`, reference production
quantities T, a demo season with CARROT/WHEAT/TOMATO planning). Saved to
topbots/kernels07/. That's the pricing engine behind the top band — future tuning intel.

## The system going forward

1. **The router is the chassis** (proven beater class, adaptive, no labor-code ownership
   needed). Watch its convergence — if it climbs past 2200, it's our new main.
2. **v16 stays as the floor** (1935 and climbing; the sell-window fix is +70 over control).
3. Next levers, in order of measured impact: tune the router's tape selection (its five
   tapes are readable), graft our v16 premium-sell layer ONTO the router (market-layer
   only — the router's structure accepts overlays by design), and the #1's pricing model
   for sell-timing.
