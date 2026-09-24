# SESSION 107 — Elite Decode + the Route-Class Play

**Time:** 2026-09-06 ~06:45 UTC · Mission: 3000 / #1 (kwa 2951.2)

---

## TL;DR

While v4b-fixed climbs, I decoded the 2950-class from the elite daily dataset and our loss
replays, then submitted the highest live-proven public chassis as the upside slot:

| Submission | Ref | Live status |
|---|---|---|
| **v4b-fixed** (2526-class floor) | 56047687 | 1139.3 and climbing (600→820→1026→1139) |
| **2900-verbatim** (route class) | 56048083 | Fresh 600; first two games: **$147,888 vs $56,186 W** and **$118,230 vs $42,949 W** |

1 submission left today (reserve). Team score = max of actives.

## The elite decode (full detail: `analysis/ELITE_DECODE_0906.md`)

Three laws, extracted from keiz/JB/MaterW/Dmytro games (09-05 top dataset) + our loss replays:

1. **Wheat-fert loop = the volume base.** keiz: $52-60k wheat (1,188-1,495u) via 24 tiles
   fertilized by a 14-cow herd (cows = fertilizer factories, not milk).
2. **Premium windows, low volume.** MaterW milk 226u @$202 at h14/h18/h22; k2900 milk
   120u @$243. Our class dumps milk at h7 into the $4 floor.
3. **Differentiation law: overlap crashes, differentiation pays.** Mirror-vs-mirror with
   the same portfolio: both sides $43-77k. Differentiated elites: both $111-134k.

**Crash autopsy:** in our $43-73k games, opponents run OUR exact build. STRB holds $186-194
until d17, then both sides' 33-tile engines dump 12-18u/day total → $1 floor by d20,
PERMANENT (no bounce — supply >> demand forever). Wheat+FERT survive (deep demand). Every
crash-game winner had **CARROT $3.8-4.8k — the uncontested niche we don't run.**

No sell-timing overlay can fix this: portfolio composition is the only lever.

## The route-class play (why 2900-verbatim)

The route class embodies laws 1-2 by construction (premium-window seller: milk @$243,
wool @$181, strb @$139, low volume). The public "2900" notebook is a live-proven chassis
(Roman Rozen's class rated 3044.6 public). Submitted VERBATIM (zero extraction risk),
entrypoint verified (`agent` = last callable in module dict — the entrypoint law from
today's post-mortem).

- k2900_extracted (our cleaned version): solo $154,421 — kept as backup/future base.
- v27_metareset: solo $120,479, entrypoint verified correct — future candidate.

## Next-gen design brief (goose line, for the remaining slot when ready)

1. Wheat-fert loop base (24 W tiles + 8-9 cows)
2. Premium-window selling only (price-aware sells, never dump into crashes)
3. **Adaptive niche anchor:** read opponent's public tiles by d8 → if their portfolio
   collides with ours, pivot plantings to carrot/tomato (PET_CAFE carrot demand is
   uncontested; keiz runs 30 tomato tiles as his differentiator)
4. STRB discipline: sell d14-17 at $180+; stop below $80

## Standing state

- Active pair: **v4b-fixed + 2900-verbatim** (harvest E283 displaced at 1330.9)
- Quota: 1 left today, resets daily
- Next checkpoints: overnight convergence of both actives; goose-line build session
