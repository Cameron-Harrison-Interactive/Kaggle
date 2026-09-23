"""Reserve fertilizer overnight so NE tick sprays can actually pick it up."""
from pathlib import Path
p = Path("war/astra_live20_36.py")
text = p.read_text()
old = """    fert_keep = max(0, len(fert_targets) - all_carried["FERTILIZER"])
"""
new = """    fert_keep = max(0, len(fert_targets) - all_carried["FERTILIZER"])
    # R64: strawberries are never in fert_targets (harvestable() is
    # always true once they hold a unit), so hourly sells emptied the
    # shed and NE pickup found nothing. Hold fert the day of a tick
    # AND the day before so h0 stock exists.
    if not final_day and quoted("STRAWBERRY") > quoted("FERTILIZER"):
        _nk = 0
        for _pos, _t in plants:
            if quadrant(_pos) != "NE" or _t.get("crop") != "STRAWBERRY":
                continue
            if int(_t.get("fertilized_until_day", -1)) >= day:
                continue
            _age = day - int(_t.get("planted_day", day))
            _tick = _age >= 9 and (_age - 9) % 2 == 0
            _tmrw = (_age + 1) >= 9 and (_age + 1 - 9) % 2 == 0
            if _tick or _tmrw:
                _nk += 1
        fert_keep = max(fert_keep, _nk)
"""
assert old in text, "fert_keep not found"
p.write_text(text.replace(old, new, 1))
print("patched keep")
