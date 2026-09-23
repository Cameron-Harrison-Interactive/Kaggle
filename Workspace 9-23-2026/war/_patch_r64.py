"""R64: NE strawberry WATER+FERT on tick days when spray beats a sale."""
from pathlib import Path
src = Path("war/astra_live20_35.py").read_text()
text = src

old_fert = """                my_fert = [p for p in fert_by_quad.get(q, []) if p in band_set]
                if my_fert:
                    st = shed_near(w["pos"])
                    _carry = min(2, len(my_fert))
                    if (w["busy"] + distance(w["pos"], st) + 1 <= budget
                            and shed["FERTILIZER"] > 0):
                        w["plan"].append(("PICKUP_FERT", st, _carry))
                        w["busy"] += distance(w["pos"], st) + 1
                        w["pos"] = st
                        my_fert = my_fert[:_carry]
                    else:
                        my_fert = []
"""
new_fert = """                my_fert = [p for p in fert_by_quad.get(q, []) if p in band_set]
                # R64: NE strawberries - spray on the water tick when
                # one extra berry is worth more than selling the fert.
                # Paired WATER then FERTILIZE at the same stop (engine:
                # bonus only counts if the tile was watered that day).
                if (q == "NE" and not final_day
                        and quoted("STRAWBERRY") > quoted("FERTILIZER")):
                    _pair = []
                    for _p in band:
                        _t = tile_map.get(_p)
                        if (isinstance(_t, dict)
                                and _t.get("kind") == "PLANT"
                                and _t.get("crop") == "STRAWBERRY"
                                and int(_t.get("fertilized_until_day", -1)) < day
                                and not _t.get("watered_today")
                                and needs_water(_t)):
                            _pair.append(_p)
                    my_fert = _pair
                if my_fert:
                    st = shed_near(w["pos"])
                    _carry = min((8 if q == "NE" else 2), len(my_fert))
                    if (w["busy"] + distance(w["pos"], st) + 1 <= budget
                            and shed["FERTILIZER"] > 0):
                        w["plan"].append(("PICKUP_FERT", st, _carry))
                        w["busy"] += distance(w["pos"], st) + 1
                        w["pos"] = st
                        my_fert = my_fert[:_carry]
                    else:
                        my_fert = []
"""
assert old_fert in text, "fert prefix not found"
text = text.replace(old_fert, new_fert, 1)

# After harvesting an NE strawberry, still water+fert the same visit.
# Ongoing plants stay on the tile; elif-water skipped the tick.
old_h2w = """                            else:
                                # a ripe harvest is never silently lost
                                dropped += 1
                        elif (not tile.get("watered_today") and not final_day
                                and needs_water(tile)):
                            d = distance(w["pos"], pos_b)
                            if w["busy"] + d + 1 <= w["wbudget"]:
                                w["plan"].append(("WATER", pos_b, None))
                                w["busy"] += d + 1
                                w["pos"] = pos_b
                            elif (int(tile.get("consecutive_unwatered", 0)) >= 1
                                  or tile["crop"] in ("STRAWBERRY", "TOMATO")):
                                # dying plant OR missed yield-tick water:
                                # both are real losses the crew must see
                                dropped += 1
                        if (pos_b in my_fert
                                and w["busy"] + 1 <= w["wbudget"]):
                            w["plan"].append(("FERTILIZE", pos_b, None))
                            w["busy"] += 1
                            my_fert.remove(pos_b)
"""
new_h2w = """                            else:
                                # a ripe harvest is never silently lost
                                dropped += 1
                        # R64: NE strawberries keep the plant after
                        # harvest. Water the tick (and fert) on the
                        # same visit - elif skipped the bonus day.
                        _ne_strb = (q == "NE"
                                    and tile.get("crop") == "STRAWBERRY")
                        if ((not tile.get("watered_today") and not final_day
                                and needs_water(tile))
                                and (_ne_strb or not (harvestable(tile) or _ne_rotate))):
                            d = distance(w["pos"], pos_b)
                            if w["busy"] + d + 1 <= w["wbudget"]:
                                w["plan"].append(("WATER", pos_b, None))
                                w["busy"] += d + 1
                                w["pos"] = pos_b
                            elif (int(tile.get("consecutive_unwatered", 0)) >= 1
                                  or tile["crop"] in ("STRAWBERRY", "TOMATO")):
                                dropped += 1
                        if (pos_b in my_fert
                                and w["busy"] + 1 <= w["wbudget"]):
                            w["plan"].append(("FERTILIZE", pos_b, None))
                            w["busy"] += 1
                            my_fert.remove(pos_b)
"""
assert old_h2w in text, "harvest-water block not found"
text = text.replace(old_h2w, new_h2w, 1)

Path("war/astra_live20_36.py").write_text(text)
print("wrote", len(text))
print("R64 pair", "R64: NE strawberries - spray" in text)
print("R64 after harvest", "NE strawberries keep the plant" in text)
