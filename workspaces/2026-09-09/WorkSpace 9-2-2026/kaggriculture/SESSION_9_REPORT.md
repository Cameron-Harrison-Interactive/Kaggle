# Session 9 — 8-20-2026: dynamic hiring ("knows how many hands it needs") + the
# animals-fund-workers / crops-are-the-end-game-gold economy

## What you asked for, and what's now in main.py

1. **"The bot should know how many hands it needs for its field, like a real
   farmer."** — DONE. The hire decision is no longer a fixed 4-5. Every
   morning the bot counts the real work:
   - each animal ≈ 6 steps (feed/collect/harvest/care + the shed walk),
   - each standing crop ≈ 4 steps (walk + water),
   - each new plant ≈ 5 steps (walk + plant + walk + water),
   then hires EXACTLY the crew that covers it (no idle hands, nothing
   uncovered), funded by the herd, capped only by money. Measured: the crew
   scales 4 hands early → 8-9 hands as the field fills.

2. **"The animals pay for the hands; the crops are the end-game gold."** —
   Your model, implemented. The buy order builds the herd FIRST (the steady
   milk/wool/fert cash that funds the workers), then the mid-game cash buys
   melons/strawberries — the end-game gold — while their planting windows
   are still open. Seed buys now trigger when stocks are LOW (≤1) and buy 4
   at a time, so the field actually fills instead of buying 2 seeds that are
   planted in a day.

3. **Found and fixed the real killers along the way** (all measured):
   - **Animals escaped days 4-6** because feed wheat was gated behind the
     cash buffer — a $288 balance couldn't buy the $300 of feed the plan
     already assumed. Now feed wheat is life-critical: it buys regardless of
     the buffer (the engine stops the order when money runs out).
   - **Cows piled up in the shed** (2→4→7 unplaced) because placement was
     scheduled to ONE worker. Now each animal's BUILD→PICKUP→PLACE goes to a
     different worker — every hand helps, nobody is a dedicated tender.
   - **Workers nearest the shed got ALL the feeding and dropped their crop
     rows** (13 of 26 plants went unwatered). Now a dynamic role split:
     enough animal workers to carry the herd's chores, everyone else takes
     crop rows.

## Measured results

| | Result |
|---|---|
| vs PASS (10 seeds) | **$64,413 avg** (min $55.9k, max $71.3k) |
| crops | ~30 standing |
| animals | 14 (full herd) |
| hands | 4 early → 8-9 as the field fills |
| vs v2 (our reactive bot) | 0W-6L, −$15.5k (see below) |

## The honest remaining problem: contested matches

Solo we're now tied with our best reactive bot. But head-to-head vs v2 we
still lose ~$15k — and the reason is exactly what you predicted about the
market: when BOTH bots run 14-cow herds, milk and wool crash to $1 for both
sides, and the winner is whoever has the better crop economy. Our counter
code (tilt away from the cow-heavy opponent, front-run sells) is in main.py
but hasn't been re-tuned since the economy rewrite — that's the next thing to
dial in, not another architecture change.

## Where this leaves us

main.py (1,192 lines, self-contained) now has every system: dynamic
workload-based hiring, the animals→workers / crops→gold economy, role-split
real-time field routing with harvest→replant→water, town reading, opponent
reading, market reading with the crash-pivot, and anti-mirror rotation. The
remaining gap vs the leaderboard's 60-crop tape bots is the contested
counter tuning + the per-tile labor efficiency of a full-season scheduler —
both doable inside this same runtime router (no offline compiler, nothing
pre-scripted).

## Files
- `main.py` — the submission.
- `agent/decision_agent_v4.py` — the earlier verified counter (safe submit).
- `scripts/{sim,planner,rules,search_params}.py`, `scripts/battle_contested.py`.
