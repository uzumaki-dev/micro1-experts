# DEEP DIVE: aspen__expensesvc_idor_001

## What is this task?

An AI agent is asked to write a security test suite for an expense management API that
has an Insecure Direct Object Reference (IDOR) vulnerability. The agent must discover
all the leak surfaces and write sentinel-based tests that will catch the bug — and also
write anti-overblock tests to ensure legitimate access isn't broken by an over-eager fix.

## The bug in plain English

The service stores expense reports keyed by UUID. Any authenticated user can read any
expense by guessing or enumerating its ID — the service never checks whether the caller
owns the expense they're requesting. This means a stranger can see another employee's
private notes, cost codes, and receipt files.

## The substrate

FastAPI service (`expensesvc/app.py`) with 10 endpoints. In-memory store (`store.py`).
Auth is just an `X-User-Id` header — no JWT, no sessions. The `admin` user can read
everything; regular users should only see their own expenses.

## Buggy endpoints

- `GET /expenses` — returns ALL expenses, not just the caller's
- `GET /expenses/search?q=` — searches ALL expenses including private_notes
- `GET /expenses/{id}` — no ownership check
- `GET /expenses/{id}/line-items` — no ownership check, leaks cost_code
- `GET /expenses/{id}/export?format=json|csv` — no ownership check
- `GET /expenses/{id}/receipts?name=` — no ownership check + path traversal bug
- `POST /expenses/{id}/clone` — no ownership check + copies private fields into attacker's clone

## What makes a good test suite?

1. **Sentinel bytes** — seed unique random strings into private fields; assert those strings
   never appear in a stranger's response. Catches both 200-with-data AND redaction gaps.
2. **All surfaces** — cover every endpoint, including exports and receipts.
3. **Laundering chains** — test that cloning doesn't launder private data into an
   attacker-owned copy that can then be freely exported.
4. **Anti-overblock** — assert that owner, admin, collaborator, and public-visibility
   access still works after a fix.

## File layout

```
environment/expensesvc/app.py      ← the buggy service (10 endpoints)
environment/expensesvc/models.py   ← Expense, LineItem, ExpenseCreate, ExpensePatch
environment/expensesvc/store.py    ← in-memory store
environment/tests/test_smoke.py    ← reference legitimate flows (baked into image)
tests/review/agent_judge.toml      ← 17-item rubric (total weight 48)
solution/solve.sh                  ← oracle answer
```
