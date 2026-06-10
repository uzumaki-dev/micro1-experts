#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_candidate_idor.py b/tests/exfiltration/test_candidate_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_candidate_idor.py
@@ -0,0 +1,181 @@
+"""Oracle test suite for aspen__candidatesvc_idor_001 (rub_001..rub_014).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private candidate content (sentinel-absent style, robust to either a 403 or
+a redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from candidatesvc.app import app
+from candidatesvc import store
+
+SECRET   = "ZZ-SENTINEL-c9q4r"
+EVAL     = "ZZ-EVAL-c9q4r"
+DOC      = "ZZ-DOC-c9q4r"
+STRANGER = "mallory"
+
+
+@pytest.fixture(autouse=True)
+def _reset():
+    store.reset()
+    yield
+
+
+@pytest.fixture
+def client():
+    return TestClient(app)
+
+
+def _h(user_id: str) -> dict:
+    return {"X-User-Id": user_id}
+
+
+def _private_candidate(client, owner: str = "alice", visibility: str = "private") -> dict:
+    return client.post("/candidates", json={
+        "name": "Alice Smith",
+        "position": "Software Engineer",
+        "status": "reviewing",
+        "screening_notes": SECRET,
+        "assessments": [{"round": "technical", "score": 8, "eval_code": EVAL}],
+        "documents": {"resume.pdf": DOC},
+        "interviewer_ids": [],
+        "visibility": visibility,
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private candidate's screening_notes
+def test_stranger_cannot_read_private_candidate(client):
+    d = _private_candidate(client)
+    r = client.get(f"/candidates/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and EVAL not in r.text
+
+
+# rub_002 — list does not expose other owners' private candidate data
+def test_list_excludes_other_owners_private(client):
+    _private_candidate(client, "alice")
+    r = client.get("/candidates", headers=_h(STRANGER))
+    assert SECRET not in r.text and EVAL not in r.text
+
+
+# rub_003 — search does not return other owners' private candidate content
+def test_search_excludes_other_owners_private(client):
+    _private_candidate(client, "alice")
+    r = client.get("/candidates/search", params={"q": "Alice"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and EVAL not in r.text
+
+
+# rub_004 — assessments endpoint does not leak eval_code sentinel
+def test_assessments_does_not_leak_eval_code(client):
+    d = _private_candidate(client)
+    r = client.get(f"/candidates/{d['id']}/assessments", headers=_h(STRANGER))
+    assert EVAL not in r.text
+
+
+# rub_005 — JSON export does not leak screening_notes sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_candidate(client)
+    r = client.get(f"/candidates/{d['id']}/export",
+                   params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and EVAL not in r.text
+
+
+# rub_006 — CSV export does not contain private bytes (inspect rows)
+def test_export_csv_does_not_contain_private_bytes(client):
+    d = _private_candidate(client)
+    r = client.get(f"/candidates/{d['id']}/export",
+                   params={"format": "csv"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and EVAL not in text
+
+
+# rub_007 — stranger cannot download a non-owned document
+def test_stranger_cannot_download_document(client):
+    d = _private_candidate(client)
+    r = client.get(f"/candidates/{d['id']}/documents",
+                   params={"name": "resume.pdf"}, headers=_h(STRANGER))
+    assert DOC not in r.text
+
+
+# rub_008 — clone-then-PATCH laundering does not expose inherited private fields
+def test_clone_then_patch_does_not_leak(client):
+    victim = _private_candidate(client, "alice")
+    clone_r = client.post(f"/candidates/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text and EVAL not in clone_r.text
+    if clone_r.status_code == 201:
+        patch_r = client.patch(
+            f"/candidates/{clone_r.json()['id']}",
+            json={"position": "Updated Role"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text and EVAL not in patch_r.text
+
+
+# rub_009 — clone-then-share laundering does not expose inherited private fields
+def test_clone_then_share_does_not_leak(client):
+    victim = _private_candidate(client, "alice")
+    clone_r = client.post(f"/candidates/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        share_r = client.post(
+            f"/candidates/{clone_r.json()['id']}/share",
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in share_r.text
+
+
+# rub_010 — clone-then-export laundering does not expose inherited private fields
+def test_clone_then_export_does_not_leak(client):
+    victim = _private_candidate(client, "alice")
+    clone_r = client.post(f"/candidates/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        export_r = client.get(
+            f"/candidates/{clone_r.json()['id']}/export",
+            params={"format": "json"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in export_r.text and EVAL not in export_r.text
+
+
+# rub_011 — anti-overblock: owner still reads full candidate with screening_notes
+def test_owner_still_reads_full(client):
+    d = _private_candidate(client, "alice")
+    r = client.get(f"/candidates/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["screening_notes"] == SECRET
+
+
+# rub_012 — anti-overblock: recruiter still reads full candidate with screening_notes
+def test_recruiter_still_reads_full(client):
+    d = _private_candidate(client, "alice")
+    r = client.get(f"/candidates/{d['id']}", headers=_h("recruiter1"))
+    assert r.status_code == 200 and r.json()["screening_notes"] == SECRET
+
+
+# rub_013 — anti-overblock: non-recruiter can still create and list own candidates
+def test_user_can_create_and_list_own(client):
+    create_r = client.post("/candidates", json={
+        "name": "Mallory Applicant",
+        "position": "Designer",
+    }, headers=_h(STRANGER))
+    assert create_r.status_code == 201
+    listing = client.get("/candidates", headers=_h(STRANGER)).json()
+    assert any(c["id"] == create_r.json()["id"] for c in listing)
+
+
+# rub_014 — sentinel sweep: seeded bytes never appear in any stranger response
+def test_sentinel_absent_from_all_stranger_responses(client):
+    d = _private_candidate(client, "alice")
+    did = d["id"]
+    texts = [
+        client.get(f"/candidates/{did}", headers=_h(STRANGER)).text,
+        client.get("/candidates", headers=_h(STRANGER)).text,
+        client.get("/candidates/search", params={"q": "Alice"}, headers=_h(STRANGER)).text,
+        client.get(f"/candidates/{did}/assessments", headers=_h(STRANGER)).text,
+        client.get(f"/candidates/{did}/export", params={"format": "json"}, headers=_h(STRANGER)).text,
+        client.get(f"/candidates/{did}/export", params={"format": "csv"}, headers=_h(STRANGER)).text,
+    ]
+    combined = "".join(texts)
+    assert SECRET not in combined and EVAL not in combined and DOC not in combined
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
