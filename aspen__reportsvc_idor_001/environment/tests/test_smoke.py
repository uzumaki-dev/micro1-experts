"""Smoke tests — legitimate-flow reference for reportsvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from reportsvc.app import app
from reportsvc import store


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

def test_owner_creates_report(client):
    r = client.post("/reports", json={
        "title": "Q1 Revenue Analysis",
        "status": "draft",
        "data_points": [
            {
                "label": "Total Revenue",
                "value": 125000.0,
                "metric_code": "REV-Q1",
            }
        ],
        "confidential_notes": "Preliminary figures pending audit",
        "attachments": {"summary.pdf": "executive summary content"},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Q1 Revenue Analysis"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_report(client):
    r = client.post("/reports", json={
        "title": "Market Share Report",
        "confidential_notes": "Do not share with competitors",
        "attachments": {"data.csv": "raw data bytes"},
    }, headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.get(f"/reports/{rpt_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["confidential_notes"] == "Do not share with competitors"


def test_owner_lists_own_reports(client):
    client.post("/reports", json={"title": "Report A"}, headers=_h("alice"))
    client.post("/reports", json={"title": "Report B"}, headers=_h("alice"))
    r = client.get("/reports", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_report_json(client):
    r = client.post("/reports", json={
        "title": "Export Test",
        "data_points": [
            {"label": "KPI", "value": 99.5, "metric_code": "KPI-01"}
        ],
        "confidential_notes": "export note",
    }, headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.get(f"/reports/{rpt_id}/export",
                    params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_report_csv(client):
    r = client.post("/reports", json={
        "title": "CSV Export",
        "data_points": [
            {"label": "Units", "value": 500.0, "metric_code": "UNIT-CSV"}
        ],
    }, headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.get(f"/reports/{rpt_id}/export",
                    params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Export" in r2.text


def test_owner_downloads_own_attachment(client):
    r = client.post("/reports", json={
        "title": "Attach Test",
        "attachments": {"findings.pdf": "findings content here"},
    }, headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.get(f"/reports/{rpt_id}/attachments",
                    params={"name": "findings.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "findings content here" in r2.text


def test_owner_gets_data_points(client):
    r = client.post("/reports", json={
        "title": "Data Points Test",
        "data_points": [
            {"label": "Revenue", "value": 50000.0, "metric_code": "DP-01"}
        ],
    }, headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.get(f"/reports/{rpt_id}/data-points", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["label"] == "Revenue"


def test_owner_patches_own_report(client):
    r = client.post("/reports", json={"title": "Old Title"},
                    headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.patch(f"/reports/{rpt_id}", json={"title": "New Title"},
                      headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["title"] == "New Title"


def test_owner_forks_own_report(client):
    r = client.post("/reports", json={"title": "Template Report"},
                    headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.post(f"/reports/{rpt_id}/fork", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != rpt_id


def test_owner_publishes_own_report(client):
    r = client.post("/reports", json={"title": "Public Report"},
                    headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.post(f"/reports/{rpt_id}/publish", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "published"
    assert r2.json()["visibility"] == "public"


# --- Admin flows ---

def test_admin_reads_any_report(client):
    r = client.post("/reports", json={
        "title": "Confidential Report",
        "confidential_notes": "board-level strategy notes",
    }, headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.get(f"/reports/{rpt_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["confidential_notes"] == "board-level strategy notes"


# --- Non-admin creating and listing own reports ---

def test_non_admin_creates_own_report(client):
    r = client.post("/reports", json={"title": "Bob's Analysis"},
                    headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_reports(client):
    client.post("/reports", json={"title": "My First Report"},
                headers=_h("bob"))
    r = client.get("/reports", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# --- Collaborator and public-visibility flows ---

def test_collaborator_reads_shared_report(client):
    r = client.post("/reports", json={
        "title": "Partner Analysis",
        "confidential_notes": "shared with partner",
        "collaborators": ["carol"],
        "visibility": "private",
    }, headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.get(f"/reports/{rpt_id}", headers=_h("carol"))
    assert r2.status_code == 200
    assert "Partner Analysis" in r2.text


def test_stranger_reads_public_report(client):
    r = client.post("/reports", json={
        "title": "Industry Benchmark 2025",
        "visibility": "public",
    }, headers=_h("alice"))
    rpt_id = r.json()["id"]

    r2 = client.get(f"/reports/{rpt_id}", headers=_h("mallory"))
    assert r2.status_code == 200
    assert "Industry Benchmark 2025" in r2.text
