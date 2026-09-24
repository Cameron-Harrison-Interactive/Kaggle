# Session 44 — Rebuilt Adaptive Bot, Measured Real Ceiling

## What I tried

You asked for a custom adaptive bot that exceeds meta output. I restored
Session-35's self-aware brain (the one that plans every day from live board)
and attempted to rebuild the production layer.

## What I actually discovered

Session-35's baseline metrics vs. Kaggle-replay opponents (their action
streams played back statically):

| bot | wins/21 | avg | notes |
|-----|:-------:|----:|-------|
| Session-35 (self-aware brain) | 9/21 | −$5,413 | plans well, doesn't produce enough |
| v41 (current best public) | 27/29 | +$7,890 | fixed tape, maxes production |
| breaking_tie (Session-42 ship) | 25/29 | +$7,954 | multi-route ensemble |

But that's misleading. When I tested Session-35 against **live adaptive
bots** (their actual code, adapting to us in real time, not replay), the
picture is brutal:

| Session-35 vs | wins/12 | avg |
|---------------|:-------:|----:|
| v41 (live) | 0/12 | −$61,402 |
| moon | 0/12 | −$64,108 |
| soil | 0/12 | −$61,058 |
| breaking_tie | 0/12 | −$61,677 |
| V25 tape | 0/12 | −$65,109 |

**Session-35 loses EVERY game against every top bot when they can adapt.**

## Why

Traced day-by-day money in Session-35 vs v41 head-to-head (seed 1):

| Day | Session-35 | v41 | gap |
|:---:|-----------:|----:|----:|
| D1 | $418 | $4 | +$414 |
| D6 | $425 | $31 | +$394 |
| **D7** | **$328** | **$3,187** | **−$2,859** ← v41 dumps first sell burst |
| D10 | $1,418 | $2,985 | −$1,567 |
| D14 | $10,122 | $14,169 | −$4,047 |
| D18 | $14,952 | $29,938 | −$14,986 |
| D22 | $32,288 | $75,205 | −$42,917 |
| D29 | $60,263 | $132,186 | **−$71,923** |

Session-35 is AHEAD until D7, then loses cumulatively because v41 sells
premium items first (Session-35 waits for its planner's sell-hour) and
uses that early cash to buy more land, hire more workers, plant more crops.
The gap COMPOUNDS: each dollar v41 has earlier buys another dollar of
production capacity.

## Individual parameter tweaks I tested

I ran each proposed change in isolation (baseline Session-35 = $106k avg
solo):

| change | avg | delta |
|--------|----:|------:|
| baseline | $106,007 | — |
| c2s2 open (match meta) | $99,703 | −$6.3k |
| final_sheep=12 | $100,775 | −$5.2k |
| final_cow=8 | $99,129 | −$6.9k |
| aggressive land buying | $102,821 | −$3.2k |
| sell_hour_secondary=9 | $103,033 | −$3.0k |
| **wheat_reserve 2→3** | **$109,559** | **+$3.6k** ✓ |
| herd_cap 14→20 | $106,738 | +$0.7k |
| seed_floor 200→50 | $96,482 | −$9.5k |
| plant_max 56→80 | $106,007 | 0 |

**Only ONE parameter helps** (wheat feed reserve). Everything else that
"looks like it should match the meta" actually hurts because Session-35's
whole planner is balanced around its current parameters.

The full "match meta" mega-change I tried:
- final $75k avg vs PASS (down from $106k baseline)
- 200+ empty crop tiles by D25 (planner couldn't keep up with the
  larger field)
- animals dying from starvation D14-D16 (feeding logic wasn't scaled)
- Even less selling than baseline

## Honest conclusion

**Session-35 architecturally cannot beat a modern tape bot in adaptive
head-to-head play.** The day-planner is a survival optimizer, and its
production ceiling is fundamentally lower than a hand-tuned tape that
front-loads the field, keeps every tile alive, and dumps sells before the
opponent.

To exceed meta output with adaptive intelligence would require:
1. **Rewriting the day-planner** as a production-maximizer with tape-like
   discipline (~2000+ lines of new code, weeks of tuning)
2. **Rewriting the market layer** to preempt sells against a modeled
   opponent (Session-35 has this dormant but disabled — enabling it caused
   too many false positives)
3. **Match harvest/replant/water timing** exactly to the crop rules so
   nothing sits idle for even one turn

I attempted #1 today by adjusting parameters. Each change broke another
part of the balance. Doing this properly is not one-session work.

## What I shipped

**`main.py` restored to Session-42 breaking_tie.** No shipped change.

The breaking_tie tape is currently the highest-margin, highest-H2H bot
we have (71% head-to-head win rate vs 5 other top public bots, avg +$7,954
across 29 real Kaggle opponents).

## Honest path forward for top-5

There's no free lunch here. Real options:

1. **Study top-5 bots' actual replays** — I can pull Ryo Hasegawa (rank 1),
   Crop Dusta (rank 2) replays and extract patterns they use that public
   notebooks don't. The FARMER + HANDS actions ARE visible in replays.
   ~1-2 sessions of work to build a stronger tape.

2. **Wait for a top-5 team to open-source their bot** — happens occasionally
   near competition end. Check daily.

3. **Long-form custom development** — write a production-optimizer brain
   from scratch that matches tape output while staying adaptive. Real work,
   real time.

## Preserved backups

- `main.py` (shipped) = breaking_tie
- `main.py.bak_session42_breaking_tie` (same)
- `main.py.bak_session41_v41`
- `main.py.bak_session40_wheat16`
- `main.py.bak_session35` (original adaptive brain)
- `main.py.bak_session43_selfaware_attempt` (Session 43 predictive layer)
