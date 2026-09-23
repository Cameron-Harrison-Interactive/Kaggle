#!/usr/bin/env python3
"""patch_r52b.py - WORK-AWARE CREW FLOOR (R52b).

Generates:
  war/astra_live20_13.py  = live20_10 (v29) + crew floor
  war/astra_live20_14.py  = live20_12 (merged sweep) + crew floor

THE BUG THIS FIXES (found by war/standing_probe.py, seed 5):

  The crew is sized by `build_plan`'s "smallest n with dropped == 0", and
  `dropped` counts ONLY must-work (unfed animals, ripe harvests, dying
  plants). So ANY routing improvement - which fits the same must-work into
  fewer bodies - SHRINKS the crew. Measured:

    baseline  d12-d17: crew 13,13,14,14,14,14  plants 35,53,62,62,70,73
    merged    d12-d17: crew 10,10,12,10,10,13  plants 30,30,26,30,30,30

  That is a DEATH SPIRAL: fewer hands -> fewer plants tended -> less cash
  -> land/herd buys fail -> fewer quads -> the work-based crew floor falls
  again. The optional work (care, fert, routine water, weeds) that the
  extra hands would have done is invisible to `dropped`, so the planner
  happily gives it up to save ~$400/day of wages - and loses $36k.

THE FIX: floor the crew on the farm's POTENTIAL load, not on today's
must-work. `owned` ground + the herd is the honest work forecast:

    _work_floor = min(14, max(4, (25 * len(owned) + len(animals)) // 5))

Calibrated against the v29 baseline crew curve (seed 5):
  d2  1 quad,  4 animals ->  5   (baseline 5)
  d5  1 quad,  5 animals ->  6   (baseline 5)   +1 hand = $8/day
  d9  2 quads, 8 animals -> 11   (baseline 13)
  d12 3 quads,17 animals -> 14   (baseline 13)  +1 hand = $233/day
  d14 4 quads,17 animals -> 14   (baseline 14)

Safe by construction: the hire block already caps desired_hands at 13
(crew 14) and gates every hire on cash, so the floor can never over-hire
past the measured optimum - it can only stop the mid-game collapse.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OLD = '''        # hires target the SPEC crew (3/quad + 1/5 animals), not just the
        # zero-drop floor — the standing farm is tomorrow's load too
        state["crew"] = max(best_n, _spec_n)'''

NEW = '''        # hires target the SPEC crew (3/quad + 1/5 animals), not just the
        # zero-drop floor — the standing farm is tomorrow's load too
        # ---- R52b WORK-AWARE CREW FLOOR ----
        # `dropped` counts ONLY must-work, so every routing improvement
        # shrinks the crew - and a shrinking crew starves the farm that
        # funds the next hire (measured death spiral: crew 13->10,
        # plants 70->30, seed 5 -36.6k). Floor the crew on the farm's
        # POTENTIAL load instead: owned ground + the herd. The hire block
        # caps desired_hands at 13 (crew 14) and gates on cash, so this
        # can only stop a collapse, never over-hire past the optimum.
        _work_floor = min(14, max(4, (25 * len(owned) + len(animals)) // 5))
        state["crew"] = max(best_n, _spec_n, _work_floor)'''


def build(src_name, dst_name):
    src = io.open(os.path.join(ROOT, "war", src_name), encoding="utf-8").read()
    assert src.count(OLD) == 1, (src_name, src.count(OLD))
    out = src.replace(OLD, NEW)
    dst = os.path.join(ROOT, "war", dst_name)
    with io.open(dst, "w", encoding="utf-8") as fh:
        fh.write(out)
    print("wrote %s (%d bytes)" % (dst, len(out)))


if __name__ == "__main__":
    build("astra_live20_10.py", "astra_live20_13.py")   # floor only
    build("astra_live20_12.py", "astra_live20_14.py")   # merge + floor
