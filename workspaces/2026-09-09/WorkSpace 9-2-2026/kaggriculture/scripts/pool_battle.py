"""Pool battle harness: fight our candidates vs REAL top-LB opponents.

Opponents: k2900 public kernel bot + tape bots rebuilt from top-16 episodes.
Usage: python3 scripts/pool_battle.py CAND_PATH CAND_NAME [more ...]
"""
import importlib.util
import json
import os
import sys
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.chdir(open("/tmp/ws").read().strip())
from kaggle_environments import make  # noqa: E402
from tape_replayer import TapeReplayer  # noqa: E402

POOL = json.load(open(os.path.join(os.path.dirname(__file__), "pool_refs.json")))

_cache = {}


def load_file(path, name):
    key = ("f", path)
    if key not in _cache:
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _cache[key] = m.agent
    return _cache[key]


def load_tape(path, name):
    key = ("t", path)
    if key not in _cache:
        tape = json.load(open(path))["tape"]
        tr = TapeReplayer(tape)

        def agent(obs, config=None):  # plain closure (bound methods break kaggle runner)
            return tr.agent(obs)
        _cache[key] = agent
    return _cache[key]


def get_bot(kind, ref, name):
    return load_file(ref, name) if kind == "file" else load_tape(ref, name)


def h2h(a, b, seeds=range(10007, 10012)):
    w = l = t = 0
    sa = sb = 0
    for seed in seeds:
        for seat in (0, 1):
            env = make("kagg" + "riculture",
                       configuration={"episodeSteps": 720, "seed": seed})
            pair = [a, b] if seat == 0 else [b, a]
            env.run(pair)
            ra = env.steps[-1][seat]["reward"] or 0
            rb = env.steps[-1][1 - seat]["reward"] or 0
            sa += ra
            sb += rb
            if ra > rb:
                w += 1
            elif rb > ra:
                l += 1
            else:
                t += 1
    return w, l, t, sa, sb


if __name__ == "__main__":
    args = sys.argv[1:]
    cands = [(args[i], args[i + 1]) for i in range(0, len(args) - 1, 2)]
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    for path, name in cands:
        A = load_file(path, name)
        print(f"=== {name} vs the pool ===", flush=True)
        for pname, (kind, ref) in POOL.items():
            if only and pname not in only:
                continue
            B = get_bot(kind, ref, pname)
            w, l, t, sa, sb = h2h(A, B)
            print(f"  {name:10s} vs {pname:12s}: {w}-{l}-{t}   avg ${sa/10:,.0f} vs ${sb/10:,.0f}", flush=True)
