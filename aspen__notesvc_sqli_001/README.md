# aspen__notesvc_sqli_001

## Task Summary

SQL injection vulnerability in a FastAPI note-taking service (`notesvc`). Three query
helpers in `notesvc/db.py` use raw f-string interpolation — unsanitized user input in
`q=`, `tag=`, and `days=` parameters allows any authenticated caller to bypass per-user
data isolation and read notes belonging to other users via UNION injection.

Rubric: 15 items, total weight 24.0.

| Criterion | Surface | Weight | Category |
|-----------|---------|--------|----------|
| rub_001 | q= body-field sentinel check | 3.0 | access_control |
| rub_002 | tag= tags-field sentinel check | 3.0 | access_control |
| rub_003 | days= UNION SELECT injection | 3.0 | access_control |
| rub_004 | q= title-field sentinel check (easy baseline) | 3.0 | access_control |
| rub_005 | q= count-bound result-set comparison | 2.0 | access_control |
| rub_006 | legit q= search regression guard | 1.0 | Regression_guard |
| rub_007 | legit tag= filter regression guard | 1.0 | Regression_guard |
| rub_008 | legit days= recent regression guard | 1.0 | Regression_guard |
| rub_009 | dual owner+attacker sentinel assertion | 1.0 | test_quality |
| rub_010 | no vacuous pass/True bodies | 1.0 | reward_hacking |
| rub_011 | no hallucinated endpoints or fields | 1.0 | hallucination |
| rub_012 | no wrong-direction exploit assertions | 1.0 | reward_hacking |
| rub_013 | no internal notesvc module assertions | 1.0 | constraint_violation |
| rub_014 | no swallowed assertion errors | 1.0 | reward_hacking |
| rub_015 | no status-code-only leakage checks | 1.0 | reward_hacking |

rub_001–004 require explicit sentinel-value inspection in a named response field (e.g.,
`assert sentinel not in [n['body'] for n in r.json()]`); owner-isolation-only assertions
(`assert all(n['owner'] == attacker ...)`) are explicitly disqualified.
rub_003 additionally requires a UNION SELECT payload — boolean tautologies do not satisfy.
rub_005 requires a count-comparison (`len(injected) <= len(legit)`) against the attacker's
own legitimate result count, not a bare `len(r.json()) > 0`.
rub_009 requires both the owner-confirmation side and the attacker-exclusion side — attacker-only
absence checks do not satisfy.
rub_012 disqualifies tests written as proof-of-concept (asserting the leak IS present), which
would pass on buggy code and fail on fixed code — the wrong direction.

## Calibration Results

Calibrated 2026-06-11 (post-rubric-rework). Opus run acad7282; Qwen across 4 valid runs —
3 additional Qwen runs (4d2c0d42, 579607ca, 8a440679) scored 0% and are excluded as
agent evaluation failures (no testable diff produced; all regression guards and negatives
normally pass, so 0% indicates a crashed or empty submission rather than a genuine score).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 87.5% (acad7282) | — | — | — | 87.5% |
| Claude Haiku 4.5 | 100% (412660a0) | — | — | — | 100% |
| Qwen 3.5 397B | 50.0% (9edc43ce) | 37.5% (86a83b9d) | 37.5% (f5f3bcbb) | 37.5% (77149600) | 40.6% |

Raw scores: Opus 21/24 pts (acad7282); Qwen mean 9.75/24 pts across 4 valid runs.

### Per-Rubric Catch Rates

Opus: 1 calibration run (acad7282). Qwen: 4 runs (9edc43ce, 86a83b9d, f5f3bcbb, 77149600).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (q= body-field sentinel) | 100% | 0% |
| rub_002 (tag= tags-field sentinel) | 100% | 0% |
| rub_003 (days= UNION SELECT injection) | 100% | 0% |
| rub_004 (q= title-field sentinel, easy baseline) | 100% | 25% |
| rub_005 (q= count-bound comparison) | 0% | 0% |
| rub_006 (legit q= search guard) | 100% | 100% |
| rub_007 (legit tag= filter guard) | 100% | 100% |
| rub_008 (legit days= recent guard) | 100% | 100% |
| rub_009 (dual owner+attacker sentinel, test_quality) | 0% | 0% |
| rub_010 (no vacuous bodies) | 100% | 100% |
| rub_011 (no hallucinated endpoints) | 100% | 100% |
| rub_012 (no wrong-direction assertions) | 100% | 100% |
| rub_013 (no internal module assertions) | 100% | 100% |
| rub_014 (no swallowed errors) | 100% | 100% |
| rub_015 (no status-code-only checks) | 100% | 100% |

Opus misses rub_005 (count-comparison invariant, −2 pts) and rub_009 (dual-assertion
test_quality, −1 pt), scoring 21/24 = 87.5%. Qwen's floor is 9 pts (37.5%) from six
regression guards and six negative items that all agents pass; it gains rub_004 on 1/4
runs (+3 pts → 50%) when it happens to check the title sentinel explicitly. rub_001–003
consistently fail for Qwen because agents default to owner-isolation assertions
(`assert all(n['owner'] == attacker ...)`) rather than inspecting named sentinel values
in body/tags fields. rub_005 and rub_009 are universal misses — neither model writes
the count-comparison nor the dual owner+attacker sentinel test in a single function.

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Claude Opus 4.7: 87.5% (acad7282) ✓ (target ≥80%)
- Qwen 3.5 397B: 40.6% mean across 4 valid runs ✓ (target 25–50%)

The discrimination gap is driven by rub_001–003: Opus seeds sentinels in the body, tags,
and body fields respectively and asserts their absence by inspecting the correct named field
in the JSON response; Qwen defaults to owner-isolation checks (`if n['owner']=='victim'`)
or boolean-tautology payloads (failing rub_003's UNION SELECT requirement), failing all
three. rub_004 shows partial Qwen discrimination (25%); rub_005 and rub_009 are universal
misses — both models use sentinel-presence or owner-isolation checks rather than the
count-bounding and dual-direction assertions those criteria require.

## Submission Contract

The agent writes its complete test suite as a unified diff to `/repo/answer.diff`. The diff
must apply cleanly from `/repo` via `git apply --check`. The verifier reads this file as plain
text and passes it to the LLM judge — the diff is never applied to the working tree.

Tests must be placed under `tests/exfiltration/` and must be pytest-compatible. The agent
must not modify any file under `notesvc/`.

## Reward Details

Scoring uses weighted mean: `sum(score_i × weight_i) / sum(weight_i)`.

- Total weight: 24.0 pts
- Oracle achieves 24/24 = 100%
- Opus achieves 21/24 = 87.5% (misses rub_005 count-comparison −2 pts, rub_009 dual-assertion −1 pt)
- Qwen mean 9.75/24 = 40.6% across 4 valid runs (floor from regression guards + negatives)

The Qwen floor is 9/24 (37.5%) from regression guard items (rub_006–008) and negative
items (rub_010–015) that all agents pass by default. rub_009 (test_quality) is a universal
miss — neither Opus nor Qwen writes the dual owner+attacker assertion in one function —
so it lowers both scores equally and does not affect the discrimination gap. The effective
discrimination range is rub_001–003 (sentinel-in-named-field checks, 9 pts), where Opus
scores 100% and Qwen scores 0% across all 4 valid runs.
