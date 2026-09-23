# R54 — I was wrong about the weeds. You were right.

**Date:** 2026-09-15
**You said:** "Day 16 fresh planted strawberries die by day 21. Go watch all the episodes. You'll see." And: "we are still not pivoting — milk is 300 at the end but we did not monetize it."

Both are true. Last round I told you the weeds were harmless. **That conclusion was wrong, and it was wrong because of a bug in my own measuring tool.** Here is what actually happened.

---

## 1. My probe was broken, and it hid your bug

Two separate faults, both mine:

**(a) The age counter never reset.** My probe recorded the day a tile *first ever* held a plant and never updated it. So a strawberry sown on d16 onto a tile that had grown wheat back in week 1 was scored as **"age 21"** instead of **"age 5"**. The exact failure you watched was being filed under a harmless-looking old age.

**(b) I used the wrong safety metric.** I reported "ripe deaths = 0" and concluded nothing was lost. But that only catches crops that die **after** setting fruit. A strawberry's first yield is at age 10 — so one dying at age 5 has produced *nothing*, dies holding zero units, and is completely invisible to a "was it carrying ripe fruit?" check. My all-clear was not evidence of anything.

**The fix to the tool:** reset the clock whenever a tile stops holding a plant, and use a hard bound that needs no observation — *a plant that dies before its first-yield day cannot possibly have produced anything*. First yields: wheat/carrot 2, tomato 8, **melon/strawberry 10**.

---

## 2. The strawberries — confirmed, and it is worse than "some"

Rewritten probe, all 6 gate seeds:

```
  deaths by crop          STRAWBERRY:187  WHEAT:12  MELON:9  TOMATO:4  CARROT:1
  TOTAL LOSS (age<yield)  ~4 per game     STRAWBERRY:24  MELON:1
  deaths by true age      a3:14 a5:10 a9:10 a14:19 a17:138 ...
```

**~4 strawberries per game are planted, never watered, and die before their first yield.** Seed money gone, the tile dead for 3–9 days, plus a dig before it can be replanted. Total loss, every game.

The planting→death pairs show your pattern exactly:

```
  planted d12  died d15   age 3   x14   <-- NEVER YIELDED
  planted d12  died d19   age 7   x2    <-- NEVER YIELDED
  planted d12  died d21   age 9   x1    <-- NEVER YIELDED
  planted d13  died d22   age 9   x7    <-- NEVER YIELDED
```

### And here is the part that matters: **every single one is in SW**

```
  ALL deaths by quadrant   SW/STRAWBERRY:103   NE/STRAWBERRY:84   ...
  TOTAL-LOSS by quadrant   SW/STRAWBERRY:24    SW/MELON:1
                           (NW: 0   NE: 0   SE: 0)
```

Not one crop dies before yielding in NW, NE or SE. **All 25 total losses are in the SW quadrant.**

That is not a watering-priority bug — it is the **SW worker's band being over-subscribed**. And the playbook already caught this exact mechanism once before (line 213, from the R38 sheep test):

> *"the south strb tiles miss their every-other-day water, die (2 misses = weed), and the factory unwinds... ~$18k of destroyed factory."*

So the south strawberry factory has been quietly bleeding the whole time, not just during that one sheep experiment. The fix is not "water harder" — it is **not planting more strawberries in the south than that one worker can physically tend**, and putting the surplus tiles into wheat/carrot (far fewer ops per unit).

---

## 3. The milk — you are right that it ends at $300. The obvious fixes are both dead.

Price trace, live20_18:

```
  day     MILK    WOOL    EGG   STRAWBERRY   MELON
    0     169     206     50       128        256
   12     233     214     45       192        220
   20     267     177     44       215        213
   29     292       1     42       188        142    (seed 42)
   29     314     248     42       316        148    (seed 5)
```

