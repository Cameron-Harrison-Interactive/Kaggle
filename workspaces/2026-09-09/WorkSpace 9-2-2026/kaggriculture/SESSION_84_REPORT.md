# SESSION 84 — The Shinichiro Loss (101033101): 3 escapes forensically explained, feed rescue v2 built

User report: "this loss is bad … We lost animals again and they won with eggs."

## 1. The loss: ep 101033101, v11.9 vs Shinichiro Yoshida (−$21,421)

Opponent = melon-first custom engine (D1: 12 MELON + 1 STRAW + 2 WHEAT + 1 CARROT
seeds, 3 SHEEP, 5 HIRE, farmer BUILD_PASTURE — not any known family). Final:
his 15 animals (5 cows, 8 sheep, 2 geese) vs our 11 (+1 cow stranded in shed).

### Loss decomposition (measured)
| component | value |
|---|---:|
| **Melon wave**: he sold 118 melons (~$20.9k, 12 seeds D1 + late top-up) vs our 66 (~$10k) | **−$10.9k** |
| **Animal losses: 3 COW escapes + 1 cow stranded in shed 18.5 days** | **≈ −$6-9k** |
| Herd/fert edge (15 vs 11 animals; $12.3k fert sold vs our ~$9k) | ≈ −$2-4k |
| Eggs themselves | only ~$1.5k (the "won with eggs" is really herd+fert+melons) |

The D11 swing (−$10,674 in one day) = his melon wave + fert, not the eggs.

### The escapes (forensics)
1. **COW@(2,1) placed D4 → escaped D11** — the classic (2,1) class again, but a
   *new failure mode*: fed fine D4-D8, **unfed ALL of D9** (rescue v1 never
   fired — it requires streak ≥ 1, and D9 is the *first* missed day), then
   unfed D10. On D10 the rescue DID fire (streak 1, H22-H23) and dispatched
   u11/u3 to (2,1) — **both with 0 wheat in hand** (shed had 8-63; wheat
   carriers u0/u4 were 3 tiles away) → FEED no-op → escape at D11H00.
2. COW@(6,1) placed D7 → escaped D10 (same class).
3. COW@(6,3) placed D7 → escaped D14 (same class).

**Rescue v1's four defects (all proven by this episode):**
(a) issues FEED without wheat in hand (guaranteed no-op) — line: `units[idx] = ["FEED"]`
(b) dispatch = nearest unit, wheat-blind
(c) window hour ≥ 20 — no time left to fetch wheat from the shed
(d) streak ≥ 1 gate — the first missed day is never rescued, so one failed
    evening = escape

## 2. Fix: feed rescue v2 → v11.10 (v11.9 + rescue v2)

Design (topbots/v1110_feedrescue.py; build: /_ref/build_v1110_clean.py, kept in
workspace at kaggriculture/scripts/build_v1110_clean.py):
- eligible: unfed today AND (streak ≥ 1 from H18, streak == 0 from H22)
- **stand-down**: if the executing tape schedules ANY FEED within the next few
  steps, the wave is working → no new dispatch — EXCEPT when any starving
  animal is already streaked (it has one miss left; always dispatch)
- wheat-aware dispatch tiers (max 2/step):
  T0 carries wheat (d ≤ 5, can arrive+feed by EOD)
  T1 on a shed tile and shed has wheat (PICKUP then walk)
  T2 fetch-capable (d(unit→shed) + d(shed→animal) + 2 ≤ hours left)
  (no last-resort no-wheat tier)
- transaction phases: fetch (walk to shed, PICKUP WHEAT min(shed,4)) → walk →
  FEED only when carrying wheat (on-shed pickup retry; one last-resort attempt
  if dry); 12-step expiry
