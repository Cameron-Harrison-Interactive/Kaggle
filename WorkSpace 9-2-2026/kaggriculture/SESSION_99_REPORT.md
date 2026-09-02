# SESSION 99 — land hypothesis + 6 real-edge tests (all measured)

Bench = solo vs PASS, same-seed, `_ref/bench_variants.py`, seeds 1/2/3.
v1112fr base: seed1 179,265 · seed2 186,184 · seed3 189,706 (avg 185,052).
Nothing shipped. Live sub still 55925101 (v1112fr, ~1728.6).

## 1. Your land call — tested first, answer is: we never buy that land

Engine (`LAND_PRICES`): NE $1,000 · SW $2,000 · SE $4,000. There is no $5k land.
Decoded all 5 route tapes in v1112fr: **every route buys exactly 2 lands** —
NE (D6H14/16) and SW (D10H12 / D11H01). **SE is never bought.** (The "SE by D10"
note from the egg session was wrong: it was the grafted egg build's own purchase.)

Removing land purchases anyway, to price them:

| variant | seed1 | seed2 | seed3 | avg Δ |
|---|---|---|---|---|
| v1112fr | 179,265 | 186,184 | 189,706 | — |
| no SW ($2k saved) | 140,871 | 137,672 | 150,072 | **−40,251** |
| no NE ($1k saved) | 47,494 | 47,497 | 65,283 | **−125,392** |

Land is the highest-ROI purchase in the game by two orders of magnitude.
The cash squeeze is not land.

## 2. Shed-headroom lever (was next on the list) — dead

Instrumented `_drop_inventories_to_shed` for the whole game:
**0 units discarded, all seeds.** Mean shed occupancy 33/100, only 1 hour ≥95.
The "+$1–3k of EOD overflow" estimate from earlier sessions was wrong. Closed.

## 3. Where the money actually is (seed 1 flow, gross)

| item | units sold | revenue | avg | end price | verdict |
|---|---|---|---|---|---|
| WHEAT | 2,982 | 127,151 | 42.6 | 45 (rising) | buys 2,891 @ 42.0 → **maker nets only ~$5.6k** |
| STRAWBERRY | 319 | 75,390 | 236 | 253 | under-supplied |
| MILK | 266 | 68,793 | 259 | 276 (rising) | under-supplied |
| FERTILIZER | 257 | 19,121 | 74 | 49 | town never consumes FERT → price only falls |
| MELON | 66 | 16,398 | 249 | 237 | fine |
| WOOL | 135 | 11,419 | **84.6** | **5 (floor)** | self-crashed |
| CARROT | 57 | 4,033 | 71 | 80 | fine |

WOOL glut curve is quadratic: `200 − 0.058·(inv−10000)²`, T=105 → ~58 net
surplus units take it to the floor. D20-D29 wool clears at $2–5.

## 4. Six edge ideas tested against that picture

| # | idea | result (avg Δ) |
|---|---|---|
| a | hold WOOL in shed, sell only above a price floor (floors 60/120/180) | −10,275 / −13,133 / −29,353 |
| b | same, with tight shed guard (only hold while shed ≤25) | **+20** (fires almost never) |
| c | wheat MarketMaker off / batch 30 / batch 90 / min-profit 4.0 | −746 / −153 / −228 / −30 |
| d | SHEEP→COW swap (wool $85 realised vs milk $259) | **−114,890** |
| e | hold wool on the sheep (skip HARVEST under price floor, free max_held=6 storage) | −186 to −641 |
| f | hire cap 10 / 11 / 12 / 13 per day | −64,958 / −24,880 / −5,603 / −313 |

Mechanisms behind the two big failures:

* **(a) shed space is the scarce resource, not shed headroom.** Holding ~40 wool
  costs ~$19k: the wheat maker's 60-unit batch stops fitting and milk/strawberry
  get squeezed out of the EOD drop. Wool revenue itself did improve
  (11,419 → 12,684 on fewer units) — it is just worth far less than the slots.
* **(d) early cash, not product mix, is the binding constraint.** Cows first yield
  at placed_day+8 vs sheep+6, so D6–D12 wool cash disappears; the whole snowball
  fails (strawberry 319→66 units, wheat 2,982→1,632). Milk price ended at **324**
  in that run — the market wants far more milk, we just can't finance it early.
* **(f)** hands are priced correctly by the fib ladder: the 12th hand is worth
  ~$5.6k/game, the 13th ~$0.3k — v1112fr sits exactly at break-even. The tape is
  labour-saturated.

## 5. Standing conclusion

Solo cash for this architecture is walled by (i) shed capacity 100,
(ii) the fib hire ladder at break-even, (iii) D0–D11 cash starvation, and
(iv) quadratic glut curves on WOOL/EGG. Wheat/milk/strawberry are the only
non-saturated sinks and all three are already run to the labour limit.
No candidate here is shippable; base stays.

Tools added: `_ref/build_landvar.py`, `_ref/build_cfg.py`, `_ref/build_swap.py`,
`_ref/build_throttle.py`, `_ref/build_woolhold.py`, `_ref/build_hirecap.py`,
`_ref/bench_variants.py`, `_ref/probe_shed.py`, `_ref/probe_sales.py`,
`_ref/probe_econ.py`.
(Env note: sandbox was wiped — `pip install kaggle_environments==1.32.7` again.)
