# SESSION 90 REPORT — v11.16 cow-first: built, benched, and its structural wall

Date: 2026-08-29. Predecessor: STATE_89.md (v1c checkpoint, $52k seed-1 solo).

## What was built this session

1. **v1116d** (`topbots/v1116v1d.py`, builder `_ref/build_v1116d.py`):
   v1116v1c + the D6-D10 cow wave re-added (s154 COW1, s168 COW2, s192 COW1,
   s248 COW2), SW LAND restored to s252 (v11.12 position), D13 land removed,
   D15 cow dropped, D10 hire count restored to 12 (the v1c 9→4 reduction broke
   the 12-hand D10 choreography — hand spawns are a function of hire count, so
   h4-h11 walks shift; melon harvests + the (3,5)/(4,5) pair circuit hit wrong
   tiles), and a NEW D11 h1 placement circuit (D11 cow → (5,3), fed same day).
   Suffix routes got the cow-first D0 prefix copied + D6-D9 cow purchases
   stripped (yarn sheep purchases kept; bakery keeps s248/s252).

2. **v1116e** (`topbots/v1116v1e.py`): v1116d + s24 restored to v11.12's
   [WHEAT seed 2, WHEAT product 4] (v1c had cut WHEAT product 4→1).

## Verified results (clean isolated processes, seed set [1,3,5,7,9,11,13,19])

| build  | solo avg | solo escapes | vs v1112 (h2h) avg | h2h escapes |
|--------|----------|--------------|--------------------|-------------|
| v1112  | $140,237 | 0            | —                  | 0           |
| v1116d | $95,664  | 0            | $19,376            | D3 EVERY seed |
| v1116e | $95,429* | seed3 D4 esc | $63,981 (seeds 1,5,11) | 0 on 1,5,11 |

*seed 3 solo broke: $38,028 + D4 escape (the s24 fix traded seed-3 for 1/9/13/19).

v1116e h2h detail: seed1 $92,163 vs $153,415 · seed5 $42,335 vs $67,904 ·
seed11 $57,444 vs $90,290 — all 0 escapes, 8c/1s placed (3 D0 + (2,1) D4 +
(3,5)/(4,5) D10 pair + (5,3) D11 + 1 of D6-D8).

## ROOT CAUSE forensics (why v1116d collapsed head-to-head)

Chain (sim-verified, seed 1, v1116d vs v1112):
1. D2: the (3,4) sheep misses its feed under opponent market pressure
   (head-to-head WHEAT price +$1-2/unit, D5 sells ~$174 less → D0-D3 feed
   wheat margin is ~0; in solo the same circuit survives with cu1 spikes).
2. Unfed sheep → NO wool production (animals only yield on fed days). By
   D6H12 the 2-sheep shed has ZERO wool. v11.12's 4-sheep wave = ~18-24 wool
   ≈ $4-5k on D6 — that is v11.12's D6-D8 cow-wave funding.
3. D6H16 BUY_LAND (NE, $1,000) fails ($294 cash) → NE stays locked all game.
4. NE locked → (5,4)/(6,1)/(5,2)/(5,3)/(6,3)/(6,4)/(8,4) pastures never build →
   D7 COW2 ($74) / D8 COW1 ($327) fail even when attempted → D10 SW land ($2,000)
   fails (no melon wave: D10 only harvests ~6 melons when the hand walk is
   mis-spawned or the sale is unfunded) → D10 pair + D11 (5,3) cow stranded
   in shed (3 cows never placed).
5. Final: 4 cows, $25,879 vs $124,273.

The v1116e s24 fix (+3 WHEAT product on D1) re-thickens the D1-D3 feed buffer:
D3 escape gone on seeds 1/5/11/9/13/19, but seed 3 solo now escapes on D4 —
the D0-D3 cow-first margin is structurally thinner than v11.12's (v1c shaved
~$200 off D0-D3 cash: WHEAT product 4→1, s88 WHEAT 3+1 cut, MELON 7→5, to
afford the 3rd D0 cow). One fix trades seed failures; the margin, not a slot,
is the problem.

## Strategic finding (the one that matters)

