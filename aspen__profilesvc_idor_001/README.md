# aspen__profilesvc_idor_001

## Status

This task rewards tests that verify private profile data (confidential HR summary notes,
salary history in experience entries, and private documents) is not exposed to unauthorized
callers across seven distinct read surfaces plus a fork-laundering vector. Tests must fail
on the current buggy code and pass on a correct fix, while also asserting that legitimate
owner and admin flows are not over-blocked.

## Substrate

* **Source**: Hand-authored
* **Commit**: FILL_AFTER_DOCKER_BUILD
* **Description**: Small FastAPI service (`profilesvc`) with an in-memory store. Users own
  their profiles; the `admin` user is privileged. Profiles carry a `private_summary` field
  and experience entries with a `salary_band` field — both private. The shipped code has no
  ownership checks on any read, list, search, export, experience, document, or fork endpoint.

## Submission Contract

The agent writes a unified diff (adding new test files) to `/repo/answer.diff`. The judge
inspects that file as a text artifact — the diff is never applied to the working tree. Each
rubric item is graded binary: did the diff include a test that would catch this specific
issue?

## Final Calibration Results

| model | runs | rewards | mean | verdict |
|---|---:|---|---:|---|
| micro1/oracle | 1 | — | — | pending |
| anthropic/claude-opus-4-7 | — | — | — | pending |
| openrouter/qwen/qwen3.5 | — | — | — | pending |

**Discrimination Verdict**: Pending calibration.

## Reward Details

Total rubric weight: 47.0 across 20 items.

| Rubric | Weight | Category |
|---|---|---|
| rub_001 | 3.0 | access_control |
| rub_002 | 3.0 | access_control |
| rub_003 | 3.0 | access_control |
| rub_004 | 3.0 | access_control |
| rub_005 | 3.0 | access_control |
| rub_006 | 3.0 | access_control |
| rub_007 | 3.0 | ownership |
| rub_008 | 2.0 | traversal |
| rub_009 | 3.0 | redaction |
| rub_010 | 2.0 | regression_guard |
| rub_011 | 3.0 | redaction |
| rub_012 | 3.0 | regression_guard |
| rub_013 | 3.0 | regression_guard |
| rub_014 | 3.0 | regression_guard |
| rub_015 | 2.0 | constraint_violation (Negative) |
| rub_016 | 1.0 | reward_hacking (Negative) |
| rub_017 | 1.0 | hallucination (Negative) |
| rub_018 | 1.0 | anti_spam (Negative) |
| rub_019 | 1.0 | constraint_violation (Negative) |
| rub_020 | 1.0 | reward_hacking (Negative) |

## Verdict Details

- Opus score >= 80%: pending
- All four Qwen runs in 25-50%: pending
- Final: PENDING
