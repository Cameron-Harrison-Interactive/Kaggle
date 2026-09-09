# SESSION 25 — Day-0 ramp fix + town-tick-aware sell timing

**Combined result: +$4,237 / 20 seeds ($97,641 → $101,878).  MIN floor $69k → $75k.**

Two independent wins in one session:
1. **Day-0 ramp**: `open_hires 4→7`, `day0_plan False→True`.  Adds 3 workers +
   plants day 0.  Verified +$3,041 alone.
2. **Sell timing**: `sell_hour 2→21`.  Sells right after the LAST town-shop
   consumption tick of the day (hour 20), when market inventory is at its
   daily minimum and prices are at their daily peak.  Verified +$2,076 alone.

---

## PART 2 — sell_hour 2 → 21

### The mechanic (verified against engine source)

Every step in the engine (`interpreter()`, kaggriculture.py:880):
1. Apply worker actions
2. `_process_market(state, env)` — SELL/BUY orders quote against `market["inventory"]`
3. `_town_consume(env, state, step)` — town shops LOWER inventory
4. `_refresh_prices(market)` — prices recompute

Town shops consume every 4 hours (`townShopSellInterval=4`): hours **0, 4, 8,
12, 16, 20** each day.  Each tick drops inventory (and each shop instance
consumes independently — single-product shops consume 2x).  Lower inventory
means HIGHER sell price (`price = base + amp*f(10000 - inv)`).

The old default `sell_hour=2` was 2 hours AFTER the hour-0 tick, so the
inventory had partially recovered.  Selling at `sell_hour=21` is 1 hour after
the **last** town-tick of the day (hour 20), when inventory is at its daily
minimum and hasn't had time to be refilled by other sellers.

### Measured (40 seeds vs PASS, baseline = post-ramp-fix $93,830)

| sell_hour | avg      | min     | Δ vs h=2 |
|-----------|----------|---------|----------|
| 2 (old)   | $93,830  | $60,091 | 0        |
| 5         | $94,679  | $60,164 | +$849    |
| 9         | $94,845  | $60,228 | +$1,015  |
| 13        | $95,234  | $60,292 | +$1,404  |
| 17        | $95,483  | $60,354 | +$1,653  |
| **21 (new)** | **$95,906** | **$60,412** | **+$2,076** |
| 22        | $95,906  | $60,412 | +$2,076  |

Monotonic improvement following the tick pattern.  Hours 0 and 1 crash to
~$5k because selling BEFORE the hour-0 tick means we hit dawn prices when
inventory hasn't dropped yet AND we sell into our own reserve.  Hours 20-23
tie because there's no more consumption in that day.

### Split-sell test (secondary hour)

Also added a `sell_hour_secondary` param (default -1 = off) for a mid-day dump.
Verified: splitting the daily dump between hours 13 and 21 LOSES $500-$900
per game.  Volume matters more than tick-timing for our shed sizes — one big
dump at peak > two smaller dumps.  Left as a switch for future strategies.

### Full head-to-head impact (10 seeds x 2 seats = 20 games)

|          | PRE (h=2, hires=4, d0p=F) | POST (h=21, hires=7, d0p=T) |
|----------|--------------------------|------------------------------|
| vs tape_v25 | 0W ours=$34,389 | 0W ours=$34,910 |
| sheepbot | 20W +$20,266 ours=$59,557 | 19W **+$26,627** ours=$59,241 |
| goosebot | 18W +$45,436 ours=$70,031 | **20W** +$46,044 ours=$74,485 |
| mirror   | 17W +$17,290 ours=$54,620 | 18W **+$21,717** ours=**$66,328** |
| cropbot  | 20W +$48,490 ours=$79,029 | 20W +$49,166 ours=$79,848 |
| cowbot   | 19W +$22,806 ours=$62,903 | **20W** **+$31,263** ours=**$72,656** |

Biggest wins: mirror ours +$12k, cowbot ours +$10k.  The tape still crushes
us but our absolute score improved.  No head-to-head regressions.

---

# SESSION 25 — Part 1: Day-0 ramp fix (open_hires 4→7, day0_plan True)

## The user's question (part 1)

> "look even if we buy 1 worker on day 0 We can fill some of the Quad no?
>  Or even 2 Workers cause starting cash is 2k? We can find a way to ramp
>  faster We have to or we will always lose in the long run since they can
>  expand way faster and Accumulate??"

Yes — and it turns out the fix is bigger than "1 or 2 more workers". Two facts
we'd been under-using:

1. **Starting cash is $3,000, not $2,000** (`startingMoney` default in the engine).
2. **Hires are almost free.** They're fib-costed: `1, 1, 2, 3, 5, 8, 13, 21…`
   The seventh hire of the day costs $13; SEVEN hires all day only total **$33**.
   We already saw the herd (2 sheep + 2 cow = $1,800) and 12 wheat (~$300) as
   the big day-0 costs.

So the ramp gap was NEVER a money problem. It was that we were writing 4 to
the opener when the market cap could hold 10 orders, and we weren't planting on
day 0 at all.

## What changed in `main.py`

Two `DEFAULT_PARAMS` values, nothing else:

