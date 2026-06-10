"""Smoke tests — legitimate-flow reference for projectsvc.

These tests document normal API behavior under intended use. They are
intentionally silent about authorization enforcement; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient
from projectsvc.app import app
from projectsvc import store


@pytest.fixture(autouse=True)
def _reset():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(user_id: str) -> dict:
    return {"X-User-Id": user_id}


def test_admin_creates_project(client):
    r = client.post("/projects", json={"name": "Alpha", "description": "First project"},
                    headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Alpha"
    assert data["owner_id"] == "alice"
    assert data["members"]["alice"] == "admin"


def test_admin_adds_editor(client):
    p = client.post("/projects", json={"name": "Beta"}, headers=_h("alice")).json()
    r = client.post(f"/projects/{p['id']}/members",
                    json={"user_id": "carol", "role": "editor", "private_reason": "trusted contributor"},
                    headers=_h("alice"))
    assert r.status_code == 201
    assert r.json()["members"]["carol"] == "editor"


def test_admin_adds_viewer(client):
    p = client.post("/projects", json={"name": "Gamma"}, headers=_h("alice")).json()
    r = client.post(f"/projects/{p['id']}/members",
                    json={"user_id": "bob", "role": "viewer"},
                    headers=_h("alice"))
    assert r.status_code == 201
    assert r.json()["members"]["bob"] == "viewer"


def test_admin_changes_member_role(client):
    p = client.post("/projects", json={"name": "Delta"}, headers=_h("alice")).json()
    pid = p["id"]
    client.post(f"/projects/{pid}/members", json={"user_id": "bob", "role": "viewer"},
                headers=_h("alice"))
    r = client.patch(f"/projects/{pid}/members/bob", json={"role": "editor"},
                     headers=_h("alice"))
    assert r.status_code == 200
    assert r.json()["members"]["bob"] == "editor"


def test_admin_removes_member(client):
    p = client.post("/projects", json={"name": "Epsilon"}, headers=_h("alice")).json()
    pid = p["id"]
    client.post(f"/projects/{pid}/members", json={"user_id": "bob", "role": "viewer"},
                headers=_h("alice"))
    r = client.delete(f"/projects/{pid}/members/bob", headers=_h("alice"))
    assert r.status_code == 200
    assert "bob" not in r.json()["members"]


def test_admin_archives_project(client):
    p = client.post("/projects", json={"name": "Zeta"}, headers=_h("alice")).json()
    r = client.post(f"/projects/{p['id']}/archive", headers=_h("alice"))
    assert r.status_code == 200
    assert r.json()["is_archived"] is True


def test_admin_deletes_project(client):
    p = client.post("/projects", json={"name": "Eta"}, headers=_h("alice")).json()
    r = client.delete(f"/projects/{p['id']}", headers=_h("alice"))
    assert r.status_code == 204


def test_admin_reads_audit_log(client):
    p = client.post("/projects", json={"name": "Theta"}, headers=_h("alice")).json()
    pid = p["id"]
    client.post(f"/projects/{pid}/members",
                json={"user_id": "bob", "role": "viewer", "private_reason": "onboarding"},
                headers=_h("alice"))
    r = client.get(f"/projects/{pid}/audit-log", headers=_h("alice"))
    assert r.status_code == 200
    events = r.json()
    assert any(e["event_type"] == "member_added" for e in events)


def test_editor_updates_project(client):
    p = client.post("/projects", json={"name": "Iota"}, headers=_h("alice")).json()
    pid = p["id"]
    client.post(f"/projects/{pid}/members", json={"user_id": "carol", "role": "editor"},
                headers=_h("alice"))
    r = client.patch(f"/projects/{pid}", json={"name": "Iota v2"}, headers=_h("carol"))
    assert r.status_code == 200
    assert r.json()["name"] == "Iota v2"


def test_viewer_reads_project(client):
    p = client.post("/projects", json={"name": "Kappa"}, headers=_h("alice")).json()
    pid = p["id"]
    client.post(f"/projects/{pid}/members", json={"user_id": "bob", "role": "viewer"},
                headers=_h("alice"))
    r = client.get(f"/projects/{pid}", headers=_h("bob"))
    assert r.status_code == 200
    assert r.json()["name"] == "Kappa"


def test_viewer_cannot_edit_project(client):
    p = client.post("/projects", json={"name": "Lambda"}, headers=_h("alice")).json()
    pid = p["id"]
    client.post(f"/projects/{pid}/members", json={"user_id": "bob", "role": "viewer"},
                headers=_h("alice"))
    r = client.patch(f"/projects/{pid}", json={"name": "Lambda v2"}, headers=_h("bob"))
    assert r.status_code == 403


def test_non_member_blocked(client):
    p = client.post("/projects", json={"name": "Mu"}, headers=_h("alice")).json()
    r = client.get(f"/projects/{p['id']}", headers=_h("mallory"))
    assert r.status_code == 403


def test_user_lists_own_projects(client):
    p1 = client.post("/projects", json={"name": "Nu-1"}, headers=_h("alice")).json()
    p2 = client.post("/projects", json={"name": "Nu-2"}, headers=_h("alice")).json()
    r = client.get("/projects", headers=_h("alice"))
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()]
    assert p1["id"] in ids and p2["id"] in ids
