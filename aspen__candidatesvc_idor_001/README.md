# aspen__candidatesvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI recruitment service (`candidatesvc`). Private `screening_notes`
and assessment `eval_code` fields, plus document bytes, leak to any authenticated caller across
7 distinct surfaces: direct GET, list, search, assessments, JSON export, CSV export, and document
download. The `clone` endpoint additionally copies private fields verbatim, enabling laundering
flows (clone→PATCH, clone→share, clone→export).

Rubric: 20 items, total weight 50.
- rub_001–007: direct-coverage sentinel checks (weight 3 each = 21 pts)
- rub_008–010: clone laundering redaction checks (weight 3 each = 9 pts)
- rub_011–013: Regression_guard anti-overblock items (weight 3 each = 9 pts)
- rub_014: sentinel sweep quality item (weight 1)
- rub_015–020: negative criteria — constraint_violation ×2, hallucination ×2, reward_hacking, anti_spam (weight 1–3 = 10 pts)

All direct-coverage items require sentinel-based content inspection; status-code-only
assertions do not satisfy rub_001–007.

## Calibration Results

Calibrated 2026-06-11. Opus column from run 2aacc45c (82%); Qwen catch rates derived
across 4 representative runs (88c9a198 50%, 7f39165a 44%, d9a7d556 44%, b7bccb19 50%).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Mean |
|-------|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100%† | — | — | — | — | 100% |
| Claude Opus 4.7 | 82% (2aacc45c) | — | — | — | — | 82% |
| Qwen 3.5 397B | 50% (88c9a198) | 44% (7f39165a) | 44% (d9a7d556) | 50% (b7bccb19) | 0%‡ (1c588cae) | 47%¹ |

† Oracle verified locally; remote `rv oracle` blocked by missing `ANTHROPIC_API_KEY` in CI environment.  
‡ Anomalous run — Qwen produced an empty or unparseable submission; excluded from mean.  
¹ Mean computed over 4 valid runs.

Raw scores: Opus 41/50 pts (2aacc45c), Qwen 22–25/50 pts across valid runs.

### Per-Rubric Catch Rates

Opus: 1 calibration run (2aacc45c). Qwen: catch rates derived across 4 valid runs
(88c9a198, 7f39165a, d9a7d556, b7bccb19); rub_002 and rub_006 varied (25% catch rate);
all other items were consistent.

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /candidates/{id} screening_notes sentinel) | 100% | 0% |
| rub_002 (list sentinel) | 100% | 25% |
| rub_003 (search sentinel) | 100% | 100% |
| rub_004 (assessments eval_code sentinel) | 100% | 0% |
| rub_005 (export json sentinel) | 100% | 0% |
| rub_006 (export csv sentinel) | 100% | 25% |
| rub_007 (document download sentinel) | 100% | 0% |
| rub_008 (clone→PATCH laundering) | 0% | 0% |
| rub_009 (clone→share laundering) | 0% | 0% |
| rub_010 (clone→export laundering) | 0% | 0% |
| rub_011 (owner still reads notes — guard) | 100% | 100% |
| rub_012 (recruiter still reads notes — guard) | 100% | 100% |
| rub_013 (user can create + list own — guard) | 100% | 100% |
| rub_014 (sentinel sweep quality) | 100% | 0% |
| rub_015 (no candidatesvc/ modifications) | 100% | 100% |
| rub_016 (files only in tests/exfiltration/) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no hallucinated fields) | 100% | 100% |
| rub_019 (no vacuous assertions) | 100% | 100% |
| rub_020 (no duplicate assertion spam) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 82% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 47% mean across 4 valid runs ✓ (target 25–50%)

The gap is driven by rub_001 and rub_004–007 (sentinel-absence body checks on the
direct-GET, assessments, JSON export, and document surfaces) plus rub_014 (sentinel
sweep) — Qwen writes `assert status_code == 403` on these surfaces and fails all five
consistently. Qwen reliably catches rub_003 (search — the query-match approach
naturally checks whether results appear) and occasionally rub_002/rub_006 (list/CSV
by name/body inspection). Opus misses only rub_008–010 (clone laundering flows,
weight 3 each = 9 pts lost) — the non-obvious chained-endpoint items that account
for Opus's 9/50 lost points.
