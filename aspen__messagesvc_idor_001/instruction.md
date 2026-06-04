# Task: Message Service — Security Test Suite

The repository contains a private messaging service (`messagesvc`). A security
report indicates that private message content intended only for thread participants
is being returned in API responses to callers who are not members of the thread.

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
