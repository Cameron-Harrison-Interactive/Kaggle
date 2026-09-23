#!/usr/bin/env python3
"""patch_r53.py - build war/astra_live20_17.py (R53 endgame leak fixes).

Three leaks found by watching v30 episodes and confirmed with
`war/endgame_probe.py` (seed 42, at the final whistle d29 h23):

    seed pouch : WHEAT 43          -> $430  (seeds can never be sold)
    shed       : SHEEP 1           -> $500  (bought, never placed)
    on workers : WHEAT 32, STRB 2  -> $1,040 (never reached the market)
                                      ------
                                      ~$1,970 burned per game

All three fixes are ENDGAME-ONLY, so they cannot disturb the mid-game.

FIX 1 - SEED BUY CAP (single choke point, inside buy_order).
  The pouch jumped 20 -> 43 on d28. Wheat planted on d28 first-yields on
  d30 - after the horn - so those seeds can never be sown. Cap every
  BUY_SEED by the crop's last plantable day AND by the crew's plant rate
  (~8/day). last_plant(crop) = 29 - first_yield_day:
      wheat/carrot d27 · tomato d21 · melon/strawberry d19.

FIX 2 - FINAL-DAY CARGO RESERVE (inside build_plan).
  Score is farm money at step 719. Cargo on a worker at the horn is $0,
  and the EOD auto-dump lands after the last step. On the final day we
  reserve 6 hours so the end-of-plan DROP always executes - and executes
  early enough for the hourly sell loop to convert it.

FIX 3 - FINAL-DAY DROP THRESHOLD (maybe_drop 4 -> 2).
  On the final day only. The all-days threshold-2 variant measured
  CATASTROPHIC (-$40-65k: constant shed returns ate the workday); on the
  last day there is little work left and the alternative is losing the lot.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "war", "astra_live20_15_c13.py")   # = v30
DST = os.path.join(ROOT, "war", "astra_live20_17.py")

src = io.open(SRC, encoding="utf-8").read()

# ---------------------------------------------------------------- FIX 1
OLD1 = """    def buy_order(order, estimated_cost, reserve=0):
"""
NEW1 = """    def buy_order(order, estimated_cost, reserve=0):
        # ---- R53 FIX 1: SEED BUY CAP (endgame leak) ----
        # Measured (endgame_probe, v30 seed 42): the wheat pouch went
        # 20 -> 43 on d28 and 43 seeds sat unsellable at the horn ($430).
        # A seed sown on d28 first-yields on d30 - after the horn - so it
        # can never be planted at all. Cap every seed buy by the crop's
        # last plantable day and by the crew's measured plant rate (~8/day).
        # last_plant = (total_days - 1) - first_yield_day:
        #   wheat/carrot d27 · tomato d21 · melon/strawberry d19.
        if order[0] == "BUY_SEED" and len(order) >= 3:
            _c = order[1]
            _lp = (total_days - 1) - ECROPS[_c][0]
            if day > _lp:
                return False
            _room = 8 * (_lp - day + 1) - int(seeds.get(_c, 0))
            if _room < order[2]:
                if _room <= 0:
                    return False
                order = ["BUY_SEED", _c, _room]
                estimated_cost = CROPS[_c][0] * _room
"""
assert src.count(OLD1) == 1, src.count(OLD1)
src = src.replace(OLD1, NEW1, 1)

# ---------------------------------------------------------------- FIX 2
OLD2 = """        pinned = None  # pinning measured net -6.5k solo (round 5)
        pin_ex = set()"""
NEW2 = """        # ---- R53 FIX 2: FINAL-DAY CARGO RESERVE ----
        # reward = farm money at step 719 and the EOD auto-dump lands after
        # the last step, so cargo on a worker at the horn is worth $0
        # (measured: WHEAT 32 + STRAWBERRY 2 on workers at d29 h23 = $1,040).
        # Reserve 6 hours so the end-of-plan DROP always runs, and runs
        # early enough for the hourly sell loop to convert it.
        if final_day:
            budget = budget - 6
        pinned = None  # pinning measured net -6.5k solo (round 5)
        pin_ex = set()"""
assert src.count(OLD2) == 1, src.count(OLD2)
src = src.replace(OLD2, NEW2, 1)

# ---------------------------------------------------------------- FIX 3
OLD3 = """            if w["cargo"] < 4:
                return"""
NEW3 = """            # R53 FIX 3: on the final day dump at 2 instead of 4 - the
            # all-days threshold-2 variant measured CATASTROPHIC (-$40-65k:
            # constant shed returns ate the workday), but on the last day
            # there is little work left and the alternative is losing it all.
            if w["cargo"] < (2 if final_day else 4):
                return"""
assert src.count(OLD3) == 1, src.count(OLD3)
src = src.replace(OLD3, NEW3, 1)

with io.open(DST, "w", encoding="utf-8") as fh:
    fh.write(src)
print("wrote %s (%d bytes)" % (DST, len(src)))
