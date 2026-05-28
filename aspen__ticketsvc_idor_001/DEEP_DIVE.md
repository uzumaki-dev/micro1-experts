# Deep Dive: aspen__ticketsvc_idor_001

## What Is This?

An AI evaluation task. An AI agent is given a buggy FastAPI service and told to write
a test suite that catches all instances of a reported security vulnerability. This
document explains the service, the bug, and what a good test suite looks like.

## The Service

`ticketsvc` is a support-ticket management service. Think Zendesk or Jira — users file
tickets, support agents annotate them with private investigation notes, and everything
is stored in-memory.

Two key resources:

**Ticket** — has a `description` (public, what the reporter wrote) and `internal_notes`
(private, what agents write during investigation). In a correct service, only agents/admins
see `internal_notes`.

**Comment** — has a `body` and a `type` field (`"public"` or `"internal"`). Internal
comments are agent-only discussion, not visible to the ticket reporter.

The service also supports attachments (some public, some private), JSON/ZIP export, and
cloning (copying a ticket to a new ID).

## The Bug

Every read endpoint returns all fields to every authenticated caller — there is no
ownership or role check. Specifically:

- `GET /tickets/{id}` returns `internal_notes` to any caller
- `GET /tickets` list includes `internal_notes` in every row
- `GET /tickets/search?q=` searches `internal_notes` and returns results to anyone
- `GET /tickets/{id}/export` dumps everything including `internal_notes`
- `GET /tickets/{id}/attachments` serves private attachment files to anyone
- `GET /tickets/{id}/comments` includes `type="internal"` comments for everyone
- `POST /tickets/{id}/clone` → cloned ticket inherits `internal_notes`
- Path traversal in attachment names reaches a global private store

## Sentinel Values

The oracle seeds three known strings into the fixture to make assertions robust:
- `ZZ-INTERNAL-7f3a9` — placed in `internal_notes`
- `ZZ-ATTACH-7f3a9` — placed in a private attachment's content
- `ZZ-COMMENT-7f3a9` — placed in an internal comment's body

A test asserting the sentinel doesn't appear in a non-agent response passes whether the
fix returns 403, redacts the field, or filters the response — all correct mitigations
are accepted.

## What a Good Test Suite Looks Like

A maximally-scoring submission:
1. Seeds all three sentinel values into a fixture ticket
2. Calls each of the 9 leak surfaces as a non-agent caller
3. Asserts the sentinel strings are absent (NOT just checking status codes)
4. Opens ZIP exports and inspects archive member bytes
5. Chains POST /clone → GET/export and asserts the clone doesn't leak inherited fields
6. Asserts that agents still see `internal_notes` and internal comments (anti-overblock)
7. Asserts that reporters can still clone, export, and comment on their own tickets
8. Rejects path-traversal attachment names

## Why Is This Discriminative?

A weak model (Qwen 3.5) typically:
- Checks `GET /tickets/{id}` and `GET /tickets` (obvious surfaces)
- Writes `assert r.status_code == 403` (fails sentinel-inspection rubric items)
- Misses the comments endpoint, the clone laundering flows, and the ZIP archive inspection
- Scores ~32% (passes only regression guards)

A strong model (Claude Opus 4.7) typically:
- Discovers all 9 leak surfaces including comments and laundering chains
- Seeds sentinel values and asserts content absence
- Opens ZIP archives to inspect bytes
- Scores ~86%

## Rubric Summary (16 items, weight 44)

| Items | Category | Count | Weight each |
|-------|----------|-------|-------------|
| rub_001–009 | Direct coverage (access_control, ownership, redaction) | 9 | 3.0 |
| rub_010–013, 015 | Regression_guard | 5 | 3.0 / 2.0 |
| rub_014 | Traversal | 1 | 2.0 |
| rub_016 | test_quality (sentinel sweep) | 1 | 1.0 |
