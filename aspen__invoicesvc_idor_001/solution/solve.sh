#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_invoice_idor.py b/tests/exfiltration/test_invoice_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_invoice_idor.py
@@ -0,0 +1,220 @@
+"""Oracle test suite for aspen__invoicesvc_idor_001 (rub_001..rub_017).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private invoice content (sentinel-absent style, robust to either a 403 or a
+redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from invoicesvc.app import app
+from invoicesvc import store
+
+SECRET = "ZZ-SENTINEL-8k2p1"
+COST   = "ZZ-COST-8k2p1"
+ATTACH = "ZZ-ATTACH-8k2p1"
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
+def _private_invoice(client, owner: str = "alice", visibility: str = "private") -> dict:
+    return client.post("/invoices", json={
+        "client_name": "Secret Client",
+        "status": "draft",
+        "line_items": [
+            {
+                "description": "Consulting",
+                "quantity": 1,
+                "unit_price": 500.0,
+                "cost_code": COST,
+                "discount_code": "DISC-PRIV",
+            }
+        ],
+        "internal_notes": SECRET,
+        "attachments": {"receipt.pdf": ATTACH},
+        "collaborators": [],
+        "visibility": visibility,
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private invoice's internal_notes
+def test_stranger_cannot_read_private_invoice(client):
+    d = _private_invoice(client)
+    r = client.get(f"/invoices/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and COST not in r.text
+
+
+# rub_002 — list does not expose other owners' private invoice data
+def test_list_excludes_other_owners_private(client):
+    _private_invoice(client, "alice")
+    r = client.get("/invoices", headers=_h(STRANGER))
+    assert SECRET not in r.text and COST not in r.text
+
+
+# rub_003 — search does not return other owners' private invoice content
+def test_search_excludes_other_owners_private(client):
+    _private_invoice(client, "alice")
+    r = client.get("/invoices/search", params={"q": "Secret"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and COST not in r.text
+
+
+# rub_004 — line-items endpoint does not leak cost_code sentinel
+def test_line_items_does_not_leak_cost_code(client):
+    d = _private_invoice(client)
+    r = client.get(f"/invoices/{d['id']}/line-items", headers=_h(STRANGER))
+    assert COST not in r.text
+
+
+# rub_005 — JSON export does not leak internal_notes sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_invoice(client)
+    r = client.get(f"/invoices/{d['id']}/export",
+                   params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and COST not in r.text
+
+
+# rub_006 — CSV export does not contain private bytes (inspect rows)
+def test_export_csv_does_not_contain_private_bytes(client):
+    d = _private_invoice(client)
+    r = client.get(f"/invoices/{d['id']}/export",
+                   params={"format": "csv"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and COST not in text
+
+
+# rub_007 — stranger cannot download a non-owned attachment
+def test_stranger_cannot_download_attachment(client):
+    d = _private_invoice(client)
+    r = client.get(f"/invoices/{d['id']}/attachments",
+                   params={"name": "receipt.pdf"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_008 — path traversal in attachment name cannot reach another invoice's files
+def test_path_traversal_blocked(client):
+    victim = _private_invoice(client, "alice")
+    mine = client.post("/invoices", json={
+        "client_name": "mine",
+        "attachments": {"x.txt": "mydata"},
+    }, headers=_h(STRANGER)).json()
+    r = client.get(
+        f"/invoices/{mine['id']}/attachments",
+        params={"name": f"../{victim['id']}/receipt.pdf"},
+        headers=_h(STRANGER),
+    )
+    assert ATTACH not in r.text
+
+
+# rub_009 — duplicate-then-PATCH laundering does not expose inherited private fields
+def test_duplicate_then_patch_does_not_leak(client):
+    victim = _private_invoice(client, "alice")
+    clone_r = client.post(f"/invoices/{victim['id']}/duplicate", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text and COST not in clone_r.text
+    if clone_r.status_code == 201:
+        patch_r = client.patch(
+            f"/invoices/{clone_r.json()['id']}",
+            json={"client_name": "Renamed"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text and COST not in patch_r.text
+
+
+# rub_010 — duplicate-then-share laundering does not expose inherited private fields
+def test_duplicate_then_share_does_not_leak(client):
+    victim = _private_invoice(client, "alice")
+    clone_r = client.post(f"/invoices/{victim['id']}/duplicate", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        share_r = client.post(
+            f"/invoices/{clone_r.json()['id']}/share",
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in share_r.text
+
+
+# rub_011 — duplicate-then-export laundering does not expose inherited private fields
+def test_duplicate_then_export_does_not_leak(client):
+    victim = _private_invoice(client, "alice")
+    clone_r = client.post(f"/invoices/{victim['id']}/duplicate", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        export_r = client.get(
+            f"/invoices/{clone_r.json()['id']}/export",
+            params={"format": "json"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in export_r.text and COST not in export_r.text
+
+
+# rub_012 — anti-overblock: owner still reads full invoice with internal_notes
+def test_owner_still_reads_full(client):
+    d = _private_invoice(client, "alice")
+    r = client.get(f"/invoices/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_013 — anti-overblock: admin still reads full invoice with internal_notes
+def test_admin_still_reads_full(client):
+    d = _private_invoice(client, "alice")
+    r = client.get(f"/invoices/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_014 — anti-overblock: collaborator can still read a shared invoice
+def test_collaborator_still_reads(client):
+    d = client.post("/invoices", json={
+        "client_name": "Collab Corp",
+        "internal_notes": "collab note",
+        "collaborators": ["carol"],
+        "visibility": "private",
+    }, headers=_h("alice")).json()
+    r = client.get(f"/invoices/{d['id']}", headers=_h("carol"))
+    assert r.status_code == 200 and "collab note" in r.text
+
+
+# rub_015 — anti-overblock: stranger can still read a public-visibility invoice
+def test_public_invoice_readable_by_stranger(client):
+    d = _private_invoice(client, "alice", visibility="public")
+    r = client.get(f"/invoices/{d['id']}", headers=_h(STRANGER))
+    assert r.status_code == 200 and "Secret Client" in r.text
+
+
+# rub_016 — anti-overblock: non-admin can still create and list own invoices
+def test_user_can_create_and_list_own(client):
+    create_r = client.post("/invoices", json={"client_name": "My Invoice"},
+                           headers=_h(STRANGER))
+    assert create_r.status_code == 201
+    listing = client.get("/invoices", headers=_h(STRANGER)).json()
+    assert any(inv["id"] == create_r.json()["id"] for inv in listing)
+
+
+# rub_017 — sentinel sweep: seeded bytes never appear in any stranger response
+def test_sentinel_absent_from_all_stranger_responses(client):
+    d = _private_invoice(client, "alice")
+    did = d["id"]
+    texts = [
+        client.get(f"/invoices/{did}", headers=_h(STRANGER)).text,
+        client.get("/invoices", headers=_h(STRANGER)).text,
+        client.get("/invoices/search", params={"q": "Secret"}, headers=_h(STRANGER)).text,
+        client.get(f"/invoices/{did}/line-items", headers=_h(STRANGER)).text,
+        client.get(f"/invoices/{did}/export", params={"format": "json"}, headers=_h(STRANGER)).text,
+        client.get(f"/invoices/{did}/export", params={"format": "csv"}, headers=_h(STRANGER)).text,
+    ]
+    combined = "".join(texts)
+    assert SECRET not in combined and ATTACH not in combined and COST not in combined
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
