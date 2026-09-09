# Session 47 — Custom Bot v0 → v2 (multi-session build, NO SHIP)

## Ground rules (per user)
- Build custom bot from scratch across multiple sessions
- **No shipping** until H2H measurably beats BT (Session-42 breaking_tie, currently on ladder)
- No copying public notebook tapes
- Session-35 self-aware brain preserved as bak; not touched this session

## What was built

Module layout under `agent/custom/`:

| file | role | lines |
|---|---|---|
| `board.py` | read-only obs wrapper (game constants + coord helpers) | 130 |
| `pathing.py` | Manhattan step_toward, nearest — no BFS needed | 60 |
| `plan.py` | fixed layout (which tile is CROP / PASTURE / COOP) + herd targets | 90 |
| `tasks.py` | Task classes + `generate_tasks(board)` — state-derived task set | 220 |
| `assigner.py` | greedy priority × distance matching of units → tasks | 80 |
| `executor.py` | per-unit primitive: walk / shed-detour / terminal action | 100 |
| `economy.py` | market orders (SELL/BUY/HIRE/BUY_LAND) each turn | 145 |
| `agent.py` | top-level: wires it all together + config | 65 |

## Design principle (user's core ask)

**No precompiled routes.** Every turn:
1. Read `Board` (fresh view of obs)
2. `generate_tasks(board)` returns tasks worth doing NOW, purely from state
3. `assign(board, tasks)` greedily pairs units to tasks by priority + distance
4. `executor.action_for_unit` produces ONE primitive per unit (walk, pickup, or terminal)

Tasks are recomputed every turn from live state — no two games route the same way. Opponents can't fingerprint a fixed opening; the sequence emerges from the seed's specific weed spawns, animal placements, and market pressure.

## Progression this session

| version | scope | solo avg (5 seeds) |
|---|---|---:|
| **v0** (agent only) | Wheat only, NW quad, 6 hires/day | $10,780 |
| **v1** (bugs fixed) | + animals (3 sheep, 2 cow, 3 goose), wheat feed reserve | $12,992 |
| **v2** (land + more) | NW+NE build, 4/3/4 herd, 9 hires, seed-budget-per-empty-tile | **$22,278** |

All 5 seeds hit **all 11 animals alive** in v2. Weed counts < 10.

## Bugs found and fixed this session

1. **Harvest at yield=1 catastrophe** — pulled wheat at yield 1 (throwing away 5 free units). Fix: wait for yield ≥ achievable_max_without_fert.
2. **Water vs harvest priority inversion** on `age == max_day` — was harvesting before the final in-window water. Fix: in-window water pri 82 > pre-decay harvest pri 78.
3. **Animals starving because bought before wheat available** — bought 3 sheep + 3 geese on D0 before any wheat harvest. Fix: `_can_feed_one_more()` requires wheat already in shed to cover new animal to day 4.
4. **Wheat sold before animal placement** — bought 7 animals D6-D9 but they starved because reserve = current_herd was 0 before purchase. Fix: reserve uses `planned_herd * 3` as floor.
5. **End-game fire sale killed animals** — dumped ALL wheat at D28. Fix: keep `current_herd * (days_left + 1)` wheat aside during fire sale.
6. **Herd target mismatch between plan.py and agent.py** — `plan.py` hardcoded `GOOSE_TARGET=3` while agent said `goose_target=4`. Wheels bought 4 geese but placer refused. Fix: `desired_animal_for(x, y, counts, targets)` accepts targets dict.
7. **DIG priority too low** — weeds accumulated (77 on D29) blocking replant. Fix: DIG pri 25 → 50 (above PLANT).
8. **Seed over-buy** — bought 78 wheat seeds early ($780) when only 20 tiles could be planted immediately. Fix: seed target = current empty CROP tiles + 5 buffer.

## Preliminary H2H (baseline, established for future sessions)

12 games (6 seeds × 2 seats) vs breaking_tie:

| metric | value |
|---|---:|
| custom H2H final avg | $14,000 |
| BT H2H final avg | $145,032 |
| **wins** | **0 / 12** |
| **avg delta** | **−$131,033** |

Meta production ceiling: BT solo ~$150-170k. Our v2 solo $22k. **The gap is entirely production ceiling** — we don't yet plant SW/SE (bought land but seeds don't cover them), no strawberry / high-margin ongoing crops, no fertilizer routing.

## Failed experiments this session (documented, not shipped)

- Herd target 6/4/8 (18 animals): starved after D14 despite big wheat reserve. Feed loop can't sustain 18 on 30-tile field.
- Remote-tile plant priority boost (bump SE tile pri to ~50): hands wasted turns walking, avg fell $22k → $20k.
- Bump hires to 12: no effect (fib 13+ cost blocks 11th/12th hire early).

## Verified this session

- All 11 animals survive in all 5 seeds tested
- Field packs cleanly in NW+NE, no weeds > 6
- Loop end-to-end passes zero agent errors across 720 × 5 games
- `main.py` md5 UNCHANGED: `c0c74b43ea577dfb05f1e21dd0f8991b` (= Session-42 breaking_tie)

## Session 48 plan

Real production jumps needed:

1. **Strawberry tiles in SW/SE** (highest ROI ongoing crop @ ~$120-334 rising) — 4 productions × ~$200 = $800/tile
2. **Fertilizer routing to strawberry** — 2 fert → double all 4 productions = +$800/tile net
3. **Region-specialized hand assignment** — assign hands to sub-regions to prevent all-hands-in-NW pileup, so SE actually gets planted
4. **Additional seed budget for SW+SE wheat**
5. **More hires funded by strawberry income** — hitting 15+ hands/day mid-game

Target: solo $50-80k, then H2H test.

## Files created (all under `agent/custom/`, none touch `main.py`)
- `agent/custom/__init__.py` `board.py` `pathing.py` `plan.py` `tasks.py` `assigner.py` `executor.py` `economy.py` `agent.py`
- `tests/test_v0_solo.py` `tests/debug_dump.py` `tests/trace_early.py` `tests/h2h.py`
- `SESSION_47_REPORT.md`
