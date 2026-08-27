# SESSION 23 — The phantom-worker bug (the big one) + SW unlock + no escapes

**Date:** 2026-08-21  ·  **Bot:** `main.py` (1,640 lines)  ·  **Tool:** `watch.py`

---

## The honest bottom line — this was the big one

You said "we shouldn't be losing anything with our planner" — that sentence led
me to a real bug that was quietly breaking the whole late game, and fixing it
is the biggest single win of the whole project.

**Solo: $88.5k → $97.6k** (10 seeds) / **$97.6k** (20 seeds). **Animal escapes:
0.** SW now unlocks.

---

## 1. The phantom-worker bug (fixed)

The planner was deciding it needed **14–16 workers** on busy days, but hour 0
can only place **10 market orders** (1 wheat buy + 9 hires) — so only ~9 hands
ever actually existed. The plan still handed jobs to workers 10–16, and those
jobs **never ran**. That's why:

- the field emptied out at day 25+ (the planting jobs went to ghost workers),
- animals escaped (the feed jobs went to ghost workers) — your seed-3
  "lost animals then repurchased them",
- everything looked like we "weren't thinking".

**Fixes:**
1. Hires that don't fit hour 0's cap now **carry over to hour 1**, so the crew
   the planner assumed is the crew that exists (verified: planned 16 → 16
   hired).
2. The animal sweep's wheat pickup was capped at `wheat_batch=5`, so when hands
   were short and one worker's slice held 7+ animals, the tail of the slice
   went unfed and escaped. Now a worker picks up wheat for **its whole slice**.

Result: **0 animal escapes across 20 seeds** (was 3–10/game), and solo jumped
~$10k.

## 2. SW now unlocks (land gate relaxed)

`land_density` 0.9 → 0.8 and the crop-town cutoff moved 15 → 19. Land timeline
now: NE ~day 11, SW ~day 16–23, instead of "SW never". It still only unlocks
when the earlier quads are mostly full — just not impossible-to-fill full.

## 3. Late-game fill

We now keep buying/planting wheat (and carrots from day 23) through day ~26, so
the field stays at ~24 crops until the final harvests, then the day-28/30
terminal sell clears everything. (I tried *bulk* late buying — 12 wheat +
8 carrots/day — and it lost money: the extra late plants eat water/hands and
some never mature. Reverted to the moderate fill.)

## 4. Where the gauntlet sits

| opponent | result |
|---|---|
| cowbot / sheepbot / goosebot / cropbot | **6W-0L** (+$22k to +$44k) |
| mirror | 4W-2L, +$7.8k (two games lost by $3k–$7k) |
| v25 tape | 0W-6L, −$73k (3-seed, noisy) |

The mirror wobble is the town-herd betting wrong on two mixed towns (we run the
small herd, the clone runs plain 10 cows, and on those draws the cows win by a
few thousand). The 10-seed solo gain is far bigger than those two small losses,
so I shipped it — but tell me if you want the herd a little less aggressive on
uncertain towns and I'll tighten it.

## Watch it

`watch.html` regenerated. Scrub days 15–28: you'll see SW unlock, the full crew
show up (no more ghost hands), and the animals stay fed the whole way.

**Next, in priority order:** (1) tighten the town-herd for the mirror matchups,
(2) keep pushing the tape gap now that the economy actually runs at full
strength — the +$10k solo means we're finally comparing apples to apples.
