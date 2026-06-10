"""Smoke tests — legitimate-flow reference for candidatesvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from candidatesvc.app import app
from candidatesvc import store


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

def test_owner_creates_candidate(client):
    r = client.post("/candidates", json={
        "name": "Alice Smith",
        "position": "Software Engineer",
        "status": "pending",
        "screening_notes": "Strong background in distributed systems",
        "assessments": [
            {"round": "phone_screen", "score": 8, "eval_code": "PS-001"},
        ],
        "documents": {"resume.pdf": "Alice resume content"},
        "interviewer_ids": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Alice Smith"
    assert data["owner_id"] == "alice"
    assert data["status"] == "pending"


def test_owner_reads_own_candidate(client):
    r = client.post("/candidates", json={
        "name": "Alice Smith",
        "screening_notes": "Confidential: salary expectation high",
    }, headers=_h("alice"))
    cid = r.json()["id"]

    r2 = client.get(f"/candidates/{cid}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["screening_notes"] == "Confidential: salary expectation high"


def test_owner_lists_own_candidates(client):
    client.post("/candidates", json={"name": "Candidate A"}, headers=_h("alice"))
    client.post("/candidates", json={"name": "Candidate B"}, headers=_h("alice"))
    r = client.get("/candidates", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_candidate_json(client):
    r = client.post("/candidates", json={
        "name": "Export Candidate",
        "assessments": [{"round": "technical", "score": 7, "eval_code": "TC-X"}],
        "screening_notes": "export test note",
    }, headers=_h("alice"))
    cid = r.json()["id"]

    r2 = client.get(f"/candidates/{cid}/export",
                    params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_candidate_csv(client):
    r = client.post("/candidates", json={
        "name": "CSV Candidate",
        "assessments": [{"round": "technical", "score": 9, "eval_code": "CSV-CC"}],
    }, headers=_h("alice"))
    cid = r.json()["id"]

    r2 = client.get(f"/candidates/{cid}/export",
                    params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Candidate" in r2.text


def test_owner_downloads_own_document(client):
    r = client.post("/candidates", json={
        "name": "Doc Candidate",
        "documents": {"resume.pdf": "Resume content here"},
    }, headers=_h("alice"))
    cid = r.json()["id"]

    r2 = client.get(f"/candidates/{cid}/documents",
                    params={"name": "resume.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "Resume content here" in r2.text


def test_owner_gets_assessments(client):
    r = client.post("/candidates", json={
        "name": "Assess Candidate",
        "assessments": [{"round": "technical", "score": 8, "eval_code": "TC-01"}],
    }, headers=_h("alice"))
    cid = r.json()["id"]

    r2 = client.get(f"/candidates/{cid}/assessments", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["round"] == "technical"


def test_owner_patches_own_candidate(client):
    r = client.post("/candidates", json={"name": "Old Name", "position": "Junior Dev"},
                    headers=_h("alice"))
    cid = r.json()["id"]

    r2 = client.patch(f"/candidates/{cid}", json={"position": "Senior Dev"},
                      headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["position"] == "Senior Dev"


def test_owner_clones_own_candidate(client):
    r = client.post("/candidates", json={"name": "Template Candidate"},
                    headers=_h("alice"))
    cid = r.json()["id"]

    r2 = client.post(f"/candidates/{cid}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != cid


# --- Recruiter flows ---

def test_recruiter_reads_any_candidate(client):
    r = client.post("/candidates", json={
        "name": "Private Candidate",
        "screening_notes": "internal recruiter notes",
    }, headers=_h("alice"))
    cid = r.json()["id"]

    r2 = client.get(f"/candidates/{cid}", headers=_h("recruiter1"))
    assert r2.status_code == 200
    assert r2.json()["screening_notes"] == "internal recruiter notes"


# --- Non-recruiter creating and listing own candidates ---

def test_non_recruiter_creates_own_candidate(client):
    r = client.post("/candidates", json={"name": "Bob Jones", "position": "Designer"},
                    headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_recruiter_lists_candidates(client):
    client.post("/candidates", json={"name": "My Application"},
                headers=_h("bob"))
    r = client.get("/candidates", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1
