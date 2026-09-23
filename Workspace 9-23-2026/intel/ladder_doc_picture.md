# Whole-ladder picture from the daily Replays Doc

Source: [georgymamarin/kaggriculture-episodes](https://www.kaggle.com/datasets/georgymamarin/kaggriculture-episodes), rebuilt 2026-09-17 01:01 UTC. Live report: [What 2600+ Farms Do Differently](https://www.kaggle.com/code/georgymamarin/kaggriculture-what-2600-farms-do-differently) (v118, data through Sep 16 22:28 UTC).

The searchable file is `episode_features.csv`: **148,112 episodes, 296,224 seats**. One row per (game, seat): what they planted all season, when they bought land, peak crew, and the min/max of every price. Shops are not a column — they show up as whether strawberry stayed at base or crashed to $1.

Our v41 games are **not in it yet** (crawl lag). Harrison Interactive is not on the named 9,160-team snapshot. This is the rest of the ladder, Sep 10–15, engine 1.32.7: **27,681 public games**.

## The field is one factory

Sep 10–15 winners:

| thing | share of winners |
|---|---|
| exactly **33 strawberries** planted | **93.5%** |
| 30–36 strawberries | 97% |
| exactly **12 melons** | 97% |
| **0 tomatoes** | 90% |
| land on **day 6** | **99%** |
| crew 11 or 12 | 90% |
| exact clone 163 wheat / 31 carrot / 12 melon / 33 berry / 0 tomato / land d6 | 56% |

Georgy’s takeaway the same morning: record is **keiz 214,959**, crew 12, land day 6, wheat lead. Median win **$92k**. Record is 2.3× median.

Plant mix does **not** separate $70k from $150k. Clone winners median $97k / p90 $134k. Non-clone 120k+ winners still plant 33 berries. DSM (3k rating, 292 games) is the clone. Tomato is a 10-tile add-on after 33, never instead — 522 of the 120k+ winners used it.

## What actually separates a big bank

Among winners who planted the same 33 berries:

| strawberry **min** price in the game | median bank | games |
|---|---|---|
| crashed to **$1** | **$86k** | 14,650 |
| $5–80 | $103k | 2,951 |
| $80–119 | $110k | 1,312 |
| held at **$120** (base) | **$117k** | 5,750 |

150k+ seats (1,022 of them): strawberry min median **$120**, max $235. 60–90k seats: strawberry min median **$1**.

The shop picture from 27k games, without parsing JSON: **shops either ate the factory and straw never left $120, or they didn’t and both 33-bots dumped it to $1.** Same plants. Thirty thousand dollars.

Daily_stats (winner p90): Sep 10 $131k → Sep 14 $138k. Clone share of winners 46% → 67% then back to 53%. The meta is not moving off 33 berries.

## Top of the rating board (named snapshot)

Majkel 3181, SpaTaro 3068, Sida Zuo 3061, M&M&P&Q 3049, DSM 3044. Crawl only has a handful of their games. SpaTaro is the one odd land: **day 1–2**. Orbital plants ~40 berries. Mother-Goose ~36 berries, crew 13. Everyone else is 33 / land 6 / crew 11–12.

## What this says we should build

1. **33 berries is the ladder, not a shop fork.** 93% of winners. Our 8/16 caps vs 0–1 berry shops are fighting the whole field. The 86k vs 117k split is whether straw holds, not whether you plant 33.

2. **$120 is alive.** Base strawberry is $120. Games that hold $120 are the 117k band. R90 shrinks us when they have 30+ and straw < **$160**. Stefano’s $151 and every 150k game’s $120 both look “dead” to that gate. They are not. Dead is $1.

3. **Do not plant tomatoes instead of the factory.** 90% of winners plant zero. The 120k tomato users still planted 33 berries, then ~10 tomatoes.

4. **Land day 6 / 12 melon / carrot fill is the clone.** 99% land d6. We already know forcing NE d7 vs pass loses yarn H2H. Do not restack that. The clone hits d6 because it never bought two geese.

5. **The sell/shop-tick drain is the $30k lever**, not a new crop. Same 33 tiles: straw holds $120 → $117k, straw hits $1 → $86k. 87 already sells on shop hours. The miss vs Stefano was shrinking the factory, not missing pizza tomatoes.

Do not restack: 0-shop always-33 (R112h +0 vs pass), opp≥8→33 (R120b 6–2 vs 65), 8 cows no shop, early-NE, NW berries plant-only.

Files used (in `/tmp/ladder_doc`, not copied into the workspace — 65 MB): `episode_features.csv`, `episodes.csv`, `teams.csv`, `daily_stats.csv`.
