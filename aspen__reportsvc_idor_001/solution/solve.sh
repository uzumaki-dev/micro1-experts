#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_report_idor.py b/tests/exfiltration/test_report_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_report_idor.py
@@ -0,0 +1,186 @@
+"""Oracle test suite for aspen__reportsvc_idor_001 (rub_001..rub_014).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private report content (sentinel-absent style, robust to either a 403 or a
+redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from reportsvc.app import app
+from reportsvc import store
+
+SECRET = "ZZ-SENTINEL-9r4q2"
+METRIC = "ZZ-METRIC-9r4q2"
+ATTACH = "ZZ-ATTACH-9r4q2"
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
+def _private_report(client, owner: str = "alice", visibility: str = "private") -> dict:
+    return client.post("/reports", json={
+        "title": "Confidential Analysis",
+        "status": "draft",
+        "data_points": [
+            {
+                "label": "Revenue",
+                "value": 99999.0,
+                "metric_code": METRIC,
+            }
+        ],
+        "confidential_notes": SECRET,
+        "attachments": {"findings.pdf": ATTACH},
+        "collaborators": [],
+        "visibility": visibility,
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private report's confidential_notes
+def test_stranger_cannot_read_private_report(client):
+    d = _private_report(client)
+    r = client.get(f"/reports/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and METRIC not in r.text
+
+
+# rub_002 — list does not expose other owners' private report data
+def test_list_excludes_other_owners_private(client):
+    _private_report(client, "alice")
+    r = client.get("/reports", headers=_h(STRANGER))
+    assert SECRET not in r.text and METRIC not in r.text
+
+
+# rub_003 — search does not return other owners' private report content
+def test_search_excludes_other_owners_private(client):
+    _private_report(client, "alice")
+    r = client.get("/reports/search", params={"q": "Confidential"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and METRIC not in r.text
+
+
+# rub_004 — data-points endpoint does not leak metric_code sentinel
+def test_data_points_does_not_leak_metric_code(client):
+    d = _private_report(client)
+    r = client.get(f"/reports/{d['id']}/data-points", headers=_h(STRANGER))
+    assert METRIC not in r.text
+
+
+# rub_005 — JSON export does not leak confidential_notes sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_report(client)
+    r = client.get(f"/reports/{d['id']}/export",
+                   params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and METRIC not in r.text
+
+
+# rub_006 — CSV export does not contain private bytes (inspect rows)
+def test_export_csv_does_not_contain_private_bytes(client):
+    d = _private_report(client)
+    r = client.get(f"/reports/{d['id']}/export",
+                   params={"format": "csv"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and METRIC not in text
+
+
+# rub_007 — stranger cannot download a non-owned attachment
+def test_stranger_cannot_download_attachment(client):
+    d = _private_report(client)
+    r = client.get(f"/reports/{d['id']}/attachments",
+                   params={"name": "findings.pdf"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_008 — path traversal in attachment name cannot reach another report's files
+def test_path_traversal_blocked(client):
+    victim = _private_report(client, "alice")
+    mine = client.post("/reports", json={
+        "title": "My Report",
+        "attachments": {"x.txt": "mydata"},
+    }, headers=_h(STRANGER)).json()
+    r = client.get(
+        f"/reports/{mine['id']}/attachments",
+        params={"name": f"../{victim['id']}/findings.pdf"},
+        headers=_h(STRANGER),
+    )
+    assert ATTACH not in r.text
+
+
+# rub_009 — fork-then-PATCH laundering does not expose inherited private fields
+def test_fork_then_patch_does_not_leak(client):
+    victim = _private_report(client, "alice")
+    fork_r = client.post(f"/reports/{victim['id']}/fork", headers=_h(STRANGER))
+    assert SECRET not in fork_r.text and METRIC not in fork_r.text
+    if fork_r.status_code == 201:
+        patch_r = client.patch(
+            f"/reports/{fork_r.json()['id']}",
+            json={"title": "Renamed"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text and METRIC not in patch_r.text
+
+
+# rub_010 — fork-then-export laundering does not expose inherited private fields
+def test_fork_then_export_does_not_leak(client):
+    victim = _private_report(client, "alice")
+    fork_r = client.post(f"/reports/{victim['id']}/fork", headers=_h(STRANGER))
+    assert SECRET not in fork_r.text
+    if fork_r.status_code == 201:
+        export_r = client.get(
+            f"/reports/{fork_r.json()['id']}/export",
+            params={"format": "json"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in export_r.text and METRIC not in export_r.text
+
+
+# rub_011 — anti-overblock: owner still reads full report with confidential_notes
+def test_owner_still_reads_full(client):
+    d = _private_report(client, "alice")
+    r = client.get(f"/reports/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["confidential_notes"] == SECRET
+
+
+# rub_012 — anti-overblock: admin still reads full report with confidential_notes
+def test_admin_still_reads_full(client):
+    d = _private_report(client, "alice")
+    r = client.get(f"/reports/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["confidential_notes"] == SECRET
+
+
+# rub_013 — anti-overblock: non-admin can still create and list own reports
+def test_user_can_create_and_list_own(client):
+    create_r = client.post("/reports", json={"title": "My Report"},
+                           headers=_h(STRANGER))
+    assert create_r.status_code == 201
+    listing = client.get("/reports", headers=_h(STRANGER)).json()
+    assert any(rpt["id"] == create_r.json()["id"] for rpt in listing)
+
+
+# rub_014 — sentinel sweep: seeded bytes never appear in any stranger response
+def test_sentinel_absent_from_all_stranger_responses(client):
+    d = _private_report(client, "alice")
+    did = d["id"]
+    texts = [
+        client.get(f"/reports/{did}", headers=_h(STRANGER)).text,
+        client.get("/reports", headers=_h(STRANGER)).text,
+        client.get("/reports/search", params={"q": "Confidential"}, headers=_h(STRANGER)).text,
+        client.get(f"/reports/{did}/data-points", headers=_h(STRANGER)).text,
+        client.get(f"/reports/{did}/export", params={"format": "json"}, headers=_h(STRANGER)).text,
+        client.get(f"/reports/{did}/export", params={"format": "csv"}, headers=_h(STRANGER)).text,
+    ]
+    combined = "".join(texts)
+    assert SECRET not in combined and ATTACH not in combined and METRIC not in combined
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
