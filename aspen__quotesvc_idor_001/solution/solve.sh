#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_quote_idor.py b/tests/exfiltration/test_quote_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_quote_idor.py
@@ -0,0 +1,188 @@
+"""Oracle test suite for aspen__quotesvc_idor_001 (rub_001..rub_020).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private quote content (sentinel-absent style, robust to either a 403 or a
+redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from quotesvc.app import app
+from quotesvc import store
+
+SECRET = "ZZ-SENTINEL-q9r3x"
+VENDOR = "ZZ-VENDOR-q9r3x"
+ATTACH = "ZZ-ATTACH-q9r3x"
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
+def _private_quote(client, owner: str = "alice", visibility: str = "private") -> dict:
+    return client.post("/quotes", json={
+        "client_name": "Secret Client",
+        "status": "draft",
+        "line_items": [
+            {
+                "description": "Implementation",
+                "quantity": 5.0,
+                "unit_price": 200.0,
+                "vendor_code": VENDOR,
+                "discount_code": "DISC-PRIV",
+            }
+        ],
+        "internal_notes": SECRET,
+        "terms": "Confidential terms",
+        "attachments": {"proposal.pdf": ATTACH},
+        "collaborators": [],
+        "visibility": visibility,
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private quote's internal_notes
+def test_stranger_cannot_read_private_quote(client):
+    d = _private_quote(client)
+    r = client.get(f"/quotes/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and VENDOR not in r.text
+
+
+# rub_002 — list does not expose other owners' private quote data
+def test_list_excludes_other_owners_private(client):
+    _private_quote(client, "alice")
+    r = client.get("/quotes", headers=_h(STRANGER))
+    assert SECRET not in r.text and VENDOR not in r.text
+
+
+# rub_003 — search does not return other owners' private quote content
+def test_search_excludes_other_owners_private(client):
+    _private_quote(client, "alice")
+    r = client.get("/quotes/search", params={"q": "Secret"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and VENDOR not in r.text
+
+
+# rub_004 — line-items endpoint does not leak vendor_code sentinel
+def test_line_items_does_not_leak_vendor_code(client):
+    d = _private_quote(client)
+    r = client.get(f"/quotes/{d['id']}/line-items", headers=_h(STRANGER))
+    assert VENDOR not in r.text
+
+
+# rub_005 — JSON export does not leak internal_notes sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_quote(client)
+    r = client.get(f"/quotes/{d['id']}/export",
+                   params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and VENDOR not in r.text
+
+
+# rub_006 — CSV export does not contain private bytes (inspect rows)
+def test_export_csv_does_not_contain_private_bytes(client):
+    d = _private_quote(client)
+    r = client.get(f"/quotes/{d['id']}/export",
+                   params={"format": "csv"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and VENDOR not in text
+
+
+# rub_007 — stranger cannot download a non-owned attachment
+def test_stranger_cannot_download_attachment(client):
+    d = _private_quote(client)
+    r = client.get(f"/quotes/{d['id']}/attachments",
+                   params={"name": "proposal.pdf"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_008 — path traversal in attachment name cannot reach another quote's files
+def test_path_traversal_blocked(client):
+    victim = _private_quote(client, "alice")
+    mine = client.post("/quotes", json={
+        "client_name": "mine",
+        "attachments": {"x.txt": "mydata"},
+    }, headers=_h(STRANGER)).json()
+    r = client.get(
+        f"/quotes/{mine['id']}/attachments",
+        params={"name": f"../{victim['id']}/proposal.pdf"},
+        headers=_h(STRANGER),
+    )
+    assert ATTACH not in r.text
+
+
+# rub_009 — fork-then-PATCH laundering does not expose inherited private fields
+def test_fork_then_patch_does_not_leak(client):
+    victim = _private_quote(client, "alice")
+    fork_r = client.post(f"/quotes/{victim['id']}/fork", headers=_h(STRANGER))
+    assert SECRET not in fork_r.text and VENDOR not in fork_r.text
+    if fork_r.status_code == 201:
+        patch_r = client.patch(
+            f"/quotes/{fork_r.json()['id']}",
+            json={"client_name": "Renamed"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text and VENDOR not in patch_r.text
+
+
+# rub_010 — fork-then-send laundering does not expose inherited private fields
+def test_fork_then_send_does_not_leak(client):
+    victim = _private_quote(client, "alice")
+    fork_r = client.post(f"/quotes/{victim['id']}/fork", headers=_h(STRANGER))
+    assert SECRET not in fork_r.text
+    if fork_r.status_code == 201:
+        send_r = client.post(
+            f"/quotes/{fork_r.json()['id']}/send",
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in send_r.text
+
+
+# rub_011 — anti-overblock: owner still reads full quote with internal_notes
+def test_owner_still_reads_full(client):
+    d = _private_quote(client, "alice")
+    r = client.get(f"/quotes/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_012 — anti-overblock: admin still reads full quote with internal_notes
+def test_admin_still_reads_full(client):
+    d = _private_quote(client, "alice")
+    r = client.get(f"/quotes/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_013 — anti-overblock: non-admin can still create and list own quotes
+def test_user_can_create_and_list_own(client):
+    create_r = client.post("/quotes", json={"client_name": "My Quote"},
+                           headers=_h(STRANGER))
+    assert create_r.status_code == 201
+    listing = client.get("/quotes", headers=_h(STRANGER)).json()
+    assert any(q["id"] == create_r.json()["id"] for q in listing)
+
+
+# rub_014 — sentinel sweep: seeded bytes never appear in any stranger response
+def test_sentinel_absent_from_all_stranger_responses(client):
+    d = _private_quote(client, "alice")
+    did = d["id"]
+    texts = [
+        client.get(f"/quotes/{did}", headers=_h(STRANGER)).text,
+        client.get("/quotes", headers=_h(STRANGER)).text,
+        client.get("/quotes/search", params={"q": "Secret"}, headers=_h(STRANGER)).text,
+        client.get(f"/quotes/{did}/line-items", headers=_h(STRANGER)).text,
+        client.get(f"/quotes/{did}/export", params={"format": "json"}, headers=_h(STRANGER)).text,
+        client.get(f"/quotes/{did}/export", params={"format": "csv"}, headers=_h(STRANGER)).text,
+    ]
+    combined = "".join(texts)
+    assert SECRET not in combined and ATTACH not in combined and VENDOR not in combined
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
