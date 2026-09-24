"""Apply v7 race-mode market/economy edits to a freshly spliced goosebot_v7.py.

Build flow: goosebot_v6.py head + v7_tasking_block.py + tail -> goosebot_v7.py
then run THIS script. All edits are race-gated (H2H opponent detected) so the
solo benchmark stays byte-identical. Exact-text asserts: fails loudly if the
upstream v6 head text changed.
"""
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "topbots/goosebot_v7.py"
src = open(PATH).read()

RACE_DETECT = '''    # ---------- market layer ----------
    # race detection (H2H: opponent is an active bot, not a pass_agent) --
    # gates H2H-only economy behavior; inert in solo play.
    race = False
    try:
        _fs = obs.get("farms") or []
        if len(_fs) > 1:
            _opp = _fs[1 - int(obs.get("player") or 0)]
            if _opp is not None:
                if ((len(_opp.get("hands") or []) > 0)
                        or (_opp.get("money") or 0) > 4200):
                    race = True
                else:
                    _np = 0
                    for _row in (_opp.get("tiles") or []):
                        for _t in _row:
                            if isinstance(_t, dict) and (
                                    _t.get("kind") == "PLANT"
                                    or _t.get("animal")):
                                _np += 1
                                if _np >= 2:
                                    break
                        if _np >= 2:
                            break
                    race = _np >= 2
    except Exception:
        race = False

    market = []
'''


def rep(old, new, tag):
    global src
    assert old in src, f"PATCH FAIL [{tag}]: anchor text not found"
    assert src.count(old) == 1, f"PATCH FAIL [{tag}]: anchor not unique"
    src = src.replace(old, new, 1)
    print(f"  ok: {tag}")


# E1: race detection at top of market layer
rep('    # ---------- market layer ----------\n    market = []\n',
    RACE_DETECT, "E1 race detect")

# E2: hands targets in race
rep('''    else:
        target_hands = 12
''',
    '''    else:
        target_hands = 12
    if race:
        # H2H: hands are the service bottleneck (weeds, feed, muling)
        target_hands = 12 if (day >= 6 or money > 2500) else (8 if day >= 3 else 5)
''', "E2 hands")

# E3: animal buys -- early race budget + feed security + spend reserve
rep('''    if (1 <= day <= 20 and n_cows < TARGET_COWS and money > 900
            and pastures_total > n_cows and hour <= 12
            and shed.get("COW", 0) == 0):
        market.append(["BUY_ANIMAL", "COW", 1])
    if (2 <= day <= 22 and n_sheep < TARGET_SHEEP and money > 800
            and pastures_empty and hour <= 12 and shed.get("SHEEP", 0) == 0
            and wheat_secure and n_cows >= 3):
        market.append(["BUY_ANIMAL", "SHEEP", 1])
''',
    '''    tgt_cows = 6 if race else TARGET_COWS
    cow_early = race and day <= 6 and n_cows < 4
    sheep_early = race and day <= 8 and n_sheep < 4
    feed_ok = (wheat_tiles >= n_animals + 2
               or shed.get("WHEAT", 0) >= 2 * n_animals + 2)
    if (1 <= day <= 20 and n_cows < tgt_cows
            and money > (750 if race else 900)
            and (pastures_total > n_cows or cow_early)
            and hour <= 12
            and shed.get("COW", 0) == 0
            and (not race or feed_ok)):
        market.append(["BUY_ANIMAL", "COW", 1])
    if (2 <= day <= 22 and n_sheep < TARGET_SHEEP
            and money > (850 if race else 800)
            and (pastures_empty or sheep_early) and hour <= 12
            and shed.get("SHEEP", 0) == 0
            and (sheep_early or (wheat_secure and n_cows >= 3))
            and (not race or feed_ok)):
        market.append(["BUY_ANIMAL", "SHEEP", 1])
''', "E3 animals")

# E4: strb seeds -- race skips the d0 $800 buy (money goes to animals instead;
# strb seeds resume d1+ funded by wheat/melon income, v11 cadence)
rep('''    if (day <= 12 and money > 1000
            and seeds.get("STRAWBERRY", 0) + strb_tiles < 33):
''',
    '''    if ((1 if race else 0) <= day <= 12 and money > (900 if race else 1000)
            and seeds.get("STRAWBERRY", 0) + strb_tiles < 33):
''', "E4 strb seeds")

