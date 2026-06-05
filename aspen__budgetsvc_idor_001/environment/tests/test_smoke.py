"""Smoke tests — legitimate-flow reference for budgetsvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from budgetsvc.app import app
from budgetsvc import store


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

def test_owner_creates_budget(client):
    r = client.post("/budgets", json={
        "name": "Q3 Marketing Budget",
        "status": "draft",
        "items": [
            {
                "description": "Digital advertising",
                "amount": 10000.0,
                "allocation_code": "MKT-Q3-001",
                "discount_code": "",
            }
        ],
        "budget_memo": "Approved by VP of Marketing",
        "fiscal_code": "FC-2025-Q3",
        "attachments": {},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Q3 Marketing Budget"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_budget(client):
    r = client.post("/budgets", json={
        "name": "Annual IT Budget",
        "budget_memo": "Confidential — board review pending",
        "fiscal_code": "FC-IT-2025",
        "attachments": {"proposal.pdf": "proposal content"},
    }, headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.get(f"/budgets/{budget_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["budget_memo"] == "Confidential — board review pending"
    assert r2.json()["fiscal_code"] == "FC-IT-2025"


def test_owner_lists_own_budgets(client):
    client.post("/budgets", json={"name": "Budget A"}, headers=_h("alice"))
    client.post("/budgets", json={"name": "Budget B"}, headers=_h("alice"))
    r = client.get("/budgets", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_budget_json(client):
    r = client.post("/budgets", json={
        "name": "Export Budget",
        "items": [
            {"description": "Servers", "amount": 5000.0,
             "allocation_code": "IT-SRV", "discount_code": "D10"}
        ],
        "budget_memo": "export test note",
        "fiscal_code": "FC-EXP",
    }, headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.get(f"/budgets/{budget_id}/export",
                    params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_budget_csv(client):
    r = client.post("/budgets", json={
        "name": "CSV Budget",
        "items": [
            {"description": "Licenses", "amount": 2000.0,
             "allocation_code": "SW-LIC", "discount_code": ""}
        ],
        "fiscal_code": "FC-CSV",
    }, headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.get(f"/budgets/{budget_id}/export",
                    params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Budget" in r2.text


def test_owner_downloads_own_attachment(client):
    r = client.post("/budgets", json={
        "name": "Attachment Budget",
        "attachments": {"contract.pdf": "contract content"},
    }, headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.get(f"/budgets/{budget_id}/attachments",
                    params={"name": "contract.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "contract content" in r2.text


def test_owner_gets_items(client):
    r = client.post("/budgets", json={
        "name": "Items Budget",
        "items": [
            {"description": "Task A", "amount": 1000.0,
             "allocation_code": "ALLOC-01", "discount_code": ""}
        ],
    }, headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.get(f"/budgets/{budget_id}/items", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["description"] == "Task A"


def test_owner_patches_own_budget(client):
    r = client.post("/budgets", json={"name": "Old Name"},
                    headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.patch(f"/budgets/{budget_id}", json={"name": "New Name"},
                      headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["name"] == "New Name"


def test_owner_clones_own_budget(client):
    r = client.post("/budgets", json={"name": "Template Budget"},
                    headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.post(f"/budgets/{budget_id}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != budget_id


def test_owner_submits_own_budget(client):
    r = client.post("/budgets", json={"name": "Submit Budget"},
                    headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.post(f"/budgets/{budget_id}/submit", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "submitted"


# --- Admin flows ---

def test_admin_reads_any_budget(client):
    r = client.post("/budgets", json={
        "name": "Confidential Budget",
        "budget_memo": "board-only memo",
        "fiscal_code": "FC-BOARD",
    }, headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.get(f"/budgets/{budget_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["budget_memo"] == "board-only memo"


# --- Non-admin creating and listing own budgets ---

def test_non_admin_creates_own_budget(client):
    r = client.post("/budgets", json={"name": "Bob's Budget"},
                    headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_budgets(client):
    client.post("/budgets", json={"name": "My Budget"}, headers=_h("bob"))
    r = client.get("/budgets", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# --- Collaborator and public-visibility flows ---

def test_collaborator_reads_shared_budget(client):
    r = client.post("/budgets", json={
        "name": "Shared Budget",
        "budget_memo": "shared with partner",
        "collaborators": ["carol"],
        "visibility": "private",
    }, headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.get(f"/budgets/{budget_id}", headers=_h("carol"))
    assert r2.status_code == 200
    assert "Shared Budget" in r2.text


def test_stranger_reads_public_budget(client):
    r = client.post("/budgets", json={
        "name": "Open Budget Initiative",
        "visibility": "public",
    }, headers=_h("alice"))
    budget_id = r.json()["id"]

    r2 = client.get(f"/budgets/{budget_id}", headers=_h("mallory"))
    assert r2.status_code == 200
    assert "Open Budget Initiative" in r2.text
