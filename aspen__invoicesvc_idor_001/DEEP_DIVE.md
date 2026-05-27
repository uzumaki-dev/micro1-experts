# DEEP DIVE: aspen__invoicesvc_idor_001

## What is this service?

`invoicesvc` is a minimal FastAPI billing service. Users create invoices for their
clients. Each invoice has an owner (`owner_id`), a client name, line items (with
internal cost codes), private memo notes (`internal_notes`), and file attachments.

Authentication is header-based: every request includes an `X-User-Id` header. There
is no password or token system — the header value IS the user identity.

## The bug

The service stores invoices in an in-memory dict keyed by UUID. The read-path
endpoints (`GET /invoices/{id}`, `GET /invoices`, `GET /invoices/search`,
`GET /invoices/{id}/line-items`, `GET /invoices/{id}/export`,
`GET /invoices/{id}/attachments`) have **no ownership check**. Any caller can read
any invoice by guessing or iterating IDs.

The `POST /invoices/{id}/duplicate` endpoint copies the full invoice including
`internal_notes` and `attachments` into a new invoice owned by the attacker. This
creates a "laundering" path: duplicate the victim's invoice, then call PATCH, share,
or export on the clone — all of which the attacker legitimately owns.

## How the task works

An agent is told "a user reported finding someone else's invoice data." The agent must:
1. Read `invoicesvc/app.py` to understand the API surface.
2. Read `tests/test_smoke.py` to understand the legitimate-flow contract.
3. Write a test suite in `tests/exfiltration/` that catches each leak path.
4. Include anti-overblock assertions so a correct fix doesn't break owner/admin access.
5. Submit the suite as a unified diff to `/repo/answer.diff`.

## What good tests look like

A strong test seeds a sentinel string (`ZZ-SENTINEL-8k2p1`) into `internal_notes`
and asserts that string is NOT present in the stranger's response body. A weak test
only checks `assert r.status_code == 403`. The rubric requires sentinel content
inspection for all primary access-control items.

## File map

```
invoicesvc/
├── __init__.py          — empty package marker
├── models.py            — Pydantic models: Invoice, LineItem, InvoiceCreate, InvoicePatch
├── store.py             — in-memory dict store with reset() for test isolation
└── app.py               — FastAPI routes (contains the IDOR bug)

tests/
└── test_smoke.py        — legitimate-flow reference tests (no sentinels, no bug hints)
```

## Running tests locally

```bash
# From environment/ directory with deps installed:
PYTHONPATH=. pytest tests/test_smoke.py -v
```
