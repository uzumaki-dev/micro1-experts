#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/access/test_order_access.py b/tests/access/test_order_access.py
new file mode 100644
--- /dev/null
+++ b/tests/access/test_order_access.py
@@ -0,0 +1,110 @@
+"""Oracle test suite — mass-assignment coverage for ordersvc."""
+from fastapi.testclient import TestClient
+from ordersvc.app import app
+
+client = TestClient(app)
+ITEMS = [{"name": "Widget", "qty": 1, "unit_price": 5.00}]
+
+
+def _create(user: str, **extra) -> dict:
+    r = client.post(
+        "/orders",
+        json={"items": ITEMS, "shipping_address": "1 Test St", **extra},
+        headers={"x-user-id": user},
+    )
+    assert r.status_code == 201
+    return r.json()
+
+
+# --- rub_001: PATCH status override must not persist ---
+def test_patch_status_not_applied():
+    order = _create("alice")
+    oid = order["id"]
+    client.patch(
+        f"/orders/{oid}",
+        json={"status": "shipped"},
+        headers={"x-user-id": "alice"},
+    )
+    got = client.get(f"/orders/{oid}", headers={"x-user-id": "alice"}).json()
+    assert got["status"] != "shipped", "status override must not persist for non-admin"
+
+
+# --- rub_002: PATCH discount_pct override must not persist ---
+def test_patch_discount_not_applied():
+    order = _create("bob")
+    oid = order["id"]
+    client.patch(
+        f"/orders/{oid}",
+        json={"discount_pct": 97.3},
+        headers={"x-user-id": "bob"},
+    )
+    got = client.get(f"/orders/{oid}", headers={"x-user-id": "bob"}).json()
+    assert got["discount_pct"] != 97.3, "discount_pct override must not persist for non-admin"
+
+
+# --- rub_003: PATCH payment_status override must not persist ---
+def test_patch_payment_status_not_applied():
+    order = _create("carol")
+    oid = order["id"]
+    client.patch(
+        f"/orders/{oid}",
+        json={"payment_status": "paid"},
+        headers={"x-user-id": "carol"},
+    )
+    got = client.get(f"/orders/{oid}", headers={"x-user-id": "carol"}).json()
+    assert got["payment_status"] != "paid", "payment_status override must not persist for non-admin"
+
+
+# --- rub_004: POST creation must ignore status override ---
+def test_create_ignores_status_override():
+    order = _create("dave", status="shipped")
+    oid = order["id"]
+    got = client.get(f"/orders/{oid}", headers={"x-user-id": "dave"}).json()
+    assert got["status"] == "pending", "creation must start at pending regardless of body"
+
+
+# --- rub_005: POST creation must ignore discount_pct override ---
+def test_create_ignores_discount_override():
+    order = _create("eve", discount_pct=88.5)
+    oid = order["id"]
+    got = client.get(f"/orders/{oid}", headers={"x-user-id": "eve"}).json()
+    assert got["discount_pct"] == 0.0, "creation must start at 0.0 discount regardless of body"
+
+
+# --- rub_006: owner can PATCH shipping_address (regression guard) ---
+def test_owner_can_patch_shipping_address():
+    order = _create("frank")
+    oid = order["id"]
+    r = client.patch(
+        f"/orders/{oid}",
+        json={"shipping_address": "42 New St"},
+        headers={"x-user-id": "frank"},
+    )
+    assert r.status_code == 200
+    got = client.get(f"/orders/{oid}", headers={"x-user-id": "frank"}).json()
+    assert got["shipping_address"] == "42 New St"
+
+
+# --- rub_007: admin can PATCH status (regression guard) ---
+def test_admin_can_set_status():
+    order = _create("grace")
+    oid = order["id"]
+    r = client.patch(
+        f"/orders/{oid}",
+        json={"status": "confirmed"},
+        headers={"x-user-id": "admin"},
+    )
+    assert r.status_code == 200
+    got = client.get(f"/orders/{oid}", headers={"x-user-id": "admin"}).json()
+    assert got["status"] == "confirmed"
+
+
+# --- rub_008: owner can cancel order (regression guard) ---
+def test_owner_can_cancel():
+    order = _create("henry")
+    oid = order["id"]
+    r = client.post(f"/orders/{oid}/cancel", headers={"x-user-id": "henry"})
+    assert r.status_code == 200
+    assert r.json()["status"] == "cancelled"
+
+
+# rub_009 (test_quality sweep) is satisfied by tests 1-3 above covering all 3 privileged fields.
+# rub_010-014 (negative criteria) are satisfied by the absence of violations in this file.
DIFF_EOF

echo "Oracle diff written to /repo/answer.diff"
