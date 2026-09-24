#!/usr/bin/env bash
# submit.sh — submit the current build to Kaggle.
# Requires: kaggle CLI + KAGGLE_API_TOKEN (or ~/.kaggle/access_token).
# Always build first so the tarball matches agent/main.py exactly.
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="HI_AgriBot_v8_FieldMarshal"
MSG="${1:-$VERSION}"

python3 scripts/build_submission.py
if [ -n "${KAGGLE_API_TOKEN:-}" ]; then
  export KAGGLE_API_TOKEN
elif [ -f "$HOME/.kaggle/access_token" ]; then
  export KAGGLE_API_TOKEN="$(cat "$HOME/.kaggle/access_token")"
fi

echo "[submit] uploading submit/${VERSION}.tar.gz ..."
kaggle competitions submit kaggriculture \
  -f "submit/${VERSION}.tar.gz" \
  -m "$MSG"
echo "[submit] done. Check: kaggle competitions submissions kaggriculture"
