"""Oracle test suite for ticketsvc IDOR task (rub_001..rub_016).

Direct-coverage tests assert that a stranger never receives private content
(content-absent style, robust to either a 403 or a redaction fix).
Anti-overblock tests assert legitimate access is preserved.
Against the shipped (vulnerable) substrate:
  - direct tests FAIL (catching the leak)
  - anti-overblock tests PASS
Against a correct fix all tests pass.
"""
import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from ticketsvc.app import app
from ticketsvc import store

INTERNAL = "ZZ-INTERNAL-7f3a9"
ATTACH   = "ZZ-ATTACH-7f3a9"
COMMENT  = "ZZ-COMMENT-7f3a9"
DESC     = "ticket-description-text"
STRANGER = "mallory"


@pytest.fixture(autouse=True)
def _reset():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(uid):
    return {"X-User-Id": uid}


def _seed(client, owner="alice"):
    t = client.post("/tickets", json={
        "title": "Agent investigation",
        "description": DESC,
        "internal_notes": INTERNAL,
        "priority": "high",
        "assignee_id": "agent1",
        "attachments": {
            "public_readme.txt": "public-content",
            "private_logs.txt": ATTACH,
        },
    }, headers=_h("agent1")).json()
    client.post(f"/tickets/{t['id']}/comments",
                json={"body": COMMENT, "type": "internal"}, headers=_h("agent1"))
    return t


def test_get_ticket_hides_internal_notes(client):
    t = _seed(client)
    r = client.get(f"/tickets/{t['id']}", headers=_h(STRANGER))
    assert INTERNAL not in r.text


def test_list_hides_internal_notes(client):
    _seed(client)
    r = client.get("/tickets", headers=_h(STRANGER))
    assert INTERNAL not in r.text


def test_search_hides_internal_notes(client):
    _seed(client)
    r = client.get("/tickets/search", params={"q": INTERNAL[:10]}, headers=_h(STRANGER))
    assert INTERNAL not in r.text


def test_export_json_hides_internal_notes(client):
    t = _seed(client)
    r = client.get(f"/tickets/{t['id']}/export", params={"format": "json"},
                   headers=_h(STRANGER))
    assert INTERNAL not in r.text


def test_export_zip_hides_sentinels(client):
    t = _seed(client)
    r = client.get(f"/tickets/{t['id']}/export", params={"format": "zip"},
                   headers=_h(STRANGER))
    blob = r.content
    if r.status_code == 200 and blob[:2] == b"PK":
        zf = zipfile.ZipFile(io.BytesIO(blob))
        blob = b"".join(zf.read(n) for n in zf.namelist())
    assert INTERNAL.encode() not in blob
    assert ATTACH.encode() not in blob


def test_private_attachment_hidden(client):
    t = _seed(client)
    r = client.get(f"/tickets/{t['id']}/attachments",
                   params={"name": "private_logs.txt"}, headers=_h(STRANGER))
    assert ATTACH not in r.text


def test_internal_comments_hidden(client):
    t = _seed(client)
    r = client.get(f"/tickets/{t['id']}/comments", headers=_h(STRANGER))
    assert COMMENT not in r.text


def test_clone_then_get_hides_internal_notes(client):
    t = _seed(client)
    clone = client.post(f"/tickets/{t['id']}/clone", headers=_h(STRANGER))
    if clone.status_code == 201:
        r = client.get(f"/tickets/{clone.json()['id']}", headers=_h(STRANGER))
        assert INTERNAL not in r.text
    else:
        assert clone.status_code in (401, 403, 404)


def test_clone_then_export_hides_sentinel(client):
    t = _seed(client)
    clone = client.post(f"/tickets/{t['id']}/clone", headers=_h(STRANGER))
    if clone.status_code == 201:
        r = client.get(f"/tickets/{clone.json()['id']}/export",
                       params={"format": "json"}, headers=_h(STRANGER))
        assert INTERNAL not in r.text
    else:
        assert clone.status_code in (401, 403, 404)


def test_agent_still_sees_internal_notes(client):
    t = _seed(client)
    r = client.get(f"/tickets/{t['id']}", headers=_h("agent1"))
    assert r.status_code == 200
    assert r.json()["internal_notes"] == INTERNAL


def test_agent_still_sees_internal_comments(client):
    t = _seed(client)
    r = client.get(f"/tickets/{t['id']}/comments", headers=_h("agent1"))
    bodies = [c["body"] for c in r.json()]
    assert COMMENT in bodies


def test_reporter_own_write_surface_not_blocked(client):
    t = client.post("/tickets", json={
        "title": "My issue", "description": DESC,
    }, headers=_h("alice")).json()
    clone_r  = client.post(f"/tickets/{t['id']}/clone", headers=_h("alice"))
    export_r = client.get(f"/tickets/{t['id']}/export",
                          params={"format": "json"}, headers=_h("alice"))
    comment_r = client.post(f"/tickets/{t['id']}/comments",
                            json={"body": "Still seeing this", "type": "public"},
                            headers=_h("alice"))
    assert clone_r.status_code == 201
    assert export_r.status_code == 200
    assert comment_r.status_code == 201


def test_public_attachment_accessible(client):
    t = _seed(client)
    r = client.get(f"/tickets/{t['id']}/attachments",
                   params={"name": "public_readme.txt"}, headers=_h(STRANGER))
    assert r.status_code == 200


def test_path_traversal_rejected(client):
    _seed(client)
    t2 = client.post("/tickets", json={
        "title": "T2", "description": "D",
    }, headers=_h("bob")).json()
    r = client.get(f"/tickets/{t2['id']}/attachments",
                   params={"name": "../agent_handbook"}, headers=_h(STRANGER))
    assert r.status_code in (400, 403, 404)


def test_reporter_reads_own_description(client):
    t = client.post("/tickets", json={
        "title": "T", "description": DESC,
    }, headers=_h("alice")).json()
    r = client.get(f"/tickets/{t['id']}", headers=_h("alice"))
    assert r.status_code == 200
    assert DESC in r.text


def test_sentinel_sweep(client):
    t = _seed(client)
    tid = t["id"]
    texts = [
        client.get(f"/tickets/{tid}", headers=_h(STRANGER)).text,
        client.get("/tickets", headers=_h(STRANGER)).text,
        client.get("/tickets/search", params={"q": "investigation"},
                   headers=_h(STRANGER)).text,
        client.get(f"/tickets/{tid}/export", params={"format": "json"},
                   headers=_h(STRANGER)).text,
        client.get(f"/tickets/{tid}/comments", headers=_h(STRANGER)).text,
    ]
    zip_r = client.get(f"/tickets/{tid}/export", params={"format": "zip"},
                       headers=_h(STRANGER))
    zip_blob = b""
    if zip_r.status_code == 200 and zip_r.content[:2] == b"PK":
        zf = zipfile.ZipFile(io.BytesIO(zip_r.content))
        zip_blob = b"".join(zf.read(n) for n in zf.namelist())
    all_bytes = "".join(texts).encode() + zip_blob
    assert INTERNAL.encode() not in all_bytes
    assert ATTACH.encode() not in all_bytes
    assert COMMENT.encode() not in all_bytes
