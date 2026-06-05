# aspen__paymentsvc_idor_001

## Status

This task rewards tests that verify ownership isolation in a payment management service.
The shipped code exposes private payment data (private_notes, line-item fee_codes, and
document bytes) to any authenticated user due to missing ownership checks on read, list,
search, export, line-items, and document endpoints. A secondary clone endpoint compounds
the leak by inheriting private fields without scrubbing.

## Substrate

* **Source**: Hand-authored FastAPI service (~300 LOC)
* **Commit**: f53365bcedcd2974001840e052bd78a13e99342b
* **Description**: Small in-memory multi-tenant payment API with roles: Admin, Owner,
  Stranger. Payments have private_notes, line items with fee_code, and documents dict.
  Caller identified by X-User-Id header. No authentication middleware — ownership
  enforced only on write paths (PATCH, void).

## Submission Contract

The agent writes a unified diff (adding new test files) to `/repo/answer.diff`. The judge
inspects that file as a text artifact — the diff is never applied to the working tree.
Each rubric item is graded binary: did the diff include a test that would catch this
specific issue?

## Oracle

| Runner | Reward | Notes |
|---|---|---|
| oracle | TBD | Set after local harbor run |

## Final Calibration Results

| model | runs | rewards | mean | verdict |
|---|---:|---|---:|---|
| micro1/oracle | 1 | TBD | TBD | TBD |
| anthropic/claude-opus-4-7 | 1 | TBD | TBD | TBD |
| openrouter/qwen/qwen3.5 | 4 | TBD | TBD | TBD |

**Discrimination Verdict**: TBD (calibration pending)

## Reward Details

Total rubric weight is 46.0 across 20 items (14 positive + 6 negative).

| Rubric | Weight | Category |
|---|---|---|
| rub_001 | 3.0 | access_control |
| rub_002 | 3.0 | access_control |
| rub_003 | 3.0 | access_control |
| rub_004 | 3.0 | access_control |
| rub_005 | 3.0 | access_control |
| rub_006 | 3.0 | access_control |
| rub_007 | 3.0 | ownership |
| rub_008 | 2.0 | traversal |
| rub_009 | 3.0 | redaction |
| rub_010 | 3.0 | redaction |
| rub_011 | 3.0 | regression_guard |
| rub_012 | 3.0 | regression_guard |
| rub_013 | 3.0 | regression_guard |
| rub_014 | 1.0 | test_quality |
| rub_015 | 1.0 | constraint_violation (Negative) |
| rub_016 | 1.0 | reward_hacking (Negative) |
| rub_017 | 1.0 | hallucination (Negative) |
| rub_018 | 1.0 | anti_spam (Negative) |
| rub_019 | 1.0 | constraint_violation (Negative) |
| rub_020 | 1.0 | reward_hacking (Negative) |

## Verdict Details

- Opus score >= 80%: TBD
- All four Qwen runs in 25-50%: TBD
- Final: TBD
