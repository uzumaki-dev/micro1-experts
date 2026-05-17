# aspen__quizhub_idor_001

Realm Aspen test-authoring task — LLM-judge **test authoring** against a
curated `ground_truth_issues[]` rubric.

Aspen is `rubric_only`: there is no in-sandbox verifier and no `FAIL_TO_PASS`
test set. The agent reviews a buggy codebase and authors the test suite that
catches the seeded vulnerability; the LLM judge scores the agent's git diff
against the rubric. The platform converts each `ground_truth_issues[]` entry
into one `nl_assertion` criterion, weighted by severity
(`critical=4, major=3, minor=2, nitpick=1`).

The companion [`DEEP_DIVE.md`](DEEP_DIVE.md) is the on-ramp for readers who
haven't seen this task before. This file is the team-facing status report.

## Tasks in this pack

| Task | Substrate | Rubric items | Status |
| --- | --- | --- | --- |
| `quizhub_idor` | Hand-authored FastAPI quiz/assessment service (~410 LOC) with seeded broken-access-control bug | 13 (10 major + 2 minor + 1 nitpick) | **PENDING CALIBRATION** |

`rubric_max_score` = `10 major×3 + 2 minor×2 + 1 nitpick×1` = **35**.

## Intended calibration targets

Design target for the discrimination ladder (per the Aspen authoring guide):

- **`claude-opus-4-7`** — 80%+, and a perfect score (1.0) on at least one run.
- **`openrouter/qwen/qwen3.5-397b-a17b`** — run 4×, scores in the 25–50% band.
- **`gemini-3.1-pro-preview`** — passing score (1.0) on at most 2/4 runs.

The structural discriminator is the duplicate-then-X laundering chain
(RUB-006/007/008) plus the dual-contract anti-overblock guards
(RUB-009/010): weaker models reliably enumerate the read-side leak surface
but miss the chained-flow and dual-contract items.

## Calibration results

> **PENDING — fill this section after running the triad on Realm.** Run each
> model from the Realm **Runs** tab, then paste per-model reward, status, and
> final score below. See "Placeholders to fill" at the bottom of this file.

### Per-model summary

| Model | n | Mean | Saturate (=1.00) | Pass-rate (≥0.5) | Distribution |
| --- | :---: | :---: | :---: | :---: | --- |
| `claude-opus-4-7` | _PENDING_ | _PENDING_ | _PENDING_ | _PENDING_ | _PENDING_ |
| `gemini-3.1-pro-preview` | _PENDING_ | _PENDING_ | _PENDING_ | _PENDING_ | _PENDING_ |
| `openrouter/qwen/qwen3.5-397b-a17b` | _PENDING_ | _PENDING_ | _PENDING_ | _PENDING_ | _PENDING_ |

Frontier-mean spread = _PENDING_ (target ≈ 0.20, no saturation).

### Stability — pass@k

> Fill after the n-escalation run (per-model saturation-aware ladder: escalate
> only models that hit 1.0 at round 1; always escalate the high-variance
> model for n=10 variance characterization).

`pass@k = 1 − C(n − c, k) / C(n, k)`

**Success threshold = reward ≥ 0.5:**

| k | pass@k |
| :---: | :---: |
| 1 | _PENDING_ |
| 2 | _PENDING_ |
| 3 | _PENDING_ |
| 5 | _PENDING_ |

**Success threshold = reward = 1.0:** _PENDING_

### Per-rubric catch rates

> Fill `Caught` and `Rate` per rubric over the full calibration sample.

| Rubric | Severity (weight) | Caught | Rate | Notes |
| --- | --- | :---: | :---: | --- |
| RUB-001 (`GET /quizzes/{id}` field redaction) | major (3) | _PENDING_ | _PENDING_ | read-side leak coverage |
| RUB-002 (list-endpoint redaction) | major (3) | _PENDING_ | _PENDING_ | read-side leak coverage |
| RUB-003 (per-quiz hidden_resource_files awareness) | major (3) | _PENDING_ | _PENDING_ | read-side leak coverage |
| RUB-004 (audit-mode attempt privacy via `mode`) | major (3) | _PENDING_ | _PENDING_ | read-side leak coverage |
| RUB-005 (cross-author attempt privacy) | major (3) | _PENDING_ | _PENDING_ | read-side leak coverage |
| RUB-006 (duplicate-then-PATCH laundering) | major (3) | _PENDING_ | _PENDING_ | write-side laundering chain |
| RUB-007 (duplicate-then-share laundering) | major (3) | _PENDING_ | _PENDING_ | write-side laundering chain |
| RUB-008 (duplicate-then-export laundering) | major (3) | _PENDING_ | _PENDING_ | write-side laundering chain |
| RUB-009 (instructor still sees full data) | major (3) | _PENDING_ | _PENDING_ | dual-contract anti-overblock |
| RUB-010 (students can still call write endpoints) | major (3) | _PENDING_ | _PENDING_ | dual-contract anti-overblock |
| RUB-011 (public handout still downloadable) | minor (2) | _PENDING_ | _PENDING_ | anti-overblock |
| RUB-012 (path traversal containment) | minor (2) | _PENDING_ | _PENDING_ | traversal |
| RUB-013 (sentinel marker bytes + zip-content rigor) | nitpick (1) | _PENDING_ | _PENDING_ | test_quality |

