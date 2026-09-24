# Kaggle — Kaggriculture Bots

Cameron's competition repo for the Kaggle **kaggriculture** farming-simulation
competition: bot sources, dated work sessions, replay intel, and test results.

## Layout

| Path | What's in it |
|---|---|
| `bots/` | Curated keeper bots — the good stuff. Start here. |
| `bots/top3-2026-09-23/` | Top-3 snapshot (2026-09-23): `tt_router_938`, `tetsu_r5_v11_adapeak2`, `v18_Adapt2Survive`, each a byte-identical `main.py` plus notes. |
| `bots/testver-compiler-v19/` | TestVer compiler v19 bot project (`main.py`, `agent/`, `scripts/`, `submit/`). |
| `bots/v18-adapt-2-survive/` | V18 Adapt-2-Survive bot project. |
| `bots/v15-adaptive/` | V15 Adaptive bot project (older generation). |
| `bots/kraggriculture/` | Kraggriculture bot sources (champion/candidate `main_*.py` series). |
| `bots/v7.3.py` | Single-file "Dairy Baron" bot. |
| `old-bots/` | Historical `HI_AgriBot_*` submission tarballs (champions & candidates). |
| `workspaces/` | Dated work sessions: reports, intel, matches, experiments. |
| `workspaces/2026-09-23/` | *(pending move — see note below)* |
| `workspaces/testing/`, `testing-compiler/`, `arena-ai/` | Test harnesses and experiment sandboxes. |
| `archive/` | Snapshot `.zip` files of old workspaces. Never delete — extract if needed. |
| `docs/chat-logs/` | Saved chat transcripts. |
| `docs/screenshots/` | Screenshots. |
| `data/saved-data/` | Saved ledger JSONL files. |

> **Note (2026-09-23):** `Workspace 9-23-2026/` is still at the repo root because an
> active analysis job is reading from `Workspace 9-23-2026/intel/` right now.
> Once that finishes, move it to `workspaces/2026-09-23/` with:
> `git mv "Workspace 9-23-2026" workspaces/2026-09-23`

> **Security note:** `archive/workspace-8-15-2026.zip` contains an old
> `.kaggle/access_token` file (a stale Kaggle API token — it does not match the
> current one). Do not extract/reuse it; rotate the token if it was ever valid.

## Where new work goes

- New dated session → `workspaces/YYYY-MM-DD/`
- New bot candidate → `bots/<name>/` (keep the submission-ready `main.py` at its root)
- One-off test results → `workspaces/testing/`
- Snapshot zips of retired workspaces → `archive/` (keep both the zip and the dir if both exist)

## Conventions

- Moves use `git mv` so file history is preserved — don't copy/paste in the file manager.
- Never commit secrets (`.kaggle/`, `*.pem`, tokens). Check `git status` before committing.
- `__pycache__/`, `*.pyc`, and other build artifacts are git-ignored.
