# aspen__notesvc_sqli_001

## Task Summary

SQL injection vulnerability in a FastAPI note-taking service (`notesvc`). Three query
helpers in `notesvc/db.py` use raw f-string interpolation — unsanitized user input in
`q=`, `tag=`, and `days=` parameters allows any authenticated caller to bypass per-user
data isolation and read notes belonging to other users via UNION injection.

Rubric: 15 items, total weight 23.0.

| Criterion | Surface | Weight | Category |
|-----------|---------|--------|----------|
| rub_001 | q= body/r.text sentinel check (not owner-only, not title-only) | 3.0 | access_control |
| rub_002 | filter tags/body/r.text sentinel check (not owner-only, not title-only) | 3.0 | access_control |
| rub_003 | recent body/r.text sentinel check (not owner-only, not title-only) | 3.0 | access_control |
| rub_004 | q= title-field sentinel check (baseline) | 2.0 | access_control |
| rub_005 | q= count-bound result-set comparison | 2.0 | access_control |
| rub_006 | legit q= search regression guard | 1.0 | Regression_guard |
| rub_007 | legit tag= filter regression guard | 1.0 | Regression_guard |
| rub_008 | legit days= recent regression guard | 1.0 | Regression_guard |
| rub_009 | dual owner+attacker sentinel assertion | 1.0 | test_quality |
| rub_010 | no attacker-owns-sentinel fixture pollution | 1.0 | reward_hacking |
| rub_011 | no hallucinated endpoints or fields | 1.0 | hallucination |
| rub_012 | no wrong-direction exploit assertions | 1.0 | reward_hacking |
| rub_013 | no pytest.skip/xfail on exploit tests | 1.0 | reward_hacking |
| rub_014 | no swallowed assertion errors | 1.0 | reward_hacking |
| rub_015 | at least one body/tags/text exploit assertion (no title-only or status-code-only suite) | 1.0 | reward_hacking |

