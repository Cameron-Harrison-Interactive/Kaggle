# WAR MODEL — Intel from 375 real ladder episodes (2026-09-09)

Corpus: 375 episodes = all 55 of our games + top-40 ladder teams' recent episodes
(~750 player-sides). Source pipeline: `kaggle competitions team-submissions →
episodes → replay` (see harvest.py). Compact intel: intel/eps/ep_*.json.gz.

## 0. ENGINE FACTS CONFIRMED FROM SOURCE + REPLAYS (war-enabling)
- **Market is SHARED in H2H** — same inventory object in both obs. Price war is real.
- **SELL orders execute from the SHED** via `{"market": [["SELL", item, n]]}` — NO unit
  labor, no walking. 10 orders/turn, each `["SELL", item, n]` drains n units one-by-one.
- **Both players' orders interleave 1:1 per unit** (lockstep). Equal queues split the
  price decay ~50/50. Whoever queues MORE volume eats more of the good price.
- **BUY_PRODUCT only works for WHEAT + FERTILIZER.** "Buy all crops cheap" arbitrage is
  only possible on those two. (Wheat rebound buy IS possible.)
- **obs.farms exposes BOTH farms** (enemy money, tiles, crew, animals every hour).
  Enemy obs.private (shed/seeds) is hidden. market.inventory (shared) is visible.
- **reward = farm money at step 719** (episodeSteps=720 = 30 days × 24 h).
  Anything in shed/inventories at horn = $0. Top bots already full-dump: median value
  left in shed $0; only 1% of players leave >$2k.
- Town consumption: shops eat 1-2 of their products every 4 steps; town center eats 1 of
  everything (except FERT) every 24 steps. Shops unlock every 3 days, max 8 instances.
- Sales at $1 do NOT add inventory (floor sales are free for the price — no further crash).

## 1. PRICE MODEL (exact, from engine source)
price(inv): I0=10000, floor $1.
- inv > I0 (glut): price = base − amp·f(inv−I0); inv < I0 (scarcity): base + amp2·f(I0−inv)
- glut depths reachable by selling X units over I0:
  WHEAT (log):    +100→$21, +400→$20, +10k→$17  **CANNOT go below ~$15 — log cliff too gentle**
  CARROT (sqrt):  +300→$15,  +900→$1
  STRB (linear):  +50→$24,   +62→$1    **easiest big-item crash**
  MELON (sq):     +100→$150, +141→$51, +160→$1  (NO town drain — stays dead forever)
  MILK (linear):  +50→$55,   +94→$1
  WOOL (sq):      +57→$10,   +59→$1
  EGG (log):      +200→$41   **effectively uncrashable**
  FERT (linear):  +250→$1

## 2. WHO EARNS WHAT (revenue mix, from units×daily price)
**Our mid-tier opponents (55 our-episodes):** WHEAT 33.4% · WOOL 16.9% · MELON 13.9%
· FERT 11.7% · STRB 11.2% · MILK 9.6% · carrot 1.5% · egg 1.2% · tomato 0.7%.
→ User is right: our bracket = wheat machines + animal/wool + melon.
**Top-40 meta (median player-side):** STRB 21.9% · MELON 14.4% · MILK 13.1% · FERT
11.4% · WHEAT 10.6% · WOOL 9.2% · carrot/egg/tomato ~2-3% each.
→ Top bracket = strawberry FIRST, then melon/milk/fert. Wheat is minor at the top.

## 3. MARKET REALITY (median inventory paths across corpus)
- WHEAT: drains BELOW I0 all game (d29 median −311) → ends $40 med (0% of games <$10).
  Late-game wheat is SCARCE — every wheat we sell late both earns and caps that premium.
- MILK: +62 by d29 → $9; 51% of games end <$10. Self-crashes from bots' own volume.
- WOOL: +49 → $5; 55% end <$10. Self-crashes.
- FERT: +493 → $1; 73% end <$10. Fully crashed — but ~290 units still sold (early sales
  at $60-100 are real money; late = $1 garbage).
- MELON: +115 → $120 med (only 3% crash). **MELON HOLDS VALUE** — best big crop.
- STRB: +20 → $85 med (8% crash). Holds unless someone forces it.
- EGG −113 → $57. CARROT −220 → $45. TOMATO −185 → $83. All end scarce-ish.

## 4. TIMING
- Winner money curve (median): d5 $0.8k, d10 $13.6k, d15 $22.6k, d20 $40.4k, d29 $64.5k.
  **37% of final gold is earned after d20** — engines stay cash-hungry all game.
  F4-style bots run ~$100-2k until d10 (thin ice window) then compound.
