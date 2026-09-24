# WHY WE LOSE TO TETSU — THE NUMBERS (R40 analysis, 09-14)

Match: astra_live20_5 (v25) vs nb3_tetsu_r5, seed 42. Final: **$23,579 vs $113,620 (−$90,041)**.
Same crew (13-14), same herd (17), same land (3 quads), same strb standing at peak (33).
The loss is a REVENUE CONVERSION gap, not an asset gap.

## 1. Revenue by good — the whole story

| good | us (units, $) | tetsu (units, $) | gap |
|---|---|---|---|
| WOOL | 60u, $14,178 | 266u, $62,620 | **−$48,442** |
| STRAWBERRY | 74u, $5,565 | 354u, $39,539 | **−$33,974** |
| WHEAT | 78u, $3,187 | 364u, $15,872 | **−$12,685** |
| FERTILIZER | 208u, $8,573 | 355u, $18,801 | **−$10,228** |
| MELON | 93u, $8,285 | 72u, $15,612 | **−$7,327** |
| MILK | 65u, $1,918 | 333u, $7,325 | −$5,407 |
| EGG | 120u, $6,291 | — | +$6,291 |
| CARROT | 22u, $1,608 | 14u, $1,149 | +$459 |
| **TOTAL** | **$49,605** | **$160,918** | **−$111,313** |

**−$98k of the −$111k gap is three lines: wool, strawberry, milk+fert.** Same animals, same
tiles — they extract 3–5× the UNITS per asset. The mechanism (engine-verified):

- **Strawberry**: 4 production ticks (plant+10/12/14/16). A tick produces 1 unit IF watered
  that day, **3 units if watered AND fertilized**. Tetsu waters daily + ferts every tick:
  33 tiles → 354 units (10.7/tile). We survival-water (every other day): 74 units (2.2/tile).
  We hit ~25% of possible ticks and ~0% of the fert bonus.
- **Wool/milk (care bonus)**: caring on a fed day banks +1 unit for the next production.
  Tetsu cares daily: sheep 266u (2.2/tick), cows 333u. We don't run care (measured loser at
  our staffing): 60u and 65u (0.6/tick).
- **FERTILIZER**: we SELL 208u at ~$41. Applied to a strb tick the same unit is worth
  **+$240–500** (2 extra units × $120–250). We are selling dollar bills for quarters.

## 2. The cash-gap curve — when it opens

| day | us | tetsu | gap |
|---|---|---|---|
| 5 | $446 | $237 | +209 |
| 10 | $152 | $15,896 | **−15,744** ← their melon dump lands (72u @ ~$217 avg) |
| 13 | $673 | $21,788 | −21,115 ← their strb factory complete (33 standing d13; ours d19) |
| 16 | $1,535 | $37,863 | −36,328 ← wool/milk/wheat volume machine compounding |
| 22 | $7,515 | $78,054 | −70,539 |
| 29 | $23,579 | $113,620 | −90,041 |

## 3. The melon line — we sold MORE units for LESS money

Us: 93u @ $89 avg. Them: 72u @ $217. They fire the whole dump at first yield (d10, ~$250/u),
never replant. We trickle d12–16 INTO the crash they made, and then the R39 sell floor
(bug, see §5) held 17–19 units in the shed d16–22 at $60–90.

## 4. The wheat line — desk economics

They run 25–41 standing wheat all game: +$15.9k sold, −$7.9k seed/buy = **+$8k net**.
We run 10–15 standing: $3.2k sold, −$12.3k bought (214u feed at market prices) = **−$9k net**.
Their feed comes home-grown; ours comes from the market.

## 5. Bugs this analysis found (fix next round)

1. **SELL FLOOR HOSTAGE (R39 bug)**: melon price <$100 after THEIR dump; their standing
   dropped to 0 so denial mode turned OFF; the floor then held our 17–19 melons for a
   recovery that never comes (their 60 units sit in inventory forever). Fix: the floor may
   only hold while withholding has power — inventory < anchor or actively draining; if the
   opponent's flood is already banked in inventory, DUMP (salvage beats zero).
2. **SEED PIPELINE OVERBUY (the "75 seeds in shed" tape complaint)**: pocket peaked at ~56
   seeds (d13: CAR15 MEL7 STR18 WHE16). CAR15 = pipeline argmax buys the plan never plants
   (carrot looked best at buy time; strb/melon owned the ground). Fix: per-crop pocket cap —
   never buy a crop with ≥4 in pocket that the plan hasn't planted in 2 days.
3. **FERT MISALLOCATION**: sell-fert at $41 vs +$240–500 applied to strb/milk ticks.
   Fix: fert every watered strb tick + every cow/sheep production day before ANY fert sale.

## 6. The strategic read

Our line wins the SOLO economy game (96.8k, best-ever vs v21) by spending labor on the
melon wave, NE-first expansion, and full coverage. Tetsu spends the SAME labor on tick
conversion (water every plant daily, care every animal daily, fert every tick) and converts
identical assets into 3–5× revenue. The counter is not copying them — it is capturing the
**cheap conversions first**: fert-on-tick (no extra labor, just priority), care on
production days (labor), and firing our melon dump at first yield vs melon opponents
(already shipped in v24, needs to be more aggressive).

## Ladder context (v24 episodes, from the Kaggle episode API)

| episode | opponent (elo) | score | result |
|---|---|---|---|
| 108038710 | TW_益民_li (543) | 98,276 – 65,070 | W |
| 108037690 | Ali Al-Killidar (446) | 85,476 – 21,225 | W |
| 108036656 | **Aleksander Sachuk (731)** | 49,790 – 126,503 | L |
| 108035667 | MD. AS-AID RAHMAN (611) | 54,951 – 68,524 | L |
| 108034683 | lsystudyhard (515) | 77,415 – 49,492 | W |
| 108034553 | self-play validation | — | ok |

Record 3–2, rating 600 → 638. The Sachuk loss is the tetsu shape at higher voltage
(126.5k = full-tend volume machine). The RAHMAN loss (no geese, crashed wool/melon/milk)
is §5's floor-hostage + overbuy bugs in the wild.
