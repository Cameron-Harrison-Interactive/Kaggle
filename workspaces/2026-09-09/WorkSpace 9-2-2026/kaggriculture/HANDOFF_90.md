# HANDOFF 90 — build v11.16 (the lean-cow tape that beats the meta)

You are continuing a multi-session build for the Kaggle kaggriculture farming
bot (team "Harrison Interactive", user nosiru; token KGAT_174ebff7462e0b34526c2936d51a2fc0
via KAGGLE_API_TOKEN; competition `kaggle competitions kaggriculture`).
FIRST: `pip install kaggle_environments==1.32.7 kaggle`, then read
`/home/user/WorkSpace 8-27-2026/kaggriculture/STATE_89.md` in full — it has the
complete design, three iterations of sim-verified results, root causes, and the
exact v1c slot-level spec to build.

TASK: build v11.16 per the V1c SPEC (last section of STATE_89.md). Working
starting point: `_ref/build_v1116b.py` (builder) + `topbots/rejected/v1116v1b.py`
(the v1b tape — its D0-D3 prefix and D6-D10 market buys are PROVEN working; the
v1c spec is a delta on top: defer the (3,2) cow to the D5H19 buy + D6H03
placement, CD-aligned D0 market, 5-animal D3 cycle, +2-3 D5 harvest slots).
Then: (1) verify the 6 default-route seeds solo (0 escapes, all animals fed
same-day at placement, D5H01+ cash headroom), (2) rebuild the yarn_first/
second/third + bakery_capital D4-D29 suffixes for the 3c/2s prefix (the
route-flip mechanism is documented in STATE_89 — a cow-first prefix FORCES all
5 suffixes), (3) audit the drawn route per bench seed, (4) hand-count reduction
10-15 -> 6-8 LAST. Bench gate (ship only if ALL pass, from STATE_89): solo 8
seeds [1,3,5,7,9,11,13,19] all green vs v11.12 with 0 escapes + per-animal feed
>=28/30; 80-game matrix (bt/v46/k2900/moon/soil x 8 seeds x 2 seats)
non-regression vs v11.12 via `_ref/run_isolated.py`; ghost A/B flips >=3 of the
6 cow-heavy losses (CD 101359580, haodou 101363961, Djaafar 101381927, Sahil
101366252, 21-regress 101085547/101197456/101115302).

DO NOT: retry D0 sheep cuts below 2 (the wool-engine law, sessions 86-87);
add a 4th D0 cow (over-budget, quantified in STATE_89); ship anything before
the full gate (the live pair v11.12 2256.9 + v11.13 1754.7 holds the team ATH —
churn is the enemy); post to Kaggle without an explicit user go.

Work in tight sim-verification loops (the engine is bit-exact: one targeted
trace per suspected bug, not broad re-runs). Keep STATE_89.md's progress log
updated after every iteration. The user wants momentum with minimal context
burn — report tersely: what was built, what the sim showed, what's next.
