# Context for an AI assistant

You are assisting a human task author. They drive — defer to them on the
planted issues, the test surface, what counts as "caught", and any
judgment call. Do not ever act on ambiguity; ask.

## What this directory is
A single task in the `testgen` realm. The author is shipping one
test-authoring challenge: a repo is checked out at `base_commit`, the agent
must write tests that catch a set of planted ground-truth issues. This is
a **rubric-only** pipeline — the LLM judge scores how many of the
`[[criterion]]` entries in `tests/review/agent_judge.toml` the agent's
authored tests actually catch.

At eval time, the agent gets `instruction.md` and the repo at
`base_commit`. The oracle convention is to write the reference tests to
`/repo/answer.diff`; the verifier reads the agent's authored tests and the
judge scores per-criterion using `tests/review/prompt.md` against
`tests/review/agent_judge.toml`. The oracle (`solution/solve.sh`) must
score 1.0.

## Files
- `task.toml` — schema + metadata. `metadata.rubric_only = true`,
  `metadata.task_type = "test_authoring"`, `metadata.base_commit` is the
  commit the authored tests run against.
- `instruction.md` — the agent-facing prompt. Describe the surface and what
  behaviour the tests must exercise. Do **not** reveal the ground-truth
  issues — those live only as `[[criterion]]` entries in `agent_judge.toml`.
- `environment/Dockerfile` — the agent's container; must check out the
  repo at `base_commit` and must not COPY `agent_judge.toml` or
  `solve.sh` into the image.
- `solution/solve.sh` — the oracle. Writes the reference tests as a unified
  diff to `/repo/answer.diff`; must score 1.0 against the judge.
- `tests/test.sh` — the verifier entrypoint: collect the agent's tests,
  run the judge.
- `tests/review/agent_judge.toml` — the **canonical source of truth** for
  ground-truth issues. One `[[criterion]]` per issue:
  `name` = issue id, `description` = the finding the judge should look for,
  `weight` = scoring weight. Lint requires at least one criterion.
- `tests/review/prompt.md` — the judge rubric prompt.

## What the eval agent sees
Only `instruction.md` and the contents of the built image. The agent never
sees `tests/`, `solution/`, or this file. Never name the criteria, their
count, or any path under `tests/review/` from `instruction.md`.

## Useful commands
- `rv check` — runs realm lint. (quick)
- `rv oracle` — builds the env, runs the oracle's `answer.diff` through the
  judge, asserts reward == 1.0.
- `rv run` — runs the realm's default agent against the task. (>2min)
- `rv analyze` — runs criteria against a harbor trial job folder.
- `rv submit` — runs the full pipeline and zips for submission.
