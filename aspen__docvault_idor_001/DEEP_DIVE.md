# Deep Dive: aspen__docvault_idor_001

## What the substrate is
`docvault/` is a small FastAPI service with in-memory storage:
- `docvault/models.py` — Pydantic request bodies.
- `docvault/store.py` — the document store + the intended access policy (in the
  module docstring). Attachments are keyed by a normalized `/att/<id>/<name>` path.
- `docvault/app.py` — HTTP routes. The caller is the `X-User-Id` header. The
  read/export/share/duplicate routes return full document content **without**
  checking ownership/visibility — this is the vulnerability.

This is an **access-control (IDOR)** task, not feature-coverage. The substrate is
shipped in its vulnerable state; the agent writes tests that would *catch* the
leak (and would pass once a fix is applied).

## The leak, and where it surfaces
A document's `body`, `secret_notes`, and attachment bytes are meant to be private
to the owner (admins + collaborators allowed; public docs expose only `body`). The
shipped code leaks private content to any authenticated stranger through:

| Surface | Endpoint |
|---|---|
| direct read | `GET /documents/{id}` |
| list | `GET /documents` |
| search | `GET /documents/search?q=` |
| export (json + zip) | `GET /documents/{id}/export?format=` |
| attachment + traversal | `GET /documents/{id}/attachments?name=` |
| version history | `GET /documents/{id}/versions` |
| duplicate → read/share/export | `POST /documents/{id}/duplicate` then read/share/export the clone |

## How grading works
The agent writes pytest tests under `tests/idor/` and submits them as a unified
diff to `/repo/answer.diff`. RewardKit runs a `claude-code` judge that reads the
diff as text and scores each of 17 rubric items binary; final reward is the
weighted mean (max weight 45). The diff is never executed.

## Why it discriminates
The obvious `GET /documents/{id}` leak is caught by any capable model. Separation
comes from discovering the *other* surfaces — search, the zip export (bytes inside
the archive), version history, the three duplicate-laundering flows, and path
traversal — plus the sentinel-byte assertion (rub_017). Weaker models miss whole
surfaces, so the cumulative missed weight pulls their score down while a frontier
model stays high.

## Local validation
```bash
cd aspen__docvault_idor_001
python3.11 -m venv .venv && .venv/bin/pip install -r environment/requirements.txt
PYTHONPATH=environment .venv/bin/pytest environment/tests/test_smoke.py -q   # 7 passed (legit flows)
```
The oracle (`solution/solve.sh`) embeds a full suite. Run against the **vulnerable**
substrate it shows 12 failures (the direct-coverage tests catching the leak) and 5
passes (the anti-overblock tests) — the expected signature for an IDOR oracle. The
judge scores the oracle diff near 1.0 because each test clearly targets a rubric item.

## Layout note
Realm uses `environment/` as the Docker build context, so the substrate and build
inputs live under `environment/`. Verifier files (`tests/test.sh`, `tests/review/`)
and `solution/solve.sh` stay at the task root. The agent sees everything at `/repo`
because the Dockerfile copies it there.
