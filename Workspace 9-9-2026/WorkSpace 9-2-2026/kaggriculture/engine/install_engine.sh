#!/bin/bash
# Reinstall the engine after a sandbox recycle (site-packages is volatile).
# Files: engine/*.py + *.json (this dir). Source: Kaggle/kaggle-environments GitHub,
# verified 2026-09-06 to reproduce v7b $78,858 seed 10001 EXACTLY (seed 10011).
# NOTE: the env name is the 13-letter k-a-g-g-r-i-c-u-l-t-u-r-e word; it is built
# from parts because typing it directly can inject a zero-width space.
set -e
if ! python3 -c "import kaggle_environments" 2>/dev/null; then
  pip install kaggle_environments >/dev/null
fi
HERE=$(cd "$(dirname "$0")" && pwd)
python3 - "$HERE" <<'PY'
import os, shutil, sys, glob
here = sys.argv[1]
import kaggle_environments
NAME = "kagg" + "riculture"   # k-a-g-g-r-i-c-u-l-t-u-r-e
envs = os.path.join(os.path.dirname(kaggle_environments.__file__), "envs")
dest = os.path.join(envs, NAME)
os.makedirs(dest, exist_ok=True)
py = [f for f in glob.glob(os.path.join(here, "*.py")) if "install" not in os.path.basename(f)][0]
js = glob.glob(os.path.join(here, "*.json"))[0]
shutil.copy(py, os.path.join(dest, NAME + ".py"))
shutil.copy(js, os.path.join(dest, NAME + ".json"))
for junk in ("__init__.py", "__pycache__"):
    p = os.path.join(dest, junk)
    if os.path.isfile(p): os.remove(p)
    elif os.path.isdir(p): shutil.rmtree(p)
from kaggle_environments import make
e = make(NAME)
print("engine installed + verified:", e.name)
PY
