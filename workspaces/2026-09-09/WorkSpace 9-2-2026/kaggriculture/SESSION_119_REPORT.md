# SESSION 119 — Router Upgrade Campaign: Every Path Tested, The Verdict

**Time:** 2026-09-07 ~20:10 UTC · User: "Look through the router and make upgrades vs the
things we lost. We need to get into the 2800 bracket." (No submissions — all offline.)

---

## The router, read completely

- 5 tapes (all wheat/strb/melon/carrot family; herds 5C/4S/4G, 7C/3S/3G, 6C/3S/4G, 5C/8S)
- Feature vector: both farms' money, prices, inventories, shops, demand, both farms'
  tile counts/yields, shed, seeds — ~100 dims
- Decision trees (blocks = day 0/6/12/18/24; real branching only at day 6 & 24)
- **Sells are price-blind tape replays** — that was the upgrade target

## Live twins confirmed

First 12 games: 5W-2L-5T. The 5 ties = verbatim twins (Igor Zharov, Ace Team, Agricola,
HIDEYO CHIBA, Juyong — 30-vote kernel = twin army; identical $79,356=$79,356 games).
The 2 losses (Ant, bharat) = tuned variants.

## Upgrades built and gated (all vs the verbatim router, 20-seed twin tests)

| Candidate | Idea | Result | Verdict |
|---|---|---|---|
| v24 | full market brain: milk/wool/strb/melon strength-sells, egg clear, endgame dump | 7W-13W, −$1,190/game | FALSIFIED |
| v25 | minimal: eggs + strb$180 + melon$220 + endgame only | 7W-13W, −$1,355/game | FALSIFIED |
| **CONTROL** | **router vs itself, same seeds/seats** | **0W-3W-17T** | — |
| v26 | Ant's own tape (their 8C/6S/3G = 17-animal herd, extracted from the loss replay) | 0W-6W vs router | FALSIFIED |

**The control is the finding:** identical routers tie 17/20 — and a tie is worth half a
win in BT (17 ties = 8.5 pts). My overlay broke the symmetry into 7W-13L = 7.0 pts —
WORSE than doing nothing. Thomas's tape tuning is genuinely good: every deviation we
tried (market overlays in two strengths, grafted variant tapes) loses on average.

**Ant's decode (the loss that started this):** 17 animals (8C/6S/3G) bought early
(2C+2S at d0h2), geese d10-11 — a bigger-herd variant tape. It beat us once live, but
its blind replay loses 0-6 to our router: their win was context, not class.

## The verdict for the 2800 push

1. **The router stays verbatim** — it's at **2540.8** and climbing (600→2540 in ~1h;
   the fastest climb we've ever had; already above our all-time best 2526.5).
   v16 (1909.1) holds the second slot as the floor.
2. Its ceiling threats, in order: tuned variants (Ant-class — but measured: their
   tapes don't generalize), twin ties (half-wins — actually rating-PROTECTIVE),
   and the true elites (2800+ camp — complementary portfolios).
3. Remaining upgrade paths not yet falsified:
   - **Retrain the trees** (5 small trees [1,5,1,1,3 nodes] — grow our own on sims
     vs the twin/meta pool; the architecture accepts new trees directly)
   - **Herd-scale tape authorship** (17-animal line + its matching labor plan —
     the labor-planner problem, now with a readable spec)
   - Both are 1-2 session projects. Neither is a tonight fix.

## Files
- topbots/tt_router_v24_market.py, tt_router_v25_minmarket.py (falsified overlays)
- topbots/ant_tape_v26.py (falsified graft)
- topbots/tt_router_938.py (the live 2540 asset — UNTOUCHED)
