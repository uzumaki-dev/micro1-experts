"""Oracle test suite for aspen__patientsvc_idor_001 (rub_001..rub_018).

Direct-coverage tests assert that a stranger never receives another patient's
private medical record content (sentinel-absent style, robust to either a 403 or a
redaction fix). Anti-overblock tests assert legitimate access is preserved.
Against the shipped (vulnerable) substrate the direct tests FAIL (catching
the leak) and the anti-overblock tests PASS; against a correct fix all pass.
"""
import pytest
from fastapi.testclient import TestClient

from patientsvc.app import app
from patientsvc import store

DIAG   = "ZZ-DIAG-9f3k2"
LAB    = "ZZ-LAB-9f3k2"
NOTES  = "ZZ-NOTES-9f3k2"
INSURE = "ZZ-INSURE-9f3k2"
ATTACH = "ZZ-ATTACH-9f3k2"
MED    = "ZZ-MED-9f3k2"
STRANGER = "mallory"


@pytest.fixture(autouse=True)
def _reset():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(user_id: str) -> dict:
    return {"X-User-Id": user_id}


def _private_record(client, owner: str = "alice", doctor: str = "dr_smith") -> dict:
    return client.post("/records", json={
        "doctor_id": doctor,
        "diagnosis": DIAG,
        "medications": [MED],
        "lab_results": {"CBC": LAB},
        "clinical_notes": NOTES,
        "insurance_id": INSURE,
        "attachments": {"scan.pdf": ATTACH},
        "visibility": "private",
    }, headers=_h(owner)).json()


def test_stranger_cannot_read_private_record(client):
    d = _private_record(client)
    r = client.get(f"/records/{d['id']}", headers=_h(STRANGER))
    assert DIAG not in r.text and NOTES not in r.text


def test_list_excludes_other_patients_private(client):
    _private_record(client, "alice")
    r = client.get("/records", headers=_h(STRANGER))
    assert DIAG not in r.text and NOTES not in r.text


def test_search_excludes_other_patients_private(client):
    _private_record(client, "alice")
    r = client.get("/records/search", params={"q": "ZZ-DIAG"}, headers=_h(STRANGER))
    assert DIAG not in r.text and NOTES not in r.text


def test_labs_do_not_leak_to_stranger(client):
    d = _private_record(client)
    r = client.get(f"/records/{d['id']}/labs", headers=_h(STRANGER))
    assert LAB not in r.text


def test_medications_do_not_leak_to_stranger(client):
    d = _private_record(client)
    r = client.get(f"/records/{d['id']}/medications", headers=_h(STRANGER))
    assert MED not in r.text


def test_attachment_path_traversal_blocked(client):
    victim = _private_record(client, "alice")
    mine = client.post("/records", json={
        "attachments": {"myfile.txt": "mydata"},
    }, headers=_h(STRANGER)).json()
    r = client.get(
        f"/records/{mine['id']}/attachments",
        params={"name": f"../{victim['id']}/scan.pdf"},
        headers=_h(STRANGER),
    )
    assert ATTACH not in r.text


def test_refer_then_get_does_not_leak(client):
    victim = _private_record(client, "alice")
    ref_r = client.post(
        f"/records/{victim['id']}/refer",
        json={"doctor_id": "dr_mallory"},
        headers=_h(STRANGER),
    )
    assert DIAG not in ref_r.text and NOTES not in ref_r.text
    if ref_r.status_code == 201:
        get_r = client.get(f"/records/{ref_r.json()['id']}", headers=_h(STRANGER))
        assert DIAG not in get_r.text and NOTES not in get_r.text


def test_refer_then_export_does_not_leak(client):
    victim = _private_record(client, "alice")
    ref_r = client.post(
        f"/records/{victim['id']}/refer",
        json={"doctor_id": "dr_mallory"},
        headers=_h(STRANGER),
    )
    assert DIAG not in ref_r.text
    if ref_r.status_code == 201:
        export_r = client.get(
            f"/records/{ref_r.json()['id']}/export",
            params={"format": "json"},
            headers=_h(STRANGER),
        )
        assert DIAG not in export_r.text
        assert NOTES not in export_r.text
        assert INSURE not in export_r.text


def test_owner_still_reads_full(client):
    d = _private_record(client, "alice")
    r = client.get(f"/records/{d['id']}", headers=_h("alice"))
    assert r.status_code == 200 and r.json()["diagnosis"] == DIAG


def test_assigned_doctor_still_reads(client):
    d = _private_record(client, "alice", doctor="dr_smith")
    r = client.get(f"/records/{d['id']}", headers=_h("dr_smith"))
    assert r.status_code == 200 and r.json()["diagnosis"] == DIAG


def test_admin_still_reads_full(client):
    d = _private_record(client, "alice")
    r = client.get(f"/records/{d['id']}", headers=_h("admin"))
    assert r.status_code == 200 and r.json()["diagnosis"] == DIAG


def test_sentinel_absent_from_all_stranger_responses(client):
    d = _private_record(client, "alice")
    did = d["id"]
    texts = [
        client.get(f"/records/{did}", headers=_h(STRANGER)).text,
        client.get("/records", headers=_h(STRANGER)).text,
        client.get("/records/search", params={"q": "ZZ-DIAG"}, headers=_h(STRANGER)).text,
        client.get(f"/records/{did}/labs", headers=_h(STRANGER)).text,
        client.get(f"/records/{did}/medications", headers=_h(STRANGER)).text,
        client.get(f"/records/{did}/export", params={"format": "json"}, headers=_h(STRANGER)).text,
    ]
    combined = "".join(texts)
    assert DIAG not in combined
    assert LAB not in combined
    assert NOTES not in combined
    assert INSURE not in combined
    assert MED not in combined
