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

| Criterion | Opus 4.7 | Qwen3.5 |
|-----------|----------|---------|
| rub_001 (read — sentinel req.) | ✓ | ✗ |
| rub_002 (list) | ✓ | ✓ |
| rub_003 (search — sentinel req.) | ✓ | ✗ |
| rub_004 (export json — sentinel req.) | ✓ | ✗ |
| rub_005 (export zip — content inspection) | ✓ | ✗ |
| rub_006 (attachment — sentinel req.) | ✓ | ✗ |
| rub_007 (versions — sentinel req.) | ✓ | ✗ |
| rub_008 (traversal — sentinel req.) | ✓ | ✗ |
| rub_009 (dup-read laundering) | ✗ | ✗ |
| rub_010 (dup-share laundering) | ✗ | ✗ |
| rub_011 (dup-export laundering) | ✓ | ✗ |
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
and the two laundering flows (rub_009/010). Qwen writes status-code-only assertions and
misses non-obvious surfaces; Opus naturally uses content-inspection and covers more routes
but misses the dup-read and dup-share laundering surfaces.
