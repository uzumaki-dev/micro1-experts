# aspen__contractsvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI contract management service. Private `internal_notes` and
clause `rate_card` fields leak to any authenticated caller across 9 distinct surfaces:
direct GET, list, search, clauses endpoint, JSON export, PDF export, document download,
path traversal, and duplicate-laundering flows (clone→PATCH and clone→sign).

Rubric: 20 items, total weight 47.
- rub_001–007: direct-coverage sentinel checks on 7 stranger-access endpoints (weight 3 each = 21 pts)
- rub_008: path-traversal sentinel check (weight 2)
- rub_009–010: duplicate-laundering flows — clone→PATCH and clone→sign (weight 3 each = 6 pts)
- rub_011–013: Regression_guard anti-overblock items (weight 3 each = 9 pts)
- rub_014–018: negative criteria — constraint_violation, hallucination, anti_spam, reward_hacking (weight 1 each = 5 pts)
- rub_019: body-inspection gate — requires ≥5 of 7 primary endpoints use sentinel body checks, not status-code-only (weight 3)
- rub_020: test_quality nitpick — PDF export decoded text-layer check or owner document-download Content-Type assertion (weight 1, added during rework)

All direct-coverage items (rub_001–010) require sentinel-based content inspection;
status-code-only assertions do not satisfy them.

## Calibration Results

Recalibrated 2026-06-13 post-rework (rub_020 added; Dockerfile updated to golden base;
task.toml name prefix and base_commit corrected). Results below use the reworked rubric
(20 items, 47 pts total).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 85.1% (44d76623) | — | — | — | 85.1% |
| Qwen 3.5 397B | 29.8% (79eb6d93) | 29.8% (7bbcbf8a) | 29.8% (12703670) | 36.2% (952c9e57) | 31.4% |

Raw scores: Opus 40/47 pts (44d76623), Qwen representative 14/47 pts (79eb6d93).

### Per-Rubric Catch Rates

Opus: 1 calibration run (44d76623). Qwen: 4 runs; rates computed across all 4.

| Criterion | Opus 4.7 | Qwen 3.5 (4 runs) |
|-----------|----------|-------------------|
| rub_001 (GET /{id} internal_notes sentinel) | 100% | 0% |
| rub_002 (list endpoint sentinel) | 100% | 0% |
| rub_003 (search endpoint sentinel) | 100% | 0% |
| rub_004 (clauses rate_card sentinel) | 100% | 0% |
| rub_005 (export json sentinel) | 100% | 0% |
| rub_006 (export pdf sentinel) | 100% | 25% |
| rub_007 (documents download sentinel) | 100% | 0% |
| rub_008 (path traversal sentinel) | 100% | 0% |
| rub_009 (duplicate→PATCH laundering) | 0% | 0% |
| rub_010 (duplicate→sign laundering) | 0% | 0% |
| rub_011 (owner access guard) | 100% | 100% |
| rub_012 (admin access guard) | 100% | 100% |
| rub_013 (user create+list guard) | 100% | 100% |
| rub_014 (no contractsvc/ modifications) | 100% | 100% |
| rub_015 (no files outside exfiltration/) | 100% | 100% |
| rub_016 (no hallucinated endpoints) | 100% | 100% |
| rub_017 (no duplicate assertion spam) | 100% | 100% |
| rub_018 (no vacuous assertions) | 100% | 100% |
| rub_019 (body-inspection gate) | 100% | 0% |
| rub_020 (PDF text-layer / Content-Type rigor) | 0% | 0% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 85.1% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 31.4% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001–008 (sentinel-absence checks across all leak surfaces) and
rub_019 (body-inspection gate) — Qwen consistently uses status-code-only (403) or
count/length assertions. rub_006 is caught in 1 of 4 Qwen runs (25%) when an agent
incidentally writes an unconditional sentinel check on the PDF export. Opus misses only
rub_009–010 (duplicate-laundering flows, 6 pts) and rub_020 (test_quality nitpick, 1 pt),
accounting for its 7/47 lost points.
