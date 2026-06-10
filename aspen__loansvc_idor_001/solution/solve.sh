#!/usr/bin/env bash
# Oracle — writes the full sentinel-based test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_loan_idor.py b/tests/exfiltration/test_loan_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_loan_idor.py
@@ -0,0 +1,179 @@
+"""Oracle test suite for aspen__loansvc_idor_001."""
+import pytest
+from fastapi.testclient import TestClient
+
+from loansvc.app import app
+from loansvc import store
+
+SENTINEL = "ZZ-SENTINEL-9k3q2"
+FEE_CODE = "ZZ-FEECODE-9k3q2"
+DOC_DATA = "ZZ-DOCDATA-9k3q2"
+ATTACKER = "mallory"
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
+def _private_loan(client, owner: str = "alice") -> dict:
+    r = client.post("/loans", json={
+        "applicant_name": "Alice Example",
+        "underwriter_notes": SENTINEL,
+        "fees": [{"description": "Origination", "amount": 500.0, "fee_code": FEE_CODE}],
+        "documents": {"receipt.pdf": DOC_DATA},
+        "private_rate": 4.5,
+        "visibility": "private",
+    }, headers=_h(owner))
+    assert r.status_code == 201
+    return r.json()
+
+
+# rub_001
+def test_stranger_cannot_read_loan_detail(client):
+    d = _private_loan(client)
+    r = client.get(f"/loans/{d['id']}", headers=_h(ATTACKER))
+    assert SENTINEL not in r.text and FEE_CODE not in r.text
+
+
+# rub_002
+def test_list_does_not_expose_private_data(client):
+    _private_loan(client)
+    r = client.get("/loans", headers=_h(ATTACKER))
+    assert SENTINEL not in r.text and FEE_CODE not in r.text
+
+
+# rub_003
+def test_search_does_not_expose_private_data(client):
+    _private_loan(client)
+    r = client.get("/loans/search", params={"q": "Alice"}, headers=_h(ATTACKER))
+    assert SENTINEL not in r.text and FEE_CODE not in r.text
+
+
+# rub_004
+def test_fees_does_not_expose_fee_code(client):
+    d = _private_loan(client)
+    r = client.get(f"/loans/{d['id']}/fees", headers=_h(ATTACKER))
+    assert FEE_CODE not in r.text
+
+
+# rub_005
+def test_export_json_does_not_leak(client):
+    d = _private_loan(client)
+    r = client.get(f"/loans/{d['id']}/export", params={"format": "json"}, headers=_h(ATTACKER))
+    assert SENTINEL not in r.text and FEE_CODE not in r.text
+
+
+# rub_006
+def test_export_csv_does_not_leak(client):
+    d = _private_loan(client)
+    r = client.get(f"/loans/{d['id']}/export", params={"format": "csv"}, headers=_h(ATTACKER))
+    assert SENTINEL not in r.text and FEE_CODE not in r.text
+
+
+# rub_007
+def test_stranger_cannot_download_document(client):
+    d = _private_loan(client)
+    r = client.get(f"/loans/{d['id']}/documents", params={"name": "receipt.pdf"}, headers=_h(ATTACKER))
+    assert DOC_DATA not in r.text
+
+
+# rub_008
+def test_path_traversal_blocked(client):
+    victim = _private_loan(client, "alice")
+    mine = client.post("/loans", json={
+        "applicant_name": "Bob",
+        "underwriter_notes": "",
+        "fees": [],
+        "documents": {"x.txt": "mydata"},
+        "visibility": "private",
+    }, headers=_h(ATTACKER)).json()
+    r = client.get(
+        f"/loans/{mine['id']}/documents",
+        params={"name": f"../{victim['id']}/receipt.pdf"},
+        headers=_h(ATTACKER),
+    )
+    assert DOC_DATA not in r.text
+
+
+# rub_009
+def test_clone_then_patch_does_not_leak(client):
+    victim = _private_loan(client, "alice")
+    clone_r = client.post(f"/loans/{victim['id']}/clone", headers=_h(ATTACKER))
+    clone_id = clone_r.json()["id"]
+    patch_r = client.patch(
+        f"/loans/{clone_id}",
+        json={"applicant_name": "Eve"},
+        headers=_h(ATTACKER),
+    )
+    assert SENTINEL not in patch_r.text
+
+
+# rub_010
+def test_clone_then_submit_does_not_leak(client):
+    victim = _private_loan(client, "alice")
+    clone_r = client.post(f"/loans/{victim['id']}/clone", headers=_h(ATTACKER))
+    clone_id = clone_r.json()["id"]
+    submit_r = client.post(
+        f"/loans/{clone_id}/submit",
+        headers=_h(ATTACKER),
+    )
+    assert SENTINEL not in submit_r.text
+
+
+# rub_011
+def test_clone_then_export_does_not_leak(client):
+    victim = _private_loan(client, "alice")
+    clone_r = client.post(f"/loans/{victim['id']}/clone", headers=_h(ATTACKER))
+    clone_id = clone_r.json()["id"]
+    export_r = client.get(
+        f"/loans/{clone_id}/export",
+        params={"format": "json"},
+        headers=_h(ATTACKER),
+    )
+    assert SENTINEL not in export_r.text
+
+
+# rub_012 (test_quality)
+def test_sentinel_sweep_all_stranger_endpoints(client):
+    d = _private_loan(client)
+    did = d["id"]
+    texts = [
+        client.get(f"/loans/{did}", headers=_h(ATTACKER)).text,
+        client.get("/loans", headers=_h(ATTACKER)).text,
+        client.get("/loans/search", params={"q": "Alice"}, headers=_h(ATTACKER)).text,
+        client.get(f"/loans/{did}/fees", headers=_h(ATTACKER)).text,
+        client.get(f"/loans/{did}/export", params={"format": "json"}, headers=_h(ATTACKER)).text,
+        client.get(f"/loans/{did}/export", params={"format": "csv"}, headers=_h(ATTACKER)).text,
+        client.get(f"/loans/{did}/documents", params={"name": "receipt.pdf"}, headers=_h(ATTACKER)).text,
+    ]
+    combined = "".join(texts)
+    assert SENTINEL not in combined
+    assert FEE_CODE not in combined
+    assert DOC_DATA not in combined
+
+
+# rub_013
+def test_owner_still_reads_full(client):
+    d = _private_loan(client, "alice")
+    r = client.get(f"/loans/{d['id']}", headers=_h("alice"))
+    assert r.status_code == 200
+    assert SENTINEL in r.json()["underwriter_notes"]
+
+
+# rub_014
+def test_admin_still_reads_full(client):
+    d = _private_loan(client, "alice")
+    r = client.get(f"/loans/{d['id']}", headers=_h("admin"))
+    assert r.status_code == 200
+    assert SENTINEL in r.json()["underwriter_notes"]
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
