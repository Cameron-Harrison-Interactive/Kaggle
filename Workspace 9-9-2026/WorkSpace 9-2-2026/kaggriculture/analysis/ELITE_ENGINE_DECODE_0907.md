# Elite Engine Decode — 09-07 late session (THE MOAT)

## Market mechanics (exact, from engine source)
- price(I) = base ± amp·f(|I−I0|), I0=10000, floor $1. BUY_PRODUCT quotes P(I−1); SELL fills at P(I) instantly.
- Sales at $1 add NO supply. Round-trip vs unchanged market nets zero.
- Town = only net buyer: each shop instance drains 1 of each product (2 if single-product shop) every 4 steps; town center drains 1 of 8 products every 24 steps. Shop unlocks are RANDOM (seeded rng, every 3 days, max 8 instances) — you adapt, you don't cause.
- Crash thresholds above I0: WOOL +6 (sq), MELON +9 (sq, NO shop buys melon), STRB +63 (linear), MILK +76 (linear), TOMATO +136 (sqrt), WHEAT ~uncrashable ($17-45 band), EGG ~$37+ (log).
- Scarcity rockets (hinge/sqrt below I0): TOMATO $531 at −493 (day 28 observed), MILK $232 at −64, WHEAT $49 at −590, CARROT $54.
- SHOP_DRAIN units/day: wheat 5/8 shop types, milk 3/8, strb 4/8, tomato 2/8, carrot 2/8, egg 2/8, wool 1/8 (×2).

## Crops/animals economics (per tile/day)
- TOMATO: $50 seed, first yield d8, 1/day, cap 4 (8 if fertilized), plant dies after; ~$108/day/tile at late prices. THE UNCONTESTED ROCKET (nobody in the 2550-meta grows it; PIZZA+FARMERS drain it all game).
- COW: $400, milk 0.5/day from d8, $80-115/day/tile at $160-230. FEED = 1 wheat per animal per ~2 days (escape at 2 consecutive unfed; production happens even unfed, only the care bonus needs fed).
- WHEAT: $18/day/tile farmed — TRAP for planners; buy it instead ($28-35), sell late ($45-49) or intraday float.
- MELON: dead (crashes +9, no shop). STRB: contested ~$101-157, ok secondary. FERTILIZE: 1 fert = 3 days double yield = +4 tomato units = +$1,300 at late prices.
- CARE on fed animal: +1 pending production unit.

## ymg_aq (2955) decoded — the 2900-class recipe
- 11W-3L vs the rest of top-10; +60k blowout of 3Jeonghoon (166,483-106,500) = days 24-29 revenue $92k vs $37k.
- Build: 8C/3S/1G (sheep starved deliberately — no YARN), W126 seeds, TOMATO 21 staggered, STRB 43, 287 hires, 2 lands.
- Wheat market-making: bought 1,123 / sold 1,361 (135 sell orders, every day from d0); float rotation + carry into the drain.
- Continuous dribble selling at drain rate; endgame liquidation days 28-29 (39k on day 29 alone).
- Money curve: all-in by d6 ($29 left), $8.7k d12, $34.8k d18, $79.5k d24, $166k end.

## v28 "HARVEST MOON" (our build, topbots/v28_harvest_moon.py) — status after session 1
- Architecture: exact price-curve market brain (drain-rate sells, wheat carry, cash-floor liquidation, endgame dump) + reactive labor planner (sticky assignment, quadrant bias, farmer=logistics / hands=field crew, animal pipeline BUILD→PICKUP→PLACE with carried-tracking, feed-sacred funding).
- Solo: $2k (first draft) → $6-23k (current, 3 seeds). Works: pipeline, feeding, tomato waves, milk d8+, endgame liquidation, weeds controlled.
- REMAINING (next session): (1) LATE FEED BUG — cows die after d23 (8→4 by d26), each dead cow = $150-250/day; (2) early cash too thin — herd completes d18 vs ymg d7; add wheat intraday float + more geese earlier; (3) walking still ~50% of actions — mower routes/zoning; (4) tomato to 22+ tiles with fert on all; (5) then H2H gates vs router/v16/ant-tape.
- NO SUBMISSIONS (per directive). Router 2550.2 stays slot A.
