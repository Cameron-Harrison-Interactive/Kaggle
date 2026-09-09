#!/bin/bash
# AUTONOMOUS v11 SHIP — fires at 2026-09-05 00:02 UTC (after quota reset)
export KAGGLE_API_TOKEN=KGAT_174ebff7462e0b34526c2936d51a2fc0
WS="/home/user/WorkSpace 9-2-2026/kaggressur"   # placeholder, fixed below
WS="/home/user/WorkSpace 9-2-2026/kaggriculture"
TARBALL="$WS/submission_tetsu_r5_v11.tar.gz"
TARGET_EPOCH=1788566520   # 2026-09-05 00:02:00 UTC

echo "[ship] waiting until 00:02 UTC (now: $(date -u))"
while [ "$(date -u +%s)" -lt "$TARGET_EPOCH" ]; do
  sleep 20
done
echo "[ship] quota window reached at $(date -u)"

# self-heal: ensure kaggle client exists
python3 -c "import kaggle" 2>/dev/null || pip install -q kaggle 2>&1 | tail -1

# verify tarball
if [ ! -f "$TARBALL" ]; then
  echo "[ship] FATAL: tarball missing at $TARBALL"
  ls -la "$WS" | head -30
  exit 1
fi
echo "[ship] tarball sha: $(sha256sum "$TARBALL" | head -c 16)..."

for ATTEMPT in 1 2 3; do
  echo "[ship] submit attempt $ATTEMPT at $(date -u)"
  python3 - "$TARBALL" <<'PYEOF'
import sys, json
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()
try:
    resp = api.competition_submit(
        sys.argv[1],
        "tetsu_r5_v11 adapeak2 W36A2R717",
        "kaggriculture",
    )
    print("[ship] SUBMIT OK:", resp)
    sid = getattr(resp, "submission_id", None) or getattr(resp, "id", None)
    print("[ship] submission id:", sid)
    sys.exit(0)
except Exception as e:
    body = getattr(e, "response", None)
    if body is not None:
        print("[ship] FAIL", body.status_code, body.text[:300])
    else:
        print("[ship] FAIL", type(e).__name__, str(e)[:300])
    sys.exit(1)
PYEOF
  if [ $? -eq 0 ]; then
    echo "[ship] SUCCESS at $(date -u)"
    exit 0
  fi
  sleep 90
done
echo "[ship] ALL ATTEMPTS FAILED at $(date -u)"
exit 2
