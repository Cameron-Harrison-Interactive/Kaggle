# Clone continuation — 2026-09-20 session

## Current file / limits
- `war/meta_v1.py` **9c969268** (full md5 9c969268d2f8907db2282878c11bb369), compiled, exactly one maybe_drop.
- `war/horizon_line_v1.py` still **61d6e9cc** untouched. No edits to 41/51, no submissions, vs-pass only.
- Last submission state remains v46=600, v45=711.7; not re-queried this turn.
- Backups live HERE (persisted), including meta_f645882e.py (turn-entry), meta_helpers_near.py, meta_orphan_sites.py, meta_orphan_actionable.py, meta_afternoon_safe.py (=bf37b19c), meta_8ebc3fd0.py, meta_9c969268.py (current).

## Verified replay, not inferred source
Downloaded Majkel episode **109798422**, stored `intel/majkel_replays/109798422.json.gz`. Majkel seat 1; reward161591, opponent163274. Seed787258433. This is a loss, not proof of winner.
- d10 harvest/drop: water before harvest yields6, not5. Two auxiliary hands harvest shed-side NW melon (1,4), (3,2), deliver by h9/h10; NW crop hands do others. Six melons harvested,36 sold d10. One worker batches2 melon then drops12.
- Fertilizer is NOT strictly odd age>=9. Replayed strawberries fertilized ages7,8,9,12,etc. Collectors carry fertilizer from animals into afternoon field work. Some actual duplicate actions occur too; do not call replay literally perfect W0 through20: this episode W1 d17 W2 d18/d19 W0d20.
- Replay d9 wheat16, WATER46. d10 WATER42, W0, E4. d12 E1/W0. d16 E2/W0, wheat21/strawberry32. Fert d11..16=2,5,4,7,13,11.

## Index correction
`env.steps[j][seat].action` is the action producing that observation, NOT action chosen from it. New `probe.py` groups by observation day/hour at j and reads action at j+1. Old memory tables grouped raw step indices and are off one action hour. Do not blindly mix action-count tables. New d9 seed42 wheat actions=23 vs old21; d10 WATER48 vs old-count variant. End-of-day crops/score and melon same-day sales unaffected in these runs.

## Changes retained from f645882e
1. Restore water BEFORE cutting melon, both NE and NW crop paths. Skip fallback water after finite crop is cut. Fix missing return travel cost and position update when replanting after a melon DROP.
2. d10<=h3: FIRST TWO SW crop workers take one ripe NW melon each: WATER, HARVEST, DROP, then their normal SW band. Reserve assigned melons from NW route without changing band slicing. Do NOT use last2 SW hands: that delayed weed removal; do NOT remove positions before band slicing (changes ownership). NW ripe melon priority -1 ONLY d10, normal dying/tick/melon priority0 afterward. No wheat-hoist.
3. Actual root of repeated empty DROPs: **unplaced sheep with no eligible site** triggered `_orphan_animals` EVERY HOUR; full replan reset workers repeatedly. Now from **day10** validate legal north sites, compatible structure, NW6 cap and whitelist, NE10 cap, and deduplicate retries by `(day,held animals,eligible sites)`. Preserve opening d<=9. All-days version bf37b19c changed seed101 land timing and cut d10 hires to6; NOT current. day>=11 variant8ebc3fd0 sold0 d10 on101; current day>=10 sells26 while hire11 holds.
4. No-PLANT wheat rebuild now also requires an idle worker with time to reach empty SW and plant+water. On its own nearly no change; retain as actual actionability check. Not the main empty-DROP root.
5. Afternoon **collected** fertilizer routing d11..22 h>=10: only workers at DROP/exhausted plans and NO pending dry WATER/FEED/CARE/PLANT/INSTALL. Spray unclaimed northern strawberry age7..15, prioritize current production tick; use carried fertilizer, no shed theft. At shed PLACE sale goods individually to retain fertilizer. Add WATER only if dry AND no WATER already booked anywhere. Protect booked water, and never change d6. First ungated version stole row work; reverted for the safe guard.

