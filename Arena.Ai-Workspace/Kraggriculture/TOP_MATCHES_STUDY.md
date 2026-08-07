# Top Matches Study — 6 leaderboard episodes

Episodes pulled and analyzed:
- 90563851 — Chloe 94,063 vs Raj Aryan 94,034
- 90557461 — Tagir 107,091 vs Seb 109,021
- 90564660 — Raj Aryan 91,564 vs Seb 100,507
- 90566229 — Seb 89,345 vs Chloe 79,097
- 90592858 — Youssef 92,207 vs Seb 109,163
- 90615567 — THUNDER 127,661 vs Seb **139,143** (highest seen)

## Two distinct winning builds

### Build A — "Meta" (Chloe / Raj / Tagir / Youssef / THUNDER)
- 3 quadrants (NW, NE, SW), never SE. Lands day 7 + 11.
- 8 cows + 6 sheep (14 animals).
- Day 0: 5 hires, 2 cows + 2 sheep, 7 wheat seed + 12 melon seed.
- 259-277 hires total; sells 828 wheat (buys 980) OR is net wheat seller (THUNDER).
- Scores $79k–$128k. THUNDER's $128k edge = net wheat seller (264 bought),
  more wheat seed, less fertilizer sold (kept for crops), fewer hires.

### Build B — "Seb" (the consistent #1)
- **4 quadrants (buys SE!)** — lands **day 4, day 6, day 10** (aggressive early).
- **Cow-heavy: 13–14 cows + 7 sheep (20 animals)**.
- Day 0: **7 hires**, 2 cows, 14 wheat seed + 3 melon seed; buys sheep on hour 2.
- Buys wheat for feed (~18/day late), sells little wheat; cows are the engine.
- Sells huge milk (298-346) + fertilizer (298-333).
- 303-309 hires (more labor).
- Ends with ~45 weeds (abandons crops late, pure animal economy).
- Scores $89k–$139k; **beats Build A in every head-to-head**.

### Seb's exact schedule (from 90615567, $139k)
- Day 0: 7 hires, 2 cows (h1), 2 sheep + 2 wheat seed (h2); 12 wheat seed, 3 melon.
- +1 cow days 1, 3, 4; NE bought day 4 h22.
- SW bought day 6 h6.
- Strawberry/melon seed waves days 5, 7, 8.
- +2 cows + 2 sheep day 9; +2 cows + 2 sheep day 10 (SE bought h17);
  +2 cows + 1 sheep day 11; +2 cows day 13 → **13 cows / 7 sheep final**.
- 12 hands/day after expansion; 0 hires on final day 29.

## What this means for our bot

**Our v6.1 (Build A) is the safe ship:** 3-quad, 8c/6s, mean ~$78k vs starter
(min $48k, max $94k). It reliably beats our old 69k champion.

**v6.2 (Build B / Seb-style) is the upside play but not yet reliable:** 4-quad,
13c/7s, lands day 4/6/10. It hits $90-96k on good seeds but crashes to $29-33k
when animals die during the rapid 4-quad expansion (feeding at 14-20 animals
with only 11 hands fails on some seeds). It is saved as `main_v6.py` for
continued work; `main.py` is the stable v6.1.

## Path to beat Seb (the real goal: ~$140k+, then push higher)

1. **Fix feeding at scale.** With 16-20 animals we need either more hands on
   feed duty during expansion days (9-13) or better multi-wheat carrying so one
   hand can feed several animals per trip. Target: 0 animal deaths on every seed.
2. **Cow-heavy mix.** Cows (milk $160/2 days) out-earn sheep; Seb runs ~2:1
   cows:sheep. Our 8/6 is too sheep-heavy.
3. **Earlier, all-4 land.** Buying NE day 4 / SW day 6 / SE day 10 gives more
   pasture room earlier and more fertilizer/milk. Requires the day-0 cash buffer.
4. **Don't overbuy wheat late** — stop feed purchases on day 29 (Seb hires 0
   and buys 0 wheat on the final day; every coin should be in the bank).
5. **Net wheat seller** (THUNDER's edge): grow feed, batch-sell surplus,
   fertilize own crops — potentially +$10-20k.
6. Note on the "$300k" goal: observed top scores are ~$139k. In-game gold is
   opponent-dependent (shared market), so beating Seb means winning head-to-head
   matchups and climbing the Bradley-Terry rating, not raw gold.
