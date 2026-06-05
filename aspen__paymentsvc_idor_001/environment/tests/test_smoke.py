"""Smoke tests — legitimate-flow reference for paymentsvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from paymentsvc.app import app
from paymentsvc import store


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

def test_owner_creates_payment(client):
    r = client.post("/payments", json={
        "merchant": "Acme Supplies",
        "status": "pending",
        "line_items": [
            {"description": "Hardware", "amount": 750.0, "fee_code": "FEE-001", "category_code": "CAT-A"}
        ],
        "private_notes": "Q3 procurement deal",
        "reference_code": "REF-2024-001",
        "documents": {"invoice.pdf": "invoice content"},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["merchant"] == "Acme Supplies"
    assert data["owner_id"] == "alice"
    assert data["status"] == "pending"


def test_owner_reads_own_payment(client):
    r = client.post("/payments", json={
        "merchant": "Globex Corp",
        "private_notes": "VIP contract payment",
        "documents": {"contract.pdf": "contract content"},
    }, headers=_h("alice"))
    pmt_id = r.json()["id"]
    r2 = client.get(f"/payments/{pmt_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["private_notes"] == "VIP contract payment"


def test_owner_lists_own_payments(client):
    client.post("/payments", json={"merchant": "Vendor A"}, headers=_h("alice"))
    client.post("/payments", json={"merchant": "Vendor B"}, headers=_h("alice"))
    r = client.get("/payments", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_payment_json(client):
    r = client.post("/payments", json={
        "merchant": "Export Vendor",
        "line_items": [
            {"description": "Service", "amount": 300.0, "fee_code": "FEE-X", "category_code": "CAT-B"}
        ],
        "private_notes": "export test note",
    }, headers=_h("alice"))
    pmt_id = r.json()["id"]
    r2 = client.get(f"/payments/{pmt_id}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_payment_csv(client):
    r = client.post("/payments", json={
        "merchant": "CSV Vendor",
        "line_items": [
            {"description": "Labor", "amount": 150.0, "fee_code": "CSV-FEE", "category_code": ""}
        ],
    }, headers=_h("alice"))
    pmt_id = r.json()["id"]
    r2 = client.get(f"/payments/{pmt_id}/export", params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Vendor" in r2.text


def test_owner_downloads_own_document(client):
    r = client.post("/payments", json={
        "merchant": "Document Vendor",
        "documents": {"receipt.pdf": "PDF content here"},
    }, headers=_h("alice"))
    pmt_id = r.json()["id"]
    r2 = client.get(f"/payments/{pmt_id}/documents", params={"name": "receipt.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "PDF content here" in r2.text


def test_owner_gets_line_items(client):
    r = client.post("/payments", json={
        "merchant": "Line Vendor",
        "line_items": [
            {"description": "Item A", "amount": 50.0, "fee_code": "LI-01", "category_code": ""}
        ],
    }, headers=_h("alice"))
    pmt_id = r.json()["id"]
    r2 = client.get(f"/payments/{pmt_id}/line-items", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["description"] == "Item A"


def test_owner_patches_own_payment(client):
    r = client.post("/payments", json={"merchant": "Old Vendor"}, headers=_h("alice"))
    pmt_id = r.json()["id"]
    r2 = client.patch(f"/payments/{pmt_id}", json={"merchant": "New Vendor"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["merchant"] == "New Vendor"


def test_owner_clones_own_payment(client):
    r = client.post("/payments", json={"merchant": "Template Vendor"}, headers=_h("alice"))
    pmt_id = r.json()["id"]
    r2 = client.post(f"/payments/{pmt_id}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != pmt_id


def test_owner_voids_own_payment(client):
    r = client.post("/payments", json={"merchant": "Void Vendor"}, headers=_h("alice"))
    pmt_id = r.json()["id"]
    r2 = client.post(f"/payments/{pmt_id}/void", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "void"


# --- Admin flows ---

def test_admin_reads_any_payment(client):
    r = client.post("/payments", json={
        "merchant": "Confidential Vendor",
        "private_notes": "private deal notes",
    }, headers=_h("alice"))
    pmt_id = r.json()["id"]
    r2 = client.get(f"/payments/{pmt_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["private_notes"] == "private deal notes"


# --- Non-admin creating and listing own payments ---

def test_non_admin_creates_own_payment(client):
    r = client.post("/payments", json={"merchant": "Bob Vendor"}, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_payments(client):
    client.post("/payments", json={"merchant": "My Vendor"}, headers=_h("bob"))
    r = client.get("/payments", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1
