# aspen__timesheetsvc_idor_001

## Status

Timesheet management service leaks private billing data to any authenticated user because
read, list, search, export, entries, and receipts endpoints perform no ownership checks.
The task rewards tests that verify: (1) stranger cannot read another owner's
`internal_notes`, `private_rate`, `rate_code`, or receipt bytes; (2) a "clone-then-mutate"
laundering flow does not inherit private fields into the attacker's copy; and (3) legitimate
owner, admin, collaborator, and public-visibility flows are not over-blocked.

## Substrate

* **Source**: Hand-authored FastAPI service (~170 LOC)
* **Commit**: 4564d73b645c75185d190d6d516976e1f5771c25
* **Description**: In-memory multi-tenant timesheet API. Identity via `X-User-Id` header.
  Timesheets carry `internal_notes`, `private_rate`, per-entry `rate_code`, and `receipts`
  (file map). Endpoints: POST/GET/PATCH/search/export/entries/receipts/clone/submit.
  All read endpoints ship without ownership checks. Clone copies private fields verbatim.
  Path traversal in the receipts endpoint allows cross-timesheet file reads.

## Submission Contract

The agent writes a unified diff (adding files under `tests/exfiltration/`) to
`/repo/answer.diff`. The judge inspects that file as a text artifact — the diff is never
applied to the working tree. Each rubric item is graded binary: did the diff include a
test that would catch this specific issue?

## Final Calibration Results

| model | runs | rewards | mean | verdict |
|---|---:|---|---:|---|
| anthropic/claude-haiku-4-5-20251001 (oracle) | 1 | 100.0% | 100.0% | verifier wiring passes |
| anthropic/claude-opus-4-7 | 1 | 81.3% | 81.3% | passes target (≥80%) |
| openrouter/qwen/qwen3.5-397b-a17b | 4 | 33.3%, 37.5%, 43.8%, 39.6% | 38.6% | within target range (25–50%) |

*One additional Qwen run (fbb67a27) failed at the system level (0%) and is excluded from calibration.*

**Discrimination Verdict**: DISCRIMINATIVE. Opus lands above the 80% floor (81.3%) and all four valid Qwen runs fall within the 25–50% target band (33.3%–43.8%), producing a 42.7 pp spread. The laundering flows (rub_009–011) and comprehensive sentinel sweep (rub_017) are the primary discrimination levers — Opus catches the sentinel-based access-control items but misses all three clone laundering flows; Qwen further misses most body-inspection items, relying on status-code-only assertions.

## Reward Details

Total rubric weight: 48.0 across 17 items.

| Rubric | Weight | Category |
|---|---|---|
| rub_001 | 3.0 | access_control |
| rub_002 | 3.0 | access_control |
| rub_003 | 3.0 | access_control |
| rub_004 | 3.0 | access_control |
| rub_005 | 3.0 | access_control |
| rub_006 | 3.0 | access_control |
| rub_007 | 3.0 | access_control |
| rub_008 | 2.0 | traversal |
| rub_009 | 3.0 | redaction |
| rub_010 | 3.0 | redaction |
| rub_011 | 3.0 | redaction |
| rub_012 | 3.0 | regression_guard |
| rub_013 | 3.0 | regression_guard |
| rub_014 | 2.0 | regression_guard |
| rub_015 | 2.0 | regression_guard |
| rub_016 | 3.0 | regression_guard |
| rub_017 | 3.0 | test_quality |

## Verdict Details

- Opus score ≥ 80%: yes (81.3%)
- All four Qwen runs in 25–50%: yes (33.3%, 37.5%, 43.8%, 39.6%)
- Final: PASS
