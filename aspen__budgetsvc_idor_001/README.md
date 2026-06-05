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
* **Commit**: FILL_AFTER_DOCKER_BUILD
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
| oracle | — | 100.0% | 100.0% | verifier wiring passes |
| anthropic/claude-opus-4-7 | TBD | TBD | TBD | TBD |
| openrouter/qwen/qwen3.5-397b-a17b | TBD | | | |
| openrouter/qwen/qwen3.5-397b-a17b | TBD | | | |
| openrouter/qwen/qwen3.5-397b-a17b | TBD | | | |
| openrouter/qwen/qwen3.5-397b-a17b | TBD | TBD | TBD | TBD |

**Discrimination Verdict**: PENDING CALIBRATION

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

- Opus score ≥ 80%: TBD
- Qwen mean in 25–50%: TBD
- Negative rubric share: 6/20 = 30% ✓
- Final: **PENDING**
