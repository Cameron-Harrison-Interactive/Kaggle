# Session 60 — Field Utilization + Priority Sweep (NO SHIP)

## Summary

- Solo: **$91,429 (10 seeds)** — best ever, up from $80k shipped
- H2H BT: **-$67,693 (20 seeds)** — best ever (was $-87k shipped)
- H2H avg vs 4 top opps: **-$60,566** — best ever
- Alive: 16/16 all seeds
- Ship unchanged (still v10.5)

## User's complaints — status

### 1. "Animals way too late" — FIXED
D0-D1 bootstrap now buys 2 sheep + 2 cow + 12 wheat product on H1.
Delay NE land to D2. Result:
- D1: **4 animals** (was 0)
- D6: **8 animals** (was 1)
- D12: **16 animals** (was 2)

Matches BT's timing.

### 2. "Aren't using a lot of the field" — PARTIALLY FIXED
Still 30-35 empty tiles late-game. Root cause: after full herd of 16
animals set up, ALL 10 hands spend nearly every turn on FEED/CARE/HARVEST/
COLLECT_FERT tasks. Priority system means PLANT (40) always loses.

Experiments tried:
- Reduce herd to 3/3/4 (10 animals) — solo -$12k, H2H hurt moon badly
- Reduce herd to 4/4/5 (13) — hurts moon and V41
- Reduce herd to 4/5/5 (14) — hurts moon
- Wheat plant priority 40→45,50,55,60 — all same or worse
- Dead-zone boost (wheat pri 63 after D20) — plants D21-D27 improved from 8-13 to 12-20 but solo/H2H worse
- HARVEST_ANIMAL priority dynamic (55 low yield, 84 near cap) — worse

**Conclusion**: 30 empty tiles is a hard tradeoff. Reducing herd loses more
income than the plant boost gains. The task-scheduler design inherently
prioritizes animals over plants because animals starve.

## Wins this session

| tuning | old | new | delta |
|---|---:|---:|---:|
| FertilizeTask.priority | 85 | **90** | +$5k avg |
| DigTask.priority | 50 | **40** | +$1.5k avg |
| PICKUP batch | 3 | tested 4-6 (reverted) | +$5k BT only |
| DROP_CARRY_THRESHOLD | 6 | tested 8-15 (reverted) | mixed |
| PlaceAnimalTask.priority | 75 | **75** (confirmed best) | |
| CareTask.priority | 65 | **65** (confirmed best) | |

Also revealed: **wheat production now MATCHES BT (817 vs 879 units).**
Gap is in strawberry (52 vs 187) and wool (108 vs 183).

## Diagnostic: BT's strawberry advantage

BT plants **38 strawberry** by D15. We plant 5-6. BT covers entire SW quad
with strawberry (rows 5-9). BT strategy: strawberry flood.

Tested: SW row 7 as STRAW — hurt because late unlock means missed productions.
BT does it earlier by unlocking SW faster.

## Full H2H progression

| session | solo | BT | V41 | moon | soil |
|---|---:|---:|---:|---:|---:|
| S47 v2 | $22,278 | -$131k | | | |
| S55 v10 (shipped) | $80,007 | -$87k | -$115k | -$89k | -$115k |
| S57 v10.5 (shipped) | $80,007 | -$87k | -$115k | -$90k | -$116k |
| S59 v10.8 | $84,644 | -$73k | -$66k | -$80k | -$66k |
| **S60 v10.9** | **$91,429** | **-$67k** | **-$62k** | **-$77k** | **-$62k** |

Total (v10.5 shipped → v10.9 dev): solo **+$11k**, BT H2H **+$19k**, V41 **+$53k**, soil **+$54k**.

## Ready to ship?

v10.9 is significantly better than v10.5 shipped:
- Solo up ~14% ($80k → $91k)
- H2H BT up ~22% (from -$87k to -$68k)
- V41/soil up ~50% (from -$115k to -$62k)

Available submissions today: **1 remaining** (based on daily limit).

Recommendation: ship v10.9 to see real ladder ELO. Even if we can't hit
top-5, the improvement should be visible in the ELO climb.

## What's left to try (Session 61+)

1. **BT-style strawberry flood**: replace some wheat rows with strawberry
   after SW unlocks. Needs careful priority/timing.
2. **Region hand-specialization**: reserve 2 hands for far-tile planting
   even when animals need feed. Multiple failed attempts previously.
3. **Cash-flow smoothing**: sell melon in smaller batches to avoid glut.
4. **Forward-search wrapper** at select decision points (S46 wrapper exists).

## Files touched
- `agent/custom/economy.py` — D0 bootstrap, NE delay to D2
- `agent/custom/tasks.py` — CareTask pri 65, FertilizeTask pri 90, DigTask pri 40, fallback place-any-animal
- `agent/custom_v108_snapshot/` — S59 v10.8 backup
- `agent/custom_v109_final_bak/` — v10.9 backup (current dev)
- `tests/bench.py`, `tests/multi_opp_sweep.py`, `tests/task_trace.py` — diagnostic tools
- **`main.py` UNCHANGED** (still v10.5 shipped)