- The 2-sheep cow-first economy is worth **~$40-60k LESS per game** than
  v11.12's 4-sheep economy: wool D6-D29 (~$8-12k) + D6-D8 cow wave that the
  thin cash can't fund (~$6-8k milk) + D10 melon 5-plant vs 7-plant wave
  (~$3k) + D5 wheat-sale/feed trade. Neither v1116d nor v1116e beats v11.12
  on any bench axis. The bench gate (solo all-green + h2h non-regression +
  ghost 3/6) is NOT met. DO NOT SHIP.
- CD's 3c/2s economy only works because of the 36-WHEAT D5 pipeline (9+2 wheat
  plants harvested by D4-D5, sold D5H00). That pipeline (v1b spec item 4,
  "mandatory") was never built: our D4-D5 harvest circuit (v11.12-verbatim,
  choreographed for the 5-plant v11.12 layout) only captures ~8 of our 13
  plants. Building it = re-routing D4-D5 hand walks onto the west-column
  wheat ((0,0),(1,0),(0,1),(1,1),(0,2)) — the same choreography-fragile work
  that the hand-count discovery showed is high-risk.
- v11.12's D4-D29 circuits are load-bearing and choreographed for exact hand
  counts (12 on D10) and exact tile layouts. Any prefix change (animal mix,
  crop mix, hand count) shifts spawns/walks and silently breaks harvests,
  placements, and feed stops. This is why 89 sessions produced no shippable
  cow-first tape.

## Environment / tooling notes

- kaggle_environments 1.32.7 + kaggle present (verified at session start).
- **Engine state leaks between games in ONE python process** (re-confirmed
  this session: sequential in-process games gave contradictory animal states).
  All bench/trace work must stay process-isolated (`run_isolated.py` pattern).
  In-process traces are only valid for the FIRST game in the process.
- Ghost replays in /tmp/eps2: only 101359580 (CD) + 101381927 (Djaafar)
  survived. haodou 101363961, Sahil 101366252, 101085547/101197456/101115302
  need re-download (token KGAT_174eb... in KAGGLE_API_TOKEN) before any
  ghost A/B gate run.
- New tools in /home/user/_ref: `dump_tape.py`, `diff_tape.py`,
  `pos_trace.py`, `bench_solo.py`, `trace_h2h.py`, `trace_v1c.py`,
  `animal_map.py`. `run_isolated.py` VERSIONS now includes v1116c/d/e.
- Bench parallelism: 8-way occasionally flakes (one game times out); 4-way or
  re-run single is reliable.

## State of the gate

- Solo 8 all-green: FAIL (v1116e seed 3 D4 escape; v1116d seed-11 outlier;
  both below v11.12 on cash).
- 80-game matrix non-regression vs v11.12: NOT RUN (moot — h2h vs v1112
  itself is a ~$60k/seed loss).
- Ghost A/B 3/6: NOT RUN (replays missing; moot per above).
- **Live pair v11.12 (2256.9) + v11.13 (1754.7) HOLDS. Nothing to ship.**

## Ghost A/B (v1112 live vs v1116e, our original seats, 2026-08-29)

All 7 replays re-downloaded via kagglesdk (fetch_replays.py -> /tmp/eps2; do
NOT copy into the workspace, ~30MB each).

```
     ghost |     v1112 (live) |   v1116e (new) | verdict
 101359580 CD        +41,989 WIN |      -2,312 lose | FLIP-
 101381927 Djaafar   +32,217 WIN |     -24,591 lose | FLIP-
 101363961 haodou    -16,378 lose |    -53,280 lose | same-lose (worse)
 101366252 Sahil      +6,659 WIN |     -35,648 lose | FLIP-
 101085547           +15,012 WIN |     -23,003 lose | FLIP-
 101197456           -9,209 lose |    -24,320 lose | same-lose (worse)
 101115302           -2,398 lose |   -117,915 lose | same-lose (much worse)
```

**v1116e loses ALL 7. v11.12 WINS 4 of 7** — including +42k vs CD's recorded
strategy. The "we lose to the cow-heavy meta" narrative came from the ORIGINAL
live games (older tape). The current v11.12 tape already flips CD/Djaafar/
Sahil/101085547 against their recorded play. The 2257 rating is stale relative
to the current bot, not the other way around.

