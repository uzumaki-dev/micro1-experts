# aspen__ticketsvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI support-ticket service. Private `internal_notes` and
`type="internal"` comments leak to any authenticated caller across 9 distinct surfaces:
direct GET, list, search, JSON export, ZIP export, attachment download, comments endpoint,
clone→GET laundering, and path traversal into the global private store.

Rubric: 20 items, total weight 38.
- rub_001–008: direct-coverage sentinel checks (weight 3 each = 24 pts)
- rub_009–012: Regression_guard anti-overblock items (weight 1 each = 4 pts)
- rub_013: path-traversal check (weight 3)
- rub_014: sentinel sweep quality item (weight 1)
- rub_015–020: negative criteria — constraint_violation, reward_hacking, hallucination, anti_spam (weight 1 each = 6 pts)

All direct-coverage items require sentinel-based content inspection; status-code-only
assertions do not satisfy rub_001–008.

## Calibration Results

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Claude Opus 4.7 | - | - | - | - | - |
| Qwen 3.5 | - | - | - | - | - |

### Per-Rubric Catch Rates

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /{id} internal_notes sentinel) | - | - |
| rub_002 (list internal_notes sentinel) | - | - |
| rub_003 (search internal_notes sentinel) | - | - |
| rub_004 (export json sentinel) | - | - |
| rub_005 (export zip archive sentinel) | - | - |
| rub_006 (private attachment sentinel) | - | - |
| rub_007 (internal comments sentinel) | - | - |
| rub_008 (clone→GET sentinel) | - | - |
| rub_009 (agent sees notes — guard) | - | - |
| rub_010 (agent sees internal comments — guard) | - | - |
| rub_011 (reporter write surface — guard) | - | - |
| rub_012 (public attachment — guard) | - | - |
| rub_013 (path traversal) | - | - |
| rub_014 (sentinel sweep quality) | - | - |
| rub_015 (no ticketsvc/ modifications) | - | - |
| rub_016 (no vacuous assertions) | - | - |
| rub_017 (no hallucinated endpoints) | - | - |
| rub_018 (no duplicate assertion spam) | - | - |
| rub_019 (no internal module bypass) | - | - |
| rub_020 (no swallowed assertion errors) | - | - |

## Discrimination Verdict

**PENDING CALIBRATION**

Expected: Opus ≥80%, Qwen 25–50%
