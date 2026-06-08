# aspen__leasesvc_idor_001

## Status

Lease management service leaks private landlord notes and per-clause assessment codes
to any authenticated user because read, list, search, export, clauses, and document
endpoints perform no ownership checks. The task rewards tests that verify:
(1) a stranger cannot read another owner's `private_notes`, clause `clause_code`,
or document bytes; (2) a clone-then-mutate laundering flow does not inherit
private fields into the attacker's copy; and (3) legitimate owner and admin
flows are not over-blocked.

## Substrate

* **Source**: Hand-authored FastAPI service (~200 LOC)
* **Commit**: `b21cb61673d1492da33f53ea8f5eb21a1f574828`
* **Description**: In-memory multi-tenant lease API. Identity via
  `X-User-Id` header. Admin identity: `admin`. Leases carry `private_notes`,
  per-clause `clause_code`, and `attachments` (filename→content map).
  Endpoints: POST/GET/PATCH/search/export/clauses/documents/clone/renew/share.
  All read endpoints ship without ownership checks. Clone copies private fields
  verbatim. Path traversal in the documents endpoint allows cross-lease
  file reads.

## Submission Contract

The agent writes a unified diff (adding files under `tests/exfiltration/`) to
`/repo/answer.diff`. The judge inspects that file as a text artifact — the diff
is never applied to the working tree. Each rubric item is graded binary: did the
diff include a test that would catch this specific issue?

## Calibration Results

Initial calibration runs completed 2026-06-08. Two Opus runs at 76.5% (96202286, 97bb6898)
and one 0% Opus run (351c24aa, agent failure — excluded). Qwen runs: 37.3% (09342f89),
43.1% (cf246574). rub_019 was subsequently narrowed to exempt correctly-protected endpoints
(PATCH, renew) so Opus tests against those endpoints no longer fail the criterion; rubric
updated and re-submitted for re-calibration.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 (pre-fix) | 76.5% (96202286) | 76.5% (97bb6898) | — | — | 76.5% |
| Qwen 3.5 397B | 37.3% (09342f89) | 43.1% (cf246574) | — | — | 40.2% |

*Post-fix Opus calibration pending.*

### Per-Rubric Catch Rates (pre-fix, Opus run 96202286)

| Criterion | Opus 4.7 | Qwen 3.5 (2 runs) |
|-----------|----------|-------------------|
| rub_001 (GET /{id} private_notes sentinel) | 100% | 0% |
| rub_002 (list private_notes/clause_code sentinel) | 100% | 100% |
| rub_003 (search sentinel — private_notes leak) | 100% | 100% |
| rub_004 (clauses clause_code sentinel) | 100% | 0% |
| rub_005 (export JSON private_notes sentinel) | 100% | 0% |
| rub_006 (export CSV sentinel) | 100% | 0% |
| rub_007 (documents download sentinel) | 100% | 0% |
| rub_008 (path traversal attachment sentinel) | 100% | 0% |
| rub_009 (clone→PATCH private_notes absent) | 0% | 0% |
| rub_010 (clone→renew private_notes absent) | 0% | 0% |
| rub_011 (clone→export sentinel absent) | 0% | 0% |
| rub_012 (owner still reads private_notes — guard) | 100% | 100% |
| rub_013 (admin still reads private_notes — guard) | 100% | 100% |
| rub_014 (non-admin create + list own — guard) | 100% | 100% |
| rub_015 (no leasesvc/ modifications) | 100% | 100% |
| rub_016 (files only under tests/exfiltration/) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no hallucinated model fields) | 100% | 100% |
| rub_019 (no status-code-only on leaking endpoints) | 0%* | 0% |
| rub_020 (no off-topic spam) | 100% | 100% |

\* Opus failed rub_019 because test_patch_blocks_non_owner and test_renew_blocks_non_owner
had status-code-only assertions on correctly-protected endpoints. The criterion was narrowed
post-calibration to exempt tests on PATCH/renew (which already return 403); Qwen
discrimination is preserved because Qwen writes status-code-only tests on the actual
leaking endpoints (GET /{id}, /clauses, /export, /documents).

## Reward Details

Total rubric weight: 51.0 across 20 items (6 negative = 30%).

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
| rub_009 | 3.0 | redaction | positive |
| rub_010 | 3.0 | redaction | positive |
| rub_011 | 3.0 | redaction | positive |
| rub_012 | 3.0 | regression_guard | positive |
| rub_013 | 3.0 | regression_guard | positive |
| rub_014 | 3.0 | regression_guard | positive |
| rub_015 | 3.0 | constraint_violation | **negative** |
| rub_016 | 1.0 | constraint_violation | **negative** |
| rub_017 | 1.0 | hallucination | **negative** |
| rub_018 | 1.0 | hallucination | **negative** |
| rub_019 | 3.0 | reward_hacking | **negative** |
| rub_020 | 1.0 | anti_spam | **negative** |