## Diagnostics (cash vs pass only; NOT ladder W/L)
| seed | entry f645882e | current9c969268 | d10 melon sold | d10 hands | W through d12 |
|42|106973|123604|30|11|0 at each EOD|
|5|52268|98825|6|11|W6 d12|
|101|95136|124857|26|11|W3 d12|
|202|87867|138037|23|11|W3 d12|
Use saved named text/json.gz files, not tool output ordering: parallel tool responses appeared in completion order, easy to misattribute seeds101 and202. The filenames are definitive.
Current tag **orphan_d10** on all four seeds. `probe.py` accepts seed tag [botpath], writes gzipped steps and summary. `orphan_d10_42.txt` etc exist.

Seed42 current: d9 $695, E6,W0,wheat22,ST26,MEL12. d10 $10438,E10,W0,wheat24,ST26,MEL6; WTR48,DIG2,SELL30. d12 E10,W0,wheat25,ST29,MEL1. d13 E10,W1,WH23,ST31,MEL0. d16 E5,W1,WH26,ST33,MEL0. d20 E5,W9,WH21,ST30. Fert every day d11..20 =2,2,1,2,16,3,4,3,15,2. No new melons afterd9.
Still fails exact clone: empty ground excessive, late weeds, d9 overplant; seeds5/101/202 open SW d10/d11 rather than d9. More cash != winner. DO NOT SUBMIT.

## Experiments rejected / new dead ends
- Water-before-cut alone108764; helpers last2 SW108435 W2d10 (natural weeds at0,9/1,9 unremoved); stable slicing110728 still W2d10. FIRST2 fixed W0d12, score106266 (closer tape).
- Fresh morning rows (stop retaining old WATER plan at h<=3)105397 W1d10; reverted. Trace showed old hand8/newhand9 duplicate SW bands, but blanket preservation removal is not solution.
- Broaden ALL scheduled berry fert windows to ages7..15:110595 vs122707, worsened weeds, d12 fert STILL0; REVERTED. Do not replace morning routing with broad fert priority.
- Afternoon spray without guarding pending row WATER:118099, worse weeds; SAFE guard retained123604.
- Active no-PLANT guard alone106266 unchanged; orphan retry was cause.
- All-days orphan retry bf37b19c s42 123604 s5 82488 s101103805 (d10 hire6) s202138273. Opening gating retained; not score-based revert.
- day>=11 orphan8ebc3fd0 s42 123604 s5 98825 s101132729 (d10 SELL0) s202126215. Current day>=10 improves melon tape on101 to26 despite lower final124857; KEEP closer tape.

## Next work
- Keep current as closer and better but NOT ready. Need match pre-d10 land/crew/planting routes across shop draws, especially yarn/bakery seed5 d10 only6 melon; SW helpers cannot start until SW exists, and it opens too late there.
- Need reduce E10 after dump to E1/E2 via actual replay replacement routes without stealing WATER; maintain W0 beyond12. s42 lone d13 weed (7,2) d8-wheat expiry is known.
- Do not reopen forbidden wheat hoists, leftover wet overrides, d6 leftover water, land-day wheat cap, two-pass SW, or KEEP edits. Existing user constraints in conversation still apply.

## Round2 log (2026-09-21) — current disk 5dfb9936
Base was 9c969268 (s42 123604). All probes vs passbot. KEEP md5 61d6e9cc
verified unchanged throughout. Backups in intel/clone_runs/round2/.

### Kept (on disk)
- grain_walk (neutral, faithful): SW wheat harvest no longer counts cargo or
  forces midday shed trips. s42 122992 (-612, kept as closer to tape).
- melon batch-2 + drop_hold + EOD sweep: one hand cuts TWO melons then drops
  12; the deferred trip cost is RESERVED in busy at defer time (a promised
  delivery the band cannot eat) and refunded at DROP; EOD appends DROP if
  cargo>=4. s42 d10 SELLM 30->36 (his 36). Count-only batching stranded 17
  units overnight on s202 (-23k); the hold fixed it.
