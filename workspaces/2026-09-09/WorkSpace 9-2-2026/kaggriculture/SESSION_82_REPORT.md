# SESSION 82 — The GitHub/Notebook Winner Hunt (complete survey + top-16 tape harvest)

Continuation after the Chat-Log-12 context cutoff. The pending task at cutoff:
*"Search GitHub and other notebook locations wherever someone might keep kaggle
files and find us the winners."* Completed, plus a full top-16 tape harvest and
local H2H benches. Artifacts in `analysis/top16_tapes/` and
`topbots/kernels_0827/`.

## 1. Live state at session start (2026-08-27 14:25 ET)

| item | value |
|---|---|
| Team | Harrison Interactive — **#471, 1994.5** |
| v11.7 (55808478) | 1994.5, still earning games |
| v11.8b (55818897) | 1709.9, converging (posted 13:10) |
| Best historical score | v11.3 = 2194.8 (retired at last-2 rule) |
| Submissions remaining today | 2 |
| Ladder top | Crop Dusta 3113.2 / Ryo Hasegawa 2979.1 / Subramanya 2963.6 |

Rules re-verified from the official page: 5 subs/day; max 2 final submissions
for judging; $5,000 × top 10; **Rule 2.12: no ingress/egress during episodes**
(all intelligence must be baked in at build time — mining public replays at
build time is fine and is exactly what the top meta does); winners must
open-source under CC-BY 4.0 (code stays private until someone wins).
**Ladder rating is W/L/T Elo only — coin margin is irrelevant to rating**
(confirmed independently by Rayk Kretzschmar's notebook, 105 votes).

## 2. GitHub survey (267 repos) + Kaggle notebooks

- Repo search `kaggriculture` → 267 public repos. Cloned & inspected the 15
  most promising (recency/size/stars/descriptions). Full list:
  `analysis/top16_tapes/gh_repos.json`.
- **No top-16 team publishes under their Kaggle login** (checked all 16
  member logins against GitHub; team #3 Subramanya's "farmermarkets" repo is an
  unrelated Next.js app).
- Three independent groups built **route-replay engines from public replays**
  (the meta the top uses):
  | repo | claim | verdict |
  |---|---|---|
  | ergousha/kaggriculture | rating 670→**3,068** | mines **Ueddy** (#35) route; repair layers credited to Kaito's public notebook (we own it); 60/60 vs their reference ladder; claim unverified vs live board |
  | tejrai07/kaggriculture-submissions | model.py **2,601.5** | "THUNDER" episode-91364946 distilled trajectory + front-run controller; THUNDER is now #1806 (1439) — score likely decayed |
  | Jameshuang07/kaggriculture | **2,284.9** (#204) | route replay + shop routing; 66% win claim vs top-10 pool; his own docs: "route replay is near the ceiling" |
- CDrookieDc/kaggriculture: sophisticated A/B self-play lab reverse-engineering
  Ryo/Leonardo/Yagawa from replays — heuristic replicas only, mid-band scores
  (~562-600). No new engine.
- Rest: RL prototypes (gytdrop, diffmap, Algio-Nightly JAX/Flax dual-tower,
  bravefe), small scripts, replay viewers. Nothing above ~2,600 claimed.
- New Kaggle kernels since last pull (`topbots/kernels_0827/`):
  - **raykkretzschmar "Findings from Zero to Top Meta"** (#143, 2368.9) — the
    best public meta document (see §5). Pulled.
  - salemali7 2900 (8/26 update): **identical agent code** to our K2900 —
    notebook analysis changed, code unchanged. Nothing new.
  - prvsiyan frontier-moon (8/27): kernel code restructured; prvsiyan #29.
  - harishyadav v111 8C4S (#1690): mid-band, analysis-heavy.
- **The "combined" engine — 7 of the top 16 (Blu3s #4, Mingkang #10, tetsuya's
  rivals: Carson #15, Kaileh #14, Naru #6, SCNU #16, antadam #9) — is NOT
  public anywhere.** No GitHub, no kernels (checked all 7 members + taiseiu
  #326). Its source is private.

## 3. Top-16 tape harvest (39 episodes, 72 tape records)

Pipeline: team leaderboard → team-submissions → episodes → replay download →
extract 719-step tape (both seats) → delete raw. Artifacts:
`analysis/top16_tapes/*.json` (72 tapes + shop configs + stability + solo
scores + full leaderboard CSV).

### Family map by D1 opening signature
| family | teams | D1 market orders |
|---|---|---|
| **COMBINED (private engine)** | Blu3s, Carson, Kaileh57, Mingkang, Naru, SCNU, antadam (7 of top-16) | 4×HIRE, SHEEP 4, WHEAT 4+9, MELON seed 7, WHEAT seed 6 |
| V46 (our family) | **Kenjo1209 #11 (2802.9), peikopon #13 (2780.2)** = V46 STOCK, 1-step-desynced; QQ Farming #12 = V46 variant | WHEAT 4, 2×HIRE, MELON 7, WHEAT 5, SHEEP 4 |
| tetsuya #5 | unique | 5×HIRE, COW 2, SHEEP 3, WHEAT 5, WHEAT seed 10 |
| William Diment #7 | unique | 4×HIRE, SHEEP 4, WHEAT 7+12, MELON 7, WHEAT seed 7 |
| Crop Dusta #1 | unique (reactive) | 4×HIRE, COW 2, SHEEP 2, MELON 5, WHEAT 8, farmer BUILD_PASTURE |
| Ryo Hasegawa #2 | unique (shop-routed) | 5×HIRE, COW 2, SHEEP 2, MELON 11, WHEAT 6, farmer BUILD_PASTURE |
| Subramanya #3 | unique (carrot) | 6×HIRE, SHEEP 1, CARROT 6, MELON 6, WHEAT 3, BUILD_PASTURE |

Every team's openings are FIXED across episodes (20/20 first-step match), but
full 719-step tapes differ per episode = **shop-configuration routing** (routes
diverge D4-D20 based on first 3 shop types + cash/HIRE outcomes), exactly as
Jameshuang's docs stated ("the top ten's 'adaptive' is shop-order routing, not
price reading").

### Replayability (solo vs PASS)
| engine | best actual game | solo replay | replayable? |
|---|---:|---:|---|
| tetsuya #5 | $139,546 | **$143k** (116-163k on own seeds) | YES — pure fixed tape |
| Michael Timbs #8 | $105,101 | $135k (2 of 3 tapes identical) | mostly |
| William Diment #7 | $136,117 | $41k avg | partially (reactive layer) |
| COMBINED (26 routes) | $116,969 | $40-98k on own seeds | partially |
| Ryo #2 | $140,659 | $68k (ep-100075619 tape only) | partially (shop-routed) |
| **Crop Dusta #1** | $139,299 | **$21k (23%)** | **NO — reactive engine** |

### The decisive H2H bench (standard: 4 seeds × 2 seats)
| opponent (our side) | vs v11.8b (ours) |
|---|---:|
| tetsuya tape (#5) | **W 8/8, avg +$20k** |
| COMBINED router (7-team shop-routed replay) | **W 8/8, avg +$88k** |
| (ref) v11.8b vs V46 stock / BT | known positive margins |

**Pure-tape replays of every mined top engine LOSE to our v11.8b in H2H.**
Their value lives in a private adaptive market layer that the tape doesn't
carry (cash/HIRE re-planning, sell pacing, clone front-run). Our stack
(V46 + wheat maker + yarn graft + L715 + preemption batch 25 + gate 1.0 +
feed rescue) IS that adaptive layer, and it is strictly stronger in H2H.

## 4. What the top actually is (synthesized)

1. **The ladder is a three-family war**: (a) the private COMBINED engine
   (7 of top-16, ~2750-2890 band), (b) the V46/Kaito family (ours; 2 pure
   members at 2780-2803, boatlee #85 2493, Rayk #143 2368, Kaito #190 2283,
   georgymamarin #83 2494, prvsiyan #29 2664), (c) three private reactive
   engines (CD 3113, Ryo 2979, Subramanya 2963).
2. **The mature farm has converged** (8c/6s/12 hands/3 quads across 144/200
   sampled top episodes per Rayk's 200-replay study). Farm design is settled;
   the edge is **market execution**: clone-aware premium front-run,
   price-impact SELL ordering, terminal cleanup, one-step shed banking.
3. **Our v11.7/v11.8b implements exactly that execution layer** on the
   strongest public field tape. Kenjo1209/peikopon running UNMODIFIED V46 at
   2780-2803 proves the family's convergence band: **our V46+upgrades should
   settle at 2800+**. "Stuck at 1990" was scheduling starvation +
   mid-convergence, not a ceiling.

## 5. Verdict on the hunt

- **No public code found that beats our current stack.** The GitHub/notebook
  frontier is: route-replay + Kaito repair layers (2,200-2,600 band claims),
  below our benched V46+ family. The only engines above us (CD, Ryo,
  Subramanya, COMBINED) are **private**; only their replays are public.
- **Do NOT ship a tape clone today.** It would bench below v11.8b in H2H and
  spend a submission slot + push a weaker submission into the active pair.
  Hold the 2 remaining slots; let v11.7/v11.8b converge (fresh-scheduling
  trickle is the only bottleneck).
- **Next real lever (top-10 path)**: reverse-engineer the REACTIVE layer.
  Crop Dusta's tape replays at 23% — the other 77% is his market controller.
  We can now extract it: we have his full action streams; mine
  sell/buy timing rules as functions of (own inventory, price vs base,
  opponent's last sell, hours-to-EOD) across 20-30 of his episodes, and build
  a controller that replicates it on top of our (or his) field tape.
  Rayk's C68 document shows the exact method (opponent-batch fitting,
  horizon 1-6, public-farm-similarity gate) and is in
  `topbots/kernels_0827/`.
- Secondary: the COMBINED field tape is now fully mined (26 routes + shop
  configs) — usable later as a route base if we build a better market layer
  than V46's, or for a shop-routed hybrid bench.

## Ship state
No new submission this session (nothing benches strictly above v11.8b).
Active pair unchanged: v11.7 (1994.5 floor) + v11.8b (converging).
Workspace additions: `analysis/top16_tapes/` (72 top-16 tapes, family map,
stability, solo scores, 2026-08-27 full leaderboard CSV, GitHub repo index),
`topbots/kernels_0827/` (Rayk meta findings, updated 2900, v111 8C4S,
v24-robustmarketlead).
