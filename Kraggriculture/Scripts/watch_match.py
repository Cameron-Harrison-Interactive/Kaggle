"""
watch_match.py — render one Kaggriculture match to HTML and open it in your browser.

Run from project root:
    cd Z:\Kaggle\Kraggriculture
    python Scripts\watch_match.py
    python Scripts\watch_match.py random
    python Scripts\watch_match.py starter

Important:
    The environment name is "kaggriculture" with TWO g's after ka.
    "kagriculture" is wrong and causes: Unknown Environment Specification.
"""

import os
import sys
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AGENT_DIR = os.path.join(ROOT, "Agent")
DATA_DIR = os.path.join(ROOT, "Data")
REPLAY_FILE = os.path.join(DATA_DIR, "latest_replay.html")
os.makedirs(DATA_DIR, exist_ok=True)

OPPONENT = sys.argv[1] if len(sys.argv) > 1 else "starter"


def main():
    from kaggle_environments import make

    agent_path = os.path.join(AGENT_DIR, "main.py")
    if not os.path.exists(agent_path):
        raise FileNotFoundError(f"Could not find bot file: {agent_path}")

    print(f"Simulating one match: main.py vs {OPPONENT} ...")
    env = make("kaggriculture", configuration={"episodeSteps": 720})
    env.run([agent_path, OPPONENT])

    p0 = env.state[0].reward if env.state[0].reward is not None else 0
    p1 = env.state[1].reward if env.state[1].reward is not None else 0
    print(f"  p0=${p0:.0f}  p1=${p1:.0f}")

    print("Rendering HTML replay ...")
    html = env.render(mode="html")
    with open(REPLAY_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Saved to {REPLAY_FILE}")
    url = "file://" + os.path.abspath(REPLAY_FILE)
    print(f"Opening {url} in your browser ...")
    webbrowser.open(url)


if __name__ == "__main__":
    main()
