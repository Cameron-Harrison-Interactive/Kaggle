# V133B "EGGPLAT" — new-platform build spec (next session's build)

## Why this build (measured rationale)

1. The meta's only decisive edges over us are product-differentiation
   games: CD goose eggs (+$13.5k measured), peikopon tomato (+$18.5k).
   Sibling/cow-mirror games are a wash (v1112fr vs meta9 16-seed:
   −$819/game ≈ 0; the live 6-15k losses are variance + diversity).
2. EGG has measured demand in most meta games: BAKERY [EGG,WHEAT] and
   BRUNCH_SPOT [EGG,WHEAT,STRAWBERRY] consume eggs (6/day each, multiplier
   1). Today's meta losses show 2-3 egg shops in TIM (BAKERY×2), Ignat
   (BRUNCH×2), Maksim (BAKERY×3), Shadow (BAKERY+BRUNCH). The meta sells
   ZERO eggs (no geese in any of the 8 final herds). Egg price: base $50,
   rises as shops drain inventory (same channel as the tomato premium).
3. Egg economics for 3 geese (placed D10-D11, eggs D14-D29): ~90-110 eggs.
   0-1 egg-shop game: ~$5k at base. 2-3 egg-shop games: $10-16k (price
   rises toward $200-300 by D26-29). Costs: 3 coops on 3 strawberry tiles
   ($2.4-4.8k opp cost) + $900 geese + ~57 wheat feed (negligible vs the
   ~250 wheat produced). EV vs the meta ≈ +$2-4k/game, and it owns a
   product line no meta bot sells.

## Why the previous attempts died (measured, do not repeat)

- v131 (2 geese D0): D1-D3 feed geometry — no wheat exists before D2,
  geese escape. BLOCKED.
- v133a (1 goose D10, FEED insertions into existing walks): 0 eggs, cow
  escape D14 in 5/8 seeds. Root cause: FEED inserted on 1-step TRANSIT
  slots shifts the unit's whole downstream daily walk one step → cow feed
  hits an empty tile. (3,3) has ZERO 2+ hour dwell slots D11-D29. DEAD.
- v11.16 cow-first / v130 tomato / v1121-22 tomato endgame: portfolio
  economics dead.

## The fix: a DEDICATED goose unit (no existing walk touched)

Architecture: one hand unit whose entire daily job is the goose circuit.
No other unit's schedule changes (except u6's three single-action swaps,
which are position-neutral: BUILD_COOP replaces PLANT at the same tile
while u6 dwells there).

### Coop geometry (verified on the default platform map)
- Coop A (2,3), Coop B (3,3), Coop C (2,4) — the west triangle, all
  currently strawberry tiles (D10H7/H15/H19 plantings).
- All three reachable in ≤3 steps from the shed-adjacent tiles
  (4,4)/(4,5)/(5,4)/(5,5) — the circuit is short.

### Unit assignment
- HIRE the goose-keeper at D8H0 (the route already hires 8 hands there;
  add one — or reassign the least-loaded late hand, u13, from D8; verify
  u13's D8+ load first).
- Daily circuit (from D10H0, ~8-10 steps, fits inside the unit's current
  idle time — late hands dwell 5-11 h/night):
  (4,5) PICKUP WHEAT 3-4 → (3,4)→(2,4)? no — path: (4,5)→(4,4)→(4,3)→
  (3,3) FEED A → (2,3) FEED B → (2,4) FEED C → return to home tile
  (4,5)/(0,9 corner). CARE actions on the return leg (bonus: +1 egg per
  fed production day).
- Placement (one-time, D10-D11): keeper walks shed-adjacent → PICKUP
  GOOSE 3 → place A (D10), B (D11), C (D11); farmer untouched.
- FEED same day as placement (keeper carries the wheat).

### Market
- SELL EGG orders: D16/D18/D20/D22/D24/D26/D28/D29 × 15 (staggered so the
  price rises as shops drain; the D26-29 orders catch the $200-300
  premium). Egg is never bought by anyone (nobody grows geese) → no
  competition.

## Risk gates (hard; if any fails, stop and re-plan)

1. **D0-D12 gate (8 seeds)**: 0 animal escapes, 0 unwatered crop days,
   all 3 geese placed+fed by D11, 3 coops built, u6's crop work intact
   (strawberry/wheat plantings count unchanged minus the 3 coops).
2. **Full-game gate (8 seeds)**: geese survive to D29 (0 escapes), ≥80
   eggs sold, no crop/animal regressions vs v1112fr, net cash ≥ v1112fr
   in ≥6/8 seeds (the egg premium should carry the 3-tile opportunity
   cost in egg-shop games).
3. **Meta gate (16 seeds)**: v133b vs meta9 h2h ≥ v1112fr (no regression)
   and vs the recorded top-16 72-game bench ≥ v1112fr.
4. **Shop-draw sensitivity**: run the 72-game bench twice (same seeds) to
   confirm the layer->shop-draw channel isn't inflating the result
   (the v1112fr +39.5k included shop-draw swings; the platform build
   changes the layout, which changes the RNG stream — net must hold).

## Expected outcome (measured target, not hypothesis)

- vs meta9 sibling: ≥ v1112fr (wash +$0) + egg premium in egg-shop games
  ≈ +$1-2k average.
- vs recorded 72 metas: v1112fr's +39.5k baseline preserved (no layers
  removed beyond what v1112fr has) + egg premium ≈ +$4-7k.
- vs goose meta (CD class): closes the $13.5k egg gap (we sell eggs now).

## Session-97 continuation state

- v1112fr SHIPPED (sub 55925101, live, 662.5 accumulating).
- v133a DEAD (audit: 0 eggs, cow escapes, −4..−12k/seed) — the insertion
  class is dead on the existing platform; the dedicated-unit class is the
  next attempt.
- This spec's geometry (coops, circuit path, keeper hire timing) is
  verified against posmap.json; what remains is the walk authoring + the
  gate runs.
