"""Local oracle dev harness — run with pytest from the environment/ directory.

This file mirrors the oracle in solution/solve.sh and is used to validate
the test suite locally before submission. Not part of the graded artifact.
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


SENTINEL_SUMMARY = "PRIV_SENTINEL_a3f7b291"
SENTINEL_SALARY = "SALARY_SENTINEL_d4e8c012"
SENTINEL_DOC = "DOC_SENTINEL_b5f2a883"


@pytest.fixture
def alice_profile(client):
    r = client.post("/profiles", json={
        "display_name": "Alice Smith",
        "headline": "Senior Engineer",
        "private_summary": SENTINEL_SUMMARY,
        "experience": [
            {
                "title": "Senior Engineer",
                "company": "Acme Corp",
                "years": 3.0,
                "salary_band": SENTINEL_SALARY,
            }
        ],
        "documents": {"portfolio.pdf": SENTINEL_DOC},
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    return r.json()


def test_get_profile_hides_private_summary_from_stranger(client, alice_profile):
    r = client.get(f"/profiles/{alice_profile['id']}", headers=_h("mallory"))
    assert SENTINEL_SUMMARY not in r.text


def test_list_profiles_hides_private_summary_from_stranger(client, alice_profile):
    r = client.get("/profiles", headers=_h("mallory"))
    assert SENTINEL_SUMMARY not in r.text


def test_search_profiles_hides_private_summary_from_stranger(client, alice_profile):
    r = client.get("/profiles/search", params={"q": "Alice"}, headers=_h("mallory"))
    assert SENTINEL_SUMMARY not in r.text


def test_get_experience_hides_salary_band_from_stranger(client, alice_profile):
    r = client.get(f"/profiles/{alice_profile['id']}/experience", headers=_h("mallory"))
    assert SENTINEL_SALARY not in r.text


def test_export_json_hides_private_summary_from_stranger(client, alice_profile):
    r = client.get(f"/profiles/{alice_profile['id']}/export",
                   params={"format": "json"}, headers=_h("mallory"))
    assert SENTINEL_SUMMARY not in r.text


def test_export_csv_hides_private_data_from_stranger(client, alice_profile):
    r = client.get(f"/profiles/{alice_profile['id']}/export",
                   params={"format": "csv"}, headers=_h("mallory"))
    assert SENTINEL_SUMMARY not in r.text
    assert SENTINEL_SALARY not in r.text


def test_get_document_hides_content_from_stranger(client, alice_profile):
    r = client.get(f"/profiles/{alice_profile['id']}/documents",
                   params={"name": "portfolio.pdf"}, headers=_h("mallory"))
    assert SENTINEL_DOC not in r.text


def test_path_traversal_in_documents_does_not_expose_sentinel(client, alice_profile):
    r = client.get(f"/profiles/{alice_profile['id']}/documents",
                   params={"name": "../portfolio.pdf"}, headers=_h("mallory"))
    assert r.status_code in (400, 403, 404) or SENTINEL_DOC not in r.text


def test_fork_then_patch_does_not_launder_private_summary(client, alice_profile):
    fork_r = client.post(f"/profiles/{alice_profile['id']}/fork", headers=_h("mallory"))
    assert fork_r.status_code == 201
    fork_id = fork_r.json()["id"]
    assert SENTINEL_SUMMARY not in fork_r.text
    patch_r = client.patch(f"/profiles/{fork_id}",
                           json={"display_name": "Mallory Profile"}, headers=_h("mallory"))
    assert SENTINEL_SUMMARY not in patch_r.text


def test_stranger_can_access_public_profile(client):
    r = client.post("/profiles", json={
        "display_name": "Public Speaker",
        "visibility": "public",
    }, headers=_h("alice"))
    assert r.status_code == 201
    profile_id = r.json()["id"]
    r2 = client.get(f"/profiles/{profile_id}", headers=_h("mallory"))
    assert r2.status_code == 200
    assert "Public Speaker" in r2.json()["display_name"]


def test_fork_then_export_does_not_launder_private_data(client, alice_profile):
    fork_r = client.post(f"/profiles/{alice_profile['id']}/fork", headers=_h("mallory"))
    assert fork_r.status_code == 201
    fork_id = fork_r.json()["id"]
    assert SENTINEL_SUMMARY not in fork_r.text
    exp_r = client.get(f"/profiles/{fork_id}/export",
                       params={"format": "json"}, headers=_h("mallory"))
    assert SENTINEL_SUMMARY not in exp_r.text
    assert SENTINEL_SALARY not in exp_r.text


def test_owner_can_still_read_own_private_summary(client, alice_profile):
    r = client.get(f"/profiles/{alice_profile['id']}", headers=_h("alice"))
    assert r.status_code == 200
    assert SENTINEL_SUMMARY in r.json()["private_summary"]


def test_admin_can_still_read_private_summary(client, alice_profile):
    r = client.get(f"/profiles/{alice_profile['id']}", headers=_h("admin"))
    assert r.status_code == 200
    assert SENTINEL_SUMMARY in r.json()["private_summary"]


def test_non_owner_can_create_and_list_own_profile(client):
    create_r = client.post("/profiles", json={"display_name": "Bob Jones"}, headers=_h("bob"))
    assert create_r.status_code == 201
    profile_id = create_r.json()["id"]
    list_r = client.get("/profiles", headers=_h("bob"))
    assert list_r.status_code == 200
    ids = [p["id"] for p in list_r.json()]
    assert profile_id in ids
