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

Calibrated 2026-06-08. Three 0% runs (b1e9b3fb Opus, d46430d2 and 0e97ef8e Qwen) excluded —
judge exited with `error_max_structured_output_retries` before writing scores.
Opus column from run de9723eb (82.4%); Qwen catch rates derived from 4 valid runs.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% (86016f83) | — | — | — | 100% |
| Claude Opus 4.7 | 82.4% (de9723eb) | — | — | — | 82.4% |
| Qwen 3.5 397B | 37.3% (07bc2ce4) | 41.2% (02b410d8) | 43.1% (3267973a) | 43.1% (7bcc658b) | 41.2% |

Raw scores: Opus 42/51 pts (de9723eb), Qwen ~21/51 pts mean.

### Per-Rubric Catch Rates

Opus: 1 calibration run (de9723eb). Qwen: 4 runs; catch rate = fraction of runs scoring 1 per item.

| Criterion | Opus 4.7 | Qwen 3.5 (4 runs) |
|-----------|----------|-------------------|
| rub_001 (GET /{id} internal_notes sentinel) | 100% | 0% |
| rub_002 (list internal_notes/rate_code sentinel) | 100% | 50% |
| rub_003 (search sentinel — internal_notes leak) | 100% | 100% |
| rub_004 (entries rate_code sentinel) | 100% | 0% |
| rub_005 (export JSON internal_notes sentinel) | 100% | 0% |
| rub_006 (export CSV sentinel) | 100% | 0% |
| rub_007 (attachment download sentinel) | 100% | 0% |
| rub_008 (path traversal attachment sentinel) | 100% | 25% |
| rub_009 (clone→PATCH internal_notes absent) | 0% | 0% |
| rub_010 (clone→publish internal_notes absent) | 0% | 0% |
| rub_011 (clone→export sentinel absent) | 0% | 0% |
| rub_012 (owner still reads internal_notes — guard) | 100% | 100% |
| rub_013 (admin still reads internal_notes — guard) | 100% | 100% |
| rub_014 (non-admin create + list own — guard) | 100% | 100% |
| rub_015 (no schedulesvc/ modifications) | 100% | 100% |
| rub_016 (files only under tests/exfiltration/) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no hallucinated model fields) | 100% | 100% |
| rub_019 (no status-code-only cross-owner assertions) | 100% | 0% |
| rub_020 (no off-topic spam) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 82.4% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 41.2% mean across 4 runs ✓ (target 25–50%, range 37.3–43.1%)

The gap is driven by rub_001/rub_004–007 (sentinel-absence checks on direct read/entries/export/attachment
surfaces — Qwen writes status-code-only assertions on all of these and fails them all) and rub_019
(reward_hacking, weight 3.0 — Qwen scores 0% across all runs, the single largest discrimination lever).
rub_008 (path traversal) and rub_002 (list sentinel) show partial Qwen success (25% and 50%),
contributing secondary separation. Opus consistently misses rub_009–011 (clone laundering flows,
9 pts combined) — these are the only items preventing a perfect Opus score.

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
