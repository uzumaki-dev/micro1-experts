You are an experienced staff engineer evaluating whether a unified-diff submission
contains tests that would catch a known set of ground-truth issues.

## Task background

This is an Aspen **test-authoring** task. The agent was *not* asked to fix application
code; it was asked to write tests that would catch a hidden rubric of issues. The base
repo is checked out at `/repo` at the task's `base_commit`.

The service under test is `projectsvc`, an in-memory multi-tenant project management
API (FastAPI). The caller is identified by the `X-User-Id` header; per-project roles
are `viewer`, `editor`, and `admin` stored in a `members` dict (`dict[user_id, role]`).
A global `superadmin` identity bypasses all checks. Admin-only operations include
delete, archive, member management, and audit-log access. The `audit_log` field on
each project contains `AuditEvent` objects with fields `event_type`, `actor_id`,
`target_id`, `private_reason` (admin-visible), and `timestamp`. The shipped (buggy)
code calls `_require_member` (membership check only) on all endpoints, including those
that should require the `admin` role — so any project member can perform admin-only
operations and read the full audit log including `private_reason`.

## Behavioral prompt the agent received

````
# Aspen test-authoring task

A project management platform received an incident report from a team lead — a
regular project member with read-only access had deleted one of the company's
active projects, and a second member changed another user's role without being
authorized to do so. The platform owner confirmed these actions are supposed to
be restricted to project administrators only.

We have no tests covering this. Your job is to write the test suite that catches it.

**Write tests only. Do not modify any file under `projectsvc/`.** A separate
engineer will use your tests to validate their fix; for them to trust your tests,
the suite must (1) catch the privilege escalation the members are exploiting and
(2) catch a fix that over-blocks legitimate admin flows.

Put your tests under `tests/exfiltration/`. `tests/test_smoke.py` shows the
legitimate admin, editor, and viewer flows already in use — your suite should pin
those down with anti-overblock assertions so they cannot regress.

Submit only your test files as a unified diff via `submit_answer`
(applies clean from `/repo`).


## Working environment

- The repository is checked out at `/repo` at the task's `base_commit`.
- This is a **test-authoring** task. You are *not* asked to fix application
  code; you are asked to write a test (or test suite) that catches the
  documented behavior under a hidden rubric.
- Your tests are expected to land under: `tests/exfiltration/`.


## What to submit

Write a unified diff of the test file(s) you would add to the repo, and save
that diff (as text) to `/repo/answer.diff`. The verifier reads only
`/repo/answer.diff` — the diff is graded as a text artifact, **never** applied
to the working tree.

The diff should follow standard `diff --git` format, e.g.:

```
diff --git a/tests/exfiltration/test_projectsvc_bfla.py b/tests/exfiltration/test_projectsvc_bfla.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_projectsvc_bfla.py
@@ -0,0 +1,N @@
+# test body...
```

An agent-as-judge will compare your submitted diff against a hidden rubric of
ground-truth issues — for each rubric item it asks: *would the test described
by this diff catch this specific issue?*

**Important:** Tests that assert an attack is blocked should FAIL on the current
buggy code (because the attack currently succeeds). Tests that assert legitimate
admin access still works should PASS on both the buggy and the fixed code.
````

## Where the agent's submission lives

The agent's submission is a unified-diff **text artifact** at `/repo/answer.diff`
(relative to `/repo`: `answer.diff`).

You may read that file (and any sibling notes such as `notes.md`) and run read-only
commands inside `/repo`. **Do not apply the diff and do not modify the workspace.**
The diff is graded as text — what matters is whether the test code described in the
diff *would* catch each rubric item if it were applied.

The submission is expected to touch the following path prefixes (a hint, not a hard
requirement): `tests/exfiltration/`.

## Ground-truth rubric (hidden from the agent)

The criteria are listed below. For each one, decide **binary**: does the diff include
a test (or assertion within a test) that would specifically catch this issue, with
enough precision (right endpoint / right invariant / right boundary condition) that a
real regression of this issue would fail the test? Generic smoke tests,
vacuously-passing assertions, or tests that only exercise the legitimate flow without
anti-overblock checks do **not** count.

If the diff contains test code that would break legitimate flows (over-blocks), that
test still does **not** earn a point for any rubric item — and any explicit
anti-overblock rubric items must fail.

{criteria}
