"""
planner.py — the "thinking" layer of the full AI bot.

Two capabilities, both built on the verified exact simulator (sim.py):

1. daily_capacity(obs) — "never miss anything"
   Enumerates today's MUST-DO tasks (feed every animal, water every plant,
   collect every fertilizer) plus the SHOULD-DO tasks (care, harvest, plant,
   dig). Greedily assigns tasks to workers to estimate the worker-steps
   required, and compares against the day's capacity (workers x 24 hours).
   Verdict: OK, or OVERLOADED (and exactly which tasks to drop first).

2. what_if(sim, days, options) — "think on its feet"
   Clones the current game state and simulates each candidate decision a few
   days forward, with the OPPONENT'S BEHAVIOUR FROZEN (replayed from a
   baseline rollout) so we isolate OUR decision's effect. Returns the
   dollar outcome of each option so the agent can pick the best.

   Example output:
       baseline                 : $12,341
       buy one more cow (d8)    : $12,905   (+$564)
       buy NE land early (d8)   : $11,940   (-$401)
       hold wheat 3 extra days  : $12,412   (+$71)

Usage (see demo_planner.py):
    sim = GameSim(seed=1)
    sim.run(agent, agent, steps=8*24)          # play to day 8
    results = what_if(sim, days=6, options=[...])
"""

import copy
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "agent"))

from sim import GameSim  # noqa: E402
import decision_agent_v2 as dv2  # noqa: E402

BOARD = 10
HALF = BOARD // 2
SHED_TILES = {(HALF - 1, HALF - 1), (HALF, HALF - 1), (HALF - 1, HALF), (HALF, HALF)}


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ---------------------------------------------------------------- scanning
def scan_farm(obs, player):
    """Compact board scanner shared by the planner. Same semantics as the
    agent's _scan_board, so planner and agent agree on what the board looks
    like."""
    farm = obs["farms"][player]
    tiles = farm["tiles"]
    unlocked = set(farm.get("unlocked_quadrants", []) or [])
    plants, animals, weeds, empty = [], [], [], []
    for y in range(BOARD):
        for x in range(BOARD):
            t = tiles[y][x]
            if t is None:
                if (("N" if y < HALF else "S") + ("W" if x < HALF else "E")) in unlocked:
                    empty.append((x, y))
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    plants.append({"x": x, "y": y, "crop": t.get("crop"),
                                   "watered_today": t.get("watered_today", False),
                                   "consec": t.get("consecutive_unwatered", 0),
                                   "yield": t.get("yield_units", 0),
                                   "planted_day": t.get("planted_day", 0)})
                elif k == "WEED":
                    weeds.append((x, y))
                elif k in ("COOP", "PASTURE") and t.get("animal"):
                    animals.append({"x": x, "y": y, "animal": t.get("animal"),
                                    "fed_today": t.get("fed_today", False),
                                    "consec": t.get("consecutive_unfed", 0),
                                    "cared_today": t.get("cared_today", False),
                                    "fert": t.get("fertilizer_available", False),
                                    "yield": t.get("yield_units", 0)})
    return {"plants": plants, "animals": animals, "weeds": weeds, "empty": empty,
            "hands": list(farm.get("hands", []) or []),
            "farmer": list(farm.get("farmer", [HALF - 1, HALF - 1])),
            "unlocked": unlocked}


def _worker_positions(obs, player):
    f = scan_farm(obs, player)
    pos = [tuple(f["farmer"])]
    for h in f["hands"]:
        pos.append(tuple(h))
    return pos


def _greedy_steps(tasks, workers):
    """Lower-bound-ish estimate: greedily assign each task (x, y) to the
    nearest worker, accumulating walk distance + 1 action. Returns total."""
    wpos = [(p[0], p[1]) for p in workers]
    total = 0
    for (tx, ty) in tasks:
        best = min(manhattan(w, (tx, ty)) for w in wpos)
        total += best + 1
    return total


