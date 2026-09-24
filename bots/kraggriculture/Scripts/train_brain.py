"""
train_brain.py — build HI_Market_Brain.pkl from your match data.

Run:
    python Scripts\\train_brain.py
"""

import json
import os
import pickle
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AGENT_DIR = os.path.join(ROOT, "Agent")
DATA_DIR  = os.path.join(ROOT, "Data")
BRAIN_PATH = os.path.join(AGENT_DIR, "HI_Market_Brain.pkl")
warnings.filterwarnings("ignore")


def train_from_real_data():
    import numpy as np
    import pandas as pd

    episodes_csv = os.path.join(DATA_DIR, "episodes.csv")
    replays_parq = os.path.join(DATA_DIR, "replays.parquet")
    if not (os.path.exists(episodes_csv) or os.path.exists(replays_parq)):
        return None

    try:
        if os.path.exists(replays_parq):
            df = pd.read_parquet(replays_parq)
        else:
            df = pd.read_csv(episodes_csv)
    except Exception as e:
        print(f"  ! could not read data file: {e}")
        return None

    required = {"step", "player", "item", "price", "action"}
    if not required.issubset(df.columns):
        print(f"  ! data file missing required columns {required}; have {list(df.columns)}")
        print(f"  ! falling back to synthetic data")
        return None

    df["day"] = df["step"] // 24
    df["hour"] = df["step"] % 24

    sells = df[df["action"].str.upper() == "SELL"].copy()
    if len(sells) < 10:
        print(f"  ! only {len(sells)} sell events; too few to train on. Falling back.")
        return None

    X_rows, y_rows = [], []
    for item in ("WHEAT", "CARROT"):
        sub = sells[sells["item"] == item].sort_values("step")
        if len(sub) < 3:
            continue
        for idx, row in sub.iterrows():
            step = row["step"]
            future = df[(df["item"] == item) & (df["step"] > step) & (df["step"] <= step + 24)]
            if len(future) == 0:
                continue
            peak = future["price"].max()
            X_rows.append([row["day"], row["hour"], row["price"], row.get("qty", 0) or 0])
            y_rows.append(1 if row["price"] >= 0.8 * peak else 0)

    if len(X_rows) < 5:
        print(f"  ! only {len(X_rows)} training rows; falling back.")
        return None

    X = np.array(X_rows, dtype=np.float32)
    y = np.array(y_rows, dtype=np.int32)
    print(f"  real data: {X.shape[0]} training rows, {y.sum()} positive labels")
    return X, y


def train_from_synthetic():
    import numpy as np

    sys.path.insert(0, AGENT_DIR)
    from kaggle_environments import make

    print("  synthetic mode: running 4 self-play matches to build training data ...")
    X_rows, y_rows = [], []

    for trial in range(4):
        env = make("kaggriculture", configuration={"episodeSteps": 720})
        env.run([os.path.join(AGENT_DIR, "main.py"), "starter"])
        steps = env.steps
        for step_idx, step in enumerate(steps):
            for player_idx in (0, 1):
                s = step[player_idx]
                obs = s.observation
                if not isinstance(obs, dict):
                    continue
                market = obs.get("market", {}) or {}
                prices = (market.get("prices", {}) or {}).get("WHEAT", 25)
                private = obs.get("private", {}) or {}
                shed = private.get("shed", {}) or {}
                action = s.action if isinstance(s.action, dict) else {}
                m_orders = action.get("market", []) if isinstance(action, dict) else []
                wheat_sell_qty = 0
                for order in (m_orders or []):
                    if isinstance(order, list) and len(order) >= 2 and order[0] == "SELL" and order[1] == "WHEAT":
                        wheat_sell_qty = order[2] if len(order) >= 3 else 1
                day = obs.get("day", 0)
                hour = obs.get("hour", 0)
                wheat_qty = shed.get("WHEAT", 0)
                future_prices = []
                for k in range(step_idx + 1, min(step_idx + 24, len(steps))):
                    fp = (steps[k][player_idx].observation.get("market", {}) or {}).get("prices", {}).get("WHEAT", wheat_qty)
                    future_prices.append(fp)
                if not future_prices or wheat_sell_qty == 0:
                    continue
                peak = max(future_prices)
                X_rows.append([day, hour, wheat_qty, wheat_qty])
                y_rows.append(1 if wheat_qty >= 0.8 * peak else 0)

    if len(X_rows) < 5:
        print("  ! not enough real training data; using a placeholder brain")
        X = np.array([
            [0, 0, 25, 0],
            [5, 0, 30, 10],
            [10, 0, 40, 50],
            [20, 0, 45, 100],
            [25, 0, 20, 50],
        ], dtype=np.float32)
        y = np.array([0, 0, 1, 1, 0], dtype=np.int32)
    else:
        X = np.array(X_rows, dtype=np.float32)
        y = np.array(y_rows, dtype=np.int32)

    print(f"  synthetic data: {X.shape[0]} training rows, {int(y.sum())} positive")
    return X, y


def train_and_save(X, y):
    from sklearn.tree import DecisionTreeClassifier
    clf = DecisionTreeClassifier(max_depth=5, random_state=42)
    clf.fit(X, y)
    with open(BRAIN_PATH, "wb") as f:
        pickle.dump(clf, f)
    size = os.path.getsize(BRAIN_PATH)
    print(f"  saved brain to {BRAIN_PATH} ({size} bytes)")
    return clf


def main():
    print("=" * 60)
    print("  TRAIN BRAIN v2.3")
    print("=" * 60)
    real = train_from_real_data()
    if real is None:
        X, y = train_from_synthetic()
    else:
        X, y = real
    train_and_save(X, y)
    print("Done. main.py will pick this up on next match.")


if __name__ == "__main__":
    main()
