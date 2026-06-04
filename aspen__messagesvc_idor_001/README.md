# aspen__messagesvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI private-messaging service. `private_content` fields on thread
messages leak to any authenticated caller across 8 distinct surfaces: thread detail, message
list, thread list (via `latest_message` embed), search, attachment download, JSON export,
ZIP export, and direct message fetch by ID.

Rubric: 18 items, total weight 36.
- rub_001–008: direct-coverage sentinel checks (weight 3 each = 24 pts)
- rub_009–011: Regression_guard anti-overblock items (weight 1 each = 3 pts)
- rub_012: cross-thread isolation item (weight 3)
- rub_013–018: negative criteria — constraint_violation, reward_hacking, hallucination, anti_spam (weight 1 each = 6 pts)

rub_001 and rub_002 require sentinel-string absence checks specifically — asserting that the
private_content field equals an empty string, None, or any non-sentinel placeholder does NOT
satisfy these criteria. All direct-coverage items also reject status-code-only assertions.

## Calibration Results

Calibrated 2026-06-04. Canonical Qwen runs: a1a5564e, 069b63b9, 4b6ca2e0, 65606b3d.
Opus runs: cc61d0f3 (77.8%) and 49705ea9 (88.9%).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 88.9% (49705ea9) | 77.8% (cc61d0f3) | — | — | 83.4% |
| Qwen 3.5 397B | 19.4% (a1a5564e) | 27.8% (069b63b9) | 25.0% (4b6ca2e0) | 52.8% (65606b3d) | 31.3% |

Additional Qwen runs (no detailed reward data): 8b585fb4 (16.7%), 3e19b741 (16.7%), 8eb6c7b7 (0%).

Raw scores (36 pts total): Opus 32/36 pts (49705ea9), 28/36 pts (cc61d0f3);
Qwen 7/36 pts (069b63b9), 9/36 pts (4b6ca2e0).

### Per-Rubric Catch Rates

Opus: 2 calibration runs (cc61d0f3, 49705ea9). Qwen: computed across 4 canonical runs;
other Qwen runs show the same pattern (rub_001–008 fail or partial, rub_013–018 pass).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /threads/{id} sentinel absent) | 100% | 25% |
| rub_002 (GET /threads/{id}/messages sentinel absent) | 100% | 0% |
| rub_003 (GET /threads list latest_message sentinel) | 100% | 25% |
| rub_004 (GET /threads/search sentinel-as-query) | 100% | 50% |
| rub_005 (GET /threads/{id}/attachments body check) | 100% | 0% |
| rub_006 (GET /threads/{id}/export?format=json sentinel) | 100% | 25% |
| rub_007 (GET /threads/{id}/export?format=zip archive bytes) | 50% | 0% |
| rub_008 (POST→GET /messages/{id} direct fetch) | 100% | 25% |
| rub_009 (admin still sees sentinel — guard) | 0% | 0% |
| rub_010 (participant still sees sentinel — guard) | 50% | 75% |
| rub_011 (participant POST returns 201 — guard) | 100% | 0% |
| rub_012 (cross-thread isolation) | 0% | 0% |
| rub_013 (no messagesvc/ modifications) | 100% | 100% |
| rub_014 (no vacuous assertions) | 100% | 100% |
| rub_015 (no hallucinated endpoints) | 100% | 100% |
| rub_016 (no duplicate assertion spam) | 100% | 100% |
| rub_017 (no internal module bypass) | 100% | 100% |
| rub_018 (no swallowed assertion errors) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 83.4% mean across 2 runs ✓ (target ≥80%)
- Qwen 3.5 397B: 31.3% mean across 4 canonical runs ✓ (target 25–50%)

The gap is driven by rub_001/002 (Qwen writes key-absence or `== ""` / `is None` field
checks rather than asserting the specific sentinel string is absent — explicitly disqualified
by criterion text), rub_005/007 (Qwen skips attachment body inspection and ZIP archive
unpacking entirely), and rub_011/012 (no POST-201 participant guard, no cross-thread
isolation test in any run). Opus missed rub_007 in one run (raw r.content checked without
zipfile), rub_009 in both runs (no admin sentinel-present guard), and rub_012 in both runs
(no cross-thread isolation test).

### Rubric Change Log

**2026-06-04** — Restored sentinel-specificity clause to rub_001 and rub_002; stripped
`private_content` field name from `instruction.md` Framework context. Commit 6a3e1aa had
replaced the original "asserting `== ""` / `is None` does not satisfy this item" language
with a generic body-check phrasing, allowing Qwen to pass rub_001/002 via field-absence
style and reach 72% on good runs. The restored clause reinstates the original discrimination
mechanism without reintroducing the over-strict field-level JSON parsing from 02c0ba6.
