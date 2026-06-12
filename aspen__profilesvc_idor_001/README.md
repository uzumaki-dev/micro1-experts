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
checked two behaviors in one item). rub_014 and rub_022 are the items from those splits.
rub_010 (public-visibility guard) and rub_021 (sentinel dual-direction) were dropped to
stay within the 20-item cap. rub_018 was strengthened from anti_spam to a sentinel isolation
check (agent must seed custom sentinel strings, not reuse smoke-test fixture values).

## Calibration Results

Calibrated 2026-06-12. Opus column from run 6a3d0278 (86.4%); Qwen catch rates derived
from all four runs. Docker image SHA verified: `git -C /repo rev-parse HEAD` inside the
built container returns `0dedd2da25bc042fc522ec0d46feec8094d5086a`, matching `metadata.base_commit`.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% (9a2de537) | — | — | — | 100% |
| Claude Opus 4.7 | 86.4% (6a3d0278) | — | — | — | 86.4% |
| Qwen 3.5 397B | 43.2% (9c0d29a0) | 36.4% (ac18146a) | 47.7% (e086ece1) | 50.0% (34d58a4c) | 44.3% |
| Claude Haiku 4.5 | 100% (a8e53ba5) | — | — | — | 100% |

Raw scores: Opus 38/44 pts (6a3d0278), Qwen lowest 16/44 pts (ac18146a).

### Per-Rubric Catch Rates

Opus: 1 calibration run (6a3d0278). Qwen: averaged across all four runs
(9c0d29a0, ac18146a, e086ece1, 34d58a4c).
Negative criteria (rub_015–020) pass universally for competent agents and serve as
baseline integrity guards, not discrimination drivers.

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /{id} private_summary sentinel) | 100% | 50% |
| rub_002 (list private_summary sentinel) | 100% | 25% |
| rub_003 (search private_summary sentinel) | 100% | 100% |
| rub_004 (experience salary_band sentinel) | 100% | 0% |
| rub_005 (export json private_summary sentinel) | 100% | 25% |
| rub_006 (export csv private_summary+salary_band sentinel) | 100% | 0% |
| rub_007 (document download sentinel) | 100% | 0% |
| rub_008 (path traversal sentinel) | 100% | 25% |
| rub_009 (fork response — private_summary) | 100% | 0% |
| rub_014 (fork-then-PATCH — PATCH response) | 0% | 0% |
| rub_011 (fork-then-export — private_summary) | 0% | 0% |
| rub_022 (fork-then-export — salary_band) | 0% | 0% |
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
- Opus 4.7: 86.4% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 44.3% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_004, rub_006, rub_007 (experience salary_band, CSV export,
document download) — Qwen scores 0% across all four runs on these, consistently falling
back to status-code-only assertions. rub_001 (direct GET) shows partial Qwen pickup at
50%; rub_002 (list), rub_005 (JSON export), and rub_008 (path traversal) each land at
25%. rub_003 (search) is caught by all four Qwen runs (100%) — Qwen reliably constructs
result-count assertions but stops short of sentinel-string body inspection on direct
access endpoints. rub_009/011/014/022 (fork laundering chain) are missed by all Qwen
runs; Opus catches the fork response itself (rub_009, 100%) but misses the subsequent
PATCH and export chain (rub_014, rub_011, rub_022, all 0%). Opus's 13.6% gap from 100%
is accounted for entirely by those three fork-chain items (6 pts on 44).
