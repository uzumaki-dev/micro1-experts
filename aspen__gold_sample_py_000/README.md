# aspen__gold_sample_py_000

## Status
Test-authoring task over a **hand-authored TaskHub API substrate**. Rewards Python tests that catch unauthorized access and artifact exfiltration (IDOR) vulnerabilities while preserving legitimate participant and admin flows. The prompt is symptom-only — it describes participant-reported file leakage but never names the specific endpoints or attack vectors — so the agent must read the mock API and deduce the attack surface itself.

## Substrate
* **Source**: Hand-authored TaskHub API mock (synthetic Python FastAPI/Django-style API)
* **Commit**: `main` (initialized with sample request/response patterns)
* **Description**: Mock TaskHub API with participant and admin roles. Endpoints include GET/PATCH `/tasks/{id}`, GET `/coding-tasks`, GET `/tasks/{id}/files/{name}`, GET `/runs/{id}/artifacts`, POST `/tasks/{id}/duplicate`, POST `/tasks/{id}/share`, GET `/tasks/{id}/export`. Tests target access control across these endpoints using standard Python `unittest` + `requests` or `httpx`.

## Submission Contract
The agent writes a unified diff (new Python test files under `tests/exfiltration/`) to `/repo/answer.diff`. The judge inspects that file as a text artifact — the diff is never applied. Each rubric item is graded binary: would the diff include a test that catches this specific issue?

## Final Calibration Results

| model | runs | rewards | mean | verdict |
|---|---:|---|---:|---|
| micro1/oracle | TBD | TBD | TBD | TBD |
| anthropic/claude-opus-4-7 | TBD | TBD | TBD | TBD |
| openrouter/qwen/qwen3.5 | TBD | TBD | TBD | TBD |

**Discrimination Verdict**: TBD. To be populated after calibration runs.

## Reward Details
Total rubric weight is **31.0** across **13 items** (2 negative = 15% of items / 10% of weight; 3 regression_guard; 6 access_control). Note: predates the 30% negative mandate — new tasks must meet it.

| Rubric | Weight | Category | What it checks |
|---|---|---|---|
| rub_001 | 3.0 | access_control | GET `/tasks/{id}` redacts `sandbox_config` fields |
| rub_002 | 3.0 | access_control | GET `/coding-tasks` (list) redacts `sandbox_config` per row |
| rub_003 | 3.0 | access_control | GET `/tasks/{id}/files/{name}` rejects hidden seed files |
| rub_004 | 3.0 | access_control | GET `/runs/{id}/artifacts` blocks validation-mode runs |
| rub_005 | 3.0 | ownership | GET `/runs/{id}/artifacts` checks `created_by` ownership |
| rub_006 | 3.0 | redaction | duplicate-then-PATCH does not leak inherited fields |
| rub_007 | 3.0 | redaction | duplicate-then-share does not leak inherited fields |
| rub_008 | 3.0 | redaction | duplicate-then-export does not leak inherited fields |
| rub_009 | 2.0 | regression_guard | admin GET `/coding-tasks` STILL sees `sandbox_config` |
| rub_010 | 2.0 | regression_guard | non-admin participant CAN call their own duplicate/share/export |
| rub_011 | 2.0 | regression_guard | non-admin GET public seed files (e.g., `public_readme.md`) |
| rub_012 | 2.0 | constraint_violation (Neg) | no path traversal in `/tasks/{id}/files/{path}` |
| rub_013 | 1.0 | reward_hacking (Neg) | sentinel marker bytes don't appear in private artifacts |

## Verdict Details
- Oracle score = 100%: TBD
- Opus score >= 80%: TBD
- All four Qwen runs in 25–50%: TBD
- Final: TBD
