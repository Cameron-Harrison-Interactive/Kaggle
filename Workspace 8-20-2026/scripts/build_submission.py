#!/usr/bin/env python3
"""build_submission.py — smoke-test then package the agent for Kaggle.

Produces the always-current submission artifacts under kaggriculture/submit/:
  - submit/main.py                 (single-file agent, Kaggle-ready)
  - submit/HI_AgriBot_v8.tar.gz    (bundled submission)
  - submit/BUILD_INFO.txt          (version, sha256, local test scores)

Usage:
  python3 scripts/build_submission.py          # smoke test + package
  python3 scripts/build_submission.py --fast   # skip the smoke test
"""
import hashlib
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AGENT = os.path.join(ROOT, "agent", "main.py")
SUBMIT_DIR = os.path.join(ROOT, "submit")


def _read_version():
    """The tarball name ALWAYS matches the agent's VERSION exactly."""
    with open(AGENT) as f:
        for line in f:
            if line.startswith("VERSION"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "HI_AgriBot_unknown"


VERSION = _read_version()


def smoke_test():
    from kaggle_environments import make
    print("[build] smoke test: agent vs starter (1 seed) ...")
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
    env.run([AGENT, "starter"])
    p0 = env.steps[-1][0].reward or 0
    p1 = env.steps[-1][1].reward or 0
    print(f"[build]   p0=${p0:,.0f}  p1=${p1:,.0f}")
    if p0 < 30000:
        print("[build] FAIL: score too low, refusing to package.")
        sys.exit(1)
    return p0


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    fast = "--fast" in sys.argv
    score = smoke_test() if not fast else None

    os.makedirs(SUBMIT_DIR, exist_ok=True)
    # 1) single-file submit target (always current)
    target_py = os.path.join(SUBMIT_DIR, "main.py")
    shutil.copyfile(AGENT, target_py)

    # 2) tar.gz bundle with main.py at the archive root, named EXACTLY by version
    import tarfile
    tar_path = os.path.join(SUBMIT_DIR, f"{VERSION}.tar.gz")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(target_py, arcname="main.py")
    # drop any older differently-named bundles so submit/ stays unambiguous
    for fn in os.listdir(SUBMIT_DIR):
        if fn.endswith(".tar.gz") and fn != f"{VERSION}.tar.gz":
            os.remove(os.path.join(SUBMIT_DIR, fn))

    size = os.path.getsize(tar_path)
    digest = sha256(tar_path)

    # 3) build info
    info = [
        f"version: {VERSION}",
        f"built: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"source: agent/main.py",
        f"smoke_score_p0: {int(score) if score else 'skipped'}",
        f"tarball: {os.path.basename(tar_path)} ({size} bytes)",
        f"sha256: {digest}",
        "",
        "Submit with:",
        f"  kaggle competitions submit kaggriculture -f submit/{VERSION}.tar.gz -m \"{VERSION}\"",
    ]
    with open(os.path.join(SUBMIT_DIR, "BUILD_INFO.txt"), "w") as f:
        f.write("\n".join(info) + "\n")

    print(f"[build] wrote {target_py}")
    print(f"[build] wrote {tar_path} ({size} bytes)")
    print(f"[build] sha256 {digest}")
    print("[build] DONE.")


if __name__ == "__main__":
    main()
