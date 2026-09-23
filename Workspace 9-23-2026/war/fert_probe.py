#!/usr/bin/env python3
"""fert_probe.py -- are we fertilizer-LIMITED or fertilizer-BLIND?

Engine facts (intel/engine_kagg_1327.py):
  L481  tile["fertilized_until_day"] = max(..., day + 2)   -> lasts 3 days
  L799  fertilized = was_watered and fertilized_until_day >= day
  L800  yield_units = min(max_yield, yield_units + (2 if fertilized else 1))
  L796  production stops only once production_count > max_yield
  STRAWBERRY: max_yield 4, ongoing, interval 2, first_yield 10
        -> 4 production ticks; fert+water pays +2 instead of +1 each, so a
           fully fertilized strawberry is 8 units instead of 4.

So at strawberry $200-316 one unit of fertilizer is worth $200-632 on a
strawberry tile versus roughly $90 sold on the market. The question is
which constraint binds us:

  SUPPLY   - do we even collect enough fertilizer?
  CAP      - fert_targets is hard-capped at min(8, fert_total) per day
  DECISION - do we sell fertilizer while strawberry tiles go bare?

Counts every order the agent actually issues across a whole season.

Usage: python3 war/fert_probe.py [bot] [seed ...]
"""
import contextlib
import io
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from watch import env_name, resolve, ensure_env, orders_of  # noqa: E402


def run(path_a, path_b, seed):
    import kaggle_environments as ke
    env = ke.make(env_name(), configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])
    return env


def main():
    bot = sys.argv[1] if len(sys.argv) > 1 else "live20_18"
    seeds = [int(x) for x in sys.argv[2:]] or [42]
    ensure_env()
    path = resolve(bot)

    grand = Counter()
    n = 0
    for seed in seeds:
        env = run(path, "random", seed)
        ops = Counter()
        sold = Counter()
        bought = Counter()
        px_strb_end = 0.0
        px_fert_end = 0.0
        fert_shed_end = 0
        strb_tiles_end = 0
        for st in env.steps:
            for order in orders_of(st, 0):
                if not order:
                    continue
                kind = order[0]
                if kind == "FERTILIZE":
                    ops["FERTILIZE"] += 1
                elif kind == "COLLECT_FERTILIZER":
                    ops["COLLECT_FERTILIZER"] += 1
                elif kind == "SELL":
                    sold[order[1]] += int(order[2])
                elif kind == "BUY_PRODUCT":
                    bought[order[1]] += int(order[2])
            obs = (st[0] or {}).get("observation") or {}
            if "farms" not in obs:
                continue
            px = obs.get("market", {}).get("prices", {})
            px_strb_end = px.get("STRAWBERRY", px_strb_end)
            px_fert_end = px.get("FERTILIZER", px_fert_end)
            farm = obs["farms"][0]
            fert_shed_end = (obs.get("private", {}) or {}).get(
                "shed", {}).get("FERTILIZER", fert_shed_end)
            strb_tiles_end = sum(
                1 for row in farm.get("tiles", [])
                for t in row
                if isinstance(t, dict) and t.get("kind") == "PLANT"
                and t.get("crop") == "STRAWBERRY")
        n += 1
        for k, v in ops.items():
            grand[k] += v
        grand["SOLD_FERT"] += sold.get("FERTILIZER", 0)
        grand["BOUGHT_FERT"] += bought.get("FERTILIZER", 0)
        grand["STANDING_STRB_END"] += strb_tiles_end
        grand["SHED_FERT_END"] += fert_shed_end
        print("### seed %-4d collected=%-4d fertilized=%-4d "
              "SOLD fert=%-4d (strb $%.0f, fert $%.0f, %d strb standing)"
              % (seed, ops.get("COLLECT_FERTILIZER", 0),
                 ops.get("FERTILIZE", 0), sold.get("FERTILIZER", 0),
                 px_strb_end, px_fert_end, strb_tiles_end))

    print()
    print("=== %s over %d seeds (per-game averages) ===" % (bot, n))
    for k in ("COLLECT_FERTILIZER", "FERTILIZE", "SOLD_FERT",
              "BOUGHT_FERT", "SHED_FERT_END", "STANDING_STRB_END"):
        print("   %-22s %8.1f / game" % (k, grand[k] / max(1, n)))
    used = grand["FERTILIZE"]
    sold_f = grand["SOLD_FERT"]
    print()
    print("   fertilizer SPRAYED %d  vs  SOLD %d" % (used, sold_f))
    if used + sold_f:
        print("   -> %.0f%% of the fertilizer we monetized went to the "
              "market, not the field" % (100.0 * sold_f / (used + sold_f)))


if __name__ == "__main__":
    main()
