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

Calibrated 2026-05-31. Opus column from the 81.3% run (f147650d); Qwen 4-run average
shown — scores vary run-to-run (Qwen is not deterministic on this task).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Claude Opus 4.7 | 81.3% | — | — | — | 81.3% |
| Qwen 3.5 397B | 43.8% | 43.8% | 27.1% | 43.8% | 39.6% |

Raw scores: Opus 39/48 pts (f147650d), Qwen 21/48 pts (032bc7a2). Oracle: 1.0.

### Per-Rubric Catch Rates

Opus column from run f147650d (81.3%); Qwen column from run 032bc7a2 (43.8%).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /expenses/{id} — sentinel req.) | ✓ | ✗ |
| rub_002 (list) | ✓ | ✓ |
| rub_003 (search) | ✓ | ✓ |
| rub_004 (line-items — sentinel req.) | ✓ | ✗ |
| rub_005 (export json — sentinel req.) | ✓ | ✗ |
| rub_006 (export csv — sentinel req.) | ✓ | ✗ |
| rub_007 (receipt download — sentinel req.) | ✓ | ✗ |
| rub_008 (path traversal — sentinel req.) | ✓ | ✓ |
| rub_009 (clone+PATCH laundering) | ✗ | ✗ |
| rub_010 (clone+submit laundering) | ✗ | ✗ |
| rub_011 (clone+export laundering) | ✗ | ✗ |
| rub_012 (owner overblock guard) | ✓ | ✓ |
| rub_013 (admin overblock guard) | ✓ | ✓ |
| rub_014 (collaborator overblock guard) | ✓ | ✓ |
| rub_015 (public expense overblock guard) | ✓ | ✓ |
| rub_016 (create+list own overblock guard) | ✓ | ✓ |
| rub_017 (sentinel sweep — w=3) | ✓ | ✗ |

## Discrimination Verdict

**DISCRIMINATIVE**

- Opus 4.7: 81.3% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 39.6% mean across 4 runs ✓ (target 25–50%)

The gap is driven by the five sentinel-inspection items (rub_001, rub_004–rub_007) plus
the sentinel sweep (rub_017) — Qwen writes status-code-only assertions on these and
fails all six. Both models miss the three laundering flows (rub_009–011), the non-obvious
chained surfaces; these account for Opus's 9 lost points (39/48).
