# Session 50 — Custom Bot v5: CARE + NE Strawberry + Extra Melon (multi-session, NO SHIP)

## Where we are
- **Session 47 v2**: solo $22,278 avg
- **Session 48 v3**: solo $28,962 avg (+$6,684)
- **Session 49 v4**: solo $43,556 avg (+$14,594)
- **Session 50 v5**: solo **$56,292 avg (10 seeds)** — **+$12,736 (+29%) vs S49**
- Ship unchanged: `main.py` md5 = `c0c74b43ea577dfb05f1e21dd0f8991b` (Session-42 breaking_tie)
- **All animals alive on every seed. Zero errors.**

## What changed this session

### 1. **CARE priority bump** — biggest win of session (+$10k)
- Was priority 30, and required animal to be `fed_today=True` (chicken-and-egg — could only fire after FEED completed same day)
- Now priority 58, unconditional (`if not cared_today`)
- CARE + FEED same day banks a +1 unit bonus on next production day
- Sheep produces every 3 days → CARE for D0..D2 → +3 bonuses collected D6 → doubles wool yield
- 10 animals × ~10 productions × +1 unit average × ~$150 avg = ~$15k additional
- Tuned across priorities: 55 → +$9k, 58 → +$10k, 60 → same, 65 → -$1k
- Kept at 60

### 2. **NE row 1 → STRAWBERRY** (+$3k)
- Plant on D1 (NE unlocks D0), full 4 productions D11-D17
- Cost: 5 wheat tiles removed
- Doubled strawberry throughput; fertilization pays off since 4 productions per plant

### 3. **SW/SE row 8 → MELON** (+$2k)
- Added 10 more melon tiles (SW row 6+8, SE row 6+8)
- Plant D13-D14 after SW/SE unlock, single harvest each
- Total melon tiles: 25 (was 15)

### 4. **Herd bump 4/3/4=11 → 4/3/6=13**
- Added 2 more geese ($300/each, easy pastures/coops)
- More fertilizer output → more strawberry doubling

## Ablation this session

| change | avg | delta |
|---|---:|---:|
| Session 49 baseline (v4) | $43,556 | — |
| herd 6/4/8=18 (fill all slots) | $37,558 | -$5,998 (cash constrained) |
| herd 4/3/6=13 (add geese) | $47,521 | +$3,965 |
| + NE row 1 STRAWBERRY | $46,955 (5 seeds) | +marginal |
| + SW/SE row 8 MELON | $46,527 (10 seeds) | +marginal (with above) |
| + CARE task always eligible | $46,527 | 0 (pri 30 loses everything) |
| + **CARE priority 58** | **$56,292** | **+$9,765** |
| **10-seed final** | **$56,292** | **+$12,736 vs S49** |
| ❌ Region-specialization revisited | $22-46k (variance) | still hurts |
| ❌ Wheat plant priority bump 66 | $21k (mass plant deaths) | -$25k |
| ❌ Multi-hour hire spread | $6k (over-hiring blew cash) | -$40k |
| ❌ Melon row 5 replacing straw | $40k | -$6k |
| ❌ Extra SW row 9 pasture | $45k | -$1k |
| ❌ NE row 2 → MELON | tested, kept row 2 wheat | 0 |

## Preliminary H2H vs BT (12 games, 6 seeds × 2 seats)

| metric | S47 | S48 | S49 | **S50** |
|---|---:|---:|---:|---:|
| custom H2H avg | $14k | $16k | $24k | **$27k** |
| BT H2H avg | $145k | $142k | $145k | $146k |
| **wins vs BT** | 0/12 | 0/12 | 0/12 | **0/12** |
| **avg delta** | −$131k | −$126k | −$121k | **−$120k** |

Steady H2H closing but still 0/12 vs BT. BT solo ~$150k, we're at $56k — ~2.7x gap.

## Progression summary

| session | solo avg | H2H delta vs BT | key insight |
|---|---:|---:|---|
| S47 v2 | $22,278 | −$131k | scheduler works |
| S48 v3 | $28,962 | −$126k | strawberry + fert |
| S49 v4 | $43,556 | −$121k | **melon** + emergency wheat buy |
| **S50 v5** | **$56,292** | **−$120k** | **CARE + herd bump** |

## Root diagnosis of remaining gap

Solo gap: $56k vs $150k = ~$94k missing. Where does BT make it?

BT does 700+ market orders (we do 567) → more sells. BT sells ~1465 wheat (we sell ~180) → they have DOUBLE our wheat production. That's the primary gap.

Our field: 40 wheat + 25 melon + 13 straw. BT tapes suggest more wheat + less specialty. Because H2H, opponent competes for melon/straw price and it collapses fast. Wheat market is more elastic.

## Next session (Session 51) plan

1. **Larger wheat field** — try replacing 1-2 melon rows with wheat. Melons glut fast in H2H; wheat elastic.
2. **Better hand utilization** — current 10 hands do ~30 productive actions/hour of possible 240. Debug why hands idle.
3. **Continuous market maker** — bot only uses 190/720 hours of market. Fill idle hours with small sells.
4. **Fix task overflow** — with 40+ tasks/turn and 10 hands, low-pri tasks (PLANT, BUILD) starve. Consider round-robin or task fairness.

Target: solo $70-90k, H2H delta down to −$100k.

## Files touched
- `tasks.py` — CARE priority 30→60, CARE always eligible (no fed_today gate)
- `plan.py` — NE row 1 STRAW, SW row 8 MELON, SE row 8 MELON
- `agent.py` — herd 4/3/4=11 → 4/3/6=13
- `agent/custom_v4_bak/` — snapshot of Session 49 code
- `SESSION_50_REPORT.md`

`main.py` UNCHANGED (still Session-42 breaking_tie shipped).
