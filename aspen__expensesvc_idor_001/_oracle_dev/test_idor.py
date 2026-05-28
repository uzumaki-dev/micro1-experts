"""Oracle test suite for aspen__expensesvc_idor_001 (rub_001..rub_017).

Direct-coverage tests assert that a stranger never receives another owner's
private expense content (sentinel-absent style, robust to either a 403 or a
redaction fix). Anti-overblock tests assert legitimate access is preserved.
Against the shipped (vulnerable) substrate the direct tests FAIL (catching
the leak) and the anti-overblock tests PASS; against a correct fix all pass.
"""
import pytest
from fastapi.testclient import TestClient

from expensesvc.app import app
from expensesvc import store

SECRET = "ZZ-SENTINEL-7n3q9"
COST   = "ZZ-COST-7n3q9"
ATTACH = "ZZ-ATTACH-7n3q9"
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


def _private_expense(client, owner: str = "alice", visibility: str = "private") -> dict:
    return client.post("/expenses", json={
        "merchant": "Secret Vendor",
        "status": "draft",
        "line_items": [
            {
                "description": "Consulting",
                "amount": 500.0,
                "cost_code": COST,
                "discount_code": "DISC-PRIV",
            }
        ],
        "private_notes": SECRET,
        "policy_code": "POL-PRIV",
        "receipts": {"receipt.pdf": ATTACH},
        "collaborators": [],
        "visibility": visibility,
    }, headers=_h(owner)).json()


# rub_001 — stranger cannot read a private expense's private_notes
def test_stranger_cannot_read_private_expense(client):
    d = _private_expense(client)
    r = client.get(f"/expenses/{d['id']}", headers=_h(STRANGER))
    assert SECRET not in r.text and COST not in r.text


# rub_002 — list does not expose other owners' private expense data
def test_list_excludes_other_owners_private(client):
    _private_expense(client, "alice")
    r = client.get("/expenses", headers=_h(STRANGER))
    assert SECRET not in r.text and COST not in r.text


# rub_003 — search does not return other owners' private expense content
def test_search_excludes_other_owners_private(client):
    _private_expense(client, "alice")
    r = client.get("/expenses/search", params={"q": "Secret"}, headers=_h(STRANGER))
    assert SECRET not in r.text and COST not in r.text


# rub_004 — line-items endpoint does not leak cost_code sentinel
def test_line_items_does_not_leak_cost_code(client):
    d = _private_expense(client)
    r = client.get(f"/expenses/{d['id']}/line-items", headers=_h(STRANGER))
    assert COST not in r.text


# rub_005 — JSON export does not leak private_notes sentinel
def test_export_json_does_not_leak(client):
    d = _private_expense(client)
    r = client.get(f"/expenses/{d['id']}/export",
                   params={"format": "json"}, headers=_h(STRANGER))
    assert SECRET not in r.text and COST not in r.text


# rub_006 — CSV export does not contain private bytes (inspect rows)
def test_export_csv_does_not_contain_private_bytes(client):
    d = _private_expense(client)
    r = client.get(f"/expenses/{d['id']}/export",
                   params={"format": "csv"}, headers=_h(STRANGER))
    text = r.text if r.status_code == 200 else ""
    assert SECRET not in text and COST not in text


# rub_007 — stranger cannot download a non-owned receipt
def test_stranger_cannot_download_receipt(client):
    d = _private_expense(client)
    r = client.get(f"/expenses/{d['id']}/receipts",
                   params={"name": "receipt.pdf"}, headers=_h(STRANGER))
    assert ATTACH not in r.text


# rub_008 — path traversal in receipt name cannot reach another expense's files
def test_path_traversal_blocked(client):
    victim = _private_expense(client, "alice")
    mine = client.post("/expenses", json={
        "merchant": "mine",
        "receipts": {"x.txt": "mydata"},
    }, headers=_h(STRANGER)).json()
    r = client.get(
        f"/expenses/{mine['id']}/receipts",
        params={"name": f"../{victim['id']}/receipt.pdf"},
        headers=_h(STRANGER),
    )
    assert ATTACH not in r.text


