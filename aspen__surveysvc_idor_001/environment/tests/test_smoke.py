"""Smoke tests — legitimate-flow reference for surveysvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from surveysvc.app import app
from surveysvc import store


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

def test_owner_creates_survey(client):
    r = client.post("/surveys", json={
        "title": "Q3 Customer Satisfaction",
        "visibility": "private",
        "internal_notes": "Analyst: flag low NPS responses for follow-up",
        "responses": [
            {"question_id": "q1", "answer": "Very satisfied", "score_code": "NPS-9"}
        ],
        "attachments": {"summary.pdf": "PDF content here"},
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Q3 Customer Satisfaction"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_survey(client):
    r = client.post("/surveys", json={
        "title": "Private Survey",
        "internal_notes": "Sensitive analyst notes",
    }, headers=_h("alice"))
    sid = r.json()["id"]
    r2 = client.get(f"/surveys/{sid}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "Sensitive analyst notes"


def test_owner_lists_own_surveys(client):
    client.post("/surveys", json={"title": "Survey A"}, headers=_h("alice"))
    client.post("/surveys", json={"title": "Survey B"}, headers=_h("alice"))
    r = client.get("/surveys", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_owner_searches_own_surveys(client):
    client.post("/surveys", json={"title": "Exit Interview Q3"}, headers=_h("alice"))
    r = client.get("/surveys/search", params={"q": "Exit"}, headers=_h("alice"))
    assert r.status_code == 200
    assert any(s["title"] == "Exit Interview Q3" for s in r.json())


def test_owner_gets_responses(client):
    r = client.post("/surveys", json={
        "title": "Responses Survey",
        "responses": [
            {"question_id": "q1", "answer": "Good", "score_code": "SC-001"}
        ],
    }, headers=_h("alice"))
    sid = r.json()["id"]
    r2 = client.get(f"/surveys/{sid}/responses", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["score_code"] == "SC-001"


def test_owner_exports_json(client):
    r = client.post("/surveys", json={
        "title": "Export Survey",
        "internal_notes": "export note",
        "responses": [
            {"question_id": "q1", "answer": "OK", "score_code": "EXP-001"}
        ],
    }, headers=_h("alice"))
    sid = r.json()["id"]
    r2 = client.get(f"/surveys/{sid}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_csv(client):
    r = client.post("/surveys", json={
        "title": "CSV Survey",
        "responses": [
            {"question_id": "q2", "answer": "Fine", "score_code": "CSV-001"}
        ],
    }, headers=_h("alice"))
    sid = r.json()["id"]
    r2 = client.get(f"/surveys/{sid}/export", params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Survey" in r2.text


def test_owner_downloads_attachment(client):
    r = client.post("/surveys", json={
        "title": "Attachment Survey",
        "attachments": {"contract.pdf": "PDF bytes here"},
    }, headers=_h("alice"))
    sid = r.json()["id"]
    r2 = client.get(f"/surveys/{sid}/attachments", params={"name": "contract.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "PDF bytes here" in r2.text


def test_owner_patches_survey(client):
    r = client.post("/surveys", json={"title": "Old Title"}, headers=_h("alice"))
    sid = r.json()["id"]
    r2 = client.patch(f"/surveys/{sid}", json={"title": "New Title"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["title"] == "New Title"


def test_owner_clones_own_survey(client):
    r = client.post("/surveys", json={"title": "Template Survey"}, headers=_h("alice"))
    sid = r.json()["id"]
    r2 = client.post(f"/surveys/{sid}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != sid
    assert clone["title"] == "Template Survey"


def test_owner_publishes_own_survey(client):
    r = client.post("/surveys", json={"title": "Publish Survey"}, headers=_h("alice"))
    sid = r.json()["id"]
    r2 = client.post(f"/surveys/{sid}/publish", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "published"


# --- Admin flows ---

def test_admin_reads_any_survey(client):
    r = client.post("/surveys", json={
        "title": "Confidential Survey",
        "internal_notes": "private analyst notes",
    }, headers=_h("alice"))
    sid = r.json()["id"]
    r2 = client.get(f"/surveys/{sid}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "private analyst notes"


# --- Non-admin basic flows ---

def test_non_admin_creates_own_survey(client):
    r = client.post("/surveys", json={"title": "Bob's Survey"}, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_surveys(client):
    client.post("/surveys", json={"title": "My Survey"}, headers=_h("bob"))
    r = client.get("/surveys", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_nonexistent_survey_returns_404(client):
    r = client.get("/surveys/nonexistent-id-12345", headers=_h("alice"))
    assert r.status_code == 404
