"""shopopt.py — offline optimizer for the town-shop sequence (forced-shop H2H).

Coordinate descent over the 8 shop-draw slots. Objective: H2H margin
(our money - their money), GameSim seed 1 (forced runs are seed-independent:
tapes are deterministic and weed-immune; the discarded rng.choice is the only
seed influence). Every evaluated sequence is cached with (ours, theirs) so any
re-weighted objective (ours - lam*theirs) can be re-ranked offline for free.

Usage:
  python _ref/shopopt.py free8            # all 8 slots free, start from ANTI
  python _ref/shopopt.py free8 natural    # ... start from natural seed-1 shops
  python _ref/shopopt.py frozen2          # slots 0,1 frozen to natural, opt 2..7
  python _ref/shopopt.py rank             # re-rank cache by several objectives
"""
import sys, os, json, time
import multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

SHOPS = ["BAKERY", "PIZZA_SHOP", "BRUNCH_SPOT", "YARN_STORE", "ICE_CREAM_SHOP",
         "PET_CAFE", "SMOOTHIE_SHOP", "FARMERS_MARKET"]
OURS = os.path.join(ROOT, "topbots", "v6h2.py")
OPP = os.path.join(ROOT, "topbots", "v1112fr.py")
NATURAL_S1 = ["SMOOTHIE_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET", "PET_CAFE",
              "SMOOTHIE_SHOP", "SMOOTHIE_SHOP", "YARN_STORE", "BRUNCH_SPOT"]
ANTI = ["YARN_STORE"] * 4 + ["SMOOTHIE_SHOP"] * 4

CACHE = os.path.join(HERE, "shopopt_cache.json")


def load_cache():
    return json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def save_cache(c):
    json.dump(c, open(CACHE, "w"), indent=0)


_W = {}


def _winit():
    import h2h_forced as H
    _W["run"] = H.run_h2h


def _weval(seq):
    out = _W["run"](OURS, OPP, 1, force=seq)
    return (",".join(seq), out["a"], out["b"])


def evaluate(seqs, cache, pool, verbose=True):
    """Evaluate list of sequences (tuples), using/updating cache. Returns dict key->(a,b)."""
    tasks, seen = [], set()
    for s in seqs:
        k = ",".join(s)
        if k not in cache and k not in seen:
            seen.add(k)
            tasks.append(list(s))
    if tasks:
        for k, a, b in pool.imap_unordered(_weval, tasks):
            cache[k] = [a, b]
        save_cache(cache)
    if verbose and tasks:
        print("  evaluated %d new seqs (cache %d)" % (len(tasks), len(cache)), flush=True)
    return {",".join(s): tuple(cache[",".join(s)]) for s in seqs}


def margin(kv):
    return kv[0] - kv[1]


def descend(start, free_slots, cache, pool, max_passes=4):
    base = list(start)
    basekey = ",".join(base)
    evaluate([base], cache, pool)
    print("start %s -> ours %,.0f theirs %,.0f margin %,.0f".replace(",", "") %
          (basekey, cache[basekey][0], cache[basekey][1], margin(cache[basekey])), flush=True)
    for p in range(max_passes):
        changed = False
        for slot in free_slots:
            cands = [base[:slot] + [s] + base[slot + 1:] for s in SHOPS]
            res = evaluate(cands, cache, pool)
            bestk = max(res, key=lambda k: margin(res[k]))
            if bestk != ",".join(base):
                base = bestk.split(",")
                changed = True
            bk = ",".join(base)
            print("pass%d slot%d best %s ours %,.0f theirs %,.0f margin %,.0f"
                  .replace(",", "") % (p, slot, bk, cache[bk][0], cache[bk][1],
                                       margin(cache[bk])), flush=True)
        if not changed:
            print("converged after pass %d" % p, flush=True)
            break
    return base


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "free8"
    cache = load_cache()
    with mp.Pool(2, initializer=_winit) as pool:
        # extra probes: all-one-type sets (saturation info), natural, anti
        probes = [tuple([s] * 8) for s in SHOPS] + [tuple(ANTI), tuple(NATURAL_S1)]
        evaluate([list(p) for p in probes], cache, pool)

        if mode == "free8":
            start = ANTI if len(sys.argv) < 3 else (NATURAL_S1 if sys.argv[2] == "natural" else sys.argv[2].split(","))
            best = descend(start, range(8), cache, pool)
        elif mode == "frozen2":
            best = descend(NATURAL_S1, range(2, 8), cache, pool)
        elif mode == "rank":
            best = None
        else:
            raise SystemExit("unknown mode " + mode)

    if best:
        bk = ",".join(best)
        a, b = cache[bk]
        print("\nBEST %s\nours %,.0f theirs %,.0f margin %,.0f".replace(",", "") %
              (bk, a, b, a - b), flush=True)

    # rank report over the whole cache under several objectives
    print("\n=== cache ranking (top 12 by margin; ours/theirs in k) ===", flush=True)
    rows = sorted(cache.items(), key=lambda kv: -(kv[1][0] - kv[1][1]))
    for k, (a, b) in rows[:12]:
        print("margin %+8.1fk  ours %7.1fk  theirs %7.1fk  %s" %
              ((a - b) / 1000, a / 1000, b / 1000, k), flush=True)
    print("\n=== top 6 by OUR OWN income ===", flush=True)
    for k, (a, b) in sorted(cache.items(), key=lambda kv: -kv[1][0])[:6]:
        print("ours %7.1fk  theirs %7.1fk  margin %+8.1fk  %s" %
              (a / 1000, b / 1000, (a - b) / 1000, k), flush=True)
    print("\n=== top 6 by ours - 0.5*theirs ===", flush=True)
    for k, (a, b) in sorted(cache.items(), key=lambda kv: -(kv[1][0] - 0.5 * kv[1][1]))[:6]:
        print("obj %7.1fk  ours %7.1fk  theirs %7.1fk  %s" %
              ((a - 0.5 * b) / 1000, a / 1000, b / 1000, k), flush=True)


if __name__ == "__main__":
    main()
