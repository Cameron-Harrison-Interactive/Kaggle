#!/usr/bin/env python3
"""build_v28full_agent.py — inject compiled v28-full tapes into the v25 source.

Usage: python3 scripts/build_v28full_agent.py data/v28full/tapes/{name}_seat0.json \
                                        data/v28full/tapes/{name}_seat1.json \
                                        HI_AgriBot_v28_WheatMachine

Replaces the OPERATIVE tail literal (_SEAT0_ACTIONS = json.loads('[..]') and the
_SEAT1_ACTIONS = _SEAT0_ACTIONS override) with fresh b85 blocks for both seats.
Keeps every runtime layer of v25 (nocow, labor, cashrank, terminal sweep).
"""
import base64
import json
import re
import sys
import zlib

V25_SRC = "/home/user/kaggriculture/agent/main_v25_wheat16.py"
OUT = "/home/user/kaggriculture/agent/main_v28_wheatmachine.py"


def b85_block(tape):
    b85 = base64.b85encode(zlib.compress(json.dumps(tape).encode())).decode()
    lines = "\n".join(f"    '{b85[i:i+100]}'"
                      for i in range(0, len(b85), 100))
    return (
        "_SEAT{n}_ACTIONS = json.loads(zlib.decompress(base64.b85decode(\n"
        f"(\n{lines}\n))).decode(\"utf-8\"))\n"
    )


def main():
    s0_path, s1_path, version = sys.argv[1], sys.argv[2], sys.argv[3]
    t0 = json.load(open(s0_path))
    t1 = json.load(open(s1_path))
    assert len(t0) == 719 and len(t1) == 719, (len(t0), len(t1))
    src = open(V25_SRC).read()

    # locate the operative tail literal (last occurrence)
    idx = src.rfind("_SEAT0_ACTIONS = json.loads('[")
    if idx < 0:
        raise SystemExit("tail literal not found")
    # find the _SEAT1_ACTIONS = _SEAT0_ACTIONS override after it
    i1 = src.find("_SEAT1_ACTIONS = _SEAT0_ACTIONS", idx)
    if i1 < 0:
        raise SystemExit("seat1 override not found")
    end = src.find("\n", i1)
    block = b85_block(t0).replace("_SEAT{n}", "_SEAT0") + b85_block(t1).replace("_SEAT{n}", "_SEAT1")
    src = src[:idx] + block + src[end + 1:]

    old_v = re.search(r'VERSION = "[^"]+"', src)
    src = src.replace(old_v.group(0), f'VERSION = "{version}"')

    src = src.replace("HI_AgriBot_v25_Wheat16", version)
    src = src.replace("_v25_agent = agent", "_v28full_agent = agent")

    open(OUT, "w").write(src)
    import ast
    ast.parse(src)
    print(f"wrote {OUT} ({len(src)} chars, VERSION={version})")


if __name__ == "__main__":
    main()
