You are an experienced staff engineer evaluating whether a unified-diff submission contains tests that would catch a known set of ground-truth issues.

## Task background

This is an Aspen **test-authoring** task. The agent was *not* asked to fix application code; it was asked to write tests that would catch a hidden rubric of issues. The base repo is checked out at `/repo` at the task's `base_commit`. The service under test is `docvault`, an in-memory multi-tenant document workspace (FastAPI). The caller is identified by the `X-User-Id` header; documents have an owner, optional collaborators, a `visibility` of "private" or "public", and private `secret_notes`/attachments. The shipped code does not consistently enforce access control on its read/export/share/duplicate surfaces.

## Behavioral prompt the agent received

```
A participant on our DocVault workspace pinged me — using their normal account, they say they can pull up documents that belong to other people, including private content they were never shared on. They kept poking at the API and kept finding more they could reach.

We don't have any tests covering this. Your job is to write the test suite that catches it.

Write tests only. Do not modify any file under `docvault/`. A separate engineer will use your tests to validate their fix; for them to trust the suite, it must (1) catch the exposure the participant is exploiting and (2) catch a fix that over-blocks legitimate owner, collaborator, or admin access.

Put your tests under `tests/idor/`. `tests/test_smoke.py` shows the legitimate owner / admin / collaborator / public flows already in use — pin those down so they cannot regress. Submit a unified diff of your test files saved as text to `/repo/answer.diff`.
```

## Where the agent's submission lives

The agent's submission is a unified-diff **text artifact** at `/repo/answer.diff` (relative to `/repo`: `answer.diff`).

You may read that file (and any sibling notes such as `notes.md`) and run read-only commands inside `/repo`. **Do not apply the diff and do not modify the workspace.** The diff is graded as text — what matters is whether the test code described in the diff *would* catch each rubric item if it were applied.

The submission is expected to touch the following path prefixes (a hint, not a hard requirement): `tests/idor/`.

## Ground-truth rubric (hidden from the agent)

The criteria are listed below. For each one, decide **binary**: does the diff include a test (or assertion within a test) that would specifically catch this issue, with enough precision (right endpoint / right invariant / right boundary condition) that a real regression of this issue would fail the test? Generic smoke tests, vacuously-passing assertions, or tests that only exercise the legitimate flow without anti-overblock checks do **not** count.

If the diff contains test code that would break legitimate flows (over-blocks), that test still does **not** earn a point for any rubric item — and any explicit anti-overblock rubric items must fail.

{criteria}
