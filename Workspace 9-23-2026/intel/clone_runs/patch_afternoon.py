from pathlib import Path
p=Path('war/meta_v1.py');s=p.read_text()
a='''    free_shed = Counter(shed)
    free_seeds = Counter(seeds)
    actions = [["PASS"] for _ in positions]

    for i in range(len(positions)):'''
b='''    free_shed = Counter(shed)
    free_seeds = Counter(seeds)
    actions = [["PASS"] for _ in positions]

    # Replay 109798422: after the animal run, the collector takes
    # its own fertilizer to northern berries in the afternoon. Do not
    # steal a waterer's turn or a shed pickup from another hand.
    _spray_claimed = set()
    _water_booked = set()
    for _i, _pl in plans.items():
        for _op, _p, _arg in _pl[ptrs.get(_i, 0):]:
            if _op == "FERTILIZE":
                _spray_claimed.add(_p)
            elif _op == "WATER":
                _water_booked.add(_p)
    _afternoon_sprays = (11 <= day <= 22 and hour >= 10
                         and quoted("STRAWBERRY") > quoted("FERTILIZER"))

    for i in range(len(positions)):'''
assert s.count(a)==1;s=s.replace(a,b,1)
a='''        act = None

        while act is None and ptr < len(plan_i):'''
b='''        act = None

        if (_afternoon_sprays and int(inv.get("FERTILIZER", 0)) > 0
                and (ptr >= len(plan_i) or plan_i[ptr][0] == "DROP")):
            _todo = []
            for _p, _t in plants:
                _age = day - int(_t.get("planted_day", day))
                if (_t.get("crop") != "STRAWBERRY"
                        or quadrant(_p) not in ("NW", "NE")
                        or not 7 <= _age <= 15
                        or int(_t.get("fertilized_until_day", -1)) >= day
                        or _p in _spray_claimed):
                    continue
                _water = not _t.get("watered_today") and _p not in _water_booked
                _cost = distance(pos, _p) + 1 + int(_water)
                if _cost <= remaining:
                    _tick = _age >= 9 and (_age - 9) % 2 == 0
                    _todo.append((not _tick, _cost, _p, _water))
            if _todo:
                _goods = [(k, q) for k, q in inv.items()
                          if k in MARKET and k not in ("WHEAT", "FERTILIZER")
                          and q > 0]
                if _goods and pos in SHED:
                    # Place the sale item, retaining the fertilizer
                    # collected from the animals for the next walk.
                    _k, _n = max(_goods, key=lambda kv: kv[1] * quoted(kv[0]))
                    actions[i] = ["PLACE", _k, _n]
                    ptrs[i] = ptr
                    continue
                if not _goods:
                    _, _, _p, _water = min(_todo)
                    _jobs = ([("WATER", _p, None)] if _water else [])
                    _jobs.append(("FERTILIZE", _p, None))
                    plans[i] = _jobs + plan_i[ptr:]
                    plan_i = plans[i]
                    ptr = 0
                    _spray_claimed.add(_p)
                    if _water:
                        _water_booked.add(_p)

        while act is None and ptr < len(plan_i):'''
assert s.count(a)==1;s=s.replace(a,b,1)
p.write_text(s)
