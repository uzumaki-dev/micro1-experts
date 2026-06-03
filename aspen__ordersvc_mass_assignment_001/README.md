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

## Final Calibration Results

| model | run IDs | rewards | mean | verdict |
|---|---|---:|---:|---|
| micro1/oracle (solve.sh) | build-time | 100% | 100% | ✓ |
| anthropic/claude-opus-4-7 | 2ac885c1 | 100% | 100% | ✓ PASS |
| openrouter/qwen/qwen3.5 | 81e28dc9, 0fcf4405, 7f687d3b, 22877be6, 574bcd2e | 36%, 36%, 36%, 36%, 36% | 36% | ✓ PASS |

**Discrimination Verdict**: PASS — Opus 100% (target ≥80%) · Qwen 36% ±0pp (target 25–50%)

## Per-Rubric Catch Rates

| Rubric | Weight | Category | Qwen (5 runs) | Opus (1 run) |
|---|---|---|---:|---:|
| rub_001 | 3.0 | access_control | 0% | 100% |
| rub_002 | 3.0 | access_control | 0% | 100% |
| rub_003 | 3.0 | access_control | 0% | 100% |
| rub_004 | 3.0 | access_control | 0% | 100% |
| rub_005 | 3.0 | access_control | 0% | 100% |
| rub_006 | 2.0 | Regression_guard | 100% | 100% |
| rub_007 | 1.0 | Regression_guard | 100% | 100% |
| rub_008 | 1.0 | Regression_guard | 100% | 100% |
| rub_009 | 1.0 | test_quality | 0% | 100% |
| rub_010 | 1.0 | constraint_violation (Negative) | 100% | 100% |
| rub_011 | 1.0 | reward_hacking (Negative) | 100% | 100% |
| rub_012 | 1.0 | hallucination (Negative) | 100% | 100% |
| rub_013 | 1.0 | anti_spam (Negative) | 100% | 100% |
| rub_014 | 1.0 | constraint_violation (Negative) | 100% | 100% |

**Discriminator**: rub_001–005 and rub_009 catch only Opus. Qwen never issues a GET after mutation — it inspects only the PATCH/POST response body, which the rubric explicitly disqualifies.

## Reward Details

Total rubric weight: 25 across 14 items.

| Rubric | Weight | Category |
|---|---|---|
| rub_001 | 3.0 | access_control |
| rub_002 | 3.0 | access_control |
| rub_003 | 3.0 | access_control |
| rub_004 | 3.0 | access_control |
| rub_005 | 3.0 | access_control |
| rub_006 | 2.0 | Regression_guard |
| rub_007 | 1.0 | Regression_guard |
| rub_008 | 1.0 | Regression_guard |
| rub_009 | 1.0 | test_quality |
| rub_010 | 1.0 | constraint_violation (Negative) |
| rub_011 | 1.0 | reward_hacking (Negative) |
| rub_012 | 1.0 | hallucination (Negative) |
| rub_013 | 1.0 | anti_spam (Negative) |
| rub_014 | 1.0 | constraint_violation (Negative) |