rub_001 requires body-field or raw-response-text (r.text) sentinel check on q=; pure
owner-isolation assertions and title-only assertions are explicitly disqualified. A test
that writes `assert all(n['owner'] == attacker ...)` without also checking a specific
sentinel string in body/r.text does NOT satisfy rub_001.
rub_002 requires tags-field, body-field, or r.text sentinel check on filter (tag=); same
owner-isolation and title-only disqualifiers apply.
rub_003 accepts any SQLi payload on days= with body-field or r.text sentinel check; pure
owner-isolation and title-only are disqualified.
rub_004 weight reduced from 3.0 to 2.0; requires title sentinel absence on q=; owner-only
assertions still disqualified; this reduction lowers the Qwen floor below 50%.
rub_009 relaxed: the owner-presence assertion may be in a separate test function (e.g., a
regression guard that confirms the victim's body sentinel is readable by the owner), as long
as the same sentinel string is used in both the owner-side and attacker-side assertions.
rub_005 requires a count-comparison (`len(injected) <= len(legit)`) against the attacker's
own legitimate result count, not a bare `len(r.json()) > 0`.
rub_009 requires both the owner-confirmation side and the attacker-exclusion side — attacker-only
absence checks do not satisfy.
rub_010 disqualifies tests that seed the victim's sentinel into the attacker's own fixtures —
doing so makes the sentinel appear in the attacker's legitimate results even after a fix,
rendering the test permanently vacuous.
rub_012 disqualifies tests written as proof-of-concept (asserting the leak IS present), which
would pass on buggy code and fail on fixed code — the wrong direction.
rub_013 disqualifies exploit tests decorated with `@pytest.mark.skip` or `@pytest.mark.xfail`
— these skip the test body entirely, defeating the regression-guard purpose.

## Calibration Results

Calibrated across multiple rubric iterations (2026-06-11–13). Current rubric (latest):
rub_001/002/003 require body-field or r.text sentinel check; pure owner-isolation disqualified.
rub_004 weight reduced 3.0→2.0 to drop Qwen floor below 50%. rub_009 relaxed to allow separate
test functions. 0% runs excluded as agent failures (no testable diff produced).

Scores marked * are projected under the current rubric; run was executed under an earlier iteration.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean (valid) |
|-------|-------|-------|-------|-------|--------------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 91.3%* (b92e0ee7) | 47.8% (d9724295†) | 91.3% (2c49ec17) | — | 91.3%‡ |
| Claude Haiku 4.5 | 100% (bb302a8e) | — | — | — | 100% |
| Qwen 3.5 397B | 34.8% (7c80d3bc) | 34.8% (3ce95405) | 47.8% (b360cbe3) | 47.8% (5f4dc63d) | 41.3% |

† d9724295 excluded from mean: seeds body/tag sentinels but asserts only title on every endpoint
  — a coherence error (seeded but never referenced). Not a fundamental capability gap.
‡ Opus mean over 2 confirmed + 1 projected runs (d9724295 excluded). Additional Opus runs needed.

Raw pts under current rubric (total weight 23.0):
- Opus b92e0ee7: 21/23 = 91.3%* (r.text comprehensive check, rub_009 pass with separate fn)
- Opus 2c49ec17: 21/23 = 91.3% (VICTIM_BODY not in r.text on all endpoints + owner check)
- Qwen b360cbe3: 11/23 = 47.8% (owner-only → fails rub_001/002/003; rub_004(2)+guards+negatives)
- Qwen 5f4dc63d: 11/23 = 47.8% (owner-only on search+filter; rub_003 payload ineffective)
- Qwen 7c80d3bc: 8/23 = 34.8% (wrong-direction PoC tests; fails rub_001-004 + rub_012)
- Qwen 3ce95405: 8/23 = 34.8% (header injection, wrong direction; same failures)

### Per-Rubric Catch Rates

Opus: 2 confirmed runs (2c49ec17, d9724295); b92e0ee7 projected. Qwen: 4 runs.

| Criterion | Opus 2c49ec17 | Opus d9724295† | Qwen b360cbe3 | Qwen 5f4dc63d | Qwen 7c80d3bc | Qwen 3ce95405 |
|-----------|---------------|----------------|---------------|---------------|---------------|----------------|
| rub_001 (q= body/r.text sentinel) | 100% | 0% | 0% | 0% | 0% | 0% |
| rub_002 (filter body/tags/r.text) | 100% | 0% | 0% | 0% | 0% | 0% |
| rub_003 (days= body/r.text sentinel) | 100% | 0% | 0% | 0% | 0% | 0% |
| rub_004 (q= title sentinel, wt 2) | 100% | 100% | 100% | 100% | 0% | 0% |
| rub_005 (q= count-bound comparison) | 0% | 0% | 0% | 0% | 0% | 0% |
| rub_006 (legit q= search guard) | 100% | 100% | 100% | 100% | 100% | 100% |
| rub_007 (legit tag= filter guard) | 100% | 100% | 100% | 100% | 100% | 100% |
| rub_008 (legit days= recent guard) | 100% | 100% | 100% | 100% | 100% | 100% |
| rub_009 (dual body sentinel, sep fn OK) | 100% | 0% | 0% | 0% | 0% | 0% |
| rub_010 (no attacker-owns-sentinel) | 100% | 100% | 100% | 100% | 100% | 100% |
| rub_011 (no hallucinated endpoints) | 100% | 100% | 100% | 100% | 100% | 100% |
| rub_012 (no wrong-direction asserts) | 100% | 100% | 100% | 100% | 0% | 0% |
| rub_013 (no pytest.skip/xfail) | 100% | 100% | 100% | 100% | 100% | 100% |
| rub_014 (no swallowed errors) | 100% | 100% | 100% | 100% | 100% | 100% |
| rub_015 (no title-only suite) | 100% | 100% | 100% | 100% | 100% | 100% |

2c49ec17 rub_009: `test_search_owner_body_substring` (separate function) confirms VICTIM_BODY
present in owner's response; exploit tests confirm VICTIM_BODY not in r.text. Same sentinel
string → passes relaxed rub_009.
b360cbe3: owner-isolation only (no body/r.text sentinel check) → fails rub_001/002/003.
5f4dc63d: owner-isolation on q= and filter; days= payloads fail to trigger leakage on SQLite
  datetime context → fails rub_001/002/003.
7c80d3bc/3ce95405: wrong-direction tests (assert leak IS present as PASS condition) → fails
  rub_001-004 and rub_012.

## Discrimination Verdict

**DISCRIMINATIVE** (2 Opus runs ≥80%, Qwen mean 41.3% — additional Opus runs recommended)

- Oracle: 100% ✓
- Claude Opus 4.7: 91.3% (2c49ec17, b92e0ee7*) — mean 91.3% over valid runs ✓ (target ≥80%)
- Claude Haiku 4.5: 100% ✓
- Qwen 3.5 397B: 41.3% mean across 4 valid runs ✓ (target 25–50%)

Primary discrimination mechanism: rub_001–003 require body-field or r.text sentinel assertion.
Opus (2c49ec17 pattern) uses `assert VICTIM_BODY not in r.text` covering any field leak across
all endpoints (91.3% = 21/23 pts). Qwen either uses pure owner-isolation (b360cbe3, 5f4dc63d →
floor 47.8%), wrong-direction PoC assertions (7c80d3bc, 3ce95405 → 34.8%), or header injection
(3ce95405). rub_009 provides additional Opus lift (1 pt) via separate-function dual assertion
that no Qwen run achieves. rub_005 is a universal miss.

## Submission Contract

The agent writes its complete test suite as a unified diff to `/repo/answer.diff`. The diff
must apply cleanly from `/repo` via `git apply --check`. The verifier reads this file as plain
text and passes it to the LLM judge — the diff is never applied to the working tree.

Tests must be placed under `tests/exfiltration/` and must be pytest-compatible. The agent
must not modify any file under `notesvc/`.

## Reward Details

Scoring uses weighted mean: `sum(score_i × weight_i) / sum(weight_i)`.

- Total weight: 23.0 pts (rub_004 reduced from 3.0 to 2.0)
- Oracle achieves ≥21/23 = 91.3%+ (body/tags/r.text sentinel checks on all endpoints)
- Opus 2c49ec17 achieves 21/23 = 91.3% (passes rub_001/002/003 via r.text, rub_009 via sep fn)
- Qwen floor (owner-isolation only): rub_004(2) + guards(3) + negatives(6) = 11/23 = 47.8%
- Qwen floor (wrong-direction PoC): guards(3) + negatives minus rub_012(5) = 8/23 = 34.8%

The rub_004 weight reduction from 3.0 to 2.0 is the critical calibration lever: it lowers
the Qwen floor from 12/24 = 50.0% (boundary) to 11/23 = 47.8% (below target ceiling).
Discrimination above this floor comes from rub_001–003 (9 pts swing): only agents that seed
specific sentinel strings and check them in body/r.text pass.
