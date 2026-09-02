# Session 48 — Custom Bot v3: Strawberry + Fertilizer (multi-session, NO SHIP)

## Where we are
- **Session 47 finished at solo $22,278 avg (5 seeds)**
- **Session 48 finishes at solo $28,962 avg (10 seeds)** — +$6,684 (30% gain)
- Ship unchanged: `main.py` md5 = `c0c74b43ea577dfb05f1e21dd0f8991b` (Session-42 breaking_tie)
- **All 11 animals alive on every seed tested. Zero errors.**

## What changed this session

### 1. Strawberry crop (SW/SE layout tiles)
- Added `STRAW` role to `plan.py`; SW rows 5-6 and SE row 5 = 18 strawberry tiles
- `desired_crop_for` returns STRAWBERRY for STRAW tiles
- Priority 78 (high) so we plant strawberry as soon as land unlocks
- Economy buys strawberry seeds up to 3/turn at $100 each
- Strawberry sells continuously as it comes in (price rises over game)

### 2. Fertilization loop
- New `FertilizeTask` (priority 88 — beats HARVEST, loses to FEED)
- Fires when strawberry/tomato is 1 day before OR on a production day
- Doubles yield: 4 → 8 units per plant with 4 fertilizations
- `required_items = {"FERTILIZER": 1}` so executor auto-detours to shed for pickup
- Economy keeps `fert_reserve = min(12, n_straw_tiles)` on hand

### 3. Wheat reserve raised to 10 days
- Was `current_herd * 7`, now `current_herd * 10`
- Fixes the D20-D21 starvation cliff seen in Session 47 seed 3
- All 5 test seeds now retain all 11 animals through D30

### 4. Rebuy-starving-animal cooldown
- New `starving_market` flag blocks animal purchases when `wheat_shed < planned_herd * 3 and day >= 5`
- Prevents wasteful $500 sheep buys during a wheat dip

## Ablation this session (documented failures)

| change | avg | delta |
|---|---:|---:|
| baseline v2 (Session 47) | $22,278 | — |
| + strawberry crop only | $23,648 | +$1,370 |
| + fertilize task | $26,126 | +$3,848 |
| + wheat_reserve 10d + rebuy cooldown | $29,604 | +$7,326 |
| **10-seed final** | **$28,962** | **+$6,684** |
| ❌ +NE strawberry row 0 (5 tiles) | $24,466 | -$5,138 |
| ❌ +remote-tile plant priority boost | $20,547 | -$9,057 |
| ❌ +bonus-vs-maintenance water split | $24,413 | -$5,191 |
| ❌ +$2100 cash reserve for SW land | $4,344 | -$25k (killed animal buys) |

## Preliminary H2H vs BT (12 games, 6 seeds × 2 seats)

| metric | Session 47 | Session 48 |
|---|---:|---:|
| custom H2H avg | $14,000 | $15,916 |
| BT H2H avg | $145,032 | $142,062 |
| **wins** | **0/12** | **0/12** |
| **avg delta** | **−$131,033** | **−$126,146** |

H2H delta improved by +$4,887, but still 0/12. BT solo produces $150-170k vs our $29k — gap remains fundamental.

## Root diagnosis of the remaining gap

**Land unlock timing**: SW ($2000) doesn't unlock until D13 in most seeds because early cash goes to hires + animals + wheat seed. Strawberry planted D14 gets only 2 productions vs the 4 possible from a D6 plant. That's ~$4-6k/game left on the table.

Attempted fix (reserve $2100 for SW) killed the animal build-out and dropped avg to $4k. Real fix requires: delay 2-3 hires + skip 1 sheep D0-D5, banking cash for SW while still building minimal herd. Complex — next session.

**Field utilization**: at D30 we still have empty tiles in each quadrant:
- NW: 7 empty (mostly walkable/plants)
- NE: 13 empty
- SW: 15 empty
- SE: 21 empty ← never reached

SE tiles are never planted because assigner favors nearby WATER tasks over distant PLANT tasks. Region-specialization would fix this but needs proper design (assign hands to sub-regions or bias assignment cost by region).

## Next session (Session 49) plan

1. **Region-specialized hand assignment** — split hands into NW/NE/SW/SE clusters at spawn so SE actually gets planted. Should hit ~50 plants/game vs current ~35.
2. **Cash-flow tuning for earlier SW unlock** — need to accept slightly slower animal build to reach $2k earlier without breaking feed loop.
3. **Fertilize wheat when profitable** — wheat fertilizer nets negative but ongoing crops (tomato) might benefit. Tomato ROI vs strawberry TBD.
4. **Melon in SE** — 6-unit crops at $250-400 base. High ROI, but 10-day cycle. Fills SE tiles nicely if land is unlocked by D8.

Target: solo $40-50k, H2H delta down to −$100k.

## Files touched (all under `agent/custom/`)
- `plan.py` — added STRAW role, SW/SE straw layout
- `tasks.py` — new FertilizeTask, strawberry plant priority, ongoing crop harvest fix
- `economy.py` — strawberry seed buys, fert reserve, wheat reserve up, starving-market guard, land reserves per quad
- `agent/custom_v2_bak/` — snapshot of Session 47 v2 code (for regression testing)
- `SESSION_48_REPORT.md`

`main.py` UNCHANGED (still Session-42 breaking_tie shipped).
