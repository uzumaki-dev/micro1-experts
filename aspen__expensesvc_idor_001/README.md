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

Calibrated 2026-05-31. Qwen scores vary run-to-run (model is not deterministic).
Catch rates computed from 4 Qwen runs: 3 runs at 43.8% (21/48 pts) and 1 run at 27.1%
(13/48 pts).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% (5cbd119b) | — | — | — | 100% |
| Claude Opus 4.7 | 81.3% (f147650d) | — | — | — | 81.3% |
| Qwen 3.5 397B | 43.8% (032bc7a2) | 43.8% (40902aa1) | 27.1% (fffb71e5) | 43.8% (0c20d732) | 39.6% |

Raw scores: Opus 39/48 pts (f147650d), Qwen 21/48 pts (032bc7a2).

### Per-Rubric Catch Rates

Opus: 1 calibration run (f147650d). Qwen: 4 calibration runs; 3 runs at 43.8%
(pass rub_002, rub_003, rub_008, rub_012–016), 1 run at 27.1% (passes rub_012–016 only).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /expenses/{id} — sentinel check) | 100% | 0% |
| rub_002 (list — sentinel check) | 100% | 75% |
| rub_003 (search — sentinel check) | 100% | 75% |
| rub_004 (line-items — sentinel check) | 100% | 0% |
| rub_005 (export json — sentinel check) | 100% | 0% |
| rub_006 (export csv — sentinel check) | 100% | 0% |
| rub_007 (receipt download — sentinel check) | 100% | 0% |
| rub_008 (path traversal — sentinel check) | 100% | 75% |
| rub_009 (clone→PATCH laundering) | 0% | 0% |
| rub_010 (clone→submit laundering) | 0% | 0% |
| rub_011 (clone→export laundering) | 0% | 0% |
| rub_012 (owner still sees own expense — guard) | 100% | 100% |
| rub_013 (admin still sees expense — guard) | 100% | 100% |
| rub_014 (collaborator still sees expense — guard) | 100% | 100% |
| rub_015 (public expense accessible to stranger — guard) | 100% | 100% |
| rub_016 (user can create + list own expenses — guard) | 100% | 100% |
| rub_017 (sentinel sweep across all surfaces) | 100% | 0% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 81.3% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 39.6% mean across 4 runs ✓ (target 25–50%)

The gap is driven by the five sentinel-inspection items (rub_001, rub_004–007) plus the
sentinel sweep (rub_017) — Qwen writes status-code-only assertions on these and fails all
six. Both models miss the three laundering flows (rub_009–011), the non-obvious chained
surfaces; these account for Opus's 9 lost points (39/48).
