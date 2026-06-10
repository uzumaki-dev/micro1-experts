# aspen__candidatesvc_idor_001

## Task Summary

A recruitment FastAPI service (`candidatesvc`) has an IDOR vulnerability: no
ownership checks exist on any read, list, search, export, assessments, or document
endpoint. Any authenticated user can read any other user's private candidate record —
including sensitive `screening_notes`, assessment `eval_code` fields, and document
bytes. The `clone` endpoint additionally inherits private fields verbatim, enabling
a laundering pattern (clone → PATCH/share/export).

The agent must write a sentinel-based test suite covering 7 direct-coverage surfaces,
3 laundering flows, 3 anti-overblock regression guards, and a sentinel sweep.

## Rubric

20 items: 14 positive + 6 negative. Max score: 50 pts.

| Group | Items | Weight each |
|---|---|---|
| Direct coverage (access_control/ownership) | rub_001–007 | 3.0 |
| Laundering flows (redaction) | rub_008–010 | 3.0 |
| Regression guards | rub_011–013 | 3.0 |
| Test quality | rub_014 | 1.0 |
| Negative (constraint/hallucination/spam) | rub_015–020 | 1.0–3.0 |

## Calibration Results

Pending first eval run.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | — | — | — | — | — |
| Claude Opus 4.7 | — | — | — | — | — |
| Qwen 3.5 | — | — | — | — | — |

## Discrimination Verdict

Pending calibration.
