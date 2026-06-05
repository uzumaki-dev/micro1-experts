# aspen__contractsvc_idor_001

## Status

This task rewards tests that verify private contract data (internal notes, clause
rate cards, and document content) is not accessible to unauthorized callers.
The substrate ships with IDOR bugs across all contract read endpoints and a
duplicate-laundering bug that copies private fields into cloned contracts.

## Substrate

* **Source**: Hand-authored
* **Commit**: (base_commit from task.toml)
* **Description**: Small FastAPI contract management service with roles: Admin,
  Owner, Counterparty. Authentication is simulated via `X-User-Id` header.

## Submission Contract

The agent writes a unified diff (adding new test files) to `/repo/answer.diff`.
The judge inspects that file as a text artifact — the diff is never applied to
the working tree. Each rubric item is graded binary.

## Final Calibration Results

Rubric updated after initial runs: rub_002/rub_003 tightened to require raw `sentinel not in r.text` checks; rub_019 upgraded to a body-inspection gate (weight 3.0). Scores below are pre-update; re-run pending.

| model | run id | reward | mean | verdict |
|---|---|---:|---:|---|
| micro1/oracle | local | ~1.00 | ~1.00 | ✓ |
| anthropic/claude-opus-4-7 | 3edc9e59 | 86.4% | 86.4% | ✓ (≥80%) |
| openrouter/qwen/qwen3.5 | 0180ec36 | 52.3% | | |
| openrouter/qwen/qwen3.5 | 4eb0fa34 | 59.1% | | |
| openrouter/qwen/qwen3.5 | b268e850 | 61.4% | | |
| openrouter/qwen/qwen3.5 | 521e5336 | 54.6% | 56.9% | ✗ (>50%, rubric tightened) |

**Discrimination Verdict**: Post-update re-run required. Pre-update Qwen mean 56.9% (above 50% ceiling); rubric tightened to target ~38-43%.

## Per-Rubric Catch Rates (pre-update, 3 evaluated runs)

| Rubric | Weight | Category | Opus | Qwen b268 | Qwen 521e | Catch % |
|---|---|---|---|---|---|---|
| rub_001 | 3.0 | access_control | ✓ | ✗ | ✓ | 67% |
| rub_002 | 3.0 | access_control | ✓ | ✓ | ✓ | 100% |
| rub_003 | 3.0 | access_control | ✓ | ✓ | ✓ | 100% |
| rub_004 | 3.0 | access_control | ✓ | ✗ | ✗ | 33% |
| rub_005 | 3.0 | access_control | ✓ | ✗ | ✗ | 33% |
| rub_006 | 3.0 | access_control | ✓ | ✓ | ✓ | 100% |
| rub_007 | 3.0 | access_control | ✓ | ✓ | ✗ | 67% |
| rub_008 | 2.0 | traversal | ✓ | ✗ | ✗ | 33% |
| rub_009 | 3.0 | redaction | ✗ | ✗ | ✗ | 0% |
| rub_010 | 3.0 | redaction | ✗ | ✗ | ✗ | 0% |
| rub_011 | 3.0 | regression_guard | ✓ | ✓ | ✓ | 100% |
| rub_012 | 3.0 | regression_guard | ✓ | ✓ | ✓ | 100% |
| rub_013 | 3.0 | regression_guard | ✓ | ✓ | ✗ | 67% |
| rub_014 | 1.0 | constraint_violation (−) | ✓ | ✓ | ✓ | 100% |
| rub_015 | 1.0 | constraint_violation (−) | ✓ | ✓ | ✓ | 100% |
| rub_016 | 1.0 | hallucination (−) | ✓ | ✓ | ✓ | 100% |
| rub_017 | 1.0 | anti_spam (−) | ✓ | ✓ | ✓ | 100% |
| rub_018 | 1.0 | reward_hacking (−) | ✓ | ✓ | ✓ | 100% |
| rub_019 | 3.0 | reward_hacking (−, updated) | — | — | — | pending |

## Reward Details

Total rubric weight is 46 across 19 items (rub_019 upgraded from 1.0 to 3.0).

| Rubric | Weight | Category |
|---|---|---|
| rub_001 | 3.0 | access_control |
| rub_002 | 3.0 | access_control |
| rub_003 | 3.0 | access_control |
| rub_004 | 3.0 | access_control |
| rub_005 | 3.0 | access_control |
| rub_006 | 3.0 | access_control |
| rub_007 | 3.0 | access_control |
| rub_008 | 2.0 | traversal |
| rub_009 | 3.0 | redaction |
| rub_010 | 3.0 | redaction |
| rub_011 | 3.0 | regression_guard |
| rub_012 | 3.0 | regression_guard |
| rub_013 | 3.0 | regression_guard |
| rub_014 | 1.0 | constraint_violation (Negative) |
| rub_015 | 1.0 | constraint_violation (Negative) |
| rub_016 | 1.0 | hallucination (Negative) |
| rub_017 | 1.0 | anti_spam (Negative) |
| rub_018 | 1.0 | reward_hacking (Negative) |
| rub_019 | 3.0 | reward_hacking (Negative) |
