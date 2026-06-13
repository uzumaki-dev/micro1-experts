# aspen__expensesvc_idor_001 — Calibration Report

## Task Summary

An expense management FastAPI service (`expensesvc`) has an IDOR vulnerability: no
ownership checks exist on any read, list, search, export, line-items, or receipt
endpoint. Any authenticated user can read any other user's private expense — including
sensitive `private_notes`, line-item `cost_code` fields, and receipt bytes. The
`clone` endpoint additionally inherits private fields verbatim, enabling a laundering
pattern (clone → PATCH/submit).

The agent must write a sentinel-based test suite covering 7 direct-coverage surfaces,
1 traversal check, 2 laundering flows, 1 sentinel-sweep quality check, 3 anti-overblock
regression guards, and 6 negative guards.

## Calibration Results

Calibrated 2026-06-12. Qwen scores vary run-to-run (model is not deterministic).
A fifth Qwen run (9d80cdf0) scored 0% with no reward output and is excluded as
an infrastructure failure.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 87.0% (6fc72c6b) | — | — | — | 87.0% |
| Qwen 3.5 397B | 28.3% (13173a96) | 28.3% (fb6808cb) | 28.3% (8efe6eb2) | 41.3% (1ab18c1b) | 31.5% |

Raw scores: Opus 40/46 pts (6fc72c6b), Qwen mean 14.5/46 pts across 4 runs.

### Per-Rubric Catch Rates

Opus: 1 calibration run (6fc72c6b). Qwen: 4 calibration runs; catch rates computed
across all 4 runs (0% = never caught, 100% = caught every run).

| Criterion | Weight | Category | Opus 4.7 | Qwen 3.5 |
|-----------|--------|----------|----------|----------|
| rub_001 (GET /expenses/{id} — sentinel check) | 3 | access_control | 100% | 0% |
| rub_002 (list — sentinel substring check) | 3 | access_control | 100% | 0% |
| rub_003 (search — sentinel substring check) | 3 | access_control | 100% | 25% |
| rub_004 (line-items — cost_code sentinel check) | 3 | access_control | 100% | 0% |
| rub_005 (export json — sentinel check) | 3 | access_control | 100% | 0% |
| rub_006 (export csv — both sentinels check) | 3 | access_control | 100% | 0% |
| rub_007 (receipt download — sentinel check) | 3 | access_control | 100% | 0% |
| rub_008 (path traversal — sentinel check) | 2 | traversal | 100% | 0% |
| rub_009 (clone→PATCH laundering) | 3 | redaction | 0% | 0% |
| rub_010 (clone→submit laundering) | 3 | redaction | 0% | 0% |
| rub_012 (owner still sees own expense — guard) | 3 | regression_guard | 100% | 100% |
| rub_013 (admin still sees expense — guard) | 3 | regression_guard | 100% | 100% |
| rub_016 (user creates + finds own expense by ID — guard) | 3 | regression_guard | 100% | 25% |
| rub_017 (sentinel sweep across surfaces) | 1 | test_quality | 100% | 0% |
| rub_018 (neg: no dead-code body checks) | 2 | reward_hacking | 100% | 100% |
| rub_019 (neg: no app code modification) | 1 | constraint_violation | 100% | 100% |
| rub_020 (neg: no empty test bodies) | 1 | reward_hacking | 100% | 100% |
| rub_021 (neg: no hallucinated endpoints) | 1 | hallucination | 100% | 100% |
| rub_022 (neg: no verbatim assertion spam) | 1 | anti_spam | 100% | 100% |
| rub_023 (neg: no internal imports for manufacturing) | 1 | constraint_violation | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 87.0% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 31.5% mean across 4 runs ✓ (target 25–50%), variance 13.0 pp ✓
- All 4 Qwen runs within 25–50% band ✓

The gap is driven by seven sentinel-inspection items (rub_001–007), the traversal
check (rub_008), and the sentinel sweep (rub_017) — Qwen writes status-code-only or
count-only assertions and fails all nine. rub_003 (search) is a partial discriminator:
one run (1ab18c1b) used a len-check that the judge accepted as logically equivalent.
rub_016 (create + list by ID) is also a partial discriminator for the same reason.
Both models miss the two laundering flows (rub_009–010). The 6 negative guards
(rub_018–023) all pass at 100% for both models, confirming they are clean passive guards.