- Median sell day: MELON 10.2 (first wave at ripen!), FERT 15.5, WOOL 18.6, MILK 19.0,
  WHEAT 19.3, STRB 21.6, EGG 22.8, CARROT 28.8 (pure endgame dump).
- Sell hours: top bots either h0-h1 (morning, from yesterday's shed) or h14-23 (evening,
  after same-day harvests). Mid-tier bots trickle all day.
- Winners vs losers: SAME crop mix, SAME crew (12), SAME animals (17), SAME sell volume.
  Winners just execute tighter (money 94.6k vs 84.5k median). The meta is CONVERGED —
  edges now come from pricing/timing/labor efficiency, not build order.

## 5. THE WAR MODEL (v49 spec)
Principle: we don't need max gold — we need OUR gold > THEIRS. Every $1 of price we
destroy on an item they rely on is a $1 we keep (differential). But never burn more of
our own revenue than we deny.

1. **WHEAT FLOOD (their 33%)**: sell ALL wheat daily from d0 h0 except a 2-day feed
   reserve (reserve→0 from d27). Our volume (NW+NE wheat quads, ~30-60/day) + their
   volume > town drain (≤31/day) → pins wheat ~$20-25 instead of $35-46 late.
   Denial ≈ $5-10k on their ~300-500 units; our wheat still pays (volume at $20+).
2. **FIRST-SELLER ADVANTAGE**: at h0 sharp, sell yesterday's shed stock BEFORE their
   morning/evening dumps (lockstep 1:1 — queue max volume early and often). This is
   free: market orders need no units. Our standing all-day sells keep pressure on.
3. **MELON/MILK/WOOL/STRB/FERT: sell max daily, no self-pacing** (v48 SELL_CAP was
   misdirected — sell pacing helps SOLO score, hurts the war). Exception: sell our own
   first waves greedily too (they're at high prices anyway = max revenue + still adds
   glut pressure). Fert: collect + sell every single day (early fert = $60-100).
4. **MELON wave-2 denial**: their wave 1 (d10-13, $250→150) is unstoppable — we match it
   (sell ours first at h0). By their wave 2 (d20+) our + theirs volume has melon ≤$50 →
   their wave 2 earns ~nothing. Melon has NO town drain — once dead, stays dead.
5. **EGG = our uncrashable income** (log cliff): goose eggs hold $40-57 all game.
   Our engine anchor: wheat + eggs + early melon wave + fert-before-crash.
6. **ARBITRAGE (wheat/fert only)**: if wheat price < $18 (someone over-dumped), buy up
   to N and resell ≥$22 next days (town drain guarantees rebound). Only with spare cash
   ≥ 2× hire budget.
7. **ENDGAME**: d26+: stop planting anything that can't ripen by d29 (melon needs d10-12
   → last plant d17; strb d10 + ongoing → last plant ~d25 for one pickup; wheat d2-4 →
   plant through d27). d28 h0 + all hours: sell EVERYTHING (feed wheat too, animals'
   products same-hour they're collected). Match the field: median bot leaves $0.
8. **SPY ob.farms every hour**: enemy money (are they cash-choked?), enemy crew/animals
   (their future sell volume by item → what to crash), enemy tiles (their harvest
   calendar is as predictable as ours).

## 6. NUMBERS TO TUNE IN BENCH
- wheat feed reserve: 2 days × animals.
- melon plant cutoff: d17 (first_yield 10 + slack).
- strb plant cutoff: d24 (one last pickup d28-29).
- wheat flood: does pinning at $20 vs $40 cost us more than it denies? (Bench H2H both ways.)
- Crash strb actively ONLY if enemy strb share > 15% (spy on their tiles: strb crop count).

## 7. HARVEST/REPLAY PIPELINE (for future sessions)
```
export KAGGLE_API_TOKEN=KGAT_...   # nosiru
python3 -m kaggle competitions leaderboard kaggriculture -s --page-size 200 --format json [--page-token TOK]
python3 -m kaggle competitions team-submissions <teamId> --format json     # active subs + scores
python3 -m kaggle competitions episodes <submissionId> --format json       # episode ids (recent ~100)
python3 -m kaggle competitions replay <episodeId> -p /tmp/replays -q       # ~25MB, ~2s
```
Scripts: intel/harvest.py (batch dl+extract+rm), intel/extract.py (replay→compact),
intel/analyze.py (team table, winners-vs-losers, market paths). Queue state: queue.json,
done set = eps/*.json.gz. lb_full_0909.json = all 8,351 teams. WE = "Harrison Interactive"
teamId 16668748, rank ~5,776. NOTE: team-submissions/episodes/replay DON'T burn the
5/day submit quota.
