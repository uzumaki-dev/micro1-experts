# Aspen test-authoring task

A bug report came in from a QA engineer: they were able to get orders into states
that should only be set by the platform's operations team. Specifically, order records
are showing discounts and fulfillment statuses that customers claim they never requested
and that bypass the normal approval workflow.

We have no tests covering this. Your job is to write the test suite that catches it.

**Write tests only. Do not modify any file under `ordersvc/`.** A separate engineer will
use your tests to validate their fix; for them to trust your tests, the suite must
(1) catch the issue being exploited and (2) not break legitimate customer or admin flows.

Put your tests under `tests/access/`. `tests/test_smoke.py` shows the legitimate
customer and admin flows already in use — your suite should pin those down with
anti-overblock assertions so they cannot regress.

Submit only your test files as a unified diff via `submit_answer`
(applies clean from `/repo`).


## Working environment

- The repository is checked out at `/repo` at the task's `base_commit`.
- This is a **test-authoring** task. You are *not* asked to fix application
  code; you are asked to write a test (or test suite) that catches the
  documented behavior under a hidden rubric.
- Your tests are expected to land under: `tests/access/`.


## What to submit

Write a unified diff of the test file(s) you would add to the repo, and save
that diff (as text) to `/repo/answer.diff`. The verifier reads only
`/repo/answer.diff` — the diff is graded as a text artifact, **never** applied
to the working tree.

The diff should follow standard `diff --git` format, e.g.:

```
diff --git a/tests/access/test_order_access.py b/tests/access/test_order_access.py
new file mode 100644
--- /dev/null
+++ b/tests/access/test_order_access.py
@@ -0,0 +1,N @@
+# test body...
```

An agent-as-judge will compare your submitted diff against a hidden rubric of
expected test behaviors. Do not try to reverse-engineer the rubric — write tests
that genuinely catch the security issue.
