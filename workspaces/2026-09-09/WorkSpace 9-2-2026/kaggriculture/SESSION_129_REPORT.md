# SESSION 129 — Tue 2026-09-08 (night)
## The choreography campaign: 9 builds tested, search space now definitive

**LIVE:** 56079632 router **2483.7** · quota 3 left, lifetime 70. **NO POSTS.**

---

## What you asked for — done, with the tools to prove it

You said: do our own choreography. This session built the full pipeline and ran it to its conclusion:

1. **RECORDER** (labor_lab/recorder.py): logs every step — actions, positions, tile states, shed, money. 719-step trace saved (labor_lab/trace_404.json).
2. **OPTIMIZER** (labor_lab/optimizer.py): recomputes each day's min-walk routing for the SAME tasks (arcs + nearest-neighbor chains).
3. **THE MEASUREMENT**: same 90-100 daily tasks — our planner burns 180-230 walk steps, optimal routing needs 50-70. **2,611 recoverable steps = ~1,305 extra tile-ops = roughly double farm throughput.** The prize is real.
4. **9 attempts to realize it online — ALL FALSIFIED** (below). The offline bound is unreachable through the planner's greedy-step architecture because the "wasted" walk is load-bearing: deadline insurance (weak priorities crash the farm to $25k — v36a/b), carrying logistics the optimizer ignores, and tasks that only appear mid-day.

## The 9 falsifications (solo means vs v32.1's $79.7k)

| build | idea | result |
|---|---|---|
| v35 | task-arc territories, per-step | $44.9k — territory thrash |
| v35.1 | day-stable angular wedges | $67.4k — walk unchanged, completion down |
| v36a/b | priority weight 6→2/3 | $28-30k — deadline misses, farm collapse |
| v37 | animal-crew/field-crew role split | $57.8k — role rigidity breaks carrying chains |
| v38 | lean start (5 hands pre-d8) | $76.2k — d1-7 slack is productive |
| v40 | plan-then-commit full-day routes | $48.6k — h0 routes go stale intraday |
| v41 | **router labor + our adaptive sell brain** | H2H 0-10, $51.7k vs $125.8k |

**v41's lesson (important):** in tape-vs-tape play, holding products RAISES the prices your dumping opponent collects — you subsidize him — while his dumps keep your take-profits from firing, so your cash floor sells at crashed prices anyway. The tape's recorded sell cadence is already adapted to tape-dump dynamics. The market layer cannot be improved by graft either.

## The meta fight (new this session)

- **v39 sim-twin** built (twin archetype on our engine: 6C/1S/0G, wheat-heavy, no tomato, land d6/d10, desk-60): $73.9k solo.
- **v32.1 vs sim-twin: 6-4 us** ($57.9k vs $56.9k) — we edge the meta archetype on even labor.
- **Router vs sim-twin: 10-0, $130k vs $34k** — taped labor annihilates planner labor at identical schedules. The real twins (2700-2900) sit above our router (2483) on the same advantage.
- Mining correction: earlier "whe22/str13" counts were op-occurrences; twins actually buy ~100 wheat/25 strb/11 melon seeds — their farm is our scale; the herd is what's tiny (6-7 animals vs our 16).

## The definitive map

Four independent proofs (keiz replay, v30 port, planner surgery ×9, v41 graft) all point at one wall: **the game is won at the labor layer; taped choreography is 2-4x production; everything else (schedule, herd, market, desk) moves results ±10%.** Our planner cannot be patched to tape-class labor — it must be replaced by recorded-then-optimized labor of our own.

## The one remaining build (next session, with today's toolchain)

**Self-tape library, farm-state-keyed (not seed-keyed):**
1. Record v32.1 across ~20 seeds (recorder ready).
2. Cluster days by farm-state signature (tile layout, herd, task set).
3. Optimize choreography per cluster (optimizer ready) → tape LIBRARY.
4. Live agent: match current farm-state signature → play optimized tape; mismatch → v32.1 planner fallback; market brain adaptive throughout.
This is the only architecture that survives replay (our own assumptions) and carries the labor win. If it clears solo $100k+ then H2H vs router ≥60%, it's the submission.
