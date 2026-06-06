"""Smoke tests — legitimate-flow reference for proposalsvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from proposalsvc.app import app
from proposalsvc import store


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

def test_owner_creates_proposal(client):
    r = client.post("/proposals", json={
        "client_name": "Acme Corp",
        "status": "draft",
        "line_items": [
            {"description": "Consulting", "quantity": 5, "unit_price": 200.0, "margin_code": "MRG-001"}
        ],
        "internal_notes": "Client wants Q3 delivery",
        "discount_pct": 10.0,
        "attachments": {"terms.pdf": "terms content"},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["client_name"] == "Acme Corp"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_proposal(client):
    r = client.post("/proposals", json={
        "client_name": "Beta Inc",
        "internal_notes": "Sensitive negotiation details",
        "attachments": {"brief.pdf": "brief bytes"},
    }, headers=_h("alice"))
    p_id = r.json()["id"]
    r2 = client.get(f"/proposals/{p_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "Sensitive negotiation details"


def test_owner_lists_own_proposals(client):
    client.post("/proposals", json={"client_name": "Client A"}, headers=_h("alice"))
    client.post("/proposals", json={"client_name": "Client B"}, headers=_h("alice"))
    r = client.get("/proposals", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_proposal_json(client):
    r = client.post("/proposals", json={
        "client_name": "Export Client",
        "line_items": [
            {"description": "Service A", "quantity": 3, "unit_price": 100.0, "margin_code": "MRG-X"}
        ],
        "internal_notes": "export test note",
    }, headers=_h("alice"))
    p_id = r.json()["id"]
    r2 = client.get(f"/proposals/{p_id}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_proposal_csv(client):
    r = client.post("/proposals", json={
        "client_name": "CSV Client",
        "line_items": [
            {"description": "Widget", "quantity": 10, "unit_price": 50.0, "margin_code": "CSV-MRG"}
        ],
    }, headers=_h("alice"))
    p_id = r.json()["id"]
    r2 = client.get(f"/proposals/{p_id}/export", params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Client" in r2.text


def test_owner_downloads_own_attachment(client):
    r = client.post("/proposals", json={
        "client_name": "Attachment Client",
        "attachments": {"contract.pdf": "PDF content here"},
    }, headers=_h("alice"))
    p_id = r.json()["id"]
    r2 = client.get(f"/proposals/{p_id}/attachments", params={"name": "contract.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "PDF content here" in r2.text


def test_owner_gets_line_items(client):
    r = client.post("/proposals", json={
        "client_name": "Line Items Client",
        "line_items": [
            {"description": "Phase 1", "quantity": 2, "unit_price": 500.0, "margin_code": "LI-01"}
        ],
    }, headers=_h("alice"))
    p_id = r.json()["id"]
    r2 = client.get(f"/proposals/{p_id}/line-items", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["description"] == "Phase 1"


def test_owner_patches_own_proposal(client):
    r = client.post("/proposals", json={"client_name": "Old Client"}, headers=_h("alice"))
    p_id = r.json()["id"]
    r2 = client.patch(f"/proposals/{p_id}", json={"client_name": "New Client"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["client_name"] == "New Client"


def test_owner_clones_own_proposal(client):
    r = client.post("/proposals", json={"client_name": "Template Client"}, headers=_h("alice"))
    p_id = r.json()["id"]
    r2 = client.post(f"/proposals/{p_id}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != p_id


def test_owner_sends_own_proposal(client):
    r = client.post("/proposals", json={"client_name": "Send Client"}, headers=_h("alice"))
    p_id = r.json()["id"]
    r2 = client.post(f"/proposals/{p_id}/send", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "sent"


# --- Admin flows ---

def test_admin_reads_any_proposal(client):
    r = client.post("/proposals", json={
        "client_name": "Confidential Client",
        "internal_notes": "private sales notes",
    }, headers=_h("alice"))
    p_id = r.json()["id"]
    r2 = client.get(f"/proposals/{p_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "private sales notes"


# --- Non-admin creating and listing own proposals ---

def test_non_admin_creates_own_proposal(client):
    r = client.post("/proposals", json={"client_name": "Bob's Client"}, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_proposals(client):
    client.post("/proposals", json={"client_name": "My Client"}, headers=_h("bob"))
    r = client.get("/proposals", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1
