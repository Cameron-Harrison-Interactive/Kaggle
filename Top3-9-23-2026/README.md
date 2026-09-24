# Top 3 Bots — consolidated 2026-09-23

Strongest 3 bots across the whole repo, ranked by best credible score.
Each subfolder holds the bot's `main.py` (byte-identical copy of the original).

## 1. `tt_router_938/` — 2483.7 LB (peak 2550.2), Sep 7–8
- Source: `Workspace 9-9-2026/WorkSpace 9-2-2026/kaggriculture/topbots/tt_router_938.py`
- Score: **2483.7 leaderboard publicScore (peak 2550.2)** — `Workspace 9-15-2026/archive/SESSION_125/127_REPORT.md`
- Strategy: six-day replay portfolio — replays action tapes extracted from top players' public replays. Submitted as Kaggle #56079632 (resubmitted #56100058).
- Self-contained: tapes are embedded (base64+zlib) in main.py.

## 2. `tetsu_r5_v11_adapeak2/` — 2325.5 LB, submitted Sep 5
- Source: `Workspace 9-15-2026/archive/submission_tetsu_r5_v11.tar.gz` (verified identical to `Workspace 9-9-2026/war/tetsu_r5_v11_adapeak2.py`)
- Score: **2325.5 publicScore** — `Workspace 9-23-2026/chatlogs/`
- Strategy: tetsu-style high-volume strawberry factory line ("adapeak2 W36A2R717").

## 3. `v18_Adapt2Survive/` — 2739 rating ("best ever"), Aug 10–11
- Source: `TestVer-Compiler_v19/submit/HI_AgriBot_v18_Adapt2Survive.tar.gz` (verified identical to `TestVer-Compiler_v19/agent/main.py` and `V18 - Adapt-2-Survive/agent/main.py`)
- Score: **2739 live rating ("best ever")** — `TestVer-Compiler_v19/STATUS.md` + `WorkSpace 8-14-2026` README. Older (mid-Aug); ratings drift with the player pool, so not directly comparable to September numbers — but it's the proven ceiling.
- Strategy: frozen dual-seat route tape + Adapt-2-Survive overlays (opponent-family classifier, strawberry→tomato swaps, price-impact SELL ranking, terminal liquidation).

## Notes
- Score eras: Kaggle publicScore/rating (hundreds–thousands) is the real metric from mid-Aug onward. Early-Aug "gold"/coins scores (55k–69k) and local solo-$ sims are not comparable.
- Next objective: clone rival "unknown mother goose" (only intel: `Workspace 9-23-2026/intel/ladder_doc_picture.md` — ~36 berries, crew 13, non-standard variant; rose to top between Sep 2–17). No code/replay in repo — needs a live Kaggle pull of its public notebook/replays, then run through the tape-extraction pipeline (`topbots/` builders).
