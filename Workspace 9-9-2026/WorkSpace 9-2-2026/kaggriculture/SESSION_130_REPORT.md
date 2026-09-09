# SESSION 130 — Wed 2026-09-08 (late night)
## The from-scratch tape campaign: 8 builds, every crash root-caused, new best build installed

**LIVE:** 56079632 router **2483.7** · quota 3 left, lifetime 70. **NO POSTS.**

---

## What was built tonight (in order)

| build | architecture | solo 5-seed | what broke / what it proved |
|---|---|---|---|
| v42 | checkpoint route planning (h0/6/12/18) | $59.2k | unpack crash at d1 boundary (single-unit branch stored 6-element tasks, not (op,pos) pairs) — kaggle **swallows exceptions and benches the agent silently** ($1,190 signature) |
| v43 | full-day plan at h0 | $65.4k | carrying-gap deadlock: `_route_next` returned None without advancing → units PASSed forever, feeds skipped |
| **v43c** | **routes disabled (isolation test)** | **$80.0k** | **THE KEY RESULT: execution layer (locks+urgent+greedy) is sound and ≥ v32.1 — the routes were the entire problem** |
| v44.1 | phased routes (everyone pen-share → arcs) | $39.8k | found the **h0-zero-hands bug**: routes built at h0 when the daily reset means no crew exists yet — multi-unit routing never ran; the farmer's garbage route was −$15k |
| v44.2 | + contiguous wedges | $722 | pinwheel→wedge fix, but early-game bleed (no fert collection → no income → no hires → death spiral) |
| **v45** | **clean greedy + sectors + locks + urgent interrupts** | **$80,054** | **INSTALLED — new best own build; worst-case $73.5k vs v32.1's $68.2k (urgent interrupts save the tails)** |

**Gates:** v45 vs sim-twin **6-4** ($58.6k vs $59.4k — meta gate holds). v45 vs router **0-10** ($21.9k vs $133.6k — labor wall unchanged, as measured all week).

## The debugging method that changed tonight

**kaggle_environments swallows agent exceptions** — a crashing agent plays PASS for the rest of the game and finishes "DONE" with ~$1,190. Every flat-low score tonight was a hidden crash. The fix: a **manual stepper** (env.step loop calling the agent directly with traceback) — finds the exact line in seconds. Five real bugs found and fixed this way (unpack crash, carrying deadlock, h0-hands timing, orphan call, h2h seat bug). Never diagnose a low score without stepping.

## Engine facts locked in (from source, verified)

- **Daily reset**: farmer → (4,4), hands cleared, inventories force-dropped to shed (overflow discarded), flags reset, weeds spawn (rng, seed-keyed). **Consequence 1:** the h0 task set is complete from h1 (after hires land). **Consequence 2:** errors do NOT cascade across days — every morning re-syncs from real state. This is what makes day-by-day offline script generation viable.
- Hires are a daily rental (fib: 1,1,2,3,5,8,13,21,34,55,89,144 → 12 hands = $376/day).
- Shed = 4 center tiles (4,4),(5,4),(4,5),(5,5); all quadrants unlockable ($1k/$2k/$4k) → 100 tiles.
- Corrected labor ceiling: the offline 0.6 walk/prod bound was an artifact (pen cluster + no fan-out cost). True optimum ≈ 1.2–1.4; we run 1.76. **Recoverable: +$10–20k, not 2x.**

## Where the from-scratch tape actually stands

The route-based day-plan architectures (3 variants, all measured worse than greedy) fail because live intraday coordination (carrying chains, coverage, early-game cash flow) is exactly what the co-adapted greedy handles for free. The remaining correct architecture is the one the daily reset enables:

**Env-oracle day-by-day script generator:**
1. Play the partial script in the real env → capture day D's true morning state.
2. Generate day D's full action set offline from that state — chores routed with hindsight, carrying chains pre-simulated (no live coordination at all).
3. Splice, repeat for D+1. Errors are day-local; repair loop converges.
4. Result: a literal 719-step script (the "write every move" artifact) + live market wrapper for opponent adaptation.

All machinery now exists: recorder, optimizer, stepper, isolation harness. What was missing every prior attempt (state fidelity) is solved by construction — the env IS the state source.

## Standing numbers

- Own best: **v45 $80,054** (prev v32.1 $79,687)
- Router (LIVE): solo $163–197k; H2H vs our builds $130–140k
- Sim-twin (meta): $73.9k solo; v45 beats it 6-4
- Falsified tonight: checkpoint routes, full-day plans, dedicated crews, phased pinwheels, phased wedges (5 architectures, each with measured failure mode)
