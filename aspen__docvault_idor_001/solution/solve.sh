#!/usr/bin/env bash
# Oracle solution for aspen__docvault_idor_001: writes a full test suite that
# catches the IDOR leak on every surface as a unified diff to /repo/answer.diff.
# The judge inspects the diff as text and never applies it; oracle scores ~1.0.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > /repo/answer.diff <<'DIFF_EOF'
diff --git a/tests/idor/test_idor.py b/tests/idor/test_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/idor/test_idor.py
@@ -0,0 +1,193 @@
+"""Oracle test suite for the DocVault IDOR task (rub_001..rub_017).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private content (content-absent style, robust to either a 403 or a redaction
+fix). Anti-overblock tests assert legitimate access is preserved. Against the
+shipped (vulnerable) substrate the direct tests FAIL (catching the leak) and the
+anti-overblock tests PASS; against a correct fix all tests pass.
+"""
+import io
+import zipfile
+
+import pytest
+from fastapi.testclient import TestClient
+
+from docvault.app import app
+from docvault import store
+
+SECRET = "ZZ-SENTINEL-7f3a9"
+ATTACH = "ZZ-ATTACH-7f3a9"
+BODY = "confidential-body-text"
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
+def _h(user_id):
+    return {"X-User-Id": user_id}
+
+
+def _private_doc(client, owner="alice", visibility="private"):
+    return client.post("/documents", json={
+        "title": "Q3 plan", "body": BODY, "visibility": visibility,
+        "secret_notes": SECRET, "collaborators": [], "attachments": {"k.txt": ATTACH},
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private document's contents
+def test_stranger_cannot_read_private_document(client):
+    d = _private_doc(client)
+    r = client.get(f"/documents/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and BODY not in r.text
+
+
+# rub_002 — list does not expose other owners' private documents
+def test_list_excludes_other_owners_private(client):
+    _private_doc(client, "alice")
+    r = client.get("/documents", headers=_h(STRANGER))
+    assert SECRET not in r.text and BODY not in r.text
+
+
+# rub_003 — search does not return other owners' private documents
+def test_search_excludes_other_owners_private(client):
+    _private_doc(client, "alice")
+    r = client.get("/documents/search", params={"q": "confidential"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and BODY not in r.text
+
+
+# rub_004 — JSON export of a non-owned doc does not leak private fields
+def test_export_json_does_not_leak(client):
+    d = _private_doc(client)
+    r = client.get(f"/documents/{d['id']}/export", params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text
+
+
+# rub_005 — ZIP export does not contain private bytes (inspect archive contents)
+def test_export_zip_does_not_contain_private_bytes(client):
+    d = _private_doc(client)
+    r = client.get(f"/documents/{d['id']}/export", params={"format": "zip"}, headers=_h(STRANGER))
+    blob = r.content
+    if r.status_code == 200 and r.content[:2] == b"PK":
+        z = zipfile.ZipFile(io.BytesIO(r.content))
+        blob = b"".join(z.read(n) for n in z.namelist())
+    assert SECRET.encode() not in blob and ATTACH.encode() not in blob
+
+
+# rub_006 — stranger cannot download a non-owned attachment
+def test_stranger_cannot_download_attachment(client):
+    d = _private_doc(client)
+    r = client.get(f"/documents/{d['id']}/attachments", params={"name": "k.txt"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_007 — version history does not leak prior private content
+def test_versions_do_not_leak(client):
+    d = _private_doc(client)
+    client.patch(f"/documents/{d['id']}", json={"body": "v2"}, headers=_h("alice"))
+    r = client.get(f"/documents/{d['id']}/versions", headers=_h(STRANGER))
+    assert SECRET not in r.text
+
+
+# rub_008 — path traversal in attachment name cannot reach another doc's files
+def test_path_traversal_blocked(client):
+    victim = _private_doc(client, "alice")
+    mine = client.post("/documents", json={"title": "m", "attachments": {"x.txt": "mine"}},
+                       headers=_h(STRANGER)).json()
+    r = client.get(f"/documents/{mine['id']}/attachments",
+                   params={"name": f"../{victim['id']}/k.txt"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_009 — duplicate-then-read laundering does not expose inherited private fields
+def test_duplicate_then_read_does_not_leak(client):
+    victim = _private_doc(client, "alice")
+    clone = client.post(f"/documents/{victim['id']}/duplicate", headers=_h(STRANGER))
+    assert SECRET not in clone.text
+
+
+# rub_010 — duplicate-then-share laundering does not leak inherited private fields
+def test_duplicate_then_share_does_not_leak(client):
+    victim = _private_doc(client, "alice")
+    clone = client.post(f"/documents/{victim['id']}/duplicate", headers=_h(STRANGER))
+    if clone.status_code == 201:
+        r = client.post(f"/documents/{clone.json()['id']}/share", headers=_h(STRANGER))
+        assert SECRET not in r.text
+    else:
+        assert clone.status_code in (401, 403, 404)
+
+
+# rub_011 — duplicate-then-export laundering does not leak inherited private fields
+def test_duplicate_then_export_does_not_leak(client):
+    victim = _private_doc(client, "alice")
+    clone = client.post(f"/documents/{victim['id']}/duplicate", headers=_h(STRANGER))
+    if clone.status_code == 201:
+        r = client.get(f"/documents/{clone.json()['id']}/export", params={"format": "json"},
+                       headers=_h(STRANGER))
+        assert SECRET not in r.text
+    else:
+        assert clone.status_code in (401, 403, 404)
+
+
+# rub_012 — anti-overblock: owner still reads full content
+def test_owner_still_reads_full(client):
+    d = _private_doc(client, "alice")
+    r = client.get(f"/documents/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["secret_notes"] == SECRET
+
+
+# rub_013 — anti-overblock: admin still reads full content
+def test_admin_still_reads_full(client):
+    d = _private_doc(client, "alice")
+    r = client.get(f"/documents/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["secret_notes"] == SECRET
+
+
+# rub_014 — anti-overblock: a collaborator can still read a shared doc
+def test_collaborator_still_reads(client):
+    d = client.post("/documents", json={
+        "title": "t", "body": BODY, "visibility": "private", "secret_notes": SECRET,
+        "collaborators": ["carol"], "attachments": {},
+    }, headers=_h("alice")).json()
+    r = client.get(f"/documents/{d['id']}", headers=_h("carol"))
+    assert r.status_code == 200 and r.json()["body"] == BODY
+
+
+# rub_015 — anti-overblock: a public document's body stays readable by a stranger
+def test_public_document_body_readable(client):
+    d = _private_doc(client, "alice", visibility="public")
+    r = client.get(f"/documents/{d['id']}", headers=_h(STRANGER))
+    assert r.status_code == 200 and r.json()["body"] == BODY
+
+
+# rub_016 — anti-overblock: a non-admin can still create and list their OWN docs
+def test_user_can_create_and_list_own(client):
+    mine = client.post("/documents", json={"title": "mine", "body": "x"}, headers=_h(STRANGER))
+    assert mine.status_code == 201
+    listing = client.get("/documents", headers=_h(STRANGER)).json()
+    assert any(d["id"] == mine.json()["id"] for d in listing)
+
+
+# rub_017 — sentinel bytes seeded into a private doc never appear in any stranger
+# response, including inside the zip export
+def test_sentinel_absent_from_all_stranger_responses(client):
+    d = _private_doc(client, "alice")
+    did = d["id"]
+    texts = [
+        client.get(f"/documents/{did}", headers=_h(STRANGER)).text,
+        client.get("/documents", headers=_h(STRANGER)).text,
+        client.get("/documents/search", params={"q": "confidential"}, headers=_h(STRANGER)).text,
+        client.get(f"/documents/{did}/export", params={"format": "json"}, headers=_h(STRANGER)).text,
+        client.get(f"/documents/{did}/versions", headers=_h(STRANGER)).text,
+    ]
+    zip_r = client.get(f"/documents/{did}/export", params={"format": "zip"}, headers=_h(STRANGER))
+    blob = "".join(texts).encode() + (zip_r.content if zip_r.status_code == 200 else b"")
+    assert SECRET.encode() not in blob and ATTACH.encode() not in blob
DIFF_EOF

echo "Wrote oracle answer.diff to /repo/answer.diff (full docvault IDOR suite)."
