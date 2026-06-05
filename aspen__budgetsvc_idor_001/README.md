# aspen__budgetsvc_idor_001

## Status

Budget management service leaks private financial data to any authenticated user because
read, list, search, export, items, and attachments endpoints perform no ownership checks.
The task rewards tests that verify: (1) a stranger cannot read another owner's
`budget_memo`, `fiscal_code`, or `allocation_code`; (2) a "clone-then-mutate"
laundering flow does not inherit private fields into the attacker's copy; and
(3) legitimate owner, admin, collaborator, and public-visibility flows are not over-blocked.

## Substrate

* **Source**: Hand-authored FastAPI service (~175 LOC)
* **Commit**: f19f6a3cadd47e2a1c25caad6c542060b3c46ffa
* **Description**: In-memory multi-tenant budget API. Identity via `X-User-Id` header.
  Budgets carry `budget_memo`, `fiscal_code`, per-item `allocation_code`, and `attachments`
  (file map). Endpoints: POST/GET/PATCH/search/export/items/attachments/clone/submit.
  All read endpoints ship without ownership checks. Clone copies private fields verbatim.
  Path traversal in the attachments endpoint allows cross-budget file reads.

## Submission Contract

The agent writes a unified diff (adding files under `tests/exfiltration/`) to
`/repo/answer.diff`. The judge inspects that file as a text artifact — the diff is never
applied to the working tree. Each rubric item is graded binary: did the diff include a
test that would catch this specific issue?

## Final Calibration Results

| model | run | reward | mean | verdict |
|---|---|---:|---:|---|
| anthropic/claude-haiku-4-5-20251001 (oracle) | 501b32a7 | 100.0% | 100.0% | verifier wiring passes |
| anthropic/claude-opus-4-7 | abe7c465 | 87.2% | 87.2% | passes target (≥80%) |
| openrouter/qwen/qwen3.5-397b-a17b | 475e4317 | 40.4% | | |
| openrouter/qwen/qwen3.5-397b-a17b | 0d31b8f8 | 44.7% | | |
| openrouter/qwen/qwen3.5-397b-a17b | a11f29b5 | 38.3% | | |
| openrouter/qwen/qwen3.5-397b-a17b | a4efadbd | 44.7% | 42.0% | within target range (25–50%) |

*One additional run excluded from calibration: 089a1980 (system failure, 0%).*

**Discrimination Verdict**: DISCRIMINATIVE. Opus lands above the 80% floor (87.2%, run abe7c465) and the mean across all four valid Qwen runs is 42.0%, within the 25–50% target band. The primary discrimination lever is rub_019 (reward_hacking: body-inspection requirement) — Opus inspects all 7 primary stranger-access endpoints with sentinel-absence checks, while every Qwen run relied on status-code-only assertions for GET /budgets/{id}, /items, export json, export csv, and attachments. The clone laundering flows (rub_009–011) further separate Opus from Qwen; no Qwen run discovered the chained PATCH/submit/export laundering patterns. rub_001 (GET /budgets/{id} sentinel body check) was missed by all Qwen runs, which substituted status-code-only 403 assertions.

## Reward Details

Total rubric weight: 47.0 across 20 items (6 negative = 30%).

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
| rub_009 | 2.0 | redaction | positive |
| rub_010 | 2.0 | redaction | positive |
| rub_011 | 2.0 | redaction | positive |
| rub_012 | 3.0 | regression_guard | positive |
| rub_013 | 3.0 | regression_guard | positive |
| rub_014 | 3.0 | constraint_violation | **negative** |
| rub_015 | 1.0 | constraint_violation | **negative** |
| rub_016 | 1.0 | hallucination | **negative** |
| rub_017 | 1.0 | hallucination | **negative** |
| rub_018 | 2.0 | redaction | positive |
| rub_019 | 3.0 | reward_hacking | **negative** |
| rub_020 | 1.0 | anti_spam | **negative** |

## Verdict Details

- Opus score ≥ 80%: **yes** (87.2%, run abe7c465)
- Qwen mean in 25–50%: **yes** (42.0% across 4 valid runs: 40.4%, 44.7%, 38.3%, 44.7%)
- Negative rubric share: 6/20 = 30% ✓
- Final: **PASS**
