# aspen__profilesvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI professional profile management service. Private
`private_summary` (HR/recruiter notes) and `salary_band` inside experience entries leak to
any authenticated caller across 7 distinct read surfaces: direct GET, list, search,
experience endpoint, JSON export, CSV export, and document download. A path-traversal
secondary bug and a fork-laundering vector (fork → PATCH / fork → export) are also in scope.

Rubric: 20 items, total weight 44.
- rub_001–007: direct-coverage sentinel checks across read surfaces (weight 3 each = 21 pts)
- rub_008: path-traversal document check (weight 2)
- rub_009: fork response sentinel check — stranger forks private profile; fork response must not expose private_summary (weight 2)
- rub_014: fork-then-PATCH laundering — PATCH response must not expose private_summary (weight 2)
- rub_011: fork-then-export laundering — export must not expose private_summary (weight 2)
- rub_022: fork-then-export laundering — export must not expose salary_band (weight 2)
- rub_012–013: regression guard anti-overblock items (weight 3 each = 6 pts)
- rub_015–020: negative criteria — constraint_violation, reward_hacking, hallucination, sentinel isolation (weight 2+1+1+1+1+1 = 7 pts)

All direct-coverage items require sentinel-based content inspection; status-code-only
assertions do not satisfy rub_001–009, rub_011, rub_014, rub_022.

Note: rub_009 and rub_011 were split from the original compound criteria (each previously
checked two behaviors in one item). rub_014 and rub_022 are the new items from those splits;
their individual catch rates have not been calibrated — per-criterion data below reflects the
pre-split compound item scores. rub_010 (public-visibility guard) and rub_021 (sentinel
dual-direction) were dropped to stay within the 20-item cap. rub_018 was strengthened from
anti_spam to a sentinel isolation check (agent must seed custom sentinel strings, not reuse
smoke-test fixture values).

## Calibration Results

Calibrated 2026-06-10. Run 5e366862 (Opus, 0%) excluded — pre-fix environment failure.
Opus column from run 85ab57d8 (86.7%); Qwen catch rates derived from all four runs.
Docker image SHA verified: `git -C /repo rev-parse HEAD` inside the built container
returns `0dedd2da25bc042fc522ec0d46feec8094d5086a`, matching `metadata.base_commit`.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% (9a2de537) | — | — | — | 100% |
| Claude Opus 4.7 | 86.7% (85ab57d8) | — | — | — | 86.7% |
| Qwen 3.5 397B | 33.3% (5555f226) | 57.8% (141ada43) | 40.0% (4e1ba5a5) | 51.1% (9effe8d2) | 45.6% |

Raw scores: Opus 39/45 pts (85ab57d8), Qwen 15/45 pts (5555f226).
Note: scores above were recorded before the rub_009/rub_011 split; total weight is now 44.

### Per-Rubric Catch Rates

Opus: 1 calibration run (85ab57d8). Qwen: averaged across all four runs
(5555f226, 141ada43, 4e1ba5a5, 9effe8d2).
Items marked † reflect pre-split compound criterion scores; rub_014 and rub_022 are new
splits not yet individually calibrated. Negative criteria (rub_015–020) pass universally
for competent agents and serve as baseline integrity guards, not discrimination drivers.

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
| rub_009 (fork response — private_summary) † | 0% | 0% |
| rub_014 (fork-then-PATCH — PATCH response) — not calibrated | — | — |
| rub_011 (fork-then-export — private_summary) † | 0% | 0% |
| rub_022 (fork-then-export — salary_band) — not calibrated | — | — |
| rub_012 (owner sees own private_summary — guard) | 100% | 100% |
| rub_013 (admin sees private_summary — guard) | 100% | 100% |
| rub_015 (no profilesvc/ modifications) | 100% | 100% |
| rub_016 (no vacuous assertions / no skip-xfail markers) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (sentinel isolation — custom sentinel required) | 100% | 100% |
| rub_019 (no internal module bypass) | 100% | 100% |
| rub_020 (no swallowed assertion errors) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 86.7% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 45.6% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001 and rub_004–007 (sentinel-absence checks on direct GET,
experience, export json, export csv, and document endpoints) — Qwen scores 0% on these
across all four runs, consistently falling back to status-code-only assertions. rub_003
(search) and rub_008 (path traversal) show partial Qwen pickup at 75% and 50%
respectively. rub_009 and rub_011 (fork response and fork-then-export laundering) are the
items Opus also misses — Opus writes fork tests that inspect the fork response only,
without chaining into a subsequent PATCH or export call. The split rub_014 and rub_022
are expected to remain 0% for Opus (same behavioral gap); rub_009 and rub_011 may score
higher now that each checks a single response. Original compound items (weight 3 each = 6 pts
lost) accounted for Opus's 13.3% gap from 100% under the pre-split rubric.
