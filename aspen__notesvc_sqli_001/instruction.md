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
