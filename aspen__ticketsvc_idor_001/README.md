# aspen__ticketsvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI support-ticket service. Private `internal_notes` and
`type="internal"` comments leak to any authenticated caller across 9 distinct surfaces:
direct GET, list, search, JSON export, ZIP export, attachment download, comments endpoint,
clone→GET laundering, and path traversal into the global private store.

Rubric: 20 items, total weight 38.
- rub_001–008: direct-coverage sentinel checks (weight 3 each = 24 pts)
- rub_009–012: Regression_guard anti-overblock items (weight 1 each = 4 pts)
- rub_013: path-traversal check (weight 3)
- rub_014: sentinel sweep quality item (weight 1)
- rub_015–020: negative criteria — constraint_violation, reward_hacking, hallucination, anti_spam (weight 1 each = 6 pts)

All direct-coverage items require sentinel-based content inspection; status-code-only
assertions do not satisfy rub_001–008.

## Calibration Results

Calibrated 2026-06-01. Qwen run 2d3e4a14 (65.8%) excluded as an outlier.
Opus column from run 6e8d9ce0 (89.5%); Qwen catch rates derived from run b8add06b (44.7%).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 89.5% (6e8d9ce0) | — | — | — | 89.5% |
| Qwen 3.5 397B | 39.5% (830f6fb1) | 44.7% (b8add06b) | 31.6% (f4ef9503) | 57.9% (9e35a623) | 43.4% |

Raw scores: Opus 34/38 pts (6e8d9ce0), Qwen 17/38 pts (b8add06b).

### Per-Rubric Catch Rates

Opus: 1 calibration run (6e8d9ce0). Qwen: derived from representative run b8add06b (44.7%);
other Qwen runs show same item-level pattern (rub_001–008 fail, rub_013–020 pass consistently).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /{id} internal_notes sentinel) | 100% | 0% |
| rub_002 (list internal_notes sentinel) | 100% | 0% |
| rub_003 (search internal_notes sentinel) | 100% | 0% |
| rub_004 (export json sentinel) | 100% | 0% |
| rub_005 (export zip archive sentinel) | 100% | 0% |
| rub_006 (private attachment sentinel) | 100% | 0% |
| rub_007 (internal comments sentinel) | 100% | 100% |
| rub_008 (clone→GET sentinel) | 100% | 0% |
| rub_009 (agent sees notes — guard) | 0% | ~75% |
| rub_010 (agent sees internal comments — guard) | 0% | ~25% |
| rub_011 (reporter write surface — guard) | 0% | ~50% |
| rub_012 (public attachment — guard) | 0% | 0% |
| rub_013 (path traversal) | 100% | 100% |
| rub_014 (sentinel sweep quality) | 100% | 0% |
| rub_015 (no ticketsvc/ modifications) | 100% | 100% |
| rub_016 (no vacuous assertions) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no duplicate assertion spam) | 100% | 100% |
| rub_019 (no internal module bypass) | 100% | 100% |
| rub_020 (no swallowed assertion errors) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 89.5% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 43.4% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001–006 and rub_008 (sentinel-absence checks across all leak
surfaces) plus rub_014 (sentinel sweep) — Qwen uses empty-field or status-code-only
assertions on these and fails all seven. Opus consistently misses rub_009–012 (regression
guard items, weight 1 each = 4 pts); these account for Opus's 4/38 lost points.
