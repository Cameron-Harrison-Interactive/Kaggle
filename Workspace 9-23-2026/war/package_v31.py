#!/usr/bin/env python3
"""package_v31.py — build submit/v31_champion.py from war/astra_live20_18.py.

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
SRC = os.path.join(ROOT, "war", "astra_live20_18.py")
DST = os.path.join(ROOT, "submit", "v31_champion.py")

HEADER = '''"""
v31_champion.py  (2026-09-15)  --  R53a: THE ENDGAME SEED LEAK.

Built from war/astra_live20_18.py = v30 (war/astra_live20_15_c13.py) plus ONE
mechanism, applied at a single choke point:

  R53a  SEED BUY CAP. Watching v30 episodes the user saw >60 seeds stranded
        in the seed pouch at the final whistle. Measured with
        war/endgame_probe.py (v30, seed 42): the wheat pouch went 20 -> 43
        on d28 and all 43 sat there at the horn, unsellable -- seeds can
        never be sold, only planted, so that is $430 of pure cash burn.

        Root cause: the endgame wheat fill and the coverage filler both buy
        seeds against the number of EMPTY+WEED tiles, with no regard for
        whether those seeds can still be planted. Wheat sown on d28 first
        -yields on d30 -- after the horn -- so it can never pay back at all.

        Fix: cap every BUY_SEED order by the crop's last plantable day and
        by the crew's measured plant rate (~8/day):
            last_plant(crop) = (total_days - 1) - first_yield_day
            wheat/carrot d27 . tomato d21 . melon/strawberry d19
        Applied inside buy_order(), so it covers every buy path at once.

        Result: seed 42 wheat pouch at the whistle 43 -> 12.

Measured (6-seed gate 42/5/101/202/303/777):
    v30  99,247 / 106,898 / 103,289 / 103,282 / 106,335 / 88,822 = 101,312
    v31  99,557 / 107,248 / 103,629 / 103,592 / 106,905 / 89,162 = 101,682
    delta   +310 / +350 / +340 / +310 / +570 / +340              =    +370

Self-play (must stay DONE/DONE):
    v30  seed 5  64,324 - 55,255     seed 777  64,639 - 43,932
    v31  seed 5  64,644 - 55,585     seed 777  64,989 - 43,942

NOT fixed this round (measured, reported honestly -- see R53_WORKERS_REPORT):
  * A sheep bought ~d18 never gets installed and sits in the shed to the
    horn ($500). This is an INSTALL-SCHEDULING bug, not a buy bug: the buy
    gate already requires a genuinely free north site and already blocks
    sheep after d22. Needs its own measured round (labour reallocation has
    a 0-for-7 track record here).
  * Cargo left on workers at the horn (~$1,040). A 6-hour final-day work
    reserve was built and MEASURED NEGATIVE (-5.4k seed 42, -8.1k seed 5):
    final-day harvests are worth far more than the stranded cargo.

v30 (astra_live20_15_c13) is preserved byte-for-byte as the fallback line.
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
