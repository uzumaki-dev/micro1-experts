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

## Calibration Results

Calibrated 2026-06-02. Opus column from run 9bbac11d (97.1%); Qwen catch rates derived
across all 4 runs (7e404097, e894ffcf, 48d90f14, ea1b6af0).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 97.1% (9bbac11d) | — | — | — | 97.1% |
| Qwen 3.5 397B | 58.8% (7e404097) | 32.4% (e894ffcf) | 29.4% (48d90f14) | 17.7% (ea1b6af0) | 34.6% |

Raw scores: Opus 33/34 pts (9bbac11d), Qwen mean 11.8/34 pts across 4 runs.

### Per-Rubric Catch Rates

Opus: 1 calibration run (9bbac11d). Qwen: computed across all 4 runs; other Qwen runs show
same item-level pattern (rub_001–008 fail, rub_013–018 pass consistently).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /threads/{id} sentinel absent) | 100% | 0% |
| rub_002 (GET /threads/{id}/messages sentinel absent) | 100% | 0% |
| rub_003 (GET /threads list sentinel absent) | 100% | 25% |
| rub_004 (GET /threads/search sentinel absent) | 100% | 50% |
| rub_005 (GET /threads/{id}/attachments sentinel absent) | 100% | 0% |
| rub_006 (GET /threads/{id}/export?format=json sentinel absent) | 100% | 25% |
| rub_007 (GET /threads/{id}/export?format=zip archive bytes) | 100% | 0% |
| rub_008 (POST→GET /messages/{id} direct fetch) | 100% | 25% |
| rub_009 (admin still sees sentinel — guard) | ~0% | 75% |
| rub_010 (participant still sees sentinel — guard) | ~100% | 50% |
| rub_011 (participant POST returns 201 — guard) | ~100% | 0% |
| rub_012 (sentinel sweep across all surfaces) | ~100% | 0% |
| rub_013 (no messagesvc/ modifications) | 100% | 100% |
| rub_014 (no vacuous assertions) | 100% | 100% |
| rub_015 (no hallucinated endpoints) | 100% | 100% |
| rub_016 (no duplicate assertion spam) | 100% | 100% |
| rub_017 (no internal module bypass) | 100% | 100% |
| rub_018 (no swallowed assertion errors) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 97.1% (1 run) ✓ (target ≥ 80%)
- Qwen 3.5 397B: 34.6% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001/002 (Qwen consistently writes `is None / == ""` field-absence
assertions instead of sentinel-string absence checks — explicitly disqualified by criterion
text) plus rub_005/007 (Qwen skips the attachment and ZIP surfaces entirely) and rub_011/012
(no POST-201 guard, no collective sentinel sweep). Opus missed only rub_009 (checked
`/threads/{id}/messages` for admin visibility instead of `/threads/{id}`).
