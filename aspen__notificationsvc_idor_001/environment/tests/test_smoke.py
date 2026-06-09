"""Smoke tests — legitimate-flow reference for notificationsvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from notificationsvc.app import app
from notificationsvc import store


@pytest.fixture(autouse=True)
def _reset():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(user_id: str) -> dict:
    return {"X-User-Id": user_id}


# --- Owner flows ---

def test_owner_creates_notification(client):
    r = client.post("/notifications", json={
        "subject": "Q3 Budget Alert",
        "recipient": "alice",
        "private_body": "Budget threshold exceeded by 12%",
        "delivery_log": [
            {
                "timestamp": "2025-01-01T00:00:00Z",
                "status": "delivered",
                "channel_code": "EMAIL-PRIV-001",
            }
        ],
        "attachments": {"report.pdf": "budget report content"},
        "shared_with": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["subject"] == "Q3 Budget Alert"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_notification(client):
    r = client.post("/notifications", json={
        "subject": "Confidential Notice",
        "private_body": "Internal escalation details",
        "attachments": {"details.pdf": "confidential content"},
    }, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.get(f"/notifications/{nid}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["private_body"] == "Internal escalation details"


def test_owner_lists_own_notifications(client):
    client.post("/notifications", json={"subject": "Notice A"}, headers=_h("alice"))
    client.post("/notifications", json={"subject": "Notice B"}, headers=_h("alice"))
    r = client.get("/notifications", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_notification_json(client):
    r = client.post("/notifications", json={
        "subject": "Export Test",
        "private_body": "export note",
        "delivery_log": [
            {"timestamp": "2025-01-01T00:00:00Z", "status": "delivered", "channel_code": "CH-01"}
        ],
    }, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.get(f"/notifications/{nid}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_notification_csv(client):
    r = client.post("/notifications", json={
        "subject": "CSV Export",
        "delivery_log": [
            {"timestamp": "2025-01-01T00:00:00Z", "status": "delivered", "channel_code": "CH-CSV"}
        ],
    }, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.get(f"/notifications/{nid}/export", params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Export" in r2.text


def test_owner_downloads_own_attachment(client):
    r = client.post("/notifications", json={
        "subject": "Attach Test",
        "attachments": {"findings.pdf": "findings content here"},
    }, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.get(f"/notifications/{nid}/attachments",
                    params={"name": "findings.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "findings content here" in r2.text


def test_owner_gets_delivery_log(client):
    r = client.post("/notifications", json={
        "subject": "Delivery Test",
        "delivery_log": [
            {"timestamp": "2025-01-01T00:00:00Z", "status": "delivered", "channel_code": "DL-01"}
        ],
    }, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.get(f"/notifications/{nid}/delivery-log", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["channel_code"] == "DL-01"


def test_owner_patches_own_notification(client):
    r = client.post("/notifications", json={"subject": "Old Subject"}, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.patch(f"/notifications/{nid}", json={"subject": "New Subject"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["subject"] == "New Subject"


def test_owner_duplicates_own_notification(client):
    r = client.post("/notifications", json={"subject": "Template Notice"}, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.post(f"/notifications/{nid}/duplicate", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != nid


def test_owner_forwards_own_notification(client):
    r = client.post("/notifications", json={"subject": "Forward Test"}, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.post(f"/notifications/{nid}/forward", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "forwarded"


# --- Admin flows ---

def test_admin_reads_any_notification(client):
    r = client.post("/notifications", json={
        "subject": "Confidential Notice",
        "private_body": "board-level strategy alert",
    }, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.get(f"/notifications/{nid}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["private_body"] == "board-level strategy alert"


# --- Non-admin creating and listing own notifications ---

def test_non_admin_creates_own_notification(client):
    r = client.post("/notifications", json={"subject": "Bob's Notice"}, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_notifications(client):
    client.post("/notifications", json={"subject": "My First Notice"}, headers=_h("bob"))
    r = client.get("/notifications", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# --- Collaborator and public-visibility flows ---

def test_collaborator_reads_shared_notification(client):
    r = client.post("/notifications", json={
        "subject": "Partner Notice",
        "private_body": "shared with partner",
        "shared_with": ["carol"],
        "visibility": "private",
    }, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.get(f"/notifications/{nid}", headers=_h("carol"))
    assert r2.status_code == 200
    assert "Partner Notice" in r2.text


def test_stranger_reads_public_notification(client):
    r = client.post("/notifications", json={
        "subject": "Public System Alert",
        "visibility": "public",
    }, headers=_h("alice"))
    nid = r.json()["id"]
    r2 = client.get(f"/notifications/{nid}", headers=_h("mallory"))
    assert r2.status_code == 200
    assert "Public System Alert" in r2.text
