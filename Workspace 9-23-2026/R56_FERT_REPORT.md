# R56 — Fertilizer on strawberries: right idea, wrong time

**Date:** 2026-09-15
**You said:** "Find a way to add fertilizer to our crops for strawberries — in most games by day 30 straw is still sitting at 200+ and if we fert it gives us more to spray than it does to sell the fert."

**Short version: your economics are correct and the opportunity is real and large. But it measures negative today, for a specific reason — and that reason is already on our to-do list. Fix the water first, then this pays.**

---

## 1. Your premise checks out, and the waste is bigger than you thought

Engine facts (`intel/engine_kagg_1327.py`):

```
L481  tile["fertilized_until_day"] = max(..., day + 2)     lasts 3 days
L799  fertilized = was_watered and fertilized_until_day >= day
L800  yield_units = min(max_yield, yield_units + (2 if fertilized else 1))
L796  production stops only once production_count > max_yield
STRAWBERRY: max_yield 4, ongoing, interval 2 -> four production ticks
```

A fertilized **and watered** tick pays **+2 units instead of +1**. Strawberry has four ticks, so a fully covered plant is **8 units instead of 4**. At strawberry's closing price of $200–316, **one fertilizer is worth $200–632 in the field versus about $50 sold on the market.**

And here is what we are actually doing with it (seed 42, one full season):

```
COLLECT_FERTILIZER   264     <-- we collect 264 units a season
FERTILIZE             17     <-- we spray 17  (6.4%)
```

**We spray 6.4% of the fertilizer we produce and sell the rest at ~$50.** The debug trace shows stock sitting at **3–19 units in the shed every single day from d4 onward**, while **30–47 tiles per day** are profitable candidates. We are sitting on the input and not using it.

So why is it not free money?

---

## 2. Because fertilizer only pays on a WATERED tile

That `L799` line is the whole story:

```python
fertilized = was_watered and tile["fertilized_until_day"] >= day
```

**No water, no bonus. The fertilizer is worth exactly zero.**

And we established last round that **every single one of the ~4 strawberries per game that die before yielding is in SW**, killed by missed water. So we would be paying a labour hour to spray tiles that then do not get watered — and that hour comes out of the budget that was going to do the watering.

---

## 3. Every version I tested is negative — but they get better as targeting sharpens

| Variant | Gate | Result |
|---|---|---|
| **R56b** flag 40 tiles, any crop | `value > 35` | **−8,106** |
| **R56c** strawberry only | any quad | **−5,610** |
| **R56d** strawberry, watered quads only | NW/NE only | **−2,016** |

The `value > 35` gate was the first problem — it admits wheat (~$100) and carrot (~$70), so R56b sprayed cheap crops at a loss. Restricting to strawberries recovered 2.5k of that. Restricting further to the quads that actually land their water recovered another 3.6k.

**And the trend matters: two seeds went clearly positive.**

```
R56d vs baseline:   seed 202  +2,483     seed 777  +3,362
                    seed 42   -4,853     seed 5    -3,760
```

So fertilizer is not worthless — it is *just barely* not worth a marginal labour hour in the quads that are already water-starved, and clearly worth it where the water lands. The crew is oversubscribed (166 ops demanded vs 131 capacity), so every extra op displaces one worth more.

---

## 4. What this means for the plan

**Fertilizer is a follow-on prize, not a standalone fix.** It is gated behind the thing we already knew we had to do:

1. **Cap south strawberries to what the SW worker can tend** (the open item from R54). This stops ~4 tiles/game dying before they yield anything.
2. **Then re-run R56d.** Watered tiles make the fertilizer pay, and step 1 frees exactly the labour that step 2 needs. My prediction is R56d flips positive once the south stops burning hours on crops that were never going to survive.

Trying to fertilize *first* is backwards: it spends the scarce hour on a tile that cannot pay it back.

---

## 5. Standing status

- **v31 (`submit/v31_champion.py`) is still NOT SUBMITTED** — the sandbox has no Kaggle credentials. It is the seed-leak fix (+370, wheat pouch at the whistle 43 → 12) and is fully validated.
- Do not retry: extra cows (**+0**, no free slot), a 15th hand (**−4,079**), fertilize-all (**−8,106**), south animals (−26k to −71k).

## Files

| File | What |
|---|---|
| `war/fert_probe.py` | counts fertilizer collected / sprayed / sold per season |
| `war/astra_live20_22.py` | R56a reserve-against-opportunity — **+0**, not the constraint |
| `war/astra_live20_23.py` | R56b fert cap 8 → 40 — **−8,106** |
| `war/astra_live20_24.py` | R56c strawberry-only — **−5,610** |
| `war/astra_live20_25.py` | R56d strawberry + watered quads — **−2,016** (keep, re-test after the SW fix) |
| `war/astra_live20_22_dbg.py` | instrumented build that produced the candidate/stock trace |
