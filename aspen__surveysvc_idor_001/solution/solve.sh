#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

OUTFILE=/repo/answer.diff
TESTPATH=tests/exfiltration/test_survey_idor.py

mkdir -p "$(dirname "$OUTFILE")"
mkdir -p "/repo/tests/exfiltration"

cat > "/repo/$TESTPATH" <<'PYEOF'
"""Oracle test suite for aspen__surveysvc_idor_001 (rub_001..rub_014).

Direct-coverage tests assert that a stranger never receives another owner's
private survey content (sentinel-absent style, robust to either a 403 or a
redaction fix). Anti-overblock tests assert legitimate access is preserved.
Against the shipped (vulnerable) substrate the direct tests FAIL (catching
the leak) and the anti-overblock tests PASS; against a correct fix all pass.
"""
import pytest
from fastapi.testclient import TestClient

from surveysvc.app import app
from surveysvc import store

SECRET = "ZZ-SENTINEL-9m3q2"
SCORE  = "ZZ-SCORE-9m3q2"
ATTACH = "ZZ-ATTACH-9m3q2"
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


def _private_survey(client, owner: str = "alice") -> dict:
    return client.post("/surveys", json={
        "title": "Q3 Feedback",
        "visibility": "private",
        "internal_notes": SECRET,
        "responses": [
            {"question_id": "q1", "answer": "Good", "score_code": SCORE}
        ],
        "attachments": {"report.pdf": ATTACH},
    }, headers=_h(owner)).json()


# rub_001 — stranger cannot read a private survey's internal_notes
def test_stranger_cannot_read_private_survey(client):
    d = _private_survey(client)
    r = client.get(f"/surveys/{d['id']}", headers=_h(STRANGER))
    assert SECRET not in r.text and SCORE not in r.text


# rub_002 — list does not expose other owners' private survey data
def test_list_excludes_other_owners_private(client):
    _private_survey(client, "alice")
    r = client.get("/surveys", headers=_h(STRANGER))
    assert SECRET not in r.text and SCORE not in r.text


# rub_003 — search does not return other owners' private survey content
def test_search_excludes_other_owners_private(client):
    _private_survey(client, "alice")
    r = client.get("/surveys/search", params={"q": "Q3"}, headers=_h(STRANGER))
    assert SECRET not in r.text and SCORE not in r.text


# rub_004 — responses endpoint does not leak score_code sentinel
def test_responses_does_not_leak_score_code(client):
    d = _private_survey(client)
    r = client.get(f"/surveys/{d['id']}/responses", headers=_h(STRANGER))
    assert SCORE not in r.text


# rub_005 — JSON export does not leak internal_notes sentinel
def test_export_json_does_not_leak(client):
    d = _private_survey(client)
    r = client.get(f"/surveys/{d['id']}/export",
                   params={"format": "json"}, headers=_h(STRANGER))
    assert SECRET not in r.text and SCORE not in r.text


# rub_006 — CSV export does not contain private bytes (inspect rows)
def test_export_csv_does_not_contain_private_bytes(client):
    d = _private_survey(client)
    r = client.get(f"/surveys/{d['id']}/export",
                   params={"format": "csv"}, headers=_h(STRANGER))
    text = r.text if r.status_code == 200 else ""
    assert SECRET not in text and SCORE not in text


# rub_007 — stranger cannot download a non-owned attachment
def test_stranger_cannot_download_attachment(client):
    d = _private_survey(client)
    r = client.get(f"/surveys/{d['id']}/attachments",
                   params={"name": "report.pdf"}, headers=_h(STRANGER))
    assert ATTACH not in r.text


# rub_008 — path traversal in attachment name cannot reach another survey's files
def test_path_traversal_blocked(client):
    victim = _private_survey(client, "alice")
    mine = client.post("/surveys", json={
        "title": "My Survey",
        "attachments": {"x.txt": "mydata"},
    }, headers=_h(STRANGER)).json()
    r = client.get(
        f"/surveys/{mine['id']}/attachments",
        params={"name": f"../{victim['id']}/report.pdf"},
        headers=_h(STRANGER),
    )
    assert ATTACH not in r.text


# rub_009 — clone-then-PATCH laundering does not expose inherited private fields
def test_clone_then_patch_does_not_leak(client):
    victim = _private_survey(client, "alice")
    clone_r = client.post(f"/surveys/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text
    if clone_r.status_code == 201:
        patch_r = client.patch(
            f"/surveys/{clone_r.json()['id']}",
            json={"title": "Renamed"},
            headers=_h(STRANGER),
        )
        assert SECRET not in patch_r.text


# rub_010 — clone-then-publish laundering does not expose inherited private fields
def test_clone_then_publish_does_not_leak(client):
    victim = _private_survey(client, "alice")
    clone_r = client.post(f"/surveys/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text
    if clone_r.status_code == 201:
        pub_r = client.post(
            f"/surveys/{clone_r.json()['id']}/publish",
            headers=_h(STRANGER),
        )
        assert SECRET not in pub_r.text


# rub_011 — clone-then-export laundering does not expose inherited private fields
def test_clone_then_export_does_not_leak(client):
    victim = _private_survey(client, "alice")
    clone_r = client.post(f"/surveys/{victim['id']}/clone", headers=_h(STRANGER))
    assert SECRET not in clone_r.text
    if clone_r.status_code == 201:
        export_r = client.get(
            f"/surveys/{clone_r.json()['id']}/export",
            params={"format": "json"},
            headers=_h(STRANGER),
        )
        assert SECRET not in export_r.text and SCORE not in export_r.text


# rub_012 — anti-overblock: owner still reads full survey with internal_notes
def test_owner_still_reads_full(client):
    d = _private_survey(client, "alice")
    r = client.get(f"/surveys/{d['id']}", headers=_h("alice"))
    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET


# rub_013 — anti-overblock: admin still reads full survey with internal_notes
def test_admin_still_reads_full(client):
    d = _private_survey(client, "alice")
    r = client.get(f"/surveys/{d['id']}", headers=_h("admin"))
    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET


# rub_014 — anti-overblock: non-admin can still create and list own surveys
def test_user_can_create_and_list_own(client):
    create_r = client.post("/surveys", json={"title": "My New Survey"},
                           headers=_h(STRANGER))
    assert create_r.status_code == 201
    listing = client.get("/surveys", headers=_h(STRANGER)).json()
    assert any(s["id"] == create_r.json()["id"] for s in listing)
PYEOF

# Generate a proper unified diff using git (auto-computes correct hunk count)
cd /repo
git add "$TESTPATH"
git diff --cached -- "$TESTPATH" > "$OUTFILE"
git rm --cached "$TESTPATH"
rm -f "/repo/$TESTPATH"

echo "Wrote oracle diff to $OUTFILE"
