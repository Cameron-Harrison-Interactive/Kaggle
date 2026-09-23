from pathlib import Path
p=Path('war/meta_v1.py');s=p.read_text()
a='''    # Replay: idle SW hand plants the next wheat. No full-farm rebuild'''
b='''    # Majkel 109798422 d10-d12: refill the harvested northern
    # melons nearby. Lower-left NW remains a small wheat patch;
    # upper NW becomes berries. An idle northern worker should not
    # start an unreachable walk to the far SW corner instead.
    if 10 <= day <= 22 and hour > 0:
        _north_claimed = set()
        _north_seeds = Counter(seeds)
        for _wi, _pl in plans.items():
            for _op, _p, _crop in _pl[ptrs.get(_wi, 0):]:
                if _op == "PLANT":
                    _north_claimed.add(_p)
                    _north_seeds[_crop] -= 1
                elif _op == "INSTALL":
                    _north_claimed.add(_p)
        for _wi, _pos in enumerate(positions):
            _pl = plans.get(_wi) or []
            if ptrs.get(_wi, 0) < len(_pl):
                continue
            if quadrant(_pos) not in ("NW", "NE"):
                continue
            if any(inventories[_wi].get(_k, 0) > 0
                   for _k in ("MELON", "MILK", "WOOL", "EGG")):
                continue
            _options = []
            for _p in empty:
                if quadrant(_p) != "NW" or _p in SHED or _p in _north_claimed:
                    continue
                _cost = distance(_pos, _p) + 2
                if _cost > remaining:
                    continue
                _wheat_patch = _p in ((1, 2), (1, 3), (1, 4), (2, 3), (3, 3))
                _crop = ("WHEAT" if _wheat_patch else "STRAWBERRY")
                if _north_seeds[_crop] <= 0:
                    continue
                if _crop == "STRAWBERRY" and counts["STRAWBERRY"] >= STRB_TARGET:
                    continue
                _options.append((_cost, _p, _crop))
            if _options:
                _, _p, _crop = min(_options)
                plans[_wi] = [("PLANT", _p, _crop), ("WATER", _p, None)]
                ptrs[_wi] = 0
                _north_claimed.add(_p)
                _north_seeds[_crop] -= 1

    # Replay: idle SW hand plants the next wheat. No full-farm rebuild'''
assert s.count(a)==1;s=s.replace(a,b,1);p.write_text(s)
