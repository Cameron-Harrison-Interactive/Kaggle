# R61 — The EOD auto-dump: right mechanism, wrong conclusion

**Date:** 2026-09-15
**You said:** workers get sent to the shed at end of day and drop all inventory anyway, so they don't need to go back — only melons need an ASAP sell.

**You are right about the mechanism. The engine confirms it.** But when I removed the mid-day drops it cost **−7,124**, and the reason changes the conclusion.

---

## 1. You were right — verified in the engine

```python
# _end_of_day(), intel/engine_kagg_1327.py L878-881
_drop_inventories_to_shed(private, shed_cap)
farm["farmer"] = list(_default_spawn(board_size))
farm["hands"] = []
private["inventories"] = [{}]
```

Every end of day the engine dumps **all** worker inventory into the shed and despawns the hands. So yes — the cargo does arrive for free at h23.

## 2. But two things stop us deleting the drops

**(a) Overflow is destroyed.** The docstring on `_drop_inventories_to_shed` reads *"up to `capacity`; **overflow is discarded**"*. Capacity is 100. Measured peaks: **shed 76 (non-wheat), cargo 69** — so a pure EOD dump would hit ~145 and destroy ~45 units in a day. The drops are load-bearing overflow protection.

**(b) Goods in the shed can be SOLD; goods on a worker cannot.** This is the big one. Market orders execute from the shed, so the mid-day drop is not transport — **it is what sets the sell cadence.** Hold everything to h23 and you sell one glut the next morning into a falling price, instead of feeding units out through the day as the market absorbs them. That is exactly what the original comment says (*"absorb into rising prices instead of one end-of-day glut burst"*), and the measurement backs it: **−7,124**.

So the drop trip isn't wasted work. It buys price.

---

## 3. Result

| Variant | Rule | Result |
|---|---|---|
| **R61** drop only when loaded (10+) or shed near cap | keep final-day + overflow guard | **−7,124** |

Per seed: 91,194 / 96,913 / 92,666 / 90,653 / 96,611 / **99,312**. Interesting split — seed 777 went **+10,150** while the rest fell, so on some shapes the glut sale is fine. Not shippable, but a real signal that seed-dependent sell cadence is worth a look later.

---

## 4. On the architecture: preset scripted routes

I agree with the diagnosis behind this, and I want to build it — but I want to be straight about what the measurements now say.

The dynamic router isn't there by accident; it exists because three things change under it every turn: **shed capacity**, **live prices**, and **crop age**. The failures we keep hitting are the router making bad local calls (ripe tiles = bare dirt at priority 1, fert with no guaranteed return trip).

I think your framing is the right fix, and the concrete first piece is the one you named:

- **Scout SE on opponent crop choice.** If they are not on carrots → SE runs the carrot route. If they are → SE runs the wheat/fert/water route. Both routes fully specified up front: what to plant, when, how many seeds, and the water/fert days.
- Preset routes also fix **over-buying**, exactly as you say — a scripted route knows it needs N seeds on day D, so the pouch stops accumulating.

That is a real piece of work, not a patch, and I'd want to spec the routes with you before writing them so we don't guess wrong on the carrot/wheat split.

---

## Standing status

- **v31 (`submit/v31_champion.py`) STILL NOT SUBMITTED** — no Kaggle credentials in the sandbox. Needs `kaggle auth login` or a manual upload. +370, seed-leak fix, fully validated.
- **Nothing this session beat the baseline.** Session negatives, all measured: extra cows **+0**, 15th hand **−4,079**, fert-all **−8,106**, fert-strb **−5,610**, fert-watered **−2,016**, paired ratchet **−2,591**, SE-late **−288**, ripe-priority **−5,788**, EOD-drop **−7,124**.

## Files

| File | What |
|---|---|
| `war/astra_live20_33.py` | R61 drop-only-when-needed — **−7,124** (777 +10,150) |
| `war/astra_live20_32.py` | R60 ripe tiles priority 0 — **−5,788** |
| `war/astra_live20_31.py` | R59b SE from d20 — **−288**, best of the round |
