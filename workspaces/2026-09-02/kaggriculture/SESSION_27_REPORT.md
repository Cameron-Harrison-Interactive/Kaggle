# SESSION 27 — Price-momentum dump + melon hold-until

**Head-to-head margins UP $5-6k against every reactive opponent (mirror, sheepbot,
goosebot).  Mirror goes 17W → 20W (perfect).  V25 tape margin closes by $5k for
the first time this project (-$87.5k → -$82.6k).**

Two changes:

1. **Price-momentum dump** (`momentum_drop_pct: 0.04`) — every 4 hours, check
   if any product's price has DROPPED 4%+ below its 5-day rolling max.  If
   yes, an opponent is flooding that product's market and its price is about
   to crash further.  Dump our stock RIGHT NOW instead of waiting for the
   once-a-day hour-21 sale.
2. **Melon hold-until** (`hold_melon_until: 15`) — melon price rises ~5% from
   day 10 → 15 as town shops eat the first few units.  Holding early stock
   until day 15 nets **+$181 on 60 seeds — 60/60 wins**.

---

## PART 1 — the momentum dump

### Discovery

Traced sell prices in a same-seed vs-tape game (seed 1) — spotted that
WOOL/FERTILIZER/MELON crash to $1-24 mid-game because the tape sells 132 wool
/ 245 fert / 114 melon over ~30 days:

```
day  WOOL_price  our_action
 11    $209      D11H21 SELL 8u @$209   ($1,672)
 14     $24      D14H21 SELL 8u @$24    ($192)    <-- tape crashed it
 17     $11      D17H21 SELL 8u @$11    ($88)     <-- deeper crash
 20     $11      D20H21 SELL 8u @$11    ($88)
```

Our once-a-day sell at hour 21 is TOO LATE — the tape's mid-day dumps happen
within the same day and we sit on our stock earning nothing.

### The rule (encoded in `_decide_market`)

```python
mom_drop = params["momentum_drop_pct"]        # 0.04
mom_hours = (1, 5, 9, 13, 17)                 # 5 checkpoints per day
if hour in mom_hours:
    for item in ("WOOL","MELON","FERTILIZER","MILK","EGG","CARROT","TOMATO"):
        hist = self._price_history[item]      # rolling 5-day window
        if hist[-1].price < max(hist[:-1].price) * (1 - mom_drop):
            orders.append(["SELL", item, shed[item]])
```

Data source: at hour 0 each day, log the current price for every product;
keep last 5 days.  Trigger hours (1,5,9,13,17) are the "just-after-town-tick"
slots so the momentum check runs against the freshest price data.

### Why hour 1 matters (an easy trap)

First attempt put the momentum check INSIDE the existing hour==0 / hour==1
branches — which early-return after handling hires / seed buys.  The check
never fired at hour 1, so my initial numbers were only +$1.8k margin.  Moved
it to the TOP of `_decide_market` before the hour-branch dispatch → +$5.9k
margin.

Same-seed trace (seed 1 vs mirror), old logic vs new:

```
                            OLD (h=5 only)              NEW (h=1 fires)
D6:   FERT tick at H01      -> normal H05 sell $96      -> H01 sell $96 (same)
D14:  WOOL crash at H01     -> H05 sell $24 (crashed)   -> H01 sell $95 (peak!)
D17:  WOOL crash at H01     -> H05 sell $11             -> H01 sell $86
```

Same total volume sold, ~4x the revenue on the crash days.

### Measured (10 seeds × 2 seats = 20 games / opponent)

| opponent | PRE-27 | S27 (mom=0.04) | Δ margin |
|----------|--------|----------------|----------|
| tape_v25 | 0W -$87,541 | 0W **-$82,568** | **+$4,973** |
| sheepbot | 19W +$23,291 | **20W** **+$29,077** | +$5,786 |
| goosebot | 19W +$44,985 | **20W** **+$49,342** | +$4,357 |
| mirror   | 17W +$22,881 | **20W** **+$28,754** | +$5,873 |
| cropbot  | 20W +$49,986 | 20W +$50,660 | +$674 |
| cowbot   | 20W +$30,015 | 20W +$30,153 | +$138 |

Big wins on the "reactive" opponents (mirror, sheepbot, goosebot).  Cropbot
and cowbot were already 20W with big margins so limited room.  Even the
static tape's margin improves — we can react to its dumps a little.

### Solo verification (60 seeds vs PASS)

BASELINE $98,829 → shipped $98,829 — **exactly neutral**.  No opponent → no
downtrends to detect → the trigger never fires.  Pure counter tool.

### Drop threshold sweep (mirror match)

| momentum_drop_pct | margin vs mirror |
|-------------------|------------------|
| 0.02 | +$28,369 |
| 0.03 | +$28,181 |
| **0.04 (SHIPPED)** | **+$28,754** |
| 0.05 | +$28,504 |
| 0.06 | +$28,449 |
| 0.08 | +$26,202 |

Peak at 0.04.  Below it we react to noise; above it we miss real crashes.

---

## PART 2 — melon hold-until (small but perfect)

Same principle as strawberry hold: melon price rises slightly ($256 → $272
day 10-15) because town shops eat the small early harvest faster than we
produce.  Holding early stock nets +$181 on 60 seeds — **60/60 wins**.

| hold_melon_until | avg / 60 seeds | wins |
|------------------|----------------|------|
| 0 (baseline)     | $98,829 | 0/60 |
| 12               | $98,937 | 60/60 |
| 13               | $98,961 | 60/60 |
| 14               | $98,985 | 60/60 |
| **15 (SHIPPED)** | **$99,010** | **60/60** |
| 16               | $99,010 | 59/60 |
| 17               | $98,720 | 29/60 |

Peak at 15.  Beyond 15 the shed starts to fill from mid-game melon
plantations and the hold starts costing us.

## Solo progression (all vs PASS)

| session | 20-seed avg | seed 1 |
|---------|-------------|--------|
| Start of 25 | $97,641 | $97,976 |
| 25 (ramp + sell_hour=21) | $101,878 | $103,212 |
| 26 (mel=10 + straw-hold) | $105,482 | $108,078 |
| **27 (mom-dump + melon-hold)** | **$105,444** | **$108,165** |

Solo ~unchanged (momentum is a no-op vs PASS).  All the value shows up in the
head-to-head numbers.

## What we tried and rejected this session

- **Bargain-buy WHEAT/FERTILIZER when price crashes** (`BuyLowAgent`
  wrapper): the wheat we bought went into our normal sell loop and got
  dumped at low prices too.  Net neutral to slightly negative.  Skipped.
- **Hold MILK / EGG / FERTILIZER**: shed cap 100 overflows in ~15 days.
  MILK hold=15 costs -$5.7k, hold=22 costs -$44k, FERT hold=15 costs -$47k.
  Only strawberry and melon have the small volume + rising curve combo.

## Files

- `main.py` (1739 lines): +2 params + 40 lines of momentum-dump + melon-hold.
  `python3 main.py` prints `$108,165`.
- `watch.html` — regenerated (seeds 1/2/3 vs V25 tape).
