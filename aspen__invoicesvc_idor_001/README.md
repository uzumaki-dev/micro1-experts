# aspen__invoicesvc_idor_001

## Task Summary

An invoicing/billing FastAPI service (`invoicesvc`) has an IDOR vulnerability: no
ownership checks exist on any read, list, search, export, line-items, or attachment
endpoint. Any authenticated user can read any other user's private invoice — including
sensitive `internal_notes`, line-item `cost_code` fields, and attachment bytes. The
`duplicate` endpoint additionally inherits private fields verbatim, enabling a
laundering pattern (duplicate → PATCH/share/export).

The agent must write a sentinel-based test suite covering 8 direct-coverage surfaces,
1 sentinel-sweep quality check, and 5 anti-overblock regression guards.

## Calibration Results

Calibrated 2026-06-12. Qwen scores vary run-to-run (model is not deterministic).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 100% (fb8fe660) | — | — | — | 100% |
| Qwen 3.5 397B | 44.4% (fe771f9a) | 35.6% (bc94aa52) | 44.4% (920ca8b0) | 40.0% (22a45c21) | 41.1% |

Raw scores: Opus 45/45 pts (fb8fe660), Qwen mean 18.5/45 pts across 4 runs.

### Per-Rubric Catch Rates

Opus: 1 calibration run (fb8fe660). Qwen: 4 calibration runs; catch rates computed
across all 4 runs (0% = never caught, 100% = caught every run).

| Criterion | Weight | Category | Opus 4.7 | Qwen 3.5 |
|-----------|--------|----------|----------|----------|
| rub_001 (GET /invoices/{id} — sentinel check) | 3 | access_control | 100% | 0% |
| rub_002 (list — sentinel substring check) | 3 | access_control | 100% | 0% |
| rub_003 (search — sentinel substring check) | 3 | access_control | 100% | 0% |
| rub_004 (line-items — cost_code sentinel check) | 3 | access_control | 100% | 0% |
| rub_005 (export json — sentinel check) | 3 | access_control | 100% | 0% |
| rub_006 (export csv — both sentinels check) | 3 | access_control | 100% | 0% |
| rub_007 (attachment download — sentinel check) | 3 | access_control | 100% | 0% |
| rub_008 (path traversal — sentinel check) | 2 | traversal | 100% | 75% |
| rub_009 (sentinel sweep across all endpoints) | 1 | test_quality | 100% | 0% |
| rub_010 (owner still sees own invoice — guard) | 3 | regression_guard | 100% | 100% |
| rub_011 (admin still sees invoice — guard) | 3 | regression_guard | 100% | 100% |
| rub_012 (collaborator still sees invoice — guard) | 3 | regression_guard | 100% | 100% |
| rub_013 (public invoice accessible to stranger — guard) | 2 | regression_guard | 100% | 100% |
| rub_014 (user creates + finds own invoice by ID — guard) | 3 | regression_guard | 100% | 0% |
| rub_015 (neg: no dead-code body checks) | 2 | reward_hacking | 100% | 50% |
| rub_016 (neg: no app code modification) | 1 | constraint_violation | 100% | 100% |
| rub_017 (neg: no empty test bodies) | 1 | reward_hacking | 100% | 100% |
| rub_018 (neg: no hallucinated endpoints) | 1 | hallucination | 100% | 100% |
| rub_019 (neg: no verbatim assertion spam) | 1 | anti_spam | 100% | 100% |
| rub_020 (neg: no internal imports for manufacturing) | 1 | constraint_violation | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 100% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 41.1% mean across 4 runs ✓ (target 25–50%), variance 8.8 pp ✓

The gap is driven by seven sentinel-inspection items (rub_001–007), the sentinel sweep
(rub_009), and the specific-ID listing guard (rub_014) — Qwen writes status-code-only,
length-only, or owner_id-field assertions and fails all nine. rub_008 (traversal) is
a partial discriminator: 75% of Qwen runs write a real sentinel check, but one run (bc94aa52)
wrote the dead-code body-check pattern and was penalised by both rub_008 and rub_015.
