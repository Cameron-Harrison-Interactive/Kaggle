# SESSION 124 — 2026-09-08 ~12:15 UTC
## v28.17 probe submitted (56097984). Router stays primary. The real gap is now measured.

**Posted:** `submission_v28_17_probe.tar.gz` = topbots/v28_harvest_moon.py (v28.17) — ID **56097984**, 12:12 UTC. Description discloses local scores (solo ~$50k, 0-10 H2H vs router) and that tt_router remains primary. 4 submissions left today (quota is 5/day, not 2 — memory corrected).

**Ladder right now:** router 56079632 = **2483.7** (slipped from 2550.2 peak; team rank ~363/8175). v16 1801.0. Best submission counts → probe cannot hurt team rating.

---

## THE HEADLINE FINDING (changes the roadmap)

**tt_router SOLOS at $163-197k** (seeds 101/202/303): 8 sheep + 7 cows, zero crops at end, tape-timed full dumps, airtight (final shed empty, no hire gaps, +$8-13k/day through d29).
v28's best solo is $67k (v28.12). **The gap was never H2H adaptation — it's total economy scale.** Five H2H variants (v28.13-17) all plateau at $27-69k vs the router's $88-197k because the underlying economy is half as productive, not because of market blindness.

## H2H/mirror meta decoded (router-vs-router price matrix)

- Crashes to ~$1: MILK (d16), WOOL (d16), STRAWBERRY ($12 by d20), FERTILIZER ($1 by d24), MELON ($78 by d12)
- Deep deficits all game: CARROT $74, WHEAT $44, TOMATO $79, EGG $59
- Elite (ymg 2955) recipe vs this field: wheat carry (1123@29 -> 1361@47-50), late-stagger tomato, 8C/3S/1G, endgame $92k in final 6 days.

## v28 fixes this session (all traced, all kept)

1. H2H death spiral fixed: milk gate 150 + drain-cap "+2 leak" pinned milk at $145 with $18k trapped in shed → shed clog → feed buys blocked → herd starved. Now: volume-mode sells with small floors, shed-pressure clearance.
2. Morning order starvation fixed: 7 standing sells + hire flood left day-4 with 2 hands. Now h0/h1 = feed/animals/seeds/land/hires + max 2 sells.
3. Engine facts: 1 fertilizer = 3 days of DOUBLED production; ongoing crops expire after 4 productions (treadmill replanting required — our 12 strb sat dead half the game); hands are fired every midnight; standing SELL orders fill only what's in the shed (order spam is free).
4. v28.16/17 mirror-meta crops (carrot treadmill) tested — did NOT beat v28.14/17 baseline (labor overload at 55+ tiles remains the binding constraint; walking still ~64% of unit-steps).

## ROADMAP TO >2500 (next sessions, slots in reserve)

1. **Close the solo economy gap to router class ($190k)**: sheep at scale on YARN seeds (router ends 8S), cycle-treadmill with labor that holds at 60 tiles (walking 64% -> <50%), tape-style endgame dumps.
2. Gate: solo $100k+ AND H2H >=60% vs tt_router locally BEFORE any "replace primary" submission.
3. Probe 56097984 replays = live meta data vs the real field (check episodes overnight; expect ~2100-2300 rating — its job is data, not rank).
4. Token T1 verified for submit+submissions+leaderboard via exact slug (slug contains invisible bytes — use /tmp/slug, never hand-type).

## FILES
- topbots/v28_harvest_moon.py = v28.17 (probe, submitted as 56097984)
- topbots/v28_14_probe.py = v28.14 reconstruction (A/B parity with v28.17: 3-3)
- topbots/tt_router_938.py = PRIMARY (2483.7 live)
- /tmp VOLATILE: solo28.py (per-seed fresh module), solo_router.py, h2h.py (swap-mode, agent-vs-agent), diag28.py, slug, ws, pkg/
