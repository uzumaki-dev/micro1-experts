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
| anthropic/claude-haiku-4-5-20251001 (oracle) | 5fcc71aa | 100.0% | 100.0% | verifier wiring passes |
| anthropic/claude-opus-4-7 | d4011138 | 87.2% | 87.2% | passes target (≥80%) |
| openrouter/qwen/qwen3.5-397b-a17b | c71c4b62 | 63.8% | | ⚠ above 50% cap |
| openrouter/qwen/qwen3.5-397b-a17b | 85637ba8 | 55.3% | | ⚠ above 50% cap |
| openrouter/qwen/qwen3.5-397b-a17b | 62f1793f | 44.7% | | |
| openrouter/qwen/qwen3.5-397b-a17b | 37c7c806 | 44.7% | | |
| openrouter/qwen/qwen3.5-397b-a17b | 0af2cf65 | 34.0% | 48.5% | mean in range; 2/5 runs above 50% cap |

*One additional Qwen run (1f4a5d99) failed at the system level (0%) and is excluded from calibration.*

**Discrimination Verdict**: PARTIALLY DISCRIMINATIVE. Opus lands above the 80% floor (87.2%). Three of five valid Qwen runs fall within the 25–50% target band (34.0%–44.7%); two runs (85637ba8 at 55.3%, c71c4b62 at 63.8%) exceed the 50% cap. The mean across all five valid Qwen runs is 48.5% (within range), but individual run variance is wider than ideal. The primary discrimination lever is rub_019 (reward_hacking: body-inspection requirement) — Opus inspects all 7 endpoints with sentinel absence checks while Qwen typically guards only 2–3 endpoints with body inspection. The two over-cap Qwen runs wrote additional sentinel body checks (e.g. CSV export, clone body) that pushed their totals above 50%; rubric tightening on rub_019 or weight redistribution may be needed to clamp the ceiling.

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

- Opus score ≥ 80%: **yes** (87.2%, run d4011138)
- Qwen runs in 25–50%: **partial** — 3/5 in range (34.0%, 44.7%, 44.7%); 2/5 above cap (55.3%, 63.8%); mean 48.5%
- Negative rubric share: 6/20 = 30% ✓
- Primary discriminator: rub_019 (reward_hacking) — Qwen runs that pass rub_006/rub_018 with body inspection gain enough weight to breach 50%
- Final: **NEEDS REVIEW** (Qwen ceiling above target on 2 runs)
