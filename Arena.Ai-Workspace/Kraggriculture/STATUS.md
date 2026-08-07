# Kraggriculture — Workspace Status

**Last updated:** 2026-08-06
**Competition:** Kaggriculture (Kaggle Featured Simulation) — $50k prize pool
**URL:** https://www.kaggle.com/competitions/kaggriculture/overview
**Team:** Nosiru

## Active bot: v6.1 "Dairy Baron"

Our own animal-first agent, built from decoding the top leaderboard meta
(Chloe, Raj Aryan, and the $137k player). Source: `Agent/main_v6.py`
(= `Agent/main.py`), config `Agent/dna_v6.json` (= `dna.json`).

**Local scores (10 seeds vs starter): mean $80,378 / median $80,096 / min $66,833 / max $88,396.**
This beats our previous best (v5.8z5f = 69,203 gold) in 9 of 10 seeds.

### Strategy
- 8 cows + 6 sheep target on a compact pasture corridor around the shed.
- NW start; buy NE day 7, SW day 11; never SE.
- Day-0 opening: 5 hires, 2 cows + 2 sheep, 7 wheat seed + 12 melon seed, 5 wheat.
- Animal ramp: +1 cow d3, +1 cow d5, +2 cow/+2 sheep d7, +2 cow d9, +2 sheep d11.
- **Opportunistic distributed feeding**: every hand carries wheat and FEEDs any
  unfed animal it reaches; per-turn target-claiming prevents hands piling on
  one animal. No single dedicated tender (this is how the top bots keep all
  14 alive).
- Farmer + hand 0 build pastures and place animals during opening.
- Daily sales of milk, wool, fertilizer (keep 2), melon, strawberry, surplus wheat.

### Still to improve
1. Some seeds lose a few animals on the day-11 expansion (12→13 vs target 14).
2. Late-game cash-out: ensure all products sold and no over-buying wheat on day 29.
3. The THUNDER/$137k edge: become a net wheat seller (grow own feed, batch-sell
   surplus day 5), use more fertilizer on own crops, trim expensive fib hires.
4. Synchronized fertilizer-boosted melon/strawberry waves.
5. Test against stronger opponents than starter (self-play, replay-derived bots).

## Reference analysis
- `TOP2_DECODE.md` — Chloe ($94k) vs Raj Aryan ($94k) full blueprint.
- `TWO_WINNING_BUILDS.md` — two top matches compared; the $137k winner's wheat
  engine is the biggest remaining margin opportunity.

Replays can be re-pulled (CLI authenticated):
`kaggle competitions replay <EPISODE_ID> -p replays`

## Files
```
Kraggriculture/
├── Agent/
│   ├── main.py                     # active v6.1 (copy of main_v6.py)
│   ├── main_v6.py                  # v6.1 Dairy Baron source
│   ├── main_v5.8z5f_brainoff_69203.py  # prior best, fallback reference
│   ├── dna.json / dna_v6.json      # v6.1 config
│   └── HI_Market_Brain.pkl         # unused by v6
├── Data/last_package.txt
├── Scripts/ (package_bot, watch_match, auto_evolve, evolution, train_brain)
├── HI_AgriBot_v6.1_candidate.tar.gz  # current submission package
├── HI_AgriBot_v6.0_candidate.tar.gz  # previous v6 build
├── STATUS.md
├── TOP2_DECODE.md
└── TWO_WINNING_BUILDS.md
```

## Test / package / submit
```bash
pip install -U kaggle-environments
cd Kraggriculture
python -c "
from kaggle_environments import make
env=make('kaggriculture', configuration={'episodeSteps':720,'seed':1})
env.run(['Agent/main_v6.py','starter'])
print('p0=$%.0f p1=$%.0f' % (env.state[0].reward, env.state[1].reward))"
python Scripts/package_bot.py
kaggle competitions submit kaggriculture -f HI_AgriBot_v6.1_candidate.tar.gz -m "v6.1 animal-first"
```

## Update: 6 top matches studied (2026-08-06 evening)

Pulled 5 more top episodes. Two builds exist: the 3-quad 8c/6s "meta" and
**Seb's 4-quad cow-heavy build (13c/7s, lands day 4/6/10, up to $139k)**. See
`TOP_MATCHES_STUDY.md`.

- **Active ship for tonight: v6.1** (`main.py`, `HI_AgriBot_v6.1_candidate.tar.gz`),
  mean ~$78k vs starter, min ~$48k, max ~$94k. Consistently beats the 69k champ.
