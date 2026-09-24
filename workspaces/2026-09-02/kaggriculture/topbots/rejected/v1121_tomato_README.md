# v1121_tomato — WIP, DO NOT SHIP (session 91)

Endgame TOMATO scarcity play. Discovery: TOMATO is the only item with a real
endgame scarcity premium — town bakery consumes it, almost nobody grows it.
Measured: peikopon game (ep 100841489): $71 (D12) -> $522 (D29H15); they sold
45u at D29H18 = +$18.5k in 3 hours. CD goose game: $62-70 (field supplied).
Solo seeds: $64-111.

What was built: 12 strawberry tiles (D10-D11 SW wave) converted to tomatoes:
DIG D15/D16, PLANT TOMATO D17/D18, the v11.12 D26/D27 dig-replant cycles kept
with PLANT arg flipped strawberry->WHEAT, sells D26H20-D29H17.

Why it failed (sim, seed 1): all 12 tomatoes DIED. The tile's only watering
visits are the slots the PLANT replaced (the v11.12 hand walks water these
tiles every 2nd day, single unit; a plant starts consecutive_unwatered=1 and
dies if not watered the planting day). The only same-tile 2-unit work days are
the FERT+WATER pairs, which exist ONLY on D19/D20. A D19/D20 plant (FERT->
PLANT, keep the next-hour WATER) survives, but:
  * the D26/D27 replant DIG removes it at/just before first yield (D27),
  * the EOD-drop mechanic means D29 harvests are unsellable,
  => sellable value capped at ~1-3u/tile ~= $1-3k total, minus $720 seeds and
     ~$600 strawberry forgone. Below ship threshold.

The BIG play (peikopon's 145u / $18.5k) = a real EARLY tomato farm (D8-D12,
30+ tiles) — a full hand-walk choreography rebuild (same fragility class as
the cow-first rebuild, which lost $65k/game). And the premium is situational
(depends on bakery draws + field supply; solo is only $64-111 where melon
$150-250 beats it). VERDICT: shelve as a documented adaptive opportunity
(replant strawberry->tomato when tomato price crosses ~$200 mid-game), do not
build statically.
