#!/usr/bin/env python3
"""Build crop-variant tapes: swap early WHEAT plants for CARROT (same tiles,
route unchanged) and adjust the seed buy. Legal per ROUTING_BIBLE: change
PLANT X -> PLANT Y on the same worker/tile.

Approach: run v18 with a runtime crop patch vs PASS, record the tape. The
patch converts the FIRST N wheat PLANT actions (days 0-1) into CARROT and
changes the seed purchase (WHEAT 5 -> WHEAT 2 + CARROT 3).

Usage: python3 scripts/record_crop_variant.py --crop CARROT --count 3 --seeds 1-5
"""
import argparse
import importlib.util
import json
import os
import sys
import time

from kaggle_environments import make

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "data", "tapes_variants")
os.makedirs(OUT_DIR, exist_ok=True)

SWAP = {
    "CARROT": ("WHEAT", "CARROT"),
}


def load_v18(path):
    spec = importlib.util.spec_from_file_location("v18", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._weed_repair_action = lambda obs, action, actions, step: action
    return mod


def make_pass():
    def agent(obs, configuration=None):
        farm = obs["farms"][obs["player"]]
        return {"market": [], "farmer": ["PASS"],
                "hands": [["PASS"]] * len(farm.get("hands") or [])}
    return agent


def record(mod, seed, seat, crop, count):
    """Record tape for seat with the first `count` WHEAT plants swapped to crop."""
    from_crop, to_crop = SWAP[crop]
    pass_agent = make_pass()
    tape = []
    swapped = [0]

    def rec(obs, config):
        act = mod.agent(obs, config)
        # Market: change the BUY_SEED from_crop order (early only) into
        # fewer from_crop + count to_crop
        market = [list(o) for o in (act.get("market") or [])]
        day = int(obs.get("day", 0) or 0)
        if day <= 1:
            new_market = []
            seen_wheat = False
            for o in market:
                if o and o[0] == "BUY_SEED" and o[1] == from_crop and not seen_wheat and count > 0:
                    # reduce wheat buy, add crop seeds
                    qty = max(0, int(o[2]) - count)
                    if qty > 0:
                        new_market.append(["BUY_SEED", from_crop, qty])
                    new_market.append(["BUY_SEED", to_crop, count])
                    seen_wheat = True
                else:
                    new_market.append(o)
            market = new_market[:10]
        # Labor: swap the first `count` PLANT from_crop (early only) to to_crop
        if day <= 3 and swapped[0] < count:
            for key in ("farmer", "hands"):
                acts = act.get(key)
                if isinstance(acts, list):
                    for i, a in enumerate(acts):
                        if (isinstance(a, list) and len(a) >= 2
                                and a[0] == "PLANT" and a[1] == from_crop
                                and swapped[0] < count):
                            acts[i] = ["PLANT", to_crop]
                            swapped[0] += 1
        tape.append({"market": market,
                     "farmer": list(act.get("farmer") or ["PASS"]),
                     "hands": [list(h) for h in (act.get("hands") or [])]})
        return act

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()
    if seat == 0:
        env.run([rec, pass_agent])
        r = env.steps[-1][0].reward or 0
    else:
        env.run([pass_agent, rec])
        r = env.steps[-1][1].reward or 0
    return tape, r, swapped[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crop", default="CARROT")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--seeds", default="1,2,3,4,5")
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]
    mod = load_v18(os.path.join(ROOT, "submit", "main.py"))
    for seed in seeds:
        for seat in (0, 1):
            tape, r, n = record(mod, seed, seat, args.crop, args.count)
            out = os.path.join(OUT_DIR, f"{args.crop}{args.count}_seat{seat}_s{seed}.json")
            with open(out, "w") as f:
                json.dump(tape, f)
            print(f"{args.crop}{args.count} seat{seat} s{seed}: {len(tape)} steps, "
                  f"${r:,.0f}, swaps={n}", flush=True)


if __name__ == "__main__":
    main()
