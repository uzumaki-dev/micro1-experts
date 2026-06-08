# aspen__surveysvc_idor_001

## Status

Survey service leaks private analyst notes and response scoring data to any
authenticated user because read, list, search, export, responses, and attachment
endpoints perform no ownership checks. The task rewards tests that verify:
(1) a stranger cannot read another owner's `internal_notes`, response `score_code`,
or attachment bytes; (2) a clone-then-mutate laundering flow does not inherit
private fields into the attacker's copy; and (3) legitimate owner and admin
flows are not over-blocked.

## Substrate

* **Source**: Hand-authored FastAPI service (~200 LOC)
* **Commit**: `0e56134d2a2e0e37f5b2ea9c3388d2aa1abd4329`
* **Description**: In-memory multi-tenant survey API. Identity via
  `X-User-Id` header. Admin identity: `admin`. Surveys carry `internal_notes`,
  per-response `score_code`, and `attachments` (filename→content map).
  Endpoints: POST/GET/PATCH/search/export/responses/attachments/clone/publish/share.
  All read endpoints ship without ownership checks. Clone copies private fields
  verbatim. Path traversal in the attachments endpoint allows cross-survey
  file reads.

## Submission Contract

The agent writes a unified diff (adding files under `tests/exfiltration/`) to
`/repo/answer.diff`. The judge inspects that file as a text artifact — the diff
is never applied to the working tree. Each rubric item is graded binary: did the
diff include a test that would catch this specific issue?

## Calibration Results

Calibrated 2026-06-08. One failed run (a8008f69) and one 0% run (46989788) excluded —
a8008f69 was a container/agent failure; 46989788 likely hit judge error before writing
scores (same pattern as schedulesvc). Opus column from run ebdc0833 (82.4%); Qwen catch
rates derived from 4 valid runs.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% (ba897ab1) | — | — | — | 100% |
| Claude Opus 4.7 | 82.4% (ebdc0833) | — | — | — | 82.4% |
| Qwen 3.5 397B | 43.1% (b104141d) | 43.1% (06b75fcd) | 49.0% (d9f858b6) | 52.9% (d1b6cec9) | 47.0% |

Raw scores: Opus 42/51 pts (ebdc0833), Qwen ~24/51 pts mean.

### Per-Rubric Catch Rates

Opus: 1 calibration run (ebdc0833). Qwen: 4 runs; catch rate = fraction of runs scoring 1 per item.

| Criterion | Opus 4.7 | Qwen 3.5 (4 runs) |
|-----------|----------|-------------------|
| rub_001 (GET /{id} internal_notes sentinel) | 100% | 0% |
| rub_002 (list internal_notes/score_code sentinel) | 100% | 100% |
| rub_003 (search sentinel — internal_notes leak) | 100% | 100% |
| rub_004 (responses score_code sentinel) | 100% | 0% |
| rub_005 (export JSON internal_notes sentinel) | 100% | 0% |
| rub_006 (export CSV sentinel) | 100% | 50% |
| rub_007 (attachment download sentinel) | 100% | 0% |
| rub_008 (path traversal attachment sentinel) | 100% | 25% |
| rub_009 (clone→PATCH internal_notes absent) | 0% | 0% |
| rub_010 (clone→publish internal_notes absent) | 0% | 0% |
| rub_011 (clone→export sentinel absent) | 0% | 0% |
| rub_012 (owner still reads internal_notes — guard) | 100% | 100% |
| rub_013 (admin still reads internal_notes — guard) | 100% | 100% |
| rub_014 (non-admin create + list own — guard) | 100% | 100% |
| rub_015 (no surveysvc/ modifications) | 100% | 100% |
| rub_016 (files only under tests/exfiltration/) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no hallucinated model fields) | 100% | 100% |
| rub_019 (no status-code-only cross-owner assertions) | 100% | 25% |
| rub_020 (no off-topic spam) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 82.4% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 47.0% mean across 4 runs ✓ (target 25–50%, range 43.1–52.9%)

The gap is driven by rub_001/rub_004–005/rub_007 (sentinel-absence checks on direct
read/responses/JSON-export/attachment surfaces — Qwen writes status-code-only assertions
on these and scores 0% across all runs) and rub_019 (reward_hacking, weight 3.0 — Qwen
passes in only 1 of 4 runs, 25%, the single largest discrimination lever). rub_006 (CSV
export) and rub_008 (path traversal) show partial Qwen success (50% and 25%),
contributing secondary separation. Opus consistently misses rub_009–011 (clone laundering
flows, 9 pts combined) — the only items preventing a perfect Opus score. Qwen mean sits
at 47% (high end of the 25–50% band), driven by one run that fully body-inspected exports
and wrote a correct traversal test (d1b6cec9, 52.9%).

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
