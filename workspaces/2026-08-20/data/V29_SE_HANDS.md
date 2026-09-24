# Dedicated-Hands SE Quad — full experiment log (2026-08-15)

User's plan: "unlock SE by d15, sit on strawberries/wheat/carrot, 2 hands
dedicated per quad — like our early crops-only versions with per-quad routing."

## The historical record (recovered from GitHub)
- Chat-Log-2 (line 12368, user's own words): "i want to keep 3 workers per
  quad and allow them to only stray from their paths after they have gone
  through their designed path" → v5.7a design: 12 hands, 4 quads, lanes
  0/1/2 per quad, flipped from the shed-side entry corner. That era scored
  ~37-41k — and it worked because the economy then had IDLE capacity.
- ROUTING_BIBLE.md: the ancestors already tested SE unlock in the v14.5
  era: **"SE unlock (4th quad) −9.5k vs 14.5"** — rejected then too.

## The modern tape's worker census (v25, seed 1 — the key data)
- 15 workers on peak days; re-hired DAILY (fibonacci ladder: 11 hires/day
  ≈ $1,160 — extra hands are unaffordable: 2 more = $1,885/day).
- w2/w3/w6 = daily-constant crop workers (0-10 animal ops) — looked like
  the perfect dedicated hands.
- **But the tape's plant mix at d12 is 36 STRAWBERRY + 14 MELON + 13
  WHEAT** — it IS already a strawberry economy, and w2/w3's "crop work"
  is the SW harvest chain that supplies the d13-19 sell wave AND the
  shed wheat that feeds the herd.

## The three executions (engine as judge, PASS seeds 1-3 both seats)
| Execution | Result | Mechanism |
|---|---|---|
| SE unlock only (d11h1/d12h1) | **−$2.6k..−$6.5k** (matches ancestor −9.5k) | land is a dead $4,000 with no program |
| Dedicated hands w2/w3: delete crop anchors d12-26, add SE strawberry program (24 tiles, plant d12/d16, water alt, harvest d26/d28, sells) | **−$62k, animals 13→2, 20 weeds** | deleting w2/w3's harvest cycles broke the shed-wheat supply → FEEDs starved → escapes + mid-game sell chain collapsed |
| Dedicated hands via inter-anchor GAPS only (no deletion) | **0/24 plant windows on d12-15** | the tape has zero idle slack; gaps are 1-4h shards, smaller than any SE round trip |

## The definitive conclusion
1. The early "per-quad routing" philosophy worked at ~40k because the
   economy had idle hands. The 145k tape has NONE: every worker-hour is
   priced into a load-bearing chain (feeding, harvest→sell, flood).
2. The SE quad pays only inside a FULL re-allocation — explicitly deciding
   what to give up (herd mix, flood tail, water redundancy) and re-balancing
   the chains — which is exactly the ledger portfolio search
   (scripts/ledger_planner.py, V29_PLANNER.md).
3. The data needed to run that search is now complete: worker census,
   daily hire map, per-day gap map, wheat-stock cycle, strawberry
   production economics (3 units/tile from a d12 plant, ~$105/unit).

## Bottom line for shipping
v25 Wheat16 remains the post. Every single-axis idea — market, animals,
land, choreography, dedicated hands — is now measured and closed with
numbers. The Holy Grail is the portfolio redesign, and all its inputs are
on the table.
