"""Build hybrid v21: W4 SE-quad chassis + v11's decoded opening.

v11 solo census (seed 10011, $145,887) — the exact build order we port:
  d0: HIRE 5, COW 2 + SHEEP 2, WHEAT 7 seeds, MELON 12, BUY wheat 22 feed
  d4-12: strb +4/batch -> 33 tiles; cows -> 9 by d8; sheep -> 8 by d10
  wheat tiles: 7 -> 12 (d10) -> 24 (d12) -> 25-41 (d16+, top-ups 4-9/day)
  hands: 5,4,4,4,8,10,11,12... (12/day steady from d10)
  quads: NE ~d6, SW ~d11 (SE kept from W4: +$8.9k solo on our chassis)
  feed: steady BUY wheat 6-40/day (net wheat BUYER early — 108 by d10)

Goose chassis keeps: job-board tasking, price-aware selling, race mode,
endgame dump. This is THE hybrid: v11's economy, goose's adaptivity.
"""
import os

SRC = "topbots/v7v_W4_SE_quad.py"
OUT = "topbots/hybrid_v21.py"
src = open(SRC).read()


def rep(old, new, tag):
    global src
    assert src.count(old) == 1, f"[{tag}] anchor count = {src.count(old)}"
    src = src.replace(old, new, 1)
    print("ok:", tag)


# 1. wheat: flat 28-seed gate -> v11's day-scaled engine with small top-ups
rep('''    if seeds.get("WHEAT", 0) < 10 and money > 100:
        market.append(["BUY_SEED", "WHEAT", 28 - int(seeds.get("WHEAT", 0))])''',
    '''    # v11 wheat engine: 7 early (walk-light), 12 d8+, 24 d12+, 40 d16+;
    # small top-ups (never more than 9/day) keep cash for animals
    _wt = 7 if day < 8 else 12 if day < 12 else 24 if day < 16 else 40
    _wshort = _wt - wheat_tiles - int(seeds.get("WHEAT", 0))
    if _wshort > 0 and money > 100:
        market.append(["BUY_SEED", "WHEAT", min(9, _wshort)])''',
    "wheat engine")

# 2. cows: money 900/750 -> 420, open day 0 (v11: 2 cows on d0, 9 by d8)
rep('''    if (1 <= day <= 20 and n_cows < tgt_cows
            and money > (750 if race else 900)
            and (pastures_total > n_cows or cow_early)''',
    '''    if (0 <= day <= 20 and n_cows < tgt_cows
            and money > 420
            and (pastures_total > n_cows or cow_early or day <= 2)''',
    "cow ramp")

# 3. sheep: money -> 420, open day 0, drop the cows>=3 dependency
#    (v11: 2 sheep d0, 8 by d10; feed comes from BUY wheat, not wheat tiles)
rep('''    if (2 <= day <= 22 and n_sheep < TARGET_SHEEP
            and money > (850 if race else 800)
            and (pastures_empty or sheep_early) and hour <= 12
            and shed.get("SHEEP", 0) == 0
            and (sheep_early or (wheat_secure and n_cows >= 3))''',
    '''    if (0 <= day <= 22 and n_sheep < TARGET_SHEEP
            and money > 420
            and (pastures_empty or sheep_early) and hour <= 12
            and shed.get("SHEEP", 0) == 0
            and (sheep_early or wheat_secure or money > 700)''',
    "sheep ramp")

# 4. feed: emergency-only -> steady net-buyer (v11 buys 6-40 wheat/day)
rep('''    _feed_px = ((obs.get("market") or {}).get("prices") or {}).get("WHEAT", 25) or 25
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
                       min(2 * n_animals, (money - 500) // 40)])''',
    '''    _feed_px = ((obs.get("market") or {}).get("prices") or {}).get("WHEAT", 25) or 25
    # steady feed buying (v11 net wheat buyer: 108 by d10). 1 wheat/day keeps
    # a cow milking at $160/2d — buying at <2x that is always +EV.
    if (day <= 27 and n_animals > 0 and money > 300
            and shed.get("WHEAT", 0) + 2 * len(wheat_ripe) < n_animals + 6
            and _feed_px < 90):
        _q = min(2 * n_animals + 2 - shed.get("WHEAT", 0),
                 max(1, money // max(1, int(_feed_px) + 5)))
        if _q > 0:
            market.append(["BUY_PRODUCT", "WHEAT", _q])''',
    "steady feed")

compile(src, OUT, "exec")
open(OUT, "w").write(src)
print("built", OUT, len(src), "bytes")
