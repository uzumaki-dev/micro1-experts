#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_payment_idor.py b/tests/exfiltration/test_payment_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_payment_idor.py
@@ -0,0 +1,188 @@
+"""Oracle test suite for aspen__paymentsvc_idor_001 (rub_001..rub_014).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private payment content (sentinel-absent style, robust to either a 403 or a
+redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from paymentsvc.app import app
+from paymentsvc import store
+
+SECRET = "ZZ-SENTINEL-8p4r2"
+FEE    = "ZZ-FEE-8p4r2"
+ATTACH = "ZZ-ATTACH-8p4r2"
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
+def _private_payment(client, owner: str = "alice", visibility: str = "private") -> dict:
+    return client.post("/payments", json={
+        "merchant": "Secret Vendor",
+        "status": "pending",
+        "line_items": [
+            {
+                "description": "Consulting",
+                "amount": 500.0,
+                "fee_code": FEE,
+                "category_code": "CAT-PRIV",
+            }
+        ],
+        "private_notes": SECRET,
+        "reference_code": "REF-PRIV",
+        "documents": {"receipt.pdf": ATTACH},
+        "collaborators": [],
+        "visibility": visibility,
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private payment's private_notes
+def test_stranger_cannot_read_private_payment(client):
+    d = _private_payment(client)
+    r = client.get(f"/payments/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and FEE not in r.text
+
+
+# rub_002 — list does not expose other owners' private payment data
+def test_list_excludes_other_owners_private(client):
+    _private_payment(client, "alice")
+    r = client.get("/payments", headers=_h(STRANGER))
+    assert SECRET not in r.text and FEE not in r.text
+
+
+# rub_003 — search does not return other owners' private payment content
+def test_search_excludes_other_owners_private(client):
+    _private_payment(client, "alice")
+    r = client.get("/payments/search", params={"q": "Secret"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and FEE not in r.text
+
+
+# rub_004 — line-items endpoint does not leak fee_code sentinel
+def test_line_items_does_not_leak_fee_code(client):
+    d = _private_payment(client)
+    r = client.get(f"/payments/{d['id']}/line-items", headers=_h(STRANGER))
+    assert FEE not in r.text
+
+
+# rub_005 — JSON export does not leak private_notes sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_payment(client)
+    r = client.get(f"/payments/{d['id']}/export",
+                   params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and FEE not in r.text
+
+
+# rub_006 — CSV export does not contain private bytes (inspect rows)
+def test_export_csv_does_not_contain_private_bytes(client):
+    d = _private_payment(client)
+    r = client.get(f"/payments/{d['id']}/export",
+                   params={"format": "csv"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and FEE not in text
+
+
+# rub_007 — stranger cannot download a non-owned document
+def test_stranger_cannot_download_document(client):
+    d = _private_payment(client)
+    r = client.get(f"/payments/{d['id']}/documents",
+                   params={"name": "receipt.pdf"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_008 — path traversal in document name cannot reach another payment's files
+def test_path_traversal_blocked(client):
+    victim = _private_payment(client, "alice")
+    mine = client.post("/payments", json={
+        "merchant": "mine",
+        "documents": {"x.txt": "mydata"},
+    }, headers=_h(STRANGER)).json()
+    r = client.get(
+        f"/payments/{mine['id']}/documents",
+        params={"name": f"../{victim['id']}/receipt.pdf"},
+        headers=_h(STRANGER),
+    )
+    assert ATTACH not in r.text
+
+
+# rub_009 — clone-then-PATCH laundering does not expose inherited private fields
+def test_clone_then_patch_does_not_leak(client):
+    victim = _private_payment(client, "alice")
+    clone_r = client.post(f"/payments/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text and FEE not in clone_r.text
+    if clone_r.status_code == 201:
+        patch_r = client.patch(
+            f"/payments/{clone_r.json()['id']}",
+            json={"merchant": "Renamed"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text and FEE not in patch_r.text
+
+
+# rub_010 — clone-then-export laundering does not expose inherited private fields
+def test_clone_then_export_does_not_leak(client):
+    victim = _private_payment(client, "alice")
+    clone_r = client.post(f"/payments/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        export_r = client.get(
+            f"/payments/{clone_r.json()['id']}/export",
+            params={"format": "json"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in export_r.text and FEE not in export_r.text
+
+
+# rub_011 — anti-overblock: owner still reads full payment with private_notes
+def test_owner_still_reads_full(client):
+    d = _private_payment(client, "alice")
+    r = client.get(f"/payments/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["private_notes"] == SECRET
+
+
+# rub_012 — anti-overblock: admin still reads full payment with private_notes
+def test_admin_still_reads_full(client):
+    d = _private_payment(client, "alice")
+    r = client.get(f"/payments/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["private_notes"] == SECRET
+
+
+# rub_013 — anti-overblock: non-admin can still create and list own payments
+def test_user_can_create_and_list_own(client):
+    create_r = client.post("/payments", json={"merchant": "My Payment"},
+                           headers=_h(STRANGER))
+    assert create_r.status_code == 201
+    listing = client.get("/payments", headers=_h(STRANGER)).json()
+    assert any(pmt["id"] == create_r.json()["id"] for pmt in listing)
+
+
+# rub_014 — sentinel sweep: seeded bytes never appear in any stranger response
+def test_sentinel_absent_from_all_stranger_responses(client):
+    d = _private_payment(client, "alice")
+    did = d["id"]
+    texts = [
+        client.get(f"/payments/{did}", headers=_h(STRANGER)).text,
+        client.get("/payments", headers=_h(STRANGER)).text,
+        client.get("/payments/search", params={"q": "Secret"}, headers=_h(STRANGER)).text,
+        client.get(f"/payments/{did}/line-items", headers=_h(STRANGER)).text,
+        client.get(f"/payments/{did}/export", params={"format": "json"}, headers=_h(STRANGER)).text,
+        client.get(f"/payments/{did}/export", params={"format": "csv"}, headers=_h(STRANGER)).text,
+    ]
+    combined = "".join(texts)
+    assert SECRET not in combined and ATTACH not in combined and FEE not in combined
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
