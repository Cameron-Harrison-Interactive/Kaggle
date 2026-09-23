#!/usr/bin/env python3
"""patch_r52a.py - build war/astra_live20_12.py from live20_10.

R52-A: MERGED ANIMAL SWEEP (single traversal).

The old sweep walked every animal row TWICE per day: pass 1 fed every
animal, pass 2 chained collect/harvest/care. Measured (war/walk_probe.py,
seed 42, v29 = live20_10): FEED costs 2.11 moves/op and COLLECT_FERTILIZER
1.69 - the A-worker's 24h day is walk-bound, and CARE (the last op of pass 2)
is exactly what gets cut when the budget runs dry (care 202/season vs 17
animals x 30 days = 40% coverage).

This patch visits each animal ONCE and chains feed -> collect -> harvest ->
care at the stop, preserving the original op priority order exactly. Feed
stays a guaranteed prefix: the row is re-ordered so every animal that still
needs feeding is visited before any already-fed one.

Single-mechanism diff: nothing else changes.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "war", "astra_live20_10.py")
DST = os.path.join(ROOT, "war", "astra_live20_12.py")

src = io.open(SRC, encoding="utf-8").read()
lines = src.split("\n")

# Lines 1046..1093 (1-indexed) hold the two traversals.
start, end = 1046, 1096
old = "\n".join(lines[start - 1:end])
assert old.startswith("                for pos_a, tile in mine:"), old[:80]
assert old.rstrip().endswith('w["pos"] = pos_a'), old[-80:]

NEW = '''                # ---- R52-A MERGED SWEEP (one traversal, all ops/stop) ----
                # OLD: pass 1 fed every animal, pass 2 chained
                # collect/harvest/care - the row was WALKED TWICE a day.
                # Measured (walk_probe, seed 42): FEED 2.11 moves/op,
                # COLLECT 1.69 -> the A-worker day is walk-bound and CARE
                # (last op of pass 2) is what the budget cuts. One
                # traversal = ~half the row walking for the same ops.
                # Op PRIORITY is unchanged (feed, collect, harvest, care) -
                # this patch only merges the walk.
                # Feed stays a guaranteed PREFIX of the walk: every animal
                # that still needs feeding is visited before any animal
                # that is already fed (survival can never lose to care).
                _unfed, _fedq = [], []
                for pos_a, tile in mine:
                    if not tile.get("fed_today") and not final_day:
                        # R38 (user tape, milk $1): FLOOR TRIAGE - a
                        # floored product's animal goes SURVIVAL-ONLY
                        # (engine truth: production is unfed; feed buys
                        # survival + the care bonus). Feed every other
                        # day, keep the asset alive for a price
                        # recovery - half the feed wheat, zero loss.
                        if ((quoted(ANIMALS[tile["animal"]][2]) <= 10
                             or quadrant(pos_a) == "SW")
                                and int(tile.get("consecutive_unfed", 0)) < 1):
                            _fedq.append((pos_a, tile, False))
                            continue
                        _unfed.append((pos_a, tile, True))
                    else:
                        _fedq.append((pos_a, tile, False))
                for pos_a, tile, _needs_feed in _unfed + _fedq:
                    d = distance(w["pos"], pos_a)
                    if _needs_feed:
                        if w["busy"] + d + 1 <= budget:
                            w["plan"].append(("FEED", pos_a, None))
                            w["busy"] += d + 1
                            w["pos"] = pos_a
                            d = 0
                        else:
                            # an unfed animal is a drop, never a silent
                            # skip - escapes take two consecutive misses
                            dropped += 1
                    if (tile.get("fertilizer_available")
                            and w["busy"] + d + 1 <= budget
                            and ("COLLECT_FERTILIZER", pos_a) not in pin_ex):
                        w["plan"].append(("COLLECT_FERTILIZER", pos_a, None))
                        w["busy"] += d + 1
                        w["pos"] = pos_a
                        w["cargo"] += 1
                        d = 0
                        maybe_drop(w)
                    if (int(tile.get("yield_units", 0)) >= (
                            # R38: SW row animals batch at 2 units -
                            # halve the fallback worker's collection stops
                            2 if quadrant(pos_a) == "SW" else 1)
                            and w["busy"] + d + 1 <= budget
                            and ("HARVEST", pos_a) not in pin_ex):
                        w["plan"].append(("HARVEST", pos_a, None))
                        w["busy"] += d + 1
                        w["pos"] = pos_a
                        w["cargo"] += 1
                        d = 0
                        maybe_drop(w)
                    if (not final_day and not tile.get("cared_today")
                            and quoted(ANIMALS[tile["animal"]][2]) > 10
                            and quadrant(pos_a) != "SW"
                            and w["busy"] + d + 1 <= budget
                            and ("CARE", pos_a) not in pin_ex):
                        w["plan"].append(("CARE", pos_a, None))
                        w["busy"] += d + 1
                        w["pos"] = pos_a'''

out = "\n".join(lines[:start - 1] + [NEW] + lines[end:])
with io.open(DST, "w", encoding="utf-8") as fh:
    fh.write(out)
print("wrote", DST, len(out), "bytes")
sys.exit(0)
