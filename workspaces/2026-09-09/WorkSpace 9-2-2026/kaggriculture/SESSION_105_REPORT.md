# SESSION 105 — THE LIVE RATING PUZZLE & THE PATH TO #1 (Session 42, day 4)

*"We need to get 3000 rating to #1. Find something that wins!!!"*

---

## 1. WHAT WE LEARNED TONIGHT

### The local empire means nothing live
- **v11 is 300-0 locally**: 170-0 vs the August top-16 tapes, 80-0 vs every healthy
  public kernel (v27/hamburger/harvest/k2900/base/multiroute/shop_guard/v48),
  50-0 vs our own arsenal (v7b/c/e, v15, v18.8, v19, v20/b/c, W4). Zero ties vs any
  of them.
- **Live reality (user-confirmed 09-06)**: our rating is DROPPING (peak 2456 on
  09-05, falling since), W-L-T is mixed — losses and ties.
- v11 runs clean live (3 episode logs: sub-ms turns, no errors). Engine version
  matches (1.32.7 both sides). No seed bug ($110-200k on live-sized seeds).
- **Conclusion: the live mid-band (2400-2800) is full of private adaptive bots we
  have never seen, which counter v11's fixed compiled pattern. Local dominance
  ≠ live rating. The adaptive/public-kernel class rates 2700-2900 live.**

### The mirror-tie law (why ratings stall)
- v11 vs v11 = **10 exact ties / 10** (deterministic, seat-symmetric).
- Staff-confirmed: ties = half-wins in Bradley-Terry. Bots that tie their own
  lineage bleed rating potential.
- Wrapper attempt to break symmetry by holding sells: **measured disaster**
  (holding wheat/milk/wool/fert loses $70k+; hourly liquidation is a true
  equilibrium — v12 grid 0-10 across all 10 configs). Do not retry.

### Rating mechanics (staff, discussion 739410)
- **Team score = BETTER of the two active submissions. The 2nd slot is a free hedge.**
- Ties count half-wins each. Play rate may increase post-deadline.

## 2. THE LIVE POOL, RUNNING IN OUR LAB (new assets)

Extracted from public notebooks (topbots/poolsrc/) — all run on our engine:

| bot | solo | notes |
|---|---|---|
| v27_metareset | $169,270 | 25/27 top-30 strict-future replay claim |
| hamburger | $165,723 | "Anchor Exact"; contains the whole Kaito V12-V27 lineage unpacked |
| k2900 / v16_premium | $162,038 | Roman-Rozen-style: route + weed repair + front-run (MELON/MILK/STRB/WOOL, 1-step early, shop-dodge) |
| base_public | $141,089 | the base public kernel |
| harvest | $126,895 | **beats Kaito V27/Rayk C71/llcc 24-0 per its own benchmarks; beat all other publics + elite tapes locally** |
| multiroute_v21 | $109,935 | CD-class: 3 embedded experts (Moon/Mutoy/Munib) + opponent-classifier at step 1 |
| shop_guard / math / v48 | $81,709 | same base route; adaptive layers fire only vs active opponents ($96-100k vs v11!) |

Public H2H (local, 10 games): harvest > k2900 > v27 > hamburger; **non-transitive**:
harvest beats k2900 10-0 but loses 4-6 to v48/shop_guard; v48 ties shop_guard
6/10 (same lineage). The live meta is a rock-paper-scissors soup.

### Elite intel (fresh from Kaggle's daily top-episodes dataset)
- Source: kaggle.com/datasets/kaggle/kaggressu re-episodes-index → daily datasets
  (669 top games/day, avg rating ≥2882, ~32MB JSONs, anonymous download OK).
- Sept-4 elite games = keiz vs Jesse Bullard vs Crop Dusta; finals $59-95k,
  margins 5-15%. Elite builds: wheat engines (CD sold 2,153 wheat in one game),
  strb ~30 tiles, herd 7-13c + 4-12s + geese, fert 200-320 sold, everyone
  differentiates their sell mix (CD wheat-heavy, keiz strb/carrot, JB fert/milk).
- Elite money curve: $10-20k@d8-12, ~$50k@d20, $75-89k@d28.
- Current top-5 (09-06): kwa 2951.2, keiz 2888.9, Mengfei Li 2871.4,
  Crop Dusta 2869.8, CemBas 2849.0. Nobody at 3000+ tonight — the bar moves.
- Tapes saved: analysis/elite_tapes/ (keiz/JB/CD, live seeds, + census.jsonl).

## 3. THE DECISION — TWO SLOTS, TWO HORSES

- **Slot A (already live): v11.** 300-0 locally; may still climb; zero risk to keep.
- **Slot B (SUBMIT TODAY): harvest** — `submission_harvest_slotB.tar.gz`
  (workspace root; tar = main.py, verified byte-identical to the tested agent).
  Rationale: dominant vs the public soup + elite tapes locally; its class rates
  2700-2900 live; slot B is a free hedge (staff-confirmed best-of-two).
- Watch both for 24-48h. Whichever converges higher becomes the horse.

## 4. THE PATH TO #1 (3000) — the build program

1. **Live-loss telemetry**: user downloads our live episode replays (episode
   page → download JSON) for 2-3 losses + 2-3 ties → we decode exactly what
   beats/ties us live. THE critical missing data.
2. **Improve harvest** (we hold full source): graft our advantages —
   continuous premium-gated selling (market decode: I0=10000, crash curves),
   the W4 SE-quad economy, terminal sweep, front-run all 9 products
   (k2900 only front-runs 4), tie-breaking route switching (multiroute's
   opponent classifier).
3. **Pool-sim gate**: beat {harvest, v48, k2900, v27, multiroute, elite tapes}
   round-robin before any submission swap.
4. Target: public-class base (~2850) + our edges = 2950+.
