from pathlib import Path
p=Path('war/meta_v1.py');s=p.read_text()
def rep(a,b,label):
 global s
 assert s.count(a)==1,(label,s.count(a));s=s.replace(a,b,1)
# restore watering before cutting in both crop routes, uniquely match surrounding next block
for following,label in [('                        if pos_b in my_fert:', 'ne'),('                        if pos_b in my_fert:', 'nw')]:
 a='''                        if (not tile.get("watered_today") and not final_day
                                and not _cut_m):'''
 # identical pair is deliberately replaced by separate exact full region contexts below
 pass
for start,end,label in [('            if q == "NE":\n                # R68:', '            if q == "SW":\n                # R69:', 'ne'),('                stops.sort(key=lambda st_: (st_[0], st_[1]))','                    elif kind_b in ("WEED", "EMPTY"):', 'nw')]:
 i=s.index(start);j=s.index(end,i);region=s[i:j]
 a='''                        if (not tile.get("watered_today") and not final_day
                                and not _cut_m):'''
 assert region.count(a)==1
 region=region.replace(a,'''                        if not tile.get("watered_today") and not final_day:''',1)
 # don't water finite crop after harvest (unless replanted then already planned WATER)
 a='''                        if (not tile.get("watered_today") and not final_day
                                and not _sprayed):'''
 assert region.count(a)==1
 region=region.replace(a,'''                        if (not tile.get("watered_today") and not final_day
                                and not _sprayed and not (_did_h and _cut_m)):''',1)
 # after melon DROP return-to-tile planting had no travel cost or position update
 a='''w["busy"] + 2 <= budget'''
 assert region.count(a)==1
 region=region.replace(a,'''w["busy"] + distance(w["pos"], pos_b) + 2 <= budget''',1)
 a='''                                        w["busy"] += 2'''
 assert region.count(a)==1
 region=region.replace(a,'''                                        w["busy"] += distance(w["pos"], pos_b) + 2
                                        w["pos"] = pos_b''',1)
 s=s[:i]+region+s[j:]
p.write_text(s)
