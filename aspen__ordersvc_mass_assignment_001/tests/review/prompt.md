You are an experienced staff engineer evaluating whether a unified-diff submission
contains tests that would catch a known set of ground-truth issues.

## Task background

This is an Aspen **test-authoring** task. The agent was *not* asked to fix application
code; it was asked to write tests that would catch a hidden rubric of issues. The base
repo is checked out at `/repo` at the task's `base_commit`. The service under test is
`ordersvc`, an in-memory e-commerce order management API (FastAPI). The caller is
identified by the `X-User-Id` header. The `admin` user may update any order field
including privileged fields. Regular (non-admin) users may legitimately update only
`shipping_address` and `notes` via PATCH. The fields `status`, `discount_pct`, and
`payment_status` are privileged and should only be settable by admin. The shipped code
does not enforce field-level role checks: both the PATCH endpoint and the POST creation
endpoint accept privileged fields from any authenticated caller without restriction.

## Behavioral prompt the agent received

```
A bug report came in from a QA engineer: they were able to get orders into states
that should only be set by the platform's operations team. Specifically, order records
are showing discounts and fulfillment statuses that customers claim they never requested
and that bypass the normal approval workflow.

We have no tests covering this. Your job is to write the test suite that catches it.

Write tests only. Do not modify any file under `ordersvc/`. A separate engineer will
use your tests to validate their fix; for them to trust your tests, the suite must
(1) catch the issue being exploited and (2) not break legitimate customer or admin flows.

Put your tests under `tests/access/`. `tests/test_smoke.py` shows the legitimate
customer and admin flows already in use — your suite should pin those down with
anti-overblock assertions so they cannot regress.

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
requirement): `tests/access/`.

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
