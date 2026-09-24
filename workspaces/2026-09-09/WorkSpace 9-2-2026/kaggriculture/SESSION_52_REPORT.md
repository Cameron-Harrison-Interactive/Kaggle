# Session 52 — Custom Bot v7: PLACE priority fix + Cow-heavy herd

## Where we are
- **S47 v2**: solo $22,278
- **S48 v3**: solo $28,962 (+$6,684)
- **S49 v4**: solo $43,556 (+$14,594)
- **S50 v5**: solo $56,292 (+$12,736)
- **S51 v6**: solo $60,890 (+$4,598)
- **S52 v7**: solo **$70,307 (10 seeds)** — **+$9,417 (+15%) vs S51**
- Ship unchanged: `main.py` md5 = `c0c74b43ea577dfb05f1e21dd0f8991b`
- **All 16 animals alive on every seed (up from 13). Zero errors.**

## What changed this session

### 1. **PLACE priority 50 → 75** — biggest single-turn win (+$8k)
Diagnostic: watched 4+ pastures/coops stuck empty for 15+ days while
6 bought animals sat in shed. PLACE tasks at priority 50 lost every
tie to WATER (60/82), HARVEST (70/78), FEED (90). Bumped to 75
(above HARVEST 70, below WATER 82) so animals get placed the same
day they're bought.

Before: 3 cow + 4 sheep + 5 goose = 12 placed. Now: 5+5+6=16.

### 2. **Cow-heavy herd (5/5/6 = 16)**
BT solo produces ~360 milk; we produced 49. Milk = $160/unit vs egg $50.
5 cows × 15 productions × 2 (care) = 150 max milk. Now producing ~71
(getting there — still 30-40% coverage due to hand routing latency).

### 3. **BT solo-tape analysis**
Instrumented BT solo to understand the $150k gap. Key deltas:
| item | us S51 | BT | gap $$ |
|---|---:|---:|---:|
| MILK | 49 | ~360 | $50k |
| STRAWBERRY | 67 | ~360 | $44k |
| WHEAT sold | 200 | ~500 | $8k |
| FERT sold | 71 | ~240 | $17k |

**Milk gap is largest.** Fixed by 5 cows + place fix.

## Ablation this session

| change | avg | delta |
|---|---:|---:|
| S51 baseline | $60,890 | — |
| Cow 3 → 6 (herd 4/6/4) | $53,029 | -$8k (starved variance) |
| Cow 3 → 5 (herd 4/5/6) | $61,888 | +$1k |
| Cow 3 → 4 (herd 4/4/7) | $62,783 | +$2k |
| Herd 5/5/6 = 16 | $64,099 | +$3k |
| Herd 5/5/8 = 18 | $56,340 | -$5k (too many) |
| + **PLACE priority 75** | **$70,307** | **+$6k** |
| **10-seed final** | **$70,307** | **+$9,417 vs S51** |
| ❌ PLACE priority 83 | $61,460 | seeds 3/8 starved |
| ❌ BUILD priority 74 | $61,600 | over-eager, seed at $90 |
| ❌ MELON fertilize | $65,779 | -$5k (net-negative confirmed) |
| ❌ Goose 6 → 8 (herd 18) | $52,477 | -$18k |
| ❌ SW/SE row 6 → STRAW | $53,507 | strawberry too late |
| ❌ Melon buy up to D19 | $63,712 | wasted seed cash |

## Preliminary H2H vs BT (12 games, 6 seeds × 2 seats)

| metric | S47 | S48 | S49 | S50 | S51 | **S52** |
|---|---:|---:|---:|---:|---:|---:|
| custom H2H avg | $14k | $16k | $24k | $27k | $28k | **$37k** |
| BT H2H avg | $145k | $142k | $145k | $146k | $144k | $138k |
| **wins vs BT** | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | **0/12** |
| **avg delta** | −$131k | −$126k | −$121k | −$120k | −$108k | **−$100k** |

**First time below -$100k delta.** custom H2H +$9k vs S51. BT solo also
dropped slightly ($146k→$138k) — some of the improvement is BT being
squeezed by our better market pressure.

## Progression summary

| session | solo avg | H2H delta | key win |
|---|---:|---:|---|
| S47 v2 | $22,278 | −$131k | scheduler |
| S48 v3 | $28,962 | −$126k | strawberry + fert |
| S49 v4 | $43,556 | −$121k | melon + emergency wheat |
| S50 v5 | $56,292 | −$120k | CARE priority |
| S51 v6 | $60,890 | −$108k | fert-fix + multi-buy + stickiness |
| **S52 v7** | **$70,307** | **−$100k** | **PLACE priority + cow-heavy herd** |

Total closing across 6 sessions: **−$131k → −$100k (+$31k)**.

## Root diagnosis of remaining $100k H2H gap

Our solo $70k vs BT $150k = $80k gap. From BT solo tape:
- Missing milk: ~250 units × $160 = $40k (herd density issue — BT has more animals over more days)
- Missing strawberry: ~250 units × $150 = $37k (need more straw tiles or better plant timing)
- Missing wheat: ~300 units × $25 = $7k

To close: need denser herd (more cows earlier), more strawberry tiles, and reliable wheat production.

## Next session (Session 53) plan

1. **Investigate real Ryo tile allocation** — download a Ryo replay and reconstruct their layout
2. **Try 6 cow / 4 sheep / 4 goose (14 animals)** — max milk revenue
3. **Add pastures beyond NW row 3** — SW row 8 could be pasture instead of melon
4. **Forward-search wrapper** — the base is finally strong enough that search might help

Target: solo $80-90k, H2H delta −$85k.

## Files touched
- `tasks.py` — PLACE priority 50 → 75, MELON fertilize tried+reverted (documented)
- `agent.py` — herd 4/3/8 → 5/5/6
- `agent/custom_v6_bak/` — snapshot of Session 51 code
- `SESSION_52_REPORT.md`

`main.py` UNCHANGED (still Session-42 breaking_tie shipped).
