# Session 11 — 8-20-2026: the full-season crop scheduler (dump prediction + per-match crop config)

## What you asked for, built this turn

"Know what beats each bot tape... what matters most is crop dump and what
crops we actually grow, configured by the bot each time... even if we sell one
turn early."

That is now in `main.py`. The key insight that made it possible: **the
opponent's crop tiles are public AND carry their `planted_day`**. We can
literally read when every one of their crops was planted and compute the exact
day it matures and hits the market. (Note: their *shed* is private — the engine
never sends it — but the planted_day timing gives us the "full route" signal
you wanted, which is the part that matters for dumps.)

## What was built

1. `_opp_dump_days(day)` — the season scheduler's eye on the opponent:
   scans their public tiles, takes each crop's `planted_day`, adds the crop's
   grow time (melon 10 days, strawberry 10 to first yield, wheat 4, carrot 3),
   and returns exactly which of their crops will dump today / tomorrow / the
   day after.

2. **Per-match crop config** (`_pick_crop` upgraded) — the crop we grow is now
   decided by the matchup, every turn:
   - if the opponent is massing a crop (>=6 of it, or >=3 when their farm is
     big), we heavily discount it — we don't share their glut;
   - if OUR crop would mature within 1 day of THEIR dump of the same crop, we
     discount it (don't walk into the crash);
   - if we'd mature just AFTER their dump, we boost it (sell into the
     recovered price).

3. **Sell one turn early** — the front-run rule now fires on predicted dump
   days (their crop matures today/tomorrow), not just on harvest-ready stock.
   We dump ours first, at the pre-glut price, and soften the market for their
   batch.

## Verified (measured)

Instrumented a match vs a melon-heavy cropbot:
```
predicted opponent dumps:  day 8 {WHEAT:3}, day 10 {WHEAT:1, MELON:6},
                           day 12 {MELON:10}, day 14 {MELON:1}
opponent planted:          MELON 16, WHEAT 25
we planted:                MELON 10, WHEAT 43   <- we shifted away from their melons
```
The prediction is exact, and our crop mix visibly pivots away from their glut
crop. No solo regression (still $44.4k avg; the new terms don't fire vs PASS).

| Gauntlet (seeds 1,2,3) | margin |
|---|---|
| vs cowbot (14 cows) | +$2.3k |
| vs sheepbot | −$10.6k |
| vs goosebot | −$2.8k |
| vs mirror (v2 clone) | −$19.4k |
| vs cropbot (melon/straw mass) | −$29.9k |

## The honest bottom line

The season scheduler is built and its two core mechanisms — dump prediction and
per-match crop selection — are verified working. But it cannot beat the tape
bots yet, for a reason that is now measured and unambiguous: **our base
economy is $44k; a crop-heavy v2 build scores $56k, and the real v25 tape
scores $145k.** Predicting their dumps perfectly still leaves us selling
melons into a market where we grew half as many as they did.

The counter is now complete (animals + crops + dumps + timing). The only
remaining lever is the base economy: getting from $44k to the tape's crop
volume, which needs the full-season per-worker labor plan (each worker's
dated sow/water/harvest schedule replayed through a cash/labour/feed ledger,
re-built from the live board every morning — no pre-compiled routes, no
scripting). That is the build that closes the gap, and everything around it —
counter, market reader, town reader, dump scheduler, anti-mirror — is now in
main.py and measured.

## Files
- `main.py` — the submission (1,291 lines, stdlib only).
- `agent/decision_agent_v4.py` — the earlier verified counter (safe submit).
- `scripts/{sim,planner,rules,search_params}.py`, `scripts/battle_contested.py`.
