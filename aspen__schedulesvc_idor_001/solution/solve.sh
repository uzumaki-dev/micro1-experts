#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_schedule_idor.py b/tests/exfiltration/test_schedule_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_schedule_idor.py
@@ -0,0 +1,178 @@
+"""Oracle test suite for aspen__schedulesvc_idor_001 (rub_001..rub_014).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private schedule content (sentinel-absent style, robust to either a 403 or a
+redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from schedulesvc.app import app
+from schedulesvc import store
+
+SECRET = "ZZ-SENTINEL-9m3q2"
+RATE   = "ZZ-RATE-9m3q2"
+ATTACH = "ZZ-ATTACH-9m3q2"
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
+def _private_schedule(client, owner: str = "alice") -> dict:
+    return client.post("/schedules", json={
+        "title": "Q3 Roster",
+        "visibility": "private",
+        "internal_notes": SECRET,
+        "pay_rate": 42.0,
+        "entries": [
+            {"date": "2025-07-01", "hours": 8.0, "rate_code": RATE}
+        ],
+        "attachments": {"policy.pdf": ATTACH},
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private schedule's internal_notes
+def test_stranger_cannot_read_private_schedule(client):
+    d = _private_schedule(client)
+    r = client.get(f"/schedules/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and RATE not in r.text
+
+
+# rub_002 — list does not expose other owners' private schedule data
+def test_list_excludes_other_owners_private(client):
+    _private_schedule(client, "alice")
+    r = client.get("/schedules", headers=_h(STRANGER))
+    assert SECRET not in r.text and RATE not in r.text
+
+
+# rub_003 — search does not return other owners' private schedule content
+def test_search_excludes_other_owners_private(client):
+    _private_schedule(client, "alice")
+    r = client.get("/schedules/search", params={"q": "Q3"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and RATE not in r.text
+
+
+# rub_004 — entries endpoint does not leak rate_code sentinel
+def test_entries_does_not_leak_rate_code(client):
+    d = _private_schedule(client)
+    r = client.get(f"/schedules/{d['id']}/entries", headers=_h(STRANGER))
+    assert RATE not in r.text
+
+
+# rub_005 — JSON export does not leak internal_notes sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_schedule(client)
+    r = client.get(f"/schedules/{d['id']}/export",
+                   params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and RATE not in r.text
+
+
+# rub_006 — CSV export does not contain private bytes (inspect rows)
+def test_export_csv_does_not_contain_private_bytes(client):
+    d = _private_schedule(client)
+    r = client.get(f"/schedules/{d['id']}/export",
+                   params={"format": "csv"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and RATE not in text
+
+
+# rub_007 — stranger cannot download a non-owned attachment
+def test_stranger_cannot_download_attachment(client):
+    d = _private_schedule(client)
+    r = client.get(f"/schedules/{d['id']}/attachments",
+                   params={"name": "policy.pdf"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_008 — path traversal in attachment name cannot reach another schedule's files
+def test_path_traversal_blocked(client):
+    victim = _private_schedule(client, "alice")
+    mine = client.post("/schedules", json={
+        "title": "My Schedule",
+        "attachments": {"x.txt": "mydata"},
+    }, headers=_h(STRANGER)).json()
+    r = client.get(
+        f"/schedules/{mine['id']}/attachments",
+        params={"name": f"../{victim['id']}/policy.pdf"},
+        headers=_h(STRANGER),
+    )
+    assert ATTACH not in r.text
+
+
+# rub_009 — clone-then-PATCH laundering does not expose inherited private fields
+def test_clone_then_patch_does_not_leak(client):
+    victim = _private_schedule(client, "alice")
+    clone_r = client.post(f"/schedules/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        patch_r = client.patch(
+            f"/schedules/{clone_r.json()['id']}",
+            json={"title": "Renamed"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text
+
+
+# rub_010 — clone-then-publish laundering does not expose inherited private fields
+def test_clone_then_publish_does_not_leak(client):
+    victim = _private_schedule(client, "alice")
+    clone_r = client.post(f"/schedules/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        pub_r = client.post(
+            f"/schedules/{clone_r.json()['id']}/publish",
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in pub_r.text
+
+
+# rub_011 — clone-then-export laundering does not expose inherited private fields
+def test_clone_then_export_does_not_leak(client):
+    victim = _private_schedule(client, "alice")
+    clone_r = client.post(f"/schedules/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        export_r = client.get(
+            f"/schedules/{clone_r.json()['id']}/export",
+            params={"format": "json"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in export_r.text and RATE not in export_r.text
+
+
+# rub_012 — anti-overblock: owner still reads full schedule with internal_notes
+def test_owner_still_reads_full(client):
+    d = _private_schedule(client, "alice")
+    r = client.get(f"/schedules/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_013 — anti-overblock: admin still reads full schedule with internal_notes
+def test_admin_still_reads_full(client):
+    d = _private_schedule(client, "alice")
+    r = client.get(f"/schedules/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_014 — anti-overblock: non-admin can still create and list own schedules
+def test_user_can_create_and_list_own(client):
+    create_r = client.post("/schedules", json={"title": "My New Schedule"},
+                           headers=_h(STRANGER))
+    assert create_r.status_code == 201
+    listing = client.get("/schedules", headers=_h(STRANGER)).json()
+    assert any(s["id"] == create_r.json()["id"] for s in listing)
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
