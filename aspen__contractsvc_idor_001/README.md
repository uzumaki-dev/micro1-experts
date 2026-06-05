# aspen__contractsvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI contract management service. Private `internal_notes` and
clause `rate_card` fields leak to any authenticated caller across 9 distinct surfaces:
direct GET, list, search, clauses endpoint, JSON export, PDF export, document download,
path traversal, and duplicate-laundering flows (clone→PATCH and clone→sign).

Rubric: 19 items, total weight 46.
- rub_001–007: direct-coverage sentinel checks on 7 stranger-access endpoints (weight 3 each = 21 pts)
- rub_008: path-traversal sentinel check (weight 2)
- rub_009–010: duplicate-laundering flows — clone→PATCH and clone→sign (weight 3 each = 6 pts)
- rub_011–013: Regression_guard anti-overblock items (weight 3 each = 9 pts)
- rub_014–018: negative criteria — constraint_violation, hallucination, anti_spam, reward_hacking (weight 1 each = 5 pts)
- rub_019: body-inspection gate — requires ≥5 of 7 primary endpoints use sentinel body checks, not status-code-only (weight 3)

All direct-coverage items (rub_001–010) require sentinel-based content inspection;
status-code-only assertions do not satisfy them.

## Calibration Results

Calibrated 2026-06-05. Rubric tightened after pre-fix runs (rub_002/003 tightened; rub_019
upgraded to body-inspection gate weight 3.0). Results below are post-fix.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 87.0% (5b91fbbd) | — | — | — | 87.0% |
| Qwen 3.5 397B | 30.4% (9badf6b3) | 23.9% (7d94afe7) | 30.4% (ae9ca95e) | 30.4% (ea851f26) | 28.8% |

Raw scores: Opus 40/46 pts (5b91fbbd), Qwen representative 14/46 pts (9badf6b3).

### Per-Rubric Catch Rates

Opus: 1 calibration run (5b91fbbd). Qwen: 4 runs; rates computed across all 4.

| Criterion | Opus 4.7 | Qwen 3.5 (4 runs) |
|-----------|----------|-------------------|
| rub_001 (GET /{id} internal_notes sentinel) | 100% | 0% |
| rub_002 (list endpoint sentinel) | 100% | 0% |
| rub_003 (search endpoint sentinel) | 100% | 0% |
| rub_004 (clauses rate_card sentinel) | 100% | 0% |
| rub_005 (export json sentinel) | 100% | 0% |
| rub_006 (export pdf sentinel) | 100% | 0% |
| rub_007 (documents download sentinel) | 100% | 0% |
| rub_008 (path traversal sentinel) | 100% | 0% |
| rub_009 (duplicate→PATCH laundering) | 0% | 0% |
| rub_010 (duplicate→sign laundering) | 0% | 0% |
| rub_011 (owner access guard) | 100% | 100% |
| rub_012 (admin access guard) | 100% | 100% |
| rub_013 (user create+list guard) | 100% | 75% |
| rub_014 (no contractsvc/ modifications) | 100% | 100% |
| rub_015 (no files outside exfiltration/) | 100% | 100% |
| rub_016 (no hallucinated endpoints) | 100% | 100% |
| rub_017 (no duplicate assertion spam) | 100% | 100% |
| rub_018 (no vacuous assertions) | 100% | 100% |
| rub_019 (body-inspection gate) | 100% | 0% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 87.0% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 28.8% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001–008 (sentinel-absence checks across all leak surfaces) and
rub_019 (body-inspection gate) — Qwen consistently uses status-code-only (403) or
count/length assertions and fails all nine. Opus misses only rub_009–010 (duplicate-
laundering flows, weight 3 each = 6 pts), accounting for its 6/46 lost points.