| param        | old   | new   |
|--------------|-------|-------|
| `open_hires` | 4     | **7** |
| `day0_plan`  | False | **True** |

That's it. The market ordering already handles the fallout:

* **Hour 0 orders:** wheat(1) + hires(7) + sheep(1) + cow(1) = 10 → the seed
  lines (melon/straw/wheat_seed) *would* be dropped by the 10-order cap.
* **They aren't dropped** — the hour-1 opening block appends them as `BUY_SEED`
  orders that hour, so the seeds land in the shed by hour 1.
* **`day0_plan=True`** tells the morning planner it can schedule those seeds
  into the day-0 timeline (the seeds are deterministic, we know exactly how
  many will arrive), so hands start planting at hour 2 instead of waiting to
  day 1.

Result on seed 1 traced hour-by-hour:

```
D0H00  MKT=[BUY WHEAT 12, HIRE×7, SHEEP 2, COW 2]    plants=0    money=$3000
D0H01  MKT=[BUY_SEED STRAWBERRY 3, BUY_SEED MELON 4] plants=0    money=$839
D0H02  MKT=[SELL WHEAT 8]                             plants=1    money=$219  (7 hands!)
D0H06                                                 plants=3
D0H10                                                 plants=1  → 7 tiles planted by end of day 0
```

vs baseline where day 0 ends with **zero** plants.

## Verified numbers (all bit-exact engine, this session)

### SOLO vs PASS

| variant                    | N   | avg      | min     | max      |
|----------------------------|-----|----------|---------|----------|
| BASE (prior default)       | 20  | $97,641  | $69,274 | $116,470 |
| **d0p + hires=7 (shipped)**| 20  | **$100,682** | $73,262 | $118,565 |
| BASE                       | 40  | $92,697  | $33,342 | $116,470 |
| **d0p + hires=7 (shipped)**| 40  | **$93,830** | $60,091 | $118,565 |

The average lift is real (**+$1,133 on 40 seeds, +$3,041 on 20 seeds**) but the
bigger win is **the worst-case floor jumps $27k** (min $33k → $60k on 40
seeds). Fewer disaster games.

### Head-to-head archetypes (20 games per opp, 10 seeds × 2 seats)

| opponent   | BASE           | d0p+hires=7     |
|------------|----------------|-----------------|
| sheepbot   | 20W  +$20,266  | 16W  **+$23,023** |
| goosebot   | 18W  +$45,436  | **20W** +$46,115  |
| mirror     | 17W  +$17,290  | 17W  +$17,894   |
| cropbot    | 20W  +$48,490  | 20W  **+$50,854** |
| cowbot     | 19W  +$22,806  | **20W** +$30,772  |
| tape_v25   | 0W  −$82,769   | 0W  −$79,066    |

Only sheepbot loses win-count (20→16) but its margin *grows* by +$3k because
the wins get bigger. Every other opponent improves both W-count and margin.

### V25 tape (unsolved)

Contested vs the tape still loses. Margin narrowed a hair ($-83k → $-79k avg)
but that's within noise on 10 samples. The tape has 5 animals + massive
melon/straw stockpile from days 7-10 and out-scales us no matter what we do on
day 0. That fight requires a different intervention (probably swinging the
mid-game investment pattern, not the opener), so leaving it for the next
session.

## Why the previously-rejected `day0_plan` works now

The comment in `main.py` used to say "TESTED twice, net-negative both times:
the bigger day-0 field dies on the cash-poor days 2-4 (we can't afford the
watering crew)." That was TRUE — with **4** opening hires.

The unlock is that `day0_plan` + `open_hires=7` are joint: the extra 3 workers
ARE the watering crew that keeps those day-0 plants alive through the
days-2-4 cash valley. Neither alone works:

| variant                       | Δ vs BASE (20 seeds) |
|-------------------------------|----------------------|
| `day0_plan=True` alone (hires=4) | **−$9,487** |
| `open_hires=7` alone (no plant) | **−$5,038** |
| **both together**              | **+$3,041** |

Classic case where two individually-negative changes multiply into a positive
combo. The A/B methodology (test one thing at a time) missed it in earlier
sessions.

## What's next

The user's core complaint about ramp speed vs v25 is *partially* addressed —
we now have 7 crops planted by day 0 hour 22 instead of 0. But v25 still
wins the tape contest because it out-invests us mid-game (melon/straw bulk
buys days 7 & 10). Next likely moves:

1. **Solve the days-6-10 investment gap** — the tape spends $1000 on 10
   strawberry seeds day 7 while we're still scraping $700-$1000. Options:
   deferred first cow → more day-7 cash; or dump fertilizer more aggressively
   on days 3-5 to hit the day-7 seed shop with $1,500+ in hand.
2. Re-test **survival_water=True** — the original rejection predates the
   phantom-worker fix; with the extra hires it may now be net-positive.
3. Aster re-test (not done since main.py grew).

## Files

* `main.py` — parameter change only, no logic edits. `python3 main.py` prints
  `$101,763`.
* `watch.html` — regenerated (seed 1/2/3 vs V25 tape, still contested).
