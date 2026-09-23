# R53 — The Endgame Leak Report

**Date:** 2026-09-15
**What you asked for:** you watched v30 play and saw two things you didn't like —
(1) over 60 seeds and a sheep still sitting in the pouch/shed at turn 720, and
(2) crops still turning into weeds. Fix both. Score is money at the final whistle only.

**Short version:**

| What you saw | What it actually was | Status |
|---|---|---|
| 60+ seeds stranded | We were **buying seeds that could never be planted** | **FIXED** — pouch 43 → 12, +370 on the gate |
| A sheep stranded | An **install-scheduling** bug, not a buy bug | Diagnosed, **not** fixed this round (see §3) |
| Crops turning to weeds | **Spent strawberries dying of old age**, after full yield | **Not a leak** — evidence in §2 |
| Cargo left on workers | Worth ~$1,040 | Tried to fix, **measured worse** — reverted (§4) |

---

## 1. The seed leak — FIXED, and it was worse than it looked

I pointed a new probe (`war/endgame_probe.py`) at the last week of a v30 game.
Here is the end of seed 42, sampled at the end of each day:

```
 day  plants  weeds    money  seed pouch          shed
  26      64      7   66339  {'WHEAT': 15}      {'SHEEP': 1}
  27      60      7   72300  {'WHEAT': 20}      {'STRAWBERRY': 5, 'SHEEP': 1}
  28      37     23   81692  {'WHEAT': 43}      {'SHEEP': 1}      <-- +23 seeds in one day
  29       9     34   99247  {'WHEAT': 43}      {'SHEEP': 1}
```

The pouch jumps from 20 to 43 **on day 28**. That is the bug, and it is simple:
**wheat sown on day 28 first-yields on day 30 — after the horn.** Those seeds can
never pay for themselves. Worse, seeds can't be sold, only planted, so every one
of them is cash thrown away: **$430 gone, every game, for nothing.**

Both seed-buying routines worked the same wrong way — they bought against the
number of *empty and weedy tiles*, with no thought for whether there was still
time to sow them.

**The fix.** One choke point, inside `buy_order()`, so it covers every buy path at
once. Every seed buy is now capped by the crop's last plantable day and by how
fast the crew can actually plant (about 8 tiles a day):

```
last plantable day = 29 - first_yield_day
    wheat / carrot  -> day 27
    tomato          -> day 21
    melon / strawberry -> day 19
```

A buy that can't be sown in time is simply refused.

**Result:** wheat in the pouch at the whistle **43 → 12**, and the 6-seed gate
goes up on **all six** seeds — 101,312 → **101,682** (+370). Nothing else moved.

---

## 2. The weeds — measured, and mostly NOT a leak

This one surprised me, so I built a second probe (`war/weed_deaths.py`) that
watches every tile every night and classifies what happened. There are two
completely different ways a weed appears, and they need opposite fixes:

- **DEATH** — a plant becomes a weed because it went too long without water. That's a care failure.
- **SPREAD** — a weed appears on bare ground after a harvest. That's a replant-speed problem.

Here's what actually happens (seed 42 and seed 5, v30 line):

```
                        seed 42    seed 5
  DEATHS (plant->weed)      31        37
    of which RIPE            0         0     <-- important
  SPREAD (bare->weed)        2         1
  HARVEST (plant->bare)     60        61
```

Three things fall out of this:

**(a) Weeds are NOT spreading on bare ground — 1 or 2 a season.** Essentially
every weed you see on screen is a dead plant. So the fix is about watering, not
about digging faster.

**(b) Nothing is being lost.** "RIPE deaths = 0" means **not one single crop died
while it was carrying harvestable fruit.** We are never leaving a ripe crop to
rot in the field. That was the expensive failure mode and it isn't happening.

**(c) The deaths are strawberries dying of old age.** Breaking it down:

```
  DEATHS BY CROP     STRAWBERRY:29   WHEAT:1   CARROT:1
  DEATHS BY AGE      age17:23   age15:2   age14:1   age9:2   age3:3
```

A strawberry sets its four units at plant ages 10, 12, 14 and 16, then it is
finished. **29 of 31 deaths are strawberries, and 23 of those die at age 17 —
after the last unit has already been set and picked.** They are spent plants
reaching end of life in the final week, on tiles we have no time to replant
anyway. That is cosmetic, not money.

**Honest caveat:** I tried to measure the yield of every individual strawberry
plant to prove nothing was skipped, and the measurement didn't work — we pick
crops within a few hours of them ripening, so a once-a-day snapshot never sees
units sit on the plant. I am *not* claiming proof that every strawberry reaches
its full four units. What I can stand behind is (b): nothing died with fruit on it.

