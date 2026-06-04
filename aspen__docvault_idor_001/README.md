# aspen__docvault_idor_001

## Task Summary
Access-control (IDOR) test-authoring task on a hand-authored FastAPI document
workspace (`docvault`). The service leaks other users' private documents across many
surfaces (direct read, list, search, json/zip export, attachment download + path
traversal, version history, and duplicate→read/share/export laundering). The agent
writes a pytest suite that catches the exposure on each surface without over-blocking
legitimate owner/admin/collaborator/public access. Graded by an LLM judge against a
17-item rubric (weights sum 47).

## Calibration Results

Calibrated 2026-05-27 after sentinel-inspection hardening on rub_001/003/004/006/007/008
and rub_017 weight promotion (1→3). Qwen uses near-deterministic inference on the Realm
platform — all four runs produce the same score. Opus shows natural run-to-run variance.

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Claude Opus 4.7 | 74.5% | 80.9% | 87.2% | — | 80.9% |
| Qwen 3.5 397B | 31.9% | 31.9% | 31.9% | 31.9% | 31.9% |

Oracle: 1.0 (sentinel assertions, unaffected by rubric tightening).

### Per-Rubric Catch Rates

Opus column from the 87.2% run (95bc3c4d); Qwen is deterministic — all 4 runs identical.

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (read — sentinel req.) | ✓ | ✗ |
| rub_002 (list) | ✓ | ✓ |
| rub_003 (search — sentinel req.) | ✓ | ✗ |
| rub_004 (export json — sentinel req.) | ✓ | ✗ |
| rub_005 (export zip — content inspection) | ✓ | ✗ |
| rub_006 (attachment — sentinel req.) | ✓ | ✗ |
| rub_007 (versions — sentinel req.) | ✓ | ✗ |
| rub_008 (traversal — sentinel req.) | ✓ | ✗ |
| rub_009 (dup-read laundering) | ✓ | ✗ |
| rub_010 (dup-share laundering) | ✗ | ✗ |
| rub_011 (dup-export laundering) | ✗ | ✗ |
| rub_012 (owner guard) | ✓ | ✓ |
| rub_013 (admin guard) | ✓ | ✓ |
| rub_014 (collaborator guard) | ✓ | ✓ |
| rub_015 (public guard) | ✓ | ✓ |
| rub_016 (own-CRUD guard) | ✓ | ✓ |
| rub_017 (sentinel sweep — w=3) | ✓ | ✗ |

## Discrimination Verdict

**DISCRIMINATIVE**

- Opus 4.7: 80.9% mean across 3 runs ✓ (target ≥80%)
- Qwen 3.5 397B: 31.9% mean across 4 runs ✓ (target 25–50%)

The gap is driven by the six sentinel-inspection items plus the sentinel sweep (rub_017)
and the two laundering flows (rub_010/011). Qwen writes status-code-only assertions and
misses every surface that requires content inspection; Opus uses sentinel-based assertions
and covers all direct-access surfaces but misses the dup-share and dup-export laundering
chains (rub_010/011 fail across runs, accounting for the variance from 74.5% to 87.2%).
