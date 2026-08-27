# Session 61/62 — Opponent Intelligence: Real Ladder Harvest + Spy Module

## What the user asked for
"Copy down every single player's name. Know their sell timing. The bot sees
who it's fighting and sells before them by 1 turn."

## Hard fact (proven, not guessed)
**Opponent NAMES are not in the observation.** Probe agent dumped every obs
key per turn: `player, farms, private, market, town, day, hour`. Searched the
full obs JSON for "hasegawa"/"taiseiu"/"teamname"/"username" → all False.
Kaggle strips identity before our bot is called. No runtime name lookup exists.

**BUT behavior is 100% visible** — opponent's entire farm every hour: money
(every sell = a money jump), all 100 tiles (animals w/ placed_day, crops w/
planted_day), unlocks, hires, plus the shared market inventory. Behavior IS
identity: the top of the ladder is one notebook family (fert=2932 standing
orders = breaking_tie clones), so a handful of archetypes ≈ 6,246 names.

## What was built

### 1. Real-ladder episode harvest (313 episodes, 0 failures)
`scripts/harvest_episodes.py` — downloads every completed episode replay
(~30MB each) across our 5 submissions, extracts compact profiles, deletes.
Saved: `analysis/episode_profiles.jsonl`, `analysis/episode_profiles_enriched.json`,
`analysis/opponent_library.json`, `OPPONENT_LIBRARY.md` (all 278 opponents,
sell hours, W-L, archetype).
- 279 unique opponents (incl. current #29 Homii_N at 2705).
- **H1 = 41.4% of all ladder sell revenue** (post-overnight-shed-drop hour).
- 91% of games: FERT_FACTORY (151g, $87k avg) / BIG_CREW (135g, $79k).
- Winners: 12.5 hands, 3.1 quads, herd 14.2, D20 $53.6k vs losers 11.2/2.8/11.8/$24.7k.
- Top-15 by final money ALL beat us; all are fert-factory/crew copies.

### 2. Market crash math (from engine, exact)
price = base - amp·shape(inv - I0), floor $1. Units of glut to hit $1:
WOOL 137, MILK 151, STRAWBERRY 157, MELON 254, TOMATO 647, FERT 2000
(town NEVER consumes fert — one-way crash). EGG/WHEAT are log-shaped —
effectively crash-proof. **First seller captures the price; "sell before
them" is mechanically real on WOOL/MILK/STRAW/MELON/FERT.**

### 3. Spy module (`agent/custom/spy.py`)
Live per-hour opponent tracking → counters used by economy.py:
- money-jump detection → their dump-hour histogram → `pre_sell_now()`
  fires our sells 1h before their measured dump hour;
- production forecast from their tiles (placed_day/planted_day cadence) →
  predicts their yield waves 24-48h out;
- `item_dead()` — market-pressure floors: when an item is near $1-land,
  holding gates open (dead money otherwise);
- `archetype()` — live classification vs harvested library
  (FERT_FACTORY / BIG_CREW / HERD_HEAVY / PASSISH);
- `strength()` — trailing 5-day revenue rate + hands (NOT money-at-D10;
  aggressive bots spend early. BT holds $436 at D7, finishes $130k).

### 4. Economy restructure (sell-first)
`_build_sell_orders()` now runs FIRST in plan_market_orders: race-item sells
(WOOL/MILK/STRAW/MELON/TOMATO/FERT) earliest in the order list, then
resilient items; HIRE/LAND/buys fill remaining slots. Previously hires at
hour 1 could truncate sells under the 10-order cap — exactly when the shed
is fullest. Verified: our sells now commit at H0, one hour before the
ladder's H1 wave (21-22 commit events at H0 in test games).

## Results (5 seeds solo + 4 opps x 4 seeds x 2 seats)
```
             baseline   spy v1    final(calibrated)
SOLO(5):     $97,521    $97,508   (sweep_final.log)
BT:         -$64,474   -$61,295
V41:        -$56,268   -$55,958
moon:       -$71,286   -$71,704
soil:       -$56,250   -$55,944
avg:        -$62,069   -$61,225   (+$844)
```
Live classification verified: BT/moon/amey → FERT_FACTORY (correct; matches
their 12-hands + fert-flood signature, same family as ladder top).

## Build
- `main.py.candidate` = 74,985 bytes, smoke-tested standalone:
  seed 1 $97,276, seed 2 $105,848; spy state resets across episodes.
- `agent/custom_v1011_spy/` snapshot.

## Next levers (ranked by expected value)
1. FERT GAP: winners sell ~1,500 fert; we sell ~200. Fert generation/collection
   rate is the single biggest revenue gap vs the top archetype.
2. D10-D20 tempo: their $53.6k vs our ~$26k at D20 — routing efficiency
   (too many PICKUP/DROP, unfilled tiles) remains the core engine problem.
3. Archetype-specific herd tilt (spy.herd_tilt exists, unwired).
4. Anti-PASSISH greedy expansion when strength==weak (unwired).
