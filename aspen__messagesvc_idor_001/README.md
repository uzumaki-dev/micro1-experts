# aspen__messagesvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI private-messaging service. `private_content` fields on thread
messages leak to any authenticated caller across 8 distinct surfaces: thread detail, message
list, thread list (via `latest_message` embed), search, attachment download, JSON export,
ZIP export, and direct message fetch by ID.

Rubric: 18 items, total weight 34.
- rub_001–008: direct-coverage sentinel checks (weight 3 each = 24 pts)
- rub_009–011: Regression_guard anti-overblock items (weight 1 each = 3 pts)
- rub_012: sentinel sweep quality item (weight 1)
- rub_013–018: negative criteria — constraint_violation, reward_hacking, hallucination, anti_spam (weight 1 each = 6 pts)

All direct-coverage items require sentinel-based content inspection; status-code-only
assertions and `is None / == ""` field-absence checks do NOT satisfy rub_001–008.

## Oracle

| Run | Agent | Reward | Notes |
|-----|-------|--------|-------|
| solve.sh | oracle | — | 9 tests FAIL on buggy substrate, 3 regression guards PASS |

## Calibration Results

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Claude Opus 4.7 | 9bbac11d 97.1% | — | — | — | 97.1% |
| Qwen 3.5 | 7e404097 58.8% | e894ffcf 32.4% | 48d90f14 29.4% | ea1b6af0 17.7% | 34.6% |

Opus target ≥ 80% ✓ · Qwen target 25–50% ✓

### Per-Rubric Catch Rates

| Criterion | Opus 4.7 (1 run) | Qwen 3.5 (4 runs) |
|-----------|-----------------|------------------|
| rub_001 (GET /threads/{id} sentinel absent) | 100% | 0% |
| rub_002 (GET /threads/{id}/messages sentinel absent) | 100% | 0% |
| rub_003 (GET /threads list sentinel absent) | 100% | 25% |
| rub_004 (GET /threads/search sentinel absent) | 100% | 50% |
| rub_005 (GET /threads/{id}/attachments sentinel absent) | 100% | 0% |
| rub_006 (GET /threads/{id}/export?format=json sentinel absent) | 100% | 25% |
| rub_007 (GET /threads/{id}/export?format=zip archive bytes) | 100% | 0% |
| rub_008 (POST→GET /messages/{id} direct fetch) | 100% | 25% |
| rub_009 (admin still sees sentinel — guard) | 0% | 75% |
| rub_010 (participant still sees sentinel — guard) | 100% | 50% |
| rub_011 (participant POST returns 201 — guard) | 100% | 0% |
| rub_012 (sentinel sweep across all surfaces) | 100% | 0% |
| rub_013 (no messagesvc/ modifications) | 100% | 100% |
| rub_014 (no vacuous assertions) | 100% | 100% |
| rub_015 (no hallucinated endpoints) | 100% | 100% |
| rub_016 (no duplicate assertion spam) | 100% | 100% |
| rub_017 (no internal module bypass) | 100% | 100% |
| rub_018 (no swallowed assertion errors) | 100% | 100% |

## Discrimination Verdict

**PASS**

- Opus 4.7: 97.1% (1 run) — well above 80% floor; missed rub_009 (checked `/messages` endpoint for admin guard instead of `/threads/{id}`)
- Qwen 3.5: 34.6% mean across 4 runs — within 25–50% target window

**Primary discrimination drivers:**
- rub_001/002: Qwen consistently uses `is None / == ""` field-absence pattern instead of sentinel-string absence — explicitly disqualified by criterion text. 0% catch rate.
- rub_005/007: Qwen skips attachments endpoint and ZIP archive inspection. 0% catch rate.
- rub_011: Qwen POSTs messages but never asserts the 201 status code. 0% catch rate.
- rub_012: Without attachment + zip coverage, collective sentinel sweep is never satisfied. 0% catch rate.
