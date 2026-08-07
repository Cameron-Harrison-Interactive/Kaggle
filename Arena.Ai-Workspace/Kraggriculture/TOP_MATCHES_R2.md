# Top Matches Round 2 — Findings (2026-08-07)

6 more top episodes pulled (submissions 55312591 = Wufang Hong, 55319673 =
sleepyai.org). Winners:
- 90697169: sleepyai $141,870 over venks $141,686 (highest seen)
- 90710026: Wufang Hong $132,963 over Youssef $131,123
- 90689237: Wufang Hong $116,853 over venks $113,042
- plus 3 more sleepyai wins ($81k-$110k).

## Confirmed meta
ALL winners run 8 cows + 6 sheep, 3 quadrants (NW/NE/SW, never SE), land day 7 +
11. Same day-0 opening (5 hires, 2 cow + 2 sheep, 7 wheat seed + 12 melon seed,
5 wheat). Same crop/animal layout. The top is solved around this structure; the
margins are tiny ($141,870 vs $141,686 = $184 difference).

## Nosiru's two observations — both correct
1. **Alternating/column watering:** crop workers don't all chase the same plant.
   Each sweeps a column (e.g. sleepyai's h4 works cols 0-3, h5 cols 2-4, h6 cols
   0-4) watering up/down. We implemented per-turn target-claiming in v6.4 so
   hands pick distinct water/harvest tiles.
2. **Dedicated animal labor:** the winners split units — farmer + hands 0-3 are
   animal tenders (feed/care/collect), hands 4-6 are crop workers. Animals live
   in a compact 2-row corridor around the shed so a tender sweeps through them.
   (Not a single straight line to the fence, but the zone idea is right.)

## Critical benchmarking lesson
v6.4 with crop-job-claiming scored $93k vs the **starter** bot (up from $80k),
but LOST 0-15 in self-play vs v6.3 and collapsed to 2 animals under shared-market
competition. The starter is a passive benchmark that doesn't compete for wheat;
high scores against it are misleading. **Head-to-head self-play is the real
test.** v6.3 (robust opportunistic feeding + weed digging + large wheat reserve)
beats v6.4 ~57% in self-play and is the safer, stronger ship.

## Shipped: v6.3
- Standalone $83.5k vs starter; robust in self-play.
- DIG weeds, plant through day 26, large wheat reserve (20 + 2/animal).
- Beats v6.1 in self-play 21-4.

## Next ideas to beat the $141k ceiling (margins are tiny now)
1. Dedicated tender count: try 3-4 dedicated animal hands + 3 crop hands
   (matching sleepyai) instead of fully opportunistic — but make sure crop hands
   still feed on-tile so animals don't starve.
2. Crop-claiming gated on "enough tenders are already feeding" so we get the
   anti-double-water benefit without losing feed coverage.
3. Fertilize own crops with surplus fertilizer (THUNDER/Simon edge) instead of
   selling every unit — boosts melon/wheat yields.
4. Tune the late game: stop buying wheat on day 29, sell everything, ensure
   shed empty (unsold = $0).
5. Pull v6.3 live matches and measure the REAL win rate; iterate from there.
