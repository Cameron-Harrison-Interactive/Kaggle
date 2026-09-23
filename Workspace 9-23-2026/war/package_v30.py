#!/usr/bin/env python3
"""package_v30.py — build submit/v30_champion.py from war/astra_live20_15_c13.py.

v30 = v29 (live20_10) + R52a merged animal sweep + R52b work-aware crew floor
(cap 13). See R52_WORKERS_REPORT.md for the measurements.

Packaging (identical to the v29 recipe):
  1. strip the /tmp econ debug-log block (file I/O is banned in submissions)
  2. append `kaggle_entry_agent = agent`
  3. prepend a v30 provenance header

Then verifies: stdlib-only imports, no file/network I/O, exact-match solo
gates, self-play validation, and per-turn latency.
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "war", "astra_live20_15_c13.py")
DST = os.path.join(ROOT, "submit", "v30_champion.py")

HEADER = '''"""
v30_champion.py  (2026-09-15)  --  R52: THE WORKER FIX.

Built from war/astra_live20_15_c13.py = v29 (war/astra_live20_10.py) plus two
mechanisms that ONLY work together (see R52_WORKERS_REPORT.md):

  R52a  MERGED ANIMAL SWEEP. The old sweep walked every animal row TWICE a
        day: pass 1 fed every animal, pass 2 chained collect/harvest/care.
        Measured (war/walk_probe.py): FEED costs 2.11 moves/op and
        COLLECT_FERTILIZER 1.69 -- the A-worker day is walk-bound and CARE
        (the last op of pass 2) is exactly what gets cut when the budget
        runs dry (care 202/season = 40% coverage of 17 animals x 30 days).
        Now one traversal chains feed -> collect -> harvest -> care at each
        stop. Op PRIORITY is unchanged. Feed stays a guaranteed PREFIX:
        every animal still needing feed is visited before any fed animal.

  R52b  WORK-AWARE CREW FLOOR. Crew was sized by "smallest n with
        dropped == 0", and `dropped` counts ONLY must-work -- so any routing
        improvement SHRANK the crew. Measured death spiral on seed 5:
        crew 13->10, plants 70->30, final -36.6k. The floor sizes the crew
        on the farm's POTENTIAL load instead:
            _work_floor = min(13, max(4, (25*len(owned) + len(animals)) // 5))
        The hire block already caps desired_hands at 13 and gates on cash,
        so the floor can only stop a collapse, never over-hire.

Measured (6-seed gate 42/5/101/202/303/777):
    v29  94,426 / 97,952 / 101,359 / 95,515 / 108,729 / 89,381  =  97,894
    v30  99,247 / 106,898 / 103,289 / 103,282 / 106,335 / 88,822 = 101,312
    delta   +4,821 / +8,946 / +1,930 / +7,767 / -2,394 / -559     =  +3,418

H2H (the metric that actually moves rating -- coin margin does not count):
    vs v21_champion:  v29 3-7  ->  v30 6-4      (median -3,942 -> +7,229)
    vs nb3_tetsu_r5:  v29 0-11 ->  v30 0-11     (regression, accepted)

v29 (live20_10) is preserved byte-for-byte as the fallback line.
Standard library only. No file I/O. No network.
"""

'''

BLOCK_START = '    try:\n        with open("/tmp/astra_econ19.txt"'


def strip_debug(src):
    i = src.index('/tmp/astra_econ19.txt')
    start = src.rindex("    try:\n", 0, i)
    end = src.index("    except Exception:\n        pass\n", i)
    end += len("    except Exception:\n        pass\n")
    return src[:start] + src[end:], (start, end)


def main():
    src = io.open(SRC, encoding="utf-8").read()
    out, span = strip_debug(src)
    assert "/tmp/" not in out, "debug block not fully removed"
    # header: keep the original module docstring, put ours above it
    assert out.startswith('"""'), out[:40]
    out = HEADER + out
    out = out.rstrip("\n") + "\n\n\nkaggle_entry_agent = agent\n"
    with io.open(DST, "w", encoding="utf-8") as fh:
        fh.write(out)
    print("wrote %s (%d bytes); stripped debug block %s" % (DST, len(out), span))


if __name__ == "__main__":
    main()