**Where there is still a little money:** the mid-game deaths (ages 3, 9, 14, 15 —
about 8 tiles a season) are genuine care failures during the busy middle of the
season. Each one costs a dig before the tile can be replanted. Small, but real.
Given the crew runs at 127% of capacity in the second half, this is a labour
problem, and labour reallocation is 0-for-7 in our history. I'd rather not
touch it blind.

---

## 3. The stranded sheep — real, but a different bug than it looks

Yes, a sheep sits in the shed from about day 18 to the horn. **$500 gone.**

But it is **not** a buying mistake. I read the buy code and it already does the
right things: it refuses to buy unless a genuinely free north site exists beyond
the animals already held, and it already refuses to buy a sheep after day 22
(a sheep needs 6 days to first yield, so anything later can't pay back).

So we buy it with a valid site in hand — and then **the install job never runs.**
We are carrying a $500 animal for 8–11 days while the crew is busy elsewhere.
That fits the R52 labour census exactly: demand 166 ops/day against 131 of
capacity, and installs are the job that loses that fight.

I deliberately did **not** fix this by bumping install priority. Reallocating
labour is the single most reliably negative thing we have tried in this project
(seven measured failures: R40, R51b, and others). It needs its own round with a
measurement attached, not a hopeful edit bolted onto a submission.

---

## 4. What I tried that FAILED — the final-day cargo reserve

Cargo left on workers at the horn is worth **~$1,040** (32 wheat + 2 strawberry
on seed 42). Obvious fix: reserve the last 6 hours of the final day so every
worker walks to the shed and dumps.

**It was much worse.** Seed 42 went 99,247 → 93,849 (**−5,398**) and seed 5 went
106,898 → 98,767 (**−8,131**).

Two things went wrong at once. Cutting 6 hours off 14 workers costs about 84
worker-hours of final-day harvesting, and final-day harvests are the expensive
crops — that loss alone dwarfed the cargo. And the cargo that *did* reach the
shed simply sat there unsold, because the hourly sell routine couldn't clear it
before the horn. The shed at the whistle went from nearly empty to **$7,665 of
unsold stock.**

**Reverted.** A near-free variant (dump only when a worker already happens to be
within 3 tiles of a shed) measured **exactly neutral** — no gain, no loss — so I
dropped it too rather than ship dead code. Lesson recorded: final-day harvesting
is worth far more than the cargo we fail to deliver.

---

## 5. v31 — built and validated, but NOT SUBMITTED

`submit/v31_champion.py` is packaged and fully checked:

- **Gate (6 seeds 42/5/101/202/303/777):** 99,557 / 107,248 / 103,629 / 103,592 / 106,905 / 89,162 = **101,682**, up **+370** on v30's 101,312, and up on *every* seed.
- **Self-play:** seed 5 64,644–55,585 and seed 777 64,989–43,942, both complete to turn 720. Both a shade better than v30's 64,324 / 64,639.
- **Submission audit:** imports are `math` and `collections` only; zero `open(`, zero network calls; `kaggle_entry_agent = agent` present; 116,718 bytes.
- **Packaging verified:** `submit/v31_champion.py` reproduces the dev build **exactly, delta +0, on all six seeds.**

**I could not submit it.** The sandbox lost the Kaggle credentials (installed
packages and credentials don't survive between sessions), so `kaggle` now
answers "Authentication required." The file is ready to go — either re-run
`kaggle auth login` in the sandbox, or upload `submit/v31_champion.py` by hand.

One thing to weigh before spending a slot: +370 on a ~101k score is 0.37%, and
we learned this round that **solo score is not a proxy for ladder rating** (v29
is the best solo line we have and the worst on the ladder at 519.6, against
v21's 571.0 on worse solo numbers). The honest case for submitting is not the
+370 — it's that we stop setting $430 on fire every game, which is a real
defect and can't hurt.

---

## 6. Files

| File | What it is |
|---|---|
| `submit/v31_champion.py` | **v31, ready to submit** |
| `war/astra_live20_18.py` | v31 dev source (= v30 + seed cap) |
| `war/astra_live20_15_c13.py` | v30 dev source, untouched fallback |
| `war/patch_r53.py` | builds the R53 variants |
| `war/endgame_probe.py` | last-week + final-whistle dump (found the seed leak) |
| `war/weed_deaths.py` | classifies every weed as DEATH or SPREAD (found the strawberry answer) |
| `war/astra_live20_17.py` | the failed 6-hour cargo reserve, kept as a negative record |
