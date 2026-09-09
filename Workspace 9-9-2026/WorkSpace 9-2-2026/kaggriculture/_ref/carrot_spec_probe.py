"""carrot_spec_probe.py — speculative carrot position injected into the v6h2c tape.

Engine facts this exploits:
  - BUY_PRODUCT pulls units straight out of market inventory (no seller needed);
    every bought unit drains inventory -> pushes the hinge price UP.
  - SELL at the (exploded) late price. The meta has no BUY logic to counter.
  - Shed cap 100 limits the position (bought units park in the shed).
Probe: buy N carrots at D12, dump at D28 H23; measure vs baseline.
"""
import sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import h2h_forced as H
import sim


def run_tape(tape, b_path, force=None, seed=1):
    H._st["force"] = list(force) if force else None
    H._st["seen"] = 0
    b = H.load_agent(b_path)
    g = sim.GameSim(seed=seed)
    shed_peak, px, money, disc = 0, {}, {}, 0
    for i in range(720):
        o = g.obs(0)
        act = tape[i] if i < len(tape) else {}
        hands = list(act.get("hands") or [])
        nf = len(o["farms"][0].get("hands") or [])
        while len(hands) < nf:
            hands.append(["PASS"])
        a0 = {"farmer": act.get("farmer") or ["PASS"], "hands": hands[:nf],
              "market": act.get("market") or []}
        if o["hour"] == 23:
            px[o["day"]] = dict(g.state[0].observation.market["prices"])
            shed_peak = max(shed_peak, sum(g.state[0].observation.private["shed"].values()))
            money[o["day"]] = o["farms"][0]["money"]
        g.step(a0, b(g.obs(1)))
    return g, px, shed_peak, money


def load_tape(bot_path):
    src = open(bot_path).read()
    Q = chr(39) * 3
    return json.loads(src.split("TAPE = json.loads(r" + Q)[1].split(Q)[0])


def with_spec(tape, qty=80, buy_day=12, sell_day=28):
    spec = [dict(t) for t in tape]
    bs, ss = buy_day * 24, sell_day * 24 + 23
    spec[bs] = dict(spec[bs]); spec[bs]["market"] = list(spec[bs].get("market") or []) + [["BUY_PRODUCT", "CARROT", qty]]
    spec[ss] = dict(spec[ss]); spec[ss]["market"] = list(spec[ss].get("market") or []) + [["SELL", "CARROT", qty]]
    return spec


if __name__ == "__main__":
    V = os.path.join(ROOT, "topbots", "v6h2c.py")
    M = os.path.join(ROOT, "topbots", "v1112fr.py")
    tape = load_tape(V)

    for label, force in [("PET x8", ["PET_CAFE"] * 8),
                         ("realistic S,S,F + PET x5", ["SMOOTHIE_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"] + ["PET_CAFE"] * 5)]:
        g0, px0, sp0, money = run_tape(tape, M, force=force)
        print(f"\n=== {label} ===")
        print(f"baseline:        ours {g0.money(0):>10,.0f}  shed_peak {sp0}")
        print(f"  money D10 {money.get(10, 0):,.0f}  D12 {money.get(12, 0):,.0f}  D14 {money.get(14, 0):,.0f}")
        print(f"  carrot px: D12 ${px0[12]['CARROT']}  D20 ${px0[20]['CARROT']}  D26 ${px0[26]['CARROT']}  D28 ${px0[28]['CARROT']}")
        for qty, bd, sd in [(60, 12, 28), (100, 12, 28), (60, 8, 27)]:
            t = with_spec(tape, qty, bd, sd)
            g1, px1, sp1, _ = run_tape(t, M, force=force)
            print(f"spec buy {qty:>3} @D{bd} sell @D{sd}: ours {g1.money(0):>10,.0f}  "
                  f"delta {g1.money(0) - g0.money(0):>+10,.0f}  shed_peak {sp1}")
