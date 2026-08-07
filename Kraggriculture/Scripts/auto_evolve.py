"""
auto_evolve.py — v5.8z5ff local DNA evolver.

Run on Windows:
    cd Z:\\Kaggle\\Kragriculture
    python Scripts\\auto_evolve.py

It mutates Agent\\dna.json, tests main.py locally, and saves winners to:
    Agent\\champion_dna.json
    Data\\Winning_DNA.json
"""

import json
import os
import random
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AGENT_DIR = os.path.join(ROOT, "Agent")
DATA_DIR = os.path.join(ROOT, "Data")
REPLAY_DIR = os.path.join(DATA_DIR, "Best_Replays")
os.makedirs(REPLAY_DIR, exist_ok=True)

DNA_RANGES = {
    "target_wheat": (4, 13, 1),
    "target_carrot": (2, 12, 1),
    "target_tomato": (0, 9, 1),
    "target_strawberry": (0, 8, 1),
    "target_melon": (0, 10, 1),
    "max_total": (18, 55, 1),

    "wheat_sell": (25, 48, 1),
    "carrot_sell": (32, 55, 1),
    "tomato_sell": (58, 92, 2),
    "strawberry_sell": (112, 175, 3),
    "melon_sell": (215, 330, 5),
    "egg_sell": (46, 78, 2),
    "milk_sell": (145, 235, 5),
    "wool_sell": (175, 280, 5),
    "fertilizer_sell": (85, 150, 5),

    "melon_danger_opp": (3, 12, 1),
    "melon_crash_price": (145, 225, 5),
    "dump_turn": (636, 690, 3),

    "buy_land": (0, 3, 1),
    "land_reserve": (100, 900, 50),
    "target_hires": (4, 7, 1),
    "use_animals": (0, 1, 1),
    "use_brain": (0, 1, 1),
    "wheat_buy_low": (14, 22, 1),
    "fertilizer_buy_low": (55, 85, 5),
}


def load_dna(path):
    with open(path, "r") as f:
        return json.load(f)


def save_dna(path, dna):
    with open(path, "w") as f:
        json.dump(dna, f, indent=2)


def mutate(parent):
    child = {}
    for k, (lo, hi, step) in DNA_RANGES.items():
        base = parent.get(k, (lo + hi) // 2)
        jump = random.choice([-2, -1, 0, 0, 1, 2]) * step
        child[k] = max(lo, min(hi, int(base + jump)))
    return child


def run_match(agent_path, opponent):
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720})
    env.run([agent_path, opponent])
    p0 = env.state[0].reward if env.state[0].reward is not None else 0
    p1 = env.state[1].reward if env.state[1].reward is not None else 0
    return float(p0), float(p1), env


def fitness(my_cash, opp_cash):
    margin = my_cash - opp_cash
    return my_cash + 0.25 * margin + (300 if margin > 0 else -150 if margin < 0 else 0)


def main():
    print("=" * 64)
    print("  KAGRICULTURE AUTO-EVOLVER v5.8z5ff")
    print("  evolves 5-crop mix, melon-defense, land, hires, animal flags")
    print("=" * 64)
    print(f"Root: {ROOT}")

    agent_path = os.path.join(AGENT_DIR, "main.py")
    dna_path = os.path.join(AGENT_DIR, "dna.json")
    champion_path = os.path.join(AGENT_DIR, "champion_dna.json")
    winning_path = os.path.join(DATA_DIR, "Winning_DNA.json")

    if not os.path.exists(champion_path):
        save_dna(champion_path, load_dna(dna_path))
    champion = load_dna(champion_path)
    save_dna(dna_path, champion)

    print("\n[baseline] champion vs starter")
    p0, p1, _ = run_match(agent_path, "starter")
    best_score = fitness(p0, p1)
    best_dna = dict(champion)
    print(f"baseline: bot=${p0:.0f} starter=${p1:.0f} fit={best_score:.0f}")

    opponents = ["starter", "random", agent_path]
    labels = ["starter", "random", "champion"]
    match_no = 1
    t0 = time.time()
    failures = 0

    while True:
        child = mutate(best_dna if random.random() < 0.75 else champion)
        save_dna(dna_path, child)
        opp = opponents[match_no % len(opponents)]
        label = labels[match_no % len(labels)]
        try:
            my_cash, opp_cash, env = run_match(agent_path, opp)
            failures = 0
        except Exception as e:
            failures += 1
            print(f"[{match_no}] ERROR {e}")
            traceback.print_exc()
            if failures >= 10:
                print("too many failures; stopping")
                return
            continue

        fit = fitness(my_cash, opp_cash)
        result = "WIN" if my_cash > opp_cash else "LOSS" if my_cash < opp_cash else "TIE"
        print(
            f"[{match_no:5d}] vs {label:8s} {result:4s} "
            f"bot=${my_cash:6.0f} opp=${opp_cash:6.0f} fit={fit:7.0f} "
            f"mix W{child['target_wheat']}/C{child['target_carrot']}/T{child['target_tomato']}/S{child['target_strawberry']}/M{child['target_melon']} "
            f"land{child['buy_land']} hires{child['target_hires']}"
        )

        if fit > best_score:
            best_score = fit
            best_dna = dict(child)
            champion = dict(child)
            save_dna(champion_path, best_dna)
            save_dna(winning_path, best_dna)
            print("=" * 64)
            print(f"NEW CHAMPION fit={fit:.0f} cash=${my_cash:.0f}")
            print(json.dumps(best_dna, indent=2))
            print("=" * 64)
            try:
                html = env.render(mode="html")
                fp = os.path.join(REPLAY_DIR, f"v24_fit{int(fit)}_match{match_no}.html")
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception as e:
                print(f"replay save failed: {e}")

        match_no += 1
        if match_no % 100 == 0:
            dt = max(1, time.time() - t0)
            print(f"--- {match_no - 1} matches in {dt/60:.1f} min ({(match_no-1)/dt:.2f}/sec) ---")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[stopped] best DNA is in Agent\\champion_dna.json and Data\\Winning_DNA.json")
