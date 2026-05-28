"""Smoke tests — legitimate-flow reference for expensesvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from expensesvc.app import app
from expensesvc import store


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

def test_owner_creates_expense(client):
    r = client.post("/expenses", json={
        "merchant": "Acme Travel",
        "status": "draft",
        "line_items": [
            {"description": "Flight", "amount": 450.0, "cost_code": "CC-001", "discount_code": ""}
        ],
        "private_notes": "Q3 conference",
        "policy_code": "POL-2024",
        "receipts": {"flight.pdf": "boarding pass content"},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["merchant"] == "Acme Travel"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_expense(client):
    r = client.post("/expenses", json={
        "merchant": "Globex Hotel",
        "private_notes": "VIP client stay",
        "receipts": {"hotel.pdf": "hotel receipt"},
    }, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.get(f"/expenses/{exp_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["private_notes"] == "VIP client stay"


def test_owner_lists_own_expenses(client):
    client.post("/expenses", json={"merchant": "Vendor A"}, headers=_h("alice"))
    client.post("/expenses", json={"merchant": "Vendor B"}, headers=_h("alice"))
    r = client.get("/expenses", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_expense_json(client):
    r = client.post("/expenses", json={
        "merchant": "Export Vendor",
        "line_items": [
            {"description": "Work", "amount": 200.0, "cost_code": "CC-X", "discount_code": "D10"}
        ],
        "private_notes": "export test note",
    }, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.get(f"/expenses/{exp_id}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_expense_csv(client):
    r = client.post("/expenses", json={
        "merchant": "CSV Vendor",
        "line_items": [
            {"description": "Service", "amount": 100.0, "cost_code": "CSV-CC", "discount_code": ""}
        ],
    }, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.get(f"/expenses/{exp_id}/export", params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Vendor" in r2.text


def test_owner_downloads_own_receipt(client):
    r = client.post("/expenses", json={
        "merchant": "Receipt Vendor",
        "receipts": {"receipt.pdf": "PDF content here"},
    }, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.get(f"/expenses/{exp_id}/receipts", params={"name": "receipt.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "PDF content here" in r2.text


def test_owner_gets_line_items(client):
    r = client.post("/expenses", json={
        "merchant": "Line Vendor",
        "line_items": [
            {"description": "Item A", "amount": 50.0, "cost_code": "LI-01", "discount_code": ""}
        ],
    }, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.get(f"/expenses/{exp_id}/line-items", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["description"] == "Item A"


def test_owner_patches_own_expense(client):
    r = client.post("/expenses", json={"merchant": "Old Vendor"}, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.patch(f"/expenses/{exp_id}", json={"merchant": "New Vendor"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["merchant"] == "New Vendor"


def test_owner_clones_own_expense(client):
    r = client.post("/expenses", json={"merchant": "Template Vendor"}, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.post(f"/expenses/{exp_id}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != exp_id


def test_owner_submits_own_expense(client):
    r = client.post("/expenses", json={"merchant": "Submit Vendor"}, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.post(f"/expenses/{exp_id}/submit", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "submitted"


# --- Admin flows ---

def test_admin_reads_any_expense(client):
    r = client.post("/expenses", json={
        "merchant": "Confidential Vendor",
        "private_notes": "private deal notes",
    }, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.get(f"/expenses/{exp_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["private_notes"] == "private deal notes"


# --- Non-admin creating and listing own expenses ---

def test_non_admin_creates_own_expense(client):
    r = client.post("/expenses", json={"merchant": "Bob Vendor"}, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_expenses(client):
    client.post("/expenses", json={"merchant": "My Vendor"}, headers=_h("bob"))
    r = client.get("/expenses", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# --- Collaborator and public-visibility flows ---

def test_collaborator_reads_shared_expense(client):
    """A user in the collaborators list can read the expense."""
    r = client.post("/expenses", json={
        "merchant": "Partner Vendor",
        "private_notes": "shared with partner",
        "collaborators": ["carol"],
        "visibility": "private",
    }, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.get(f"/expenses/{exp_id}", headers=_h("carol"))
    assert r2.status_code == 200
    assert "Partner Vendor" in r2.text


def test_stranger_reads_public_expense(client):
    """An expense with visibility=public is readable by any authenticated user."""
    r = client.post("/expenses", json={
        "merchant": "Public Conference Fee",
        "visibility": "public",
    }, headers=_h("alice"))
    exp_id = r.json()["id"]
    r2 = client.get(f"/expenses/{exp_id}", headers=_h("mallory"))
    assert r2.status_code == 200
    assert "Public Conference Fee" in r2.text
