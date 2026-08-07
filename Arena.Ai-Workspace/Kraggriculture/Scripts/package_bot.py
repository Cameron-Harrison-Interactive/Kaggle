"""
package_bot.py — bundle main.py + brain + dna into a Kaggle-ready tar.gz.

Run on Windows:
    cd Z:\\Kaggle\\Kragriculture
    python Scripts\\package_bot.py

Submit:
    kaggle competitions submit kagriculture -f HI_AgriBot_v1.tar.gz -m "v5.8z5ff lookahead workers + v5.8z5ff recovery"
"""

import hashlib
import os
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AGENT_DIR = os.path.join(ROOT, "Agent")
ARCHIVE = os.path.join(ROOT, "HI_AgriBot_v1.tar.gz")
HASH_FILE = os.path.join(ROOT, "Data", "last_package.txt")


def test_local_match():
    from kaggle_environments import make
    print("[test] running local match: main.py vs starter ...")
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720})
        env.run([os.path.join(AGENT_DIR, "main.py"), "starter"])
        p0 = env.state[0].reward if env.state[0].reward is not None else 0
        p1 = env.state[1].reward if env.state[1].reward is not None else 0
        print(f"[test] p0=${p0:.0f}  p1=${p1:.0f}")
        if p0 <= 0:
            print("[test] FAIL: p0 has $0 reward; bot likely returned invalid actions.")
            return False
        if p0 < 5000:
            print("[test] WARN: p0 is lower than expected, but not zero.")
        return True
    except Exception as e:
        print(f"[test] FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def package():
    files = ["main.py"]
    optional = ["HI_Market_Brain.pkl", "dna.json", "dna_v6.json", "champion_dna.json"]
    print(f"[package] building archive at {ARCHIVE}")
    with tarfile.open(ARCHIVE, "w:gz") as tar:
        for fname in files:
            path = os.path.join(AGENT_DIR, fname)
            if not os.path.exists(path):
                print(f"[package] FATAL: required file missing: {path}")
                sys.exit(1)
            tar.add(path, arcname=fname)
            print(f"[package]   + {fname} ({os.path.getsize(path)} bytes)")
        for fname in optional:
            path = os.path.join(AGENT_DIR, fname)
            if os.path.exists(path):
                tar.add(path, arcname=fname)
                print(f"[package]   + {fname} ({os.path.getsize(path)} bytes)")
            else:
                print(f"[package]   - skipping {fname} (not present)")
    size = os.path.getsize(ARCHIVE)
    h = hashlib.sha256()
    with open(ARCHIVE, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    digest = h.hexdigest()
    os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)
    with open(HASH_FILE, "w") as f:
        f.write(f"{digest}  {ARCHIVE}  {size} bytes  {time.ctime()}\n")
    print(f"[package] archive size: {size} bytes")
    print(f"[package] SHA-256: {digest}")
    print(f"[package] hash saved to {HASH_FILE}")


def main():
    print("=" * 60)
    print("  PACKAGE BOT v5.8z5ff")
    print("=" * 60)
    if not test_local_match():
        print("[package] refusing to package: local test failed.")
        sys.exit(1)
    package()
    print()
    print("Next step:")
    print(f"  kaggle competitions submit kagriculture -f {ARCHIVE} -m \"v5.8z5ff lookahead workers + v5.8z5ff recovery\"")


if __name__ == "__main__":
    main()
