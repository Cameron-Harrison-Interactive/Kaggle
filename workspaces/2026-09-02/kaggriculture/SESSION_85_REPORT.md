# SESSION 85 — The (2,1) Class Strikes Live (ep 101085547, 101115302) + the rescue-EV ceiling

## 1. ep 101085547 vs Chakrabhuana V Deva (−$13,000; team rank 471→1259)

Opponent = cow-first custom engine (D1: 2 HIRE, 1 COW, 6 MELON seeds, 6 WHEAT
seeds + SELL WHEAT 5). Final: his 13 productive animals (8c/5s, 0 escapes)
vs our 11 + 3 cows stranded in the shed.

Loss decomposition (measured):
- **(2,1) COW escaped D7** — the original classic class (placed D4, fed fine
  D4-H12, unfed ALL of D5, unfed ALL of D6, escape D7H00). The wave's feeder
  even stood ON (2,1) at D5H17 and D6H10-H17 with NO WHEAT in hand (no-op
  FEEDs) — the feeder's wheat supply failed, the slot was consumed by the
  desync/weed slip, and v11.10's rescue window (streak>=1 from H18) started
  after the damage window: at D6H18+ only a wheat carrier within ~5 tiles
  could save it (a shed fetch needs 7 steps > the 6h left). No carrier in
  range -> escape.
- **3 cows stranded in the shed to game end** (EOD auto-drop loop: shed
  0->5 at D7H00, morning pickups fire, place slots consumed by the slip,
  3->5 at D8H00, 3->5 at D10H09...). 3 cows × ~20 days of milk+fert.
- Opponent out-production: milk 835 vs 333 (−$125k gross), strawberry 748
  vs 422 (−$47k), melon 232 vs 72 (−$24k), fert 445 vs 396 (−$4.5k); our
  wheat edge (+$72k gross, 2596 vs 1108 sold) did not offset it.
- Eggs were ~$1.5k — the "won with eggs" is really the bigger herd.

## 2. The rank drop (471 → 1259, 1994.5 → 1615.8) is rotation, not decay

Posting v11.9 (16:33) retired v11.7 (1994.5, sub 55808478) from the active
pair; posting v11.10 (~18:30) retired v11.8b (1494). Team score = max of the
active pair; the 1994.5 rating is locked to the retired v11.7 submission and
cannot be recovered — a re-post of the same code starts a new sub at 600.
v11.9/v11.10 are playing every 4 min (fresh scheduling); v11.9 is at 1615+
and climbing. Expect the team score to converge back to ~2000-2100 as they
accumulate wins (v11.7 took ~24h+ to reach 1994.5 from 600). **Do not post
today** (would retire v11.9 and drop the floor further).

v11.10 early form (6 games): 3W-3L incl. one more (2,1) D7 escape
(ep 101115302 vs Bernardus, −$19.9k; opp kept 11/11 animals) — the class is
still leaking live, as predicted.

## 3. Why the (2,1) class resists runtime rescue — the EV ceiling (proven)

Three rescue variants built, benched (process-isolated 88-game field matrix +
ghost A/B), all rejected:

| variant | field 80-game avg | verdict |
|---|---:|---|
| H15 "unfed-since-H0" alarm (H15-alarm) | **−$27,000** (80/80 nonzero) | CATASTROPHE: the wave feeds in the EVENING (H16-H23); at H15 every animal is "unfed" -> 2 hand-hours hijacked EVERY day |
| Self-calibrating per-tile feed-deadline alarm (H15b) | **−$28,170** (80/80 nonzero) | CATASTROPHE: the wave's normal slips (happening in every game) trip the 3h-late alarm -> dispatches too often |
| Morning carried-animal placement (H0-H6, anti re-stranding) | ghost −$1,865 + 3 extra sheep stranded | Rejected: pre-empts the wave's own place choreography |

**The ceiling:** each dispatch hijack costs ~$3-4k in cascading wave damage
(this engine's wave is a precision instrument; any hijacked hand-hour
propagates), while an escape costs ~$5-8k and happens in ~8% of games →
rescue EV is positive only at fire rates <~0.15/game. v11.10's narrow design
(streak>=1, H18+, stand-down when the tape is still feeding, ~15/80 games
firing, −$250/game) is already at that ceiling. Any earlier/wider alarm
crosses it catastrophically. **The (2,1) first-day miss is unsavable by
runtime dispatch** (needs a 7-step wheat delivery that must start by H16,
but acting by H16 false-alarms in every healthy game).

## 4. The real fix (next session): tape-level wave robustness

The (2,1) miss is tape-level: the cow's feed slot is consumed by the
1-step desync + weed-DIG slip. Tape-level fix (surgical, then benched on the
full 88-game matrix before shipping):
1. **Redundant early feed slot for (2,1)** (H6-H8, first 2-3 days): a second
   FEED attempt by a passing unit; if the main slot fires, the redundant
   attempt is a harmless no-op; if the main slot is consumed, the cow is fed
   before the danger window. Also for the D6/D7 cow cluster ((5,2)/(6,1)/(6,3)).
2. **Schedule-compressing weed repair** (v22): when a DIG consumes a step,
   DROP the next deferrable action (FEED-of-an-already-fed-adjacent /
   CARE) instead of shifting the whole downstream wave by 1 — keeps the
   (2,1) feed slot intact.
3. Same treatment for the EOD re-stranding loop: the tape's morning place
   slots for auto-dropped animals need redundancy (the 3-cow-stranded loss).

Each change benched on the isolated 88-game matrix (the contaminated-ghost
problem: fixed-tape opponents go bankrupt on early market shocks — ghosts are
for A/B, the field matrix is the ship gate).

## 5. Other loss-101085547 component (next session after #4)

Cow-heavy route variant (opponent's 1c-D1 opening -> 8c/5s): milk/straw/melon
out-production cost −$197k gross vs our +$72k wheat edge. Candidate: a
cow-heavy route option (1 COW on D1 instead of 4 SHEEP) selected by shop
config (milk-healthy seeds). Bigger route surgery; after the (2,1) fix.

## Ship state
- main.py = v11.10 (sub 55824203, live, converging). Rejected v11.11
  variants quarantined in topbots/rejected/.
- Active pair: v11.9 + v11.10. Team 1615.8 climbing (rotation, not decay).
- 2 submission slots remaining today: HELD (posting drops the floor).
- Tomorrow: 5 fresh slots for the tape-robustness ship.
