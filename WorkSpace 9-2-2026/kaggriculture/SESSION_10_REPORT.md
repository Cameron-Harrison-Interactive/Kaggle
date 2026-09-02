# Session 10 — 8-20-2026: counter tuning — what was measured, what works, what doesn't

## What you asked: tune the counter against the archetypes + the v25 tape

I ran main.py's new counter against the archetype gauntlet, measured it
against a counter-OFF baseline, and instrumented every matchup. Here is the
honest result.

## 1. The counter's biggest bug — found and fixed

Instrumentation of the cowbot matchup showed the counter was **reacting too
late and misclassifying**:

- Day 6: the classifier called the cowbot "crop-heavy" (it hadn't ramped cows
  yet) → we bought MORE cows into a coming milk glut.
- Days 8-12: no classification at all while the cowbot ramped 2 cows/day.
- Day 14: correct "animal-heavy" fired — but we'd already bought 8 cows.

The fix: **specialists reveal themselves early by what they DON'T have**.
- cowbot = 3+ cows and 0 sheep → pivot to sheep (wool is ours alone).
- sheepbot = 3+ sheep and ≤1 cow → pivot to cows (milk is ours alone).
- mirror (4+ cows AND 2+ sheep) → geese (eggs are the untapped product).
- goose specialist (3+ geese) → do NOT join their egg glut.

Detection now fires from day 2, before either side has flooded anything.

## 2. Measured effect of the counter (vs counter-OFF baseline)

| Opponent | counter OFF | counter ON | counter's effect |
|---|---|---|---|
| mirror (v2 clone) | −$18.0k | −$17.5k | +$0.5k |
| cowbot (14 cows) | −$7.4k | **+$2.5k** | **+$10k** |
| sheepbot (12 sheep) | −$13.3k | −$12.6k | +$0.7k |
| goosebot (10 geese) | −$6.2k | −$1.7k | **+$4.5k** |

The counter works — it just can't out-earn a weaker base economy.

## 3. The honest problem (why we still lose the mirror)

The mirror is the ladder-clone case, and we lose it −$17.5k. The reason is NOT
the counter — it's the **base economy**: main.py solo is $44k vs v2's $68k.
When two identical builds collide, the bigger economy wins. Instrumentation
showed exactly where main.py is behind v2:

| | main.py | v2 |
|---|---|---|
| milk sold | 102 | **152** |
| melon sold | 6-12 | **30** |
| strawberry sold | 16 | 16 |
| fertilizer sold | 224 | 220 |

Two gaps: (a) the herd produces ~33% less milk (our animal chores are
scheduled, not reactive, and miss harvest ticks), and (b) the melon economy
is ~5x smaller (few seeds bought + crops planted too late to mature).

## 4. What I broke and fixed this turn (being straight about it)

While tuning I experimented with the router (animal-pool restriction, seed
windows, replant scheduling) and **regressed the solo economy from $64k to as
low as $10k**. I found and reverted the regressions — the last one being an
inconsistent role split where only some animal chores went to the animal
pool, starving milk collection (milk 39 → 102 after the fix). The bot is back
to $44k solo and climbing, but I did not recover the full $64k this turn.

## 5. The bottom line

- **The counter is tuned and measured**: early specialist detection + pivots,
  worth +$10k vs cow-flooders and +$4.5k vs goose-flooders.
- **`agent/decision_agent_v4.py` remains the safest submit** — it was verified
  at +$16.9k across the gauntlet with no solo regression, and this turn's
  tuning is best ported onto it one change at a time (each verified).
- **The gap to the leaderboard's 60-crop tape bots is the base economy**, and
  the honest conclusion across every session is the same: it needs the
  full-season per-worker scheduler (the thing I keep mis-naming a "route
  compiler" — it runs in the bot, re-planned daily from the live board, and it
  is the ONLY remaining lever). Everything else — counter, market reader, town
  reader, anti-mirror, dynamic hiring — is in main.py and measured.

## Files
- `main.py` — the full bot (counter + economy + router, 1,200 lines, stdlib only).
- `agent/decision_agent_v4.py` — the verified counter (safe submit).
- `scripts/{sim,planner,rules,search_params}.py`, `scripts/battle_contested.py`.
