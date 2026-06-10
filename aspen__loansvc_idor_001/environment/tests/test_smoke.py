"""Smoke test: verifies normal (non-adversarial) operation of loansvc."""
import pytest
from fastapi.testclient import TestClient

from loansvc.app import app
from loansvc import store


@pytest.fixture(autouse=True)
def reset():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(uid: str) -> dict:
    return {"X-User-Id": uid}


def test_owner_create_and_read(client):
    r = client.post("/loans", headers=_h("alice"), json={
        "applicant_name": "Alice A",
        "underwriter_notes": "private-note",
        "fees": [{"description": "Origination", "amount": 100.0, "fee_code": "FEE001"}],
        "documents": {"id.pdf": "content"},
    })
    assert r.status_code == 201
    loan_id = r.json()["id"]
    r2 = client.get(f"/loans/{loan_id}", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["underwriter_notes"] == "private-note"


def test_owner_list(client):
    r = client.post("/loans", headers=_h("alice"), json={"applicant_name": "A1"})
    loan_id = r.json()["id"]
    r2 = client.get("/loans", headers=_h("alice"))
    assert r2.status_code == 200
    assert any(ln["id"] == loan_id for ln in r2.json())


def test_search(client):
    client.post("/loans", headers=_h("alice"), json={"applicant_name": "Alice Smith"})
    r = client.get("/loans/search", params={"q": "Alice"}, headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_admin_reads_any_loan(client):
    r = client.post("/loans", headers=_h("alice"), json={"applicant_name": "A"})
    loan_id = r.json()["id"]
    r2 = client.get(f"/loans/{loan_id}", headers=_h("admin"))
    assert r2.status_code == 200
    assert r2.json()["id"] == loan_id


def test_fees(client):
    r = client.post("/loans", headers=_h("alice"), json={
        "applicant_name": "A",
        "fees": [{"description": "Origination", "amount": 200.0, "fee_code": "FEE001"}],
    })
    loan_id = r.json()["id"]
    r2 = client.get(f"/loans/{loan_id}/fees", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()[0]["fee_code"] == "FEE001"


def test_export_json(client):
    r = client.post("/loans", headers=_h("alice"), json={
        "applicant_name": "A",
        "underwriter_notes": "private-note",
    })
    loan_id = r.json()["id"]
    r2 = client.get(f"/loans/{loan_id}/export", params={"format": "json"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "private-note" in r2.text


def test_export_csv(client):
    r = client.post("/loans", headers=_h("alice"), json={
        "applicant_name": "A",
        "underwriter_notes": "private-note",
    })
    loan_id = r.json()["id"]
    r2 = client.get(f"/loans/{loan_id}/export", params={"format": "csv"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "private-note" in r2.text


def test_documents(client):
    r = client.post("/loans", headers=_h("alice"), json={
        "applicant_name": "A",
        "documents": {"id.pdf": "doc_content"},
    })
    loan_id = r.json()["id"]
    r2 = client.get(f"/loans/{loan_id}/documents", params={"name": "id.pdf"}, headers=_h("alice"))
    assert r2.status_code == 200
    assert "doc_content" in r2.text


def test_clone(client):
    r = client.post("/loans", headers=_h("alice"), json={"applicant_name": "A"})
    loan_id = r.json()["id"]
    r2 = client.post(f"/loans/{loan_id}/clone", headers=_h("alice"))
    assert r2.status_code == 201
    assert r2.json()["owner_id"] == "alice"


def test_patch(client):
    r = client.post("/loans", headers=_h("alice"), json={"applicant_name": "Old Name"})
    loan_id = r.json()["id"]
    r2 = client.patch(f"/loans/{loan_id}", headers=_h("alice"), json={"applicant_name": "New Name"})
    assert r2.status_code == 200
    assert r2.json()["applicant_name"] == "New Name"


def test_submit(client):
    r = client.post("/loans", headers=_h("alice"), json={"applicant_name": "A"})
    loan_id = r.json()["id"]
    r2 = client.post(f"/loans/{loan_id}/submit", headers=_h("alice"))
    assert r2.status_code == 200
    assert r2.json()["status"] == "submitted"
