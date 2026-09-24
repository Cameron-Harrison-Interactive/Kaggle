# LIVE REPLAY ANALYSIS — episode 92975821 (v20 vs Álvaro Benítez) + v24 SHIP

## The API works now
The KGAT token is Kaggle's newer access-token format — it goes in
`~/.kaggle/access_token` (Bearer auth), not basic-auth username+key (my
earlier mistake, sorry). With it we pulled ALL submissions, episodes, and
the full 28MB replay of 92975821.

Live state: v20 posted at 11:31 today, **rating 1615.3** (v18 peak was
2739). v18.5 variant held 2369.9. v19 = 1870.3. So v20 has been losing.

## The loss chain — fully proven from the replay (not guessed)

**Result: LOSS $70,321 vs $103,475** (seed 1441928087).

1. d0h0: Álvaro opens with `BUY_PRODUCT WHEAT 14` FIRST in the queue.
   Our opening buys 5 wheat at the END of the queue. Their 14-unit buy
   inflates the wheat price ($25 -> $28.7) before our buy runs; we have
   ~$110 left -> only 3 wheat land.
2. We have 3 wheat for 5 animals on d0. The 5th sheep (placed late d0)
   goes unfed. d1 has ZERO wheat in the system -> it hits
   consecutive_unfed=2 -> **SHEEP ESCAPES end of d1.** (This is the
   "losing animals" you saw — it only happens under opponent wheat-price
   pressure, which is why our PASS audits never caught it.)
3. d0h1: they sell 9 wheat back (~$250, keep 5 for feed) — funds their
   d0 seed orders. 0 escapes for them.
4. d10h1: our `SELL WOOL 16` FAILS (3 sheep = no wool in shed). Theirs
   earns ~$3,120. That funds their d10 seed wave; ours dies with $54 and
   3 melon seeds -> **12 plants fail on d10** (7 strawberry + 5 melon).
5. We cap at 46 crops vs their 62 all mid-game. -$33k.

## FIXES SHIPPED (v24 = wheat_open + nocow + labor + cashrank)

- **wheat_open**: adopt the Álvaro opening (BUY_PRODUCT WHEAT 14 first,
  SELL WHEAT 9 + M3/W1 next turn). It's a feed-reserve AND a price
  weapon against everyone running the old opening.
- **nocow**: the (7,4) cow relocation (from the earlier session).
- **labor + cashrank** runtime insurance.

### Measured (the best contested numbers in project history)

| Matchup (seeds 1-2, both seats) | v24 |
|---|---|
| vs v20 | **4-0, +$14,029** |
| vs tetsu | **4-0, +$14,792** |
| vs rayk | **4-0, +$23,248** |
| vs kaito | **4-0, +$16,248** |
| self-mirror (everyone adopts it) | ≈ 0 (symmetric, no downside) |
| PASS seed 1 | **$177,932 (0 escapes)** |
| live-seed vs v20 | **+$13,299** |

Rejected by data: wholesale graft of Álvaro's market schedule onto our
tape (4 escapes — their market hours don't match our labor hours).
`submit/HI_AgriBot_v24_WheatGuard.tar.gz` packaged, smoke $147,855,
0.43ms/turn, loader-verified.

## POST v24. Then re-measure vs the ladder.

Note: v20's live rating sag is partly the (7,4) cow escape + the sheep
escape + the d10 wave collapse — all fixed — and partly mirror-coin-flip
volume. v24 attacks every known mechanism. If v24 stalls on the ladder
again, pull the next losing replay (kaggle competitions replay <id>) and
I'll diff the new opponent's schedule the same way.
