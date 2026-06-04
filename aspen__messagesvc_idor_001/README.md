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

## Rubric Change Log

**2026-06-04** — Restored sentinel-specificity clause to rub_001 and rub_002; stripped
`private_content` field name from `instruction.md` Framework context.

Background: commit 6a3e1aa replaced the original "Asserting that the private_content field
equals an empty string, None, or any non-sentinel placeholder does not satisfy this item"
language with a generic "verify it is absent from the response body" phrasing. This allowed
Qwen to pass rub_001 and rub_002 by writing `== ""` / `is None` assertions, pushing Qwen
above 70% on good runs. The restored clause reinstates the original discrimination mechanism
(Qwen consistently uses field-absence style; Opus uses sentinel-string absence) without
reintroducing the over-strict field-level JSON parsing from 02c0ba6 that broke Opus.

rub_004 (sentinel-as-query-term) and rub_012 (cross-thread isolation, weight 3) remain from
the 6a3e1aa tightening — these are good additions and are kept.

## Calibration Results

**Pending recalibration.** Prior runs (a0dd76ba, 1406eb17 at 72%/69%) were collected after
6a3e1aa removed the sentinel-specificity clause. Those numbers are invalid for the current
rubric. Expected post-fix behavior:

- Oracle: 100% (solve.sh uses `PRIVATE not in r.text` — satisfies restored clause) ✓
- Opus 4.7: ~97% (Opus writes sentinel-absence checks; restored clause is compatible) ✓
- Qwen 3.5 397B: ~25–45% mean (Qwen uses `== ""` / `is None` style — now disqualified for
  rub_001/002; consistent with original 34.6% calibration before 6a3e1aa)

Pre-6a3e1aa calibration for reference (34-weight rubric, run 2026-06-02):

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 97.1% (9bbac11d) | — | — | — | 97.1% |
| Qwen 3.5 397B | 58.8% (7e404097) | 32.4% (e894ffcf) | 29.4% (48d90f14) | 17.7% (ea1b6af0) | 34.6% |
