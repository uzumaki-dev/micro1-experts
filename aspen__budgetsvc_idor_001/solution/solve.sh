#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_budget_idor.py b/tests/exfiltration/test_budget_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_budget_idor.py
@@ -0,0 +1,183 @@
+"""Oracle test suite for aspen__budgetsvc_idor_001 (rub_001..rub_018).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private budget content (sentinel-absent style, robust to either a 403 or a
+redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from budgetsvc.app import app
+from budgetsvc import store
+
+SECRET = "ZZ-MEMO-9f3r2"
+ALLOC  = "ZZ-ALLOC-9f3r2"
+ATTACH = "ZZ-ATTACH-9f3r2"
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
+def _private_budget(client, owner: str = "alice", visibility: str = "private") -> dict:
+    return client.post("/budgets", json={
+        "name": "Q3 Operating Budget",
+        "status": "draft",
+        "items": [
+            {
+                "description": "Cloud infrastructure",
+                "amount": 5000.0,
+                "allocation_code": ALLOC,
+                "discount_code": "DISC-OPS",
+            }
+        ],
+        "budget_memo": SECRET,
+        "fiscal_code": "FC-2025-Q3",
+        "attachments": {"invoice.pdf": ATTACH},
+        "collaborators": [],
+        "visibility": visibility,
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private budget's budget_memo
+def test_stranger_cannot_read_private_budget(client):
+    d = _private_budget(client)
+    r = client.get(f"/budgets/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and ALLOC not in r.text
+
+
+# rub_002 — list does not expose other owners' private budget data
+def test_list_excludes_other_owners_private(client):
+    _private_budget(client, "alice")
+    r = client.get("/budgets", headers=_h(STRANGER))
+    assert SECRET not in r.text and ALLOC not in r.text
+
+
+# rub_003 — search does not return other owners' private budget content
+def test_search_excludes_other_owners_private(client):
+    _private_budget(client, "alice")
+    r = client.get("/budgets/search", params={"q": "Q3"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and ALLOC not in r.text
+
+
+# rub_004 — items endpoint does not leak allocation_code sentinel
+def test_items_does_not_leak_allocation_code(client):
+    d = _private_budget(client)
+    r = client.get(f"/budgets/{d['id']}/items", headers=_h(STRANGER))
+    assert ALLOC not in r.text
+
+
+# rub_005 — JSON export does not leak budget_memo sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_budget(client)
+    r = client.get(f"/budgets/{d['id']}/export",
+                   params={"export_format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and ALLOC not in r.text
+
+
+# rub_006 — CSV export does not contain private bytes (inspect rows)
+def test_export_csv_does_not_contain_private_bytes(client):
+    d = _private_budget(client)
+    r = client.get(f"/budgets/{d['id']}/export",
+                   params={"export_format": "csv"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and ALLOC not in text
+
+
+# rub_007 — stranger cannot download a non-owned attachment
+def test_stranger_cannot_download_attachment(client):
+    d = _private_budget(client)
+    r = client.get(f"/budgets/{d['id']}/attachments",
+                   params={"name": "invoice.pdf"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_008 — path traversal in attachment name cannot reach another budget's files
+def test_path_traversal_blocked(client):
+    victim = _private_budget(client, "alice")
+    mine = client.post("/budgets", json={
+        "name": "mine",
+        "attachments": {"x.txt": "mydata"},
+    }, headers=_h(STRANGER)).json()
+    r = client.get(
+        f"/budgets/{mine['id']}/attachments",
+        params={"name": f"../{victim['id']}/invoice.pdf"},
+        headers=_h(STRANGER),
+    )
+    assert ATTACH not in r.text
+
+
+# rub_009 — clone-then-PATCH laundering does not expose inherited private fields
+def test_clone_then_patch_does_not_leak(client):
+    victim = _private_budget(client, "alice")
+    clone_r = client.post(f"/budgets/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text and ALLOC not in clone_r.text
+    if clone_r.status_code == 201:
+        patch_r = client.patch(
+            f"/budgets/{clone_r.json()['id']}",
+            json={"name": "Renamed"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text and ALLOC not in patch_r.text
+
+
+# rub_010 — clone-then-submit laundering does not expose inherited private fields
+def test_clone_then_submit_does_not_leak(client):
+    victim = _private_budget(client, "alice")
+    clone_r = client.post(f"/budgets/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        submit_r = client.post(
+            f"/budgets/{clone_r.json()['id']}/submit",
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in submit_r.text
+
+
+# rub_011 — clone-then-export laundering does not expose inherited private fields
+def test_clone_then_export_does_not_leak(client):
+    victim = _private_budget(client, "alice")
+    clone_r = client.post(f"/budgets/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        export_r = client.get(
+            f"/budgets/{clone_r.json()['id']}/export",
+            params={"export_format": "json"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in export_r.text and ALLOC not in export_r.text
+
+
+# rub_012 — anti-overblock: owner still reads full budget with budget_memo
+def test_owner_still_reads_full(client):
+    d = _private_budget(client, "alice")
+    r = client.get(f"/budgets/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["budget_memo"] == SECRET
+
+
+# rub_013 — anti-overblock: admin still reads full budget with budget_memo
+def test_admin_still_reads_full(client):
+    d = _private_budget(client, "alice")
+    r = client.get(f"/budgets/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["budget_memo"] == SECRET
+
+
+# rub_018 — clone creation response does not carry forward private notes
+def test_clone_response_does_not_expose_private_data(client):
+    victim = _private_budget(client, "alice")
+    clone_r = client.post(f"/budgets/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text and ALLOC not in clone_r.text
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
