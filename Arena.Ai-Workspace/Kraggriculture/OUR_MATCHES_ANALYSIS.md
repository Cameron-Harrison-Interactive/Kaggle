# Our Live Matches — Analysis (submission 55315617, v6.1)

16 episodes pulled. Record: **4 wins, 12 losses (25% win rate)**, avg $57,612
vs opponent avg $72,719. Better than before but losing to the stronger meta.

## Results
```
90681873 WIN  $91,235 vs SuroRitch ($1,890 — opponent errored)
90710595 WIN  $78,810 vs Sarvesh Talele ($3,279)
90636008 WIN  $95,554 vs enddl22 ($51,052)
90636803 WIN  $56,551 vs Rishi Gupta ($50,986)
90707389 LOSS $20,911 vs Simon Rüba ($170,458)  <- highest score seen
90635185 LOSS $41,310 vs yang20251228 ($95,835)
90629604 LOSS $64,127 vs Alejandro Betato ($99,809)
... (8 more losses, mostly $50-70k vs $80-90k opponents)
```

## Root causes of losses (decoded from replays)

1. **We never DIG weeds.** Weeds accumulate to 15-20 by late game, blocking crop
   tiles. The winning farms stay nearly weed-free.
2. **We plant too few crops (4-12 tiles) vs winners' 40-55.** Simon Rüba
   ($170k) keeps 50+ crops all game — a dual animal+CROP economy, not animals only.
3. **Feed-wheat sell bug crashed a match.** On day 15 vs Simon we SOLD 14 of our
   feed wheat (reserve too low), then couldn't feed 10 animals for 2 days → 8
   animals died. Under opponent market pressure this is fatal. Fixed in v6.3
   (reserve raised to 20 + 2/animal; winners hold 30-50 wheat).
4. **Animals die mid-game on strong-opponent matches** (12→4 after day 12).
   Mostly a consequence of #3 and hands being over-diverted to feeding.

## What the very best do differently
- **Simon Rüba ($170k, the ceiling):** 3 quads, 8c/6s like us but runs a MASSIVE
  crop operation (50-55 tiles), holds 40-50 wheat, sells huge milk (531),
  fertilizer (324), wool (344). He does NOT abandon crops for animals — he does
  both at scale. This is the blueprint to beat.
- Most strong opponents are the 3-quad 8c/6s build (same structure as us) but
  execute it more reliably (more crops, no weeds, no feed crashes).
- Seb (from earlier) is the 4-quad cow-heavy variant; higher ceiling but riskier.

## v6.3 fixes (shipped as next candidate)
- Added **DIG weeds** so tiles get cleared and replanted.
- Plant through day 26 and fill more tiles (strawberry fallback included).
- **Large wheat reserve** (20 + 2/animal) so we never sell feed wheat and
  animals don't starve under market pressure. This is the big reliability fix.
- Result: standalone test $81,300 vs starter; self-play v6.3 beats v6.1 21-4.
- `HI_AgriBot_v6.3_candidate.tar.gz`.

## Next steps to climb toward Simon's $170k
1. Scale crop count to 40+ while keeping 14 animals — needs enough hire labor
   (Simon uses 12 hands; we use up to 14 but divert them to feeding).
2. Fertilize our own crops with surplus fertilizer instead of selling it all
   (THUNDER's edge) — boosts wheat/crop yields.
3. Tune hire count so neither crops nor animals are starved of labor.
4. Pull fresh v6.3 matches after posting and confirm win rate improves.
