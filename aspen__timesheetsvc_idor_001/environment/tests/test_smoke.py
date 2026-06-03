"""Smoke tests — legitimate-flow reference for timesheetsvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from timesheetsvc.app import app
from timesheetsvc import store


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

def test_owner_creates_timesheet(client):
    r = client.post("/timesheets", json={
        "project": "Acme Consulting",
        "status": "draft",
        "entries": [
            {
                "description": "Requirements gathering",
                "hours": 4.0,
                "rate_code": "RC-001",
                "discount_code": "",
            }
        ],
        "internal_notes": "First engagement kickoff",
        "private_rate": 150.0,
        "receipts": {"hotel.pdf": "hotel receipt bytes"},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["project"] == "Acme Consulting"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_timesheet(client):
    r = client.post("/timesheets", json={
        "project": "Globex Project",
        "internal_notes": "VIP client billing notes",
        "private_rate": 200.0,
        "receipts": {"po.pdf": "purchase order"},
    }, headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.get(f"/timesheets/{ts_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "VIP client billing notes"
    assert r2.json()["private_rate"] == 200.0


def test_owner_lists_own_timesheets(client):
    client.post("/timesheets", json={"project": "Project A"}, headers=_h("alice"))
    client.post("/timesheets", json={"project": "Project B"}, headers=_h("alice"))
    r = client.get("/timesheets", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_timesheet_json(client):
    r = client.post("/timesheets", json={
        "project": "Export Project",
        "entries": [
            {"description": "Dev work", "hours": 8.0, "rate_code": "RC-X", "discount_code": "D10"}
        ],
        "internal_notes": "export test note",
        "private_rate": 175.0,
    }, headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.get(f"/timesheets/{ts_id}/export",
                    params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_timesheet_csv(client):
    r = client.post("/timesheets", json={
        "project": "CSV Project",
        "entries": [
            {"description": "Analysis", "hours": 3.0, "rate_code": "CSV-RC", "discount_code": ""}
        ],
        "private_rate": 120.0,
    }, headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.get(f"/timesheets/{ts_id}/export",
                    params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Project" in r2.text


def test_owner_downloads_own_receipt(client):
    r = client.post("/timesheets", json={
        "project": "Receipt Project",
        "receipts": {"travel.pdf": "travel receipt content"},
    }, headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.get(f"/timesheets/{ts_id}/receipts",
                    params={"name": "travel.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "travel receipt content" in r2.text


def test_owner_gets_entries(client):
    r = client.post("/timesheets", json={
        "project": "Entry Project",
        "entries": [
            {"description": "Task A", "hours": 2.0, "rate_code": "TE-01", "discount_code": ""}
        ],
    }, headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.get(f"/timesheets/{ts_id}/entries", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["description"] == "Task A"


def test_owner_patches_own_timesheet(client):
    r = client.post("/timesheets", json={"project": "Old Project"},
                    headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.patch(f"/timesheets/{ts_id}", json={"project": "New Project"},
                      headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["project"] == "New Project"


def test_owner_clones_own_timesheet(client):
    r = client.post("/timesheets", json={"project": "Template Project"},
                    headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.post(f"/timesheets/{ts_id}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != ts_id


def test_owner_submits_own_timesheet(client):
    r = client.post("/timesheets", json={"project": "Submit Project"},
                    headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.post(f"/timesheets/{ts_id}/submit", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "submitted"


# --- Admin flows ---

def test_admin_reads_any_timesheet(client):
    r = client.post("/timesheets", json={
        "project": "Confidential Project",
        "internal_notes": "private billing arrangement",
        "private_rate": 500.0,
    }, headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.get(f"/timesheets/{ts_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "private billing arrangement"


# --- Non-admin creating and listing own timesheets ---

def test_non_admin_creates_own_timesheet(client):
    r = client.post("/timesheets", json={"project": "Bob's Project"},
                    headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_timesheets(client):
    client.post("/timesheets", json={"project": "My Engagement"},
                headers=_h("bob"))
    r = client.get("/timesheets", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# --- Collaborator and public-visibility flows ---

def test_collaborator_reads_shared_timesheet(client):
    """A user in the collaborators list can read the timesheet."""
    r = client.post("/timesheets", json={
        "project": "Partner Engagement",
        "internal_notes": "shared with partner",
        "collaborators": ["carol"],
        "visibility": "private",
    }, headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.get(f"/timesheets/{ts_id}", headers=_h("carol"))
    assert r2.status_code == 200
    assert "Partner Engagement" in r2.text


def test_stranger_reads_public_timesheet(client):
    """A timesheet with visibility=public is readable by any authenticated user."""
    r = client.post("/timesheets", json={
        "project": "Open Source Initiative",
        "visibility": "public",
    }, headers=_h("alice"))
    ts_id = r.json()["id"]

    r2 = client.get(f"/timesheets/{ts_id}", headers=_h("mallory"))
    assert r2.status_code == 200
    assert "Open Source Initiative" in r2.text
