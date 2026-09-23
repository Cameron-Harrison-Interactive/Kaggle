from pathlib import Path
p=Path('war/meta_v1.py');s=p.read_text()
def rep(a,b):
 global s
 assert s.count(a)==1,s.count(a);s=s.replace(a,b,1)
rep('''        # ---- 1. ANIMAL ZONE: installs first, then the line sweep ----''','''        # Majkel 109798422 d10: two extra hands cut the shed-side
        # melons and deliver by h9/h10, then resume field work.
        # Assign complete water/cut/delivery jobs, not a cargo override
        # that interrupts a waterer halfway through its route.
        melon_helpers = set()
        if day == 10 and hour <= 3:
            ripe = [p for p, t in plants if t.get("crop") == "MELON"
                    and harvestable(t)]
            for wi in quad_wr.get("SW", [])[-2:]:
                w = workers[wi]
                options = [p for p in ripe if p not in melon_helpers]
                if not options:
                    break
                p = min(options, key=lambda p: (
                    distance(w["pos"], p) + distance(p, shed_near(p)), p))
                t = tile_map[p]
                water = not t.get("watered_today")
                st = shed_near(p)
                cost = distance(w["pos"], p) + int(water) + 1 + distance(p, st) + 1
                if w["busy"] + cost > w["wbudget"]:
                    continue
                if water:
                    w["plan"].append(("WATER", p, None))
                w["plan"].append(("HARVEST", p, None))
                w["plan"].append(("DROP", st, None))
                w["busy"] += cost
                w["pos"] = st
                w["cargo"] = 0
                melon_helpers.add(p)

        # ---- 1. ANIMAL ZONE: installs first, then the line sweep ----''')
# remove helper crops from subsequent crop bands (generic includes NW)
rep('''            band_order = [p for p in serpentine(q)
                          if not animal_line(p)''','''            band_order = [p for p in serpentine(q)
                          if p not in melon_helpers
                          and (not animal_line(p)''')
rep('''                                       == "PLANT")))]''','''                                       == "PLANT"))))]''')
# skip animals' crop-side jobs, if present
rep('''                        d2 = distance(w["pos"], pos_r)
                        if pos_r in _row_fert:''','''                        if pos_r in melon_helpers:
                            continue
                        d2 = distance(w["pos"], pos_r)
                        if pos_r in _row_fert:''')
# northern ripe melons should precede non-dying berries as actually harvested h5-10.
rep('''                            stops.append((0 if (dying or tick or _m_dump) else 1,
                                          idx, pos_b, "PLANT"))''','''                            stops.append((-1 if _m_dump else 0 if (dying or tick) else 1,
                                          idx, pos_b, "PLANT"))''')
p.write_text(s)
