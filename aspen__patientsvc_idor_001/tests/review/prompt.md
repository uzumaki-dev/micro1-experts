You are an experienced staff engineer evaluating whether a unified-diff submission
contains tests that would catch a known set of ground-truth issues.

## Task background

This is an Aspen **test-authoring** task. The agent was *not* asked to fix application
code; it was asked to write tests that would catch a hidden rubric of issues. The base
repo is checked out at `/repo` at the task's `base_commit`. The service under test is
`patientsvc`, an in-memory multi-tenant medical records API (FastAPI). The caller is
identified by the `X-User-Id` header; role is inferred from the user ID prefix
(`admin` → admin, `dr_*` → doctor, anything else → patient). Records carry a private
`diagnosis`, `clinical_notes`, `insurance_id`, per-entry `lab_results` dict,
`medications` list, and `attachments` file map. The shipped code does not enforce
ownership checks on any read, list, search, labs, medications, export, or attachments
endpoint. The `refer` endpoint copies all private fields verbatim into a new record
owned by the caller.

## Behavioral prompt the agent received

```
A patient on our platform has filed a bug report — they say they are seeing medical
records that clearly belong to other patients. They authenticated normally with their
own credentials and were just browsing their portal, but they keep pulling up records
showing diagnoses, treatment notes, and billing details that are not theirs. The issue
reproduces consistently across different record IDs.

We have no tests covering this. Your job is to write the test suite that catches it.

Write tests only. Do not modify any file under `patientsvc/`. A separate
engineer will use your tests to validate their fix; for them to trust your tests,
the suite must (1) catch the data leak the patient is experiencing and (2) catch a
fix that over-blocks legitimate patient, doctor, or admin flows.

Put your tests under `tests/exfiltration/`. `tests/test_smoke.py` shows the
legitimate patient, doctor, and admin flows already in use — your suite should pin
those down with anti-overblock assertions so they cannot regress.

Submit only your test files as a unified diff via `submit_answer`
(applies clean from `/repo`).
```

## Where the agent's submission lives

The agent's submission is a unified-diff **text artifact** at `/repo/answer.diff`
(relative to `/repo`: `answer.diff`).

You may read that file (and any sibling notes such as `notes.md`) and run read-only
commands inside `/repo`. **Do not apply the diff and do not modify the workspace.**
The diff is graded as text — what matters is whether the test code described in the
diff *would* catch each rubric item if it were applied.

The submission is expected to touch the following path prefix (a hint, not a hard
requirement): `tests/exfiltration/`.

## Ground-truth rubric (hidden from the agent)

The criteria are listed below. For each one, decide **binary**: does the diff include
a test (or assertion within a test) that would specifically catch this issue, with
enough precision (right endpoint / right invariant / right boundary condition) that a
real regression of this issue would fail the test? Generic smoke tests,
vacuously-passing assertions, or tests that only check status codes without inspecting
response body content do **not** count.

If the diff contains test code that would break legitimate flows (over-blocks), that
test still does **not** earn a point for any rubric item — and any explicit
anti-overblock rubric items must fail.

{criteria}
