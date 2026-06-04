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

| model | run | reward | mean | verdict |
|---|---|---:|---:|---|
| anthropic/claude-haiku-4-5-20251001 (oracle) | 577284cd | 100.0% | 100.0% | verifier wiring passes |
| anthropic/claude-opus-4-7 | 418127de | 82.6% | 82.6% | passes target (≥80%) |
| openrouter/qwen/qwen3.5-397b-a17b | e494e84d | 45.7% | | |
| openrouter/qwen/qwen3.5-397b-a17b | ff1dbac1 | 50.0% | | |
| openrouter/qwen/qwen3.5-397b-a17b | 300e1277 | 43.5% | | |
| openrouter/qwen/qwen3.5-397b-a17b | ea9a7d79 | 28.3% | 41.9% | within target range (25–50%) |

*One additional Qwen run (79cc3ee6) failed at the system level (0%) and is excluded from calibration.*

**Discrimination Verdict**: DISCRIMINATIVE. Opus lands above the 80% floor (82.6%) and all four valid Qwen runs fall within the 25–50% target band (28.3%–50.0%), producing a 40.7 pp spread. The clone laundering flows (rub_009–011) and unified sentinel sweep (rub_017) are the primary discrimination levers — Opus catches all sentinel-based access-control and clone-response items but misses the chained laundering flows; Qwen further misses most body-inspection items, relying on status-code-only assertions.

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

- Opus score ≥ 80%: yes (82.6%, run 418127de; projected ~87% after negative rubric addition)
- All four Qwen runs in 25–50%: yes (28.3%, 43.5%, 45.7%, 50.0%); rub_019 (reward_hacking) is the primary downward discriminator for Qwen
- Negative rubric share: 6/20 = 30% ✓
- Final: PASS
