# Session 15 — 8-20-2026: batched labor + town-shop-mix exploitation

## What you asked for
1. The batched animal-chore refactor (one sweep per worker) to free the crew
   for crops.
2. Make sure the bot actively exploits the town shop mix — which most ladder
   bots ignore, since they run the same crops every match.

Both are done and measured.

## 1. The batched animal sweep (the labor fix)

The animals already live in a tight cluster next to the shed. The waste was
the chore ASSIGNMENT: every feed/collect/care/harvest went to whichever worker
was nearest at that moment, so the crew spent ~56 scattered walks on 14
animals and had zero capacity for 66 empty tiles (measured: all 10 workers
maxed at 24 turns, seeds sitting unplanted).

New design: each worker sweeps a CONTIGUOUS slice of the animal cluster in one
pass — one wheat pickup, then feed / collect / harvest / CARE with ~1-step
walks between adjacent pastures. The key bug from my earlier attempt was fixed
this time: CARE was `elif`-chained behind COLLECT (so care silently never
happened and milk died). Now every chore is its own independent action.

Result: milk 216 (v2: 152), wool 106, fertilizer 265, and the herd stays
**zero-unfed** all game.

## 2. The 14-animal herd cap

The town-herd sizing from last session could push cows to 12 AND sheep to 10
(16-20 animals), which we couldn't afford to feed — animals starved and
escaped. Now the herd REBALANCES within the proven 14-animal cap: milk town =
12 cow + 2 sheep, wool town = 4 cow + 10 sheep, balanced = 10 + 4, egg town =
geese *instead of* cows/sheep. Feed cost stays affordable, zero escapes.

## 3. Town-shop-mix exploitation (your ladder-advantage point)

- **Town-driven herd sizing** — cows/sheep/geese sized to what the town buys
  (milk towns → cows, wool towns → sheep, egg towns → geese).
- **Carrots on carrot-towns** — when a Pet Cafe / Farmers Market opens (carrot
  demand ≥ 12), the bot buys carrots EARLY (before day 15, so the 3-day cycle
  pays) and plants them. Seed 7 (3 Pet Cafes) went $45.8k → $58.9k.
- **Tomatoes, capped** — only a couple, only when 2+ pizza-type shops want
  them, early; their yield is weak so we don't mass them.
- **Stronger town tilt** in crop choice — a crop the town is eating keeps its
  price high no matter how much we dump, so we lean into it.

## Measured results

**Solo (10 seeds):** $78,966 avg (min $58.9k, max $93.7k) — up from $70.6k,
beating v2's $66.3k by $12.7k.

| Opponent | before | now |
|---|---|---|
| mirror (our clone) | ~$0 | **+$7.7k, 4W-2L** |
| cowbot (14 cows) | +$16.7k | **+$19.8k, 6W-0L** |
| sheepbot (12 sheep) | +$7.7k | **+$18.6k, 6W-0L** |
| goosebot (10 geese) | +$25.7k | **+$43.8k, 6W-0L** |
| cropbot (melon/straw mass) | −$3.5k | **+$11.4k, 6W-0L** |
| **v25 tape** | −$99k | **−$69k** |

Every archetype is now beaten, including our own clone (anti-mirror works) and
the crop-heavy tape-style bot. The v25 gap narrowed from −$99k to −$69k.

## The remaining gap, stated plainly

v25 still wins solo $145k to our $79k. Its edge is raw crop VOLUME: 114
melons + 285 strawberries to our ~40 + ~20. We hold ~15-22 standing crops to
v25's ~60. The batched sweep freed the labor; the remaining constraint is
seed supply + the per-tile plant cost (each new plant is walk + plant + water
= ~3-4 turns). That is a volume problem, not a strategy problem — the strategy
(counter + town + market + dump prediction) is now complete and winning every
archetype.

## Files
- `main.py` — the bot (1,373 lines, stdlib only).
- `agent/decision_agent_v4.py` — conservative safe submit (unchanged).
- `scripts/{sim,planner,rules,search_params}.py`, `scripts/battle_contested.py`.
