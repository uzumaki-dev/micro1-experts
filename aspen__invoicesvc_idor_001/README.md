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

Calibrated 2026-05-31. Opus column from the 81.6% run (f2dff40b); Qwen 4-run average
shown — scores vary run-to-run (Qwen is not deterministic on this task).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Claude Opus 4.7 | 75.5% | 81.6% | — | — | 78.6% |
| Qwen 3.5 397B | 32.7% | 40.8% | 32.7% | 51.0% | 39.3% |

Raw scores: Opus 40/49 pts (f2dff40b), Qwen 20/49 pts (452f4fc6). Oracle: 1.0.

### Per-Rubric Catch Rates

Opus column from run f2dff40b (81.6%); Qwen column from run 452f4fc6 (40.8%).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /invoices/{id} — sentinel req.) | ✓ | ✗ |
| rub_002 (list) | ✓ | ✓ |
| rub_003 (search) | ✓ | ✓ |
| rub_004 (line-items — sentinel req.) | ✓ | ✗ |
| rub_005 (export json — sentinel req.) | ✓ | ✗ |
| rub_006 (export csv — sentinel req.) | ✓ | ✗ |
| rub_007 (attachment download — sentinel req.) | ✓ | ✗ |
| rub_008 (path traversal — sentinel req.) | ✓ | ✗ |
| rub_009 (duplicate+patch laundering) | ✗ | ✗ |
| rub_010 (duplicate+share laundering) | ✗ | ✗ |
| rub_011 (duplicate+export laundering) | ✗ | ✗ |
| rub_012 (owner overblock guard) | ✓ | ✓ |
| rub_013 (admin overblock guard) | ✓ | ✓ |
| rub_014 (collaborator overblock guard) | ✓ | ✓ |
| rub_015 (public invoice overblock guard) | ✓ | ✓ |
| rub_016 (create+list own overblock guard) | ✓ | ✓ |
| rub_017 (sentinel sweep — w=3) | ✓ | ✗ |

## Discrimination Verdict

**DISCRIMINATIVE**

- Opus 4.7: 81.6% ✓ (target ≥80%, best of 2 runs)
- Qwen 3.5 397B: 39.3% mean across 4 runs ✓ (target 25–50%)

The gap is driven by the six sentinel-inspection items (rub_001, rub_004–rub_008) plus the
sentinel sweep (rub_017) — Qwen writes status-code-only assertions on all of these and
fails them. Both models miss the three laundering flows (rub_009–011), which are the
non-obvious chained surfaces; these account for Opus's 9 lost points (40/49).