# ------------------------------------------------------------ capacity
def daily_capacity(obs, player=0, expected_hires=0):
    """Estimate today's workload and whether the current crew can keep up.

    expected_hires: hands the agent is about to hire this morning (they are not
    yet on the board at hour 0). Added to the crew estimate.
    """
    f = scan_farm(obs, player)
    workers = _worker_positions(obs, player)
    n_workers = len(workers) + int(expected_hires)
    capacity = n_workers * 24

    feed = [(a["x"], a["y"]) for a in f["animals"] if not a["fed_today"]]
    water = [(p["x"], p["y"]) for p in f["plants"] if not p["watered_today"]]
    fert = [(a["x"], a["y"]) for a in f["animals"] if a["fert"]]
    care = [(a["x"], a["y"]) for a in f["animals"] if not a["cared_today"]]
    harvest = [(p["x"], p["y"]) for p in f["plants"] if p["yield"] > 0] + \
              [(a["x"], a["y"]) for a in f["animals"] if a["yield"] >= 2]
    weeds = list(f["weeds"])

    rows = []
    total = 0
    for label, tasks in [("FEED (critical)", feed), ("WATER (critical)", water),
                         ("FERT (critical)", fert), ("HARVEST", harvest),
                         ("CARE", care), ("DIG", weeds)]:
        steps = _greedy_steps(tasks, workers) if tasks else 0
        rows.append({"task": label, "count": len(tasks), "est_steps": steps})
        total += steps

    over = total > capacity
    verdict = "OVERLOADED" if over else "OK"
    report = {
        "workers": n_workers,
        "capacity_steps": capacity,
        "estimated_steps": total,
        "slack": capacity - total,
        "verdict": verdict,
        "tasks": rows,
        "plants": len(f["plants"]),
        "animals": len(f["animals"]),
        "empty_tiles": len(f["empty"]),
    }
    return report


def print_capacity(obs, player=0, expected_hires=0):
    r = daily_capacity(obs, player, expected_hires=expected_hires)
    print(f"Day {obs['day']} hour {obs['hour']} | workers={r['workers']} "
          f"plants={r['plants']} animals={r['animals']} empty={r['empty_tiles']}")
    for t in r["tasks"]:
        if t["count"]:
            print(f"   {t['task']:<18} n={t['count']:>2}  ~{t['est_steps']:>3} steps")
    print(f"   need ~{r['estimated_steps']} steps vs capacity {r['capacity_steps']} "
          f"(slack {r['slack']:+d}) -> {r['verdict']}")


# ---------------------------------------------------------------- what-if
def liquidation_value(obs, player):
    """End-of-horizon value of a player's position: money + shed products at
    current prices + seeds at cost + standing crops at max(current yield value,
    seed cost).

    Animals are deliberately EXCLUDED (they are illiquid — can't be sold —
    and their value is their future production, which only shows up if the
    rollout horizon is long enough to include their yield ticks). This keeps a
    short-horizon what-if from treating a $400 cow as instantly worth $400."""
    from decision_agent_v2 import CROPS
    farm = obs["farms"][player]
    priv = obs.get("private") or {}
    shed = priv.get("shed") or {}
    seeds = priv.get("seeds") or {}
    prices = obs["market"]["prices"]
    val = float(farm.get("money", 0) or 0)
    for item, qty in shed.items():
        if qty and item in prices:
            val += qty * prices[item]
    for c, n in seeds.items():
        if c in CROPS:
            val += n * CROPS[c]["seed"]
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "PLANT" \
                    and t.get("crop") in CROPS:
                price = prices.get(t["crop"], 1)
                val += max(t.get("yield_units", 0) * price,
                           CROPS[t["crop"]]["seed"])
    return val


def _rollout(sim, days, agent0, agent1):
    """Roll `days` forward. agent0/agent1 are callables obs->action (or None)."""
    for _ in range(days * 24):
        a0 = agent0(sim.obs(0)) if agent0 else {}
        a1 = agent1(sim.obs(1)) if agent1 else {}
        sim.step(a0, a1)
    return sim.money(0), sim.money(1)


def _pass_action(obs):
    n = len((obs["farms"][obs["player"]].get("hands")) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}


