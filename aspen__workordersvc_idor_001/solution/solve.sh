#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_workorder_idor.py b/tests/exfiltration/test_workorder_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_workorder_idor.py
@@ -0,0 +1,172 @@
+"""Oracle test suite for aspen__workordersvc_idor_001 (rub_001..rub_013).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private workorder content (sentinel-absent style, robust to either a 403 or a
+redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from workordersvc.app import app
+from workordersvc import store
+
+SECRET = "ZZ-SENTINEL-9q5r3"
+LABOR  = "ZZ-LABOR-9q5r3"
+ATTACH = "ZZ-ATTACH-9q5r3"
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
+def _private_workorder(client, owner: str = "alice", visibility: str = "private") -> dict:
+    return client.post("/workorders", json={
+        "title": "Confidential Job",
+        "status": "open",
+        "entries": [
+            {
+                "description": "Electrical work",
+                "hours": 8.0,
+                "labor_code": LABOR,
+                "discount_code": "DISC-PRIV",
+            }
+        ],
+        "internal_notes": SECRET,
+        "private_rate": 95.0,
+        "documents": {"report.pdf": ATTACH},
+        "collaborators": [],
+        "visibility": visibility,
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private workorder's internal_notes
+def test_stranger_cannot_read_private_workorder(client):
+    d = _private_workorder(client)
+    r = client.get(f"/workorders/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and LABOR not in r.text
+
+
+# rub_002 — list does not expose other owners' private workorder data
+def test_list_excludes_other_owners_private(client):
+    _private_workorder(client, "alice")
+    r = client.get("/workorders", headers=_h(STRANGER))
+    assert SECRET not in r.text and LABOR not in r.text
+
+
+# rub_003 — search does not return other owners' private workorder content
+def test_search_excludes_other_owners_private(client):
+    _private_workorder(client, "alice")
+    r = client.get("/workorders/search", params={"q": "Confidential"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and LABOR not in r.text
+
+
+# rub_004 — entries endpoint does not leak labor_code sentinel
+def test_entries_does_not_leak_labor_code(client):
+    d = _private_workorder(client)
+    r = client.get(f"/workorders/{d['id']}/entries", headers=_h(STRANGER))
+    assert LABOR not in r.text
+
+
+# rub_005 — JSON export does not leak internal_notes sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_workorder(client)
+    r = client.get(f"/workorders/{d['id']}/export",
+                   params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and LABOR not in r.text
+
+
+# rub_006 — CSV export does not contain private bytes (inspect rows)
+def test_export_csv_does_not_contain_private_bytes(client):
+    d = _private_workorder(client)
+    r = client.get(f"/workorders/{d['id']}/export",
+                   params={"format": "csv"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and LABOR not in text
+
+
+# rub_007 — stranger cannot download a non-owned document
+def test_stranger_cannot_download_document(client):
+    d = _private_workorder(client)
+    r = client.get(f"/workorders/{d['id']}/documents",
+                   params={"name": "report.pdf"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_008 — path traversal in document name cannot reach another workorder's files
+def test_path_traversal_blocked(client):
+    victim = _private_workorder(client, "alice")
+    mine = client.post("/workorders", json={
+        "title": "My Job",
+        "documents": {"x.txt": "mydata"},
+    }, headers=_h(STRANGER)).json()
+    r = client.get(
+        f"/workorders/{mine['id']}/documents",
+        params={"name": f"../{victim['id']}/report.pdf"},
+        headers=_h(STRANGER),
+    )
+    assert ATTACH not in r.text
+
+
+# rub_009 — clone-then-PATCH laundering does not expose inherited private fields
+def test_clone_then_patch_does_not_leak(client):
+    victim = _private_workorder(client, "alice")
+    clone_r = client.post(f"/workorders/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text and LABOR not in clone_r.text
+    if clone_r.status_code == 201:
+        patch_r = client.patch(
+            f"/workorders/{clone_r.json()['id']}",
+            json={"title": "Renamed Job"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text and LABOR not in patch_r.text
+
+
+# rub_010 — clone-then-export laundering does not expose inherited private fields
+def test_clone_then_export_does_not_leak(client):
+    victim = _private_workorder(client, "alice")
+    clone_r = client.post(f"/workorders/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        export_r = client.get(
+            f"/workorders/{clone_r.json()['id']}/export",
+            params={"format": "json"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in export_r.text and LABOR not in export_r.text
+
+
+# rub_011 — anti-overblock: owner still reads full workorder with internal_notes
+def test_owner_still_reads_full(client):
+    d = _private_workorder(client, "alice")
+    r = client.get(f"/workorders/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_012 — anti-overblock: admin still reads full workorder with internal_notes
+def test_admin_still_reads_full(client):
+    d = _private_workorder(client, "alice")
+    r = client.get(f"/workorders/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_013 — anti-overblock: non-admin can still create and list own workorders
+def test_user_can_create_and_list_own(client):
+    create_r = client.post("/workorders", json={"title": "My Work Order"},
+                           headers=_h(STRANGER))
+    assert create_r.status_code == 201
+    listing = client.get("/workorders", headers=_h(STRANGER)).json()
+    assert any(wo["id"] == create_r.json()["id"] for wo in listing)
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
