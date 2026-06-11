# aspen__proposalsvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI proposal management service. Private `internal_notes`,
per-line-item `margin_code`, `discount_pct`, and `attachments` leak to any authenticated
caller across 7 distinct surfaces: direct GET, list, search, line-items sub-resource,
JSON export, CSV export, and attachment download). Path traversal across proposal attachment
stores is also in scope. Clone copies private fields verbatim, enabling two laundering paths.

Rubric: 20 items, total weight 49.
- rub_001–007: direct-coverage sentinel checks, access_control (weight 3 each = 21 pts)
- rub_008: path-traversal check (weight 2)
- rub_009, rub_011: clone laundering flows, redaction (weight 3 each = 6 pts)
- rub_012–014: regression_guard anti-overblock items (weight 3 each = 9 pts)
- rub_010, rub_015–019: negative criteria — anti_spam, constraint_violation, hallucination, reward_hacking (weight 1+3+1+1+1+3 = 10 pts)
- rub_020: test_quality positive criterion — sentinel sweep across all stranger-accessible endpoints (weight 1 pt)

All direct-coverage items require sentinel-based content inspection; status-code-only
assertions do not satisfy rub_001–007.

## Substrate

* **Source**: Hand-authored FastAPI service (~280 LOC)
* **Commit**: ff8030938e77453ed11bd3f355998ea96eccd38d
* **Description**: In-memory multi-tenant proposal management API. Identity via `X-User-Id`
  header. Admin identity: `admin`. Proposals carry `internal_notes`, `discount_pct`,
  per-line-item `margin_code`, and `attachments` (filename→content map). Endpoints:
  POST/GET/PATCH/search/export/line-items/attachments/clone/send. All read endpoints
  ship without ownership checks. Clone copies private fields verbatim. Path traversal in
  the attachments endpoint allows cross-proposal file reads by splitting the `name`
  parameter on `/`.

## Submission Contract

The agent writes a unified diff (adding files under `tests/exfiltration/`) to
`/repo/answer.diff`. The judge inspects that file as a text artifact — the diff is never
applied to the working tree. Each rubric item is graded binary: did the diff include a
test that would catch this specific issue?

## Calibration Results

Calibrated 2026-06-11. Opus column from run e806b778 (82.4%); Qwen catch rates from 5
runs, 4 of which have full reward-details available. The 0% run (4a75b942) is included
in the 5-run mean; the 4-run mean (excluding it) is 31.9% (σ≈6.4pp, range 23.5–41.2%).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Mean |
|-------|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | — | 100% |
| Claude Opus 4.7 | 82.4% (e806b778) | — | — | — | — | 82.4% |
| Claude Haiku 4.5 | 100% (0075fef6) | — | — | — | — | 100% |
| Qwen 3.5 397B | 41.2% (62b6ffbe) | 23.5% (a48222db) | 33.3% (a2b835f8) | 29.4% (7b354d57) | 0% (4a75b942) | 25.5% |

Raw scores: Opus 42/51 pts (e806b778). Qwen 4-run mean 31.9% (excluding 4a75b942 which
has no reward-details); 5-run mean 25.5%.

### Per-Rubric Catch Rates

Opus: 1 calibration run (e806b778). Qwen: 4 runs with full reward-details (62b6ffbe,
a48222db, a2b835f8, 7b354d57); 4a75b942 excluded from per-criterion breakdown.

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (stranger GET /{id} — internal_notes sentinel absent unconditionally) | 100% | 0% |
| rub_002 (list — internal_notes or margin_code sentinel absent from body) | 100% | 25% |
| rub_003 (search — private content sentinel absent from body) | 100% | 50% |
| rub_004 (line-items — margin_code sentinel absent unconditionally) | 100% | 0% |
| rub_005 (JSON export — internal_notes sentinel absent unconditionally) | 100% | 0% |
| rub_006 (CSV export — sentinel absent in rows) | 100% | 0% |
| rub_007 (attachments download — attachment sentinel absent unconditionally) | 100% | 0% |
| rub_008 (path traversal — attachment sentinel absent) | 100% | 25% |
| rub_009 (clone-then-PATCH — internal_notes absent from PATCH response) | 0% | 0% |
| rub_010 (no off-topic CRUD spam — anti_spam) | 100% | 100% |
| rub_011 (clone-then-export — internal_notes absent from JSON export) | 0% | 0% |
| rub_012 (owner still reads internal_notes — anti-overblock) | 100% | 100% |
| rub_013 (admin still reads internal_notes — anti-overblock) | 100% | 100% |
| rub_014 (non-admin can create and list own proposal — anti-overblock) | 100% | 75% |
| rub_015 (no proposalsvc/ source modifications) | 100% | 100% |
| rub_016 (no files outside tests/exfiltration/) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no hallucinated model fields) | 100% | 100% |
| rub_019 (no status-code-only cross-owner assertions) | 100% | 0% |
| rub_020 (sentinel sweep across all stranger-accessible endpoints — test_quality) | 100% | 0% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 82.4% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 25.5% mean across 5 runs ✓ (target 25–50%)

The primary discrimination levers are the per-endpoint sentinel body check requirements
(rub_001, rub_004–rub_007) and rub_019 (no status-code-only cross-owner assertions,
weight 3). Opus unconditionally inspects all 7 primary stranger-access endpoints for
absent sentinel content; Qwen consistently falls back to `assert r.status_code == 403`
for direct-access endpoint tests (rub_001, rub_004–007), occasionally passing list or
search (rub_002/003) via owner-exclusion or empty-result checks (25–50% catch rate
across 4 detailed runs). rub_019, rub_020, and the laundering flows (rub_009, rub_011) are
missed by Qwen across all 4 detailed runs. The clone laundering flows are also missed
by Opus (rub_009, rub_011 = 0%), providing future discrimination headroom. Qwen scores show
meaningful variance across 4 detailed runs (σ≈6.4pp, range 23.5–41.2%); a 5th run
(4a75b942) scored 0%, pulling the 5-run mean to 25.5% — at the lower edge of the
target band.

_Note: Haiku 4.5 oracle-verification run (0075fef6) scored 100%._

## Reward Details

Total rubric weight: 49.0 across 20 items (6 negative = 30%).

| Rubric | Weight | Category | Polarity |
|---|---|---|---|
| rub_001 | 3.0 | access_control | positive |
| rub_002 | 3.0 | access_control | positive |
| rub_003 | 3.0 | access_control | positive |
| rub_004 | 3.0 | access_control | positive |
| rub_005 | 3.0 | access_control | positive |
| rub_006 | 3.0 | access_control | positive |
| rub_007 | 3.0 | access_control | positive |
| rub_008 | 2.0 | traversal | positive |
| rub_009 | 3.0 | redaction | positive |
| rub_010 | 1.0 | anti_spam | **negative** |
| rub_011 | 3.0 | redaction | positive |
| rub_012 | 3.0 | regression_guard | positive |
| rub_013 | 3.0 | regression_guard | positive |
| rub_014 | 3.0 | regression_guard | positive |
| rub_015 | 3.0 | constraint_violation | **negative** |
| rub_016 | 1.0 | constraint_violation | **negative** |
| rub_017 | 1.0 | hallucination | **negative** |
| rub_018 | 1.0 | hallucination | **negative** |
| rub_019 | 3.0 | reward_hacking | **negative** |
| rub_020 | 1.0 | test_quality | positive |
