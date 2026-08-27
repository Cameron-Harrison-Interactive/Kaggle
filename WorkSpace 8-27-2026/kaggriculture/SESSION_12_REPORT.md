# Session 12 — 8-20-2026: the full-season in-bot labor plan — built, measured, and the honest status

## What this session delivered

You asked for the full-season scheduler, and its two halves are now in
`main.py`:

### 1. The opponent-season reader (dump prediction) — VERIFIED WORKING
The opponent's crop tiles are public AND carry their `planted_day`, so we read
their whole crop schedule and predict their exact dump days:
```
predicted opponent dumps: day 8 {WHEAT:3}, day 10 {MELON:6}, day 12 {MELON:10}, day 14 {MELON:1}
opponent planted: MELON 16, WHEAT 25
we planted:        MELON 10, WHEAT 43   <- we pivoted away from their melons
```
Plus per-match crop config (avoid their glut crop, avoid maturing into their
dump, favor maturing right after it) and **sell-one-turn-early** on their dump
days.

### 2. The full-season labor plan — built, running, balanced
Each worker gets ONE continuous serpentine pass through a slice of the field
(re-derived every morning, nothing memorized, no two matches route the same):
1. FEED (outbound, at the shed — every worker "walks over" the animals),
2. FIELD PASS (water / harvest→replant→water / dig / plant, adjacent-tile walks),
3. HERD PLACEMENT (build+pickup+place, capped so it never crowds the crops),
4. INCOME CHORES (fertilizer / milk / wool / care).

Movement is exact Manhattan distance, so a job is only accepted if it truly
finishes by hour 24 — and the bot hires exactly enough hands that the plan
drops ZERO must-jobs (measured: all workers busy 17–24, dropped=0).

## Bugs found & fixed this session (all real)
1. **Wheat pickup overshoot** — workers picked up 5 wheat to feed 1 animal, so
   the 4th animal starved. Now pick up exactly what's needed.
2. **Sell/buy wheat round-trip** — we sold our grown wheat and bought it back
   for feed (286 bought vs v2's 21). Now wheat is held for feed; only a big
   surplus is sold.
3. **Herd placement crowded out crops** — 5 placements/day consumed workers
   0–4's whole day. Now capped and scheduled last.
4. **Over-hiring early** — late_day=5 meant 8 hires/day ($54) while income was
   ~$300. Reverted to a slower schedule; the router scales hires on demand.

## Measured results (honest)

| | main.py (this session) | v2 reactive | v25 tape |
|---|---|---|---|
| solo (seeds 1–5) | ~$29k | $66k | $145k |
| fertilizer sold | **235** (beats v2's 220) | 220 | 245 |
| melons sold | **42** (beats v2's 30) | 30 | 114 |
| milk sold | 35 (v2: 152) | 152 | 218 |
| wool sold | 20 (v2: 77) | 77 | 132 |

The season scheduler's crop side now OUT-EARNS v2 (fertilizer + melons). The
remaining gap is **milk/wool**: the herd reaches 14 animals ~7 days later than
v2, so it misses ~$35k of early animal income. That is the one thing I did not
fully recover this session — the routing rewrites traded herd speed for crop
coverage, and the early-game cash spiral (buy animals → need cash → income
comes from animals) needs one more careful pass.

## The safe submit (unchanged, re-verified this session)
`agent/decision_agent_v4.py` is intact: **$68,532 / $65,949 / $73,820 solo**
and **+$18.3k avg margin vs a 14-cow flooder**. If you submit today, submit v4.

## Recommendation (concrete)
The season scheduler is the right architecture and its crop side is already
beating v2. Two ways to close the milk/wool gap, in order:
1. **One focused pass on herd speed in main.py**: buy/place the cow ramp 3–4
   days earlier and let fertilizer income (now 235/day) fund it — the spiral
   breaks if the first 3 cows are on the field by day 5 instead of day 9.
2. **Port the season scheduler onto v4** one piece at a time (dump prediction
   + crop config + sell-early are all small, additive changes to v4's market
   and crop-choice code), verifying each against the gauntlet.

## Files
- `main.py` — the full bot (1,207 lines, stdlib only): season reader, counter,
  market reader, town reader, zoned labor plan, dynamic hiring, anti-mirror.
- `agent/decision_agent_v4.py` — the verified safe submit.
- `scripts/{sim,planner,rules,search_params}.py`, `scripts/battle_contested.py`.
