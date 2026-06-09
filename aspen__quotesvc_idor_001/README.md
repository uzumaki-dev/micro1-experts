# aspen__quotesvc_idor_001

## Task Summary

A sales quoting FastAPI service (`quotesvc`) has an IDOR vulnerability: no
ownership checks exist on any read, list, search, export, line-items, or attachment
endpoint. Any authenticated user can read any other user's private quote — including
sensitive `internal_notes`, line-item `vendor_code` fields, and attachment bytes. The
`fork` endpoint additionally inherits private fields verbatim, enabling a laundering
pattern (fork → PATCH/send).

The agent must write a sentinel-based test suite covering 10 direct-coverage surfaces
and 3 anti-overblock regression guards.

## Rubric

20 binary criteria, total weight 51.

| Category | Items | Weight |
|----------|-------|--------|
| access_control | rub_001–rub_007 | 21 |
| traversal | rub_008 | 2 |
| redaction (laundering) | rub_009–rub_010 | 6 |
| regression_guard | rub_011–rub_013 | 9 |
| test_quality | rub_014 | 3 |
| constraint_violation (negative) | rub_015, rub_019 | 4 |
| hallucination (negative) | rub_016 | 1 |
| reward_hacking (negative) | rub_017, rub_018 | 4 |
| anti_spam (negative) | rub_020 | 1 |

## Calibration Results

*Not yet calibrated — fill in after rv run + Realm eval.*

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | — | — | — | — | — |
| Claude Opus 4.7 | — | — | — | — | — |
| Qwen 3.5 397B | — | — | — | — | — |

## Discrimination Verdict

*Pending calibration.*
