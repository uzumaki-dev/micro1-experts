# aspen__expensesvc_idor_001 — Calibration Report

## Task Summary

IDOR vulnerability in an expense management FastAPI service. The agent must write
tests that catch private expense data leaking to unauthorized users across multiple
endpoints, while preserving legitimate access flows.

## Rubric

17 binary criteria, total weight 48.

| Category | Items | Weight |
|----------|-------|--------|
| access_control | rub_001–rub_007 | 21 |
| traversal | rub_008 | 2 |
| redaction (laundering) | rub_009–rub_011 | 9 |
| regression_guard | rub_012–rub_016 | 13 |
| test_quality | rub_017 | 3 |

## Calibration Results

| Model | Score | Status |
|-------|-------|--------|
| Claude Opus 4.7 | TBD | Target ≥ 80% |
| Qwen 3.5 | TBD | Target 25–50% |
| Oracle | 1.0 | Baseline |

_Fill after first calibration run._
