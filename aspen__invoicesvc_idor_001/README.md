# aspen__invoicesvc_idor_001

## Task Summary

An invoicing/billing FastAPI service (`invoicesvc`) has an IDOR vulnerability: no
ownership checks exist on any read, list, search, export, line-items, or attachment
endpoint. Any authenticated user can read any other user's private invoice — including
sensitive `internal_notes`, line-item `cost_code` fields, and attachment bytes. The
`duplicate` endpoint additionally inherits private fields verbatim, enabling a
laundering pattern (duplicate → PATCH/share/export).

The agent must write a sentinel-based test suite covering 11 direct-coverage surfaces
and 6 anti-overblock regression guards.

## Calibration Results

Calibrated 2026-06-01. Qwen scores vary run-to-run (model is not deterministic).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 81.6% (45e04c70) | — | — | — | 81.6% |
| Qwen 3.5 397B | 40.8% (2c189e57) | 44.9% (c7dc318a) | 44.9% (26cdabc9) | 44.9% (ef435a2a) | 43.9% |

Raw scores: Opus 40/49 pts (45e04c70), Qwen 22/49 pts (ef435a2a).

### Per-Rubric Catch Rates

Opus: 1 calibration run (45e04c70). Qwen: 4 calibration runs; 3 runs scored 44.9%
(22/49 pts, same item pattern as ef435a2a), 1 run scored 40.8% (20/49 pts, missing
one weight-2 item — rub_015 most likely).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /invoices/{id} — sentinel check) | 100% | 0% |
| rub_002 (list — sentinel check) | 100% | 100% |
| rub_003 (search — sentinel check) | 100% | 100% |
| rub_004 (line-items — sentinel check) | 100% | 0% |
| rub_005 (export json — sentinel check) | 100% | 0% |
| rub_006 (export csv — sentinel check) | 100% | 0% |
| rub_007 (attachment download — sentinel check) | 100% | 0% |
| rub_008 (path traversal — sentinel check) | 100% | 100% |
| rub_009 (duplicate→PATCH laundering) | 0% | 0% |
| rub_010 (duplicate→share laundering) | 0% | 0% |
| rub_011 (duplicate→export laundering) | 0% | 0% |
| rub_012 (owner still sees own invoice — guard) | 100% | 100% |
| rub_013 (admin still sees invoice — guard) | 100% | 100% |
| rub_014 (collaborator still sees invoice — guard) | 100% | 100% |
| rub_015 (public invoice accessible to stranger — guard) | 100% | 75% |
| rub_016 (user can create + list own invoices — guard) | 100% | 100% |
| rub_017 (sentinel sweep across all surfaces) | 100% | 0% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 81.6% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 43.9% mean across 4 runs ✓ (target 25–50%)

The gap is driven by the five sentinel-inspection items (rub_001, rub_004–007) plus
the sentinel sweep (rub_017) — Qwen writes status-code-only or empty-field assertions
and fails all six. Both models consistently miss the three laundering flows (rub_009–011),
the non-obvious chained endpoints; these alone account for Opus's 9 lost points (40/49).