- `main_v6.py` holds the in-progress v6.2 Seb-style 4-quad build (higher ceiling
  ~$96k but inconsistent due to feed failures at 16-20 animals). Do not ship
  until feeding-at-scale is fixed.
- Standalone submission verified: $77,750 vs starter when run from the tarball.

## Update: live v6.1 results + v6.3 (2026-08-07)

v6.1 went 4-12 (25%) across 16 live matches (avg $57.6k vs opp $72.7k). Decoded
losses in `OUR_MATCHES_ANALYSIS.md`: we never DIG weeds (15-20 choke the farm),
plant too few crops (4-12 vs winners' 40-55), and a feed-wheat sell bug killed
animals vs Simon Rüba ($170k ceiling).

**v6.3** fixes all three: DIG weeds, plant through day 26 / fill more tiles, and
a large wheat reserve (20 + 2/animal) so feed is never sold. Standalone test
$81.3k vs starter; beats v6.1 21-4 in self-play. Package:
`HI_AgriBot_v6.3_candidate.tar.gz` (active `Agent/main.py`).

## Update: Round 2 (2026-08-07 morning)

6 more top matches studied (sleepyai $141,870 is the new ceiling). Confirmed 8c/6s
meta; the margin at the top is tiny. v6.4 experimented with per-turn crop-job
claiming ("alternating watering"): hit $93k vs starter but collapsed in
self-play (the starter benchmark is misleading). **Shipped v6.3** as the robust
choice (standalone $83.5k, beats v6.1 self-play 21-4, beats v6.4 self-play).
Key lesson noted in `TOP_MATCHES_R2.md`: always test head-to-head, not vs starter.
Next: dedicated tender/planter split, fertilizer-on-crops, and pull fresh live
v6.3 matches to measure real win rate.

## Update: v6.5 — crop-lane routing (2026-08-07)

Nosiru's observations were correct: v6.3 expanded without filling quadrants
(only 7-11 crops vs winners' 40-55) and early unwatered crops became weeds.
v6.5 borrows v5.8z5f's proven 2-hands-per-quadrant lane/column routing:
- 3 dedicated animal tenders (farmer + hands 1-3) + lane planters (hands 4+).
- Planters sweep assigned columns (2 lanes per quadrant) and only work in their
  quadrant, so coverage goes 7 → 30+ crops (matching v5's coverage).
- Tightened day-0 pasture layout around the shed (kills the far-animal death).
- DIG weeds; weed priority when animals are fed.
Result: mean ~$81k vs starter (min $68k, max $87k), **beats v6.3 17-3 in
self-play**, standalone $88.5k. In the v6.3 match we lost to Neo_0x3f $72.5k vs
$75k, v6.5 would have scored ~$83k. Package: HI_AgriBot_v6.5_candidate.tar.gz.

## v6.5 bug fixes + breakthrough (2026-08-07)

Nosiru's local testing found critical v6.5 bugs, all fixed:
1. Seed restock ran EVERY HOUR (day==7 had no hour gate) -> bought ~376
   strawberry seeds, burning cash. Gated all seed/wheat buys to hour 1 (wheat
   tops up later only when animals are unfed).
2. 3 permanent tenders left too few crop workers -> unwatered crops died.
   Kept 3 tenders but crop workers now HELP FEED when >=5 animals are unfed
   (expansion days), then return to lanes.
3. Day-1 unfed animals / day-12 12-unfed expansion crunch -> fixed by the
   planter feed-help and wheat top-up.
Result: **mean $97k over 40 seeds (min $82k, max $110k) vs starter**, standalone
tarball **$105,623**, **beats v6.3 18-20 in self-play**, 17 animals survive.
Package: HI_AgriBot_v6.5_candidate.tar.gz. Crop coverage is still lower than v5
during feed-heavy days (next tuning target).

## v6.5 final (2026-08-07)
Tried to fix crop-fill by making planters plant-first; this regressed animal
survival (far-pasture bug + planters pulled off feeding). Restored the best
config: 3 tenders carrying 5 wheat, planters help feed when >=5 unfed then
return to lanes. Seed/wheat buys gated to hour 1 (killed the 376-seed cash
burn). Mean $94k over 30 seeds (min $85k, max $100k), standalone $94.8k,
beats v6.3 13/20 self-play. Crop-fill after expansion is still the next target
(needs more crop workers without starving animals).
