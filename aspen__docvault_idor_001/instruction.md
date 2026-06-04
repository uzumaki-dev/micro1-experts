# Aspen test-authoring task

A participant on our DocVault workspace pinged me — using their normal account, they say they can pull up documents that belong to other people, including private content they were never shared on. They kept poking at the API and kept finding more they could reach.

We don't have any tests covering this. Your job is to write the test suite that catches it.

**Write tests only. Do not modify any file under `docvault/`.** A separate engineer will use your tests to validate their fix; for them to trust the suite, it must (1) catch the exposure the participant is exploiting and (2) catch a fix that over-blocks legitimate owner, collaborator, or admin access.

Put your tests under `tests/idor/`. `tests/test_smoke.py` shows the legitimate owner / admin / collaborator / public flows already in use — pin those down so they cannot regress.

## Working environment

- The repository is checked out at `/repo` at the task's `base_commit`.
- This is a **test-authoring** task. You are *not* asked to fix application code; you are asked to write a test suite that catches the documented behavior under a hidden rubric.
- The caller is identified by the `X-User-Id` request header. A shared `tests/conftest.py` provides a `client` fixture and per-test state reset.
- Your tests are expected to land under: `tests/idor/`.

## What to submit

Write a unified diff of the test file(s) you would add to the repo, and save that diff (as text) to `/repo/answer.diff`. The verifier reads only `/repo/answer.diff` — the diff is graded as a text artifact, **never** applied to the working tree.

The diff should follow standard `diff --git` format, e.g.:

```
diff --git a/tests/idor/test_access.py b/tests/idor/test_access.py
new file mode 100644
--- /dev/null
+++ b/tests/idor/test_access.py
@@ -0,0 +1,N @@
+# test body...
```

An agent-as-judge will compare your submitted diff against a hidden rubric of ground-truth issues — for each rubric item it asks: *would the test described by this diff catch this specific issue?*
