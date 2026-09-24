# V6 MAP PLAN — the fully-choreographed quad-by-quad tape (user design)

**Philosophy: the map IS the bot.** Every worker, every step, every day, D0-D29, quad by quad.
Reactive code is NOT part of the design; the only conditional logic is what the user asked for
(price-aware selling / don't sell when the market is down). Each guard below must EARN its place
in a 12-seed A/B or it gets deleted.

---

## 1. What the engine gives the map for free (daily resets, every midnight)

| Resets nightly | Does NOT reset |
|---|---|
| farmer + all hands teleport back to shed spawn | money |
| all inventories auto-drop to shed (cap 100) | tile states (WEED = permanent death) |
| hires_today = 0 (re-hire each morning at fib cost) | animal `consecutive_unfed` counter (2 days = dead) |
| — | market prices (set by BOTH farms' flows) |
| — | unlocked land / shops |

Consequence: the map is a set of 30 self-contained **day-plans**. Each morning starts from a
known layout, known positions, empty hands. Nothing positional can drift overnight.

**Hands are a per-day budget** (fib cost per hire that day): 3=$4, 6=$20, 9=$88, 10=$143, 12=$376, 13=$609.
The map carries a hands-per-day column: ramp 3→9 through D0-D9, hold 9-10, surge late if needed.

## 2. The three things a fixed map cannot know (all measured, this workspace)

1. **Cash at step N.** Prices are set by both farms in the lockstep market — proven by the goose
   run: swapped 1 sheep for 1 goose, same seeds, and milk realized price fell $137→$104 (us) and
   $166→$140 (them) with volume flat; wool rose 25% and their bot adapted by buying a 5th sheep.
   Every buy in the map is cash-gated. Even our champion tape (a *simple* map) misses ~0.8 of 12
   cow buys per game. → **Map discipline: schedule every buy 1-2 days later than
   earliest-possible, against the worst seed's cash curve.**
2. **The 2-day fuse.** `consecutive_unwatered >= 2` → tile is WEED forever; `consecutive_unfed >= 2`
   → animal dies. A replaying map cannot notice one missed water. v5d/e (their-shape static tape):
   1,200-1,600 weed-tile-steps, solo ~79k. → **Map discipline: duty headroom ≥ 2x capacity in every
   window; never schedule a tile's water on the last possible day.**
3. **Today's sell prices.** "Don't sell when the market is down" cannot be pre-mapped because the
   price path is co-written by the opponent. Measured spread on identical volume: milk sold at
   H3 realizes $221/u vs H0 dump $137/u (60%!). Their engine harvests this; that is a big part of
   why their milk line is $42.3k vs our $24.4k. → **This one guard is required (and was the
   user's own ask): read price at sell time, pull the sell if down, re-queue same day.**

## 3. The map — day by day, quad by quad

### Phase 0 — NW opening (D0-D2)
- D0: hire 3 ($4). Buy: sheep x3 ($1,500) [goose optional knob — measured -$6k/game, default OUT],
  wheat seeds (feed starter), melon seeds x6 ($480), strawberry seeds x10 ($1,000), carrot seeds x4.
- D0-D2 duties: BUILD_PASTURE x3 + PLACE sheep; PLANT melon 6 + carrot 4 (kick-start gold);
  PLANT straw wave A (10 tiles, zone nearest shed); plant wheat 6-8 (feed bridge until feed-buying).
- Cash gate: ≥ $400 remaining at D2. (Start $3,000; spend ~$3,500 over D0-2 gated on wool trickle.)

### Phase 1 — first straw wave + NE (D3-D7)
- Straw wave A must be IN THE GROUND by D3 (their engine's 306u line flows from D13 = planted D3;
  our v5a straw landed D27 and did nothing to their line).
- D3-4: straw wave B (8 tiles). D5: cows begin, 1 every ~1.5 days ($400 each) through D20 → 11-13 total.
- D6-7: BUY_LAND NE ($1,000) when cash ≥ $2,400 (buffer rule). NE = PASTURE mirror of NW animal row
  + straw wave C (10 tiles).
- Hands: 4→6. Feed: farmed wheat D1-D10, then switch to bought (A/B in Inc 1: ~16 animals fed
  every-other-day ≈ 8 wheat/day ≈ $200/day at ~$25/u vs farming's ~40 ops/day of labor).

### Phase 2 — milk online + SW (D8-D14)
- Milk first yields D8 (first_yield_day 8, every 2 days, 3u/event with CARE).
- Straw first events D12-13 (p+9): fertilize at p+9 and p+13, water event days (yield 4+4=8u/tile/cycle),
  HARVEST after event 2 and event 4, tile dies → replant $100, 17-day rotation.
- D12-14: BUY_LAND SW ($2,000) **only when NW+NE tiles are all occupied** (user rule) and cash ≥ $3,400.
- Hands: 7→9.

### Phase 3 — full engine (D15-D22)
- Straw steady state ~35-39 tiles rotating; cows 11-13; sheep 3-4; melon second wave; carrots as filler.
- D18-20: BUY_LAND SE ($4,000) ONLY if cash ≥ $6,000 after reserve — SE is a late volume add
  (+8-10 straw tiles = volume share at crashed prices), never the core engine (SE is engine-forced
  last: NW free → NE $1k → SW $2k → SE $4k; straw planted there lands D15+ and measured no-op vs their line).
- Hands: 9-10 ($88-143/day).

### Phase 4 — endgame (D23-D29)
- Last replant no later than D13+17=D30 edge → final replant D12-13 for the last cycle; after D22
  replant only fast crops. Terminal flush: sell everything, last-day dump at best hours.

### Daily duty budget at steady state (capacity check — the user's "enough hands" math)

| Duty | Actor-turns/day |
|---|---|
| Straw water (39 tiles, every-other-day) | ~22 (incl. event-day extras) |
| Straw harvest (~4.6/day) + replant (~2.3) + fertilize (~4.6) | ~14 |
| Animals 16: CARE 16 + FEED ~8 (every-other-day legal) + collects | ~35 |
| Melon/carrot/wheat-filler chores | ~10 |
| Market orders (≤10/day cap) | ~3 |
| **Total** | **~85-95** |
| **Capacity: farmer + 9 hands = 10 actors x 24 turns** | **240** |

Headroom ≥ 2.5x — capacity is NOT the constraint; slippage discipline is (rule 2 above).

## 4. Revenue targets (measured anchors, H2H vs v1112fr)

Line | Their farm | Mirror parity | Our target
---|---|---|---
STRAWBERRY 39t | $57.2k (306u @ $186) | $24.8k | ≥ $28k (+SE share)
MILK 11-13 cows | $42.3k (254u @ $166) | ~$30k | ~$30k + timing guard
WOOL 3-4 sheep | $20.2k | ~$15k | ~$15k
MELON | $14.8k | — | $18k (we already beat them here)
FERTILIZER | $12.9k | — | $12.5k
EGG (goose, optional) | — | — | +$2.6k
WHEAT CARRY | +$4.1k net | — | skip (their market-maker game, 3% margin)
**TOTAL** | **$134k vs our current shape** | **$67k** | **≥ $72k while holding them ≤ $67k**

Where the mirror-parity edge comes from: melon (+$3.3k, already ours), sell-timing guard
(+$2-6k, the $137-vs-$221 receipt), optional goose (+$2.6k), SE late volume.

## 5. Build order — map first, guards only if they measure

- **Inc 1: THE MAP, zero reactive code.** Authoring = extend tape_author3 with the quad-by-quad
  schedule above (per-day hand counts, buy discipline with buffers, water-on-early-day rule).
  Gate: 12-seed solo — target ≥ 105k (champion band) with weed-tile-steps ≤ champion's baseline
  and zero missed-buys on the schedule; then 6-seed H2H sanity.
- **Inc 2: price-aware sell guard** (user's ask; required by receipt #3). A/B vs Inc 1.
- **Inc 3: feed rescue** (H18 check: wheat short → buy feed; the 2-day fuse). A/B — if Inc 1
  shows zero unfed days, this measures $0 and we delete it.
- **Inc 4: weed repair** (re-dig dead straw tile + replant same day). A/B — if Inc 1 shows
  ~zero dead tiles, delete it.
- **Inc 5: endgame polish** (terminal flush, SE decision, wheat-maker carry if margins allow).
- **Final gate:** 6-seed H2H vs v1112fr AND vs v120, 12 games each. Champion submission only on
  explicit user GO.

## 6. Decisions needed from user

1. **Straw from D3 in NW (recommended)** vs animals-first/melons-first with straw later —
   receipts say late straw = conceding the $57k line (v5a: D27 supply did nothing).
2. **Goose in the opening** — measured -$6k/game as a sheep swap; can include as knob, default out.
3. **Farmed vs bought feed** — A/B inside Inc 1 (both schedules mappable).
