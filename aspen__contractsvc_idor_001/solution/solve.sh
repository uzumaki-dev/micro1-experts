#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_contract_idor.py b/tests/exfiltration/test_contract_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_contract_idor.py
@@ -0,0 +1,164 @@
+"""Oracle test suite for aspen__contractsvc_idor_001 (rub_001..rub_013).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private contract content (sentinel-absent style, robust to either a 403 or
+a redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from contractsvc.app import app
+from contractsvc import store
+
+SECRET = "ZZ-SENTINEL-q7x2k"
+RATE   = "ZZ-RATE-q7x2k"
+DOC    = "ZZ-DOC-q7x2k"
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
+def _private_contract(client, owner: str = "alice", visibility: str = "private") -> dict:
+    return client.post("/contracts", json={
+        "title": "Secret Agreement",
+        "status": "draft",
+        "counterparty_id": "counterparty_corp",
+        "clauses": [{"description": "Consulting", "quantity": 10, "rate_card": RATE}],
+        "internal_notes": SECRET,
+        "documents": {"contract.pdf": DOC},
+        "collaborators": [],
+        "visibility": visibility,
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read internal_notes via GET /contracts/{id}
+def test_stranger_cannot_read_private_contract(client):
+    d = _private_contract(client)
+    r = client.get(f"/contracts/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and RATE not in r.text
+
+
+# rub_002 — list endpoint does not expose another owner's private data
+def test_list_does_not_expose_private_data(client):
+    _private_contract(client, "alice")
+    r = client.get("/contracts", headers=_h(STRANGER))
+    assert SECRET not in r.text and RATE not in r.text
+
+
+# rub_003 — search endpoint does not return another owner's private data
+def test_search_does_not_expose_private_data(client):
+    _private_contract(client, "alice")
+    r = client.get("/contracts/search", params={"q": "Secret"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and RATE not in r.text
+
+
+# rub_004 — clauses endpoint does not leak rate_card to a stranger
+def test_clauses_do_not_leak_rate_card(client):
+    d = _private_contract(client)
+    r = client.get(f"/contracts/{d['id']}/clauses", headers=_h(STRANGER))
+    assert RATE not in r.text
+
+
+# rub_005 — JSON export does not leak internal_notes sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_contract(client)
+    r = client.get(f"/contracts/{d['id']}/export",
+                   params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and RATE not in r.text
+
+
+# rub_006 — PDF export does not leak internal_notes or rate_card sentinel
+def test_export_pdf_does_not_leak(client):
+    d = _private_contract(client)
+    r = client.get(f"/contracts/{d['id']}/export",
+                   params={"format": "pdf"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and RATE not in text
+
+
+# rub_007 — stranger cannot download a document belonging to another owner
+def test_stranger_cannot_download_document(client):
+    d = _private_contract(client)
+    r = client.get(f"/contracts/{d['id']}/documents",
+                   params={"name": "contract.pdf"}, headers=_h(STRANGER))
+    assert DOC not in r.text
+
+
+# rub_008 — path traversal in document name cannot reach another contract's files
+def test_path_traversal_blocked(client):
+    victim = _private_contract(client, "alice")
+    mine = client.post("/contracts", json={
+        "title": "My Contract",
+        "documents": {"x.txt": "mydata"},
+    }, headers=_h(STRANGER)).json()
+    r = client.get(
+        f"/contracts/{mine['id']}/documents",
+        params={"name": f"../{victim['id']}/contract.pdf"},
+        headers=_h(STRANGER),
+    )
+    assert DOC not in r.text
+
+
+# rub_009 — duplicate-then-PATCH laundering does not expose inherited private fields
+def test_clone_then_patch_does_not_leak(client):
+    victim = _private_contract(client, "alice")
+    clone_r = client.post(f"/contracts/{victim['id']}/duplicate", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text and RATE not in clone_r.text
+    if clone_r.status_code == 201:
+        patch_r = client.patch(
+            f"/contracts/{clone_r.json()['id']}",
+            json={"title": "Renamed"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text and RATE not in patch_r.text
+
+
+# rub_010 — duplicate-then-sign laundering does not expose inherited private fields
+def test_clone_then_sign_does_not_leak(client):
+    victim = _private_contract(client, "alice")
+    clone_r = client.post(f"/contracts/{victim['id']}/duplicate", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        sign_r = client.post(
+            f"/contracts/{clone_r.json()['id']}/sign",
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in sign_r.text
+
+
+# rub_011 — anti-overblock: owner still reads full contract with internal_notes
+def test_owner_still_reads_full(client):
+    d = _private_contract(client, "alice")
+    r = client.get(f"/contracts/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_012 — anti-overblock: admin still reads full contract with internal_notes
+def test_admin_still_reads_full(client):
+    d = _private_contract(client, "alice")
+    r = client.get(f"/contracts/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_013 — anti-overblock: non-admin can create and find own contract in listing
+def test_user_can_create_and_list_own(client):
+    create_r = client.post("/contracts", json={"title": "My Contract"},
+                           headers=_h(STRANGER))
+    assert create_r.status_code == 201
+    listing = client.get("/contracts", headers=_h(STRANGER)).json()
+    assert any(c["id"] == create_r.json()["id"] for c in listing)
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
