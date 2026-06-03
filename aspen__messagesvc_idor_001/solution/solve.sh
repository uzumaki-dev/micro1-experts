#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$(dirname /repo/answer.diff)"

cat > /repo/answer.diff <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_idor.py b/tests/exfiltration/test_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_idor.py
@@ -0,0 +1,171 @@
+"""Oracle test suite for messagesvc IDOR task (rub_001..rub_018).
+
+Direct-coverage tests assert that a non-participant never receives private content
+(content-absent style, robust to either a 403 or a redaction fix).
+Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate:
+  - direct tests FAIL (catching the leak)
+  - anti-overblock tests PASS
+Against a correct fix all tests pass.
+"""
+import io
+import zipfile
+
+import pytest
+from fastapi.testclient import TestClient
+
+from messagesvc.app import app
+from messagesvc import store
+
+PRIVATE  = "ZZ-PRIVATE-8a2c4"
+ATTACH   = "ZZ-ATTACH-8a2c4"
+CROSS    = "ZZ-CROSS-8a2c4"
+OUTSIDER = "carol"
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
+def _h(uid):
+    return {"X-User-Id": uid}
+
+
+def _seed(client, creator="alice", other="bob"):
+    t = client.post("/threads", json={
+        "title": "Private Planning",
+        "participants": [creator, other],
+        "initial_body": "Confidential discussion",
+        "private_content": PRIVATE,
+        "attachments": {
+            "public_readme.txt": "public-bytes",
+            "private_audit.txt": ATTACH,
+        },
+    }, headers=_h(creator)).json()
+    return t
+
+
+def test_thread_detail_hides_private_content(client):
+    t = _seed(client)
+    r = client.get(f"/threads/{t['id']}", headers=_h(OUTSIDER))
+    assert PRIVATE not in r.text
+
+
+def test_message_list_hides_private_content(client):
+    t = _seed(client)
+    r = client.get(f"/threads/{t['id']}/messages", headers=_h(OUTSIDER))
+    assert PRIVATE not in r.text
+
+
+def test_thread_list_hides_private_content(client):
+    _seed(client)
+    r = client.get("/threads", headers=_h(OUTSIDER))
+    assert PRIVATE not in r.text
+
+
+def test_search_hides_private_content(client):
+    _seed(client)
+    r = client.get("/threads/search", params={"q": PRIVATE},
+                   headers=_h(OUTSIDER))
+    assert PRIVATE not in r.text
+
+
+def test_private_attachment_hidden(client):
+    t = _seed(client)
+    r = client.get(f"/threads/{t['id']}/attachments",
+                   params={"name": "private_audit.txt"}, headers=_h(OUTSIDER))
+    assert ATTACH not in r.text
+
+
+def test_export_json_hides_private_content(client):
+    t = _seed(client)
+    r = client.get(f"/threads/{t['id']}/export",
+                   params={"format": "json"}, headers=_h(OUTSIDER))
+    assert PRIVATE not in r.text
+
+
+def test_export_zip_hides_sentinels(client):
+    t = _seed(client)
+    r = client.get(f"/threads/{t['id']}/export",
+                   params={"format": "zip"}, headers=_h(OUTSIDER))
+    blob = r.content
+    if r.status_code == 200 and blob[:2] == b"PK":
+        zf = zipfile.ZipFile(io.BytesIO(blob))
+        blob = b"".join(zf.read(n) for n in zf.namelist())
+    assert PRIVATE.encode() not in blob
+    assert ATTACH.encode() not in blob
+
+
+def test_message_endpoint_hides_private_content(client):
+    t = _seed(client)
+    msg = client.post(f"/threads/{t['id']}/messages", json={
+        "body": "Admin reply",
+        "private_content": PRIVATE,
+    }, headers=_h("admin")).json()
+    r = client.get(f"/messages/{msg['id']}", headers=_h(OUTSIDER))
+    assert PRIVATE not in r.text
+
+
+def test_admin_sees_private_content(client):
+    t = _seed(client)
+    r = client.get(f"/threads/{t['id']}", headers=_h("admin"))
+    assert r.status_code == 200
+    assert PRIVATE in r.text
+
+
+def test_participant_sees_private_content_in_messages(client):
+    t = _seed(client)
+    r = client.get(f"/threads/{t['id']}/messages", headers=_h("alice"))
+    assert r.status_code == 200
+    assert PRIVATE in r.text
+
+
+def test_participant_can_post_message(client):
+    t = _seed(client)
+    r = client.post(f"/threads/{t['id']}/messages", json={
+        "body": "Participant reply", "private_content": "",
+    }, headers=_h("alice"))
+    assert r.status_code == 201
+
+
+def test_cross_thread_isolation(client):
+    """bob is a participant of thread A but NOT thread B."""
+    client.post("/threads", json={
+        "title": "Thread A", "participants": ["alice", "bob"],
+        "initial_body": "Thread A body", "private_content": "",
+    }, headers=_h("alice")).json()
+    t_b = client.post("/threads", json={
+        "title": "Thread B", "participants": ["alice"],
+        "initial_body": "Thread B body", "private_content": CROSS,
+    }, headers=_h("alice")).json()
+    r = client.get(f"/threads/{t_b['id']}", headers=_h("bob"))
+    assert CROSS not in r.text
+
+
+def test_sentinel_sweep(client):
+    t = _seed(client)
+    tid = t["id"]
+    texts = [
+        client.get(f"/threads/{tid}", headers=_h(OUTSIDER)).text,
+        client.get(f"/threads/{tid}/messages", headers=_h(OUTSIDER)).text,
+        client.get("/threads", headers=_h(OUTSIDER)).text,
+        client.get("/threads/search", params={"q": PRIVATE},
+                   headers=_h(OUTSIDER)).text,
+    ]
+    zip_r = client.get(f"/threads/{tid}/export",
+                       params={"format": "zip"}, headers=_h(OUTSIDER))
+    zip_blob = b""
+    if zip_r.status_code == 200 and zip_r.content[:2] == b"PK":
+        zf = zipfile.ZipFile(io.BytesIO(zip_r.content))
+        zip_blob = b"".join(zf.read(n) for n in zf.namelist())
+    all_bytes = "".join(texts).encode() + zip_blob
+    assert PRIVATE.encode() not in all_bytes
+    assert ATTACH.encode() not in all_bytes
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
