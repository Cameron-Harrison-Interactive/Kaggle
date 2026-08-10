# Kaggriculture — HI_AgriBot v8 "Field Marshal"

A top-target agent for the **Kaggriculture** Kaggle simulation (30-day, 720-turn
farming economy, head-to-head, most coins wins). Built by studying your GitHub
history, the official rules, and the two highest-scoring public replays, then
iterating locally until it beat every bot you've shipped.

**The coverage finding (2026-08-09):** pulling our live replays confirmed every
loss was a coverage loss (winners held 40-58 crops, we held 27-30). So we tried
hard to fix it — serpentine lane sweeps, +workers, freer planting — and reached
41 crops. **But every high-coverage build lost 0-4 head-to-head to v9.1.**
Forcing more crops than our watering can support just weeds them out and thins
labor. The winners hold 55+ crops *and* have ~47% walking efficiency; our ~58%
walking caps profitable crops at ~33. Coverage only pays after movement
efficiency improves. So the flexible job board (v9.1) remains champion — it wins
every coverage duel and is proven live.

**Results (v9.1 build):**
- Local vs `starter`: mean **$96k** (max $111k) across 6 seeds, **0 escapes**
- Self-play (contested market, the ladder-like benchmark): **~$69-76k/match**
- Peak crops **33** (the profitable ceiling at current watering efficiency);
  leftover seeds ~21 (demand-aware buying)
- Beats every high-coverage variant **4-0** head-to-head
- **LIVE on Kaggle:** v8.x reached **812.5** rating
- **Market brain**: reads market inventory, price momentum, and the OPPONENT'S
  build every turn — dumps products ahead of opponent-caused crashes
- Ongoing crops (strawberry/tomato) watered survival-only per the rules
  (no yield from daily water) — freed labor goes to filling more dirt
- 3 tenders measured optimal (4 caused escapes, 2 starved animals)

---

## Folder layout

```
kaggriculture/
├── agent/main.py            ← THE agent (single file, Kaggle-ready)
├── submit/                  ← always-current submission artifacts
│   ├── main.py              ← copy of agent/main.py (the "Submit file")
│   ├── HI_AgriBot_v8_FieldMarshal.tar.gz
│   └── BUILD_INFO.txt
├── scripts/
│   ├── run_local.py         ← test harness + invariant audit
│   ├── build_submission.py  ← smoke-test + package submit/
│   ├── submit.sh            ← one-command Kaggle upload
│   ├── analyze_replay.py    ← per-player strategy stats from a replay JSON
│   ├── opp_v7.3.py          ← your v7.3, kept as a sparring partner
│   └── opp_v6.5.py          ← your v6.5, kept as a sparring partner
└── data/
    ├── META_STUDY.md        ← decoded strategy of the $139k-$141k leaders
    ├── replay_90615567.json ← Seb ($139k) vs THUNDER analysis
    ├── replay_90697169.json ← sleepyai ($141k) vs venks analysis
    ├── replays/             ← raw downloaded top replays
    └── reference-repo/      ← full clone of your GitHub repo (all versions)
```

---

## How the agent thinks (the "brain")

It is **not** a route/DNA script like v5-v7. Every turn a central planner
enumerates *every* job on the farm, scores it by economic urgency, and assigns
each job to exactly one worker — so hands never converge on the same tile.

**Priority ladder (lower = more urgent):**
| Tier | Job | Why |
|------|-----|-----|
| 0 | Emergency feed (unfed≥1), water fresh seed | animal escapes / seed dies *tonight* |
| 1 | Survival water (unwatered≥1) | crop weeds tomorrow if skipped |
| 2 | Routine feed | keep `consecutive_unfed` at 0 |
| 3 | Harvest ripe crops, yield-water, place animals | income |
| 4 | CARE / COLLECT_FERTILIZER / build pasture | the milk & fert engine |
| 5 | **PLANT** (boosted to tier 3 while <30 crops) | the "fill every plot" mandate |
| 6 | Dig weeds | hygiene |

