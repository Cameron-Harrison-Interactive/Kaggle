# Session 13 — 8-20-2026: the herd-speed pass — main.py now BEATS v2

## What you asked for: a focused pass on herd speed in main.py

Done. The herd was reaching 14 animals around day 20 (v2: day 13), and milk
was 40 vs v2's 152. After this pass, the herd reaches 14 by **day 14** and
main.py's milk/wool now BEAT v2's.

## The five bugs found and fixed (all measured)

1. **CARE was completely missing.** v2 cares for its animals daily, which
   banks a bonus paid on every production tick — effectively DOUBLING milk/
   wool output. main.py had zero CARE jobs (only a stale reference). Added
   CARE as a must-do animal chore. **This was the single biggest lever:
   $29k → $70k.**

2. **Herd placement built every pasture on the SAME tile.** `_herd_prep_jobs`
   didn't track which tiles it had already claimed, so animal #2+ got picked
   up but its PLACE was a no-op and it returned to the shed. Only ~1
   animal/day landed. Now each group claims a distinct pasture.

3. **The animal-buy running budget under-counted.** It ordered up to 3
   animals but subtracted only one's cost from the cash budget, mis-sequencing
   every later buy. Now it buys one at a time and charges the true cost.

4. **A 3-day wheat feed buffer locked cash.** We kept n×3+2 wheat, tying up
   $300-400/day while the herd starved for cash. Now a 2-day buffer, with
   bulk buying only when wheat is cheap.

5. **The buy gate was too strict.** Lowered from `cost + 250` to `cost + 60`,
   and raised the per-day cap from 2 to 3.

## Measured results (the numbers that matter)

### Solo vs PASS (10 seeds)
| | main.py | v2 |
|---|---|---|
| **avg** | **$73,965** | $66,302 |
| best seed | $95,383 | $73,820 |

main.py now **beats v2 by $7.6k**, with 92-95k peaks.

### The herd engine (seed 1)
| | main.py (now) | v2 | main.py (before) |
|---|---|---|---|
| milk sold | **194** | 152 | 40 |
| wool sold | **109** | 77 | 24 |
| fertilizer sold | **236** | 220 | 230 |
| herd at 14 animals | day 14 | day 13 | day 20 |

### Contested gauntlet (seeds 1,2,3)
| Opponent | before | now |
|---|---|---|
| mirror (v2 clone) | 0W-6L, −$18k | **5W-1L, +$4.9k** |
| cowbot (14 cows) | −$2.8k | **+$4.0k** (2W-4L) |
| sheepbot (12 sheep) | −$10.6k | **6W-0L, +$10.1k** |
| goosebot (10 geese) | −$2.8k | **6W-0L, +$38.3k** |
| cropbot (melon/straw mass) | −$29.9k | **4W-2L, +$3.6k** |

### vs the v25 tape (our $145k champion)
0W-6L, −$99k — still losing, but the reason is now isolated and honest: v25
sells **114 melons + 285 strawberries** to our 36 + 12. The herd side is won;
the crop-volume side is the next (separate) build.

## What this means
The herd-speed pass is complete and it flipped main.py from losing to winning
vs every archetype AND beating our own reactive bot solo. The season scheduler
(counter + dump prediction + sell-early + per-match crop config) from last
session is intact and now sits on top of a properly-fast herd economy.

**`main.py` is now the best bot in the workspace** ($73,965 avg solo, positive
margins vs all archetypes). The safe submit remains `agent/decision_agent_v4.py`
(+$18.3k vs cow-flooders, zero regression risk), but main.py has overtaken it
on raw strength.

## Files
- `main.py` — the bot (1,229 lines, stdlib only).
- `agent/decision_agent_v4.py` — the conservative safe submit.
- `scripts/{sim,planner,rules,search_params}.py`, `scripts/battle_contested.py`.
