#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_notification_idor.py b/tests/exfiltration/test_notification_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_notification_idor.py
@@ -0,0 +1,185 @@
+"""Oracle test suite for aspen__notificationsvc_idor_001 (rub_001..rub_014).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private notification content (sentinel-absent style, robust to either a 403 or a
+redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from notificationsvc.app import app
+from notificationsvc import store
+
+SECRET = "ZZ-PRIV-BODY-n7k1q"
+CHANCODE = "ZZ-CHAN-CODE-n7k1q"
+ATTACH = "ZZ-ATTACH-n7k1q"
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
+def _private_notification(client, owner: str = "alice", visibility: str = "private") -> dict:
+    return client.post("/notifications", json={
+        "subject": "Confidential Alert",
+        "recipient": owner,
+        "private_body": SECRET,
+        "delivery_log": [
+            {
+                "timestamp": "2025-01-01T00:00:00Z",
+                "status": "delivered",
+                "channel_code": CHANCODE,
+            }
+        ],
+        "attachments": {"report.pdf": ATTACH},
+        "shared_with": [],
+        "visibility": visibility,
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private notification's private_body
+def test_stranger_cannot_read_private_notification(client):
+    d = _private_notification(client)
+    r = client.get(f"/notifications/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text
+
+
+# rub_002 — list does not expose other owners' private notification data
+def test_list_excludes_other_owners_private(client):
+    _private_notification(client, "alice")
+    r = client.get("/notifications", headers=_h(STRANGER))
+    assert SECRET not in r.text
+
+
+# rub_003 — search does not return other owners' private notification content
+def test_search_excludes_other_owners_private(client):
+    _private_notification(client, "alice")
+    r = client.get("/notifications/search", params={"q": "Confidential"}, headers=_h(STRANGER))
+    assert SECRET not in r.text
+
+
+# rub_004 — delivery-log endpoint does not leak channel_code sentinel
+def test_delivery_log_does_not_leak_channel_code(client):
+    d = _private_notification(client)
+    r = client.get(f"/notifications/{d['id']}/delivery-log", headers=_h(STRANGER))
+    assert CHANCODE not in r.text
+
+
+# rub_005 — JSON export does not leak private_body sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_notification(client)
+    r = client.get(f"/notifications/{d['id']}/export",
+                   params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and CHANCODE not in r.text
+
+
+# rub_006 — CSV export does not contain private bytes (inspect rows)
+def test_export_csv_does_not_contain_private_bytes(client):
+    d = _private_notification(client)
+    r = client.get(f"/notifications/{d['id']}/export",
+                   params={"format": "csv"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and CHANCODE not in text
+
+
+# rub_007 — stranger cannot download a non-owned attachment
+def test_stranger_cannot_download_attachment(client):
+    d = _private_notification(client)
+    r = client.get(f"/notifications/{d['id']}/attachments",
+                   params={"name": "report.pdf"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_008 — path traversal in attachment name cannot reach another notification's files
+def test_path_traversal_blocked(client):
+    victim = _private_notification(client, "alice")
+    mine = client.post("/notifications", json={
+        "subject": "My Notification",
+        "attachments": {"x.txt": "mydata"},
+    }, headers=_h(STRANGER)).json()
+    r = client.get(
+        f"/notifications/{mine['id']}/attachments",
+        params={"name": f"../{victim['id']}/report.pdf"},
+        headers=_h(STRANGER),
+    )
+    assert ATTACH not in r.text
+
+
+# rub_009 — duplicate-then-PATCH laundering does not expose inherited private fields
+def test_duplicate_then_patch_does_not_leak(client):
+    victim = _private_notification(client, "alice")
+    dup_r = client.post(f"/notifications/{victim['id']}/duplicate", headers=_h(STRANGER))
+    assert SECRET not in dup_r.text and CHANCODE not in dup_r.text
+    if dup_r.status_code == 201:
+        patch_r = client.patch(
+            f"/notifications/{dup_r.json()['id']}",
+            json={"subject": "Renamed"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text and CHANCODE not in patch_r.text
+
+
+# rub_010 — duplicate-then-forward laundering does not expose inherited private fields
+def test_duplicate_then_forward_does_not_leak(client):
+    victim = _private_notification(client, "alice")
+    dup_r = client.post(f"/notifications/{victim['id']}/duplicate", headers=_h(STRANGER))
+    assert SECRET not in dup_r.text
+    if dup_r.status_code == 201:
+        fwd_r = client.post(
+            f"/notifications/{dup_r.json()['id']}/forward",
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in fwd_r.text
+
+
+# rub_011 — anti-overblock: owner still reads full notification with private_body
+def test_owner_still_reads_full(client):
+    d = _private_notification(client, "alice")
+    r = client.get(f"/notifications/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["private_body"] == SECRET
+
+
+# rub_012 — anti-overblock: admin still reads full notification with private_body
+def test_admin_still_reads_full(client):
+    d = _private_notification(client, "alice")
+    r = client.get(f"/notifications/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["private_body"] == SECRET
+
+
+# rub_013 — anti-overblock: non-admin can still create and list own notifications
+def test_user_can_create_and_list_own(client):
+    create_r = client.post("/notifications", json={"subject": "My Notification"},
+                           headers=_h(STRANGER))
+    assert create_r.status_code == 201
+    listing = client.get("/notifications", headers=_h(STRANGER)).json()
+    assert any(n["id"] == create_r.json()["id"] for n in listing)
+
+
+# rub_014 — sentinel sweep: seeded bytes never appear in any stranger response
+def test_sentinel_absent_from_all_stranger_responses(client):
+    d = _private_notification(client, "alice")
+    did = d["id"]
+    texts = [
+        client.get(f"/notifications/{did}", headers=_h(STRANGER)).text,
+        client.get("/notifications", headers=_h(STRANGER)).text,
+        client.get("/notifications/search", params={"q": "Confidential"}, headers=_h(STRANGER)).text,
+        client.get(f"/notifications/{did}/delivery-log", headers=_h(STRANGER)).text,
+        client.get(f"/notifications/{did}/export", params={"format": "json"}, headers=_h(STRANGER)).text,
+        client.get(f"/notifications/{did}/export", params={"format": "csv"}, headers=_h(STRANGER)).text,
+    ]
+    combined = "".join(texts)
+    assert SECRET not in combined and ATTACH not in combined and CHANCODE not in combined
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