- one-for-one NW refill, WHEAT-FIRST: cut NW tiles refill post-DROP, exempt
  from zone_room; berry only while planned_standing<2 (his d10: 6W+2S, d11:
  9W+2S). Berry-heavy refill hurt s42 late; wheat-first balanced it.
- fert _ne_pair 7-25, day>=11: was odd-9+ (synced cohorts into spike/famine;
  d12/d14 found nothing with shed at 6-7). Water runs before spray per stop.
  Day gate: d9 sprays stole fill-day water (s101 W1); his first sprays d11.
- window-wheat tie: window wheat joins the priority-0 tie (strict dying-first
  tried and REVERTED: starved d11 melons, SELLM 0). Neutral, kept.
- north-idle v2: h>=10, day 10-22, idle NW/NE hands plant nearest unclaimed
  NW/NE empty via live plan_crop_choice, animal rows excluded, travel-aware.
  v1 (fixed coords incl. rows) blocked the herd, -2.5k.

### Panel, current disk (r2_nv2) vs round2 base (orphan_d10/9c969268)
| seed | base | current | d10 SELLM | d10 E/W | d12 W | d20 W |
| 42 | 123604 | 116260 | 30->36 | E10/W0->E7/W0 | W0->W0 | W9->W10 |
| 5 | 98825 | 96470 | 6->6 | E18->E17 | W6->W5 | W9->W11 |
| 101 | 124857 | 120531 | 26->27 | E1/W0->E1/W0 | W3->W2 | (W12) |
| 除外 202 | 138037 | 137703 | 23->27 | E2->E2 | W3->W1 | W11->W12 |
s42 -7.3k is d21+ (-5.9k past d20 with BETTER d12-19 tape: fewer E every day,
fewer total weeds d12-19). Judged tape-first per standing orders; kept.

### Rejected this round (do not retry as-is)
- wheat-at-2 any-day: 107651 (-16k), E13, broke opening economy.
- wheat-at-2 day>=10: wave came d12 not d11 (d10 young-wheat water missed).
- wheat-at-2 day>=10 + d11 seed caps: s42 +426 only; s202 -9.7k. Seeds were
  not binding (d13 left 3 unspent); scheduling is.
- one-for-one berry-heavy (pre-drop plant): d10 SELLM 24, -6.7k (stole a melon
  stop's budget); post-drop berry version -5.9k s42.
- count-only batch without hold: s202 -23k (stranded pockets).
- age-3/y>=3 wheat rule: VACUOUS (engine yield=1+window waters; age-3 morning
  holds 2, never 3). Identical score proved it.
- age-3/y>=2 wheat rule: d12 HV18 but E10, +weeds, s42 -5k. Immature cuts +
  seed-capped replants = dirt. REVERTED (no wheat rule on disk now).
- strict dying-first tuples: d11 SELLM 0. REVERTED to ties.
- north-idle v1 (fixed coords + row wheat): -2.5k, blocked herd installs.

### Engine truths nailed down
- Finite crops gain yield ONLY from WATER in window (no overnight growth);
  planted at y1; wheat window ages 2-4. needs_water formula matches engine.
- Wheat expiry (planted+5) uncut = ~80% of our d13-20 weeds (autopsy). Rest =
  thirst ((8,2),(9,2),(0,4) d17-18 misses). Weeds sit 8 days: WEED stops are
  priority 1 (last) so DIG never fits.
- Berry final tick sets max_lifespan_step (rotation signal, unused so far).

### His d21-30 (replay 109798422; cross-seed cash NOT comparable)
d21 +7.8k W0, d22 +13.4k W0, d23 +6.8k W2, d24 +7.7k W3, d25-26 +5-6k W2,
d27 +8.9k (E17, liquidation starts), d28 +9.1k E32, d29 +15.5k E41.
Late ROTATION d22-24: ST 24->10, WH 25->36, plants 11-14 wheat/day, W0-3.
Liquidates d27-29 (no replant, harvest all). We never rotate (ST stays ~30,
old berries drink, weeds explode). NEXT: DIG spent (final-tick, y0) berries
d21-26 -> wheat; then liquidation check.
