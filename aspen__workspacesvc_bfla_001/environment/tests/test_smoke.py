"""Smoke tests — legitimate-flow reference for workspacesvc.

These tests document normal API behavior under intended use. They are
intentionally silent about authorization enforcement; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient
from workspacesvc.app import app
from workspacesvc import store


@pytest.fixture(autouse=True)
def _reset():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(user_id: str) -> dict:
    return {"X-User-Id": user_id}


def test_owner_creates_workspace(client):
    r = client.post("/workspaces", json={"name": "Acme Corp"}, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Acme Corp"
    assert data["owner_id"] == "alice"
    assert data["members"]["alice"] == "owner"
    assert data["is_archived"] is False


def test_owner_can_get_workspace(client):
    w = client.post("/workspaces", json={"name": "Beta"}, headers=_h("alice")).json()
    r = client.get(f"/workspaces/{w['id']}", headers=_h("alice"))
    assert r.status_code == 200
    assert r.json()["name"] == "Beta"


def test_owner_invites_member(client):
    w = client.post("/workspaces", json={"name": "Gamma"}, headers=_h("alice")).json()
    wid = w["id"]
    r = client.post(f"/workspaces/{wid}/invites",
                    json={"user_id": "bob", "role": "member", "private_reason": "new hire"},
                    headers=_h("alice"))
    assert r.status_code == 201
    ws = client.get(f"/workspaces/{wid}", headers=_h("alice")).json()
    assert "bob" in ws["members"]
    assert ws["members"]["bob"] == "member"


def test_member_can_read_workspace(client):
    w = client.post("/workspaces", json={"name": "Delta"}, headers=_h("alice")).json()
    wid = w["id"]
    client.post(f"/workspaces/{wid}/invites", json={"user_id": "carol", "role": "member"},
                headers=_h("alice"))
    r = client.get(f"/workspaces/{wid}", headers=_h("carol"))
    assert r.status_code == 200


def test_owner_patches_settings(client):
    w = client.post("/workspaces", json={"name": "Epsilon"}, headers=_h("alice")).json()
    wid = w["id"]
    r = client.patch(f"/workspaces/{wid}",
                     json={"settings": {"billing_email": "billing@epsilon.com"}},
                     headers=_h("alice"))
    assert r.status_code == 200
    assert r.json()["settings"]["billing_email"] == "billing@epsilon.com"


def test_owner_archives_workspace(client):
    w = client.post("/workspaces", json={"name": "Zeta"}, headers=_h("alice")).json()
    r = client.post(f"/workspaces/{w['id']}/archive", headers=_h("alice"))
    assert r.status_code == 200
    assert r.json()["is_archived"] is True


def test_owner_suspends_member(client):
    w = client.post("/workspaces", json={"name": "Eta"}, headers=_h("alice")).json()
    wid = w["id"]
    client.post(f"/workspaces/{wid}/invites", json={"user_id": "carol", "role": "member"},
                headers=_h("alice"))
    r = client.post(f"/workspaces/{wid}/suspend/carol", headers=_h("alice"))
    assert r.status_code == 200
    assert r.json()["suspended"] is True


def test_owner_changes_member_role(client):
    w = client.post("/workspaces", json={"name": "Theta"}, headers=_h("alice")).json()
    wid = w["id"]
    client.post(f"/workspaces/{wid}/invites", json={"user_id": "bob", "role": "member"},
                headers=_h("alice"))
    r = client.patch(f"/workspaces/{wid}/members/bob", json={"role": "admin"},
                     headers=_h("alice"))
    assert r.status_code == 200
    ws = client.get(f"/workspaces/{wid}", headers=_h("alice")).json()
    assert ws["members"]["bob"] == "admin"


def test_owner_removes_member(client):
    w = client.post("/workspaces", json={"name": "Iota"}, headers=_h("alice")).json()
    wid = w["id"]
    client.post(f"/workspaces/{wid}/invites", json={"user_id": "carol", "role": "member"},
                headers=_h("alice"))
    r = client.delete(f"/workspaces/{wid}/members/carol", headers=_h("alice"))
    assert r.status_code == 204
    ws = client.get(f"/workspaces/{wid}", headers=_h("alice")).json()
    assert "carol" not in ws["members"]


def test_admin_reads_audit_log(client):
    w = client.post("/workspaces", json={"name": "Kappa"}, headers=_h("alice")).json()
    wid = w["id"]
    client.post(f"/workspaces/{wid}/invites",
                json={"user_id": "bob", "role": "admin", "private_reason": "trusted admin"},
                headers=_h("alice"))
    r = client.get(f"/workspaces/{wid}/audit-log", headers=_h("alice"))
    assert r.status_code == 200
    events = r.json()
    assert any(e["event_type"] == "member_invited" for e in events)


def test_non_member_blocked(client):
    w = client.post("/workspaces", json={"name": "Lambda"}, headers=_h("alice")).json()
    r = client.get(f"/workspaces/{w['id']}", headers=_h("mallory"))
    assert r.status_code == 403


def test_owner_deletes_workspace(client):
    w = client.post("/workspaces", json={"name": "Mu"}, headers=_h("alice")).json()
    r = client.delete(f"/workspaces/{w['id']}", headers=_h("alice"))
    assert r.status_code == 204
