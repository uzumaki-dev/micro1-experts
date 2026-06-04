# aspen__patientsvc_idor_001

## Status

Medical records service leaks private patient data to any authenticated user because
read, list, search, labs, medications, export, and attachments endpoints perform no
ownership checks. A `refer` endpoint copies all private fields verbatim into the
attacker's new record. The task rewards tests that verify: (1) stranger cannot read
another patient's `diagnosis`, `clinical_notes`, `insurance_id`, `lab_results`,
`medications`, or attachment bytes; (2) a "refer-then-read/export" laundering flow
does not inherit private fields into the attacker's copy; and (3) legitimate patient,
assigned-doctor, and admin flows are not over-blocked.

## Substrate

* **Source**: Hand-authored FastAPI service
* **Commit**: 98f620c03f3e1dfaa38ca6ccbd629a2769498578
* **Description**: In-memory multi-tenant medical records API. Identity via `X-User-Id`
  header; role inferred from prefix (`admin` → admin, `dr_*` → doctor, else → patient).
  Records carry `diagnosis`, `clinical_notes`, `insurance_id`, `lab_results` (dict),
  `medications` (list), and `attachments` (file map). All read endpoints ship without
  ownership checks. `refer` copies private fields verbatim.

## Submission Contract

The agent writes a unified diff (adding files under `tests/exfiltration/`) to
`/repo/answer.diff`. The judge inspects that file as a text artifact — the diff is
never applied to the working tree. Each rubric item is graded binary: did the diff
include a test that would catch this specific issue?

## Final Calibration Results

| model | runs | rewards | mean | verdict |
|---|---:|---|---:|---|
| anthropic/claude-haiku-4-5-20251001 (oracle) | — | — | — | pending |
| anthropic/claude-opus-4-7 | — | — | — | pending |
| openrouter/qwen/qwen3.5-397b-a17b | — | — | — | pending |

**Discrimination Verdict**: PENDING

## Reward Details

Total rubric weight: 47.0 across 18 items.

| Rubric | Weight | Category |
|---|---|---|
| rub_001 | 3.0 | access_control |
| rub_002 | 3.0 | access_control |
| rub_003 | 3.0 | access_control |
| rub_004 | 3.0 | access_control |
| rub_005 | 3.0 | access_control |
| rub_006 | 2.0 | traversal |
| rub_007 | 3.0 | redaction |
| rub_008 | 3.0 | redaction |
| rub_009 | 3.0 | regression_guard |
| rub_010 | 3.0 | regression_guard |
| rub_011 | 3.0 | regression_guard |
| rub_012 | 3.0 | test_quality |
| rub_013 | 3.0 | constraint_violation (Negative) |
| rub_014 | 1.0 | hallucination (Negative) |
| rub_015 | 1.0 | anti_spam (Negative) |
| rub_016 | 1.0 | reward_hacking (Negative) |
| rub_017 | 3.0 | reward_hacking (Negative) |
| rub_018 | 1.0 | hallucination (Negative) |

## Verdict Details

- Opus score ≥ 80%: pending
- All four Qwen runs in 25–50%: pending
- Final: PENDING
