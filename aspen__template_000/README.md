# aspen__<substrate>_<descriptor>_<NNN>

## Status
Brief technical overview of the scenario and the target vulnerability/feature being tested. Mention what the task rewards (e.g., "This package is designed to reward tests that verify stock consistency across cancellation...").

## Substrate
* **Source**: [Link to repo if public, or "Hand-authored"]
* **Commit**: `<base_commit_sha>`
* **Description**: Brief overview of the application (e.g., "Small FastAPI app with roles: Admin, Developer, Viewer").

## Submission Contract
The agent writes a unified diff (typically adding new test files) to `/repo/answer.diff`. The judge inspects that file as a text artifact — the diff is never applied to the working tree. Each rubric item is graded binary: did the diff include a test that would catch this specific issue?

## Final Calibration Results

| model | runs | rewards | mean | verdict |
|---|---:|---|---:|---|
| micro1/oracle | TBD | TBD | TBD | TBD |
| anthropic/claude-opus-4-7 | TBD | TBD | TBD | TBD |
| openrouter/qwen/qwen3.5 | TBD | TBD | TBD | TBD |

**Discrimination Verdict**: TBD. To be populated after calibration runs.

## Reward Details
Total rubric weight is **<X>** across **<Y> items** (<Z> negative = <N>% of items / <M>% of weight; <R> regression_guard).

| Rubric | Weight | Category | What it checks |
|---|---|---|---|
| rub_001 | 3.0 | <category> | <description> |
| rub_002 | 3.0 | <category> | <description> |
| rub_003 | 2.0 | <category> | <description> |
| rub_004 | 2.0 | regression_guard | <description> |
| rub_005 | 1.0 | test_quality | <description> |

## Verdict Details
- Oracle score ≈ 100%: TBD
- Opus score ≥ 80%: TBD
- All four Qwen runs in 25–50%: TBD
- Final: TBD
