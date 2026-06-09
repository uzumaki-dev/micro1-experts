"""Smoke tests — legitimate-flow reference for quotesvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from quotesvc.app import app
from quotesvc import store


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

def test_owner_creates_quote(client):
    r = client.post("/quotes", json={
        "client_name": "Acme Corp",
        "status": "draft",
        "line_items": [
            {
                "description": "Implementation",
                "quantity": 10.0,
                "unit_price": 150.0,
                "vendor_code": "VC-001",
                "discount_code": "DISC10",
            }
        ],
        "internal_notes": "Q3 enterprise deal",
        "terms": "Net 30",
        "attachments": {"proposal.pdf": "proposal content"},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["client_name"] == "Acme Corp"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_quote(client):
    r = client.post("/quotes", json={
        "client_name": "Globex Ltd",
        "internal_notes": "Confidential pricing",
        "attachments": {"pricing.pdf": "confidential pricing sheet"},
    }, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.get(f"/quotes/{qid}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "Confidential pricing"


def test_owner_lists_own_quotes(client):
    client.post("/quotes", json={"client_name": "Client A"}, headers=_h("alice"))
    client.post("/quotes", json={"client_name": "Client B"}, headers=_h("alice"))
    r = client.get("/quotes", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_quote_json(client):
    r = client.post("/quotes", json={
        "client_name": "Export Client",
        "line_items": [
            {"description": "Consulting", "quantity": 5.0, "unit_price": 200.0,
             "vendor_code": "VC-X", "discount_code": "D10"}
        ],
        "internal_notes": "export test note",
    }, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.get(f"/quotes/{qid}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_quote_csv(client):
    r = client.post("/quotes", json={
        "client_name": "CSV Client",
        "line_items": [
            {"description": "Service", "quantity": 1.0, "unit_price": 500.0,
             "vendor_code": "VC-CSV", "discount_code": ""}
        ],
    }, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.get(f"/quotes/{qid}/export", params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Client" in r2.text


def test_owner_downloads_own_attachment(client):
    r = client.post("/quotes", json={
        "client_name": "Attach Client",
        "attachments": {"sow.pdf": "Statement of Work content"},
    }, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.get(f"/quotes/{qid}/attachments",
                    params={"name": "sow.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "Statement of Work content" in r2.text


def test_owner_gets_line_items(client):
    r = client.post("/quotes", json={
        "client_name": "Line Client",
        "line_items": [
            {"description": "Phase 1", "quantity": 1.0, "unit_price": 1000.0,
             "vendor_code": "LI-01", "discount_code": ""}
        ],
    }, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.get(f"/quotes/{qid}/line-items", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["description"] == "Phase 1"


def test_owner_patches_own_quote(client):
    r = client.post("/quotes", json={"client_name": "Old Client"}, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.patch(f"/quotes/{qid}", json={"client_name": "New Client"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["client_name"] == "New Client"


def test_owner_forks_own_quote(client):
    r = client.post("/quotes", json={"client_name": "Template Client"}, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.post(f"/quotes/{qid}/fork", headers=_h("alice"))
    assert r2.status_code == 201
    fork = r2.json()
    assert fork["owner_id"] == "alice"
    assert fork["id"] != qid


def test_owner_sends_own_quote(client):
    r = client.post("/quotes", json={"client_name": "Send Client"}, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.post(f"/quotes/{qid}/send", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "sent"


# --- Admin flows ---

def test_admin_reads_any_quote(client):
    r = client.post("/quotes", json={
        "client_name": "Private Corp",
        "internal_notes": "sensitive deal notes",
    }, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.get(f"/quotes/{qid}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "sensitive deal notes"


# --- Non-admin creating and listing own quotes ---

def test_non_admin_creates_own_quote(client):
    r = client.post("/quotes", json={"client_name": "Bob Corp"}, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_quotes(client):
    client.post("/quotes", json={"client_name": "My Client"}, headers=_h("bob"))
    r = client.get("/quotes", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# --- Collaborator and public-visibility flows ---

def test_collaborator_reads_shared_quote(client):
    r = client.post("/quotes", json={
        "client_name": "Partner Corp",
        "internal_notes": "shared with partner",
        "collaborators": ["carol"],
        "visibility": "private",
    }, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.get(f"/quotes/{qid}", headers=_h("carol"))
    assert r2.status_code == 200
    assert "Partner Corp" in r2.text


def test_stranger_reads_public_quote(client):
    r = client.post("/quotes", json={
        "client_name": "Public Tender",
        "visibility": "public",
    }, headers=_h("alice"))
    qid = r.json()["id"]
    r2 = client.get(f"/quotes/{qid}", headers=_h("mallory"))
    assert r2.status_code == 200
    assert "Public Tender" in r2.text
