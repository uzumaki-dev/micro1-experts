#!/usr/bin/env bash
# Oracle — writes the full state-verification test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_projectsvc_bfla.py b/tests/exfiltration/test_projectsvc_bfla.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_projectsvc_bfla.py
@@ -0,0 +1,195 @@
+"""Oracle test suite for aspen__projectsvc_bfla_001 (rub_001..rub_014).
+
+State-verification tests assert that non-admin members are rejected from
+admin-only operations AND that the server state is unchanged after each
+rejected call. Anti-overblock tests assert admin operations succeed.
+
+Against the shipped (vulnerable) substrate:
+  - rub_001..rub_008 FAIL (catching the BFLA)
+  - rub_009..rub_014 PASS
+
+Against a correct fix, all tests PASS.
+"""
+import pytest
+from fastapi.testclient import TestClient
+from projectsvc.app import app
+from projectsvc import store
+
+SENTINEL = "ZZ-PRIV-REASON-bfla-7x3z"
+ALICE = "alice"
+CAROL = "carol"
+BOB = "bob"
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
+def _project_with_roles(client) -> dict:
+    p = client.post("/projects", json={"name": "Test Project"}, headers=_h(ALICE)).json()
+    pid = p["id"]
+    client.post(f"/projects/{pid}/members",
+                json={"user_id": CAROL, "role": "editor", "private_reason": SENTINEL},
+                headers=_h(ALICE))
+    client.post(f"/projects/{pid}/members",
+                json={"user_id": BOB, "role": "viewer", "private_reason": SENTINEL},
+                headers=_h(ALICE))
+    return p
+
+
+# rub_001 — viewer DELETE rejected AND project still exists
+def test_viewer_cannot_delete_project(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r = client.delete(f"/projects/{pid}", headers=_h(BOB))
+    assert r.status_code not in (200, 204)
+    r2 = client.get(f"/projects/{pid}", headers=_h(ALICE))
+    assert r2.status_code == 200
+
+
+# rub_002 — editor DELETE rejected AND project still exists
+def test_editor_cannot_delete_project(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r = client.delete(f"/projects/{pid}", headers=_h(CAROL))
+    assert r.status_code not in (200, 204)
+    r2 = client.get(f"/projects/{pid}", headers=_h(ALICE))
+    assert r2.status_code == 200
+
+
+# rub_003 — viewer archive rejected AND is_archived still false
+def test_viewer_cannot_archive_project(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r = client.post(f"/projects/{pid}/archive", headers=_h(BOB))
+    assert r.status_code not in (200, 201)
+    r2 = client.get(f"/projects/{pid}", headers=_h(ALICE))
+    assert r2.status_code == 200
+    assert r2.json()["is_archived"] is False
+
+
+# rub_004 — viewer add-member rejected AND member count unchanged
+def test_viewer_cannot_add_member(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    before = set(client.get(f"/projects/{pid}", headers=_h(ALICE)).json()["members"].keys())
+    r = client.post(f"/projects/{pid}/members",
+                    json={"user_id": "dave", "role": "viewer"},
+                    headers=_h(BOB))
+    assert r.status_code not in (200, 201)
+    after = set(client.get(f"/projects/{pid}", headers=_h(ALICE)).json()["members"].keys())
+    assert before == after
+
+
+# rub_005 — viewer change-role rejected AND target role unchanged
+def test_viewer_cannot_change_member_role(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r = client.patch(f"/projects/{pid}/members/{CAROL}",
+                     json={"role": "viewer"}, headers=_h(BOB))
+    assert r.status_code not in (200, 201)
+    r2 = client.get(f"/projects/{pid}", headers=_h(ALICE))
+    assert r2.json()["members"][CAROL] == "editor"
+
+
+# rub_006 — viewer remove-member rejected AND member still present
+def test_viewer_cannot_remove_member(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r = client.delete(f"/projects/{pid}/members/{CAROL}", headers=_h(BOB))
+    assert r.status_code not in (200, 204)
+    r2 = client.get(f"/projects/{pid}", headers=_h(ALICE))
+    assert CAROL in r2.json()["members"]
+
+
+# rub_007 — non-admin audit-log does NOT expose private_reason sentinel
+def test_non_admin_audit_log_hides_sentinel(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r = client.get(f"/projects/{pid}/audit-log", headers=_h(BOB))
+    assert SENTINEL not in r.text
+
+
+# rub_008 — self-promote laundering: viewer patches own role → still viewer AND DELETE fails
+def test_viewer_self_promote_then_delete_fails(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    client.patch(f"/projects/{pid}/members/{BOB}",
+                 json={"role": "admin"}, headers=_h(BOB))
+    r_check = client.get(f"/projects/{pid}", headers=_h(ALICE))
+    assert r_check.json()["members"][BOB] == "viewer"
+    r_del = client.delete(f"/projects/{pid}", headers=_h(BOB))
+    assert r_del.status_code not in (200, 204)
+
+
+# rub_009 — admin CAN delete project
+def test_admin_can_delete_project(client):
+    p = _project_with_roles(client)
+    r = client.delete(f"/projects/{p['id']}", headers=_h(ALICE))
+    assert r.status_code in (200, 204)
+
+
+# rub_010 — admin CAN archive AND is_archived becomes true
+def test_admin_can_archive_project(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r = client.post(f"/projects/{pid}/archive", headers=_h(ALICE))
+    assert r.status_code == 200
+    r2 = client.get(f"/projects/{pid}", headers=_h(ALICE))
+    assert r2.json()["is_archived"] is True
+
+
+# rub_011 — admin CAN add member AND member appears in GET
+def test_admin_can_add_member(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r = client.post(f"/projects/{pid}/members",
+                    json={"user_id": "dave", "role": "viewer"},
+                    headers=_h(ALICE))
+    assert r.status_code == 201
+    r2 = client.get(f"/projects/{pid}", headers=_h(ALICE))
+    assert "dave" in r2.json()["members"]
+
+
+# rub_012 — admin CAN change member role AND change reflected in GET
+def test_admin_can_change_member_role(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r = client.patch(f"/projects/{pid}/members/{BOB}",
+                     json={"role": "editor"}, headers=_h(ALICE))
+    assert r.status_code == 200
+    r2 = client.get(f"/projects/{pid}", headers=_h(ALICE))
+    assert r2.json()["members"][BOB] == "editor"
+
+
+# rub_013 — admin CAN read audit-log AND sentinel IS present
+def test_admin_can_read_audit_log_with_sentinel(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r = client.get(f"/projects/{pid}/audit-log", headers=_h(ALICE))
+    assert r.status_code == 200
+    assert SENTINEL in r.text
+
+
+# rub_014 — test_quality: sentinel sweep + state verification pattern
+def test_quality_sentinel_sweep_and_state_verification(client):
+    p = _project_with_roles(client)
+    pid = p["id"]
+    r_audit = client.get(f"/projects/{pid}/audit-log", headers=_h(BOB))
+    assert SENTINEL not in r_audit.text
+    client.delete(f"/projects/{pid}", headers=_h(BOB))
+    r_check = client.get(f"/projects/{pid}", headers=_h(ALICE))
+    assert r_check.status_code == 200
+    assert r_check.json()["name"] == "Test Project"
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
