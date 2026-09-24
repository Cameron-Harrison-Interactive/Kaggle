# Session 56 — Shipped v10 (public score 600 = initial), REVERTED

## What happened
- Solo $80,007 (10 seeds) — unchanged from S55
- H2H sim delta: -$87k vs BT, -$89k vs moon, -$112k vs V41 (0/12 all opps)
- **Shipped v10 to Kaggle**: initial public score **600.0** (fresh submissions
  start at low score and evolve as they play ladder games)
- **Reverted `main.py` back to Session-42 breaking_tie** (last-known-good, 
  scored 1862.6 after many days of matches)
- **Revert also shows 600.0** initially — confirms this is initial score, not
  actual ELO. Will take days for true score to emerge.

## The lesson

Sim-strong solo does not equal ladder-strong H2H. Our bot's:
- Solo $80k (excellent for a from-scratch build)
- H2H sim -$87 to -$112k vs top opps (LOSING every simulated game)
- Real ladder: 600 vs ~3000 top

600 vs 1862.6 (breaking_tie) means we're losing 5x worse to ladder opponents.

The "H2H closing gap from -$131k to -$87k" was optically improving but always
meant we were LOSING that many dollars per game. Real ladder has MANY opponents
of varying strength; our bot loses to all of them by significant margins.

**Root cause**: our bot over-invests in melon (25 tiles, 108-180 units sold/game)
which floods market inv, crashing prices. Opponents don't have this problem
because they don't glut low-inventory-cap items. Meta bots use wheat + fert
which market absorbs better.

## Ship-testing outcomes

| submission | ID | ship | public score |
|---|---|---|---:|
| previous | 55716221 | breaking_tie (S42) | 1862.6 |
| this session | 55730309 | v10 custom | **600.0** |
| revert this session | 55730353 | breaking_tie (S42) | pending |

## What our 10 sessions of custom bot BUILT

An excellent solo-money bot ($80k, up from $10k v0). Clean architecture:
- board.py — obs wrapper (fast queries)
- pathing.py — Manhattan step_toward
- plan.py — layout of crops/pastures/coops per quadrant
- tasks.py — 12 task classes generated from state each turn
- assigner.py — greedy priority×distance matching, carry-stickiness bonus
- executor.py — per-unit primitive: walk / pickup / terminal
- economy.py — market orders (SELL/BUY/HIRE/BUY_LAND/BUY_ANIMAL)
- agent.py — top-level: config + wire-up

**Preserved for future work.** Custom bot is at $80k solo; getting to
BT-competitive H2H ($150k+) requires fundamentally different H2H
strategy (opponent-aware market timing, not solo optimization).

## What's next

Options for user to choose:

1. **Keep breaking_tie shipped** (safest — 1862.6 score) and iterate on
   custom bot for eventual H2H tuning that BEATS BT before shipping again
2. **Try v41 or moon shipped** — these are alternative meta bots we have in
   agent/ that might score higher than breaking_tie
3. **Try a HYBRID** — custom bot planting/tasks, BT-style economy
4. **Give up on solo-tuning** — start over with an H2H-focused bot that
   models opponent behavior (needs weeks of work)

## Progression across all 10 sessions

| session | solo | sim H2H vs BT | ladder score |
|---|---:|---:|---:|
| Baseline (S42 breaking_tie) | ~$168k | (self) | 1862.6 |
| S47 v2 | $22,278 | -$131k | — |
| S48 v3 | $28,962 | -$126k | — |
| S49 v4 | $43,556 | -$121k | — |
| S50 v5 | $56,292 | -$120k | — |
| S51 v6 | $60,890 | -$108k | — |
| S52 v7 | $70,307 | -$100k | — |
| S53 v8 | $77,214 | -$93k | — |
| S54 v9 | $81,696 | -$90k | — |
| S55 v10 | $80,007 | -$87k | — |
| **S56 v10 shipped** | $80,007 | -$87k | **600** |
| **S56 revert to BT** | $167,943 (BT solo) | 0 (self) | pending |

Session 56 is a hard reality check. We built a great solo bot; it's not
competitive on the H2H ladder.

## Files touched
- Created: `scripts/build_main.py` (concatenator)
- Created: `tests/h2h_all.py` (multi-opp H2H test)
- **`main.py` = Session-42 breaking_tie** (restored)
- `agent/custom_v10_bak/` — v10 snapshot preserved
- `SESSION_56_REPORT.md`
