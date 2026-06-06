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

Calibration TBD.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | — | — | — | — | — |
| Claude Opus 4.7 | — | — | — | — | — |
| Qwen 3.5 397B | — | — | — | — | — |

## Discrimination Verdict

**PENDING CALIBRATION**

Target: Opus ≥ 80%, Qwen 25–50% across 4 runs.
