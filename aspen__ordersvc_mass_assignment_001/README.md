# aspen__ordersvc_mass_assignment_001

## Status

A FastAPI order-management service (`ordersvc`) does not enforce field-level role checks
on its PATCH and POST endpoints. Any authenticated user can include privileged fields
(`status`, `discount_pct`, `payment_status`) in PATCH /orders/{id} or POST /orders and
the server applies them without restriction. This task rewards tests that verify each
privileged field cannot be overridden by a non-admin caller, while preserving legitimate
owner and admin write flows.

## Substrate

- **Source**: Hand-authored
- **Commit**: 4770f2ae0f5d14d12e82ec2cfba86d3672155c15
- **Description**: Small FastAPI service (~200 LOC) with an in-memory order store.
  Roles: `admin` (can set any field), regular user (can set `shipping_address`, `notes`
  only). Endpoints: POST /orders, GET /orders, GET /orders/{id}, PATCH /orders/{id},
  POST /orders/{id}/confirm (admin-only), POST /orders/{id}/cancel (owner or admin).

## Submission Contract

The agent writes a unified diff (adding files under `tests/access/`) to `/repo/answer.diff`.
The judge reads that file as a text artifact — the diff is never applied to the working
tree. Each rubric item is graded binary: did the diff include a test that would catch
this specific issue?

## Calibration Results

Calibrated 2026-06-03. Opus column from run 2ac885c1 (100%); Qwen catch rates derived
from all 5 runs (identical item-level pattern across all runs).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Mean |
|-------|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | — | 100% |
| Claude Opus 4.7 | 100% (2ac885c1) | — | — | — | — | 100% |
| Qwen 3.5 397B | 36% (81e28dc9) | 36% (0fcf4405) | 36% (7f687d3b) | 36% (22877be6) | 36% (574bcd2e) | 36% |

Raw scores: Opus 25/25 pts (2ac885c1), Qwen 9/25 pts (all runs).

### Per-Rubric Catch Rates

Opus: 1 calibration run (2ac885c1). Qwen: 5 runs, all identical item-level verdicts.

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (PATCH status → separate GET check) | 100% | 0% |
| rub_002 (PATCH discount_pct → separate GET check) | 100% | 0% |
| rub_003 (PATCH payment_status → separate GET check) | 100% | 0% |
| rub_004 (POST status override → separate GET check) | 100% | 0% |
| rub_005 (POST discount_pct override → separate GET check) | 100% | 0% |
| rub_006 (owner PATCH shipping_address — regression guard) | 100% | 100% |
| rub_007 (admin PATCH status — regression guard) | 100% | 100% |
| rub_008 (owner POST cancel — regression guard) | 100% | 100% |
| rub_009 (all 3 privileged PATCH fields + GET sweep) | 100% | 0% |
| rub_010 (no ordersvc/ modifications) | 100% | 100% |
| rub_011 (no vacuous assertions) | 100% | 100% |
| rub_012 (no hallucinated endpoints) | 100% | 100% |
| rub_013 (no duplicate assertion spam) | 100% | 100% |
| rub_014 (no internal module bypass) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 100% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 36% mean across 5 runs ✓ (target 25–50%)

The gap is driven by rub_001–005 and rub_009 — Qwen never issues a GET after a mutation.
It inspects only the PATCH/POST response body, which the rubric explicitly disqualifies.
All 5 Qwen runs produced zero GET calls and identical item-level verdicts (0pp variance),
confirming near-deterministic inference on the Realm platform.
