# aspen__budgetsvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI budget-management service. Private `budget_memo`, `fiscal_code`,
and per-item `allocation_code` leak to any authenticated stranger across 7 read surfaces:
direct GET, list, search, JSON export, CSV export, items endpoint, and attachment download.
An attachment path-traversal bug allows cross-budget file reads. A clone endpoint copies private
fields verbatim, enabling "clone-then-mutate" laundering flows.

Rubric: 20 items, total weight 47.
- rub_001–007: direct-coverage sentinel checks, access_control (weight 3 each = 21 pts)
- rub_008: path-traversal sentinel check (weight 2)
- rub_009–011: clone laundering flow checks — PATCH/submit/export (weight 2 each = 6 pts)
- rub_012–013: regression_guard anti-overblock items (weight 3 each = 6 pts)
- rub_014: constraint_violation — no budgetsvc/ modifications (weight 3, negative)
- rub_015: constraint_violation — no files outside tests/exfiltration/ (weight 1, negative)
- rub_016–017: hallucination guards — endpoints and fields (weight 1 each, negative)
- rub_018: clone creation response sentinel check, redaction (weight 2)
- rub_019: reward_hacking — requires raw r.text body inspection on ≥4/7 endpoints (weight 3, negative)
- rub_020: test_quality — collective sentinel sweep across all 7 endpoints (weight 1)

All direct-coverage items (rub_001–007, rub_018) require sentinel-based raw HTTP response
body text inspection (`assert sentinel not in r.text`); status-code-only assertions and
parsed-JSON field comparisons do not satisfy these items.

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

Calibrated 2026-06-09. Rubric tightened at this calibration round to require raw HTTP
response body text inspection (`sentinel not in r.text`) for rub_001–005, rub_018, and
rub_019; parsed-JSON field comparisons no longer satisfy these items.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh / Haiku b1386a73) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 87.2% (fa47d7c0) | — | — | — | 87.2% |
| Qwen 3.5 397B | 36.2% (ae989885) | 29.8% (de6ef2b1) | 36.2% (5821326c) | 29.8% (4897dcb1) | 33.0% |

Raw pts: Opus 41/47 (fa47d7c0). Qwen representative run 17/47 (ae989885) and 14/47 (de6ef2b1).

### Per-Rubric Catch Rates

Opus: 1 calibration run (fa47d7c0). Qwen: aggregated across all 4 runs.

| Criterion | Opus 4.7 | Qwen 3.5 (4 runs) |
|-----------|----------|--------------------|
| rub_001 (GET /{id} budget_memo raw-text sentinel) | 100% | 0% |
| rub_002 (list budget_memo/fiscal_code raw-text sentinel) | 100% | 0% |
| rub_003 (search raw-text sentinel) | 100% | 0% |
| rub_004 (items allocation_code raw-text sentinel) | 100% | 0% |
| rub_005 (export json raw-text sentinel) | 100% | 0% |
| rub_006 (export csv raw-text sentinel) | 100% | 50% |
| rub_007 (attachment download raw-text sentinel) | 100% | 0% |
| rub_008 (path traversal sentinel) | 100% | 100% |
| rub_009 (clone-then-PATCH laundering) | 0% | 0% |
| rub_010 (clone-then-submit laundering) | 0% | 0% |
| rub_011 (clone-then-export laundering) | 0% | 0% |
| rub_012 (owner still reads budget_memo — guard) | 100% | 100% |
| rub_013 (admin still reads budget_memo — guard) | 100% | 100% |
| rub_014 (no budgetsvc/ modifications) | 100% | 100% |
| rub_015 (no files outside tests/exfiltration/) | 100% | 100% |
| rub_016 (no hallucinated endpoints) | 100% | 100% |
| rub_017 (no hallucinated fields) | 100% | 100% |
| rub_018 (clone response raw-text sentinel) | 100% | 0% |
| rub_019 (≥4/7 endpoints use raw r.text inspection) | 100% | 0% |
| rub_020 (collective sentinel sweep, test_quality) | 100% | 0% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 87.2% (1 run, fa47d7c0) ✓ (target ≥80%)
- Qwen 3.5 397B: 33.0% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001–007 and rub_018–019 (raw body-text sentinel-absence checks
across all leak surfaces) — Qwen consistently uses status-code-only assertions or parsed-JSON
field comparisons on these and fails all of them. The one exception is rub_006 (CSV export),
where 2 of 4 Qwen runs happened to add raw `not in r.text` checks; the other 2 did not seed
the correct private fields (budget_memo or allocation_code). rub_008 (path traversal) is
reliably caught by all models. The clone laundering flows (rub_009–011) represent the shared
ceiling — Opus also missed these in the calibration run, accounting for the 12.8pp gap from
100%. rub_020 (test_quality) requires collective sentinel sweeps across all 7 endpoints with
raw text inspection, which no Qwen run achieved.

## Reward Details

Total rubric weight: 47.0 across 20 items (6 negative items = 30%).

| Rubric | Weight | Category | Polarity |
|--------|--------|----------|----------|
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
| rub_020 | 1.0 | test_quality | positive |

## Verdict Details

- Opus score ≥ 80%: **yes** (87.2%, run fa47d7c0)
- Qwen mean in 25–50%: **yes** (33.0% across 4 runs: 36.2%, 29.8%, 36.2%, 29.8%)
- Negative rubric share: 6/20 = 30% ✓
- Final: **PASS**
