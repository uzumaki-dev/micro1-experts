# aspen__workordersvc_idor_001

**Scenario:** IDOR — work order management service leaks private data (internal_notes, labor_code, documents) to any authenticated user due to missing ownership checks on read/list/search/export/entries/documents endpoints.

**Substrate:** Hand-authored FastAPI service (~400 LOC). Auth via `X-User-Id` header. Admin identity: `admin`.

**Rubric:** 20 items — 7 access_control, 1 traversal, 2 redaction, 3 regression_guard, 1 test_quality, 6 negative (30%).

## Calibration

| Model | Score | Runs |
|-------|-------|------|
| Claude Opus 4.7 | TBD | — |
| Qwen 3.5 | TBD | — |

Target: Opus ≥ 80%, Qwen 25–50%.
