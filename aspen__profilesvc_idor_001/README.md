# aspen__profilesvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI professional profile management service. Private
`private_summary` (HR/recruiter notes) and `salary_band` inside experience entries leak to
any authenticated caller across 7 distinct read surfaces: direct GET, list, search,
experience endpoint, JSON export, CSV export, and document download. A path-traversal
secondary bug and a fork-laundering vector (fork → PATCH / fork → export) are also in scope.

Rubric: 20 items, total weight 47.
- rub_001–007: direct-coverage sentinel checks across read surfaces (weight 3 each = 21 pts)
- rub_008: path-traversal document check (weight 2)
- rub_009: fork-then-PATCH laundering sentinel check (weight 3)
- rub_010: public-visibility regression guard (weight 2)
- rub_011: fork-then-export laundering sentinel check (weight 3)
- rub_012–014: regression guard anti-overblock items (weight 3 each = 9 pts)
- rub_015–020: negative criteria — constraint_violation, reward_hacking, hallucination, anti_spam (weight 2+1+1+1+1+1 = 7 pts)

All direct-coverage items require sentinel-based content inspection; status-code-only
assertions do not satisfy rub_001–009, rub_011.

## Calibration Results

Calibrated 2026-06-03. Failed runs (5e0e0fb1, 9d1b9e7d, fc896e22) excluded — environment
failures, not model scores. Opus column from run d93fdd29 (87.2%); Qwen catch rates averaged
across all four successful runs.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | — | — | — | — | — |
| Claude Opus 4.7 | 87.2% (d93fdd29) | — | — | — | 87.2% |
| Qwen 3.5 397B | 55.3% (a3c43178) | 44.7% (61558259) | 38.3% (89725d6b) | 42.6% (c4a9edf6) | 45.2% |

Raw scores: Opus 41/47 pts (d93fdd29), Qwen 21/47 pts (61558259).

### Per-Rubric Catch Rates

Opus: 1 calibration run (d93fdd29). Qwen: averaged across all four runs
(a3c43178, 61558259, 89725d6b, c4a9edf6).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /{id} private_summary sentinel) | 100% | 0% |
| rub_002 (list private_summary sentinel) | 100% | 25% |
| rub_003 (search private_summary sentinel) | 100% | 50% |
| rub_004 (experience salary_band sentinel) | 100% | 0% |
| rub_005 (export json private_summary sentinel) | 100% | 0% |
| rub_006 (export csv private_summary+salary_band sentinel) | 100% | 0% |
| rub_007 (document download sentinel) | 100% | 0% |
| rub_008 (path traversal sentinel) | 100% | 50% |
| rub_009 (fork-then-PATCH laundering) | 0% | 0% |
| rub_010 (public-visibility access — guard) | 100% | 100% |
| rub_011 (fork-then-export laundering) | 0% | 0% |
| rub_012 (owner sees own private_summary — guard) | 100% | 100% |
| rub_013 (admin sees private_summary — guard) | 100% | 100% |
| rub_014 (non-admin create+list own profile — guard) | 100% | 100% |
| rub_015 (no profilesvc/ modifications) | 100% | 100% |
| rub_016 (no vacuous assertions) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no duplicate assertion spam) | 100% | 100% |
| rub_019 (no internal module bypass) | 100% | 100% |
| rub_020 (no swallowed assertion errors) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: not yet run
- Opus 4.7: 87.2% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 45.2% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001 and rub_004–007 (sentinel-absence checks on direct GET,
experience, export json, export csv, and document endpoints) — Qwen scores 0% on these
across all four runs, consistently falling back to status-code-only assertions. rub_003
(search) and rub_008 (path traversal) show partial Qwen pickup at 50%. rub_009 and rub_011
(fork-then-PATCH and fork-then-export laundering) are the two items Opus also misses —
Opus writes fork tests that inspect the fork response only, without chaining into a
subsequent PATCH or export call. These two items (weight 3 each = 6 pts lost) account for
Opus's 12.8% gap from 100%.