# rub_009 — clone-then-PATCH laundering does not expose inherited private fields
def test_clone_then_patch_does_not_leak(client):
    victim = _private_expense(client, "alice")
    clone_r = client.post(f"/expenses/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text and COST not in clone_r.text
    if clone_r.status_code == 201:
        patch_r = client.patch(
            f"/expenses/{clone_r.json()['id']}",
            json={"merchant": "Renamed"},
            headers=_h(STRANGER),
        )
        assert SECRET not in patch_r.text and COST not in patch_r.text


# rub_010 — clone-then-submit laundering does not expose inherited private fields
def test_clone_then_submit_does_not_leak(client):
    victim = _private_expense(client, "alice")
    clone_r = client.post(f"/expenses/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text
    if clone_r.status_code == 201:
        submit_r = client.post(
            f"/expenses/{clone_r.json()['id']}/submit",
            headers=_h(STRANGER),
        )
        assert SECRET not in submit_r.text


# rub_011 — clone-then-export laundering does not expose inherited private fields
def test_clone_then_export_does_not_leak(client):
    victim = _private_expense(client, "alice")
    clone_r = client.post(f"/expenses/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text
    if clone_r.status_code == 201:
        export_r = client.get(
            f"/expenses/{clone_r.json()['id']}/export",
            params={"format": "json"},
            headers=_h(STRANGER),
        )
        assert SECRET not in export_r.text and COST not in export_r.text


# rub_012 — anti-overblock: owner still reads full expense with private_notes
def test_owner_still_reads_full(client):
    d = _private_expense(client, "alice")
    r = client.get(f"/expenses/{d['id']}", headers=_h("alice"))
    assert r.status_code == 200 and r.json()["private_notes"] == SECRET


# rub_013 — anti-overblock: admin still reads full expense with private_notes
def test_admin_still_reads_full(client):
    d = _private_expense(client, "alice")
    r = client.get(f"/expenses/{d['id']}", headers=_h("admin"))
    assert r.status_code == 200 and r.json()["private_notes"] == SECRET


# rub_014 — anti-overblock: collaborator can still read a shared expense
def test_collaborator_still_reads(client):
    d = client.post("/expenses", json={
        "merchant": "Collab Vendor",
        "private_notes": "collab note",
        "collaborators": ["carol"],
        "visibility": "private",
    }, headers=_h("alice")).json()
    r = client.get(f"/expenses/{d['id']}", headers=_h("carol"))
    assert r.status_code == 200 and "collab note" in r.text


# rub_015 — anti-overblock: stranger can still read a public-visibility expense
def test_public_expense_readable_by_stranger(client):
    d = _private_expense(client, "alice", visibility="public")
    r = client.get(f"/expenses/{d['id']}", headers=_h(STRANGER))
    assert r.status_code == 200 and "Secret Vendor" in r.text


# rub_016 — anti-overblock: non-admin can still create and list own expenses
def test_user_can_create_and_list_own(client):
    create_r = client.post("/expenses", json={"merchant": "My Expense"},
                           headers=_h(STRANGER))
    assert create_r.status_code == 201
    listing = client.get("/expenses", headers=_h(STRANGER)).json()
    assert any(exp["id"] == create_r.json()["id"] for exp in listing)


# rub_017 — sentinel sweep: seeded bytes never appear in any stranger response
def test_sentinel_absent_from_all_stranger_responses(client):
    d = _private_expense(client, "alice")
    did = d["id"]
    texts = [
        client.get(f"/expenses/{did}", headers=_h(STRANGER)).text,
        client.get("/expenses", headers=_h(STRANGER)).text,
        client.get("/expenses/search", params={"q": "Secret"}, headers=_h(STRANGER)).text,
        client.get(f"/expenses/{did}/line-items", headers=_h(STRANGER)).text,
        client.get(f"/expenses/{did}/export", params={"format": "json"}, headers=_h(STRANGER)).text,
        client.get(f"/expenses/{did}/export", params={"format": "csv"}, headers=_h(STRANGER)).text,
    ]
    combined = "".join(texts)
    assert SECRET not in combined and ATTACH not in combined and COST not in combined
