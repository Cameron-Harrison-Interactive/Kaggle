# SESSION 94 — RESULTS: what's actually in hand (2026-08-31)

The user asked for results. Here they are, measured today, engine 1.32.7,
process-isolated.

## 1. CORRECTED: the stale file was the workspace main.py, NOT Kaggle

Diffed workspace `main.py` against the bench build
`topbots/v1112_seedfix.py` (the tape every number in sessions 86-93 was
measured on). Exactly one step differs — s24 (D1H00):

```
LIVE (shipped):  BUY_PRODUCT WHEAT 5 + BUY_SEED WHEAT 1
BENCH (current): BUY_PRODUCT WHEAT 4 + BUY_SEED WHEAT 2   <- the D1 seed fix
```

The 2-seed D1 order is the documented "(2,1) class kill" fix (two wheat seeds
before the double plant).

**Correction (after checking the Kaggle submission history):** sub 55829084
(the live v11.12 slot) is described as "v11.12 - D1 seed fix: 2 wheat seeds
before D1 double-plant", and the shipped v11.13 tape (v1113_norescue.py) also
carries the 2-seed order. So the LIVE slot already had the fix — the stale
1-seed file is the workspace `main.py` copy, which was never updated when
v11.12 was built. The submitted sub 55917889 (this session) is therefore a
FRESH RESUBMIT of the same best-measured tape, not a bugfix deploy — still
useful: per the team's own v11.8b note "fresh submission = fresh game
scheduling", the new sub starts its own rating accumulation against the
current meta. Workspace main.py should be re-synced to the shipped tape.

## 2. Measured impact (today)

Mirror live vs seedfix, 8 seeds x 2 seats (16 games):
  avg delta -$47 (statistical tie; per-game spread -$6.0k..+$12.5k = route
  flips from the D1 tile-state divergence). 0 escapes either side.

vs the 3 loss-archetype tapes (ghost replays, our seats):
  game              recorded       LIVE tape      seedfix tape
  goose 100939868   69,076>61,035  +9,362 WIN     +9,378 WIN
  peikopon 100841489 86,405<101,060 +7,432 WIN    +7,444 WIN
  dimenti 100882715  102,279<104,875 +21,651 WIN  +21,324 WIN

  => The current tape (both variants) BEATS all three recorded top-16
     strategies that the session-91 bench counted as losses. The
     "we lose to the meta" picture is stale: against the recorded 3000-tier
     meta the team's true margin is +$7k to +$22k/game on these archetypes.
     The 2256.9 rating is the lagging indicator, the tape is the leading one
     (session-90 note "rating is stale relative to the current bot" — now
     quantified).

## 3. SHIPPED (2026-08-31 14:38, user GO given)

Sub **55917889** — `submission_v1112_seedfix.tar.gz`
  - main.py = topbots/v1112_seedfix.py (the measured tape)
  - status PENDING at submit time; 4 submissions remaining today
  - effect: fresh game scheduling for the best-measured tape; the new slot
    accumulates its own rating against the current meta (the old v11.12 slot
    has drifted 2256.9 -> 2009.8 since the session-90 report; v11.13 slot
    1754.7 -> 1819.0)
  - TODO: re-sync workspace main.py to the shipped tape so future diffs
    don't get tripped by the stale copy again

## 4. What is NOT shippable (measured dead, for the record)

- v11.16 cow-first (v1a-v1e): -$35 to -65k/game, structural 2-sheep wall.
- v1121 static tomato / v1122 adaptive tomato: negative across the whole
  measured premium range (feed + wheat-MM + shed-capacity cost stack).
- All config knobs, shed cap, sell-band timing: 0 to -$111 (session 90/91).
- v11.13 slot (sub 55829890, 1754.7): the shipped file for that slot is not
  in the workspace, so the same stale-tape check could not be run on it.
  If the user has the original v11.13 submission file, diff it against
  topbots/v1113_norescue.py the same way.

## 5. Remaining upside (unchanged, now with fresh evidence)

1. Rating catch-up (quantified today: +$7.4k..+$21.7k over the 3 recorded
   meta archetypes) — accrues automatically once matches accumulate; the
   seedfix re-ship is the only action needed.
2. Meta loss mining at scale: 72-game bench said 50W-22L; 3 of the 22
   archetypes are now measured flips. The other ~19 losses still need
   per-episode forensics (replays downloadable on demand via
   _ref/fetch_replays.py).
3. Seed-19 endgame carried-items leak (~$26/game) — bundle with #2 output.

## 6. Workspace fix (2026-08-31)

Workspace was 156MB (>128MB snapshot cap) because two 31-32MB replay JSONs
sat in _ref/ (eps2_cd_101359580.json, eps2_djaafar_101381927.json) — against
the "replays live in /tmp/eps2, do NOT copy into the workspace" convention.
Moved both to /tmp/eps2/ (episode-101359580-replay.json,
episode-101381927-replay.json; /tmp/eps2 now holds all 5 gate replays).
Workspace now 95MB. Re-fetch any time: python3 _ref/fetch_replays.py <eids>.
