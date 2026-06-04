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

| model | runs | rewards | mean | verdict |
|---|---:|---|---:|---|
| micro1/oracle | 1 | TBD | TBD | pending |
| anthropic/claude-opus-4-7 | 1 | TBD | TBD | pending |
| openrouter/qwen/qwen3.5 | 4 | TBD | TBD | pending |

**Discrimination Verdict**: Pending calibration.

## Reward Details

Total rubric weight is 44 across 19 items.

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
| rub_019 | 1.0 | reward_hacking (Negative) |