### Discrimination ladder

> Fill after catch rates are known. Target shape (per the authoring guide):

- **Frontier-saturated (≥58%)** — ~30% of items, coverage baseline: _PENDING_
- **Mid-tier (42–58%)** — ~30% of items: _PENDING_
- **Hard rungs (25–42%)** — ~25% of items, chained-flow + dual-contract: _PENDING_
- **Top-of-frontier (≤10%)** — ≥1 item, the discrimination signal: _PENDING_

### Discrimination verdict

> **PENDING** — `DISCRIMINATIVE` / `UNDER-CALIBRATED` / `FLAKY`, with rationale,
> after calibration runs complete.

## Ground-truth rubric — `quizhub_idor`

| ID | Severity | Category | Criterion |
| --- | --- | --- | --- |
| RUB-001 | major | access_control | Test asserts non-instructor `GET /quizzes/{id}` redacts private `answer_bundle` fields |
| RUB-002 | major | access_control | Test asserts non-instructor `GET /quiz-bank` redacts private fields from every row |
| RUB-003 | major | access_control | Test asserts non-instructor can't fetch files in `answer_bundle.hidden_resource_files` (per-quiz awareness) |
| RUB-004 | major | ownership | Test asserts non-instructor can't fetch audit-mode attempt artifacts (`attempt.mode` = `*_audit`) |
| RUB-005 | major | ownership | Test asserts non-instructor can't fetch cross-author attempt artifacts |
| RUB-006 | major | redaction | Duplicate-then-PATCH laundering chain |
| RUB-007 | major | redaction | Duplicate-then-share laundering chain |
| RUB-008 | major | redaction | Duplicate-then-export laundering chain |
| RUB-009 | major | regression_guard | **Anti-overblock**: instructor `GET /quiz-bank` STILL returns full data |
| RUB-010 | major | regression_guard | **Anti-overblock**: students can still call own-resource write endpoints |
| RUB-011 | minor | regression_guard | Anti-overblock: public handout file remains downloadable to non-instructor |
| RUB-012 | minor | traversal | Path traversal containment (`..` segments, `.key/` prefix) |
| RUB-013 | nitpick | test_quality | Sentinel marker bytes + zip-content inspection rigor |

## Image

`micro1ai/aspen-quizhub:idor-v1` (digest `sha256:REPLACE_WITH_IMAGE_DIGEST`).

Build context: `image_build/`. Per the E2B template-builder convention, the
Dockerfile creates uid 1000 literally named `user`, snapshots the buggy
`quizhub/` starter via a fresh `git init` (single commit, no remote), and pins
FastAPI + pytest. `tests/test_smoke.py` shows the legitimate student +
instructor flows naturalistically — it tells the agent which routes are
student-callable without prescribing any specific fix shape.

Build + push:

```bash
cd image_build
docker buildx build --platform linux/amd64 --provenance=false --sbom=false \
  -t micro1ai/aspen-quizhub:idor-v1 --push .
docker buildx imagetools inspect micro1ai/aspen-quizhub:idor-v1 \
  --format '{{.Manifest.Digest}}'
```

Set the image **PRIVATE** on Docker Hub after the first push.

## Aspen pipeline gotchas

- **No deterministic gold validation.** Aspen is `rubric_only: true`; there is
  no `gold_patch.diff` and no `FAIL_TO_PASS` set. The ground truth is the
  rubric itself.
- **`task_config.repo.image_name` is the agent's working environment**, not
  just metadata. The agent reviews the buggy starter live; rubric matching
  happens only at scoring time.
- **Prompt-level instruction-following matters.** The prompt explicitly
  forbids modifying `quizhub/`; without that rule frontier models will
  sometimes write a fix instead of tests.
- **`tests/test_smoke.py` is load-bearing.** It encodes the route-to-role
  mapping (which endpoints students can call) naturalistically. Removing it
  floors model performance — the agent cannot induce the student flow from
  the buggy router code alone.

## Placeholders to fill before upload

| Where | Placeholder | How to fill |
| --- | --- | --- |
| `task_config.json` → `repo.base_commit` | `REPLACE_WITH_BASE_COMMIT_SHA` | Full SHA of the single commit baked into the image. After building, run a container and `git -C /repo rev-parse HEAD`. |
| `task_config.json` → `repo.image_digest` | `sha256:REPLACE_WITH_IMAGE_DIGEST` | Output of `docker buildx imagetools inspect micro1ai/aspen-quizhub:idor-v1 --format '{{.Manifest.Digest}}'` after `--push`. |
| `README.md` → `repo.image_digest` reference | `sha256:REPLACE_WITH_IMAGE_DIGEST` | Same digest as above. |
| `README.md` → Calibration results / pass@k / catch rates / ladder / verdict | `_PENDING_` | Run the triad on the Realm **Runs** tab and paste the numbers. |
