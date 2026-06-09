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

Calibrated 2026-06-10. Opus column from run 0f1287a3 (83.0%); Qwen catch rates derived
from all 4 valid runs (moderate variance — 40.4–53.2%, σ≈5pp).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (haiku) | 100% (2e8a0760) | — | — | — | 100% |
| Claude Opus 4.7 | 83.0% (0f1287a3) | — | — | — | 83.0% |
| Qwen 3.5 397B | 46.8% (70134dd1) | 53.2% (330bd303) | 40.4% (99c4c9cf) | 40.4% (48e19aba) | 45.2% |

Raw scores: Opus 39/47 pts (0f1287a3), Qwen 19–25/47 pts across valid runs.

*One Qwen run excluded (system failure, 0%): f7834ee1.*

### Per-Rubric Catch Rates

Opus: 1 calibration run (0f1287a3). Qwen: 4 valid runs, moderate variance (40.4–53.2%, σ≈5pp).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (stranger GET /{id} — internal_notes absent unconditionally) | 100% | 0% |
| rub_002 (list — private data absent from body) | 100% | 100% |
| rub_003 (search — private content absent from body) | 100% | 100% |
| rub_004 (entries — rate_code absent unconditionally) | 100% | 0% |
| rub_005 (JSON export — internal_notes absent unconditionally) | 100% | 0% |
| rub_006 (CSV export — sentinel absent in rows) | 100% | 25% |
| rub_007 (receipts download — receipt sentinel absent unconditionally) | 100% | 0% |
| rub_008 (path traversal — receipt sentinel absent) | 100% | 0% |
| rub_009 (clone-then-PATCH — internal_notes absent from PATCH response) | 0% | 0% |
| rub_010 (clone-then-submit — internal_notes absent from submit response) | 0% | 0% |
| rub_011 (clone-then-export — internal_notes absent from JSON export) | 0% | 0% |
| rub_012 (owner still reads internal_notes — anti-overblock) | 100% | 100% |
| rub_013 (admin still reads internal_notes — anti-overblock) | 100% | 100% |
| rub_014 (no source code modifications) | 100% | 100% |
| rub_015 (no files outside tests/exfiltration/) | 100% | 100% |
| rub_016 (no hallucinated endpoints) | 100% | 100% |
| rub_017 (no hallucinated fields) | 100% | 100% |
| rub_018 (clone response — internal_notes absent from clone body) | 0% | 0% |
| rub_019 (no status-code-only cross-owner assertions) | 100% | 50% |
| rub_020 (no off-topic spam) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 83.0% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 45.2% mean across 4 valid runs ✓ (target 25–50%)

The primary discrimination lever is rub_001, rub_004–rub_007 (unconditional sentinel body checks on each stranger-access endpoint) and rub_019 (no status-code-only cross-owner assertions). Opus seeds a sentinel into every private field and verifies its absence unconditionally from all 7 direct-access responses; Qwen consistently falls back to `assert r.status_code == 403` for single-object access (GET /{id}, /entries, /export json, /receipts), passing only list (rub_002) and search (rub_003) via count/ownership-exclusion body checks. Two of four Qwen runs also triggered rub_019 (reward_hacking), losing 3 additional weight points each. The clone laundering flows (rub_009–011, rub_018) and path traversal (rub_008) are now missed by all models, providing future headroom. One Qwen run (f7834ee1, 0%) was a system failure and excluded.

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
