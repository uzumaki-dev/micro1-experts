# aspen__leasesvc_idor_001

## Status

Lease management service leaks private landlord notes and per-clause assessment codes
to any authenticated user because read, list, search, export, clauses, and document
endpoints perform no ownership checks. The task rewards tests that verify:
(1) a stranger cannot read another owner's `private_notes`, clause `clause_code`,
or document bytes; (2) a clone-then-mutate laundering flow does not inherit
private fields into the attacker's copy; and (3) legitimate owner and admin
flows are not over-blocked.

## Substrate

* **Source**: Hand-authored FastAPI service (~200 LOC)
* **Commit**: `b21cb61673d1492da33f53ea8f5eb21a1f574828`
* **Description**: In-memory multi-tenant lease API. Identity via
  `X-User-Id` header. Admin identity: `admin`. Leases carry `private_notes`,
  per-clause `clause_code`, and `attachments` (filename→content map).
  Endpoints: POST/GET/PATCH/search/export/clauses/documents/clone/renew/share.
  All read endpoints ship without ownership checks. Clone copies private fields
  verbatim. Path traversal in the documents endpoint allows cross-lease
  file reads.

## Submission Contract

The agent writes a unified diff (adding files under `tests/exfiltration/`) to
`/repo/answer.diff`. The judge inspects that file as a text artifact — the diff
is never applied to the working tree. Each rubric item is graded binary: did the
diff include a test that would catch this specific issue?

## Calibration Results

*To be filled after calibration runs.*
