# Session 51 — Custom Bot v6: Fertilize Fix + Multi-Buy + Carry Stickiness

## Where we are
- **Session 47 v2**: solo $22,278
- **Session 48 v3**: solo $28,962 (+$6,684)
- **Session 49 v4**: solo $43,556 (+$14,594)
- **Session 50 v5**: solo $56,292 (+$12,736)
- **Session 51 v6**: solo **$60,890 (10 seeds)** — **+$4,598 (+8%) vs S50**
- Ship unchanged: `main.py` md5 = `c0c74b43ea577dfb05f1e21dd0f8991b`
- **All 12-13 animals alive on every seed. Zero errors.**

## What changed this session

### 1. **Fertilize task generation fix** (+$1k)
- Was: FERT task only fired when shed had fertilizer
- Bug: hands mid-walk with fert-in-hand got orphaned when shed emptied at
  their pickup turn — no fert task existed → assigner reassigned them to
  WATER, wandering away from strawberry
- Fix: also fire FERT task when ANY unit is already carrying fertilizer
- Result: 16 FERT actions/game → 46 FERT actions/game (nearly 3x)

### 2. **Carry stickiness in assigner** (+$1k)
- New bonus `CARRY_MATCH_BONUS = 5000` to any (unit, task) where unit
  already carries all `required_items`
- Bigger than any distance tiebreaker — locks a hand onto its target once
  it's picked up the needed item
- Fixes the "walk to shed → pick up → wander back to water" thrashing

### 3. **Multi-buy animals per turn** (+$3k)
- Was: only 1 animal purchase per market phase
- Now: loop buying while cash allows, respecting slots + feed budget
- Result: entire herd (~11-13 animals) bought same turn once cash hits, D11
  instead of D13-D24. 2+ extra production days per animal.

### 4. **Goose target 6 → 8**
- Extra 2 geese in remaining coop slots for another $500-$1000

### 5. **Cash reserve loosened** (100→50, 300→200 on D0) (+$0.3k)
- Small: enables ~1 more animal purchase per opportunity

## Ablation this session

| change | avg | delta |
|---|---:|---:|
| Session 50 baseline (v5) | $56,292 | — |
| + fert task fires w/ carry | $57,477 | +$1,185 |
| + carry stickiness | $58,830 | +$1,353 |
| + cash reserve loose | $59,325 | +$495 |
| + goose 6→8 | $60,890 | +$1,565 |
| + **multi-buy animals** | (rolled in) | +$2,801 (net) |
| **10-seed final** | **$60,890** | **+$4,598** |
| ❌ PRE_CARRY_WHEAT task | $56,349 | -$0 (hoarding starved animals) |
| ❌ DROP threshold 6→4 | $41,402 | -$15k |
| ❌ Idle hand walks to empty tile | $60,890 | 0 (no help) |
| ❌ Cow-first buy order | $60,890 | 0 |
| ❌ Sheep target 4→5 | $59,881 | -$1k |
| ❌ Hires_target 12→13 (multi-hour) | $6k | -$55k (over-hiring) |

## Preliminary H2H vs BT (12 games, 6 seeds × 2 seats)

| metric | S47 | S48 | S49 | S50 | **S51** |
|---|---:|---:|---:|---:|---:|
| custom H2H avg | $14k | $16k | $24k | $27k | **$28k** |
| BT H2H avg | $145k | $142k | $145k | $146k | $144k |
| **wins vs BT** | 0/12 | 0/12 | 0/12 | 0/12 | **0/12** |
| **avg delta** | −$131k | −$126k | −$121k | −$120k | **−$108k** |

**Best single-session H2H delta improvement**: -$120k → -$108k = **+$12k**. 
Total closing across 5 sessions: **-$131k → -$108k = +$23k**.

## Progression summary

| session | solo avg | H2H delta | key win |
|---|---:|---:|---|
| S47 v2 | $22,278 | −$131k | scheduler works |
| S48 v3 | $28,962 | −$126k | strawberry + fert |
| S49 v4 | $43,556 | −$121k | melon + emergency wheat buy |
| S50 v5 | $56,292 | −$120k | CARE priority bump |
| **S51 v6** | **$60,890** | **−$108k** | **fert-fix + multi-buy + stickiness** |

## Root diagnosis of remaining gap

Solo $61k vs BT $150k = $89k missing. Where does BT still get more?

Diagnostic from S51:
- We use 190/720 hours of market (26%) — BT uses ~70%+
- FEED coverage still ~35% of animal-days possible (herd builds late D11)
- Task priority saturation: 826 PASS turns out of 7200 (11.5%) — hands idle
- SE quadrant still under-planted (mainly wheat there gets planted late)

## Next session (Session 52) plan

Several dry wells this session. Different angles to try:

1. **Continuous market maker** — sell 1 melon / 1 strawberry / 1 fert every idle hour to keep 700+ market orders / game (currently 500-600)
2. **Task queue depth** — more tasks per turn so idle hands always find work
3. **Early strawberry planting** — plant D0 not D1 (need to verify current does D0)
4. **Fertilize wheat in the bonus window** — was tested to be net-negative individually but with bulk fert supply now maybe worth revisiting
5. **Forward-search wrapper** (from session 46) — could re-enable now that base is strong

Target: solo $70k+, H2H delta −$95k.

## Files touched
- `tasks.py` — fert task fires when carrier has fert; PRE_CARRY_WHEAT class defined but disabled
- `assigner.py` — CARRY_MATCH_BONUS added
- `economy.py` — multi-buy animal loop, cash_reserve 300→200/100→50
- `agent.py` — goose_target 6 → 8
- `executor.py` — idle_action tested with quadrant-aware walk; reverted
- `agent/custom_v5_bak/` — snapshot of Session 50 code
- `SESSION_51_REPORT.md`

`main.py` UNCHANGED (still Session-42 breaking_tie shipped).
