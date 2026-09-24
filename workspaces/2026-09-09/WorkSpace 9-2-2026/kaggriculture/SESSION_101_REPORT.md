# SESSION 101 — composition search (the "new tape" question), first real results

Answering directly: sessions 99-100 optimized the *existing* tape. This session
attacks the composition question — is 4 sheep / 11 cows / 0 geese / 41 strawberry
the right farm, or was it just the farm we happened to author?

## 1. Composition sweep *in situ* (same walks, animal kind flipped per placement day)

v1112fr's herd: 4 SHEEP placed D0, 11 COWS placed D4/D6/D7/D8/D10.
Flipping the kind of a whole placement day (both use PASTURE, so walks stay valid),
seeds 1-3 solo:

| change | avg Δ |
|---|---|
| D4 cow → sheep | −8,290 |
| D6 cows → sheep | −50,518 |
| D7 cows → sheep | −38,859 |
| D8 cow → sheep | −18,519 |
| D10 cows → sheep | −8,346 |
| drop the D8 cow entirely | −17,894 |
| drop the D10 cows entirely | −15,621 |
| (session 99) all 4 D0 sheep → cows | −114,890 |

Read: the herd is at a local optimum on every axis reachable without re-authoring
walks. **Cows are worth ~$16k each in situ** (mostly cascade: milk + fertiliser +
cash timing feeding the next expansion), and the 4 D0 sheep are worth even more as
the D6 cash wave. No composition edit on the current tape is positive.

## 2. So why not just add more cows? Labour + feed, not land

Marginal-cow arithmetic for an SE expansion (SE = $4,000, 25 tiles):
* 12 cows placed D12 → first yield D20 → ~5 events × 2 (cared) = ~120 milk
  → ~$28k at declining price (milk drops from $276 toward ~$200 as we supply).
* costs: land $4k + cows $4.8k + feed wheat 12/day × 17d × ~$45 = $9.2k
  + 3 extra hands to service them (fib slots 12-15 ≈ $1.2k/day × 17d) = ~$20k.
* net ≈ **−$10k**, same shape as the egg platform (−$19,980) but less bad.

The wall is the fib hire ladder plus $45 feed wheat, not the animal we pick. This
is consistent with session 99's hire-cap test (12th hand worth $5.6k, 13th $0.3k).

## 3. From-scratch authored tape — the honest state

`_ref/tape_author.py` (v3 design: 16 animals, melon+wheat, 7 hands/day) still runs
and emits a 720-step tape, but **the regenerated tape goes bankrupt** (money 0 by
~D16, hands stop being hired). The shipped artefact `topbots/v120_puretape.py`,
which came out of that line of work after hand repair, scores:

| seeds 1-4 solo | v1112fr | v120_puretape |
|---|---|---|
| avg | 176,833 | 172,355 (**−4,478**) |

So an independently authored, fully non-adaptive tape lands within 2.5% of the
tuned live bot. That is the only viable base for a real composition search, because
its walks are *generated from a spec* rather than hand-authored.

`_ref/tape_author2.py` (new) parameterises that author: `TAPE_SPEC` env var takes
`{"SHEEP":n,"COW":n,"GOOSE":n,"hands":n}`, adds GOOSE support (BUILD_COOP,
egg cadence placed+4 every 2 days, EGG sells) and a hands/day knob.
`_ref/sweep_comp.py` builds + scores any spec list. Both work end-to-end; the
blocker is that the author's cash schedule (`wheat_buy`, hire ramp, first income
day) is not solvent, so every spec currently scores 0.

## 4. What a real new-tape project needs (next block, in order)

1. Fix the author's solvency: income-before-spend ordering, wheat-buy schedule tied
   to actual feed demand, hire ramp tied to cash, first melon/wheat harvest by D5.
   Gate: authored default spec ≥ $150k solo on seeds 1-3.
2. Then run the composition sweep that is already written (herd mix × hands/day ×
   crop mix), 3 seeds per spec, ~1 s per game.
3. Take the top 3 specs to 16 seeds + H2H vs v1112fr and the recorded metas.
4. Only then decide whether the authored line can beat the tuned tape.

That is a multi-block build, not a one-shot. It is the only path left that is not
worth ~$0 — every in-place lever measured over sessions 99-101 is exhausted.
