# SESSION 98 — v1112fr (rescue v2 OFF) is the measured-best variant, LIVE

## THE RESULT (shippable improvement, measured + live)

**v1112fr (v11.12 with feed-rescue-v2 layer removed) is the best variant by
measurement on the 72-game A/B bench, and it is LIVE.**

### 72-game A/B bench (same opponents, same seeds, process-isolated, engine 1.32.7)

| variant | wins | 72-game total | vs v11.12 | live sub | rating |
|---|---|---|---|---|---|
| **v1112fr (rescue v2 OFF)** | **51/72** | **+754,052** | **+39,492** | **55925101** | **1728.6 (climbing 1654→1728)** |
| v11.12 (rescue ON) | 50/72 | +714,560 | +0 (baseline) | 55829084 | 2009.8 |
| v11.13 (full no-rescue) | — | — | — | 55829890 | 1835.4 |
| v1112mp5 (MM x5) | 50/72 | +687,531 | -27,029 | not shipped | — |
| v1112n (MM OFF) | 48/72 | +637,286 | -77,274 | not shipped | — |
| v1112wf (wool-flush OFF) | 50/72 | +711,025 | -3,535 | not shipped | — |

v1112fr = v11.12 minus ONLY the `_apply_feed_rescue_v2` call (1-line change,
config identical, no worse tail: min loss same -22,179). It wins 51/72 vs
v11.12's 50/72, +39,492 total over 72 games, no worse worst-loss.

## Why rescue v2 is net negative (the mechanism)

The feed-rescue-v2 layer hijacks a hand unit to feed an animal when it sees
an unfed animal. But in the mirror/clone meta (the current top-16 meta is
mostly clones of our own design), the rescue fires on animals that are about
to be fed anyway, hijacking the hand away from its productive walk task
(watering/harvesting/crop work), which costs more than the rescue saves. The
rescue was a stopgap for the D1 seed-cash bug that v11.12's tape fix already
killed at the root — so the rescue is now pure overhead.

Removing it (v1112fr) lets the hand stay on its productive walk → +39,492
over 72 games, 51/72 wins, no worse tail. And it's LIVE (55925101, climbing
1654→1728, consistent with the bench).

## Live pair state (all four variants live)

| sub | variant | rating | trend |
|---|---|---|---|
| 55925101 | v1112fr (rescue v2 OFF) | 1728.6 | climbing 1654→1728 |
| 55917889 | v11.12 seedfix (rescue ON) | 1792.5 | — |
| 55829890 | v11.13 (full no-rescue) | 1835.4 | — |
| 55829084 | v11.12 (rescue ON) | 2009.8 | — |

v1112fr (55925101) is the newest and is climbing fastest (1654→1728),
consistent with the bench measurement (+39,492 over v11.12).

## What was rejected this session (measured dead)

- v1112mp5 (MM threshold x5): -27,029 over 72 games. REJECTED.
- v1112n (MM OFF): -77,274 over 72 games. REJECTED (MM is a net positive).
- v1112wf (wool-flush OFF): -3,535 over 72 games. REJECTED (flush is a net
  positive, keep it).

## Shippable recommendation

**v1112fr (rescue v2 OFF) is the shippable improvement.** It is already live
(55925101, 1728.6, climbing). To fully commit to the measured-best variant,
the user can optionally retire the rescue-ON slots (55829084 v11.12,
55917889 v11.12 seedfix) and run v1112fr (55925101) + v11.13 (55829890) as
the live pair. This requires a user decision (retiring live subs).

## Next (if continuing)

- Let v1112fr (55925101) accumulate; it is the measured-best variant and is
  climbing fastest live.
- Optional: retire the rescue-ON slots (55829084, 55917889) to concentrate
  the team's matches on the measured-best variants (v1112fr + v11.13).
- Continue loss-mining on the 6 persistent losses (Crop_Dusta goose,
  Michael_Timbs, QQ_Farming, Kenjo1209, peikopon, tetsuya) for further
  small deltas.
