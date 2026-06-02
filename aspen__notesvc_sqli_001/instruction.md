# Task: Note-Taking Service — SQL Injection Test Suite

A teammate pinged me — they think they can read notes that don't belong to them. Said they
were poking around the API with their own `X-User-Id` and kept getting back content they
shouldn't have access to. They've been trying different things and keep finding notes from
other users showing up in their responses.

The service is supposed to enforce per-user data isolation — each user should only see their
own notes — but something is letting cross-user reads slip through.

We don't have tests covering this. Your job is to write the test suite that catches it.
A separate engineer will use your tests to validate their fix; for them to trust your tests,
the suite must (1) catch the cross-user data leak and (2) verify that a fix does not
over-block legitimate note access for the note's owner.

Concretely, the suite has two kinds of tests:

- **Exploit tests** assert that an attacker does NOT see another user's data. These should
  **FAIL** on the current (buggy) code — because the leak IS happening — and **PASS** once
  the vulnerability is correctly fixed. A test that passes on the buggy code is not catching
  anything.
- **Regression guards** assert that a legitimate owner can still access their own notes after
  a fix is applied. These should **PASS** on both the buggy code and the fixed code — because
  legitimate owner access works correctly in both states.

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
