#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

OUTFILE=/repo/answer.diff
TESTPATH=tests/exfiltration/test_lease_idor.py

mkdir -p "$(dirname "$OUTFILE")"
mkdir -p "/repo/tests/exfiltration"

cat > "/repo/$TESTPATH" <<'PYEOF'
"""Oracle test suite for aspen__leasesvc_idor_001 (rub_001..rub_014).

Direct-coverage tests assert that a stranger never receives another owner's
private lease content (sentinel-absent style, robust to either a 403 or a
redaction fix). Anti-overblock tests assert legitimate access is preserved.
Against the shipped (vulnerable) substrate the direct tests FAIL (catching
the leak) and the anti-overblock tests PASS; against a correct fix all pass.
"""
import pytest
from fastapi.testclient import TestClient

from leasesvc.app import app
from leasesvc import store

SECRET   = "ZZ-SENTINEL-lsvc7"
CLAUSE   = "ZZ-CLAUSE-lsvc7"
ATTACH   = "ZZ-ATTACH-lsvc7"
STRANGER = "mallory"


@pytest.fixture(autouse=True)
def _reset():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(user_id: str) -> dict:
    return {"X-User-Id": user_id}


def _private_lease(client, owner: str = "alice") -> dict:
    return client.post("/leases", json={
        "tenant_name": "Acme Corp",
        "property_address": "123 Main St",
        "visibility": "private",
        "private_notes": SECRET,
        "clauses": [
            {"description": "Monthly rent", "clause_code": CLAUSE}
        ],
        "attachments": {"lease.pdf": ATTACH},
    }, headers=_h(owner)).json()


# rub_001 — stranger cannot read a private lease's private_notes
def test_stranger_cannot_read_private_lease(client):
    d = _private_lease(client)
    r = client.get(f"/leases/{d['id']}", headers=_h(STRANGER))
    assert SECRET not in r.text and CLAUSE not in r.text


# rub_002 — list does not expose other owners' private lease data
def test_list_excludes_other_owners_private(client):
    _private_lease(client, "alice")
    r = client.get("/leases", headers=_h(STRANGER))
    assert SECRET not in r.text and CLAUSE not in r.text


# rub_003 — search does not return other owners' private lease content
def test_search_excludes_other_owners_private(client):
    _private_lease(client, "alice")
    r = client.get("/leases/search", params={"q": "Acme"}, headers=_h(STRANGER))
    assert SECRET not in r.text and CLAUSE not in r.text


# rub_004 — clauses endpoint does not leak clause_code sentinel
def test_clauses_does_not_leak_clause_code(client):
    d = _private_lease(client)
    r = client.get(f"/leases/{d['id']}/clauses", headers=_h(STRANGER))
    assert CLAUSE not in r.text


# rub_005 — JSON export does not leak private_notes sentinel
def test_export_json_does_not_leak(client):
    d = _private_lease(client)
    r = client.get(f"/leases/{d['id']}/export",
                   params={"format": "json"}, headers=_h(STRANGER))
    assert SECRET not in r.text and CLAUSE not in r.text


# rub_006 — CSV export does not contain private bytes (inspect rows)
def test_export_csv_does_not_contain_private_bytes(client):
    d = _private_lease(client)
    r = client.get(f"/leases/{d['id']}/export",
                   params={"format": "csv"}, headers=_h(STRANGER))
    text = r.text if r.status_code == 200 else ""
    assert SECRET not in text and CLAUSE not in text


# rub_007 — stranger cannot download a non-owned document
def test_stranger_cannot_download_document(client):
    d = _private_lease(client)
    r = client.get(f"/leases/{d['id']}/documents",
                   params={"name": "lease.pdf"}, headers=_h(STRANGER))
    assert ATTACH not in r.text


# rub_008 — path traversal in document name cannot reach another lease's files
def test_path_traversal_blocked(client):
    victim = _private_lease(client, "alice")
    mine = client.post("/leases", json={
        "tenant_name": "My Property",
        "attachments": {"x.txt": "mydata"},
    }, headers=_h(STRANGER)).json()
    r = client.get(
        f"/leases/{mine['id']}/documents",
        params={"name": f"../{victim['id']}/lease.pdf"},
        headers=_h(STRANGER),
    )
    assert ATTACH not in r.text


# rub_009 — clone-then-PATCH laundering does not expose inherited private fields
def test_clone_then_patch_does_not_leak(client):
    victim = _private_lease(client, "alice")
    clone_r = client.post(f"/leases/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text
    if clone_r.status_code == 201:
        patch_r = client.patch(
            f"/leases/{clone_r.json()['id']}",
            json={"tenant_name": "Renamed Tenant"},
            headers=_h(STRANGER),
        )
        assert SECRET not in patch_r.text


# rub_010 — clone-then-renew laundering does not expose inherited private fields
def test_clone_then_renew_does_not_leak(client):
    victim = _private_lease(client, "alice")
    clone_r = client.post(f"/leases/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text
    if clone_r.status_code == 201:
        renew_r = client.post(
            f"/leases/{clone_r.json()['id']}/renew",
            headers=_h(STRANGER),
        )
        assert SECRET not in renew_r.text


# rub_011 — clone-then-export laundering does not expose inherited private fields
def test_clone_then_export_does_not_leak(client):
    victim = _private_lease(client, "alice")
    clone_r = client.post(f"/leases/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text
    if clone_r.status_code == 201:
        export_r = client.get(
            f"/leases/{clone_r.json()['id']}/export",
            params={"format": "json"},
            headers=_h(STRANGER),
        )
        assert SECRET not in export_r.text and CLAUSE not in export_r.text


# rub_012 — anti-overblock: owner still reads full lease with private_notes
def test_owner_still_reads_full(client):
    d = _private_lease(client, "alice")
    r = client.get(f"/leases/{d['id']}", headers=_h("alice"))
    assert r.status_code == 200 and r.json()["private_notes"] == SECRET


# rub_013 — anti-overblock: admin still reads full lease with private_notes
def test_admin_still_reads_full(client):
    d = _private_lease(client, "alice")
    r = client.get(f"/leases/{d['id']}", headers=_h("admin"))
    assert r.status_code == 200 and r.json()["private_notes"] == SECRET


# rub_014 — anti-overblock: non-admin can still create and list own leases
def test_user_can_create_and_list_own(client):
    create_r = client.post("/leases", json={"tenant_name": "My New Tenant"},
                           headers=_h(STRANGER))
    assert create_r.status_code == 201
    listing = client.get("/leases", headers=_h(STRANGER)).json()
    assert any(l["id"] == create_r.json()["id"] for l in listing)
PYEOF

# Generate a proper unified diff using git (auto-computes correct hunk count)
cd /repo
git add "$TESTPATH"
git diff --cached -- "$TESTPATH" > "$OUTFILE"
git rm --cached "$TESTPATH"
rm -f "/repo/$TESTPATH"

echo "Wrote oracle diff to $OUTFILE"