- never hijacks FEED/CARE/COLLECT_FERTILIZER/HARVEST/WATER/PLANT/BUILD_*/
  animal PICKUP/PLACE/DROP (wave-critical and other starving animals' feeders)

### Ghost replay of ep 101033101 (process-isolated)
| | cash | herd | escapes |
|---|---:|---|---|
| v11.9 | $89,417 | 11 | 3: (2,1) D10, (6,1) D10, (6,3) D14 |
| **v11.10** | **$95,175** | **13** | **1: (6,1) D10** |

(2,1) and (6,3) rescued; +$5,758. In live terms the rescue is worth the
~$6-9k animal-loss component.

## 3. METHODOLOGY INCIDENT (important for all future benches)

The V44-family engine files register their bundled modules in `sys.modules`
(`_v44_load` **reuses** an existing `v44.gold_floor` entry). Loading two of
them in one python process silently cross-contaminates: the second engine
runs the first one's market/rescue/EPF code. **All in-process
multi-version benches from earlier today are invalid** (the SAR −$1.8k/game
number, the v11.10b −$250 number, etc.). All results in this report use the
**process-isolated harness** (`/_ref/run_isolated.py` + `bench_matrix.py`:
one subprocess per game; the loader purges newly-registered modules). Keep it
that way for every future comparison.

## 4. Field regression bench (final, all isolated)

8 seeds (1,3,5,7,9,11,13,19) × 2 seats × 5 field opponents (BT, V46, K2900,
moon, soil) + 8 solo vs pass, all process-isolated:

| opponent | avg (v11.10 − v11.9) | notes |
|---|---:|---|
| BT | −$275 | nonzero only s3 (±$3.7/−7.7k), s9 (−0.2k) |
| V46 | −$94 | s3 only |
| K2900 | −$216 | s3 only |
| moon | −$445 | s3/s7 |
| soil | −$217 | s3 only |
| solo | +$68 | s5 −16.5k / s7 +16.2k swings (rescue fired) |
| **H2H total** | **−$250/game** | **only 15/80 games nonzero** |

The rescue fires only when a feed wave is genuinely broken (≈15-20% of games).
Ladder EV: escape class ≈ 8% of games × ~$7k ≈ +$560/game value vs −$250 cost
→ **net ~+$300/game**. Shipped.

### The tried-cap incident (do not retry)
Attempted to cut the −$7.7k tail with a per-target dispatch cap (max 2,
reset nightly). It made the ghost case dramatically worse ($95,175→$72,813,
1→4 escapes, reproducible): in this geometry (shed is 5 tiles from the cow
cluster) wheat delivery needs multiple same-evening attempts — early
attempts arrive dry, and only the 3rd+ dispatch finds a carrier in position.
The cap blocked exactly the successful attempt. **Shipped build = no cap.**

## 5. Smoke (real engine 1.32.7)
seed1/7/19 = $179,283 / $156,636 / $169,903 (seed7 = rescue firing,
+$16k vs v11.9's $140,477), state resets clean across episodes, no ERROR
statuses. **Submitted 19:4x ET as sub 5582xxxx — final slot of the day.**
Active pair now: v11.9 + v11.10.

## 5. Next-session queue (updated)
1. **Melon-wave route variant** (the −$10.9k component): build a melon-first
   route (12 melon + 3 sheep opening + late melon top-up, per the Shinichiro
   and CD profiles) as an additional shop-routed option; bench vs v11.x.
2. (6,1)-class escapes still possible when no wheat-carrying unit is
   reachable (the ghost's remaining escape) — extend T2 reach or add an
   early-morning (H0-H6) rescue pass for streaked animals (cheapest window:
   all units at the shed after EOD).
3. Goose-economy candidate (CD's current meta: 7g/3c/1s, log-curve eggs +
   fert volume) — larger route surgery, after #1.
4. Let v11.8b/v11.9/v11.10 converge; watch escape frequency on the ladder.

## Ship state
- main.py = **v11.10** (topbots/v1110_feedrescue.py, 96,122 bytes, md5
  bb3852736abdc3d23ccb065b84f59dad) — SUBMITTED (final slot today).
- v11.9 = topbots/v119_FINAL.py (sub 55822648, 16:35 ET) — still active.
- Active pair: v11.9 + v11.10 (last-2 rule).
- Isolated bench harness saved: scripts/run_isolated.py + scripts/bench_matrix.py
  (use ONLY this harness for version comparisons — see §3 incident).
