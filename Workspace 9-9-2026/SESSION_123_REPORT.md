# SESSION 123 — 2026-09-08 ~02:00 UTC
## v28 "HARVEST MOON": root-cause pass. Solo mean $18.8k → $66.8k (7 seeds)

**Build:** `topbots/v28_harvest_moon.py` (v28.12, 513 lines). No submissions made (held per standing order).

---

## ROOT CAUSES FOUND AND FIXED (each verified by trace, not guessed)

1. **Wheat belt was cut in the v28.1 rewrite** → early cash engine died → cow ramp starved at 2-4 cows.
   FIX: belt reinstated (12 tiles d0-12, 10 to d18, 6 after; waves d0-13). Herd now completes **8C+6G by d9-12 on every seed**.
2. **Feed-buy price gate `wheat ≤ $36`** starved animals exactly when wheat ran $45+ (late drain) while milk sold $230.
   FIX: gate → ≤55. Feed is life; milk at $230 makes $50 wheat hugely +EV.
3. **Labor allocator double-locked tasks**: FEED task objects were duplicated in farmer/hand pools with separate "taken" flags → two workers walked to the same animal, one wasted the trip.
   FIX: shared task objects; `valid()` re-checked before executing on arrival.
4. **Wheat pickup only created when NOBODY carried wheat** → one distant carrier made the farmer+9 hands abandon feeding at day-end (traced: d22h20, 6 animals unfed, farmer watering far tiles).
   FIX: per-unit pickups — every unit without wheat picks up when feeding is pending.
5. **`drain_cap + 2` leak sold past market I0** → refilled the surplus the town shops were draining → milk pinned at $145 (< our 150 gate) with **$18k of milk trapped in the shed (73 units)**.
   FIX: strict drain caps for MILK/STRB/TOMATO/WOOL — never sell past I0; every unit prices ≥ base.
6. **Morning order assembly put SELL last** → the daily re-hire flood (engine fires ALL hands at midnight, `farm["hands"]=[]`) ate the 10-order cap, sells got 0-1 slots.
   FIX: sells before hires; sells sorted by value; feed order dedupe.
7. **CARE under-served** (6-9/day vs 13 animals; care = +1 unit on fed production days ≈ doubles output). FIX: prio 2→1, daily.
8. **Walking was 64-65% of all unit-steps.** FIX: priority-distance weight 10→6 (proximity matters); animal harvests batched at yield ≥3 (fewer shed trips); milk-runner drops at ≥4.

## ENGINE FACTS DECODED THIS SESSION (from engine source)

- **Price curves exact:** price = base ± amp·f(|I−I0|), f(T)=1. TOMATO below-hinge T=200 with quadratic runaway past the knee ($84@−200, $300@−400); MILK sqrt T=122 ($270@−161); STRB sqrt T=100 ($326@−598); WOOL log T=105 ($386@−105+); MELON no drain shop, sq-above crash ~$150 cumulative sold.
- **Milk market drain ≈ 6-10/day** (3/8 shop types) → **~8 cows is the market cap**; more cows just pile milk (tested 11 cows: seed collapsed to $16k from feed-race escapes, others flat).
- **Tomato drain ≈ 10/day** → 14 tiles saturates it; selling harder just slides price to the $60-84 knee.
- **Strb drain < production possible** → deficit grows all game → price rises unbounded ($300+ by d26).
- **Melon: $250 base, no shop drains it** → 2 waves × 8 tiles = ~96 units at ~$240 avg = ~$23k/2 waves for $1,280 of seeds. Added waves d9/d13.
- **SELL only works for the 9 products** — animals cannot be liquidated; early geese are a permanent bet.
- **All hands fired at midnight daily**; hire fib resets; farmer teleports to spawn.
- Shop drain ticks ~0.25 units/hour/shop-instance (measured on EGG/MILK).

## VALIDATION (fresh module per seed — harness bug fixed: state leaked across seeds before)

| seed | 101 | 202 | 303 | 404 | 505 | 606 | 707 |
|---|---|---|---|---|---|---|---|
| final money | $68,352 | $79,614 | $52,274 | $81,251 | $66,960 | $64,223 | $54,814 |

**Mean $66.8k · median $67.0k · min $52.3k.** Herd 7-8C+6G all seeds. Weeds ≤4 (was ≤15). Deterministic (101 run twice → identical).

## NOT FIXED / REMAINING (honest)

- **$100k solo gate not reached.** Remaining levers: strb planting lags (ends 3-8 tiles vs target 12 — PLANT still loses labor races); endgame d28 dump sells below caps; sheep/wool on YARN-unlock seeds (rare, blocked by herd cap); possible more labor efficiency.
- **H2H untested for v28.12.** Opponent market actions shift drains/deficits (their buys deepen our deficits, their dumps crash our prices). Router gate (≥60%) is the next milestone before any submission talk.
- Solo $66.8k vs ymg reference $166k — but that replay is H2H; solo and H2H economics differ. Do not treat the gap as like-for-like.

## HISTORY (seeds 101/202/303 unless noted)
sticky $6.5-12.5k → crop-econ $1-4k → pipeline v2 $1-9k → feed-sacred $23.2/13.9/13.6k → herd-scaling $23.4/10.7/6.4k → v28.1 rewrite $11.2/10.1/5.4k → v28.2 $18.8/15.6/21.5k → **v28.12 mean $66.8k (7 seeds)**.

## NEXT
1. Strb planting reliability (PLANT labor race) — biggest clean lever left.
2. H2H harness vs router (tt_router_938.py) — the real gate.
3. Only after solo $100k+ AND H2H ≥60%: ask user about submission. **Nothing goes out without explicit go.**
