# Task: Message Service — Security Test Suite

The repository contains a private messaging service (`messagesvc`). A security
report indicates that private message content intended only for thread participants
is accessible to unauthorized callers across several endpoints.

Your job is to write a test suite that catches all instances of this data exposure.
Concretely: each test should **FAIL** when run against the current (buggy) repository —
because the private data IS leaking — and **PASS** once the vulnerability is correctly
fixed. A test that passes on the current buggy code is not catching anything.

**Constraints**:
- Write tests only. Do not modify any file under `messagesvc/`.
- Place your tests in `tests/exfiltration/`.
- Tests must be pytest-compatible.
- Refer to `tests/test_smoke.py` to understand how the API is intended to be used.

**Submission**:
Save your complete test suite as a unified diff to `/repo/answer.diff`.
The verifier reads this file as text — the diff is never applied to the working tree.

**Framework context**:
The service uses FastAPI with an in-memory store. All endpoints accept an `X-User-Id`
header to identify the caller. Users whose ID equals `admin` or starts with `admin` are
privileged; all others are regular users. Authentication is simulated — there is no
token validation.

Threads are created with an explicit `participants` list. Only participants and admins
may post new messages to a thread. The `private_content` field on messages carries
sensitive data that should be visible only to thread participants and admins.

The service exposes the following endpoints:

- `POST /threads` — create a thread with participants and initial message
- `GET /threads` — list all threads
- `GET /threads/search?q=` — search messages
- `GET /threads/{id}` — get thread detail (includes latest message preview)
- `POST /threads/{id}/messages` — post a message to a thread
- `GET /threads/{id}/messages` — list all messages in a thread
- `GET /threads/{id}/attachments?name=` — download one attachment by name
- `GET /threads/{id}/export?format=json|zip` — export thread
- `GET /messages/{id}` — get a single message by ID
