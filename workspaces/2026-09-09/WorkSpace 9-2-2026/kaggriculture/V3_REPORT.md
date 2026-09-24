# Session 2 — 8-20-2026: the "full AI bot" foundation + live agent

## Your question, answered
**Do we need to train a model? No.** "Map the game play-by-play, never miss
anything, think on its feet" is *planning*, not machine learning — and in a
fully-observable, deterministic game, planning is strictly stronger:

| What you asked for | The right tool | Status this session |
|---|---|---|
| Never miss watering/feeding/fert | capacity-aware router | built (planner) |
| "Miss 1 crop → save 30 / add 1 → miss 6" | lookahead by simulation | built + verified |
| Read the game, adapt per match | live state reconstruction | built + verified |

Every top-10 bot (incl. #1 KAWASHIGI) is hand-built + search, not a trained
model. Training would need millions of games and still lose to exact planning.

## What I built (all verified)

### 1. `scripts/sim.py` — exact, fast simulator
Drives the **official engine's own interpreter** (imported, not re-copied), so
rules are bit-for-bit identical. `clone()` branches any game state; `step()` is
~40 µs. **VERIFIED**: replays of real games match on final money AND every
market price at every day boundary (seeds 1–5).

### 2. `GameSim.from_obs(obs)` — reconstruct a live game mid-match
Because live observations scrub the RNG seed, I added exact state
reconstruction from an observation. **VERIFIED**: with a known seed it replays
identically (money + all prices). With a fabricated seed (what live play gets),
future weed/shop rolls are approximate — but identical across all cloned
options, so *relative* what-if comparisons are reliable.

### 3. `scripts/planner.py` — the thinking layer
- `daily_capacity(obs, expected_hires)` — "never miss anything": lists the
  critical tasks (feed/water/fert), estimates worker-steps, verdict OK /
  OVERLOADED.
- `what_if(...)` — "think on its feet": clones the game, simulates candidate
  decisions to the end of the game (opponent frozen), returns $ outcome.
  Supports `terminal_value` (end-of-horizon asset valuation) and
  `opp_pass` (cleanest marginal measurement).
- `liquidation_value(...)` — money + shed + seeds + crops (animals excluded:
  they're illiquid).

### 4. `agent/decision_agent_v3.py` — the live bot
v2 (the $68.5k clean-room economy) + planning layers, same `agent()`/
`set_params()` interface:
- **Capacity layer** (every morning): estimates critical workload; hires extra
  hands if the crew can't keep up.
- **Expansion layer** (opt-in): `decision_mode="direct"` computes an animal's
  marginal value with the engine's exact price function (price elasticity);
  `decision_mode="whatif"` uses the full simulator.

**No regression, verified:** with expansion off (default), v3 == v2 exactly on
all 10 seeds ($66,302 avg).

## Honest findings (what worked, what didn't)
1. **The herd is already right-sized.** v2's ramp (10 cows + 4 sheep) is the
   economic optimum. Even with capacity, a 16-cow herd *loses* money (milk
   price gluts to $1) — it's a price problem, not a labor problem.
2. **Capacity layer is a safety net, not a driver.** A crew of 4–8 can service
   14–22 animals' critical needs within 24 turns, so defensive hiring never
   fires at current scale. It protects you if the search cranks targets up.
3. **The marginal-animal decision is the hard part.** Two honest failures:
   - `whatif` mode: ±$1–2k noise from the fabricated shop schedule swamps a
     ±$300 animal decision.
   - `direct` mode: over-values fertilizer (assumes 100% collection; the crew
     actually misses ~25%). Over-buys as a result.
   → Both left OFF by default. This is exactly the "price elasticity" gap the
   old price_predictor.py was meant to fill.

## How to test on your PC
```
pip install kaggle-environments==1.32.6
# baseline (should print ~$68,532 on seed 1):
python3 agent/decision_agent_v3.py

# watch the thinking layer (capacity + what-if demo):
python3 scripts/demo_planner.py 1          # or 2,3,4...

# verify the simulator against the real engine:
cd scripts && python3 -c "from sim import verify_sim; verify_sim([1,2,3])"

# turn the live expansion layer on (experimental):
#   in agent/decision_agent_v3.py set "expansion_enabled": True
#   and choose "decision_mode": "direct" or "whatif"
```

## Next steps (my recommendation, in order)
1. **Sell-timing via the exact price function** — the "know when to sell so we
   save 30 not lose 6" piece. Deterministic (no simulation), high value; the
   pieces exist (price_predictor.py + `_avg_sell_price`).
2. **Fertilizer collection model** — the missing term that makes the direct
   estimator accurate (assume ~75% collection, or let capacity drive it).
3. **Spatial locality** (assign workers to quadrants) so crops can scale from
   ~16 toward v25's 50+ — the main remaining gap vs the $145k tape champion.
