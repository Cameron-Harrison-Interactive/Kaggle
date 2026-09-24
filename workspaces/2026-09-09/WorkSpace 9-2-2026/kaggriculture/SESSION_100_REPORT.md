# SESSION 100 — tape optimisation round: one shippable candidate

Bench harness this session (new, ~1.0 s/game, deterministic):
`_ref/tape_lab.py` (in-process route/config evaluator), `_ref/search_tape.py`
(mutation hill-climb), `_ref/h2h.py` (head-to-head, both seats), `_ref/bench_variants.py`.

## SHIPPABLE CANDIDATE — `topbots/v1131_ch3.py`

One-line change to v1112fr: `clone_preempt_horizon: 2 -> 3`. Nothing else
(diff is one config line; routes/tape untouched).

| test | v1131_ch3 | v1112fr (live) |
|---|---|---|
| solo cash, seeds 1-8 and 9-16 | identical to base, $0 | — |
| mirror H2H vs live bot, seeds 1-8 (16 games) | **11 wins** | 5 wins |
| mirror H2H vs live bot, seeds 9-16 (16 games) | **16 wins** | 0 wins |
| mirror avg cash (32 games) | ~$2.1k/game ahead | — |
| vs 55801300 (v11.3), seeds 1-8 | 9-7, avg 81,759 | 8-8, avg 80,368 |
| vs 55730825, seeds 1-8 | 16-0, avg 90,194 | 16-0, avg 90,194 |

Why it is safe: the preemption layer only fires when a *clone* opponent is
detected, so solo play and non-mirror openings are unchanged; the longer horizon
only makes our sell fire earlier ahead of a detected clone's dump.
Why it may matter on the LB: the field contains forks of the public notebook, so
mirror matchups are a real share of our games.

**Not submitted. Awaiting your GO.**

## Tape micro-search — measured, does NOT generalise (do not ship)

Ran a stochastic hill-climb over the market layer of the tape (quantity tweaks,
intra-day moves, deletes, duplicates, per-day sell-time shifts, added orders),
~930 candidate tapes evaluated:

| tape | train seeds | train Δ | seeds 9-16 | seeds 17-24 (fresh) |
|---|---|---|---|---|
| `v1220_sa` | 1-3 | +348 | +147 | — |
| `v1220_sb` | 4-6 | +931 | +48 | — |
| `v1230_r1` (≥5/8 seeds must improve) | 1-8 | +228 | +298 | **−120** |

On seeds 1-8 `v1220_sa` looked like **+$4,647/game** — that was one seed (seed 5,
+$34,346) flipping a chaotic branch, not a real edge. Out-of-sample the whole
family is worth ~$0. Sell timing in this tape is at a genuine local optimum;
perturbations are a coin flip worth ±$1-2k of chaos each.

## Why bigger tape surgery keeps failing — the tape is already expert

Instrumented the engine's plant refresh: of **162 strawberry production events,
the tape already fertilises 160**. FERTILIZE doubles output (2 units vs 1) and a
strawberry unit clears ~$236, so this was the largest theoretical lever left —
and it is already fully harvested by v1112fr's 80 FERTILIZE actions.

Consequences measured this session:
* a live fertiliser hand (hired last at H03 so hand mapping/spawns stay intact,
  collecting straight off the animals): **−$6.3k/hand** — it adds ~35 fertilise
  actions that produce **zero** extra strawberries.
* holding fertiliser back from sale so the hand always has stock: **−$19.6k**
  (shed slots at peak are worth more than the fert).
* shifting all SELL orders 2 or 6 hours earlier, or 3 later: **−$80k to −$100k**
  in H2H — sells are tightly coupled to when the walks drop stock in the shed.
* free-slot audit: of 410 steps where a unit stands on an unfertilised plant
  while carrying fertiliser, **0** are no-ops. There is no spare labour in the tape.

## Old submissions: higher LB scores are rating-era artifacts, not strength

Pulled the actual submission list and downloaded the binaries. Live v1112fr is
**1717.9**, but older subs show 2009.8 (v11.12), 2064.6 (v11.2), 2191.2, 2194.8
(v11.3), 2739.0 (Adapt-2-Survive, 2026-08-10). Head-to-head on 8 seeds, both seats:

| opponent (LB score then) | result vs live v1112fr |
|---|---|
| Adapt-2-Survive 55394887 (2739.0) | live wins **6-0** (3 seeds) |
| 55730825 (2191.2) | live wins **16-0** |
| v11.3 55801300 (2194.8) | 8-8, live +$1.5k avg |
| v11.7 55808478 (1985.8) | 8-8, live +$1.8k avg |
| v11.2 55798503 (2064.6) | 8-8, live +$2.3k avg |
| v11.8b 55818897 (1932.4) | 8-8, live +$1.9k avg |
| v11.4 55803806 (1927.1) | 8-8, live +$2.5k avg |
| v11.12 55829084 (2009.8) | 3-3 (near-identical tape) |
| v11.13 55829890 (1835.4) | 3-3 (near-identical tape) |

So resurrecting an old submission is **not** a shortcut — the current bot is at
least as strong as every one of them. The score gap is when they were rated, not
what they play like.

## Also measured

* Cash injections of $500 at D0/D2/.../D20 change the final by exactly $500
  (multiple 1.00x): the tape never spends opportunistically, so "free early cash"
  ideas are worthless unless the plan itself buys more.
* Tile census: NW+NE+SW are 100% planted/stocked from D8 to D26 (only the never-bought
  SE is idle). No idle land, no idle labour, no idle fertiliser.

## Files

`topbots/v1131_ch3.py` (candidate), `topbots/v1220_sa.py`, `topbots/v1220_sb.py`,
`topbots/v1230_r1.py` (searched tapes, rejected), `_ref/tape_lab.py`,
`_ref/search_tape.py`, `_ref/h2h.py`, `_ref/build_cfg.py`, `_ref/build_fert.py`,
`_ref/probe_prod.py`, `_ref/probe_fert.py`, `_ref/probe_cashvalue.py`,
`_ref/old/<submission_id>/main.py` (downloaded old agents).

## SUBMITTED (user GO, 2026-09-01 21:10 UTC)

`submission_v1131_ch3.tar.gz` -> **submission 55947935**, status COMPLETE.
Description: "v11.31 ch3: v11.12fr tape, clone_preempt_horizon 2->3
(mirror H2H 27-5 over 32 games, solo identical)".

Public score reads **600.0** immediately after acceptance — that is the cold-start
rating every new agent gets, not a result. It climbs as episodes are played
(v1112fr 55925101 sits at 1720.6 after a day). Check again in a few hours.
