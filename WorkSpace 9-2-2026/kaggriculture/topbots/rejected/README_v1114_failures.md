# v11.14 D0-swap variants — REJECTED (bench, 2026-08-28)

v1114a_cowfirst.py  (D0 2c/2s, ALL 5 routes)
v1114d_defaultswap.py (D0 2c/2s, "default" route only — see below, this distinction
  turned out to be meaningless architecturally)

Bench (solo 8 seeds + 6 ghost A/B vs live tapes):
- default-suffix games: -44k..+8k (mostly negative)
- yarn-suffix games: -44k to -91k CATASTROPHIC (Sahil ghost +17.4k -> -73.3k)
- D23 mass escapes in worst yarn games

ARCHITECTURE FINDING (why "default only" is meaningless): the route system is a
FIXED DEFAULT PREFIX (D0 through the first YARN shop, s0-s87 identical in all 5
routes, always executed from 'default' selection) + per-shop SUFFIX (routes diverge
from s88). The D0 opening is load-bearing for ALL suffix economies (yarn suffixes
are sheep economies sized for the 4-sheep D0; 2c/2s starves their wool-funded
wheat line). Any D0 swap is all-or-nothing across the ladder.

Safe cow-first build = full route rework: default prefix rebalanced to 12-14 cows
+ every suffix rebalanced for the new D0 + feed-coverage verified per animal/day.
Multi-day build. See SESSION_86_REPORT section 10.

## SESSION 87 additions (2026-08-28)

v1114e1_cowroute.py (1c/3s D0: (4,4) sheep -> cow; kept in topbots/ root,
builder _ref/build_v1114e.py). REJECTED: −$7.6k…−58.5k/game on 8-seed bench.
The (4,4) D0 sheep is the D6 wool cash wave (~$3.3-4.5k/day); converting it
collapses D6 cash and breaks the D6H13/D7H00 cow buys + NE BUY_LAND (2 cows
lost ≈ $7-9k). See SESSION_87_REPORT.md §1a + §2 (the wool-engine law).

v1114b1_cowroute.py ((3,3) D3 cow + full D9-D29 feed circuit; kept in
topbots/ root, builder _ref/build_v1114_full.py). REJECTED on the D7 wall:
no hand carries wheat to (3,3) on D6/D7; the farmer detour displaces the
(5,2) D7 cow (net break-even to negative). The D9-D29 circuit authoring is
reusable. See SESSION_87_REPORT.md §1b.

ANY D0 SHEEP CUT IS DEAD (14a/14d 2c/2s: −44k…−91k; e1 1c/3s: −7.6k…−58.5k).
The 4-sheep D0 wool engine funds the D6-D8 cow wave — the tape's local
optimum is 11c/4s. Next viable path = CD-style all-in rebuild (see
SESSION_87_REPORT.md §3).

---

## v11.15 night window (SESSION 88, 2026-08-29) — REJECTED (field matrix)

v1115_exec.py: move SELL {MILK, STRAWBERRY} from H05-H21 into the meta's night
window (H22/H23/H01/H02). Market orders only (RNG-safe). The 11c/4s meta
(2527-2765 band, all 27 teams) sells at H22-H02; the tape sold mid-day.

Bench: solo 8 seeds ALL GREEN +$321/seed (0 escapes); CD ghost +$273 (entangled);
**80-game field matrix −$546/game (19+/61−, 1 extra escape)** — v46 −$2,024/game
(mid-day seller: our night sells hit their dump trough). Milk-only variant
(v1115_milk.py): solo +$236/seed but v46 still −$508/game.

Verdict: the night window is a coordination strategy — profitable only against
night-sellers (the meta). Net-negative vs the non-meta field at our current
ladder position (#199). Re-visit when the pair is in the 2400-2800 band where
opponents are mostly same-build meta (route gate). See SESSION_88_REPORT.md.
