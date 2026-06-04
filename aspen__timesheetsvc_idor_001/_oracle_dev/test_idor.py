"""Oracle test suite for aspen__timesheetsvc_idor_001 (rub_001..rub_018).

Direct-coverage tests assert that a stranger never receives another owner's
private timesheet content (sentinel-absent style, robust to either a 403 or a
redaction fix). Anti-overblock tests assert legitimate access is preserved.
Against the shipped (vulnerable) substrate the direct tests FAIL (catching
the leak) and the anti-overblock tests PASS; against a correct fix all pass.

Run from the environment/ directory:
    pytest ../_oracle_dev/test_idor.py -v
"""
import pytest
from fastapi.testclient import TestClient

from timesheetsvc.app import app
from timesheetsvc import store

SECRET = "ZZ-SENTINEL-8k2p1"
RATE   = "ZZ-RATE-8k2p1"
RCPT   = "ZZ-RCPT-8k2p1"
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


def _private_timesheet(client, owner: str = "alice", visibility: str = "private") -> dict:
    return client.post("/timesheets", json={
        "project": "Secret Engagement",
        "status": "draft",
        "entries": [
            {
                "description": "Strategy session",
                "hours": 4.0,
                "rate_code": RATE,
                "discount_code": "DISC-PRIV",
            }
        ],
        "internal_notes": SECRET,
        "private_rate": 250.0,
        "receipts": {"hotel.pdf": RCPT},
        "collaborators": [],
        "visibility": visibility,
    }, headers=_h(owner)).json()


# rub_001
def test_stranger_cannot_read_private_timesheet(client):
    d = _private_timesheet(client)
    r = client.get(f"/timesheets/{d['id']}", headers=_h(STRANGER))
    assert SECRET not in r.text and RATE not in r.text


# rub_002
def test_list_excludes_other_owners_private(client):
    _private_timesheet(client, "alice")
    r = client.get("/timesheets", headers=_h(STRANGER))
    assert SECRET not in r.text and RATE not in r.text


# rub_003
def test_search_excludes_other_owners_private(client):
    _private_timesheet(client, "alice")
    r = client.get("/timesheets/search", params={"q": "Secret"}, headers=_h(STRANGER))
    assert SECRET not in r.text and RATE not in r.text


# rub_004
def test_entries_does_not_leak_rate_code(client):
    d = _private_timesheet(client)
    r = client.get(f"/timesheets/{d['id']}/entries", headers=_h(STRANGER))
    assert RATE not in r.text


# rub_005
def test_export_json_does_not_leak(client):
    d = _private_timesheet(client)
    r = client.get(f"/timesheets/{d['id']}/export",
                   params={"format": "json"}, headers=_h(STRANGER))
    assert SECRET not in r.text and RATE not in r.text


# rub_006
def test_export_csv_does_not_contain_private_bytes(client):
    d = _private_timesheet(client)
    r = client.get(f"/timesheets/{d['id']}/export",
                   params={"format": "csv"}, headers=_h(STRANGER))
    text = r.text if r.status_code == 200 else ""
    assert SECRET not in text and RATE not in text


# rub_007
def test_stranger_cannot_download_receipt(client):
    d = _private_timesheet(client)
    r = client.get(f"/timesheets/{d['id']}/receipts",
                   params={"name": "hotel.pdf"}, headers=_h(STRANGER))
    assert RCPT not in r.text


# rub_008
def test_path_traversal_blocked(client):
    victim = _private_timesheet(client, "alice")
    mine = client.post("/timesheets", json={
        "project": "mine",
        "receipts": {"x.txt": "mydata"},
    }, headers=_h(STRANGER)).json()
    r = client.get(
        f"/timesheets/{mine['id']}/receipts",
        params={"name": f"../{victim['id']}/hotel.pdf"},
        headers=_h(STRANGER),
    )
    assert RCPT not in r.text


# rub_009
def test_clone_then_patch_does_not_leak(client):
    victim = _private_timesheet(client, "alice")
    clone_r = client.post(f"/timesheets/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text and RATE not in clone_r.text
    if clone_r.status_code == 201:
        patch_r = client.patch(
            f"/timesheets/{clone_r.json()['id']}",
            json={"project": "Renamed"},
            headers=_h(STRANGER),
        )
        assert SECRET not in patch_r.text and RATE not in patch_r.text


# rub_010
def test_clone_then_submit_does_not_leak(client):
    victim = _private_timesheet(client, "alice")
    clone_r = client.post(f"/timesheets/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text
    if clone_r.status_code == 201:
        submit_r = client.post(
            f"/timesheets/{clone_r.json()['id']}/submit",
            headers=_h(STRANGER),
        )
        assert SECRET not in submit_r.text


# rub_011
def test_clone_then_export_does_not_leak(client):
    victim = _private_timesheet(client, "alice")
    clone_r = client.post(f"/timesheets/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text
    if clone_r.status_code == 201:
        export_r = client.get(
            f"/timesheets/{clone_r.json()['id']}/export",
            params={"format": "json"},
            headers=_h(STRANGER),
        )
        assert SECRET not in export_r.text and RATE not in export_r.text


# rub_012
def test_owner_still_reads_full(client):
    d = _private_timesheet(client, "alice")
    r = client.get(f"/timesheets/{d['id']}", headers=_h("alice"))
    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET


# rub_013
def test_admin_still_reads_full(client):
    d = _private_timesheet(client, "alice")
    r = client.get(f"/timesheets/{d['id']}", headers=_h("admin"))
    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET


# rub_014
def test_collaborator_still_reads(client):
    d = client.post("/timesheets", json={
        "project": "Partner Engagement",
        "internal_notes": "collab note",
        "collaborators": ["carol"],
        "visibility": "private",
    }, headers=_h("alice")).json()
    r = client.get(f"/timesheets/{d['id']}", headers=_h("carol"))
    assert r.status_code == 200 and "collab note" in r.text


# rub_015
def test_public_timesheet_readable_by_stranger(client):
    d = _private_timesheet(client, "alice", visibility="public")
    r = client.get(f"/timesheets/{d['id']}", headers=_h(STRANGER))
    assert r.status_code == 200 and "Secret Engagement" in r.text


# rub_016
def test_user_can_create_and_list_own(client):
    create_r = client.post("/timesheets", json={"project": "My Timesheet"},
                           headers=_h(STRANGER))
    assert create_r.status_code == 201
    listing = client.get("/timesheets", headers=_h(STRANGER)).json()
    assert any(ts["id"] == create_r.json()["id"] for ts in listing)


# rub_017
def test_sentinel_absent_from_all_stranger_responses(client):
    d = _private_timesheet(client, "alice")
    did = d["id"]
    texts = [
        client.get(f"/timesheets/{did}", headers=_h(STRANGER)).text,
        client.get("/timesheets", headers=_h(STRANGER)).text,
        client.get("/timesheets/search", params={"q": "Secret"}, headers=_h(STRANGER)).text,
        client.get(f"/timesheets/{did}/entries", headers=_h(STRANGER)).text,
        client.get(f"/timesheets/{did}/export", params={"format": "json"}, headers=_h(STRANGER)).text,
        client.get(f"/timesheets/{did}/export", params={"format": "csv"}, headers=_h(STRANGER)).text,
    ]
    combined = "".join(texts)
    assert SECRET not in combined and RCPT not in combined and RATE not in combined


# rub_018 — clone creation response does not carry forward private notes or rate_code
def test_clone_response_does_not_expose_private_data(client):
    victim = _private_timesheet(client, "alice")
    clone_r = client.post(f"/timesheets/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text and RATE not in clone_r.text
