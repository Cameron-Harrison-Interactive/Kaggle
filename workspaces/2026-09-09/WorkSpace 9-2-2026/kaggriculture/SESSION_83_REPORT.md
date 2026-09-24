# SESSION 83 — The Winner Hunt (completed) + The Two Losses (diagnosed, one fixed, one shipped)

Continuation after the Chat-Log-12 context cutoff. Two tasks this session:
(1) the pending "search GitHub / notebook locations for the winners" task —
**completed, nothing above our stack found**; (2) the two user-reported v11.8b
losses (ep 100939583 vs Kenjo1209, ep 100921202 vs Bill Fan) — **diagnosed
to the step, one fixed and shipped (v11.9), one proven-fixable-only-with-a-bigger
job (documented below)**.

## Part 1 — The winner hunt (GitHub + Kaggle notebooks)

- Surveyed all 267 public GitHub repos mentioning kaggriculture
  (`analysis/top16_tapes/gh_repos.json`); cloned/benched the credible ones.
- **No top-16 team publishes code** (checked all member logins: GitHub
  accounts, Kaggle kernels). The "combined" engine (7 of top-16: Blu3s,
  Mingkang, Carson, Kaileh, Naru, SCNU, antadam) is private.
- Best public claims: ergousha (route-replay of Ueddy, claims 3,068 — unverified;
  repair design credited to Kaito's public notebook, which we already own),
  tejrai07 (2,601.5 on a THUNDER distillation — THUNDER is now #1806),
  Jameshuang07 (2,284.9, admits "route replay is near the ceiling").
- **Top-16 tape harvest**: 39 episodes, 72 tape records
  (`analysis/top16_tapes/*.json` + family map). Every top engine = fixed route
  + shop routing + a private market layer. Kenjo1209/peikopon (#11/#13,
  2803/2780) = **V46 stock** (1-step-desynced) — proof our family converges to
  ~2800; our v11.7/v11.8b/v11.9 (V46 + strictly-better upgrades) should settle
  above that band.
- **Verdict: no public code beats our current stack.** The only engines above
  us (CD 3113, Ryo 2979, Subramanya 2963, combined ~2800-2890) are private;
  their replays are the harvestable asset (and now are: 72 tapes + 1 CD profile).

## Part 2 — Loss 1: ep 100939583 vs Kenjo1209 (−$10.5k) — "losing animals"

**Root cause (step-level proof):** the 2 "lost" animals never escaped — **2 cows
sat in the shed from D8H00 to game end (21h)**. Chain:
1. Engine 1.32.7 executes the route **1 step late** (route[step-1]) — universal
   (Kenjo's stock V46 desyncs identically).
2. A weed spawned on the BUILD target (6,1) at D7H00. The weed-repair layer
   (v22) spent an hour DIGging and replayed the wave shifted, so the cow
   pickup→place pairing de-synchronized from the shed supply.
3. The (6,3) placement crossed the **EOD teleport boundary** (units reset to
   the shed at hour 0); the carried cow auto-dropped back into the shed
   ("re-stranding"). The wave's later pickups kept picking cows up, but the
   place slots were consumed → EOD auto-drop loop → 2 cows stranded 21h
   (≈$2k/day production gap × 11 days, plus the cascade).

**The attempted fix (SAR, 4 iterations) — REJECTED, negative EV.** Runtime
rescue (hijack a PASS/MOVE unit to PICKUP/PLACE the stranded animal) recovered
the cows in ghost replays, but on the real field bench (8 seeds × 2 seats × 5
opponents) every rescue is a 1-hour perturbation that cascades through market
timing: seeds 5/7/9 went **−$10k…−$32k per game** when the rescue fired.
Recovered-animal value (≈$30-500/day × 21h) ≪ cascade cost. Full data in the
session bench log. **Lesson: this game's choreography is chaos-sensitive;
any hand-hour hijack is a market event. Wave fixes must be tape-level, not
unit-hijack-level.**

**Real fix (next-session engineering target):** harden the placement wave at
tape level — add a redundant pickup+place slot after every EOD boundary for
each animal type (the re-stranding loop is the killer), and/or make the v22
weed repair schedule-compressing (drop the next deferrable FEED/CARE instead
of shifting the whole wave). Must be benched per-game on the full field, not
just ghosts.

## Part 3 — Loss 2: ep 100921202 vs Bill Fan (K2900 engine, −$2,049) — FIXED

**Root cause:** we led every checkpoint; he flipped us in the final 48h by
**batching WOOL at $245** (10/17/8 units per day, D27-H28) while our
town-drain pacing trickled 1-3 units/h. Wool at $245 = 122% of base = far
above the 58-unit saturation floor → the price had headroom; our pacing was
leaving $2-8k on the table in exactly this endgame.

**Fix shipped — v11.9 = v11.8b + EPF (endgame premium flush):**
- D26-D29 (step 624-717): if WOOL price ≥ base ($200) and the shed holds
  wool, top up SELL WOOL by up to 10/h (sells into an existing SELL slot or
  adds one; respects the 10-order cap; self-limiting — stops if price drops
  below base).
- Unit-tested on the live Bill Fan obs (D28H10: price $245, shed 5 → adds
  SELL WOOL 5 ✓).
- **88-game regression bench (8 seeds × 2 seats × 5 field opponents + 8 solo):
  zero regression, max delta $13.** EPF only fires in the exact endgame
  condition, so it can't disturb choreography.
- Smoke (real engine 1.32.7): seed1/7/19 = $179,283 / $140,477 / $169,034
  (seed1 = v11.8b to the dollar), state resets clean, no ERROR statuses.
- **Submitted 16:35 ET (1 of 2 remaining slots used today).** Build script:
  `scripts/build_v119_epf.py`; file `topbots/v119_FINAL.py`; main.py md5
  b52d13a4.

## Part 4 — Crop Dusta check (user-requested)

Pulled his latest episode (100939868, vs Subramanya, W +$8k). **His engine has
evolved past his old fixed tape** (old profile 6s/9c is stale):
- Final herd: **7 GOOSE / 3 COW / 1 SHEEP** — goose economy (eggs = log curve,
  never floors: 14 eggs/day + 7 fert/day of safe volume product).
- **Wheat trader: 2,028 bought / 2,382 sold** (net producer + maker; wheat log
  curve = safe to trade in volume).
- **Morning batch sells: H02 = 637 wheat + 121 fert + 81 straw + 22 milk;
  H06/H09 next.** He sells into the early morning before the field's evening
  dumps — the pre-dump timing edge, applied to everyone (not just clones).
- Profile saved: `analysis/crop_dusta_profile_100939868.json`.

**Actionable insight for a future tape surgery:** our route sells premiums in
the evening (H17-23); CD's morning batching (H01-H09) front-runs the shared
market's daily dump cycle. Shifting premium SELL slots to morning windows is
the highest-EV tape change identified this session — but it is tape-level
surgery (cascade-sensitive, bench per-game on the full field before shipping).

## Ship state
- **main.py = v11.9** (v11.8b + EPF), md5 b52d13a4478503f5fcf85d9a10d04ae3,
  submitted 2026-08-27 16:35 ET.
- Active pair after post: v11.8b + v11.9 (last-2 rule). v11.7's 1994.5 remains
  our leaderboard floor (scores don't expire).
- 1 submission slot remaining today (held: no strictly-better candidate ready).

## Next-session queue (highest EV first)
1. **Wave hardening (Loss-1 class):** redundant post-EOD pickup+place slots
   per animal type + schedule-compressing weed repair. Bench per-game on the
   full 5-opp × 8-seed field (not ghosts — ghost markets are inflated).
2. **Morning sell-window tape surgery** (CD insight): move premium SELL slots
   H17-23 → H01-H09 on the default route; A/B on the field bench.
3. **Goose-economy candidate:** build a 7g/3c/1s variant route (CD's current
   herd) and bench vs our V46 field — eggs' log curve is the only product
   safe at volume.
4. Let v11.8b/v11.9 converge; watch for the endgame-wool class recurring
   (if a new K2900-family loss shows up without EPF firing, the gate is too
   tight — next knob: 0.85×base in the last 24h).
