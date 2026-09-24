# ULTIMATE SEARCH v3 — PARALLEL (8 cores)

## Your Rig
- Ryzen 7 3700X: 8 cores / 16 threads
- 64GB RAM
- 12GB VRAM GPU (not needed for this)

## Run It

```bash
# Setup (one time)
pip install kaggle-environments==1.32.6

# FAST SEARCH: Focus on Kawashigi (#1) + v25 mirror + 3 seeds
# ~6.7 min/generation, ~55 hours total
$env:PYTHONUNBUFFERED="1"; python3 scripts/evo_search.py --generations 500 --population 80 --seeds 1,2,3
```

That's the one you want. It focuses on beating the two hardest opponents (Kawashigi + our own v25 mirror) across 3 seeds. Once it finds a champion, you validate it against all 6 opponents.

**Speed:**
- 2 opponents × 3 seeds × 2 seats = 12 games per variant
- 80 variants ÷ 8 cores × ~60s = **~10 min per generation**
- 500 generations = **~83 hours (~3.5 days)**

## If PC Stops / Ctrl+C

```bash
$env:PYTHONUNBUFFERED="1"; python3 scripts/evo_search.py --generations 500 --population 80 --seeds 1,2,3 --resume evo_results/state.json
```

**Ctrl+C = SAFE SAVE.** Auto-checkpoints every generation.

## Watch live progress (in a SECOND PowerShell window):
```powershell
Get-Content evo_results\search.log -Wait -Tail 10
```

---

## What It Does

**PARALLEL:** Evaluates 8 variants simultaneously (1 per core)
**BATTLES:** Kawashigi (#1), indarkarhana (top 10), v25 mirror, cowbot, healthstone, seb
**NEVER PASS:** Only real opponents
**18 DIMENSIONS:** crops, animals, wheat volume, land timing, CARE, fertilizer, route paths
**10 SEED STRATEGIES:** Starts smart, evolves beyond

## What Top 10 Players Do (from Kaggle dataset analysis)
- NEVER plant tomatoes (-87%)
- HOLD through price crashes (melon min $13 vs $32)
- Slightly more workers (+3%)
- Same core crops: ~102 wheat, ~37 straw, ~23 melon

## Hidden $20k in Our Tape
- 25% fertilizer UNCOLLECTED = ~$6k wasted
- 27% animal CARE missed = ~$8k bonus lost
- Fertilizer on wheat = LOSS. On strawberry = +$380/tile

---

## Send Me These Files

**Always:**
1. `evo_results/search.log`
2. `evo_results/best.json`

**If champion found (beats all opponents 75%+):**
3. `evo_results/champion_tape_s0.json` + `champion_tape_s1.json`

**To resume:**
4. `evo_results/state.json`

---

## Timing Estimates

| Config | Sequential | 8 Cores | Calendar |
|--------|-----------|---------|----------|
| Pop 80, 500 gen, 8 seeds | ~655 hrs | ~82 hrs | ~3.4 days |
| Pop 100, 1000 gen, 10 seeds | ~2040 hrs | ~255 hrs | ~10.6 days |
| Pop 50, 200 gen, 8 seeds | ~164 hrs | ~20 hrs | ~0.8 days |
