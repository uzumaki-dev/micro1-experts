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
    echo '{"reward":0.0}' > /logs/verifier/reward.json 2>/dev/null || true
    exit "$rc"
}
trap cleanup_and_reward EXIT

cp -f "/repo/answer.diff" /logs/artifacts/answer.diff 2>/dev/null || true
cp -f "/repo/notes.md" /logs/artifacts/notes.md 2>/dev/null || true

uvx --python 3.13 --from 'harbor-rewardkit[all]' rewardkit /tests/review --max-concurrent-agent 1 \
    > >(tee -a "$TEST_LOG") 2> >(tee -a "$TEST_LOG" >&2)
