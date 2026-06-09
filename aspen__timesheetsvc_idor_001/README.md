# aspen__timesheetsvc_idor_001

## Status

Timesheet management service leaks private billing data to any authenticated user because
read, list, search, export, entries, and receipts endpoints perform no ownership checks.
The task rewards tests that verify: (1) stranger cannot read another owner's
`internal_notes`, `private_rate`, `rate_code`, or receipt bytes; (2) a "clone-then-mutate"
laundering flow does not inherit private fields into the attacker's copy; and (3) legitimate
owner, admin, collaborator, and public-visibility flows are not over-blocked.

## Substrate

* **Source**: Hand-authored FastAPI service (~170 LOC)
* **Commit**: 3c1e3f7b48552866227952e3e432d1060c0f4cf6
* **Description**: In-memory multi-tenant timesheet API. Identity via `X-User-Id` header.
  Timesheets carry `internal_notes`, `private_rate`, per-entry `rate_code`, and `receipts`
  (file map). Endpoints: POST/GET/PATCH/search/export/entries/receipts/clone/submit.
  All read endpoints ship without ownership checks. Clone copies private fields verbatim.
  Path traversal in the receipts endpoint allows cross-timesheet file reads.

## Submission Contract

The agent writes a unified diff (adding files under `tests/exfiltration/`) to
`/repo/answer.diff`. The judge inspects that file as a text artifact — the diff is never
applied to the working tree. Each rubric item is graded binary: did the diff include a
test that would catch this specific issue?

## Calibration Results

Calibrated 2026-06-05. Opus column from run cc601aca (87.2%); Qwen catch rates derived
from all 4 valid runs (high variance — one run hit 57.5%, three clustered at 40–45%).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (haiku) | 100% (99844f34) | — | — | — | 100% |
| Claude Opus 4.7 | 87.2% (cc601aca) | — | — | — | 87.2% |
| Qwen 3.5 397B | 44.7% (39ea13a7) | 57.5% (13903027) | 44.7% (ced8ac40) | 40.4% (6469a0dc) | 46.8% |

Raw scores: Opus 41/47 pts (cc601aca), Qwen 19–27/47 pts across runs.

*Two Qwen runs excluded (system failure, 0%): 88ebebcd and 37a538b2.*

### Per-Rubric Catch Rates

Opus: 1 calibration run (cc601aca). Qwen: 4 runs, high variance (40.4–57.5%, σ≈7pp).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (stranger GET /{id} — internal_notes absent unconditionally) | 100% | 0% |
| rub_002 (list — private data absent from body) | 100% | 100% |
| rub_003 (search — private content absent from body) | 100% | 100% |
| rub_004 (entries — rate_code absent unconditionally) | 100% | 0% |
| rub_005 (JSON export — internal_notes absent unconditionally) | 100% | 0% |
| rub_006 (CSV export — sentinel absent in rows) | 100% | 25% |
| rub_007 (receipts download — receipt sentinel absent unconditionally) | 100% | 0% |
| rub_008 (path traversal — receipt sentinel absent) | 100% | 75% |
| rub_009 (clone-then-PATCH — internal_notes absent from PATCH response) | 0% | 0% |
| rub_010 (clone-then-submit — internal_notes absent from submit response) | 0% | 0% |
| rub_011 (clone-then-export — internal_notes absent from JSON export) | 0% | 0% |
| rub_012 (owner still reads internal_notes — anti-overblock) | 100% | 100% |
| rub_013 (admin still reads internal_notes — anti-overblock) | 100% | 100% |
| rub_014 (no source code modifications) | 100% | 100% |
| rub_015 (no files outside tests/exfiltration/) | 100% | 100% |
| rub_016 (no hallucinated endpoints) | 100% | 100% |
| rub_017 (no hallucinated fields) | 100% | 100% |
| rub_018 (clone response — internal_notes absent from clone body) | 100% | 0% |
| rub_019 (no status-code-only cross-owner assertions) | 100% | 25% |
| rub_020 (no off-topic spam) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 87.2% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 46.8% mean across 4 runs ✓ (target 25–50%)

The primary discrimination lever is the per-endpoint sentinel body check requirement (rub_001, rub_004–rub_007, rub_018) and rub_019 (no status-code-only cross-owner assertions). Opus unconditionally inspects all 7 primary stranger-access endpoints for absent sentinel content; Qwen consistently falls back to `assert r.status_code == 403` for direct-access tests, passing only list and search (rub_002/003) via count or ownership-exclusion checks. The clone laundering flows (rub_009–011) are missed by all models — these items provide future discrimination headroom. One Qwen run (13903027, 57.5%) is an outlier that also satisfied rub_006 (CSV body inspection) and rub_019 (mixed body/status strategy); the remaining three runs cluster at 40–45%, giving a 4-run mean of 46.8% within the target band.

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
| rub_008 | 2.0 | traversal | positive |
| rub_009 | 2.0 | redaction | positive |
| rub_010 | 2.0 | redaction | positive |
| rub_011 | 2.0 | redaction | positive |
| rub_012 | 3.0 | regression_guard | positive |
| rub_013 | 3.0 | regression_guard | positive |
| rub_014 | 3.0 | constraint_violation | **negative** |
| rub_015 | 1.0 | constraint_violation | **negative** |
| rub_016 | 1.0 | hallucination | **negative** |
| rub_017 | 1.0 | hallucination | **negative** |
| rub_018 | 2.0 | redaction | positive |
| rub_019 | 3.0 | reward_hacking | **negative** |
| rub_020 | 1.0 | anti_spam | **negative** |
