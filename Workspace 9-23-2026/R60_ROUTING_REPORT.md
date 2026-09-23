# R59/R60 — SE switch, and the routing fix

**Date:** 2026-09-15
**You said:** "LOL I meant SE has no strawberries, only wheat and carrots for late game! But yes add the fert — but also fix the routing as you go. Do a little at a time to make sure it's correct."

I did it one step at a time, exactly as asked. All three steps measured negative or flat. Honest record below.

---

## 1. SE switch

| Variant | Rule | Result |
|---|---|---|
| **R59** SE = wheat/carrot all season | no strawberry in SE ever | **−8,245** |
| **R59b** SE = wheat/carrot from **d20** only | early SE strawberries kept | **−288** |

Your "for late game" reading was the right one — trimming the switch to d20 recovered 8k of the 8.2k loss, leaving it essentially break-even. R59b is worth remembering as a near-miss: it is the correct shape, it just doesn't pay yet.

Why late strawberries are marginal: a strawberry sown at d20 first-yields at +10 = d30, past the horn. It gets at most one tick. So the switch is logical — it just isn't worth anything measurable yet.

---

## 2. The routing fix — and the real defect I found

You were right that I fert without fixing what happens after. Here is the actual line:

```python
stops.append((0 if (dying or tick) else 1, idx, pos_b, "PLANT"))
```

**A tile with ripe units sitting on it is priority 1 — the same as bare dirt.** Dying plants and tick-day waters jump the queue; the harvest that turns units into money does not. Combined with engine L800 capping standing units at `max_yield` (4), a fertilized tile that isn't revisited before its next tick silently throws the +2 away. That is the mechanism behind every negative fert result.

**R60: give ripe tiles priority 0.**

```
astra_live20_18   101,682
astra_live20_32    95,895      -5,788
```

It backfired, and the reason is instructive: the band is walked as a **serpentine** route, so pulling ripe tiles to the front makes the worker zig-zag across the quad. The extra walking costs more than the units recovered.

That is a genuinely useful negative — it says the answer is **not** reordering. The route is already efficient; what's missing is *coverage* (the worker runs out of `wbudget` before it reaches the end of the band). Reordering shuffles the same shortfall around; it doesn't add hours.

---

## 3. What this all adds up to

Every lever I have pulled this session lands in the same place:

| Lever | Result |
|---|---|
| Extra cows (price pivot) | **+0** (no free slot — 18 sites full) |
| 15th hand | **−4,079** |
| Fert, all crops | **−8,106** |
| Fert, strawberry only | **−5,610** |
| Fert, watered quads | **−2,016** |
| Fert, paired WATER+FERT + ratchet | **−2,591** |
| SE → wheat/carrot (late) | **−288** |
| Ripe tiles → priority 0 | **−5,788** |

The crop-swap levers fail because strawberries are our best crop everywhere. The fert levers fail because the follow-up harvest doesn't land. The routing lever fails because reordering can't create hours that don't exist.

**They are all one constraint: the crew cannot finish its band.** Demand 166 ops/day against 131 capacity.

---

## 4. The next thing I'd try

Not reordering — **shortening the walk**, so the existing hours cover more ground. The serpentine band is fixed per quad; the worker's `wbudget` is spent mostly on movement (1.56 moves per productive op, measured in the R52 census). Ideas, cheapest first:

1. **Shrink the bands.** More workers per quad means each covers fewer tiles and finishes. Currently `chunk = len(band_order) // len(workers)`.
2. **Split the drop.** The `DROP` trip to the shed is a long detour; batching it differently could return hours.
3. Only then revisit fert — with harvests landing, the R57 ratchet should read positive.

I'd want to do these one at a time, the same way, and stop on the first negative.

---

## Standing status

- **v31 (`submit/v31_champion.py`) is STILL NOT SUBMITTED.** No Kaggle credentials in the sandbox — this needs you. It is the seed-leak fix (+370, wheat pouch at the whistle 43 → 12), fully validated.
- You're right that +370 doesn't win matches. **Nothing this session beat the baseline.** I'd rather tell you that plainly than dress up a negative.

## Files

| File | What |
|---|---|
| `war/astra_live20_30.py` | R59 SE wheat/carrot all season — **−8,245** |
| `war/astra_live20_31.py` | R59b SE from d20 — **−288** (best of the round; correct shape) |
| `war/astra_live20_32.py` | R60 ripe tiles priority 0 — **−5,788** |
| `war/astra_live20_27.py` | R57 paired WATER+FERT + ratchet — **−2,591**, re-test after coverage improves |
