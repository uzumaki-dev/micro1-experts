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

**Constraints**:
- Write tests only. Do not modify any file under `notesvc/`.
- Place your tests in `tests/exfiltration/`.
- Tests must be pytest-compatible.
- Refer to `tests/test_smoke.py` to understand how the API is intended to be used.

Submit only your test files as a unified diff via `submit_answer` (applies clean from `/repo`).
