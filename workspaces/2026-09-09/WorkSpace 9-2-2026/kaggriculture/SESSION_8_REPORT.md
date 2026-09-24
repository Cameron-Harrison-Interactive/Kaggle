# Session 8 — 8-20-2026: the complete main.py (every system in one file)

## What you asked for this turn, and what is now IN main.py

You described the exact architecture you want, and it is all implemented in
`main.py` (1,135 lines, fully self-contained, stdlib only):

1. **No dedicated animal worker.** Animal chores (feed / collect fertilizer /
   harvest milk-wool-eggs) are ordinary jobs assigned to whichever worker is
   nearest — because the animals are pastured next to the shed and EVERY
   worker starts the day on a shed tile (they all "walk over the top of the
   animals"). The plan also keeps the outbound-feed / inbound-collect pattern
   in the scheduler design.
2. **Routes the field day-by-day from the live board.** Every morning it scans
   the board, lists only what needs work, splits each quadrant into serpentine
   rows/order (short adjacent walks, never dead space), assigns work to
   workers, and re-plans — nothing is memorized, so it can never desync and a
   copied "build and timing" can never sync to us.
3. **Harvest -> replant -> water.** The tile is replanted the moment it is
   harvested (maturity-gated), with its same-day water slot guaranteed.
4. **Knows the rules.** Exact crop/animal/market tables + the exact price
   function; a plant is only scheduled with its water guaranteed (no
   hour-22-plant-without-hour-23-water).
5. **Reads the town.** `obs.town.unlocked_shops` is read every day; the crop
   choice and seed buys tilt toward what the town is actually buying (carrots
   when a Pet Cafe / Farmers Market is open, tomatoes early if a shop wants
   them, etc.).
6. **Reads the opponent and the market.** Build classifier (animal-heavy →
   we go crops+geese; crop-heavy → we go animals), herd tilt, front-run sells,
   a market-distress pivot (stop buying cows/sheep the moment milk/wool crash,
   put the cash into crops), and a deliberate "dump" — if the opponent is
   flooding a product, we dump our surplus of it to crash the price they
   depend on.
7. **Decides its own crew.** The day's work is counted exactly (Manhattan walk
   + 1 action); it hires more hands until the work fits or the money runs out.
8. **Anti-mirror.** Crop priority and assignments rotate by a per-match
   signature, so no two matches play the same schedule.

## Honest measured results

| Matchup | Result |
|---|---|
| main.py vs PASS (10 seeds) | **$60,312 avg** (min $51.4k, max $71.1k) |
| main.py vs v2 (our reactive bot) | 0W-6L, −$14.9k avg |
| main.py vs v25 tape ($145k) | (prior: −$101k) |

**The hard truth, stated plainly:** I delivered all the architecture you asked
for, but this session's rewrites made the bot WORSE in head-to-head play than
the end of the last session (which was 3W-3L, −$1.4k vs v2, $66.9k solo). I
found and fixed several real bugs along the way (the tile-claim logic blocking
harvest-after-water, herd placement piling on one worker, duplicate carrot
buys, the round-robin idling 4 of 5 workers), but the net is still a
regression, and I'm not going to dress it up.

The reason is simple and I've said it before: every routing change I make
trades crop coverage against herd income, and finding the balance needs
hundreds of measured games — which is exactly what the search harness on your
PC is for. I was hand-sweeping one config at a time and oscillating.

## What I recommend now (concrete)

1. **Run the search on your PC against the real metric (margin), not PASS.**
   The pieces are all in place; what's missing is the tuned balance:
   ```
   python3 scripts/search_params.py --population 32 --generations 300 --seeds 1,2,3
   ```
   (edit its `import decision_agent_v2 as dv2` → `import main as dv2`).
2. **Keep the proven v4 counter** (`agent/decision_agent_v4.py`) as the safe
   submit candidate — it is +$16.9k on clone/flood matchups and beat v2 on
   contested margins earlier. main.py's systems should be migrated onto it one
   at a time, each verified against the gauntlet before the next is added.
3. **The remaining big build is still the route compiler** (per-worker
   full-season dated crop schedule replayed through a cash/labour/feed ledger,
   re-planned daily). That is what closes the ~$85k gap to the v25 tape — not
   more hand-tuning of the greedy scheduler.

## Files
- `main.py` — the complete self-contained bot (all systems above).
- `agent/decision_agent_v4.py` — the verified counter (safe submit).
- `scripts/{rules,sim,planner,search_params}.py`, `scripts/battle_contested.py`
  — the dev/tuning toolbox.
- `top10/shabby_farm_agent.py` — Aster, the real top-10 opponent for the
  gauntlet.