## Config A/B sweep (v11.12 runtime knobs)

v1120a wheat_batch 30 / b terminal 'value' / c cash_reserve 3500 / d exposure
preempt on / e a+b / f clone_preempt 0 — each = one knob off the live config.
Solo-8 deltas: 0 to -$111 (noise). Mirror h2h-8: f clearly bad (clone preempt
vs a mirror IS useful — keep live). **The live config is already tuned; no
shippable config lever.**

## Shed-cap + endgame audit (v11.12)

- shedCapacity 100->200 experiment: final-cash delta $0 to +$280/seed (avg
  ~+$60). "98/100 shed" is normal operation; EOD overflow costs ~nothing
  (D28-D29 mega-sells clear the shed). **Not a lever.**
- Endgame sells already ride the H17-H23 price-peak window D26-D29 (milk
  $261->$279 over D24-D29). Final shed empty on 7/8 seeds; seed 19 keeps 8
  carried items (WHEAT 2 + CARROT 6 ~ $210) in hands at game end. Only
  confirmed leak, ~$26/game avg, below churn threshold.

## FINAL VERDICT (data)

v11.16 cow-first (v1116d/v1116e, quarantined in rejected/):
- solo 8: ~$96.6k avg vs v11.12 $161.5k -> **-$65k/game** (corrected baseline:
  my earlier "140,237 avg" included an errored seed counted as $0 — true v11.12
  solo avg is $161,459)
- h2h vs v11.12: -$35 to -61k/game (0 escapes, 8c/1s vs 11c/4s)
- ghost 7: 0 wins vs v11.12's 4 wins
- gate: FAILS all three axes. **The 2-sheep funding wall is structural, not a
  slot bug. Direction is dead as a shippable build.** The 89b premise
  (cow-first beats the meta) is refuted: the live 11c/4s bot already beats
  the meta's recorded strategies.

## State

- LIVE PAIR HOLDS: v11.12 (sub 55829084, 2256.9) + v11.13 (sub 55829890,
  1754.7). Nothing to ship this cycle; churn is the enemy.
- Quarantined: rejected/v1116v1d.py, rejected/v1116v1e.py (+ prior v1a-v1c).
- Config sweep variants v1120a-f remain in topbots/ (evidence; do not ship).
- /tmp/eps2: all 7 ghost replays present (re-download: `pip install kagglesdk`
  then `python3 /home/user/_ref/fetch_replays.py <eids>`; token in
  KAGGLE_API_TOKEN / ~/.kaggle/access_token).
- Environment: kaggle_environments / kagglesdk / kaggle CLI and /tmp get wiped
  between sessions. Reinstall at session start: `pip install
  kaggle_environments==1.32.7 kaggle kagglesdk`.

## Next session (reframed by this evidence)

The build question is answered (do NOT rebuild the economy). Remaining levers,
priority order:
1. **Rating catch-up**: current v11.12 beats the recorded 3000-tier strategies
   (+42k CD, +32k Djaafar, +15k 101085547, +7k Sahil). Keep the live pair
   running; the 2257 should drift up as the current tape accumulates matches.
2. **Meta episode harvest for execution deltas**: build_intel2.py already
   pulled top-60 x 6 games (2026-08-28). Ghost-bench v11.12 vs those recorded
   strategies at scale (~300 episodes), mine the LOSS patterns (shop draws,
   opponent archetypes) — that is where any next tape change should come from:
   measured, not hypothesized.
