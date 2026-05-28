#!/usr/bin/env bash
set -uo pipefail

mkdir -p /logs/artifacts /logs/verifier

TEST_LOG=$(mktemp /tmp/aspen-verifier.XXXXXX.log)
export TEST_LOG

cleanup_and_reward() {
    local rc=$?
    if [ -f /logs/verifier/reward.json ] || [ -f /logs/verifier/reward.txt ]; then
        exit "$rc"
    fi
    python3 - "$rc" "$TEST_LOG" <<'PY' >/logs/verifier/reward.json 2>/dev/null || \
        echo '{"score":0.0}' > /logs/verifier/reward.json
import json, sys
rc = int(sys.argv[1])
log_path = sys.argv[2] if len(sys.argv) > 2 else ""
tail = ""
try:
    with open(log_path, "r", errors="replace") as f:
        tail = f.read()[-4000:]
except Exception:
    tail = ""
json.dump({"score": 0.0, "error": f"verifier early-exit rc={rc}", "diagnostic_log": tail}, sys.stdout)
PY
    exit "$rc"
}
trap cleanup_and_reward EXIT

cp -f "/repo/answer.diff" /logs/artifacts/answer.diff 2>/dev/null || true
cp -f "/repo/notes.md" /logs/artifacts/notes.md 2>/dev/null || true

uvx --python 3.13 --from 'harbor-rewardkit[all]' rewardkit /tests --max-concurrent-agent 1 \
    > >(tee -a "$TEST_LOG") 2> >(tee -a "$TEST_LOG" >&2)
