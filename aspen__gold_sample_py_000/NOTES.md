# Task Design Notes: TaskHub IDOR Exfiltration

## Overview
This is a test-authoring task for a hand-authored TaskHub API that simulates common IDOR (Insecure Direct Object Reference) and unauthorized access vulnerabilities. The task rewards agents for writing comprehensive tests that catch unauthorized access and artifact exfiltration while preserving legitimate participant and admin flows.

## Rubric Design

### Access Control Layer (RUB-001 through RUB-008)
These items focus on the core vulnerability: unauthorized read access to private task/run metadata and artifacts.

- **RUB-001, RUB-002**: Test that the API redacts `sandbox_config` fields (gold patches, task configs, test patches, hidden seed files) from non-admin responses at the single-task and list-endpoint levels.
- **RUB-003**: Tests awareness of per-task hidden seed file names (not just well-known defaults).
- **RUB-004, RUB-005**: Tests that validation runs and cross-author runs are treated as private and blocked.
- **RUB-006, RUB-007, RUB-008**: Tests the "laundering" attack: non-admin users duplicate a task (inheriting private fields), then use share/export/PATCH to leak those inherited fields.

### Regression Guards (RUB-009, RUB-010, RUB-011)
These prevent overly broad fixes that block legitimate flows:

- **RUB-009**: Admin users MUST still see `sandbox_config` fields in list responses (required for task authoring workflows).
- **RUB-010**: Non-admin participants MUST be able to duplicate/share/export their own tasks.
- **RUB-011**: Public seed files (e.g., `public_readme.md`) MUST remain accessible to all users.

### Constraint Violations (RUB-012, RUB-013 — Negative Items)
These catch common implementation mistakes or reward hacks:

- **RUB-012**: Path traversal protection must be in place (guards against `../` escapes in `/tasks/{id}/files/{path}`).
- **RUB-013**: Agents sometimes add test-helper functions that inject sentinel bytes into mock responses; these must not leak into actual API responses. This negative rubric catches such over-fitting.

## Calibration Notes

The initial calibration run showed Opus at 85.4% (above the 80% target) and Qwen at 70.2% mean across four runs (above the 25–50% target band). This suggests the task may be easier than intended for mid-range models. Consider:

1. **Tightening negative rubric items**: RUB-012 and RUB-013 could be made more precise (e.g., testing double-encoded traversal, testing more sentinel placements).
2. **Adding boundary-case sensitivity**: Current criteria are relatively coarse-grained; finer subdivision (e.g., distinguishing 403 vs 404, testing with various hidden-file name patterns) could improve discrimination.
3. **Introducing latent-knowledge barriers**: Agents may know IDOR patterns by name; consider adding obfuscation (symptom-only prompts, unusual endpoint naming) to raise the difficulty floor.

## Substrate Details

The hand-authored TaskHub API mock includes:

- **Endpoints**: `GET /tasks/{id}`, `GET /coding-tasks`, `GET /tasks/{id}/files/{name}`, `GET /runs/{id}/artifacts`, `GET /tasks/{id}/export`, `POST /tasks/{id}/duplicate`, `POST /tasks/{id}/share`
- **Authentication**: `Authorization: Bearer <token>` with `user_id` and `role` (participant or admin) embedded or looked up
- **Roles**: `participant` (can only see own tasks/runs) and `admin` (full visibility)
- **Private fields**: `sandbox_config` (containing gold_patch_b64, task_config_b64, test_patch_b64, hidden_seed_files)

## Testing Considerations

Tests should use standard Python testing frameworks (e.g., `unittest`, `pytest`) with HTTP clients (`requests`, `httpx`) to interact with the mock API. The agent is expected to:

1. Read the API code to deduce the attack surface (no explicit endpoint list provided in the prompt).
2. Write tests that fail when private data leaks and pass when it's properly redacted.
3. Ensure anti-overblock assertions so legitimate flows aren't broken by fixes.

This mirrors real-world scenarios where security test suites must be comprehensive yet not overly restrictive.
