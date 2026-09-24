# SESSION 110 — V46: FROM H2H PARITY TO 20-0 AND LIVE DEPLOYMENT (2026-09-08 evening)

## Arc
Started at 4-6 parity vs v39_simtwin ($54.3k vs $54.4k). Ended at **20-0 (two 10-seed sets), twin-mean $77.2k vs $57.3k, solo $85.0k**, with three submissions live (episodes accruing overnight).

## The three compounding breakthroughs
1. **Animal servers** `(len+2)//3` (was //4): 2 servers for 8-9 animals → 24h routes → missed feeds. Fix alone: 5-5 → 7-3.
2. **Strb endgame shape**: window d5-24 → **d3-19** (d20+ sows prod after d29 = pure waste; d3 start pulls first prods from d18→d13). + cow 9 @d12. → 7-3.
3. **CAPITAL REALLOCATION (the big one)**: cows 6@d2 ($1.6k) vs strb seeds d3-5. Slowing cows to 2/4/6/8/9 + geese 3 @d4 (egg≥45) moved early cash into the strb treadmill → **10-0, $69.5k**. Same recipe as melon-bank logic: crops before animals, always.
Then: tomato OFF when pxs≥150 (strb = 2× op-efficiency of tomato) → $72.5k. Strb 30 @d10+ + wheat pivot 16/20/26 → **$75.4k**. Melon d6 first-mover dump (live px 270→65 by d12; we sold from d10 into the crash) → **$77.2k**. Adaptive cows (milk px ≥150 gate — live milk crashes to $5 with 18 cows; twin meta holds 233) → $76.2k→$77.2k class.

## Live meta (decoded from 4 real episodes)
- Elite class (Danila Galkin $109k, Aryuemaan Chowdhury $104k, sunyuxiang $82k): strb 19-33, **melon as continuous rotation 17-19 tiles** (px holds 131-270), **sheep 9-10** (wool 237-246 stable all game), wheat 20-41 pivot, cows 8, crew 12, all-in capital ($3-14 cash @d4-8).
- **Milk crashes 186→$5** with 18 cows; **wool never crashes** (nobody produces); strb escalates 145→256; wheat 34→51.
- Our live results: v46 (20:40 sub) 2-2 — wins vs $39-52k class, losses vs elite $58k/$109k. v46b (21:03) 0-1 but **$82.8k** vs a $104k elite. LB: 571 early (rank 5339/8245; converging).
- tt_router resubmit scored 2218 (was 2483; field tightened). LB top now: Otter Vibe 2937.7, SpaTaro 2928.6, Matthew Huang 2902.7.

## Falsified today (do not retry)
- **Crew > 10**: 4th and 5th failures (11: 6-4/$59k; 12: 2-8/$54k, 0-10 router). Mechanism found: ops are TASK-limited (~83/day at any crew; units 50% idle by tasks) — extra hands add only walk overhead + hire-order budget pressure (hands clear EOD, re-hire = market orders; 10-order morning cap).
- **Sheep scaling** in any form vs twin: early sheep-5 (−$13k), d12+ ramp (−$17k), wool-gated (−$4k). Capital+ops always beat the wool desk in twin meta. Live insurance version kept (fires only @wool≥180 AND strb≥24 from d16).
- **Router portfolio verbatim** (strb 26 @d2 + wheat 26 pivot + sheep 5 + geese 3 @d0): $22.3k — starves; the elite finances it with tape choreography we don't have.
- **Tape-replay opponents**: even on the native seed, a lone tape diverges to $0 (market-coupled chaos). Only verbatim both-seat replay is faithful.

## Submissions (quota exhausted: 5/5 used today)
- 56106704 v46 "20-0" ($69.5k-class) 20:40 — live 2-2
- 56107017 v46b "live-meta" ($76.2k-class) 21:03 — live 0-1 ($82.8k best live score)
- 56107017+ v46c "final" ($77.2k-class + all insurance gates) ~21:50 — episodes pending
- Fallbacks in topbots/: v46_snap_77k.py (=current), v46_snap_76k.py, v46_snap_75k.py, v46_snap_200.py

## Live-only insurance layers in v46c (free vs twin, untestable locally)
- strb early gate 120 (live pxs 145 @d8 fell below old 150 gate → under-sowed)
- melon rotation 12 @d10+ if pxm ≥ 180 (Danila-game level; twin crash excluded)
- late wool desk (sheep ≤3 @d16+ only if wool ≥ 180 AND strb standing ≥ 24)
- adaptive cows (milk ≥ 150 → 9; else 6)

## Next session
1. Check overnight episodes of all 3 subs (episodes <id> + replay CLI works; slug = kaggriculture, /tmp/slug rebuilt). Whichever class wins live, iterate that direction.
2. Remaining known leaks: feed tail (1-2 missed feeds/day ≈ $2-3k); strb standing under-delivery live (13 vs 30 target in Roy game — diagnose money vs plant-task priority with live-shaped opponents).
3. Elite gap = $21k ≈ melon rotation + sheep 9 + strb 33 + wheat 41 on crew 12. Our crew-10 envelope: strb 30 + wheat 32 + melon 12. The ceiling without crew-12 routing: ~$85-90k live.
4. Quota resets ~midnight; 5 slots.
