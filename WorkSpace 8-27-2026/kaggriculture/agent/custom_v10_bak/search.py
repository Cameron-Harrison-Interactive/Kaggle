"""
search.py — forward-search wrapper for the custom agent.

At key days (H1, right after hire+basic economy runs), test a few candidate
EXTRA market orders. Roll forward 48 steps under normal agent behavior;
pick the candidate with the highest projected money.

Very cheap: each rollout ~200ms; test 3-4 candidates; total < 1s per turn.
Only fires on chosen sample days to avoid overhead.
"""

import copy
import sys


def _rollout(sim, agent_fn, n_steps):
    """Roll sim forward n_steps using agent_fn for player 0, PASS for player 1."""
    for _ in range(n_steps):
        obs0 = sim.obs(0)
        obs1 = sim.obs(1)
        try:
            a0 = agent_fn(obs0)
        except Exception:
            a0 = {"farmer": ["PASS"], "hands": [], "market": []}
        n_hands = len(obs1["farms"][1].get("hands", []) or [])
        a1 = {"farmer": ["PASS"], "hands": [["PASS"]] * n_hands, "market": []}
        sim.step(a0, a1)
    return sim


def choose_extra_order(sim, agent_fn, candidates, horizon=48):
    """Given a live sim + list of candidate market order lists, roll each
    candidate forward `horizon` steps and return the best (highest player-0
    money).

    candidates: list of (label, extra_orders) where extra_orders is a list
                of market ops to APPEND to this turn's order list (before
                stepping). If None, no extra orders added.

    Returns (best_label, best_orders, best_money).
    """
    best = None
    best_money = -1e18
    for label, extra in candidates:
        # Clone the sim BEFORE agent runs — we'll compose the action
        c = sim.clone() if hasattr(sim, "clone") else copy.deepcopy(sim)
        # Compose one-turn action: agent + extra orders
        obs0 = c.obs(0)
        try:
            a0 = agent_fn(obs0)
        except Exception:
            a0 = {"farmer": ["PASS"], "hands": [], "market": []}
        if extra:
            a0["market"] = (a0.get("market", []) + list(extra))[:10]
        n_hands = len(c.obs(1)["farms"][1].get("hands", []) or [])
        a1 = {"farmer": ["PASS"], "hands": [["PASS"]] * n_hands, "market": []}
        c.step(a0, a1)
        # Then roll (horizon-1) more steps under normal agent
        _rollout(c, agent_fn, horizon - 1)
        m = c.money(0)
        if m > best_money:
            best_money = m
            best = (label, extra)
    if best is None:
        return (None, None, 0.0)
    return (best[0], best[1], best_money)
