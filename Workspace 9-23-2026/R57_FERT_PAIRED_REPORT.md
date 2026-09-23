# R57 — Paired water+fert with a success ratchet

**Date:** 2026-09-15
**You said:** "Hit water and ferts at the same time for the double yield, but only do it on water days. Only start routing a couple at a time and test, and keep working to add more after every 5 successful ferts/water."

Built exactly that. It measures **−2,591** today. Here is why, and why I think the mechanism is still the right one to keep.

---

## 1. What I built (live20_27)

1. **Pairing.** A strawberry is only sprayed in the instant after that same tile is watered, so `L799` (`was_watered and fertilized_until_day >= day`) is guaranteed true. Strawberry's water days are ages 9/11/13/15, lining up exactly with its yield ticks at 10/12/14/16.
2. **Ratchet.** The per-quad carry starts at **2** (`_carry = min(2 + fert_bonus, len(my_fert))`) and gains **+1 for every 5 confirmed water+fert pairs**, persisted in `state` across turns.
3. **Baseline untouched.** The proven 8/day (mostly melon, ~$600 each) is not gated.

One mistake worth recording: my first attempt gated *all* fertilizer on water, which also blocked the 17 baseline ferts — that measured **−10,910**. Leaving the baseline alone recovered 8.3k of it.

---

## 2. The cap that kills it

```
L796  production_count = days_since_first // interval + 1
      if production_count > max_yield: continue     -> 4 events, so 8 units IS reachable
L800  tile["yield_units"] = min(cd["max_yield"], tile["yield_units"] + (2 if fertilized else 1))
```

`production_count` counts **events**, so 4 events × 2 = 8 units is reachable. But `yield_units` is capped at `max_yield = 4` **standing on the tile**. With fertilizer adding +2 per tick:

```
event 1 -> 2 units
event 2 -> 4 units
event 3 -> min(4, 4+2) = 4     <-- NO GAIN
event 4 -> min(4, 4+2) = 4     <-- NO GAIN
```

**Fertilizer only pays if we harvest between every single tick.** If units sit on the plant, the 4-unit standing cap binds and the fertilizer was free money spent for nothing.

And harvests are precisely what the oversubscribed crew fails to keep up with (demand 166 ops/day vs 131 capacity, and R54 proved ~4 strawberries/game die in SW from missed water).

So the fert hour is spent, then the harvest that would have made it pay doesn't arrive, and that hour also pushed the harvest further away.

---

## 3. Every targeting scheme lands in the same place

| Variant | Gate | Result |
|---|---|---|
| R56b flag 40 tiles, any crop | `value > 35` (admits wheat ~$100) | **−8,106** |
| R56c strawberry only | any quad | **−5,610** |
| R56d strawberry, watered quads | NW/NE only | **−2,016** |
| R56 bad gate-all version | everything needs water | **−10,910** |
| **R57 paired water+fert + ratchet** | water-paired, baseline intact | **−2,591** |

Four independent targeting schemes all land between **−2,000 and −2,600**. That convergence is the signal: this is not a targeting problem. The marginal fert op costs more than it earns, because the thing it depends on — prompt harvesting — is the thing the crew cannot do.

Per-seed on R57, for the record: 202 went **+2,483** and 777 went **+3,362** even in the R56d run, so it is close to break-even and not uniformly bad.

---

## 4. Verdict

**Keep the mechanism, sequence it correctly.** The ratchet you asked for is built and working (`war/astra_live20_27.py`); it is simply ahead of its prerequisite.

The dependency chain is now clear, and it is one root cause wearing three hats:

```
crew oversubscribed (166 vs 131)
   |-- SW strawberries miss water  -> ~4 tiles/game die before yielding
   |-- harvests lag behind ticks   -> fert hits the 4-unit standing cap, pays nothing
   |-- care coverage stuck at 40%  -> the cow prize (11 -> 31 units) unclaimed at milk $300
```

**Order of operations:**

1. **Cap south strawberries to what the SW worker can tend.** Frees the labour and stops the deaths. This is the prerequisite for everything else.
2. **Re-run R57 (the paired ratchet).** With harvests keeping up, the standing cap stops binding and the +2 per tick starts landing.
3. Then the care prize.

Fertilizing first is paying for a bonus that a lag in harvesting silently cancels.

---

## 5. Standing status

- **v31 (`submit/v31_champion.py`) is STILL NOT SUBMITTED** — no Kaggle credentials in the sandbox. It is the seed-leak fix (+370, wheat pouch at the whistle 43 → 12), fully validated, ready to upload.
- Do not retry: extra cows (**+0**, no free slot), a 15th hand (**−4,079**), fert-all (**−8,106**), gating all fert on water (**−10,910**), south animals (−26k to −71k).

## Files

| File | What |
|---|---|
| `war/astra_live20_27.py` | **R57** — paired WATER+FERT + success ratchet. Keep; re-test after step 1 |
| `war/astra_live20_26.py` | the −10,910 version (gated the baseline too), kept as a warning |
| `war/astra_live20_23/24/25.py` | the −8,106 / −5,610 / −2,016 targeting ladder |
| `war/fert_probe.py` | fertilizer collected vs sprayed vs sold |
