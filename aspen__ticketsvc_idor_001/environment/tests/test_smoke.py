"""Smoke tests for ticketsvc — encode normal-operation surface only.

These tests describe legitimate expected behavior and MUST PASS against
the shipped (vulnerable) substrate. They do NOT probe the IDOR bug.
"""
import pytest
from fastapi.testclient import TestClient

from ticketsvc.app import app
from ticketsvc import store


@pytest.fixture(autouse=True)
def _reset():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(user_id):
    return {"X-User-Id": user_id}


def test_agent_creates_ticket_with_internal_notes(client):
    r = client.post("/tickets", json={
        "title": "Login broken",
        "description": "Cannot log in with SSO.",
        "internal_notes": "Related to OAuth config change.",
        "priority": "high",
        "assignee_id": "agent1",
        "attachments": {"screenshot.png": "binary-data"},
        "tags": ["auth", "sso"],
    }, headers=_h("agent1"))
    assert r.status_code == 201
    data = r.json()
    assert data["internal_notes"] == "Related to OAuth config change."
    assert data["reporter_id"] == "agent1"


def test_reporter_creates_ticket(client):
    r = client.post("/tickets", json={
        "title": "Password reset broken",
        "description": "Reset link expired instantly.",
    }, headers=_h("alice"))
    assert r.status_code == 201
    assert r.json()["reporter_id"] == "alice"


def test_agent_adds_internal_comment(client):
    t = client.post("/tickets", json={
        "title": "T", "description": "D",
    }, headers=_h("alice")).json()
    r = client.post(f"/tickets/{t['id']}/comments", json={
        "body": "Investigating DB layer.", "type": "internal",
    }, headers=_h("agent1"))
    assert r.status_code == 201
    assert r.json()["type"] == "internal"


def test_reporter_adds_public_comment(client):
    t = client.post("/tickets", json={
        "title": "T", "description": "D",
    }, headers=_h("alice")).json()
    r = client.post(f"/tickets/{t['id']}/comments", json={
        "body": "Still broken for me.", "type": "public",
    }, headers=_h("alice"))
    assert r.status_code == 201


def test_agent_reads_private_attachment(client):
    t = client.post("/tickets", json={
        "title": "T", "description": "D",
        "attachments": {"private_logs.txt": "sensitive-log-data"},
    }, headers=_h("agent1")).json()
    r = client.get(f"/tickets/{t['id']}/attachments",
                   params={"name": "private_logs.txt"}, headers=_h("agent1"))
    assert r.status_code == 200
    assert "sensitive-log-data" in r.text


def test_any_user_reads_public_attachment(client):
    t = client.post("/tickets", json={
        "title": "T", "description": "D",
        "attachments": {"readme.txt": "public-content"},
    }, headers=_h("alice")).json()
    r = client.get(f"/tickets/{t['id']}/attachments",
                   params={"name": "readme.txt"}, headers=_h("bob"))
    assert r.status_code == 200


def test_reporter_exports_own_ticket_json(client):
    t = client.post("/tickets", json={
        "title": "T", "description": "D",
    }, headers=_h("alice")).json()
    r = client.get(f"/tickets/{t['id']}/export",
                   params={"format": "json"}, headers=_h("alice"))
    assert r.status_code == 200
    assert "ticket" in r.json()


def test_reporter_exports_own_ticket_zip(client):
    t = client.post("/tickets", json={
        "title": "T", "description": "D",
    }, headers=_h("alice")).json()
    r = client.get(f"/tickets/{t['id']}/export",
                   params={"format": "zip"}, headers=_h("alice"))
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


def test_reporter_clones_own_ticket(client):
    t = client.post("/tickets", json={
        "title": "T", "description": "D",
    }, headers=_h("alice")).json()
    r = client.post(f"/tickets/{t['id']}/clone", headers=_h("alice"))
    assert r.status_code == 201
    assert r.json()["reporter_id"] == "alice"
    assert r.json()["id"] != t["id"]


def test_list_returns_created_ticket(client):
    client.post("/tickets", json={
        "title": "My issue", "description": "D",
    }, headers=_h("alice"))
    r = client.get("/tickets", headers=_h("alice"))
    assert r.status_code == 200
    assert any(t["title"] == "My issue" for t in r.json())


def test_agent_updates_ticket_status(client):
    t = client.post("/tickets", json={
        "title": "T", "description": "D",
    }, headers=_h("alice")).json()
    r = client.patch(f"/tickets/{t['id']}", json={"status": "closed"},
                     headers=_h("agent1"))
    assert r.status_code == 200
    assert r.json()["status"] == "closed"


def test_search_returns_matching_ticket(client):
    client.post("/tickets", json={
        "title": "network outage", "description": "D",
    }, headers=_h("alice"))
    r = client.get("/tickets/search", params={"q": "network"}, headers=_h("alice"))
    assert r.status_code == 200
    assert any("network" in t["title"] for t in r.json())
