# Session 3 — 8-20-2026: the "counter" layer + the real test

## Your instinct, confirmed and built
You said: don't optimize solo gold — beat the *other bot's* gold by any margin
("20 extra gold because we sold sooner or picked a different animal"). That is
correct, and it's now built: **`agent/decision_agent_v4.py`**, which reads the
opponent's PUBLIC farm every turn and adapts.

## What v4 does (all deterministic, all free)
1. **HERD TILT** — when the opponent runs a meaningfully cow-heavier herd (the
   common ladder build), milk is about to crash for everyone but wool stays
   ours. We swap 2 cows → 2 sheep *within the same total headcount* (crew never
   overloaded). We deliberately do NOT tilt toward cows vs a sheep-flooder —
   wool floors so fast a balanced herd wins there.
2. **FRONT-RUN SELLS** — we can see the opponent's unharvested yield sitting on
   their tiles. When their milk/wool/melons are about to hit the market, we
   sell ours immediately — one turn earlier = our whole batch gets the
   pre-glut price and softens the market for their dump.
3. **CROP-MIX COUNTER** — opponent heavy in crash-prone strawberry/melon →
   tilt our planting toward glut-robust wheat.

## Verified results (head-to-head margins, 5 seeds × 2 seats)
| Opponent | v2 (no counter) | v4 (counter) | delta |
|---|---|---|---|
| mirror clone (10 cow / 4 sheep) | +$0 | **+$1.7k** | +$1.7k |
| cow-flooder (14 cows) | ~$0 | **+$13.9k** | +$13.9k |
| sheep-flooder (12 sheep) | +$5.5k | **+$6.4k** | +$0.8k |
| goose-flooder (10 geese) | +$37.8k | **+$38.2k** | +$0.4k |

- **No regressions**: every matchup ≥ v2; total +$16.9k across the gauntlet.
- **Zero cost vs PASS**: v4 vs PASS is byte-identical to v2 (the counter is a
  no-op when there's nothing to counter).

So for the **exact scenario you described — "they are running clones with
modifications"** — the counter layer now wins margins on top of the economy.

## The hard truth (real top-10 test)
I extracted a REAL top-10 opponent from your repo — **"Aster" (amaterasuuuuu's
shabby-farm)** — and battled it:

| | vs Aster |
|---|---|
| Aster vs PASS | **$161,383** (higher than our own v25 tape's ~$145k) |
| v2 vs Aster | −$73,306 avg (0W-4L) |
| v4 vs Aster | −$78,857 avg (0W-4L) |

**The counter does NOT close this gap, because the gap is the economy, not the
matchup.** Aster runs a *dated-portfolio + ledger-replay planner* (every
strategic choice is a dated "commitment" replayed through a cash/labour/market
ledger; only commitments that survive are executed). Our reactive agent
(~$68k) is a different, weaker class than that (~$161k). No amount of
"counter their build" can make up a 2.4× economy difference — countering only
pays once the economies are comparable.

This actually confirms what your earlier chat logs were circling: the
**ledger-planner** was the identified path. Aster IS a ledger planner.

## What I recommend next (in order)
1. **Keep v4 as the counter layer** — it's proven +$16.9k on clone matchups
   and costs nothing. Submit/run it against the ladder's clone armies.
2. **Build the ledger planner** (the real economy gap). Aster's design is the
   blueprint: dated commitments (each crop/animal is a timed plan owning its
   capital, tiles, labour, orders) + a ledger that replays them and keeps only
   what survives. This is the ~$161k class of agent. It's a bigger build —
   say the word and we start it.
3. **Tune the counter against Aster-style builds** once (2) exists, since
   countering only matters at economic parity.

## Files (download for your PC)
- `agent/decision_agent_v4.py` — the counter agent (submits like v2/v3).
- `scripts/battle_contested.py` — head-to-head margin harness vs archetypes.
- `top10/shabby_farm_agent.py` — the extracted real top-10 opponent (Aster),
  ready to battle against locally:
  ```python
  from kaggle_environments import make
  import decision_agent_v4 as v4, importlib.util
  spec = importlib.util.spec_from_file_location("a", "top10/shabby_farm_agent.py")
  aster = importlib.util.module_from_spec(spec); spec.loader.exec_module(aster)
  v4.set_params(dict(v4.V4_DEFAULT_PARAMS))
  env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
  env.run([v4.agent, aster.agent])
  ```
