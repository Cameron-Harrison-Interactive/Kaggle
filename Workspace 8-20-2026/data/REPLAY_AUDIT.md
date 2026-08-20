# Live Replay Audit — submission 55391953 (11 games)

## Scoreboard
| Ep | Us $ | Opp $ | Margin | Seat | Weeds d15/d24 | Straw price d15/d20/d25 | Low-straw sells |
|----|------|-------|--------|------|---------------|-------------------------|-----------------|
| 91480578 | 149747 | 87889 | 61858 | 1 | 8/9 | 224/228/229 | 0 |
| 91478765 | 141311 | 56674 | 84637 | 1 | 8/9 | 217/225/216 | 0 |
| 91477855 | 141264 | 19871 | 121393 | 1 | 8/9 | 224/226/219 | 0 |
| 91485115 | 137148 | 118520 | 18628 | 0 | 0/7 | 245/246/206 | 0 |
| 91484221 | 104744 | 78175 | 26569 | 0 | 0/7 | 211/196/37 | 62 |
| 91483319 | 98119 | 88359 | 9760 | 1 | 8/9 | 218/196/12 | 68 |
| 91479665 | 92038 | 22513 | 69525 | 1 | 8/9 | 184/175/36 | 40 |
| 91486028 | 85176 | 77742 | 7434 | 1 | 8/9 | 219/219/182 | 0 |
| 91481479 | 78819 | 65761 | 13058 | 0 | 0/7 | 201/165/24 | 123 |
| 91476373 | 54065 | 54912 | -847 | 1 | 2/5 | 193/150/47 | 146 |
| 91482398 | 39936 | 82018 | -42082 | 1 | 0/1 | 209/188/128 | 0 |

## What the tape already does well
- **7/7 scored wins** (one incomplete). Peak **$149,747**.
- Midgame water d11-20 is solid on most games (weeds_d15 often 0 on seat0).
- End shed always empty (full cash-out).
- Fertilizer sold ~248/game (good).
- Tomato hedge **never fired** (0 tomato plants in 11 games) — market inv/price thresholds never hit.

## The $70k spread: high vs low games
High ($140k+): straw price stays **$200-230** through d25. Scripted straw dumps land in a healthy market.
Low ($54-98k): straw crashes to **$12-47** by d25. Same scripted dumps sell 40-146 units into the floor.

Money curves diverge **after d15-d20**, not from routing:
- Best: d15=$20k → d25=$114k → end $149k
- Worst contested: d15=$13k → d25=$63k → end $78k  
- Collapse: d15=$7k → d25=$31k → end $39k (wheat net-buyer, bad matchup)

## Experiments vs our bot (keep-gate)
| Change | vs 14.5 seed1 | Verdict |
|--------|---------------|---------|
| Broader tomato (opp straw≥8, price<110) | 54k-123k **LOSS −49k** | REJECT — steals too many straw plants from cash engine |
| Soft sell-hold floor $55 | 74k-105k **LOSS −26k** | REJECT — clogs shed, starves early cash |
| Momentum +20% dump | 76k-103k **LOSS −26k** | REJECT |
| Extreme hold floor $25 | 102k win but **−1 to −6k** multi-seed losses | REJECT |
| Pure v16.5 strict (no market change) | **103017 ≡ v15** | **SHIP** |

## Why sell-hold fails vs "our bot"
14.5/v15 mirrors keep straw prices mostly healthy. Holding for a crash that never comes
delays cash that funds hires/seeds/land. The crash only happens against straw-flood
opponents — we need a **family-gated** hold (only when opp_straw is high AND price
sliding) that was not keep-gate clean in this pass.

## Corner weeds (secondary)
d24 SW corner weeds (0,7-0,9) appear even in $140k wins. Coverage limit of 3-quad
tape, not pathing into locked tiles. Chat-Log-5 forbids path rewrites to chase them.

## Recommendation
1. **Post stays v16.5 StrictAdaptive** (tape route + water + tomato-as-was + DIG/fert PASS).
2. Next adaptive research: **family-gated** straw hold that only arms when
   `opp_straw>=20 and straw_price < 80 and day>=18` — test heavily vs 14.5 first.
3. Optional offline: recompile seat tape with one extra SW-corner water pass d12-d14
   (compile-time route fix, not runtime pathing).
