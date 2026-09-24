# SESSION 33 — Randomization experiment + meta-line refinements

## The randomization question you raised

> "Why can't ours be a random tape? Like never staying the same always changing?
>  That would avoid the meta stealing."

**Tested the hypothesis rigorously.**  Built a POOL of 6 validated-safe opening
param sets (each ≥$94k solo N=20), then a `RandomAgent` that picks one per game.

Results (40 games per opponent):

| opponent type | fixed | randomized | Δ |
|---------------|-------|------------|---|
| **fixed-vs-clone-of-us** (self-mirror) | $0 margin | **+$502 margin** | +$502 |
| **mirror archetype** (adaptive v2 bot) | +$38,834 | +$40,431 | +$1,597 |
| **meta-line bots** (broker_bea etc.) | -$43,852 | **-$55,244** | **-$11,392** |

**The finding: randomization helps against ADAPTIVE opponents who observe
us and could copy our build, but HURTS against pre-compiled tapes that
ignore us entirely.**

Meta-line bots run a fixed 720-turn pre-compiled route — they don't observe
our opening or adapt to it.  Randomizing our params only makes us pick
suboptimal openings sometimes.

**Verdict: randomization is a defensive move against future copycats but
loses money against today's meta-line ladder.**  Not shipping the pool-based
random.  BUT — the code is written and tested; if the ladder shifts toward
adaptive opponents we can enable it in one param flip.

## What DID work this session — three refinements

### Change 1: meta-line seed floors → 0
Was: `seed_floor_straw=200, seed_floor_melon=250` blocked us from buying
seeds when cash was tight.  Meta-line means we NEED every seed in the ground
to compete with their crop volume.

Change: when `_meta_line_opp` detected, both floors drop to 0 (was 50 for
crop-town / tape-like modes).  

Verified:
- broker_bea: -$43,852 → **-$43,165** (+$687)
- ledger_lena: -$44,329 → **-$42,925** (+$1,404)
- slotter_silas: -$44,498 → **-$43,383** (+$1,115)
- **closer_cleo: -$52,486 → -$46,718 (+$5,768!)** — biggest single win

### Change 2: meta-line slot-promotion for sells
Was: our slot-reorder only re-shuffled sells within their original slot
positions (safe: never displaces buys/hires).

Change: when meta-line detected, promote ALL SELL orders to the FRONT of
the queue.  Meta-line dumps HUGE volumes at slot 0-1 so we need to compete
at slot 0 for first-unit pricing.

Verified (extra improvement on top of Change 1):
- broker_bea: -$43,165 → **-$43,100** (+$65)
- ledger_lena: -$42,925 → **-$42,858** (+$67)
- slotter_silas: -$43,383 → **-$43,099** (+$284)
- closer_cleo: -$46,718 → **-$46,207** (+$511)

### Change 3: (from labor analysis)
Diagnosed our workers PASS 1888 times per game vs Bea's 388.  We have IDLE
labor days 0-8 (27-71% PASS) and late-game (42-52% PASS).  Bea does WATER
851 vs our 307, FERTILIZE 107 vs our 15.  She's using her workers more
efficiently.

Tested seed-heavy openings, more mid-game hires, more geese, egg-holds,
fert-timing tweaks — all HURT vs meta.  Our labor allocator is already
maximizing what it can with the crops we have.  The gap requires MORE SEEDS
in the ground earlier — which is exactly what Change 1 (floors=0) enables.

## Measured impact — full head-to-head

| opponent | before this session | after (SHIPPED) | Δ margin |
|----------|--------------------|-----------------|----------|
| **broker_bea** | -$43,852 | **-$43,100** | +$752 |
| **ledger_lena** | -$44,329 | **-$42,858** | +$1,471 |
| **slotter_silas** | -$44,498 | **-$43,099** | +$1,399 |
| **closer_cleo** | -$52,486 | **-$46,207** | **+$6,279** |
| sheepbot | +$44,433 | +$44,433 | 0 |
| goosebot | +$59,765 | +$59,765 | 0 |
| mirror | +$38,834 | +$38,834 | 0 |
| cropbot | +$55,011 | +$55,011 | 0 |
| cowbot | +$29,232 | +$29,232 | 0 |

**Zero regression on any archetype.**  Total gain across meta-line: +$9,901
this session ($2.4k avg per meta bot).

## Ideas tested and rejected

- **`RandomOpeningAgent` (pool of 6)**: -$11k vs meta, tiny +$0.5k vs
  self-mirror.  Only ships if ladder shifts to adaptive opponents.
- **Lookahead simulator at game start**: 8s for full lookahead, picked
  worse opener 2/2 times vs meta (they don't respond to opening variation)
- **`HarvestPredictAgent`** — sell when opp crops at max_yield: -$6k meta
  (too early = wastes our small-volume advantage)
- **`FrontRunAgent`** with hard-coded Bea dump days: neutral (shed usually
  empty at "front-run" moments)
- **`fert_early_day=10`**: solo -$471, meta -$3.5k (bad trade)
- **`melon_rebuy=6`, `straw_rebuy=6`**: hurt meta $2-4k each
- **`plant_max=64/72`**: no effect
- **Bigger sheep herd for wool dominance**: crashes wool market $5k
- **Grow more geese**: solo -$16k

## Cumulative project totals (start of session 25 → now)

| opp | pre-25 | now | project Δ |
|-----|--------|-----|-----------|
| **broker_bea** | -$87,541 (tape) | **-$43,100** | **+$44,441** |
| **ledger_lena** | (untested) | **-$42,858** | -- |
| **slotter_silas** | (untested) | **-$43,099** | -- |
| **closer_cleo** | (untested) | **-$46,207** | -- |
| mirror | +$15,582 | +$38,834 | +$23,252 |
| sheepbot | +$17,093 | +$44,433 | +$27,340 |
| goosebot | +$45,097 | +$59,765 | +$14,668 |
| cropbot | +$47,746 | +$55,011 | +$7,265 |
| cowbot | +$20,566 | +$29,232 | +$8,666 |
| SOLO N=20 | $97,641 | $103,582 | +$5,941 |
| SOLO N=40 MIN | $33,342 | $75,067 | **+$41,725 floor** |

**We've cut the meta-line gap by 50%** (-$87k → -$43k) while keeping
"never uses pre-compiled routes" intact.

## Why the randomization idea works in theory but not now

The randomization was RIGHT for the case where opponents observe and adapt
to us.  On the current ladder:
- Meta-line bots are FIXED — they run `_TRACE` and never observe us
- Authored bots (fallow_finn ... rancher_rita) are FIXED
- Only truly-adaptive opponents (mirror, sheepbot) exist among our test set

So randomization defends against a threat that doesn't exist YET.  If the
ladder later shifts toward bots that inspect our public state and counter,
we flip one param to enable `RandomOpeningAgent` and defend automatically.

## Files

- `main.py` (1963 lines): +8 lines (meta-line seed_floors=0 + slot-first
  promote).  `python3 main.py` → $105,120 on seed 1.
- `watch.html` — regenerated (seeds 1/2/3 vs V25 tape).
- No new persistent data added (Kaggle downloads went to /tmp and cleaned).
