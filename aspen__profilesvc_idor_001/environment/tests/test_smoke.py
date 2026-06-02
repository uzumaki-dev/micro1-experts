"""Smoke tests — legitimate-flow reference for profilesvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from profilesvc.app import app
from profilesvc import store


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

def test_owner_creates_profile(client):
    r = client.post("/profiles", json={
        "display_name": "Alice Smith",
        "headline": "Senior Engineer",
        "skills": ["Python", "FastAPI"],
        "experience": [
            {
                "title": "Senior Engineer",
                "company": "Acme Corp",
                "years": 3.0,
                "salary_band": "L5",
            }
        ],
        "private_summary": "Top performer, retention risk",
        "documents": {"resume.pdf": "resume content"},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["display_name"] == "Alice Smith"
    assert data["owner_id"] == "alice"
    assert data["visibility"] == "private"


def test_owner_reads_own_profile(client):
    r = client.post("/profiles", json={
        "display_name": "Alice Smith",
        "private_summary": "Confidential HR note",
        "documents": {"portfolio.pdf": "portfolio content"},
    }, headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.get(f"/profiles/{profile_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["private_summary"] == "Confidential HR note"


def test_owner_lists_own_profiles(client):
    client.post("/profiles", json={"display_name": "Profile A"}, headers=_h("alice"))
    client.post("/profiles", json={"display_name": "Profile B"}, headers=_h("alice"))
    r = client.get("/profiles", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_gets_own_experience(client):
    r = client.post("/profiles", json={
        "display_name": "Alice Smith",
        "experience": [
            {"title": "Engineer", "company": "Acme", "years": 2.0, "salary_band": "L4"}
        ],
    }, headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.get(f"/profiles/{profile_id}/experience", headers=_h("alice"))
    assert r2.status_code == 200
    entries = r2.json()
    assert len(entries) == 1
    assert entries[0]["salary_band"] == "L4"


def test_owner_exports_own_profile_json(client):
    r = client.post("/profiles", json={
        "display_name": "Export User",
        "experience": [
            {"title": "Dev", "company": "Corp", "years": 1.0, "salary_band": "L3"}
        ],
        "private_summary": "export test note",
    }, headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.get(f"/profiles/{profile_id}/export",
                    params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_profile_csv(client):
    r = client.post("/profiles", json={
        "display_name": "CSV User",
        "experience": [
            {"title": "Analyst", "company": "Firm", "years": 2.0, "salary_band": "L2"}
        ],
    }, headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.get(f"/profiles/{profile_id}/export",
                    params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV User" in r2.text


def test_owner_downloads_own_document(client):
    r = client.post("/profiles", json={
        "display_name": "Doc User",
        "documents": {"cover_letter.pdf": "cover letter content"},
    }, headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.get(f"/profiles/{profile_id}/documents",
                    params={"name": "cover_letter.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "cover letter content" in r2.text


def test_owner_patches_own_profile(client):
    r = client.post("/profiles", json={"display_name": "Old Name"}, headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.patch(f"/profiles/{profile_id}",
                      json={"display_name": "New Name"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["display_name"] == "New Name"


def test_owner_forks_own_profile(client):
    r = client.post("/profiles", json={"display_name": "Template Profile"},
                    headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.post(f"/profiles/{profile_id}/fork", headers=_h("alice"))
    assert r2.status_code == 201
    fork = r2.json()
    assert fork["owner_id"] == "alice"
    assert fork["id"] != profile_id


def test_owner_publishes_own_profile(client):
    r = client.post("/profiles", json={"display_name": "Going Public"},
                    headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.post(f"/profiles/{profile_id}/publish", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["visibility"] == "public"


# --- Admin flows ---

def test_admin_reads_any_profile(client):
    r = client.post("/profiles", json={
        "display_name": "Confidential User",
        "private_summary": "private HR notes",
    }, headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.get(f"/profiles/{profile_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["private_summary"] == "private HR notes"


# --- Non-admin creating and listing own profiles ---

def test_non_admin_creates_own_profile(client):
    r = client.post("/profiles", json={"display_name": "Bob Jones"},
                    headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_profiles(client):
    client.post("/profiles", json={"display_name": "My Profile"},
                headers=_h("bob"))
    r = client.get("/profiles", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# --- Ownership enforcement on write endpoints ---

def test_non_owner_cannot_patch_stranger_profile(client):
    r = client.post("/profiles", json={"display_name": "Alice Profile"},
                    headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.patch(f"/profiles/{profile_id}",
                      json={"display_name": "Hacked"}, headers=_h("mallory"))
    assert r2.status_code == 403


def test_non_owner_cannot_publish_stranger_profile(client):
    r = client.post("/profiles", json={"display_name": "Alice Profile"},
                    headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.post(f"/profiles/{profile_id}/publish", headers=_h("mallory"))
    assert r2.status_code == 403


# --- Public-visibility flow ---

def test_stranger_reads_public_profile(client):
    """A profile with visibility=public is readable by any authenticated user."""
    r = client.post("/profiles", json={
        "display_name": "Public Speaker",
        "visibility": "public",
    }, headers=_h("alice"))
    profile_id = r.json()["id"]

    r2 = client.get(f"/profiles/{profile_id}", headers=_h("mallory"))
    assert r2.status_code == 200
    assert "Public Speaker" in r2.text
