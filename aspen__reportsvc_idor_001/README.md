# aspen__reportsvc_idor_001

## Task Summary

An analytics reporting FastAPI service (`reportsvc`) has an IDOR vulnerability: no
ownership checks exist on any read, list, search, export, data-points, or attachment
endpoint. Any authenticated user can read any other user's private report — including
sensitive `confidential_notes`, data-point `metric_code` fields, and attachment bytes.
The `fork` endpoint additionally inherits private fields verbatim, enabling a
laundering pattern (fork → PATCH / fork → export).

The agent must write a sentinel-based test suite covering 10 direct-coverage surfaces
and 3 anti-overblock regression guards.

## Calibration Results

Calibration pending first upload to Realm.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | — | — | — | — | — |
| Claude Opus 4.7 | — | — | — | — | — |
| Qwen 3.5 397B | — | — | — | — | — |

### Per-Rubric Catch Rates

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /reports/{id} — sentinel check) | — | — |
| rub_002 (list — sentinel check) | — | — |
| rub_003 (search — sentinel check) | — | — |
| rub_004 (data-points — sentinel check) | — | — |
| rub_005 (export json — sentinel check) | — | — |
| rub_006 (export csv — sentinel check) | — | — |
| rub_007 (attachment download — sentinel check) | — | — |
| rub_008 (path traversal — sentinel check) | — | — |
| rub_009 (fork→PATCH laundering) | — | — |
| rub_010 (fork→export laundering) | — | — |
| rub_011 (owner still sees own report — guard) | — | — |
| rub_012 (admin still sees report — guard) | — | — |
| rub_013 (user can create + list own reports — guard) | — | — |
| rub_014 (sentinel sweep across all surfaces) | — | — |
| rub_015–020 (negative criteria) | — | — |

## Discrimination Verdict

Pending calibration.

Expected: Opus ≥ 80%, Qwen 25–50% based on invoicesvc/expensesvc IDOR pattern.
Key discriminators: rub_001 / rub_004–007 (sentinel-inspection items Qwen typically
writes as status-code-only), rub_009–010 (laundering flows both models miss).
