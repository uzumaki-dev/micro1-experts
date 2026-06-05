# aspen__paymentsvc_idor_001

## Task Summary

IDOR vulnerability in a FastAPI payment management service. Private `private_notes` and
line-item `fee_code` fields, plus document bytes, leak to any authenticated caller across
8 distinct surfaces: direct GET, list, search, JSON export, CSV export, document download,
path traversal into the global document store, and a clone endpoint that launders all
private fields to the attacker without scrubbing.

Rubric: 20 items, total weight 45.
- rub_001–007: direct-coverage sentinel checks on single-record endpoints (weight 3 each = 21 pts)
- rub_008: path-traversal sentinel check (weight 2)
- rub_009–010: clone laundering flows — clone→PATCH and clone→export (weight 3 each = 6 pts)
- rub_011–013: Regression_guard anti-overblock items (weight 3 each = 9 pts)
- rub_014: sentinel sweep quality item (weight 1)
- rub_015–020: negative criteria — constraint_violation, reward_hacking, hallucination, anti_spam (weight 1 each = 6 pts)

All direct-coverage items require sentinel-based content inspection; status-code-only
assertions do not satisfy rub_001–010.

## Substrate

* **Source**: Hand-authored FastAPI service (~300 LOC)
* **Commit**: f53365bcedcd2974001840e052bd78a13e99342b
* **Description**: Small in-memory multi-tenant payment API with roles: Admin, Owner,
  Stranger. Payments have `private_notes`, line items with `fee_code`, and a `documents`
  dict. Caller identified by `X-User-Id` header. Ownership enforced only on write paths
  (PATCH, void); all read paths are unguarded.

## Submission Contract

The agent writes a unified diff (adding new test files) to `/repo/answer.diff`. The judge
inspects that file as a text artifact — the diff is never applied to the working tree.
Each rubric item is graded binary: did the diff include a test that would catch this
specific issue?

## Calibration Results

Calibrated 2026-06-05. Failed runs excluded (sandbox timeouts, not task faults).
Opus column from run 5fd70a8c (86.7%); Qwen catch rates derived from 5 succeeded runs.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Mean |
|-------|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | locally validated | — | — | — | — | ~100% |
| Claude Opus 4.7 | 86.7% (5fd70a8c) | — | — | — | — | 86.7% |
| Qwen 3.5 397B | 46.7% (9e4e7e42) | 51.1% (bb8e471b) | 46.7% (26c9b96f) | 46.7% (2a93be53) | 46.7% (ff714595) | 47.6% |

Raw scores: Opus 39/45 pts (5fd70a8c), Qwen 21/45 pts (typical run), 23/45 pts (bb8e471b).

### Per-Rubric Catch Rates

Opus: 1 calibration run (5fd70a8c). Qwen: 5 succeeded runs; catch rate = fraction that passed each item.

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (GET /{id} private_notes sentinel) | 100% | 0% |
| rub_002 (list private_notes/fee_code sentinel) | 100% | 100% |
| rub_003 (search private_notes sentinel) | 100% | 100% |
| rub_004 (line-items fee_code sentinel) | 100% | 0% |
| rub_005 (export json private_notes sentinel) | 100% | 0% |
| rub_006 (export csv private_notes/fee_code sentinel) | 100% | 0% |
| rub_007 (document download sentinel) | 100% | 0% |
| rub_008 (path traversal sentinel) | 100% | 20% |
| rub_009 (clone→PATCH laundering) | 0% | 0% |
| rub_010 (clone→export laundering) | 0% | 0% |
| rub_011 (owner GET still returns private_notes — guard) | 100% | 100% |
| rub_012 (admin GET still returns private_notes — guard) | 100% | 100% |
| rub_013 (non-admin can create/list own — guard) | 100% | 100% |
| rub_014 (sentinel sweep quality) | 100% | 0% |
| rub_015 (no paymentsvc/ modifications) | 100% | 100% |
| rub_016 (no vacuous assertions) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no duplicate assertion spam) | 100% | 100% |
| rub_019 (no internal module bypass) | 100% | 100% |
| rub_020 (no swallowed assertion errors) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: ~100% (locally validated) ✓
- Opus 4.7: 86.7% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 47.6% mean across 5 succeeded runs ✓ (target 25–50%)

The gap is driven by rub_001, rub_004–007 (sentinel-absence checks on single-record
endpoints) and rub_014 (full sentinel sweep). Qwen consistently writes status-code-only
(status 403) assertions on these single-record endpoints, while Opus correctly uses
unconditional sentinel-absence checks that are robust to both a 403 and a redacted-200
fix. The Qwen bb8e471b run reached 51.1% by also passing rub_008 (path traversal);
the other 4 Qwen runs hold at exactly 46.7% with consistent item-level patterns.

Both models fail rub_009 and rub_010 (clone laundering flows, weight 3 each). These are
top-of-frontier items requiring multi-step reasoning to identify the clone-as-data-exfil
attack path; they are the expected ceiling of this rubric. Opus's 4 missed laundering
points (2 × 3 = 6 pts) account for its gap from 100% without affecting the ≥80% gate.

## Reward Details

Total rubric weight is 45.0 across 20 items (14 positive + 6 negative).

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

- Opus score >= 80%: yes (86.7%)
- All Qwen runs in 25-50%: yes for 4/5 runs (46.7% each); bb8e471b at 51.1% marginally above ceiling; mean 47.6% well within target
- Final: PASS
