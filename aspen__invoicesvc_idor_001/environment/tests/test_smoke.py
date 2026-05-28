"""Smoke tests — legitimate-flow reference for invoicesvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from invoicesvc.app import app
from invoicesvc import store


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

def test_owner_creates_invoice(client):
    r = client.post("/invoices", json={
        "client_name": "Acme Corp",
        "status": "draft",
        "line_items": [
            {
                "description": "Consulting",
                "quantity": 2,
                "unit_price": 500.0,
                "cost_code": "CC-001",
                "discount_code": "",
            }
        ],
        "internal_notes": "First engagement",
        "attachments": {"sow.pdf": "signed SOW content"},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["client_name"] == "Acme Corp"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_invoice(client):
    r = client.post("/invoices", json={
        "client_name": "Globex",
        "internal_notes": "VIP client notes",
        "attachments": {"po.pdf": "purchase order"},
    }, headers=_h("alice"))
    inv_id = r.json()["id"]

    r2 = client.get(f"/invoices/{inv_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "VIP client notes"


def test_owner_lists_own_invoices(client):
    client.post("/invoices", json={"client_name": "Corp A"}, headers=_h("alice"))
    client.post("/invoices", json={"client_name": "Corp B"}, headers=_h("alice"))
    r = client.get("/invoices", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_invoice_json(client):
    r = client.post("/invoices", json={
        "client_name": "Export Corp",
        "line_items": [
            {"description": "Work", "quantity": 1, "unit_price": 200.0,
             "cost_code": "CC-X", "discount_code": "D10"}
        ],
        "internal_notes": "export test note",
    }, headers=_h("alice"))
    inv_id = r.json()["id"]

    r2 = client.get(f"/invoices/{inv_id}/export",
                    params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_invoice_csv(client):
    r = client.post("/invoices", json={
        "client_name": "CSV Corp",
        "line_items": [
            {"description": "Service", "quantity": 3, "unit_price": 100.0,
             "cost_code": "CSV-CC", "discount_code": ""}
        ],
    }, headers=_h("alice"))
    inv_id = r.json()["id"]

    r2 = client.get(f"/invoices/{inv_id}/export",
                    params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Corp" in r2.text


def test_owner_downloads_own_attachment(client):
    r = client.post("/invoices", json={
        "client_name": "Attach Corp",
        "attachments": {"invoice.pdf": "PDF content here"},
    }, headers=_h("alice"))
    inv_id = r.json()["id"]

    r2 = client.get(f"/invoices/{inv_id}/attachments",
                    params={"name": "invoice.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "PDF content here" in r2.text


def test_owner_gets_line_items(client):
    r = client.post("/invoices", json={
        "client_name": "Line Corp",
        "line_items": [
            {"description": "Item A", "quantity": 1, "unit_price": 50.0,
             "cost_code": "LI-01", "discount_code": ""}
        ],
    }, headers=_h("alice"))
    inv_id = r.json()["id"]

    r2 = client.get(f"/invoices/{inv_id}/line-items", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["description"] == "Item A"


def test_owner_patches_own_invoice(client):
    r = client.post("/invoices", json={"client_name": "Old Name"},
                    headers=_h("alice"))
    inv_id = r.json()["id"]

    r2 = client.patch(f"/invoices/{inv_id}", json={"client_name": "New Name"},
                      headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["client_name"] == "New Name"


def test_owner_duplicates_own_invoice(client):
    r = client.post("/invoices", json={"client_name": "Template Co"},
                    headers=_h("alice"))
    inv_id = r.json()["id"]

    r2 = client.post(f"/invoices/{inv_id}/duplicate", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != inv_id


# --- Admin flows ---

def test_admin_reads_any_invoice(client):
    r = client.post("/invoices", json={
        "client_name": "Confidential Client",
        "internal_notes": "private deal notes",
    }, headers=_h("alice"))
    inv_id = r.json()["id"]

    r2 = client.get(f"/invoices/{inv_id}", headers=_h("admin"))
    assert r2.status_code == 200


# --- Non-admin creating and listing own invoices ---

def test_non_admin_creates_own_invoice(client):
    r = client.post("/invoices", json={"client_name": "Bob LLC"},
                    headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_invoices(client):
    client.post("/invoices", json={"client_name": "My Client"},
                headers=_h("bob"))
    r = client.get("/invoices", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# --- Collaborator and public-visibility flows ---

def test_collaborator_reads_shared_invoice(client):
    """A user in the collaborators list can read the invoice."""
    r = client.post("/invoices", json={
        "client_name": "Partner Corp",
        "internal_notes": "shared with partner",
        "collaborators": ["carol"],
        "visibility": "private",
    }, headers=_h("alice"))
    inv_id = r.json()["id"]

    r2 = client.get(f"/invoices/{inv_id}", headers=_h("carol"))
    assert r2.status_code == 200
    assert "Partner Corp" in r2.text


def test_stranger_reads_public_invoice(client):
    """An invoice with visibility=public is readable by any authenticated user."""
    r = client.post("/invoices", json={
        "client_name": "Public Tender Notice",
        "visibility": "public",
    }, headers=_h("alice"))
    inv_id = r.json()["id"]

    r2 = client.get(f"/invoices/{inv_id}", headers=_h("mallory"))
    assert r2.status_code == 200
    assert "Public Tender Notice" in r2.text
