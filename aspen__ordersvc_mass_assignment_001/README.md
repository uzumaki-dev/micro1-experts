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
- **Commit**: FILL_AFTER_DOCKER_BUILD
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

> Fill in after Realm calibration runs are complete.

| model | runs | rewards | mean | verdict |
|---|---:|---|---:|---|
| micro1/oracle | 1 | — | — | — |
| anthropic/claude-opus-4-7 | 1 | — | — | — |
| openrouter/qwen/qwen3.5 | 4 | —, —, —, — | — | — |

**Discrimination Verdict**: PENDING

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
