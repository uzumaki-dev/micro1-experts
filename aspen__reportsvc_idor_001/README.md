# aspen__reportsvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI analytics reporting service. Private `confidential_notes`
and data-point `metric_code` fields, plus attachment bytes, leak to any authenticated
caller across 8 distinct surfaces: direct GET, list, search, JSON export, CSV export,
attachment download, path traversal, and fork laundering (fork→PATCH, fork→export).

Rubric: 20 items, total weight 45.
- rub_001–007: direct-coverage sentinel checks (weight 3 each = 21 pts)
- rub_008: path-traversal sentinel check (weight 2)
- rub_009–010: fork laundering redaction checks (weight 3 each = 6 pts)
- rub_011–013: Regression_guard anti-overblock items (weight 3 each = 9 pts)
- rub_014: sentinel sweep quality item (weight 1)
- rub_015–020: negative criteria — constraint_violation, reward_hacking, hallucination, anti_spam (weight 1 each = 6 pts)

All direct-coverage items require sentinel-based content inspection; status-code-only
assertions do not satisfy rub_001–008.

## Calibration Results

Calibrated 2026-06-02. Opus column from run cc500dff (86.7%); Qwen catch rates derived
from representative run fc2c679a (51.1%).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% (acb26f0b) | — | — | — | 100% |
| Claude Opus 4.7 | 86.7% (cc500dff) | — | — | — | 86.7% |
| Qwen 3.5 397B | 51.1% (fc2c679a) | 46.7% (2930c349) | 46.7% (a120fae7) | 51.1% (56e07368) | 48.9% |

Raw scores: Opus 39/45 pts (cc500dff), Qwen 23/45 pts (fc2c679a).

### Per-Rubric Catch Rates

Opus: 1 calibration run (cc500dff). Qwen: catch rates derived across all 4 runs;
rub_008 varied (50% catch rate); all other items were consistent across Qwen runs.

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /reports/{id} confidential_notes sentinel) | 100% | 0% |
| rub_002 (list sentinel) | 100% | 100% |
| rub_003 (search sentinel) | 100% | 100% |
| rub_004 (data-points metric_code sentinel) | 100% | 0% |
| rub_005 (export json sentinel) | 100% | 0% |
| rub_006 (export csv sentinel) | 100% | 0% |
| rub_007 (attachment download sentinel) | 100% | 0% |
| rub_008 (path traversal sentinel) | 100% | 50% |
| rub_009 (fork→PATCH laundering) | 0% | 0% |
| rub_010 (fork→export laundering) | 0% | 0% |
| rub_011 (owner still sees notes — guard) | 100% | 100% |
| rub_012 (admin still sees notes — guard) | 100% | 100% |
| rub_013 (user can create + list own — guard) | 100% | 100% |
| rub_014 (sentinel sweep quality) | 100% | 0% |
| rub_015 (no reportsvc/ modifications) | 100% | 100% |
| rub_016 (no vacuous assertions) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no duplicate assertion spam) | 100% | 100% |
| rub_019 (no internal module bypass) | 100% | 100% |
| rub_020 (no swallowed assertion errors) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 86.7% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 48.9% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001 and rub_004–007 (sentinel-absence checks on the single-report,
data-points, export, and attachment surfaces) plus rub_014 (sentinel sweep) — Qwen uses
status-code-only assertions on these and fails all five consistently. Opus misses only
rub_009–010 (fork laundering flows, weight 3 each = 6 pts); these are the non-obvious
chained-endpoint items that account for Opus's 6/45 lost points.
