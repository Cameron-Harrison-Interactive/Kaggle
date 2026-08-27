# Session 59 — User Feedback Investigation (NO SHIP, ready pending your OK)

## User's observations (both confirmed correct)

### 1. "Putting animals way too late for them to be profitable"

**Data confirming this** — animal count over time, seed 1 vs BT:

| day | us (v10.5 shipped) | BT |
|---|---:|---:|
| D1 | 0 | 4 |
| D5 | 0 | 5 |
| D8 | 1 | 9 |
| D12 | 2 | 14 |
| D14 | 8 | 14 |
| D18 | 16 | 14 |

BT has full herd by D12. We hit full herd by D18 — **6 days later**.
Cow produces every 2 days at $160. 6 days lost × 3 productions/period × 5 cows = **~$24k lost** just from cow-purchase delay.

**Root cause**: our `_can_feed_one_more()` blocks animal buys when wheat_shed=0. BT buys animals D0 AND buys wheat from market same turn — animals feed immediately.

### 2. "Aren't using a lot of the field when we could be"

**Data**: our board seed 1 at end had **44 empty tiles** out of ~54 unlocked.

| day | plants | empty tiles (unlocked, plantable) |
|---|---:|---:|
| D3 | 30 | 0 |
| D12 | 27 | 25 |
| D18 | 14 | 31 |
| D24 | 8 | 38 |
| D30 | 8 | 41 |

D15 breakdown showed:
- NW rows 0-2: **empty** (13 wheat tiles unused) — closest to shed!
- NE rows 0-2: planted (melon + straw + wheat)
- SW rows 5-6: planted (straw + melon)  
- SW rows 7-9: **empty** (15 wheat tiles unused)

**Root cause**: Once herd of 16 animals established, hands spend nearly all their time on FEED/CARE/HARVEST_ANIMAL/COLLECT_FERT (all in NW rows 3-4). PLANT priority 40 loses to WATER 60/80, HARVEST_ANIMAL 65, FEED 90. Wheat plant tasks queued but starved.

## Fix implemented (v10.8, in agent/custom/, NOT shipped)

### A. D0-D1 animal bootstrap
Buy 2 sheep + 2 cow + 12 wheat product on D0H1, mirror of BT's opening.
Delay NE land purchase to D2 (freeing $1000 for animals).

### B. Fallback animal placement
When shed has an animal but the pasture "wants" a different type, place what we have. Was: wait forever. Now: place any animal that fits.

## Results (v10.8 vs previously shipped v10.5)

Solo:
- v10.5: $80,007 avg
- **v10.8: $84,644 avg** (+$4.6k, +5.8%)

H2H (12-seed × 2-seat = 24 games per opp):

| opponent | v10.5 shipped | v10.7 (S58) | **v10.8 now** | v10.8 improvement |
|---|---:|---:|---:|---:|
| BT | -$87k | -$79k | **-$72,720** | +$14k |
| V41 | -$115k | -$111k | **-$66,304** | **+$49k** |
| moon | -$89k | -$88k | **-$80,462** | +$8.5k |
| soil | -$115k | -$112k | **-$66,374** | **+$49k** |
| amey | -$89k | -$88k | -$80,462 | +$8.5k |
| multiroute | -$89k | -$88k | -$76,169 | +$13k |

**V41 and soil (our worst matchups) gained $49k each.** Because we now compete in early markets instead of ceding them.

Animal count seed 1 (v10.8):
- D1: 4 (matches BT)
- D6: 8 (was 1)
- D12: 15 (was 2)

## What's still wasted (open work)

**44 empty tiles late-game** still not fixed. Getting them planted requires either:
1. More hands (11+ hires/day — but fib cost prohibitive)
2. Region-specialized hands (tested multiple times, all hurt)
3. Reduce herd to free hands (loses animal income)
4. Dynamic PLANT priority boost (tested, hurts because it steals hands from HARVEST_ANIMAL)

None easy. Would need architectural change (e.g., "farmer stays in NW, hands rotate to SW").

## Progression summary

| session | solo | H2H BT | notes |
|---|---:|---:|---|
| S47 v2 | $22,278 | -$131k | scratch |
| S55 v10 | $80,007 | -$87k | shipped, scored 571 initial |
| S57 v10.5 | $80,007 | -$87k | **shipped, currently on ladder** (score ~2192 stable?) |
| S58 v10.7 | $80,113 | -$79k | dev only |
| **S59 v10.8** | **$84,644** | **-$72k** | **dev, ready pending your OK** |

Total: -$131k → **-$72k** (+$59k over 12 sessions).

## Ready to ship?

v10.8 significantly better than v10.5 on all measures. But:
- We have 1 daily submission left today
- Kaggle takes 12-24h for score to stabilize
- 0/12 wins vs top-tier means real ladder ELO likely 2000-2500 range (not top 5 yet)

Your call — ship or continue tuning? I have ideas for the field-utilization issue but they'll take multiple experiments to find one that works.