# E5: proactive feed buying in race (wheat <$80 -> wool/milk ROI is huge)
rep('''    if (day <= 27 and n_animals > 0 and money > 400
            and shed.get("WHEAT", 0) < n_animals
            and len(wheat_ripe) < max(1, n_animals - shed.get("WHEAT", 0))):
        market.append(["BUY_PRODUCT", "WHEAT", min(2 * n_animals,
                                                   money // 40)])
    elif (day <= 27 and n_animals > 0 and money > 800
            and shed.get("WHEAT", 0) < n_animals):
        market.append(["BUY_PRODUCT", "WHEAT",
                       min(2 * n_animals, (money - 500) // 40)])
''',
    '''    _feed_px = ((obs.get("market") or {}).get("prices") or {}).get("WHEAT", 25) or 25
    if (race and day <= 27 and n_animals > 0 and money > 300
            and shed.get("WHEAT", 0) < n_animals + 1
            and len(wheat_ripe) < 3 and _feed_px < 80):
        market.append(["BUY_PRODUCT", "WHEAT",
                       min(2 * n_animals + 2 - shed.get("WHEAT", 0),
                           max(1, money // max(1, int(_feed_px) + 5)))])
    elif (day <= 27 and n_animals > 0 and money > 400
            and shed.get("WHEAT", 0) < n_animals
            and len(wheat_ripe) < max(1, n_animals - shed.get("WHEAT", 0))):
        market.append(["BUY_PRODUCT", "WHEAT", min(2 * n_animals,
                                                   money // 40)])
    elif (day <= 27 and n_animals > 0 and money > 800
            and shed.get("WHEAT", 0) < n_animals):
        market.append(["BUY_PRODUCT", "WHEAT",
                       min(2 * n_animals, (money - 500) // 40)])
''', "E5 feed buys")

# E6: race liquidation -- sell everything above keep, dearest first
rep('''        for item, keep in (("WHEAT", wheat_keep), ("CARROT", 0), ("EGG", 0),
                           ("MILK", 0), ("WOOL", 0), ("TOMATO", 0),
                           ("STRAWBERRY", 0), ("MELON", 0)):
            have = shed.get(item, 0)
            if have <= keep:
                continue
            surplus = have - keep
            p = prices.get(item, BASE[item])
            base = BASE[item]
            if day >= 29:
                q = surplus                  # endgame dump
            elif p >= base * 1.04:
''',
    '''        for item, keep in (("WHEAT", wheat_keep), ("CARROT", 0), ("EGG", 0),
                           ("MILK", 0), ("WOOL", 0), ("TOMATO", 0),
                           ("STRAWBERRY", 0), ("MELON", 0)) if not race else (
                tuple(sorted((("WHEAT", wheat_keep), ("CARROT", 0), ("EGG", 0),
                              ("MILK", 0), ("WOOL", 0), ("TOMATO", 0),
                              ("STRAWBERRY", 0), ("MELON", 0)),
                             key=lambda ik: -(prices.get(ik[0], 0) or 0)))):
            have = shed.get(item, 0)
            if have <= keep:
                continue
            surplus = have - keep
            p = prices.get(item, BASE[item])
            base = BASE[item]
            if day >= 29:
                q = surplus                  # endgame dump
            elif race:
                q = surplus                  # H2H race: liquidate; holding
                                             # loses to price decay + shed
                                             # cap-100 discards
            elif p >= base * 1.04:
''', "E6 race sells")

# E7: order priority under the 10-order cap (animals/feed/hires first)
rep('''    return {"farmer": acts[0], "hands": acts[1:], "market": market[:10]}
''',
    '''    if race:
        # 10-order cap: animals/feed/hires must not be starved by sell spam
        _pri = {"BUY_ANIMAL": 0, "BUY_PRODUCT": 1, "HIRE": 2, "BUY_SEED": 3,
                "BUY_LAND": 4}
        market.sort(key=lambda o: _pri.get(
            o[0] if isinstance(o, list) and o else "", 5))
    return {"farmer": acts[0], "hands": acts[1:], "market": market[:10]}
''', "E7 order priority")

open(PATH, "w").write(src)
print(f"patched {PATH}: {len(src)} bytes")
