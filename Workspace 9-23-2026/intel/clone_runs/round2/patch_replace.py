from pathlib import Path
p=Path('war/meta_v1.py');s=p.read_text()
def rep(a,b):
 global s
 assert s.count(a)==1,s.count(a);s=s.replace(a,b,1)
rep('''        if pos is not None and pos in SCATTER_PADS:
            return None''','''        if (10 <= day <= 26 and pos in (
                (1, 2), (1, 3), (1, 4), (2, 3), (3, 3))
                and not final_day):
            # Replay: these spent melons become the NW wheat patch.
            return "WHEAT" if vseeds.get("WHEAT", 0) > 0 else None
        if pos is not None and pos in SCATTER_PADS:
            return None''')
a='''                                if tile.get("crop") == "MELON":
                                    # Replay: d10 dump. Walk the 5-6 units
                                    # to the shed the same afternoon.
                                    w["cargo"] += max(
                                        0, int(tile.get("yield_units", 1) or 1) - 1)
                                    maybe_drop(w)
                                elif not my_fert:
                                    maybe_drop(w)
                                if (tile["crop"] not in ("TOMATO", "STRAWBERRY")
                                        and not final_day
                                        and (zone_room > 0
                                             or (q == "SW" and tile["crop"] == "WHEAT"))):
                                    crop = plan_crop_choice(vseeds, filler=True,
                                                            quad=q, pos=pos_b)
                                    if crop is not None and w["busy"] + distance(w["pos"], pos_b) + 2 <= budget:
                                        w["plan"].append(("PLANT", pos_b, crop))
                                        w["plan"].append(("WATER", pos_b, None))
                                        w["busy"] += distance(w["pos"], pos_b) + 2
                                        w["pos"] = pos_b
                                        vseeds[crop] -= 1
                                        planned_standing[q] += 1
                                        zone_room -= 1'''
b='''                                _refill_nw = (q == "NW" and day >= 10
                                              and tile["crop"] in ("MELON", "WHEAT"))
                                if _refill_nw and not final_day:
                                    # One-for-one replacement does not expand
                                    # the serviced area. Do it at the cut tile,
                                    # not after a second trip back from the shed.
                                    crop = plan_crop_choice(vseeds, filler=True,
                                                            quad=q, pos=pos_b)
                                    _reserve = (distance(pos_b, shed_near(pos_b)) + 2
                                                if tile["crop"] == "MELON" else 0)
                                    if (crop is not None and
                                            w["busy"] + 2 + _reserve <= w["wbudget"]):
                                        w["plan"].append(("PLANT", pos_b, crop))
                                        w["plan"].append(("WATER", pos_b, None))
                                        w["busy"] += 2
                                        vseeds[crop] -= 1
                                if tile.get("crop") == "MELON":
                                    w["cargo"] += max(
                                        0, int(tile.get("yield_units", 1) or 1) - 1)
                                    maybe_drop(w)
                                elif not my_fert:
                                    maybe_drop(w)
                                if (not _refill_nw
                                        and tile["crop"] not in ("TOMATO", "STRAWBERRY")
                                        and not final_day
                                        and (zone_room > 0
                                             or (q == "SW" and tile["crop"] == "WHEAT"))):
                                    crop = plan_crop_choice(vseeds, filler=True,
                                                            quad=q, pos=pos_b)
                                    if crop is not None and w["busy"] + distance(w["pos"], pos_b) + 2 <= budget:
                                        w["plan"].append(("PLANT", pos_b, crop))
                                        w["plan"].append(("WATER", pos_b, None))
                                        w["busy"] += distance(w["pos"], pos_b) + 2
                                        w["pos"] = pos_b
                                        vseeds[crop] -= 1
                                        planned_standing[q] += 1
                                        zone_room -= 1'''
rep(a,b);p.write_text(s)
