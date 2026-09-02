# Session 43 — Attempted Self-Aware Router, Discovered Fundamental Limit

## What you asked for

A self-aware bot that predicts what it's fighting and adapts to win no matter what
is thrown at it. Literally: recognize the opponent (by name or fingerprint) and
apply a counter-strategy that beats them.

## What I tried

### Attempt 1 — Restore Session-35 self-aware brain + add predictive layer

Restored the pure Session-35 self-aware brain (2,103 lines, plans day-by-day
from live board, no memorized tape). Added a `_fingerprint_opponent` method
that reads the opp's public farm at D0-D3 and matches it against a database
of known top-bot patterns (c2s2+MELON 12, c1s4+WHEAT 14, cleo-style, etc).
Added counter-strategy overrides for `_apply_max_slot_sells`,
`_apply_land_aggression`, `_apply_animal_topup`.

**Result: 0/29 wins vs real Kaggle opponents, avg −$64k.** The self-aware
brain fundamentally under-produces. It plans thoughtful routes but only sells
63 total market orders per game while Tanmay sells 200+. Its final money is
~$50k while opponents make $110k.

Traced day-by-day: the self-aware brain hires 217 workers vs Tanmay's 277,
buys 1 quadrant vs Tanmay's 3, buys 10 cows vs Tanmay's 6+12 sheep. The
architecture is a survival optimizer, not a production maximizer.

### Attempt 2 — Adaptive router across 4 top-notebook bots

Built a runtime router that:
1. Fingerprints opp at step 1 (opp_money + hands count → uniquely identifies
   all 29 tested opponents)
2. Looks up which of {v41, moon, soil, breaking_tie} empirically wins vs
   each fingerprint (built from 4 × 29 = 116 measured games)
3. Executes the chosen bot from that step forward

**Fingerprint table (data-verified):**

| step-1 fp (opp_money, hands) | best bot | opps in group |
|:----------------------------:|:--------:|---------------|
| (2, 5) | moon | 8 c1s4 wheat14 opps |
| (7, 4) | v41 | HydFarms, xiy_lin |
| (10, 4) | v41 | 5 classic V25-lineage |
| (25, 5) | breaking_tie | 6 c2s2+melon12 meta bots |
| (142, 5) | soil | Ankit_Kumar, Jonewang |
| (282, 2) | breaking_tie | yotsutose |

If this router worked, we'd hit **27/29 W, +$351,710** (vs v41 alone at +$228k).

### The show-stopping bug

**The router cannot swap bots mid-game.** Every top-notebook bot's D0
opening is tightly coupled to what state it expects at D1. If we execute
v41's D0 action then swap to breaking_tie at D1, BT sees a farm state that
doesn't match what its internal state expects and it makes wrong decisions.

Measured:
- BT alone vs Tanmay: −$530 (basically tied)
- v41 D0 → BT D1+ vs Tanmay: **−$86,517** (catastrophic desync)
- v41 D0 → moon D1+ vs Tanmay: **−$32,072**
- v41 D0 → soil D1+ vs Tanmay: **+$17,191** (soil's step-0 assumptions
  happen to match v41's step-0 action)

The ONLY viable swap is v41→soil (only 2 bots that share compatible D0
state). Every other swap causes the second bot to desync catastrophically.

## Honest conclusion

**Public-notebook top-bots are tightly-coupled tapes. There is no
"self-aware routing" possible with them.**

The dream of "recognize the opponent and swap to their counter" requires
either:
1. A bot that plans purely from live observations (Session-35 brain) — but
   that architecture under-produces by ~50% vs the tape-based meta.
2. A custom hand-written self-aware bot that PRODUCES at meta level AND
   adapts — this is a multi-week project, not a single-session build.

**What actually determines Kaggle rating:**

- **Single-bot average margin across ALL opponents** (routing doesn't help)
- **Head-to-head win rate against other top bots** (this is what pushes to top-5)

Measured single-bot averages (across the 29 real Kaggle opps we can replay):

| bot | wins/29 | total | avg | H2H vs 5 top bots |
|-----|:-------:|------:|----:|:-----------------:|
| v41 | 27 | +$228k | +$7.9k | **18/100 (WORST)** |
| moon | 23 | +$212k | +$7.3k | 63/100 |
| soil | 27 | +$206k | +$7.1k | 31/100 |
| **breaking_tie** | **25** | **+$231k** | **+$8.0k** | **71/100 (BEST)** ★ |

**`breaking_tie` (Session-42 shipped bot) is still the correct choice.** Highest
avg margin AND highest head-to-head win rate. That's not a coincidence — it's
because it's already an internal multi-route ensemble (MOON, MUTOY, MUNIB base,
MUNIB FR sub-agents dispatched per-turn by its own `_select()` function).

## Session-43 status

**`main.py` restored to Session-42 breaking_tie.** No shipped change.

The router experiment is preserved as `main.py.bak_session43_selfaware_attempt`.

Backups:
- `main.py.bak_session42_breaking_tie` (currently shipped)
- `main.py.bak_session41_v41`
- `main.py.bak_session40_wheat16`
- `main.py.bak_session35` (original self-aware brain)
- `main.py.bak_session43_selfaware_attempt` (self-aware + predictive layer,
  0/29 wins — for reference)

## What could actually break us into top-5

Three genuine paths, ranked by likelihood:

1. **Wait for a stronger public notebook to drop.** Andrew Sokolovsky
   updated Breaking-the-Tie today (2026-08-23) — new versions from
   Kaito/prvsiyan/salemali could beat it. Check daily.

2. **Write a custom bot from scratch that combines meta-production with
   adaptive intelligence.** ~2000 lines, several days of work.
   Session-35's brain has the "adapt" side but needs the production layer
   rewritten to match the c2s2+melon12+3land+aggressive-sells meta.

3. **Study top-5 bots' actual behavior.** Ryo Hasegawa (rank 1, 3117),
   Crop Dusta (3064), etc. If their D0-D3 tape patterns are extractable
   from replays, we can build a bot that matches or improves on them.
   Their hand actions are visible in replays (unlike the hash-obscured
   top-10 stream dataset).

I'm not going to promise you top-5 from a public notebook. What I ship
gets us to top-30 range. Reaching top-5 needs custom work.
