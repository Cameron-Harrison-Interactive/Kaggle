# SESSION 114 — The Margin Reframe: v16 Passes, Burn-Mode Falsified

**Time:** 2026-09-06 ~22:20 UTC · User: "We aren't chasing max gold — we're chasing moving
up the ladder: beat them at their own game or burn their revenue so we come out above."

---

## You changed the metric — and it changed the answer

All previous gates scored OUR revenue. The ladder only cares about **margin over the
opponent**. Re-gated on real tapes with margin as the metric:

| Variant | Mechanism | 8 real loss-opponent tapes (margin) | Verdict |
|---|---|---|---|
| v4b | baseline | +296,910 total, 8/8 wins | control |
| **v16** | premium-window liquidation | **+302,032 total, 8/8 wins** (+$640/game) | **the only margin-positive fix ever gated** |
| v17 "burn" | front-run dump everything | **−386,000, 0/8** | FALSIFIED |

**Why burn-mode fails (measured):** prices mean-revert intraday — the town drain pulls
inventory back down within hours. The instant dumper sells into the dip he creates; the
scheduled seller catches the reversion. We paid the reversion every step ($18-60k for us
vs $83-116k for them). Burning their revenue by dumping burns us worse — supply pressure
is paid by whoever adds it.

**Why v16 wins on margin:** it moves OUR volume into the freshest windows (milk h1/h14/
h18/h22, strb at ≥$180 before the permanent floor) — small revenue edge (+$236 avg),
consistent margin edge (+$640/game), zero flips to loss across all 17 gated games. It is
the elite sell-hour fix with the one mechanism that survives.

## Your tile question — honest answer

For the COMPILED tetsu blob: the labor plan isn't readable — no tile to edit. What breaks
isn't mysticism, it's cash-flow choreography: wheat buys (v15, −$66k) starved the animal
schedule; delayed sells (v14, −$50k) broke the cash timeline the plan books against.
**For the READABLE notebooks (hamburger/route): you're right — the route IS editable,
tile by tile.** That's tomorrow's build: graft tomato/carrot onto hamburger's route
(escape both the tetsu twins AND hamburger's twins — a differentiated private build).

## MIDNIGHT LINEUP (00:00 UTC, ~1.6h) — the live A/B you asked for

1. **v4b** (control — the 2526-class winner, verbatim)
2. **v16** (treatment — same winner + the elite sell-window fix, margin-gated 17/17 safe)

Both slots = our main winner, one fixed and one control, 48h undisturbed. If v16 > v4b
live, the fix works and we iterate (tomato graft next). If not, v4b is the floor.
v11 (2322.5) held in reserve with 3 slots.

## Files
- submission_MIDNIGHT_v4b.tar.gz, submission_MIDNIGHT_v16.tar.gz (ready, verified)
- topbots/tetsu_r5_v16_premium.py, topbots/tetsu_r5_v17_frontrun.py (falsified, kept for record)
