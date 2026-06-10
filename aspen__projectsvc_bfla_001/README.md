# aspen__projectsvc_bfla_001

## Status

Project management service allows any project member to invoke admin-only endpoints
(delete, archive, member management, audit-log) because role checks are absent — only
membership is verified. The task rewards tests that verify: (1) non-admin roles (viewer,
editor) are rejected from destructive and management operations; (2) the `private_reason`
sentinel in `AuditEvent` is inaccessible to non-admins; (3) a self-promotion laundering
flow cannot unlock elevated operations; and (4) legitimate admin operations are not
over-blocked.

## Substrate

* **Source**: Hand-authored FastAPI service (in-memory project management API)
* **Commit**: 055a376d90c8d7e2d80ee062060a4505960a540c
* **Description**: In-memory multi-tenant project management API. Identity via `X-User-Id`
  header. Roles per-project: viewer, editor, admin (stored in members dict). Endpoints
  include project CRUD, archive, member add/remove/role-change, and audit-log read.
  All privileged endpoints check only membership, not role, so any project member can
  perform admin-only actions. AuditEvent carries `private_reason` seeded as
  `"ZZ-PRIV-REASON-bfla-7x3z"`.

## Submission Contract

The agent writes a unified diff (adding files under `tests/exfiltration/`) to
`/repo/answer.diff`. The judge inspects that file as a text artifact — the diff is never
applied to the working tree. Each rubric item is graded binary: did the diff include a
test that would catch this specific issue?

## Calibration Results

Calibration pending — run rv oracle and rv run to populate.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (haiku) | TBD | — | — | — | TBD |
| Claude Opus 4.7 | TBD | — | — | — | TBD |
| Qwen 3.5 397B | TBD | TBD | TBD | TBD | TBD |

Raw scores: Opus TBD/47 pts, Qwen TBD–TBD/47 pts across valid runs.

### Per-Rubric Catch Rates

Opus: TBD calibration runs. Qwen: TBD valid runs.

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (viewer DELETE rejected AND project still exists) | TBD | TBD |
| rub_002 (editor DELETE rejected AND project still exists) | TBD | TBD |
| rub_003 (viewer archive rejected AND is_archived still false) | TBD | TBD |
| rub_004 (viewer add-member rejected AND member count unchanged) | TBD | TBD |
| rub_005 (viewer change-role rejected AND target role unchanged) | TBD | TBD |
| rub_006 (viewer remove-member rejected AND member still present) | TBD | TBD |
| rub_007 (non-admin audit-log — private_reason sentinel absent from body) | TBD | TBD |
| rub_008 (self-promote laundering — viewer role unchanged AND DELETE still fails) | TBD | TBD |
| rub_009 (admin CAN delete project) | TBD | TBD |
| rub_010 (admin CAN archive — is_archived true after) | TBD | TBD |
| rub_011 (admin CAN add member — appears in GET) | TBD | TBD |
| rub_012 (admin CAN change member role — reflected in GET) | TBD | TBD |
| rub_013 (admin CAN read audit-log — sentinel present in body) | TBD | TBD |
| rub_014 (tests seed sentinel, sweep audit-log, verify state after rejected op) | TBD | TBD |
| rub_015 (no modifications to projectsvc/ source files) | TBD | TBD |
| rub_016 (no test files outside tests/exfiltration/) | TBD | TBD |
| rub_017 (no references to endpoints not in substrate) | TBD | TBD |
| rub_018 (no references to fields not in substrate models) | TBD | TBD |
| rub_019 (no vacuous pass/assert True test bodies) | TBD | TBD |
| rub_020 (no bare except blocks swallowing assertion errors) | TBD | TBD |

## Discrimination Verdict

**PENDING**

- Oracle: TBD
- Opus 4.7: TBD (target ≥80%)
- Qwen 3.5 397B: TBD mean (target 25–50%)

## Reward Details

Total rubric weight: 47.0 across 20 items (6 negative = 30%).

| Rubric | Weight | Category | Polarity |
|---|---|---|---|
| rub_001 | 3.0 | access_control | positive |
| rub_002 | 3.0 | access_control | positive |
| rub_003 | 3.0 | access_control | positive |
| rub_004 | 3.0 | access_control | positive |
| rub_005 | 3.0 | access_control | positive |
| rub_006 | 3.0 | access_control | positive |
| rub_007 | 3.0 | access_control | positive |
| rub_008 | 2.0 | redaction | positive |
| rub_009 | 3.0 | regression_guard | positive |
| rub_010 | 3.0 | regression_guard | positive |
| rub_011 | 3.0 | regression_guard | positive |
| rub_012 | 3.0 | regression_guard | positive |
| rub_013 | 3.0 | regression_guard | positive |
| rub_014 | 1.0 | test_quality | positive |
| rub_015 | 3.0 | constraint_violation | **negative** |
| rub_016 | 1.0 | constraint_violation | **negative** |
| rub_017 | 1.0 | hallucination | **negative** |
| rub_018 | 1.0 | hallucination | **negative** |
| rub_019 | 1.0 | reward_hacking | **negative** |
| rub_020 | 1.0 | anti_spam | **negative** |
