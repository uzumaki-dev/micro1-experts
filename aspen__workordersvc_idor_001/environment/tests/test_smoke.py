"""Smoke tests — legitimate-flow reference for workordersvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from workordersvc.app import app
from workordersvc import store


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

def test_owner_creates_workorder(client):
    r = client.post("/workorders", json={
        "title": "HVAC Maintenance",
        "status": "open",
        "entries": [
            {"description": "Labor", "hours": 4.0, "labor_code": "LAB-001", "discount_code": "DISC-A"}
        ],
        "internal_notes": "Client requires evening access",
        "private_rate": 85.0,
        "documents": {"checklist.pdf": "checklist content"},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "HVAC Maintenance"
    assert data["owner_id"] == "alice"
    assert data["status"] == "open"


def test_owner_reads_own_workorder(client):
    r = client.post("/workorders", json={
        "title": "Plumbing Repair",
        "internal_notes": "Check basement valves",
        "documents": {"photo.jpg": "photo bytes"},
    }, headers=_h("alice"))
    wo_id = r.json()["id"]
    r2 = client.get(f"/workorders/{wo_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "Check basement valves"


def test_owner_lists_own_workorders(client):
    client.post("/workorders", json={"title": "Job A"}, headers=_h("alice"))
    client.post("/workorders", json={"title": "Job B"}, headers=_h("alice"))
    r = client.get("/workorders", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_workorder_json(client):
    r = client.post("/workorders", json={
        "title": "Export Job",
        "entries": [
            {"description": "Service", "hours": 2.0, "labor_code": "LAB-X", "discount_code": ""}
        ],
        "internal_notes": "export test note",
    }, headers=_h("alice"))
    wo_id = r.json()["id"]
    r2 = client.get(f"/workorders/{wo_id}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_workorder_csv(client):
    r = client.post("/workorders", json={
        "title": "CSV Job",
        "entries": [
            {"description": "Maintenance", "hours": 6.0, "labor_code": "CSV-LAB", "discount_code": ""}
        ],
    }, headers=_h("alice"))
    wo_id = r.json()["id"]
    r2 = client.get(f"/workorders/{wo_id}/export", params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Job" in r2.text


def test_owner_downloads_own_document(client):
    r = client.post("/workorders", json={
        "title": "Document Job",
        "documents": {"report.pdf": "PDF content here"},
    }, headers=_h("alice"))
    wo_id = r.json()["id"]
    r2 = client.get(f"/workorders/{wo_id}/documents", params={"name": "report.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "PDF content here" in r2.text


def test_owner_gets_entries(client):
    r = client.post("/workorders", json={
        "title": "Entry Job",
        "entries": [
            {"description": "Task A", "hours": 3.0, "labor_code": "E-01", "discount_code": ""}
        ],
    }, headers=_h("alice"))
    wo_id = r.json()["id"]
    r2 = client.get(f"/workorders/{wo_id}/entries", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["description"] == "Task A"


def test_owner_patches_own_workorder(client):
    r = client.post("/workorders", json={"title": "Old Title"}, headers=_h("alice"))
    wo_id = r.json()["id"]
    r2 = client.patch(f"/workorders/{wo_id}", json={"title": "New Title"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["title"] == "New Title"


def test_owner_clones_own_workorder(client):
    r = client.post("/workorders", json={"title": "Template Job"}, headers=_h("alice"))
    wo_id = r.json()["id"]
    r2 = client.post(f"/workorders/{wo_id}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != wo_id


def test_owner_submits_own_workorder(client):
    r = client.post("/workorders", json={"title": "Submit Job"}, headers=_h("alice"))
    wo_id = r.json()["id"]
    r2 = client.post(f"/workorders/{wo_id}/submit", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "submitted"


# --- Admin flows ---

def test_admin_reads_any_workorder(client):
    r = client.post("/workorders", json={
        "title": "Confidential Job",
        "internal_notes": "private site notes",
    }, headers=_h("alice"))
    wo_id = r.json()["id"]
    r2 = client.get(f"/workorders/{wo_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "private site notes"


# --- Non-admin creating and listing own workorders ---

def test_non_admin_creates_own_workorder(client):
    r = client.post("/workorders", json={"title": "Bob's Job"}, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_workorders(client):
    client.post("/workorders", json={"title": "My Job"}, headers=_h("bob"))
    r = client.get("/workorders", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1
