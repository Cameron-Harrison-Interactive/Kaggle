# V134 "EGGCORE" — goose-core platform build spec

## Why this shape (measured, not hypothesized)

1. **Add-on differentiation is infeasible on the v11.12 platform** (session 97,
   measured): a goose needs a daily FEED at a coop tile; no unit dwells ≥2h at
   the west triangle ((3,3)/(2,4)) on any D11-D29 day with a replaceable slot
   (v133a audit: 0 eggs, cow escape D14 in 5/8 seeds — transit-step insertions
   permanently derail the unit off its walk loop). The only safe dedicated
   keeper = a 14th hand hired daily = $377/day (fib hire cost) × 18 days =
   $6.8k > egg revenue of 2 geese ($2.4-9k). Dead on economics.
2. **The working goose meta (CD, +$22.2k over us in ep 100939868) is a
   goose-CORE platform**: geese from D0-D2, ~5 of ~8-10 escape D1-D3 (the
   measured D0-D3 feed-geometry tax — no wheat before D2; CD paid this tax and
   still netted +$13.5k on eggs from the survivors). Eggs: base $50, premium
   to $200-300 when BAKERY/BRUNCH shops drain inventory (2-3 egg shops in most
   meta games; the meta sells zero eggs otherwise).
3. Therefore: the new platform's CORE income = eggs (D0 geese) + milk (small
   cow ramp) + wool (4 sheep funding), NOT the v11.12 strawberry/wheat-MM
   platform with geese bolted on.

## Economics (target, to be confirmed by the build audit)

- D0: 4 SHEEP ($2,000, wool funding) + 8 GOOSE ($2,400) + 2 WHEAT plant
  (seeds) — total ~$4.6k of the $3.0k start + D0-H0 buys... (funding plan in
  D0-D4 phase below; the D0-D3 escape budget ≈ 5 geese × $300 = $1,500 lost).
- Survivors ~3-4 geese D3+ → eggs D7-D29 ≈ 150-190u:
  - 0-1 egg-shop games: ~$8-10k @ ~$50-60 base
  - 2-3 egg-shop games: ~$20-35k @ $100-280 rising
- Cow ramp: 6-8 cows D4-D10 (reduced from 11 for cash/slots) → ~120-160 milk
  ≈ $20-30k.
