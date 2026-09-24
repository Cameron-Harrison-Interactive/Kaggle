"""v12 'aswinner' — v11 + mirror-symmetry breaker (market-only wrapper).

WHY: v11 vs v11 = 10 exact ties / 10 (deterministic, seat-symmetric).
Ties are half-wins in Bradley-Terry, so vs the mirror-heavy live pool v11's
rating is suppressed. Any reproducible asymmetry in SELL TIMING converts
mirror ties into wins.

Mechanism (sells-only post-processing; v11's labor + buys untouched):
  hold selected items for H hours between sells (skip their SELL orders
  on off-hours) so our dumps land after the opponent's dump + town drain
  (price recovery), and never during the endgame (step >= 714: liquidate).

Grid-test: HOLD_ITEMS x HOLD_H -> H2H vs raw v11, count outright wins.
"""
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_V11 = os.path.join(_HERE, "..", "topbots", "tetsu_r5_v11_adapeak2.py")


def _load_v11():
    spec = importlib.util.spec_from_file_location("_v11_mod", _V11)
    m = importlib.util.module_from_spec(spec)
    sys.modules["_v11_mod"] = m
    spec.loader.exec_module(m)
    return m.agent


def make_v12(hold_items, hold_hours):
    v11_agent = _load_v11()
    last_sell = {}

    def agent(obs, config=None):
        act = v11_agent(obs, config)
        try:
            step = obs["step"] if isinstance(obs, dict) else obs.step
            if step < 690:  # endgame: never hold
                market = act.get("market") or []
                out = []
                for o in market:
                    if (isinstance(o, list) and len(o) >= 3 and o[0] == "SELL"
                            and o[1] in hold_items):
                        key = (o[1],)
                        gap = step - last_sell.get(key, -99)
                        if gap >= hold_hours:
                            last_sell[key] = step
                            out.append(o)
                        # else: hold this line this hour
                    else:
                        out.append(o)
                act["market"] = out[:10]
        except Exception:
            pass
        return act
    return agent


if __name__ == "__main__":
    import itertools
    os.chdir(open("/tmp/ws").read().strip())
    sys.path.insert(0, "scripts")
    from kaggle_environments import make

    def load(path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.agent

    V11 = load("topbots/tetsu_r5_v11_adapeak2.py", "v11ref")
    GRIDS = [
        ({"WHEAT"}, 2), ({"WHEAT"}, 4),
        ({"MILK"}, 2), ({"MILK"}, 4),
        ({"WOOL"}, 2), ({"WOOL"}, 4),
        ({"WHEAT", "MILK", "WOOL"}, 2),
        ({"WHEAT", "MILK", "WOOL"}, 4),
        ({"STRAWBERRY"}, 2),
        ({"FERTILIZER"}, 2),
    ]
    for items, hrs in GRIDS:
        A = make_v12(frozenset(items), hrs)
        w = l = t = 0
        sa = sb = 0
        for seed in range(10007, 10012):
            for seat in (0, 1):
                env = make("kagg" + "riculture",
                           configuration={"episodeSteps": 720, "seed": seed})
                pair = [A, V11] if seat == 0 else [V11, A]
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
        tag = "+".join(sorted(i[:4] for i in items))
        print(f"v12[{tag} hold{hrs}] vs v11: {w}-{l}-{t}   ${sa/10:,.0f} vs ${sb/10:,.0f}", flush=True)
