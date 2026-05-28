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
