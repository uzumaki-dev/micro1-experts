# aspen__notesvc_sqli_001

## Task Summary

SQL injection vulnerability in a FastAPI note-taking service (`notesvc`). Three query
helpers in `notesvc/db.py` use raw f-string interpolation — unsanitized user input in
`q=`, `tag=`, and `days=` parameters allows any authenticated caller to bypass per-user
data isolation and read notes belonging to other users via UNION injection.

Rubric: 16 items, total weight 23.0.
- rub_001–003: direct-coverage sentinel checks on all three injection surfaces (weight 3 each = 9 pts)
- rub_004: observational count-based check on q= surface (weight 2 = 2 pts)
- rub_005–006: assertion quality / surface coverage items (weight 1 each = 2 pts)
- rub_007–010: Regression_guard anti-overblock items (weight 1 each = 4 pts)
- rub_011–016: negative criteria — constraint_violation, reward_hacking, hallucination, anti_spam (weight 1 each = 6 pts)

All sentinel checks (rub_001–003) require content inspection; status-code-only assertions
do not satisfy them. rub_003 (UNION injection into the `days=` datetime parameter) is the
top-of-frontier item.

## Calibration Results

*Pending calibration.*

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | — | — | — | — | — |
| Claude Opus 4.7 | — | — | — | — | — |
| Qwen 3.5 397B | — | — | — | — | — |

### Per-Rubric Catch Rates

*To be filled after calibration runs.*

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (q= sentinel) | — | — |
| rub_002 (tag= sentinel) | — | — |
| rub_003 (days= UNION sentinel) | — | — |
| rub_004 (q= count check) | — | — |
| rub_005 (sentinel seeding quality) | — | — |
| rub_006 (all 3 surfaces covered) | — | — |
| rub_007 (legit search guard) | — | — |
| rub_008 (legit filter guard) | — | — |
| rub_009 (legit recent guard) | — | — |
| rub_010 (CRUD guard) | — | — |
| rub_011–016 (negatives) | — | — |

## Discrimination Verdict

**Pending.**

- Oracle: —
- Opus 4.7: — (target ≥80%)
- Qwen 3.5 397B: — mean across 4 runs (target 25–50%)
