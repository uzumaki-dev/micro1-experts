# Aspen test-authoring task

A workspace administrator filed a security incident — a regular workspace member had
archived the company workspace without authorization, sent an invitation to an external
contact without the admin's knowledge, and suspended a colleague's account. A second
member had also changed another user's workspace role without having admin privileges.
The platform owner confirmed all of these actions are restricted to workspace
administrators and owners only.

We have no tests covering this. Your job is to write the test suite that catches it.

**Write tests only. Do not modify any file under `workspacesvc/`.** A separate
engineer will use your tests to validate their fix; for them to trust your tests,
the suite must (1) catch the privilege escalation members are exploiting and (2) catch
a fix that over-blocks legitimate admin and owner flows.

Put your tests under `tests/exfiltration/`. `tests/test_smoke.py` shows the
legitimate owner and admin flows already in use — your suite should pin those down
with anti-overblock assertions so they cannot regress.

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
diff --git a/tests/exfiltration/test_workspace_bfla.py b/tests/exfiltration/test_workspace_bfla.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_workspace_bfla.py
@@ -0,0 +1,N @@
+# test body...
```

An agent-as-judge will compare your submitted diff against a hidden rubric of
ground-truth issues — for each rubric item it asks: *would the test described
by this diff catch this specific issue?*

**Important:** Tests that assert an attack is blocked should FAIL on the current
buggy code (because the attack currently succeeds). Tests that assert legitimate
admin access still works should PASS on both the buggy and the fixed code.
