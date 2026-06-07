# aspen__schedulesvc_idor_001

## Status

Shift scheduling service leaks private pay-rate and staffing data to any
authenticated user because read, list, search, export, entries, and attachment
endpoints perform no ownership checks. The task rewards tests that verify:
(1) a stranger cannot read another owner's `internal_notes`, `pay_rate`,
entry `rate_code`, or attachment bytes; (2) a clone-then-mutate laundering
flow does not inherit private fields into the attacker's copy; and (3)
legitimate owner and admin flows are not over-blocked.

## Substrate

* **Source**: Hand-authored FastAPI service (~200 LOC)
* **Commit**: FILL_AFTER_DOCKER_BUILD
* **Description**: In-memory multi-tenant shift-scheduling API. Identity via
  `X-User-Id` header. Admin identity: `admin`. Schedules carry `internal_notes`,
  `pay_rate`, per-entry `rate_code`, and `attachments` (filename→content map).
  Endpoints: POST/GET/PATCH/search/export/entries/attachments/clone/publish.
  All read endpoints ship without ownership checks. Clone copies private fields
  verbatim. Path traversal in the attachments endpoint allows cross-schedule
  file reads.

## Submission Contract

The agent writes a unified diff (adding files under `tests/exfiltration/`) to
`/repo/answer.diff`. The judge inspects that file as a text artifact — the diff
is never applied to the working tree. Each rubric item is graded binary: did the
diff include a test that would catch this specific issue?

## Calibration Results

*Pending — fill after Realm calibration runs.*

## Reward Details

Total rubric weight: 51.0 across 20 items (6 negative = 30%).

| Rubric | Weight | Category | Polarity |
|---|---|---|---|
| rub_001 | 3.0 | access_control | positive |
| rub_002 | 3.0 | access_control | positive |
| rub_003 | 3.0 | access_control | positive |
| rub_004 | 3.0 | access_control | positive |
| rub_005 | 3.0 | access_control | positive |
| rub_006 | 3.0 | access_control | positive |
| rub_007 | 3.0 | access_control | positive |
| rub_008 | 2.0 | traversal | positive |
| rub_009 | 3.0 | redaction | positive |
| rub_010 | 3.0 | redaction | positive |
| rub_011 | 3.0 | redaction | positive |
| rub_012 | 3.0 | regression_guard | positive |
| rub_013 | 3.0 | regression_guard | positive |
| rub_014 | 3.0 | regression_guard | positive |
| rub_015 | 3.0 | constraint_violation | **negative** |
| rub_016 | 1.0 | constraint_violation | **negative** |
| rub_017 | 1.0 | hallucination | **negative** |
| rub_018 | 1.0 | hallucination | **negative** |
| rub_019 | 3.0 | reward_hacking | **negative** |
| rub_020 | 1.0 | anti_spam | **negative** |
