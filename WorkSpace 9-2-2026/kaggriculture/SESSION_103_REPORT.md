# SESSION 103 — generated tape: $0 → $82k held-out, 5,288 specs searched

Continuation of 102. The author now produces working farms and the composition
search is live. Nothing shipped; live bot untouched (v11.31 55947935 rating).

## Where the generator got to

| stage (seed 1) | final |
|---|---|
| start of session 102 | $0 (bankrupt) |
| end of 102 (6 contract bugs fixed) | $26,869 |
| + feed carried per route, no early wheat round-tripping | $23k (bug exposed: we were selling the feed we had just bought) |
| + melon-start / cow-day knobs (stop starving the opening) | $58,307 |
| + coordinate descent on 8 knobs | $83,105 |
| + unified crop calendar (melon while a full cycle fits, wheat as filler) | $82,648 |
| + random-restart hill climb, 5,288 specs evaluated | **$114,341** |

Best spec found (trained on seeds 1-2):
```
{"SHEEP":4,"COW":12,"GOOSE":0,"hands":9,"melon_start":0,"cow_day":12,
 "ne_day":7,"sw_day":14,"wheat_sell_day":4,"wheat_window":4,"straw_tiles":0}
```

| seed | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| generated tape | 114,341 | 99,867 | 84,776 | 89,636 | 93,142 | 69,193 | 52,489 | 104,391 |

Trained avg (1-2) **$107,104**; **held-out avg (3-8) $82,271**. v1112fr on the same
held-out seeds averages $137,517 — so the generated line is at ~60% of the live
tape, up from 0% this morning. Saved as `topbots/v130_gen.py` (pure replay).

## Fixes made this block

* **Feed round-trip bug**: `SELL WHEAT` every day sold the feed wheat bought that
  same morning at a spread; wheat sells now start at `wheat_sell_day`.
* **Feed carry**: `PICKUP WHEAT min(6, n_feed)` capped a route at 6 feeds, so the
  tail animals of long routes starved — now carries one per FEED on the route.
* **Opening starvation**: melon seeds are $80 each; an 8-tile D0 melon block ate
  the entire $3,000 and left nothing for feed/land. `melon_start` and `cow_day`
  became knobs — moving cows to D10-D12 was worth **+$16k** on its own.
* **Crop calendar**: every field tile now has a greedy calendar — melon while a
  full 12-day cycle fits, wheat as the filler — instead of a hand-written cycle
  table that left 35-43 tiles idle from D18.

## Measured design findings (these decide the next block)

* **Strawberry in this author loses** ($83k → $43-55k). It needs ~16 waterings per
  tile versus melon's 8, and the current labour budget can't pay for it.
* **But melon has a hard market ceiling.** MELON's glut curve is quadratic
  (250 − 0.01·d²): 150 melons is already ~$26k gross total, and the last ones sell
  near the floor. A melon-dominant farm cannot exceed roughly $30k of crop revenue.
* v1112fr's revenue comes from STRAWBERRY $75k + MILK $69k, both on gentle linear
  glut curves that absorb 300+ units. **That is why it wins, and it is the mix the
  generated tape must reach** — strawberry-dominant, funded early enough to afford
  10-15 hands.
* A greedy multi-unit router (assign each tile-group to the earliest-free unit)
  was tried and is **worse** ($28k vs $83k) than the spatial snake partition —
  reverted.

## Next block

1. Make the strawberry block affordable: earlier income (wheat + wool), a hands
   ramp funded by that income, and fertiliser routed to strawberry production days
   (doubles each event — v1112fr fertilises 160 of 162 events).
2. Re-run the spec search with `straw_tiles` in the 20-40 range once labour can pay.
3. Gate: held-out average ≥ $140k, then H2H vs v1112fr and the recorded metas.

## Tools

`_ref/tape_author2.py` (spec-driven author, all knobs), `_ref/search_spec.py`
(random-restart hill climb, ~0.1 s per game, 5k specs in 14 min),
`_ref/sweep2.py` (coordinate descent), `_ref/diag_tape.py`, `_ref/spec_best.json`,
`topbots/v130_gen.py` (current best generated tape).