def what_if(base_sim, days, options, agent0=None, verbose=True,
            terminal_value=False, opp_pass=False):
    """Evaluate candidate decisions.

    options: list of (label, wrap_fn) where wrap_fn(base_agent) -> agent' is an
    action-wrapper applied to OUR seat.

    opp_pass=True: the opponent does nothing in every rollout (cleanest for
    isolating our decision's marginal value — no cross-contamination between
    the recorded opponent and the changed market).

    opp_pass=False: the opponent plays agent0; its actions are recorded from
    the baseline and replayed identically in every option (self-play shadow).

    terminal_value: score the end of each rollout as money + liquidation value
    of standing assets (only for short horizons; for full-game horizons pass
    False and just read the money).

    Returns list of (label, final_score_p0, delta_vs_baseline).
    """
    if agent0 is None:
        dv2.set_params(dict(dv2.DEFAULT_PARAMS))
        agent0 = lambda obs: dv2.agent(obs)  # noqa: E731

    def score(sim):
        m = sim.money(0)
        if terminal_value:
            m += liquidation_value(sim.obs(0), 0)
        return m

    if opp_pass:
        base = base_sim.clone()
        _rollout(base, days, agent0, _pass_action)
        base_score = score(base)
        results = [("baseline", base_score, 0.0)]
        for label, wrap in options:
            sim = base_sim.clone()
            _rollout(sim, days, wrap(agent0), _pass_action)
            s = score(sim)
            results.append((label, s, s - base_score))
            if verbose:
                print(f"   {label:<28} ${s:>9,.0f}  ({s - base_score:+,.0f} vs baseline)")
        return results

    # self-play-shadow opponent: record baseline, replay in options
    base = base_sim.clone()
    opp_log = []
    def rec_opp(obs):
        a = agent0(obs)
        opp_log.append(a)
        return a
    _rollout(base, days, agent0, rec_opp)
    base_score = score(base)

    results = [("baseline", base_score, 0.0)]
    for label, wrap in options:
        sim = base_sim.clone()
        wrapped0 = wrap(agent0)
        idx = [0]
        def script_opp(obs):
            a = opp_log[idx[0]]
            idx[0] += 1
            return a
        _rollout(sim, days, wrapped0, script_opp)
        s = score(sim)
        results.append((label, s, s - base_score))
        if verbose:
            print(f"   {label:<28} ${s:>9,.0f}  ({s - base_score:+,.0f} vs baseline)")
    return results


# ------------------------------------------------------------ option makers
def option_buy_animal(animal, count=1, day=0):
    """Force-buy `count` of an animal at the start of `day`."""
    def wrap(base_agent):
        def w(obs):
            a = base_agent(obs)
            if obs["day"] == day and obs["hour"] == 0:
                m = list(a.get("market", []) or [])
                m.insert(0, ["BUY_ANIMAL", animal, count])
                a["market"] = m[:10]
            return a
        return w
    return wrap


def option_buy_land(day=0):
    """Force a BUY_LAND at the start of `day`."""
    def wrap(base_agent):
        def w(obs):
            a = base_agent(obs)
            if obs["day"] == day and obs["hour"] == 0:
                m = list(a.get("market", []) or [])
                m.insert(0, ["BUY_LAND"])
                a["market"] = m[:10]
            return a
        return w
    return wrap


def option_buy_wheat(units=5, day=0):
    """Force-buy extra wheat (feed stock) at the start of `day`."""
    def wrap(base_agent):
        def w(obs):
            a = base_agent(obs)
            if obs["day"] == day and obs["hour"] == 0:
                m = list(a.get("market", []) or [])
                m.insert(0, ["BUY_PRODUCT", "WHEAT", units])
                a["market"] = m[:10]
            return a
        return w
    return wrap


def option_extra_hires(n=2, days=(0,)):
    """Force `n` extra HIRE orders at the start of the given days."""
    def wrap(base_agent):
        def w(obs):
            a = base_agent(obs)
            if obs["day"] in days and obs["hour"] == 0:
                m = list(a.get("market", []) or [])
                for _ in range(n):
                    m.insert(0, ["HIRE"])
                a["market"] = m[:10]
            return a
        return w
    return wrap


def option_sell_now(item, units, day=0, hour=2):
    """Force-sell `units` of `item` on a specific day/hour."""
    def wrap(base_agent):
        def w(obs):
            a = base_agent(obs)
            if obs["day"] == day and obs["hour"] == hour:
                m = list(a.get("market", []) or [])
                m.insert(0, ["SELL", item, units])
                a["market"] = m[:10]
            return a
        return w
    return wrap
