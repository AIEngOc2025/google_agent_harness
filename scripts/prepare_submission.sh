#!/usr/bin/env bash

# ------------------------------------------------------------
# prepare_submission.sh – automate the final packaging steps
# ------------------------------------------------------------

# 1. Clean up invalid submodule reference if present
if git ls-files --stage competition_kit | grep -q "competition_kit"; then
  git rm --cached competition_kit 2>/dev/null || true
fi

# 2. Commit any untracked or modified files (kit check tests the current git commit)
git add .
git commit -m "prepare: update harness and submission package" || true

# 2. Verify repository integrity with the official kit check
uv run python -m kit check . --no-smoke --env-file env.txt
if [ $? -ne 0 ]; then
  echo "[ERROR] kit check failed. Resolve issues before proceeding."
  exit 1
fi

# 3. Verify artifacts
uv run python -m kit artifacts .
if [ $? -ne 0 ]; then
  echo "[ERROR] kit artifacts validation failed. Check artifacts/ content."
  exit 1
fi

# 4. Push to remote repository
git push

echo "[INFO] Submission package prepared and pushed. Ready for Kaggle upload."

