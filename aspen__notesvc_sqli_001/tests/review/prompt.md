You are an experienced staff engineer evaluating whether a unified-diff submission
contains tests that would catch a known set of ground-truth issues.

## Task background

This is an Aspen **test-authoring** task. The agent was *not* asked to fix application
code; it was asked to write tests that would catch a hidden rubric of issues. The base
repo is checked out at `/repo` at the task's `base_commit`.

The service under test is `notesvc`, a multi-user note-taking API built with FastAPI and
a SQLite backend. Users authenticate via the `X-User-Id` header — there is no token
validation. Each note is owned by its creator (the `owner` column is set from `X-User-Id`
at creation time). The service is supposed to return only the authenticated user's own
notes on all read endpoints.

The shipped (buggy) code contains raw f-string SQL interpolation in three query helpers
in `notesvc/db.py`:
- `search_notes`: `f"... WHERE owner='{owner}' AND (title LIKE '%{q}%' OR body LIKE '%{q}%')"` — `q` is injectable
- `filter_by_tag`: `f"... WHERE owner='{owner}' AND tags LIKE '%{tag}%'"` — `tag` is injectable
- `recent_notes`: `f"... WHERE owner='{owner}' AND created_at >= datetime('now', '-{days} days')"` — `days` is injectable

An attacker with a valid `X-User-Id` can inject UNION SELECT payloads into `q=`, `tag=`,
or `days=` to bypass the `owner` filter and read notes belonging to other users.

## Behavioral prompt the agent received

````
# Task: Note-Taking Service — SQL Injection Test Suite

A teammate found a security issue in our note-taking service (`notesvc`). While poking
around the API with their own user credentials, they were able to read notes belonging to
other users through several of the search and filter endpoints. The service is supposed to
enforce per-user data isolation — each user should only see their own notes — but something
in the query layer is letting cross-user reads slip through.

We don't have tests covering this. Your job is to write the test suite that catches it.

Concretely: each test should **FAIL** when run against the current (buggy) repository —
because the cross-user data IS leaking — and **PASS** once the vulnerability is correctly
fixed. A test that passes on the current buggy code is not catching anything.

**Constraints**:
- Write tests only. Do not modify any file under `notesvc/`.
- Place your tests in `tests/exfiltration/`.
- Tests must be pytest-compatible.
- Refer to `tests/test_smoke.py` to understand how the API is intended to be used.

**Submission**:
Save your complete test suite as a unified diff to `/repo/answer.diff`.
The verifier reads this file as text — the diff is never applied to the working tree.

**Framework context**:
The service uses FastAPI with a SQLite backend. All endpoints accept an `X-User-Id`
header to identify the caller — there is no token validation. Each note belongs to its
creator; the API is supposed to return only the authenticated user's own notes.

The service exposes the following endpoints:

- `POST /notes` — create a note `{"title": str, "body": str, "tags": [str]}`
- `GET /notes` — list the current user's notes
- `GET /notes/search?q=` — search notes by keyword (title and body)
- `GET /notes/filter?tag=` — filter notes by tag
- `GET /notes/recent?days=` — notes created within the last N days
- `GET /notes/{id}` — retrieve a single note (only owner can view)
- `PUT /notes/{id}` — update a note (only owner)
- `DELETE /notes/{id}` — delete a note (only owner)
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
