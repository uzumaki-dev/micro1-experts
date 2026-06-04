"""Legitimate-flow reference for the DocVault workspace.

Shows how the API is used under normal operation by an owner, an admin, a
collaborator, and a reader of a public document. Does NOT encode any
cross-user access-control expectations.
"""


def _h(user_id):
    return {"X-User-Id": user_id}


def _create(client, owner, **kw):
    payload = {"title": "Doc", "body": "hello", "visibility": "private",
               "secret_notes": "", "collaborators": [], "attachments": {}}
    payload.update(kw)
    return client.post("/documents", json=payload, headers=_h(owner)).json()


def test_owner_creates_and_reads_full(client):
    doc = _create(client, "alice", body="quarterly plan", secret_notes="top secret")
    r = client.get(f"/documents/{doc['id']}", headers=_h("alice"))
    assert r.status_code == 200
    body = r.json()
    assert body["owner_id"] == "alice"
    assert body["body"] == "quarterly plan"
    assert body["secret_notes"] == "top secret"


def test_admin_reads_document(client):
    doc = _create(client, "alice", body="quarterly plan")
    r = client.get(f"/documents/{doc['id']}", headers=_h("admin"))
    assert r.status_code == 200
    assert r.json()["body"] == "quarterly plan"


def test_public_document_body_readable_by_other(client):
    doc = _create(client, "alice", body="announcement", visibility="public")
    r = client.get(f"/documents/{doc['id']}", headers=_h("bob"))
    assert r.status_code == 200
    assert r.json()["body"] == "announcement"


def test_collaborator_reads_shared(client):
    doc = _create(client, "alice", body="draft", collaborators=["carol"])
    r = client.get(f"/documents/{doc['id']}", headers=_h("carol"))
    assert r.status_code == 200


def test_owner_lists_exports_and_versions(client):
    doc = _create(client, "alice", body="v1", secret_notes="s1")
    listing = client.get("/documents", headers=_h("alice")).json()
    assert any(d["id"] == doc["id"] for d in listing)
    export = client.get(f"/documents/{doc['id']}/export?format=json", headers=_h("alice"))
    assert export.status_code == 200
    versions = client.get(f"/documents/{doc['id']}/versions", headers=_h("alice"))
    assert versions.status_code == 200
    assert len(versions.json()["versions"]) >= 1


def test_owner_downloads_attachment(client):
    doc = _create(client, "alice", attachments={"a.txt": "hello-bytes"})
    r = client.get(f"/documents/{doc['id']}/attachments", params={"name": "a.txt"}, headers=_h("alice"))
    assert r.status_code == 200
    assert r.text == "hello-bytes"


def test_missing_user_header_rejected(client):
    doc = _create(client, "alice")
    r = client.get(f"/documents/{doc['id']}")  # no X-User-Id
    assert r.status_code == 401
