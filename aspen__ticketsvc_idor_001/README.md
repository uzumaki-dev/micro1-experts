# aspen__ticketsvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI support-ticket service. Private `internal_notes` and
`type="internal"` comments leak to any authenticated caller across 9 distinct surfaces:
direct GET, list, search, JSON export, ZIP export, attachment download, comments endpoint,
clone→GET laundering, and clone→export laundering. Path traversal in attachment names
reaches a global private store.

Rubric: 16 items, total weight 44. All direct-coverage items require sentinel-based
content inspection (status-code-only assertions do not pass).

## Calibration Results

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Claude Opus 4.7 | - | - | - | - | - |
| Qwen 3.5 | - | - | - | - | - |

### Per-Rubric Catch Rates

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /{id} internal_notes) | - | - |
| rub_002 (list internal_notes) | - | - |
| rub_003 (search internal_notes) | - | - |
| rub_004 (export json) | - | - |
| rub_005 (export zip archive) | - | - |
| rub_006 (private attachment) | - | - |
| rub_007 (internal comments) | - | - |
| rub_008 (clone→GET) | - | - |
| rub_009 (clone→export) | - | - |
| rub_010 (agent sees notes — guard) | - | - |
| rub_011 (agent sees internal comments — guard) | - | - |
| rub_012 (reporter write surface — guard) | - | - |
| rub_013 (public attachments — guard) | - | - |
| rub_014 (path traversal) | - | - |
| rub_015 (reporter reads own desc — guard) | - | - |
| rub_016 (sentinel sweep) | - | - |

## Discrimination Verdict

**PENDING CALIBRATION**

Expected: Opus ~86%, Qwen ~32%
