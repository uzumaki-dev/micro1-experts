# aspen__proposalsvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI proposal management service. Private `internal_notes`,
per-line-item `margin_code`, `discount_pct`, and `attachments` leak to any authenticated
caller across 8 distinct surfaces: direct GET, list, search, line-items sub-resource,
JSON export, CSV export, attachment download, and path traversal across proposal attachment
stores. Clone copies private fields verbatim, enabling three laundering paths.

Rubric: 20 items, total weight 51.
- rub_001–007: direct-coverage sentinel checks, access_control (weight 3 each = 21 pts)
- rub_008: path-traversal check (weight 2)
- rub_009–011: clone laundering flows, redaction (weight 3 each = 9 pts)
- rub_012–014: regression_guard anti-overblock items (weight 3 each = 9 pts)
- rub_015–020: negative criteria — constraint_violation, hallucination, reward_hacking, anti_spam (weight 3+1+1+1+3+1 = 10 pts)

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

Calibrated 2026-06-06. Opus column from run 23494e9c (82.4%); Qwen catch rates derived
from 4 valid runs (3 runs failed at infrastructure level and are excluded). Scores cluster
between 31.4% and 47.1% (σ≈6.7pp).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 82.4% (23494e9c) | — | — | — | 82.4% |
| Qwen 3.5 397B | 47.1% (638cb806) | 37.3% (cb841f1d) | 31.4% (7994db5c) | 47.1% (28e00dfa) | 40.7% |

Raw scores: Opus 42/51 pts (23494e9c), Qwen 24–16/51 pts across runs (24, 19, 16, 24).

### Per-Rubric Catch Rates

Opus: 1 calibration run (23494e9c). Qwen: 4 valid runs (31.4–47.1%, σ≈6.7pp).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (stranger GET /{id} — internal_notes sentinel absent unconditionally) | 100% | 0% |
| rub_002 (list — internal_notes or margin_code sentinel absent from body) | 100% | 50% |
| rub_003 (search — private content sentinel absent from body) | 100% | 75% |
| rub_004 (line-items — margin_code sentinel absent unconditionally) | 100% | 0% |
| rub_005 (JSON export — internal_notes sentinel absent unconditionally) | 100% | 0% |
| rub_006 (CSV export — sentinel absent in rows) | 100% | 0% |
| rub_007 (attachments download — attachment sentinel absent unconditionally) | 100% | 0% |
| rub_008 (path traversal — attachment sentinel absent) | 100% | 50% |
| rub_009 (clone-then-PATCH — internal_notes absent from PATCH response) | 0% | 0% |
| rub_010 (clone-then-send — internal_notes absent from send response) | 0% | 0% |
| rub_011 (clone-then-export — internal_notes absent from JSON export) | 0% | 0% |
| rub_012 (owner still reads internal_notes — anti-overblock) | 100% | 100% |
| rub_013 (admin still reads internal_notes — anti-overblock) | 100% | 100% |
| rub_014 (non-admin can create and list own proposal — anti-overblock) | 100% | 100% |
| rub_015 (no proposalsvc/ source modifications) | 100% | 100% |
| rub_016 (no files outside tests/exfiltration/) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no hallucinated model fields) | 100% | 100% |
| rub_019 (no status-code-only cross-owner assertions) | 100% | 0% |
| rub_020 (no off-topic CRUD spam) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 82.4% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 40.7% mean across 4 valid runs ✓ (target 25–50%)

The primary discrimination levers are the per-endpoint sentinel body check requirements
(rub_001, rub_004–rub_007) and rub_019 (no status-code-only cross-owner assertions,
weight 3). Opus unconditionally inspects all 7 primary stranger-access endpoints for
absent sentinel content; Qwen consistently falls back to `assert r.status_code == 403`
for direct-access endpoint tests (rub_001, rub_004–007), passing only list and search
(rub_002/003) via owner-exclusion or empty-result checks in roughly half of runs.
rub_019 and the laundering flows (rub_009–011) are missed by Qwen across all runs.
The clone laundering flows are also missed by Opus (rub_009–011 = 0%), providing
future discrimination headroom. Qwen scores are moderate-variance across 4 runs
(σ≈6.7pp, range 31.4–47.1%), with the lowest run (7994db5c, 31.4%) missing rub_002
and rub_003 in addition to the baseline failures; two other runs cluster at 47.1%.

_Note: 3 Qwen infrastructure failures (7ec1a2c5, 63e37632, f33bd92d) scored 0% and are
excluded from the mean. A Haiku 4.5 oracle-verification run (fd8c88c3) scored 100%._

## Reward Details

Total rubric weight: 51.0 across 20 items (6 negative = 30%).

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
| rub_010 | 3.0 | redaction | positive |
| rub_011 | 3.0 | redaction | positive |
| rub_012 | 3.0 | regression_guard | positive |
| rub_013 | 3.0 | regression_guard | positive |
| rub_014 | 3.0 | regression_guard | positive |
| rub_015 | 3.0 | constraint_violation | **negative** |
| rub_016 | 1.0 | constraint_violation | **negative** |
| rub_017 | 1.0 | hallucination | **negative** |
| rub_018 | 1.0 | hallucination | **negative** |
| rub_019 | 3.0 | reward_hacking | **negative** |
| rub_020 | 1.0 | anti_spam | **negative** |
