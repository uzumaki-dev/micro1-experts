"""Smoke tests — legitimate-flow reference for schedulesvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from schedulesvc.app import app
from schedulesvc import store


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

def test_owner_creates_schedule(client):
    r = client.post("/schedules", json={
        "title": "Week 27 Roster",
        "visibility": "private",
        "internal_notes": "Overtime approved for Mon",
        "pay_rate": 35.50,
        "entries": [
            {"date": "2025-07-07", "hours": 8.0, "rate_code": "STD-001"}
        ],
        "attachments": {"policy.pdf": "HR policy content"},
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Week 27 Roster"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_schedule(client):
    r = client.post("/schedules", json={
        "title": "Private Roster",
        "internal_notes": "Sensitive staffing details",
        "attachments": {"brief.pdf": "brief bytes"},
    }, headers=_h("alice"))
    s_id = r.json()["id"]
    r2 = client.get(f"/schedules/{s_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "Sensitive staffing details"


def test_owner_lists_own_schedules(client):
    client.post("/schedules", json={"title": "Roster A"}, headers=_h("alice"))
    client.post("/schedules", json={"title": "Roster B"}, headers=_h("alice"))
    r = client.get("/schedules", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_searches_own_schedules(client):
    client.post("/schedules", json={"title": "Night Shift Q3"}, headers=_h("alice"))
    r = client.get("/schedules/search", params={"q": "Night"}, headers=_h("alice"))
    assert r.status_code == 200
    assert any(s["title"] == "Night Shift Q3" for s in r.json())


def test_owner_exports_own_schedule_json(client):
    r = client.post("/schedules", json={
        "title": "Export Roster",
        "entries": [
            {"date": "2025-07-01", "hours": 8.0, "rate_code": "EXP-001"}
        ],
        "internal_notes": "export test note",
    }, headers=_h("alice"))
    s_id = r.json()["id"]
    r2 = client.get(f"/schedules/{s_id}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_schedule_csv(client):
    r = client.post("/schedules", json={
        "title": "CSV Roster",
        "entries": [
            {"date": "2025-07-02", "hours": 7.5, "rate_code": "CSV-001"}
        ],
    }, headers=_h("alice"))
    s_id = r.json()["id"]
    r2 = client.get(f"/schedules/{s_id}/export", params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Roster" in r2.text


def test_owner_downloads_own_attachment(client):
    r = client.post("/schedules", json={
        "title": "Attachment Roster",
        "attachments": {"contract.pdf": "PDF content here"},
    }, headers=_h("alice"))
    s_id = r.json()["id"]
    r2 = client.get(f"/schedules/{s_id}/attachments", params={"name": "contract.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "PDF content here" in r2.text


def test_owner_gets_entries(client):
    r = client.post("/schedules", json={
        "title": "Entries Roster",
        "entries": [
            {"date": "2025-07-03", "hours": 6.0, "rate_code": "ENT-001"}
        ],
    }, headers=_h("alice"))
    s_id = r.json()["id"]
    r2 = client.get(f"/schedules/{s_id}/entries", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["rate_code"] == "ENT-001"


def test_owner_patches_own_schedule(client):
    r = client.post("/schedules", json={"title": "Old Title"}, headers=_h("alice"))
    s_id = r.json()["id"]
    r2 = client.patch(f"/schedules/{s_id}", json={"title": "New Title"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["title"] == "New Title"


def test_owner_clones_own_schedule(client):
    r = client.post("/schedules", json={"title": "Template Roster"}, headers=_h("alice"))
    s_id = r.json()["id"]
    r2 = client.post(f"/schedules/{s_id}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != s_id


def test_owner_publishes_own_schedule(client):
    r = client.post("/schedules", json={"title": "Publish Roster"}, headers=_h("alice"))
    s_id = r.json()["id"]
    r2 = client.post(f"/schedules/{s_id}/publish", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "published"


# --- Admin flows ---

def test_admin_reads_any_schedule(client):
    r = client.post("/schedules", json={
        "title": "Confidential Roster",
        "internal_notes": "private staffing notes",
    }, headers=_h("alice"))
    s_id = r.json()["id"]
    r2 = client.get(f"/schedules/{s_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "private staffing notes"


# --- Non-admin creating and listing own schedules ---

def test_non_admin_creates_own_schedule(client):
    r = client.post("/schedules", json={"title": "Bob's Roster"}, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_schedules(client):
    client.post("/schedules", json={"title": "My Roster"}, headers=_h("bob"))
    r = client.get("/schedules", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1
