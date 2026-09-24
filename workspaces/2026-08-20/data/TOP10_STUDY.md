# Top-10 Winners Study — 2026-08-14

Live leaderboard (API pull via KGAT, evening 2026-08-14):

| # | Team | Score | Last submit |
|---|---|---|---|
| 1 | カワシギ (kawashigi) | 3259.8 | 2d |
| 2 | researchstudio.site (fistyee) | 3149.2 | 3d |
| 3 | Thomas Tschinkel | 3139.9 | 4h |
| 4 | somewhere after (amaterasuuuuu) | 3094.5 | 14h |
| 5 | Aaweg | 3090.2 | 8h |
| 6 | Mohamed abdelrazik | 3086.1 | 13m |
| 7 | Utkarsh #2 | 3075.2 | 8h |
| 8 | Ueddy | 3072.1 | 4h |
| 9 | Ignat | 3066.1 | 6h |
| 10 | One-For-All (indarkarhana) | 3061.0 | 20h |

(ours: v24 = 2070.9 and climbing; v20 = 1719.6. The top ~40 are 2900-3260 —
that is the target band.)

---

## 1. What the top teams actually do (public artifacts)

### カワシギ (#1, 3259.8) — the wheat-arbitrage super-economy
Route extracted from public episode 92521336 (seat 0) via One-For-All's
notebook (decoded: `top10/kawashigi_route_92521336_s0.json`, 719 steps).
Profile:
- **BUY_PRODUCT WHEAT 522 total** over the game — buys cheap wheat all
  season, floods it back at the d19-29 peaks (112-141/day on d19-23,
  ~1,100+ units sold in the endgame).
- **10 COW** + 4 sheep; milk sells from d8 (12) growing to 24-30 late.
- **Continuous wheat seeding** (d0:7, d4:7, d7:4, d8:5, d10:4, d11:8 …).
- MELON 12 seeds at d0; STRAWBERRY 23 seeds on d11; CARROT filler d21-25.
- 277 hires.
- Wool sells from d6. Melon sells d10-18 (60 on d10).
Takeaway: the #1 economy is a **wheat-price trader** with a huge cow herd;
the consensus (our) route is the meta's floor, Kawashigi's is the ceiling.

### One-For-All (#10, 3061.0) — demand-dominance MoE selector
Notebook "Read the Market, Choose the Farm". The submitted agent
("E279-V17-demand-dominance-MoE") is:
- **LOW expert**: "Boatlee BL-V17" = the consensus route (OUR family!)
  reconstructed from 12 public traces, wrapped in generic execution guards.
- **HIGH expert**: Kawashigi's public-episode route (above), same guards.
- **Decision at step 168**, purely from the public shop sequence:
  if YARN_STORE is visible AND the opening is NOT (ICE_CREAM_SHOP → YARN_STORE),
  switch to the HIGH (wool/wheat-heavy) route; else stay LOW.
- Both route streams are identical through step 167 (shared opening).
- **Published validation**: median **+24,862 coins** per eligible demand
  block; 8/8 eligible blocks improved; non-triggered blocks 52/52 zero
  change; open-leader panel 51-2-6; sealed holdout 19-1-1; vs 3 strategy
  controls 26-3-1 / 23-7-0 / 30-0-0.

### somewhere after (#4, 3094.5) — "Shabby Farm" commitment/ledger planner
Full source in `top10/amaterasuuuuu_shabby-farm.py`. A real architect:
plans the whole season as **dated commitments** (each owns its operations,
inputs, outputs, capital, site occupancy, market orders), replays them
through one cash/labour/market **ledger**, keeps the survivors, and
**compiles** the current day into legal turns. Engine laws (crop/animal
params, sqrt/log price curves, shop demand) are baked in. This is a
tape-compiler taken online — the "thinks on its feet" design done right
(and much richer than our fixed tape + guards).

### Everyone else
- researchstudio.site, Aaweg, Utkarsh, Ueddy, etc.: no public artifacts.
- Thomas Tschinkel / Ignat / Mohamed abdelrazik / Indar's other notebooks:
  other competitions (irrelevant).

### The guards catalog (Indar's execution layer — all public-state only)
weed repair · feed guard · room evac (shed-cap) · repay shift ·
sell-slot ranking (impact × demand urgency) · preempt shift ·
r5/md counters · room guard · terminal liquidation.
These are exactly the "holes" fixes the live-loss study calls for —
the top-10 all carry a runtime guard layer over their tape/route.

---

## 2. Meta read

- The **consensus route (our family) is public property now** — teams
  reconstruct it from public episodes and resell it with guards
  (One-For-All's LOW expert is literally our lineage).
- The ladder is sorting by: (a) a better base economy (Kawashigi's
  wheat/cow arbitrage), (b) **public-state route selection**
  (One-For-All's shop-keyed MoE, +24.9k median per eligible block —
  the single best-published per-game edge), (c) robustness guards
  (weeds/feed/shed/terminal).
- First-mover wheat openings (our v23-v25 trick) are now meta-wide:
  22 of the 41 v24 losses came from opponents buying wheat at d0h0.
  The arms race continues (we hold qty-16; the beaters buy 11-14).

## 3. Our win to winning — recommended v27 direction

1. **Ship v26** (W6 + FeedReserve) — closes the two live holes, keeps the
   qty-16 arms-race edge.
2. **Build the shop-keyed selector as OUR differentiator** (not a clone):
   - Reuse the two routes we already own: the current tape (LOW/balanced)
     and a **new compiled HIGH route** = wool/heavy-wheat economy, compiled
     by our route compiler against the YARN-heavy shop sequences
     (the compiler already supports multi-seed search; melon4 machinery
     shows how to re-roll a route).
   - Selector at step 168 on `town.unlocked_shops` (public state — matches
     the user's "adapt to the opponent's observable play, never the seed"
     rule: the shop sequence is shared public state, and the opponent's
     opening also reveals their route family).
   - Validate exactly like One-For-All: paired blocks on shop sequences,
     8/8-style improvement bars, plus our 81-episode replay regression
     suite as the honesty check.
3. **Steal the good ideas without the tape**: sell-slot ranking already in
   (v23+); consider Kawashigi-style **wheat dip-buys** (we already
   BUY_PRODUCT WHEAT 1 on d2-9 — scale it to the d5-d9 dips) and
   d10 melon-60 style melon cadence as compiler variants, not runtime
   behavior.
4. The 65MB/1s budget: everything above is tiny (KBs, microseconds);
   the tape+guards design stays well inside limits.

Artifacts: `top10/kawashigi_route_92521336_s0.json`,
`top10/indarkarhana_selector_agent.py`, `top10/amaterasuuuuu_shabby-farm.py`,
the notebook JSONs in `top10/`.
