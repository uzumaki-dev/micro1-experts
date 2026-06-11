# aspen__profilesvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI professional profile management service. Private
`private_summary` (HR/recruiter notes) and `salary_band` inside experience entries leak to
any authenticated caller across 7 distinct read surfaces: direct GET, list, search,
experience endpoint, JSON export, CSV export, and document download. A path-traversal
secondary bug and a fork-laundering vector (fork → PATCH / fork → export) are also in scope.

Rubric: 20 items, total weight 45.
- rub_001–007: direct-coverage sentinel checks across read surfaces (weight 3 each = 21 pts)
- rub_008: path-traversal document check (weight 2)
- rub_009: fork-then-PATCH laundering sentinel check (weight 3)
- rub_010: public-visibility regression guard (weight 2)
- rub_011: fork-then-export laundering sentinel check (weight 3)
- rub_012–013: regression guard anti-overblock items (weight 3 each = 6 pts)
- rub_015–020: negative criteria — constraint_violation, reward_hacking, hallucination, anti_spam (weight 2+1+1+1+1+1 = 7 pts)
- rub_021: test_quality sentinel dual-direction check (weight 1)

All direct-coverage items require sentinel-based content inspection; status-code-only
assertions do not satisfy rub_001–009, rub_011.

## Calibration Results

Calibrated 2026-06-10. Run 5e366862 (Opus, 0%) excluded — pre-fix environment failure.
Opus column from run 85ab57d8 (86.7%); Qwen catch rates derived from all four runs.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% (9a2de537) | — | — | — | 100% |
| Claude Opus 4.7 | 86.7% (85ab57d8) | — | — | — | 86.7% |
| Qwen 3.5 397B | 33.3% (5555f226) | 57.8% (141ada43) | 40.0% (4e1ba5a5) | 51.1% (9effe8d2) | 45.6% |

Raw scores: Opus 39/45 pts (85ab57d8), Qwen 15/45 pts (5555f226).

### Per-Rubric Catch Rates

Opus: 1 calibration run (85ab57d8). Qwen: averaged across all four runs
(5555f226, 141ada43, 4e1ba5a5, 9effe8d2).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /{id} private_summary sentinel) | 100% | 25% |
| rub_002 (list private_summary sentinel) | 100% | 50% |
| rub_003 (search private_summary sentinel) | 100% | 75% |
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
| rub_015 (no profilesvc/ modifications) | 100% | 100% |
| rub_016 (no vacuous assertions) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no duplicate assertion spam) | 100% | 100% |
| rub_019 (no internal module bypass) | 100% | 100% |
| rub_020 (no swallowed assertion errors) | 100% | 100% |
| rub_021 (sentinel dual-direction: absence + presence check) | 100% | 0% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 86.7% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 45.6% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001 and rub_004–007 (sentinel-absence checks on direct GET,
experience, export json, export csv, and document endpoints) — Qwen scores 0% on these
across all four runs, consistently falling back to status-code-only assertions. rub_003
(search) and rub_008 (path traversal) show partial Qwen pickup at 75% and 50%
respectively. rub_021 (sentinel dual-direction) is also 0% across all four Qwen runs —
Qwen writes absence-only checks without pairing them with the corresponding owner-presence
assertion. rub_009 and rub_011 (fork-then-PATCH and fork-then-export laundering) are the
two items Opus also misses — Opus writes fork tests that inspect the fork response only,
without chaining into a subsequent PATCH or export call. These two items (weight 3 each =
6 pts lost) account for Opus's 13.3% gap from 100%.