**Labor division (decoded from the leaders):** farmer + first 2-3 hands are
**tenders** for the animal corridor; the rest are **crop workers**. Roles
overflow into each other only when their own queue is empty.

**Sticky targets:** a worker keeps walking to its committed job until it's done,
which killed the A↔B oscillation that wasted ~60% of turns as pure walking.

**Market timing:** premium goods (milk/wool/strawberry/melon) have crash-prone
price curves. The agent holds product **on the animal** (free warehouse, max_held)
when price is crashed and sells into the recovery — this alone lifted milk from
~$58 to ~$255/unit in contested play.

---

## What I studied and copied (data/META_STUDY.md)

From replays **90615567** (Seb $139k) and **90697169** (sleepyai $141k):
- 3 quadrants (NE day 7, SW day 11), **never SE**; 8 cows + 6 sheep
- Day-0 opening: 5 hires, 2 cow + 2 sheep, 7 wheat + 12 melon seed, 5 wheat
- **CARE every animal every day** → doubles milk/wool output (the real engine)
- Fertilizer = 1/animal/day free money, sold daily; a slice goes onto melons
- Top players are **net wheat sellers** and batch-sell into healthy prices

Your own failure history (STATUS.md / OUR_MATCHES_ANALYSIS.md) told me what NOT
to do: sell feed wheat, skip DIG, under-plant, and the v6.2/v6.6 4-quad builds
that starved 16-20 animals.

---

## Run it yourself

```bash
cd kaggriculture
pip install -U kaggle-environments

# WATCH a match (opens the visual replay in your browser):
python3 scripts/watch.py              # OUR BOT vs OUR BOT, seed 1
python3 scripts/watch.py 7            # self-play with a different start (seed 7)
python3 scripts/watch.py 7 starter    # or vs any opponent
python3 scripts/watch.py --latest     # our newest LIVE Kaggle episode
python3 scripts/watch.py --episode 91131124

# quick match vs starter
python3 scripts/run_local.py agent/main.py starter 1

# head-to-head vs your old bots
python3 scripts/run_local.py agent/main.py scripts/opp_v7.3.py 1
python3 scripts/run_local.py agent/main.py scripts/opp_v6.5.py 1

# self-play (contested-market stress test)
python3 scripts/run_local.py agent/main.py agent/main.py 1
```

`run_local.py` also audits invariants each match: animal escapes, weed-outs,
crop fill, fertilizer sold, and shed leftovers at turn 720.

---

## Submit to Kaggle

The submission artifact is kept current in `submit/`.

```bash
cd kaggriculture

# 1) package the current agent/main.py (runs a smoke test first)
python3 scripts/build_submission.py

# 2) upload (needs KAGGLE_API_TOKEN or ~/.kaggle/access_token)
./scripts/submit.sh "HI_AgriBot_v8_FieldMarshal"
```

Or submit manually:
```bash
kaggle competitions submit kaggriculture \
  -f submit/HI_AgriBot_v8_FieldMarshal.tar.gz \
  -m "HI_AgriBot_v8_FieldMarshal"
```

Your KGAT token is already installed at `~/.kaggle/access_token`, so
`submit.sh` works as-is.

---

## Known limits / next steps

- **Crop fill vs. survival is the binding trade-off.** The watering crew caps
  safe crops at ~30. Forcing more raises weed-outs (tested). To reach the
  leaders' 40-55 crops you'd need dedicated *column-sweep* watering lanes
  (lower walking overhead) — that's the single highest-value upgrade left.
- A sheep occasionally rides in the shed at turn 720 (~$0.5k, cosmetic).
- Contested-market revenue is the leaderboard lever; keep iterating on
  sale pacing and wheat self-sufficiency (net-wheat-seller build).

**Leaderboard note:** v8.0 debuted live at **707.1** (up from 617.8), 2-0.
The current `submit/` package is **v9.1** — the tarball name always matches
the VERSION constant in agent/main.py exactly.
