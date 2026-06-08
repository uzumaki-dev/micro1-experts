"""Smoke tests — legitimate-flow reference for leasesvc.

These tests document normal API behavior under intended use. They are
intentionally silent about security checks; that is the agent's job.
"""
import pytest
from fastapi.testclient import TestClient

from leasesvc.app import app
from leasesvc import store


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

def test_owner_creates_lease(client):
    r = client.post("/leases", json={
        "tenant_name": "Acme Corp",
        "property_address": "123 Main St",
        "visibility": "private",
        "private_notes": "Tenant has strong payment history",
        "clauses": [
            {"description": "Monthly rent clause", "clause_code": "RENT-001"}
        ],
        "attachments": {"signed_lease.pdf": "PDF content here"},
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["tenant_name"] == "Acme Corp"
    assert data["owner_id"] == "alice"
    assert data["status"] == "draft"


def test_owner_reads_own_lease(client):
    r = client.post("/leases", json={
        "tenant_name": "Private Tenant",
        "private_notes": "Sensitive landlord notes",
    }, headers=_h("alice"))
    lid = r.json()["id"]
    r2 = client.get(f"/leases/{lid}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["private_notes"] == "Sensitive landlord notes"


def test_owner_lists_own_leases(client):
    client.post("/leases", json={"tenant_name": "Tenant A"}, headers=_h("alice"))
    client.post("/leases", json={"tenant_name": "Tenant B"}, headers=_h("alice"))
    r = client.get("/leases", headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_owner_searches_own_leases(client):
    client.post("/leases", json={"tenant_name": "Sunrise Properties Ltd"}, headers=_h("alice"))
    r = client.get("/leases/search", params={"q": "Sunrise"}, headers=_h("alice"))
    assert r.status_code == 200
    assert any(l["tenant_name"] == "Sunrise Properties Ltd" for l in r.json())


def test_owner_gets_clauses(client):
    r = client.post("/leases", json={
        "tenant_name": "Clause Tenant",
        "clauses": [
            {"description": "Late fee clause", "clause_code": "FEE-001"}
        ],
    }, headers=_h("alice"))
    lid = r.json()["id"]
    r2 = client.get(f"/leases/{lid}/clauses", headers=_h("alice"))
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["clause_code"] == "FEE-001"


def test_owner_exports_json(client):
    r = client.post("/leases", json={
        "tenant_name": "Export Tenant",
        "private_notes": "export note",
        "clauses": [{"description": "Rent", "clause_code": "EXP-001"}],
    }, headers=_h("alice"))
    lid = r.json()["id"]
    r2 = client.get(f"/leases/{lid}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200


def test_owner_exports_csv(client):
    r = client.post("/leases", json={
        "tenant_name": "CSV Tenant",
        "clauses": [{"description": "Maintenance", "clause_code": "CSV-001"}],
    }, headers=_h("alice"))
    lid = r.json()["id"]
    r2 = client.get(f"/leases/{lid}/export", params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "CSV Tenant" in r2.text


def test_owner_downloads_document(client):
    r = client.post("/leases", json={
        "tenant_name": "Doc Tenant",
        "attachments": {"agreement.pdf": "PDF bytes here"},
    }, headers=_h("alice"))
    lid = r.json()["id"]
    r2 = client.get(f"/leases/{lid}/documents", params={"name": "agreement.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "PDF bytes here" in r2.text


def test_owner_patches_lease(client):
    r = client.post("/leases", json={"tenant_name": "Old Tenant"}, headers=_h("alice"))
    lid = r.json()["id"]
    r2 = client.patch(f"/leases/{lid}", json={"tenant_name": "New Tenant"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["tenant_name"] == "New Tenant"


def test_owner_clones_own_lease(client):
    r = client.post("/leases", json={"tenant_name": "Template Tenant"}, headers=_h("alice"))
    lid = r.json()["id"]
    r2 = client.post(f"/leases/{lid}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    clone = r2.json()
    assert clone["owner_id"] == "alice"
    assert clone["id"] != lid
    assert clone["tenant_name"] == "Template Tenant"


def test_owner_renews_own_lease(client):
    r = client.post("/leases", json={"tenant_name": "Renew Tenant"}, headers=_h("alice"))
    lid = r.json()["id"]
    r2 = client.post(f"/leases/{lid}/renew", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "active"


# --- Admin flows ---

def test_admin_reads_any_lease(client):
    r = client.post("/leases", json={
        "tenant_name": "Confidential Tenant",
        "private_notes": "private landlord notes",
    }, headers=_h("alice"))
    lid = r.json()["id"]
    r2 = client.get(f"/leases/{lid}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["private_notes"] == "private landlord notes"


# --- Non-admin basic flows ---

def test_non_admin_creates_own_lease(client):
    r = client.post("/leases", json={"tenant_name": "Bob's Tenant"}, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["owner_id"] == "bob"


def test_non_admin_lists_leases(client):
    client.post("/leases", json={"tenant_name": "My Tenant"}, headers=_h("bob"))
    r = client.get("/leases", headers=_h("bob"))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_nonexistent_lease_returns_404(client):
    r = client.get("/leases/nonexistent-id-12345", headers=_h("alice"))
    assert r.status_code == 404
