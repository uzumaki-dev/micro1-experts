"""Smoke tests — legitimate-flow reference for contractsvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from contractsvc.app import app
from contractsvc import store


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

def test_owner_creates_contract(client):
    r = client.post("/contracts", json={
        "title": "Master Services Agreement",
        "status": "draft",
        "counterparty_id": "acme_corp",
        "clauses": [
            {"description": "Monthly retainer", "quantity": 12, "rate_card": "RC-001"}
        ],
        "internal_notes": "Confidential deal terms",
        "documents": {"agreement.pdf": "signed contract content"},
        "collaborators": [],
        "visibility": "private",
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Master Services Agreement"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_contract(client):
    r = client.post("/contracts", json={
        "title": "NDA Agreement",
        "internal_notes": "Sensitive terms",
        "documents": {"nda.pdf": "nda content"},
    }, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.get(f"/contracts/{cid}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "Sensitive terms"


def test_owner_lists_own_contracts(client):
    client.post("/contracts", json={"title": "Contract A"}, headers=_h("alice"))
    client.post("/contracts", json={"title": "Contract B"}, headers=_h("alice"))
    r = client.get("/contracts", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_owner_exports_own_contract_json(client):
    r = client.post("/contracts", json={
        "title": "Export Contract",
        "clauses": [{"description": "Dev work", "quantity": 1, "rate_card": "RC-X"}],
        "internal_notes": "export test note",
    }, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.get(f"/contracts/{cid}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_own_contract_pdf(client):
    r = client.post("/contracts", json={
        "title": "PDF Contract",
        "clauses": [{"description": "Consulting", "quantity": 3, "rate_card": "RC-PDF"}],
        "internal_notes": "pdf test note",
    }, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.get(f"/contracts/{cid}/export", params={"format": "pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "PDF Contract" in r2.text


def test_owner_downloads_own_document(client):
    r = client.post("/contracts", json={
        "title": "Doc Contract",
        "documents": {"terms.pdf": "contract terms content"},
    }, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.get(f"/contracts/{cid}/documents", params={"name": "terms.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "contract terms content" in r2.text


def test_owner_gets_clauses(client):
    r = client.post("/contracts", json={
        "title": "Clause Contract",
        "clauses": [
            {"description": "Phase 1", "quantity": 1, "rate_card": "RC-P1"}
        ],
    }, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.get(f"/contracts/{cid}/clauses", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["description"] == "Phase 1"


def test_owner_patches_own_contract(client):
    r = client.post("/contracts", json={"title": "Old Title"}, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.patch(f"/contracts/{cid}", json={"title": "New Title"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["title"] == "New Title"


def test_owner_duplicates_own_contract(client):
    r = client.post("/contracts", json={"title": "Template Contract"}, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.post(f"/contracts/{cid}/duplicate", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != cid


def test_owner_signs_own_contract(client):
    r = client.post("/contracts", json={"title": "Sign Contract"}, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.post(f"/contracts/{cid}/sign", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "signed"


def test_owner_shares_own_contract(client):
    r = client.post("/contracts", json={"title": "Share Contract"}, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.post(f"/contracts/{cid}/share", params={"user_id": "bob"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "bob" in r2.json()["collaborators"]


# --- Admin flows ---

def test_admin_reads_any_contract(client):
    r = client.post("/contracts", json={
        "title": "Confidential Contract",
        "internal_notes": "private deal notes",
    }, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.get(f"/contracts/{cid}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["internal_notes"] == "private deal notes"


# --- Non-admin creating and listing own contracts ---

def test_non_admin_creates_own_contract(client):
    r = client.post("/contracts", json={"title": "Bob Contract"}, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_contracts(client):
    client.post("/contracts", json={"title": "My Contract"}, headers=_h("bob"))
    r = client.get("/contracts", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# --- Collaborator and public-visibility flows ---

def test_counterparty_reads_shared_contract(client):
    """A user in the collaborators list can read the contract."""
    r = client.post("/contracts", json={
        "title": "Partner Contract",
        "internal_notes": "shared with partner",
        "collaborators": ["carol"],
        "visibility": "private",
    }, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.get(f"/contracts/{cid}", headers=_h("carol"))
    assert r2.status_code == 200
    assert "Partner Contract" in r2.text


def test_stranger_reads_public_contract(client):
    """A contract with visibility=public is readable by any authenticated user."""
    r = client.post("/contracts", json={
        "title": "Public Framework Agreement",
        "visibility": "public",
    }, headers=_h("alice"))
    cid = r.json()["id"]
    r2 = client.get(f"/contracts/{cid}", headers=_h("mallory"))
    assert r2.status_code == 200
    assert "Public Framework Agreement" in r2.text