**Milk climbs all season to $292–314. Eggs sit flat at $42.** The farm is running 6 cows / 6 sheep / 6 geese on 18 north sites with a hard-coded mix and no price response. The war model already ranks milk **highest of any item for own-gain (+$7,571 per unit/day)**, because town drain (22/day) keeps milk in permanent structural deficit — selling more does not crash it.

So I built the pivot and measured it. **It scored exactly +0.**

**R54a price-conditional cow ceiling** (raise cow target 6 → 8 when milk ≥ $250):

```
  astra_live20_18   101,682
  astra_live20_20   101,682     +0
```

Zero. Because **all 18 north sites are already committed before the signal is actionable.** The binding constraint is site count, not the target. This independently confirms R42/R43/R51 — there is no free slot, and the south expansion was measured at −26k to −71k.

### Then I tested the last lever the playbook had flagged as untested

Line 233 says *"hand #15 costs ~$377–610/day — crew 14 is the cap that matters"*, and line 235 left the south-animal build disabled *"for a future paying-15th-hand test"*. Both of your defects trace to the same root cause — the crew is oversubscribed (demand 166 ops/day vs 131 capacity), so **survival waters and care ops are the jobs that get dropped**. So:

**R55 — allow a 14th hand (crew 15):**

```
  astra_live20_18   101,682
  astra_live20_21    97,603     -4,079
```

**Measured negative.** The wages eat the gain. That lever is now closed for good — crew 14 is confirmed optimal.

---

## 4. So where does that leave the milk?

Honest answer: **the cows we already own are the unmonetized milk.**

Care coverage is measured at **40%**, and the care prize for a cow is **11 → 31 units per season (×2.8)**. At $300 milk, that is the single biggest number on the board — the playbook prices the unclaimed animal leg at **$8–20k/season**. Our 6 cows are running at 40% of the output they are capable of.

But capturing it needs labour ops, labour is capped at 131/day, and adding a hand costs −4,079. So the care prize can only be won by **taking ops from something else** — and labour reallocation is 0-for-7 in this project's history (R40, R51b, and five others). That is now the whole game, and it needs to be attempted as one careful, measured mechanism, not a hopeful edit.

---

## 5. Status

| Item | Status |
|---|---|
| Seed leak (>60 seeds stranded) | **FIXED** — v31 built, +370, pouch 43 → 12 |
| Strawberries dying before yield | **CONFIRMED + LOCALIZED** — ~4/game, **100% in SW** |
| Milk not monetized | **CONFIRMED** at $292–314; cow pivot **+0**, 15th hand **−4,079**; real lever is 40% care |
| v31 submission | **BLOCKED** — no Kaggle credentials in the sandbox |

**v31 is still unsubmitted** (`submit/v31_champion.py`, 116,718 bytes). The sandbox lost the Kaggle credentials, so `kaggle` returns "Authentication required." Needs `kaggle auth login` or a manual upload.

### Ranked next steps

1. **Get v31 submitted** — it is real, measured, and stops us setting $430 on fire every game.
2. **Cap south strawberries to what the SW worker can tend.** This is the highest-confidence fix on the board: the counterfactual is *zero* (a dead strawberry earned nothing), it is localized to one quadrant, and it needs no extra labour. Surplus tiles go to wheat/carrot.
3. **Attack care coverage as a single measured mechanism.** Biggest prize ($8–20k), worst track record (0-for-7). Attempt it alone, gated on the SW fix landing first.
4. Do **not** retry: more cows/animals (no free slot, +0), a 15th hand (−4,079), south animals (−26k to −71k).

## Files

| File | What |
|---|---|
| `war/weed_deaths2.py` | **the fixed probe** — per-plant age, first-yield loss bound, quadrant attribution |
| `war/weed_deaths.py` | the broken original, kept so the bug is not reinvented |
| `war/astra_live20_20.py` | R54a cow ceiling — measured +0, kept as evidence |
| `war/astra_live20_21.py` | R55 15th hand — measured −4,079, kept as evidence |
| `submit/v31_champion.py` | v31, ready, unsubmitted |
