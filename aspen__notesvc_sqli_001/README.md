# aspen__notesvc_sqli_001

## Task Summary

SQL injection vulnerability in a FastAPI note-taking service (`notesvc`). Three query
helpers in `notesvc/db.py` use raw f-string interpolation — unsanitized user input in
`q=`, `tag=`, and `days=` parameters allows any authenticated caller to bypass per-user
data isolation and read notes belonging to other users via UNION injection.

Rubric: 15 items, total weight 24.0.
- rub_001: body-field sentinel check on q= surface (weight 3 = 3 pts)
- rub_002: tags-field sentinel check on tag= surface (weight 3 = 3 pts)
- rub_003: UNION injection on days= surface (weight 3 = 3 pts) — top-of-frontier
- rub_004: title-field sentinel check on q= surface — easy baseline (weight 3 = 3 pts)
- rub_005: count-based expansion on q= surface (weight 2 = 2 pts)
- rub_006–008: Regression_guard anti-overblock items (weight 1 each = 3 pts)
- rub_009–015: negative criteria (weight 1 each = 7 pts)

rub_001–003 discriminate via field specificity and payload sophistication.
rub_001 requires seeding in body; rub_002 requires seeding in tags; rub_003 requires UNION SELECT.

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
| rub_001 (q= body-field sentinel) | — | — |
| rub_002 (tag= tags-field sentinel) | — | — |
| rub_003 (days= UNION injection) | — | — |
| rub_004 (q= title-field sentinel, easy) | — | — |
| rub_005 (q= count expansion) | — | — |
| rub_006 (legit q= search guard) | — | — |
| rub_007 (legit tag= filter guard) | — | — |
| rub_008 (legit days= recent guard) | — | — |
| rub_009–015 (negatives) | — | — |

## Discrimination Verdict

**Pending.**

- Oracle: —
- Opus 4.7: — (target ≥80%)
- Qwen 3.5 397B: — mean across 4 runs (target 25–50%)
