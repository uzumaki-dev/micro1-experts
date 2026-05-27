# aspen__invoicesvc_idor_001

## Task Summary

An invoicing/billing FastAPI service (`invoicesvc`) has an IDOR vulnerability: no
ownership checks exist on any read, list, search, export, line-items, or attachment
endpoint. Any authenticated user can read any other user's private invoice — including
sensitive `internal_notes`, line-item `cost_code` fields, and attachment bytes. The
`duplicate` endpoint additionally inherits private fields verbatim, enabling a
laundering pattern (duplicate → PATCH/share/export).

The agent must write a sentinel-based test suite covering 11 direct-coverage surfaces
and 6 anti-overblock regression guards.

## Calibration Results

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Claude Opus 4.7 | - | - | - | - | - |
| Qwen 3.5 | - | - | - | - | - |

### Per-Rubric Catch Rates

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /invoices/{id}) | - | - |
| rub_002 (list) | - | - |
| rub_003 (search) | - | - |
| rub_004 (line-items) | - | - |
| rub_005 (export json) | - | - |
| rub_006 (export csv) | - | - |
| rub_007 (attachment download) | - | - |
| rub_008 (path traversal) | - | - |
| rub_009 (duplicate+patch) | - | - |
| rub_010 (duplicate+share) | - | - |
| rub_011 (duplicate+export) | - | - |
| rub_012 (owner overblock) | - | - |
| rub_013 (admin overblock) | - | - |
| rub_014 (collaborator overblock) | - | - |
| rub_015 (public invoice overblock) | - | - |
| rub_016 (create+list own overblock) | - | - |
| rub_017 (sentinel sweep) | - | - |

## Discrimination Verdict

**PENDING** — fill after calibration.

Rationale: <to be filled>