3. **v1116e stays in rejected/** as reference for the s24 feed-margin finding
   (D0-D3 cow-first margin breaks under opponent market pressure; any future
   cow-heavy attempt must first fix the D1-D3 feed buffers).
4. Only confirmed shippable leak: seed-19 endgame carried items (~$26/game)
   — below churn threshold; do it only bundled with #2 output.

## Tools added this session (/home/user/_ref/)

dump_tape.py, diff_tape.py, pos_trace.py, bench_solo.py, trace_h2h.py,
trace_v1c.py, animal_map.py, ab_sweep.py, build_v1116d.py,
build_v1120_configs.py. run_isolated.py VERSIONS += v1116c/d/e, v1120a-f.
Bench parallelism: 8-wide flakes (OOM/timeout) — use 4-6 wide or retry;
ab_sweep.py has 3x retry built in.

---

# SESSION 91 ADDENDUM (same session) — tomato discovery, execution-lever sweep, final state

## What was done

1. **Ghost bench at scale** (72 top-16 recorded games, all process-isolated,
   `ghost_bench_local.py`): current v11.12 vs the recorded top-16 strategies:
   **50W-22L, 27 flips of recorded losses, 16 regresses of recorded wins.**
   The 22 remaining losses mine to 3 archetypes: goose economy (CD ep
   100939868: 7 geese, eggs), 9-sheep wool factory (William Diment
   100882715), and a $20k D29 endgame dump (peikopon 100841489).
2. **Execution-lever sweep on v11.12** (all measured, all below ship bar):
   - 6 config knobs A/B (wheat MM batch, terminal rule, cash reserve,
     exposure preempt, clone preempt): solo deltas 0 to -$111. Live config is
     already tuned.
   - Shed cap 100->200 experiment: final-cash delta $0 to +$280/seed.
   - Sell-band timing: vs a real night-selling opponent the AM/MD/PM price
     bands are FLAT (MILK 223/225/224 etc.) — the "night premium" the meta
     rides does not exist intraday in head-to-head; no lever.
   - Endgame flush: already optimal (H17-H23, shed clears to 0 on 7/8 seeds).
   - PASS slots: sub-$50 expected value; not worth churn.
3. **TOMATO endgame scarcity discovered + built + shelved** (the real
   finding): see `topbots/rejected/v1121_tomato_README.md`.
   - Measured premium: $411-522 endgame in high-premium games (peikopon:
     45u sold D29H18 = +$18.5k; price $71 D12 -> $522 D29H15). Solo: only
     $64-111 (melon $150-250 beats tomato there).
   - Built the 12-tile endgame conversion (v1121_tomato.py): all 12 tomatoes
     DIED in sim — the hand walks water these tiles every 2nd day, single
     unit, and the PLANT slots consumed the watering visits. Only the D19/D20
     FERT+WATER pairs (same unit, consecutive hours) support a surviving
     plant; the D26/D27 dig-replant then removes it at first yield, and the
     EOD-drop mechanic makes D29 harvests unsellable. Sellable value capped
     ~$1-3k total, below the ~$720 seeds + ~$600 strawberry forgone +
     weed/overflow risk. **Shelved with full evidence.**
4. **v11.16 cow-first line: DEAD (measured).** v1116e (best checkpoint):
   solo ~$96k avg vs v11.12 $161.5k (-$65k/game); 0-7 ghost vs the cow-heavy
   meta. The 2-sheep D0-D3 funding wall is structural (wool engine + feed
   margin), not a slot bug. Quarantined: rejected/v1116v1d.py, v1116v1e.py.

## Final state

- **LIVE PAIR HOLDS** (v11.12 2256.9 + v11.13 1754.7). Nothing shippable
  found this session — which is itself the result: v11.12 is locally optimal
  on every measurable static lever. The rating gap to the 2800-2900 block is
  (a) game-pool/rating dynamics (current tape beats the recorded 3000-tier
  strategies: +42k CD, +32k Djaafar) and (b) situational meta plays the
  static tape can't see (goose/wool-factory builds, the tomato premium).
- **Next session (if the user wants more build):** the ADAPTIVE tomato
  replant — a runtime module (no static choreography) that watches the tomato
  price + bakery count and, when the premium crosses ~$200 mid-game, converts
  strawberry tiles to tomatoes using the existing FERT+WATER-pair days (the
  only survivable planting days, proven in sim). Scope: runtime module +
  bounded replant choreography + sim gate. This is the "adaptive bot" the
  original ask described, and the only remaining lever with a measured
  upside >$2k.
- Tooling added (in /home/user/_ref): ghost_bench_local.py, ghost_diag.py,
  raw_walk.py, tile_scan/tile_visits/rawtrace (in /tmp), build_v1121_tomato.py
  (kept for the adaptive version), /tmp/eps2 has all 7 gate replays.
- Env re-install at session start: `pip install kaggle_environments==1.32.7
  kaggle kagglesdk` (packages + /tmp get wiped between sessions).
