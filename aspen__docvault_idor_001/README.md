# aspen__docvault_idor_001

## Task Summary
Access-control (IDOR) test-authoring task on a hand-authored FastAPI document
workspace (`docvault`). The service leaks other users' private documents across many
surfaces (direct read, list, search, json/zip export, attachment download + path
traversal, version history, and duplicate→read/share/export laundering). The agent
writes a pytest suite that catches the exposure on each surface without over-blocking
legitimate owner/admin/collaborator/public access. Graded by an LLM judge against a
17-item rubric (weights sum 45).

## Calibration Results

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Claude Opus 4.7 | - | - | - | - | - |
| Qwen3.5 397B | - | - | - | - | - |

### Per-Rubric Catch Rates
| Criterion | Opus 4.7 | Qwen3.5 |
|-----------|----------|---------|
| rub_001 (read) | - | - |
| rub_002 (list) | - | - |
| rub_003 (search) | - | - |
| rub_004 (export json) | - | - |
| rub_005 (export zip) | - | - |
| rub_006 (attachment) | - | - |
| rub_007 (versions) | - | - |
| rub_008 (traversal) | - | - |
| rub_009 (dup-read) | - | - |
| rub_010 (dup-share) | - | - |
| rub_011 (dup-export) | - | - |
| rub_012 (owner) | - | - |
| rub_013 (admin) | - | - |
| rub_014 (collaborator) | - | - |
| rub_015 (public) | - | - |
| rub_016 (own-CRUD) | - | - |
| rub_017 (sentinel) | - | - |

## Discrimination Verdict
**PENDING CALIBRATION**

Designed to fix the predecessor's saturation (wallet feature-coverage: Opus 100%,
Qwen 93%). Target: Opus ≥80%, Qwen 25-50%. The discriminative weight sits in the
non-obvious surfaces (search, zip bytes, versions, the three laundering flows,
traversal, sentinel). If Qwen still lands >50%, harden/extend those; if Opus <80%,
check the prompt and rubric distribution.
