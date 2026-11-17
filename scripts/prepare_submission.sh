#!/usr/bin/env bash

# ------------------------------------------------------------
# prepare_submission.sh – automate the final packaging steps
# ------------------------------------------------------------

set -e

# 1. Clean up invalid submodule reference if present
if git ls-files --stage competition_kit | grep -q "competition_kit"; then
  git rm --cached competition_kit 2>/dev/null || true
fi

# 2. Start mock model proxy on port 8000 in background for local probe verification
uv run python scripts/mock_model_proxy.py 8000 &
MOCK_PID=$!
trap "kill -9 $MOCK_PID 2>/dev/null || true" EXIT
sleep 2

export MODEL_PROXY_URL="http://host.docker.internal:8000"
export MODEL_PROXY_KEY="dummykey"

# 3. Commit any untracked or modified files
git add .
git commit -m "prepare: update harness and submission package" || true

# 4. Verify repository integrity with the official kit check
uv run python -m kit check . --no-smoke
if [ $? -ne 0 ]; then
  echo "[ERROR] kit check failed. Resolve issues before proceeding."
  exit 1
fi

# 5. Verify artifacts
uv run python -m kit artifacts .
if [ $? -ne 0 ]; then
  echo "[ERROR] kit artifacts validation failed. Check artifacts/ content."
  exit 1
fi

# 6. Push to remote repository
git push

echo "[INFO] Submission package prepared and pushed. Ready for Kaggle upload."
