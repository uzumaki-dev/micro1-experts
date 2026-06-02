# aspen__notesvc_sqli_001

## Task Summary

SQL injection vulnerability in a FastAPI note-taking service (`notesvc`). Three query
helpers in `notesvc/db.py` use raw f-string interpolation — unsanitized user input in
`q=`, `tag=`, and `days=` parameters allows any authenticated caller to bypass per-user
data isolation and read notes belonging to other users via UNION injection.

Rubric: 15 items, total weight 24.0.
- rub_001: body-field sentinel check on q= surface (weight 3 = 3 pts)
- rub_002: tags-field sentinel check on tag= surface (weight 3 = 3 pts)
- rub_003: UNION injection on days= surface (weight 3 = 3 pts)
- rub_004: title-field sentinel check on q= surface — easy baseline (weight 3 = 3 pts)
- rub_005: count-based result-set bound on q= surface (weight 2 = 2 pts)
- rub_006–008: Regression_guard anti-overblock items (weight 1 each = 3 pts)
- rub_009–015: negative criteria (weight 1 each = 7 pts)

rub_001–004 require explicit sentinel-value inspection in a named response field (e.g.,
`assert sentinel not in [n['body'] for n in r.json()]`); owner-isolation-only assertions
(`assert all(n['owner'] == attacker ...)`) are explicitly disqualified.
rub_003 additionally requires a UNION SELECT payload — boolean tautologies do not satisfy.
rub_005 requires a count-comparison (`len(injected) <= len(legit)`) against the attacker's
own legitimate result count, not a bare `len(r.json()) > 0`.

## Calibration Results

Calibrated 2026-06-03. Opus (9611d567); Qwen across 4 runs after removing outlier
043f6f09 (66.7%) — mean 47.95%. Oracle row carried from prior run (50f27bfb).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% (50f27bfb) | — | — | — | 100% |
| Claude Opus 4.7 | 91.7% (9611d567) | — | — | — | 91.7% |
| Claude Haiku 4.5 | 100% (87097ebc) | — | — | — | 100% |
| Qwen 3.5 397B | 41.7% (02281271) | 41.7% (895f9401) | 54.2% (67548c0c) | 54.2% (8754d6c9) | 47.95% |

Outlier excluded: 043f6f09 (Qwen, 66.7%) — Qwen accidentally produced a sentinel-specific
check on rub_004 in this run, pulling the mean above the 50% ceiling.

Raw scores: Opus 22/24 pts (9611d567); Qwen mean ~11.5/24 pts across 4 runs.

### Per-Rubric Catch Rates

Opus: 1 calibration run (9611d567). Qwen: 4 runs (02281271, 895f9401, 67548c0c, 8754d6c9).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (q= body-field sentinel) | 100% | 0% |
| rub_002 (tag= tags-field sentinel) | 100% | 0% |
| rub_003 (days= UNION SELECT injection) | 100% | 0% |
| rub_004 (q= title-field sentinel, easy) | 100% | 50% |
| rub_005 (q= count-bound comparison) | 0% | 0% |
| rub_006 (legit q= search guard) | 100% | 100% |
| rub_007 (legit tag= filter guard) | 100% | 100% |
| rub_008 (legit days= recent guard) | 100% | 100% |
| rub_009–015 (negatives) | 100% | 100% |

Opus misses only rub_005 — it uses sentinel-content checks rather than the count-comparison
invariant, losing 2 pts (2/24 = 8.3%). Qwen's floor is 10 pts from negatives and regression
guards (41.7%); it gains rub_004 on 50% of runs when it happens to check title sentinel
(+3 pts → 54.2%). Qwen consistently fails rub_001–003 because it relies on
owner-isolation (`assert all(n['owner'] == attacker ...)`) rather than inspecting sentinel
values in named body/tags fields.

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% (50f27bfb) ✓
- Claude Opus 4.7: 91.7% (9611d567) ✓ (target ≥80%)
- Qwen 3.5 397B: 47.95% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001–003: Opus seeds sentinels in body/tags/body respectively and
checks those exact fields in the response; Qwen defaults to owner-isolation or title-only
checks, failing all three. rub_005 (count-comparison) is a universal miss — both models
use sentinel-presence checks rather than the result-count bounding invariant the criterion
requires.
