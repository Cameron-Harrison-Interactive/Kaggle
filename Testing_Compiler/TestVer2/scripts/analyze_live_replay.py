#!/usr/bin/env python3
"""Analyze a kaggriculture replay: who won, build summary, market crashes,
crop/animal counts, and per-day money curve for both players."""
import json
import sys


def summarize(path):
    with open(path) as f:
        data = json.load(f)
    info = data.get("info", {}) or {}
    steps = data.get("steps") or []
    print(f"\n=== {path} ===")
    print(f"seed={info.get('seed')} episodeSteps={info.get('episodeSteps')} players={len(info.get('agents', []))}")
    for i, a in enumerate(info.get("agents", [])):
        print(f"  player{i}: {a.get('name', '?')}")

    # Final rewards/status
    final = steps[-1]
    for i, s in enumerate(final):
        print(f"  final p{i}: reward={s.get('reward')} status={s.get('status')}")

    # Track per-day money + build for both players
    p0 = {"money": [], "crops": [], "weeds": [], "animals": [], "straw": [], "melon": [],
          "wheat": [], "carrot": [], "tomato": [], "hands": [], "quads": []}
    p1 = {"money": [], "crops": [], "weeds": [], "animals": [], "straw": [], "melon": [],
          "wheat": [], "carrot": [], "tomato": [], "hands": [], "quads": []}
    straw_px = []
    melon_px = []
    for step in steps:
        obs = step[0].get("observation", {}) or {}
        for i, pdata in enumerate((p0, p1)):
            farm = (obs.get("farms") or [{}] * 2)[i] or {}
            pdata["money"].append(farm.get("money") or 0)
            tiles = farm.get("tiles") or []
            crops = weeds = straw = melon = wheat = carrot = tomato = animals = 0
            for row in tiles:
                for t in row:
                    if isinstance(t, dict):
                        if t.get("animal"):
                            animals += 1
                        k = t.get("kind")
                        if k == "PLANT":
                            crops += 1
                            c = t.get("crop")
                            if c == "STRAWBERRY": straw += 1
                            elif c == "MELON": melon += 1
                            elif c == "WHEAT": wheat += 1
                            elif c == "CARROT": carrot += 1
                            elif c == "TOMATO": tomato += 1
                        elif k == "WEED":
                            weeds += 1
            pdata["crops"].append(crops); pdata["weeds"].append(weeds)
            pdata["straw"].append(straw); pdata["melon"].append(melon)
            pdata["wheat"].append(wheat); pdata["carrot"].append(carrot)
            pdata["tomato"].append(tomato); pdata["animals"].append(animals)
            pdata["hands"].append(len(farm.get("hands") or []))
            pdata["quads"].append(len(farm.get("unlocked_quadrants") or []))
        mkt = obs.get("market") or {}
        px = mkt.get("prices") or {}
        straw_px.append(px.get("STRAWBERRY"))
        melon_px.append(px.get("MELON"))

    def day_line(p, d):
        i = d * 24
        if i >= len(p["money"]):
            return ""
        return (f"  d{d:2d} p${p['money'][i]:>8,.0f} crops={p['crops'][i]:>2} "
                f"(straw{p['straw'][i]:>2} melon{p['melon'][i]:>2} wheat{p['wheat'][i]:>2} "
                f"carrot{p['carrot'][i]:>2} tom{p['tomato'][i]:>2}) weeds={p['weeds'][i]:>2} "
                f"anim={p['animals'][i]:>2} hands={p['hands'][i]:>2} quads={p['quads'][i]}")

    print("\n  day-by-day (us=p0 unless noted):")
    for d in (0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 29):
        print(f"  P0 d{d}: {day_line(p0, d) if False else ''}".rstrip())
        l0 = day_line(p0, d)
        l1 = day_line(p1, d)
        print(f"    p0{d:>2}: {l0}")
        print(f"    p1{d:>2}: {l1}")

    print(f"\n  straw price d5={straw_px[120]} d10={straw_px[240]} d15={straw_px[360]} "
          f"d20={straw_px[480]} d25={straw_px[600]} d29={straw_px[696]}")
    print(f"  melon price d10={melon_px[240]} d15={melon_px[360]} d20={melon_px[480]} "
          f"d25={melon_px[600]} d29={melon_px[696]}")
    return data


if __name__ == "__main__":
    for path in sys.argv[1:]:
        summarize(path)
