"""Battle harness — standardized testing for Kaggriculture agents.

Tests agents across multiple seeds, both seats, vs multiple opponents.
Reports wins/losses/ties, average scores, and margins.
"""
import json
import sys
import os
import time
import importlib.util
from kaggle_environments import make


def load_agent(path):
    """Load an agent module from file path."""
    if path == "self":
        return None  # will use same agent
    spec = importlib.util.spec_from_file_location("agent", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def battle(agent_a_path, agent_b_path, seed, seat_swap=False):
    """Run a single battle. Returns (p0_money, p1_money, p0_reward, p1_reward).
    
    seat_swap=False: A plays seat0, B plays seat1
    seat_swap=True:  B plays seat0, A plays seat1
    """
    agent_a = load_agent(agent_a_path) if isinstance(agent_a_path, str) else agent_a_path
    agent_b = load_agent(agent_b_path) if isinstance(agent_b_path, str) else agent_b_path
    
    if seat_swap:
        agent_a, agent_b = agent_b, agent_a
    
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    result = env.run([agent_a, agent_b])
    final = result[-1]
    
    obs0 = final[0]["observation"]
    obs1 = final[1]["observation"]
    
    p0_money = obs0["farms"][0]["money"]
    p1_money = obs1["farms"][1]["money"]
    
    return p0_money, p1_money


def run_battery(agent_path, opp_path, seeds=range(1, 11), label="test"):
    """Run a battery of tests across seeds, both seats.
    
    Returns dict with results.
    """
    results = {
        "label": label,
        "agent": agent_path,
        "opponent": opp_path,
        "seeds_tested": [],
        "wins": 0,
        "losses": 0,
        "ties": 0,
        "total_margin": 0,
        "games": [],
    }
    
    for seed in seeds:
        for seat in [0, 1]:
            p0, p1 = battle(agent_path, opp_path, seed, seat_swap=(seat == 1))
            
            if seat == 0:
                our_money, opp_money = p0, p1
            else:
                our_money, opp_money = p1, p0
            
            margin = our_money - opp_money
            if margin > 0:
                results["wins"] += 1
            elif margin < 0:
                results["losses"] += 1
            else:
                results["ties"] += 1
            
            results["total_margin"] += margin
            results["seeds_tested"].append(seed)
            results["games"].append({
                "seed": seed,
                "seat": seat,
                "our_money": our_money,
                "opp_money": opp_money,
                "margin": margin,
            })
    
    n_games = len(results["games"])
    results["avg_margin"] = results["total_margin"] / max(n_games, 1)
    results["win_rate"] = results["wins"] / max(n_games, 1)
    
    return results


def print_results(results):
    """Pretty print battle results."""
    print(f"\n{'='*60}")
    print(f"  {results['label']}")
    print(f"  vs {results['opponent']}")
    print(f"{'='*60}")
    n_games = results["wins"] + results["losses"] + results["ties"]
    print(f"  Record: {results['wins']}W-{results['losses']}L-{results['ties']}T ({n_games} games)")
    print(f"  Win Rate: {results['win_rate']:.1%}")
    print(f"  Avg Margin: ${results['avg_margin']:,.0f}")
    print(f"  Total Margin: ${results['total_margin']:,.0f}")
    print(f"  Seeds: {sorted(set(results['seeds_tested']))}")
    print()
    
    # Per-seed breakdown
    by_seed = {}
    for g in results["games"]:
        s = g["seed"]
        if s not in by_seed:
            by_seed[s] = []
        by_seed[s].append(g)
    
    print(f"  {'Seed':>4} {'Seat0':>10} {'Seat1':>10} {'Margin':>10}")
    print(f"  {'-'*4} {'-'*10} {'-'*10} {'-'*10}")
    for s in sorted(by_seed.keys()):
        games = by_seed[s]
        s0 = next((g for g in games if g["seat"] == 0), None)
        s1 = next((g for g in games if g["seat"] == 1), None)
        s0_str = f"${s0['our_money']:,.0f}" if s0 else "N/A"
        s1_str = f"${s1['our_money']:,.0f}" if s1 else "N/A"
        margins = [g["margin"] for g in games]
        avg_m = sum(margins) / len(margins)
        m_str = f"${avg_m:+,.0f}"
        print(f"  {s:>4} {s0_str:>10} {s1_str:>10} {m_str:>10}")
    print()


def quick_test(agent_path, seeds=[1, 2, 3]):
    """Quick self-play test on a few seeds."""
    results = run_battery(agent_path, agent_path, seeds=seeds, label="Self-play")
    print_results(results)
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python battle_harness.py <agent_path> [opp_path] [seeds]")
        print("  Default: self-play on seeds 1-5")
        sys.exit(1)
    
    agent = sys.argv[1]
    opp = sys.argv[2] if len(sys.argv) > 2 else "self"
    if opp == "self":
        opp = agent
    
    seeds = list(range(1, 6))
    if len(sys.argv) > 3:
        seeds = [int(x) for x in sys.argv[3].split(",")]
    
    results = run_battery(agent, opp, seeds=seeds, label=f"Test: {os.path.basename(agent)}")
    print_results(results)
