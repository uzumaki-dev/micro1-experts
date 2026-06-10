# aspen__workspacesvc_bfla_001

## Task Summary

BFLA test-authoring task. A workspace management service (`workspacesvc`) fails to
enforce admin role checks — any workspace member can invoke admin/owner-only operations
(delete, archive, invite, suspend, patch settings, change member roles) and read the
full audit log including private `private_reason` entries.

**Vulnerability:** Broken Function Level Authorization (BFLA)

Rubric: 20 items, total weight 47.
- rub_001–007: access_control sentinel/state-verification checks (weight 3 each = 21 pts)
- rub_008: self-promote laundering flow (weight 2 = 2 pts)
- rub_009–013: regression_guard anti-overblock items (weight 3 each = 15 pts)
- rub_014: test_quality sentinel sweep + state-verification (weight 1)
- rub_015: constraint_violation — no workspacesvc/ modifications (weight 3)
- rub_016–020: negative criteria — constraint_violation, hallucination×2, reward_hacking, anti_spam (weight 1 each = 5 pts)

All access_control items require state-mutation verification (follow-up GET) in addition
to the status-code check; status-code-only assertions do not satisfy rub_001–007.

## Calibration Results

Calibrated 2026-06-11. Opus column from run 67503acf (80.9%); Qwen catch rates derived
from 4 canonical runs. Two additional Qwen runs (5905a714, 083527dc) scored 0% and are
excluded from the table per the 4-run cap.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 80.9% (67503acf) | — | — | — | 80.9% |
| Qwen 3.5 397B | 48.9% (e9a4bf60) | 42.6% (a82e70c6) | 36.2% (8941d76a) | 36.2% (7139af27) | 41.0% |

Raw scores: Opus 38/47 pts (67503acf), Qwen 23/47 pts (e9a4bf60).

### Per-Rubric Catch Rates

Opus: 1 calibration run (67503acf). Qwen: 4 runs; rub_001–008, rub_012, rub_014 fail
consistently (state-verification or sentinel checks missing). rub_011 shows judge variance
(2/4 pass depending on how the judge reads suspend-response assertions).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (member DELETE rejected + workspace still exists) | 100% | 25% |
| rub_002 (member archive rejected + is_archived still false) | 100% | 0% |
| rub_003 (member invite rejected + user absent from members) | 100% | 0% |
| rub_004 (member suspend rejected + target not in suspended) | 100% | 0% |
| rub_005 (member role-change rejected + role unchanged) | 100% | 0% |
| rub_006 (member settings patch rejected + billing_email unchanged) | 100% | 0% |
| rub_007 (member audit-log hides private_reason sentinel) | 0% | 0% |
| rub_008 (self-promote laundering: role stays member + delete still rejected) | 0% | 0% |
| rub_009 (owner CAN delete workspace) | 100% | 100% |
| rub_010 (admin CAN archive + is_archived becomes true) | 100% | 100% |
| rub_011 (admin CAN suspend + target suspended) | 100% | 50% |
| rub_012 (admin CAN read audit-log + sentinel IS present) | 0% | 0% |
| rub_013 (admin CAN patch settings + billing_email updated) | 100% | 100% |
| rub_014 (sentinel seeded + member redaction verified + state non-mutation) | 0% | 0% |
| rub_015 (no workspacesvc/ modifications) | 100% | 100% |
| rub_016 (test files only in tests/exfiltration/) | 100% | 100% |
| rub_017 (no hallucinated endpoints) | 100% | 100% |
| rub_018 (no hallucinated model fields) | 100% | 100% |
| rub_019 (no vacuous assertions) | 100% | 100% |
| rub_020 (no duplicate assertion spam) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 80.9% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 41.0% mean across 4 runs ✓ (target 25–50%)

The gap is driven by rub_001–006 (state-verification checks — Qwen writes status-code-only
assertions and misses the follow-up GET confirming state was not mutated) and rub_007–008,
rub_012, rub_014 (sentinel-inspection surfaces — Qwen never seeds `private_reason` or
checks body content). Opus misses rub_007 (member audit-log sentinel absence check),
rub_008 (full self-promote laundering chain), and rub_012 (admin sentinel-present guard)
— these are the top-of-frontier items that cost Opus its lost 9 points.