- Wool: 4 sheep ≈ 180u ≈ $30-40k (price-dependent).
- Total ≈ $100-130k class (vs v1112fr's $110-140k) + the egg premium in
  egg-shop games where no meta bot competes.

## D0-D12 phase (this build's scope, next session)

### Funding (measured against the $3,000 D0 budget)
- Pure goose-core (the CD shape: no sheep) is fundable but drops the $30-40k
  wool engine -> platform cash ~$65-90k class (CD's own game: $64.6k).
  WEAKER than v1112fr ($110-140k) - only the egg premium makes up the
  difference. Not a v1112fr replacement.
- **Chosen shape: goose-sheep HYBRID core** - v11.12's funding engine (4
  sheep) + a goose line funded by the D0 buffer + D2 wheat + D6 wool:
  - D0: 4 SHEEP ($2,000) + WHEAT 5 ($~175) + SEED WHEAT 5 + SEED MELON 6 +
    HIRE x4 ~ $2,830 -> buffer $170. Pre-build 4 COOPs on the keeper circuit.
  - D1: +2 GOOSE ($600, buffer + D1 market slack). D1 feed = D0-bought wheat
    (the v131 lesson - the ONLY D1 feed source). Keeper (D1 hands[3]) circuit
    D1H1-H12: PICKUP WHEAT 6 -> FEED the 2 geese first, then sheep (geese
    have no D2 fallback). Missed feeds = the budgeted tax (expect 0-1 escapes).
  - D2: WHEAT first yield (D0 plants). +2 GOOSE (D2 wheat sales fund).
  - D3-D5: +1-2 GOOSE (wheat sales + egg start D5-D6 = first egg revenue).
  - D6: SHEEP wool first yield -> wool sell spike -> +2-3 GOOSE + first COW.
  - D8-D12: cow ramp to 4-6 cows (wool + eggs funded), west crop batch starts
    (wheat/melon/strawberry on non-coop tiles), egg sells D5+.
  - D12 clearance bar: 8-10 geese + 4 sheep + 4-6 cows, >=40 eggs sold,
    >=$15k cash.
- Platform cash projection: wool $30-40k + eggs $8-25k (150-200u @ $50-250)
  + milk $15-25k (6 cows) + crops/MM $20-30k ~= $85-120k: v1112fr-class
  minus the 11->6 cow milk cut, PLUS the egg premium in the 2-3 egg-shop
  games where no meta competes.

### The keeper circuit (the platform's spine)
- Keeper = hands[3] (4th hand of the day; hire cost $3 — cheap; exists every
  day D1+).
- Daily circuit: shed (4,4)/(4,5) PICKUP WHEAT n → walk the coop cluster
  (FEED each goose tile; CARE on alternate days for the +1 egg bonus) →
  pasture cluster (FEED cows from D4) → return to shed DROP eggs/wool...
  (exact geometry authored in the build; must be ≤22 steps/day to fit).
- Everything else (crops, MM, sheep wool) = the non-keeper hands, authored
  fresh (NOT the v11.12 crop schedule — the v11.12 west crop tiles are
  where the coops/pastures go).

## Risk gates (hard — fail = re-plan, do not ship)

1. **G1 — D0-D4 (8 seeds)**: ≥3 geese survive to D4; 4 sheep intact; 0 cow
   escapes; D1 feed lands on ≥3 geese (the rest are the budgeted tax).
2. **G2 — D5-D12 (8 seeds)**: keeper circuit completes every day (audit:
   every goose tile fed daily, 0 unfed streak ≥2); ≥5 geese + 1-6 cows alive
   at D12; egg sell orders commit ≥20 eggs by D12.
3. **G3 — full game (8 seeds vs pass)**: ≥120 eggs sold; no animal escapes
   after D4; final cash ≥ $90k (the platform-clearance bar).
4. **G4 — meta gates (16 seeds)**: vs meta9 (9-cow sibling) ≥ −$5k avg
   (parity-within-noise), vs the 72 recorded metas ≥ v1112fr − $10k, and in
   the 2-3 egg-shop games specifically: ≥ +$5k vs v1112fr (the egg premium
   must show up where it exists).
5. **G5 — shop-draw sensitivity**: run G4 twice (same seeds, different
   order) — the layout-RNG channel must not be the source of the edge.

## Session-97 continuation state

- v1112fr SHIPPED (sub 55925101, live). It remains the measured-best tape
  until v134 clears G1-G5.
- v133a (goose add-on): DEAD — audit + keeper-cost math (this spec §1).
  Quarantined rejected/v133a_goose.py.
- Next session: author the D0-D4 phase of v134 (the walk authoring is the
  critical path — the goose coop cluster geometry + keeper circuit), run
  G1, iterate to a pass, then D5-D12 + G2.

---

# MEASURED VERDICT (session 99+, 2026-08-31) — v134 EGGCORE is NOT shippable

Final build (v134b architecture: v1112fr tape + SE egg farm, 2 grafted hands
hired last each day D12-D29, 10 geese, same-day/next-morning egg sells,
keeper DROP where it fits) — 8 seeds vs same-seed v1112fr base:

  seed 1 (IFSPFSPF):  Δ -$21,237   eggs 42   escapes 0
  seed 2 (YFSBPIPB):  Δ -$30,719   eggs 42   escapes 0
  seed 3 (BPFBBFPI):  Δ -$24,244   eggs 41   escapes 0
  seed 4 (BFBPYPPB):  Δ -$11,083   eggs 42   escapes 0   (2 BAKERIES)
  seed 5 (FFPPFBIB):  Δ -$29,277   eggs 45   escapes 0
  seed 6 (BFSFBFBP):  Δ -$18,388   eggs 13   escapes 0
  seed 7 (BYSYIPIB):  Δ +$3,917    eggs 13   escapes 0   (yarn draw luck)
  seed 8 (PBBBPSBI):  Δ -$29,812   eggs 45   escapes 0   (3 BAKERIES)
  AVERAGE Δ: -$19,980   avg eggs sold: 35   G1/G2/G3: 0/8

The platform WORKS (10/10 geese alive at end of every seed, 0 animal
escapes, 10 coops, 128 eggs harvested), but it LOSES money everywhere,
including egg-shop games. Egg premium never materializes: 10 eggs/day vs
town demand 1-4/day oversupplies the market, price settles BELOW the $50
base, and the fixed costs exceed the product value even with FREE labor.

## Why eggs lose (measured breakdown)
- Fixed costs: SE land $4,000 (yarn variants: SW+SE $6,000) + 10 geese
  $3,000 + feed wheat ~10/day x 18d x ~$27 ≈ $4,900 = $12.9-14.9k.
- Product value (best case, perfect logistics): ~128 eggs x ~$45 = $5.8k
  + ~160 fert x ~$25 = $4k ≈ $9.8k.  ->  -$3 to -$5k EVEN WITH FREE HANDS.
- Hand cost (the actual layer): 2 hands at hire positions N+1/N+2 =
  fib(N)+fib(N+1) = $233-$2,584/day x 18d ≈ $11.1k.
- Realized logistics loss: shed runs 90-95/100 saturated (v1112fr's
  design); EOD hand-drop DISCARDS overflow -> only 35-48 of 128 eggs
  sellable. Same-day DROP+sell recovers a few more; cap ~100.
- Repath variant (hire my 2 hands FIRST to save fib cost) measured dead:
  inserting 2 hires shifts all v1112fr hires +2 up the fib ladder
  (~$9k/day-class total, only ~$2k better than last-2), AND the router's
  wheat market maker reacts to the layer's lower cash: shed wheat at H00
  runs to ~0, farmer pickups shortfall, cow FEEDs miss 2 straight days
  -> 8 cows + 2 sheep escaped on seed 1.

## Break-even requirements (none available in this engine)
- Egg price >= ~$130 (2.6x base) with 10-egg supply, or
- ~3x goose egg output, or
- free hands (fib ladder makes 11th+ hands cost $89-$1,597/day).

## Disposition
- v134 code retained in topbots/v134.py (final measured build) — DO NOT
  SHIP. Quarantine note: it is a working egg platform, just negative-EV.
- Live bot stays v1112fr (sub 55925101). Correct call, now with data.
- Real levers for future sessions (from this session's measurements):
  1. Shed headroom: v1112fr runs 90-95/100; EOD overflow discards real
     inventory (wheat/eggs/etc.). A shed-management tweak is worth
     ~$1-3k/game — cheaper than any animal add-on.
  2. Wheat maker front-running: it re-timed buys when cash was low
     (44-unit vs 22-unit entries); its reserve logic may be left on the
     table in some draws.
  3. G4 meta bench (72 tapes vs meta9 etc.) still owed — that is where a
     +$5k edge must be demonstrated, and eggs are NOT the path to it.
