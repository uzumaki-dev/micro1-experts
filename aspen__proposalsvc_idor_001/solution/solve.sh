#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_proposal_idor.py b/tests/exfiltration/test_proposal_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_proposal_idor.py
@@ -0,0 +1,185 @@
+"""Oracle test suite for aspen__proposalsvc_idor_001 (rub_001..rub_014).
+
+Direct-coverage tests assert that a stranger never receives another owner's
+private proposal content (sentinel-absent style, robust to either a 403 or a
+redaction fix). Anti-overblock tests assert legitimate access is preserved.
+Against the shipped (vulnerable) substrate the direct tests FAIL (catching
+the leak) and the anti-overblock tests PASS; against a correct fix all pass.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from proposalsvc.app import app
+from proposalsvc import store
+
+SECRET = "ZZ-SENTINEL-9q5r3"
+MARGIN = "ZZ-MARGIN-9q5r3"
+ATTACH = "ZZ-ATTACH-9q5r3"
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
+def _private_proposal(client, owner: str = "alice", visibility: str = "private") -> dict:
+    return client.post("/proposals", json={
+        "client_name": "Confidential Corp",
+        "status": "draft",
+        "line_items": [
+            {
+                "description": "Strategic consulting",
+                "quantity": 10,
+                "unit_price": 500.0,
+                "margin_code": MARGIN,
+            }
+        ],
+        "internal_notes": SECRET,
+        "discount_pct": 15.0,
+        "attachments": {"terms.pdf": ATTACH},
+        "collaborators": [],
+        "visibility": visibility,
+    }, headers=_h(owner)).json()
+
+
+# rub_001 — stranger cannot read a private proposal's internal_notes
+def test_stranger_cannot_read_private_proposal(client):
+    d = _private_proposal(client)
+    r = client.get(f"/proposals/{d['id']}", headers=_h(STRANGER))
+    assert SECRET not in r.text and MARGIN not in r.text
+
+
+# rub_002 — list does not expose other owners' private proposal data
+def test_list_excludes_other_owners_private(client):
+    _private_proposal(client, "alice")
+    r = client.get("/proposals", headers=_h(STRANGER))
+    assert SECRET not in r.text and MARGIN not in r.text
+
+
+# rub_003 — search does not return other owners' private proposal content
+def test_search_excludes_other_owners_private(client):
+    _private_proposal(client, "alice")
+    r = client.get("/proposals/search", params={"q": "Confidential"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and MARGIN not in r.text
+
+
+# rub_004 — line-items endpoint does not leak margin_code sentinel
+def test_line_items_does_not_leak_margin_code(client):
+    d = _private_proposal(client)
+    r = client.get(f"/proposals/{d['id']}/line-items", headers=_h(STRANGER))
+    assert MARGIN not in r.text
+
+
+# rub_005 — JSON export does not leak internal_notes sentinel
+def test_export_json_does_not_leak(client):
+    d = _private_proposal(client)
+    r = client.get(f"/proposals/{d['id']}/export",
+                   params={"format": "json"}, headers=_h(STRANGER))
+    assert SECRET not in r.text and MARGIN not in r.text
+
+
+# rub_006 — CSV export does not contain private bytes (inspect rows)
+def test_export_csv_does_not_contain_private_bytes(client):
+    d = _private_proposal(client)
+    r = client.get(f"/proposals/{d['id']}/export",
+                   params={"format": "csv"}, headers=_h(STRANGER))
+    text = r.text if r.status_code == 200 else ""
+    assert SECRET not in text and MARGIN not in text
+
+
+# rub_007 — stranger cannot download a non-owned attachment
+def test_stranger_cannot_download_attachment(client):
+    d = _private_proposal(client)
+    r = client.get(f"/proposals/{d['id']}/attachments",
+                   params={"name": "terms.pdf"}, headers=_h(STRANGER))
+    assert ATTACH not in r.text
+
+
+# rub_008 — path traversal in attachment name cannot reach another proposal's files
+def test_path_traversal_blocked(client):
+    victim = _private_proposal(client, "alice")
+    mine = client.post("/proposals", json={
+        "client_name": "My Client",
+        "attachments": {"x.txt": "mydata"},
+    }, headers=_h(STRANGER)).json()
+    r = client.get(
+        f"/proposals/{mine['id']}/attachments",
+        params={"name": f"../{victim['id']}/terms.pdf"},
+        headers=_h(STRANGER),
+    )
+    assert ATTACH not in r.text
+
+
+# rub_009 — clone-then-PATCH laundering does not expose inherited private fields
+def test_clone_then_patch_does_not_leak(client):
+    victim = _private_proposal(client, "alice")
+    clone_r = client.post(f"/proposals/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text and MARGIN not in clone_r.text
+    if clone_r.status_code == 201:
+        patch_r = client.patch(
+            f"/proposals/{clone_r.json()['id']}",
+            json={"client_name": "Renamed Client"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in patch_r.text and MARGIN not in patch_r.text
+
+
+# rub_010 — clone-then-send laundering does not expose inherited private fields
+def test_clone_then_send_does_not_leak(client):
+    victim = _private_proposal(client, "alice")
+    clone_r = client.post(f"/proposals/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text and MARGIN not in clone_r.text
+    if clone_r.status_code == 201:
+        send_r = client.post(
+            f"/proposals/{clone_r.json()['id']}/send",
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in send_r.text and MARGIN not in send_r.text
+
+
+# rub_011 — clone-then-export laundering does not expose inherited private fields
+def test_clone_then_export_does_not_leak(client):
+    victim = _private_proposal(client, "alice")
+    clone_r = client.post(f"/proposals/{victim['id']}/clone", headers=_h(STRANGER))
+    assert SECRET not in clone_r.text
+    if clone_r.status_code == 201:
+        export_r = client.get(
+            f"/proposals/{clone_r.json()['id']}/export",
+            params={"format": "json"},
+            headers=_h(STRANGER),
+        )
+        assert SECRET not in export_r.text and MARGIN not in export_r.text
+
+
+# rub_012 — anti-overblock: owner still reads full proposal with internal_notes
+def test_owner_still_reads_full(client):
+    d = _private_proposal(client, "alice")
+    r = client.get(f"/proposals/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_013 — anti-overblock: admin still reads full proposal with internal_notes
+def test_admin_still_reads_full(client):
+    d = _private_proposal(client, "alice")
+    r = client.get(f"/proposals/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200 and r.json()["internal_notes"] == SECRET
+
+
+# rub_014 — anti-overblock: non-admin can still create and list own proposals
+def test_user_can_create_and_list_own(client):
+    create_r = client.post("/proposals", json={"client_name": "My Proposal"},
+                           headers=_h(STRANGER))
+    assert create_r.status_code == 201
+    listing = client.get("/proposals", headers=_h(STRANGER)).json()
+    assert any(p["id"] == create_r.json()["id"] for p in listing)
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
