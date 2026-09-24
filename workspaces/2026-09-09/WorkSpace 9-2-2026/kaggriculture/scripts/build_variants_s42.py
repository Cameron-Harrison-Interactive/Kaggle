"""Session 42 variation matrix: patch variants on top of verified v7e.

Each variant = exact-text patches on topbots/goosebot_v7.py (v7e).
Solo ladder verdicts (seeds 10007-16 x2); winners go to H2H vs v11.
"""
import os

BASE = "topbots/goosebot_v7.py"   # v7e (verified $83,116/$66,802)


def rep(src, old, new, tag):
    assert old in src, f"[{tag}] anchor missing"
    assert src.count(old) == 1, f"[{tag}] anchor not unique"
    return src.replace(old, new, 1)


WHEAT_BUY_OLD = '''    if seeds.get("WHEAT", 0) < 10 and money > 100:
        market.append(["BUY_SEED", "WHEAT", 28 - int(seeds.get("WHEAT", 0))])'''
WHEAT_BUY_56 = '''    if seeds.get("WHEAT", 0) < 24 and money > 100:
        market.append(["BUY_SEED", "WHEAT", 56 - int(seeds.get("WHEAT", 0))])'''

STRB_CAP_OLD = '''        if (seeds.get("STRAWBERRY", 0) > 0 and 2 <= day <= 12
                and strb_tiles < 33 and wheat_tiles >= 6):
            return "STRAWBERRY"'''
STRB_CAP_20 = '''        if (seeds.get("STRAWBERRY", 0) > 0 and 2 <= day <= 12
                and strb_tiles < 20 and wheat_tiles >= 6):
            return "STRAWBERRY"'''

STRB_SEEDS_OLD = '''    if ((1 if race else 0) <= day <= 12 and money > (900 if race else 1000)
            and seeds.get("STRAWBERRY", 0) + strb_tiles < 33):'''
STRB_SEEDS_20 = '''    if ((1 if race else 0) <= day <= 12 and money > (900 if race else 1000)
            and seeds.get("STRAWBERRY", 0) + strb_tiles < 20):'''

VARIANTS = {}

# W1a: wheat engine scale-up (seeds 28 -> 56)
VARIANTS["W1a_wheat56"] = lambda s: rep(
    s, WHEAT_BUY_OLD, WHEAT_BUY_56, "W1a wheat seeds")

# W1b: wheat 56 + strb cap 33 -> 20 (CD-like allocation)
def _w1b(s):
    s = rep(s, WHEAT_BUY_OLD, WHEAT_BUY_56, "W1b wheat")
    s = rep(s, STRB_CAP_OLD, STRB_CAP_20, "W1b strb cap block")
    s = rep(s, STRB_SEEDS_OLD, STRB_SEEDS_20, "W1b strb seeds")
    return s
VARIANTS["W1b_wheat56_strb20"] = _w1b

# W2: strb FERTILIZE job value 120 -> 150 (session-41 lead, single lever)
VARIANTS["W2_strbfert150"] = lambda s: rep(
    s, 'jobs.append((x, y, "FERTILIZE", 120.0, None))',
    'jobs.append((x, y, "FERTILIZE", 150.0, None))', "W2 strb fert")

# W4: SE quadrant (4th quadrant, $4k) when rich mid-game
VARIANTS["W4_SE_quad"] = lambda s: rep(
    s, '''    elif unlocked == 2 and day <= 14 and money > 2800:
        market.append(["BUY_LAND"])''',
    '''    elif unlocked == 2 and day <= 14 and money > 2800:
        market.append(["BUY_LAND"])
    elif unlocked == 3 and day <= 22 and money > 4200:
        market.append(["BUY_LAND"])''', "W4 SE quadrant")

# W5: geese 8 (CD-style egg engine): spots + target + BUILD_COOP jobs
def _w5(s):
    s = rep(s, "COOP_SPOTS = ()",
            "COOP_SPOTS = ((2, 2), (3, 2), (2, 3), (7, 2), (6, 2), (7, 3), (2, 6), (2, 7))",
            "W5 coop spots")
    s = rep(s, "TARGET_GEESE = 0", "TARGET_GEESE = 8", "W5 target geese")
    s = rep(s, '''    # pasture builds
    if day >= 1 and pastures_total < TARGET_COWS + TARGET_SHEEP:''',
    '''    # coop + pasture builds
    if day >= 1 and coops_total < TARGET_GEESE:
        for c in COOP_SPOTS:
            if tiles[c[1]][c[0]] is None:
                jobs.append((c[0], c[1], "BUILD_COOP", 240.0, None))
    if day >= 1 and pastures_total < TARGET_COWS + TARGET_SHEEP:''',
            "W5 build coops")
    return s
VARIANTS["W5_geese8"] = _w5


if __name__ == "__main__":
    base = open(BASE).read()
    for name, fn in VARIANTS.items():
        out = f"topbots/v7v_{name}.py"
        src = fn(base)
        compile(src, out, "exec")
        open(out, "w").write(src)
        print(f"built {out}")
    print("variant count:", len(VARIANTS))
