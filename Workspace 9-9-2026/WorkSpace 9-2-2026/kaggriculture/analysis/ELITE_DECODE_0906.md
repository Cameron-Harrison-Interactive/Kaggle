# Elite Decode — the 2950+ Class Recipe (2026-09-06)

Source: 09-05 daily dataset top episodes + our live loss replays (see SESSION_106/107 reports).

## The three laws

1. **Wheat-fert loop is the volume base.** keiz (#2, 2888.9): WHEAT $52-60k from 1,188-1,495u
   @$40-44. Dmytro: $106k from 2,461u. Engine: ~24 wheat tiles + 8-14 cows as FERTILIZER
   factories (pastures generate fertilizer → FERTILIZE ops → wheat yields). Cows are for
   fert, not milk. Wheat demand is deep (BAKERY+BRUNCH+FARMERS_MARKET drain).
2. **Premium windows, low volume.** MaterW sold MILK 226u @$202 (h22/h14/h18 windows).
   k2900: milk 120u @$243, wool 107u @$181. The tetsu class dumps milk at h7 → $4/u floor.
   Volume discipline beats volume.
3. **Differentiation = both sides score; overlap = both crash.** keiz (wheat+tomato) vs JB
   (milk+wool): both $111-126k. Mirror-vs-mirror same portfolio: both $43-77k.

## The crash autopsy (our $43-73k games, episodes 105955040/105954391/105948761)

- All three opponents run OUR build (9C/8S/24W/33S/12M — tetsu forks everywhere).
- STRB price timeline (Rister game): $186-194 through d17 → both sides dump ~6-9u/day each
  → $68 (d18) → $32 (d19) → **$1 floor from d20, PERMANENT** (no bounce; supply >> demand).
- MILK/STRB/WOOL/MELON all crash the same way when both sides run them.
- WHEAT + FERT survive (deep demand): $26-28k + $10-11k even in crash games.
- **Crash-game tiebreaker = the uncontested niche: every winner had CARROT $3.8-4.8k.**
  We run none. (Prior "tomato niche" law = same principle; keiz runs 30 tomato tiles.)

## Elite census snapshots (09-05 dataset)

| Player | final | herd@20 | crops@20 | top revenue |
|---|---|---|---|---|
| keiz (W vs JB) | $126,148 | 14C+1G+4? | 25 STRB + 30 TOMATO | WHEA $51.7k(1188u), TOMA $13.3k, FERT $11.4k, STRA $10.4k |
| Jesse Bullard (L) | $111,099 | 9C+5S | 23 WHEAT + 38 STRB + 6 TOMATO | WHEA $30.8k, MILK $13.2k, FERT $9.5k |
| keiz (W by $162) | $125,768 | 11C+11S+1G | 18 WHEAT + 32 STRB | WHEA $59.9k(1495u!), STRA $24.9k(140u@$178), FERT $10.7k |
| Jesse Bullard | $125,606 | 6C+11S | 23 WHEAT + 33 STRB | WHEA $27.6k, MILK $21.5k(119u@$181), STRA $13.6k, WOOL $8.6k(121u) |
| Mater Welon (W) | $134,340 | 8C+9S | 24 WHEAT + 33 STRB | MILK $45.6k(226u@$202), STRA $31.7k(169u@$187), WHEA $29k |
| Dmytro (L) | $107,781 | 4C+11S | 23 WHEAT + 31 STRB | WHEA $106.5k(2461u!), MILK $17.9k |

Sell-hour laws: elite wheat at **h1-h2 (night band)**; premium milk at h14/h18/h22/h0;
fert at h1-h3/h5-h7. Our class: wheat h19/h22, milk h7 — the crowded windows.

## Route-class profiles (local, clean market)

- k2900_extracted solo: $154,421 — STRA $34.7k(249u@$139), MILK $29.2k(120u@$243),
  WHEA $25k(594u), FERT $20.1k(257u), WOOL $19.3k(107u@$181). Premium-window seller.
- verbatim-2900 notebook: runs as-is, last callable = `agent` ✓, solo $138,453.
- v27_metareset: solo $120,479; entrypoint `_kaggle_submission_entrypoint` wraps agent
  correctly (verified) — future candidate.

## Implications

1. Live actives (09-06): v4b-fixed (56047687, 2526-class floor) + 2900-verbatim
   (56048083, route-class premium portfolio = differentiation by construction).
2. Next-gen (goose line) design brief: wheat-fert loop base + premium-window selling +
   adaptive niche anchor (read opponent tiles by d8 → pivot to carrot/tomato if contested)
   + strb discipline (sell d14-17 at $180+, stop below $80).
3. No timing overlay can fix the crash: the floor is permanent once total supply crosses
   demand. Portfolio composition is the only lever.
