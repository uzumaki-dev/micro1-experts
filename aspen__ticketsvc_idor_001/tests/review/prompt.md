You are an experienced staff engineer evaluating whether a unified-diff submission
contains tests that would catch a known set of ground-truth issues.

## Task background

This is an Aspen **test-authoring** task. The agent was *not* asked to fix application
code; it was asked to write tests that would catch a hidden rubric of issues. The base
repo is checked out at `/repo` at the task's `base_commit`.

The service under test is `ticketsvc`, an in-memory multi-tenant support-ticket API (FastAPI).
The caller is identified by the `X-User-Id` header; users whose ID starts with `agent` or equals
`admin` are privileged agents/admins — all others are regular reporters. Tickets carry an
`internal_notes` field (agent-only) and `type="internal"` comments (agent-only). Private
attachments are registered with a `private=true` flag. The shipped (buggy) code does not enforce
role-based filtering on any read, list, search, export, comments, attachment, or clone endpoint —
all authenticated callers receive the full payload including `internal_notes`, internal comments,
and private attachment bytes.

## Behavioral prompt the agent received

````
# Task: Support Ticket Service — Security Test Suite

The repository contains a support-ticket management service (`ticketsvc`). A security
report indicates that private data intended only for support agents is accessible to
unauthorized callers across several endpoints.

Your job is to write a test suite that catches all instances of this data exposure.
Concretely: each test should **FAIL** when run against the current (buggy) repository —
because the private data IS leaking — and **PASS** once the vulnerability is correctly
fixed. A test that passes on the current buggy code is not catching anything.

**Constraints**:
- Write tests only. Do not modify any file under `ticketsvc/`.
- Place your tests in `tests/exfiltration/`.
- Tests must be pytest-compatible.
- Refer to `tests/test_smoke.py` to understand how the API is intended to be used.

**Submission**:
Save your complete test suite as a unified diff to `/repo/answer.diff`.
The verifier reads this file as text — the diff is never applied to the working tree.

**Framework context**:
The service uses FastAPI with an in-memory store. All endpoints accept an `X-User-Id`
header to identify the caller. Users whose ID starts with `agent` or equals `admin` are
privileged; all others are regular reporters. Authentication is simulated — there is no
token validation.

The service exposes the following endpoints:

- `POST /tickets` — create a ticket
- `GET /tickets` — list all tickets
- `GET /tickets/search?q=` — search tickets
- `GET /tickets/{id}` — get ticket detail
- `PATCH /tickets/{id}` — update a ticket
- `POST /tickets/{id}/comments` — add a comment (body + type field)
- `GET /tickets/{id}/comments` — list comments
- `GET /tickets/{id}/attachments?name=` — download one attachment by name
- `GET /tickets/{id}/export?format=json|zip` — export ticket
- `POST /tickets/{id}/clone` — clone a ticket (returns new ticket object)
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
