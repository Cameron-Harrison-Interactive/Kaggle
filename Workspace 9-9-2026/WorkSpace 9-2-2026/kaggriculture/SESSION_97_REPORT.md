# SESSION 97 — MEASURED RESULT: removing the rescue/flush layers is a net win

## THE RESULT (the answer to "give me something that works")

**v11.13 (v11.12 minus the feed-rescue + endgame wool-flush layers) beats
v11.12 on the controlled 72-game ghost bench: +36,085 / 72 games,
1 loss flipped to a win, 0 wins regressed.**

- The two tapes are bit-identical except two runtime layers in
  `v44.gold_floor`: `_apply_feed_rescue_v2` (H18+ anti-starvation unit
  hijack) and `endgame_premium_flush` (D26-29 wool batch sell at/above base).
  Same routes, same config, same market-maker.
- In 58/72 games the layers never fire -> outcomes identical (sum +$263,
  ~$5/game, i.e. zero). In 14 games the layers fire -> **v11.13 wins 13 of
  14** (v11.12's only win there: CD_100939866, +21k, a shop-draw coin flip).
  Net across the 14: +$35.8k for v11.13.
- Flip: Michael_Timbs_100843781: v11.12 −5,034 (L) -> v11.13 +8,908 (W).
  Regressions: none.

### WHY the layers cost money (mechanism, fully traced)

The layers change which unit acts when -> the farm's build/plant layout
differs slightly -> the engine's weed RNG consumes a different number of
rolls that day -> **the next town shop draw flips** (e.g. PIZZA_SHOP vs
BRUNCH_SPOT at D9) -> a milk-consuming shop appears/disappears -> the milk
price trajectory cascades (in CD_100939866: v11.12 sold milk @ ~$168/unit,
v11.13 @ ~$19/unit, same 154 units). Deterministic per seed, but the two
tapes land on opposite sides of the shop-draw in ~14/72 games, and v11.12's
extra layer is the side that loses 13 of those 14.

This is a real measured tape difference, not noise: the layers, when they
fire, move the bot onto the worse side of the shop-draw.

### Live corroboration (confounded by matchmaking, noted)

- v11.13 slot 55829890: 161 games 106W-55L (66%), last-10 7W-3L.
- v11.12 slot 55829084: 194 games 76W-118L (39%), last-10 3W-7L.
- fresh v11.12 55917889: 55 games 36W-19L (65%) — same tape as 55829084 at a
  different rating pool, so the raw win-rate gap is pool-confounded. The
  controlled bench (same opponents, same seeds) is the clean measure, and it
  says v11.13 wins.

## What was rejected this session (measured dead, do not re-try)

| variant | 72-game delta vs v11.12 | verdict |
|---|---|---|
| wheat MM off | **−77,274** (−1,073/game), 2 W->L, 0 flips | REJECTED — the MM is a net POSITIVE |
| wheat MM threshold 1.0->5.0 | **−27,029** (−375/game), 0 flips | REJECTED — MM already at optimum |

The wheat market-maker (profit>=1.0, batch 60) is a net +~$1,073/game
feature, confirmed by A/B. The per-game "MM bleed" seen in P&L attribution
was an artifact of comparing against the opponent's MM, not a leak.

## Shippable action (needs user GO to post to Kaggle)

Replace the v11.12 slot (sub 55829084) with the v11.13 tape
(`topbots/v1113_norescue.py`). Keep the existing v11.13 slot. Net effect:
both slots run the measured-better tape. Alternatively, run BOTH layers'
removal — same file.

Live pair otherwise HOLDS; nothing else changed.

## Layer isolation — COMPLETE (all benches measured)

| variant | 72-game Δ vs v11.12 | flips | verdict |
|---|---|---|---|
| base v11.12 | — | — | |
| wheat MM off | −77,274 | 0 L->W, 2 W->L | REJECTED |
| wheat MM threshold 5.0 | −27,029 | 0 | REJECTED |
| v1112wf (remove wool flush only) | −3,535 | 0 | flush worth +$3.5k — KEEP |
| v1113 (remove both layers) | +36,085 | 1 L->W, 0 W->L | |
| **v1112fr (remove feed-rescue ONLY)** | **+39,492** | **1 L->W, 0 W->L** | **WINNER** |

**The feed-rescue-v2 layer is the liability; the wool flush is a small net
positive.** When the rescue fires it hijacks a unit -> farm layout changes
-> the weed-RNG stream shifts -> the next shop draw flips onto the worse
side (v11.12 lost 13 of the 14 fire-games). Its docstring's own history
(session 86): "hijacks hand-hours and still fails to save the animal."

## Gate tests for v1112fr (all passed)

1. **72-game ghost bench**: +39,492; loss games −123,150 -> −100,300
   (+22,850); win games +837,710 -> +854,352 (+16,642); flip
   Michael_Timbs_100843781 −5,034 (L) -> +8,915 (W); zero regressions.
2. **Mirror vs v11.12 (8 seeds x 2 seats)**: net −2,282/16 (≈0, within
   noise). 10/16 seeds bit-identical (rescue never fires). One real
   escape: seed 3 seat 1, D9, −3,513 (the rescue's genuine safety-net
   value, ~1/16 games). Seed 5 shop-draw swing −9,320/+9,456 cancels
   between seats. No systematic degradation.
3. **Solo-8 (seeds 1-8 vs pass)**: v1112fr avg 148,819 vs v1112 138,877
   = **+99,540 (+12,443/game)**. 5/8 seeds bit-identical; seed 6 +25,741,
   seed 7 −16,907 (shop-draw swings); seed 2 D29 escapes (worthless
   endgame) 1->2.

## SHIPPABLE CANDIDATE (pending user GO to post to Kaggle)

**v1112fr** (`topbots/v1112fr.py`): v11.12 with ONLY the `_apply_feed_
rescue_v2` call disabled — one-line change in the embedded gold_floor
module; routes/config/MM/flush all bit-identical. Measured:
+39,492/72 bench, +99,540 solo-8, mirror ≈ 0. Known residual risk:
occasional mid-game escape (~1/16 mirror games, −3.5k when it happens) —
already netted in the positive totals.

Action if GO: resubmit the v11.12 slot (55829084) with v1112fr as
main.py (tar = single main.py, same format as sub 55917889). Optionally
also point the v11.13 slot at v1112fr (v1113 = v1112fr minus the flush;
the flush is worth +3.5k measured).

Live pair otherwise HOLDS.

## Live-loss meta map (19 replays from today's losses, forensics)

All 8 biggest losses (−5.9k..−15k) are to **cow-heavy + wheat-MM +
aggressive endgame-dump** bots (7-11 cows, 4-6 sheep, buyW 128-207,
over-issued endgame SELL orders). Narrow-execution class — no portfolio
counter exists that measured positive in any prior session (cow-first
v11.16 line −$35-65k; goose/tomato lines dead). Not actionable this
session; recorded for the record.
- Live-loss meta profile: 19 today's-loss replays downloaded; the frozen-
  adaptive-opponent ghost degenerates (stale hand indices), so live losses
  are profiled by replay forensics instead of ghost re-sim.

## Tools added (/home/user/_ref)

- `mine_loss.py` — bit-exact market P&L profiler (validated 0 inv / 0 cash
  drift). Per-game per-product committed revenue/units, MM net, daily
  sells+revenue, herds, escapes, shops, full action tape.
- `build_v1112_layer_variants.py` — builds v1112wf / v1112fr (single-layer
  removals) bit-identical otherwise.
- `mirror_ab.py` — mirror A/B harness (variant vs base, 8 seeds x 2 seats).
- `ghost_bench_local.py` hardened: 2 workers + 3x retry on OOM/empty output.

## Engine facts confirmed (record)

- Market: 10 orders/step cap; column lockstep (both players' i-th order
  completes before i+1); SELL quoted at inv, BUY at inv-1; a failed unit
  aborts the rest of that order; town consumes AFTER market (shops %4,
  center %24).
- Shop RNG: `Random((seed*1000003)^day)`, consumed by weed spawns (per empty
  tile) BEFORE the shop draw -> layout-sensitive. This is the
  layer->shop-draw->price-cascade channel.
- Animals: HARVEST collects all yield_units (cap max_held=6); a fed+CARE day
  queues +1 bonus consumed on the next fed production day; FERTILIZER is
  collectable from every animal every day.
- STRAWBERRY: first yield D+10, every 2 days, 4 yields, a fertilized+watered
  day doubles that yield, tile dies after the 4th.

## v133 "EGGMAX" attempt (new-tape class) — MEASURED DEAD on existing platform

Design: 1 goose at (3,3) (strawberry tile sacrificed, D10H15 BUILD_COOP on
the unit's existing transit), D7H0 buy, D10H2/H8/H13 farmer pickup/place/
feed, D11-29 FEED insertions at (3,3) visits, D26-29 SELL EGG orders.
Rationale: EGG is consumed by BAKERY + BRUNCH_SPOT (2-3 egg shops in most
meta games — same demand-premium channel as peikopon's +$18.5k tomato; the
meta sells zero eggs; CD goose precedent +$13.5k).

**8-seed audit (v133a vs v1112fr h2h): FAILED.**
- eggs sold: **0** in all 8 seeds (the walk never stably fed the goose).
- COW escape D14H23 in 5/8 seeds (1,2,4,6,7) (+ pre-existing seed-3 D9
  fragility): FEED insertions sit on 1-step TRANSIT slots — the unit stays
  put on the FEED step, its whole downstream daily walk shifts one step,
  and the cow feed it was supposed to deliver hits an empty tile.
- Net vs v1112fr: −4.1k/−6.7k/+3.5k/−6.5k/−11.9k/−7.5k/−0.5k/−4.7k.
- Root cause, verified: **(3,3) has ZERO 2+-hour dwell slots on any of
  D11-D29** (every visit is a 1-step transit). A FEED can only be inserted
  at a dwell without derailing the walk. No such slot exists at (3,3).
- Verdict: single-goose on the existing platform is walk-infeasible —
  extends the v131 "blocked" verdict to the 1-goose case. Egg (and tomato)
  differentiation requires a NEW platform with a dedicated goose circuit
  (a unit whose daily job is shed→coop→coop): 2-3 session choreography
  build with per-phase verification gates (v12.0-class work).
- Quarantined: `topbots/rejected/v133a_goose.py`.

## SHIPPED this session (user GO given)

**Sub 55925101** = v1112fr (`topbots/v1112fr.py`, tar = single main.py).
Live slots now: 55925101 v1112fr (new, 662.5, accumulating) / 55829084
v11.12 (2009.8) / 55829890 v11.13 (1835.4) / 55917889 v11.12 (1786.1).

## State & next build

- v1112fr = measured best tape, now live in its own slot (A/B against the
  v11.12/v11.13 slots accumulates live evidence for the layer-removal
  verdict).
- New-tape meta-kill = requires product differentiation (egg or tomato),
  which requires a NEW platform (dedicated goose circuit / 30-tile early
  tomato farm). Recommendation for next session: commit to the 3-goose EGG
  platform build — eggs have measured demand (BAKERY+BRUNCH in most meta
  games, meta sells zero eggs) and a D0-D12 feed-geometry gate to de-risk
  the class that killed v11.16/v131/v133a.
- Engine constants snapshotted to `/home/user/_ref/engine_constants.json`
  (the sandbox recycled site-packages twice this session;
  `pip install kaggle_environments==1.32.7 kagglesdk==0.1.37` restores).
- New tooling: `/home/user/_ref/mine_h2h.py` (two-live-bot h2h with exact
  per-product P&L, escapes, sheds), `/home/user/_ref/meta9.py` in
  topbots (9-cow sibling meta representative), `/tmp/mine/v133a_route.json`
  surgery recipe.

## Session-97 continuation (after GO): goose add-on measured dead, v134 spec written

1. **v133b attempt (goose add-on on the v11.12 platform): MEASURED DEAD on
   economics, before any audit run.**
   - Verified tile windows: (3,3) empty D10H6-H14, (2,4) empty D10H6-H18,
     (2,3) unavailable (1-h window, replanted). 2 coops max.
   - The FEED must be a daily, position-neutral action at a coop tile. No
     unit dwells >=2h at (3,3)/(2,4) on any D11-D29 day (v133a audit:
     transit insertions permanently derail the unit off its walk loop ->
     0 eggs, cow escape D14 in 5/8 seeds).
   - The only safe dedicated keeper = a 14th hand hired every day D10-D29.
     Hire cost is fib(#hires_today): the 14th hire = $377/day x 18 days =
     $6.8k > egg revenue of 2 geese ($2.4-9k). 11th-13th hands ($89-233/
     day) also exceed the 1-goose economics. **The add-on class is dead on
     keeper economics, not just choreography.**
   - Engine fact confirmed (matters for all platform work): **hands reset
     at EOD** (`farm["hands"] = []` in _end_of_day) — hiring is per-day,
     hand slot k = the k-th hire of that day. The v11.12 route re-hires 9-15
     hands every day; a "keeper" is a fixed slot (e.g. hands[3], $3/day)
     that exists only on days the route hires >=4 hands.
2. **v133a quarantined** (topbots/rejected/v133a_goose.py) with audit
   evidence: 0 eggs/8 seeds, cow escapes D14 (5/8 seeds), net -4.1k/-6.7k/
   +3.5k/-6.5k/-11.9k/-7.5k/-0.5k/-4.7k vs v1112fr.
3. **V134_EGGCORE_SPEC.md written** — the only remaining new-tape shape:
   goose-SHEEP hybrid core (v11.12 funding engine + goose line funded by
   D0 buffer/D2 wheat/D6 wool; 8-10 geese + 4 sheep + 4-6 cows by D12),
   gated G1-G5 (D0-D4 / D5-D12 / full / 16-seed meta gates / shop-draw
   sensitivity). CD goose meta is the existence proof (won +$22.2k vs us
   in ep 100939868, paid the D0-D3 escape tax, netted +$13.5k eggs).
4. **meta9 16-seed**: v1112fr vs 9-cow sibling = -819/game (wash; the 8-
   seed +949 was noise). v1112fr's measured edges: +39.5k recorded-72 meta,
   +99.5k solo-8. vs the live sibling meta it is parity — the decisive
   meta edge is the egg/tomato premium, i.e. the v134 class.
5. **SHIPPED: sub 55925101 (v1112fr)** — live, 662.5, accumulating. Live
   slots: 55925101 v1112fr / 55829084 v11.12 / 55829890 v11.13 /
   55917889 v11.12.

## Next session (if GO on v134)

Author the v134 D0-D4 phase (D0 sheep+coops+buffer, D1 goose placement +
the D1 wheat-feed circuit — the critical path), run G1 (8 seeds), iterate
to a pass, then D5-D12 + G2. Walk authoring is the bottleneck; the spec's
funding plan is measured, the walk is not yet authored.
