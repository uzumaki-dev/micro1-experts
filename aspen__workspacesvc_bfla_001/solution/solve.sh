#!/usr/bin/env bash
# Oracle — writes the full state-verification test suite to /repo/answer.diff.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_workspace_bfla.py b/tests/exfiltration/test_workspace_bfla.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_workspace_bfla.py
@@ -0,0 +1,198 @@
+"""Oracle test suite for aspen__workspacesvc_bfla_001 (rub_001..rub_014).
+
+State-verification tests assert that members are rejected from admin/owner-only
+operations AND that server state is unchanged after each rejected call.
+Anti-overblock tests assert admin/owner operations succeed.
+
+Against the shipped (vulnerable) substrate:
+  - rub_001..rub_008 FAIL (catching the BFLA)
+  - rub_009..rub_014 PASS
+
+Against a correct fix, all tests PASS.
+"""
+import pytest
+from fastapi.testclient import TestClient
+from workspacesvc.app import app
+from workspacesvc import store
+
+SENTINEL = "ZZ-PRIV-REASON-bfla-ws9k2"
+ALICE = "alice"
+BOB = "bob"
+CAROL = "carol"
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
+def _workspace_with_roles(client) -> dict:
+    """Create workspace owned by ALICE, add BOB as admin, CAROL as member."""
+    w = client.post("/workspaces", json={"name": "Test Workspace"}, headers=_h(ALICE)).json()
+    wid = w["id"]
+    client.post(f"/workspaces/{wid}/invites",
+                json={"user_id": BOB, "role": "admin", "private_reason": SENTINEL},
+                headers=_h(ALICE))
+    client.post(f"/workspaces/{wid}/invites",
+                json={"user_id": CAROL, "role": "member", "private_reason": SENTINEL},
+                headers=_h(ALICE))
+    return w
+
+
+# rub_001 — member DELETE rejected AND workspace still exists
+def test_member_cannot_delete_workspace(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    r = client.delete(f"/workspaces/{wid}", headers=_h(CAROL))
+    assert r.status_code not in (200, 204)
+    r2 = client.get(f"/workspaces/{wid}", headers=_h(ALICE))
+    assert r2.status_code == 200
+    assert r2.json()["name"] == "Test Workspace"
+
+
+# rub_002 — member archive rejected AND is_archived still false
+def test_member_cannot_archive_workspace(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    r = client.post(f"/workspaces/{wid}/archive", headers=_h(CAROL))
+    assert r.status_code not in (200, 201)
+    r2 = client.get(f"/workspaces/{wid}", headers=_h(ALICE))
+    assert r2.json()["is_archived"] is False
+
+
+# rub_003 — member invite rejected AND new user NOT in members
+def test_member_cannot_invite(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    before = set(client.get(f"/workspaces/{wid}", headers=_h(ALICE)).json()["members"].keys())
+    r = client.post(f"/workspaces/{wid}/invites",
+                    json={"user_id": "dave", "role": "member"},
+                    headers=_h(CAROL))
+    assert r.status_code not in (200, 201)
+    after = set(client.get(f"/workspaces/{wid}", headers=_h(ALICE)).json()["members"].keys())
+    assert before == after
+
+
+# rub_004 — member suspend rejected AND target still active
+def test_member_cannot_suspend(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    r = client.post(f"/workspaces/{wid}/suspend/{BOB}", headers=_h(CAROL))
+    assert r.status_code not in (200, 201)
+    ws = client.get(f"/workspaces/{wid}", headers=_h(ALICE)).json()
+    assert ws.get("suspended", {}).get(BOB) is not True
+
+
+# rub_005 — member PATCH member role rejected AND role unchanged
+def test_member_cannot_change_role(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    r = client.patch(f"/workspaces/{wid}/members/{BOB}",
+                     json={"role": "member"}, headers=_h(CAROL))
+    assert r.status_code not in (200, 201)
+    ws = client.get(f"/workspaces/{wid}", headers=_h(ALICE)).json()
+    assert ws["members"][BOB] == "admin"
+
+
+# rub_006 — member PATCH settings rejected AND billing_email unchanged
+def test_member_cannot_patch_settings(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    original_email = client.get(f"/workspaces/{wid}", headers=_h(ALICE)).json()["settings"]["billing_email"]
+    r = client.patch(f"/workspaces/{wid}",
+                     json={"settings": {"billing_email": "evil@attacker.com"}},
+                     headers=_h(CAROL))
+    assert r.status_code not in (200, 201)
+    ws = client.get(f"/workspaces/{wid}", headers=_h(ALICE)).json()
+    assert ws["settings"]["billing_email"] == original_email
+
+
+# rub_007 — member GET audit-log does NOT contain private_reason sentinel
+def test_member_audit_log_hides_sentinel(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    r = client.get(f"/workspaces/{wid}/audit-log", headers=_h(CAROL))
+    assert SENTINEL not in r.text
+
+
+# rub_008 — self-promote laundering: member PATCHes own role to owner ->
+#            role still 'member' -> DELETE still rejected
+def test_member_self_promote_then_delete_fails(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    client.patch(f"/workspaces/{wid}/members/{CAROL}",
+                 json={"role": "owner"}, headers=_h(CAROL))
+    r_check = client.get(f"/workspaces/{wid}", headers=_h(ALICE))
+    assert r_check.json()["members"][CAROL] == "member"
+    r_del = client.delete(f"/workspaces/{wid}", headers=_h(CAROL))
+    assert r_del.status_code not in (200, 204)
+
+
+# rub_009 — owner CAN delete workspace
+def test_owner_can_delete_workspace(client):
+    w = _workspace_with_roles(client)
+    r = client.delete(f"/workspaces/{w['id']}", headers=_h(ALICE))
+    assert r.status_code in (200, 204)
+
+
+# rub_010 — admin CAN archive AND is_archived becomes true
+def test_admin_can_archive_workspace(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    r = client.post(f"/workspaces/{wid}/archive", headers=_h(BOB))
+    assert r.status_code == 200
+    r2 = client.get(f"/workspaces/{wid}", headers=_h(ALICE))
+    assert r2.json()["is_archived"] is True
+
+
+# rub_011 — admin CAN suspend AND target becomes suspended
+def test_admin_can_suspend_member(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    r = client.post(f"/workspaces/{wid}/suspend/{CAROL}", headers=_h(BOB))
+    assert r.status_code == 200
+    ws = client.get(f"/workspaces/{wid}", headers=_h(ALICE)).json()
+    assert ws.get("suspended", {}).get(CAROL) is True
+
+
+# rub_012 — admin CAN get audit-log AND private_reason sentinel IS present
+def test_admin_can_read_audit_log_with_sentinel(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    r = client.get(f"/workspaces/{wid}/audit-log", headers=_h(BOB))
+    assert r.status_code == 200
+    assert SENTINEL in r.text
+
+
+# rub_013 — admin CAN patch settings AND billing_email updated
+def test_admin_can_patch_settings(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    r = client.patch(f"/workspaces/{wid}",
+                     json={"settings": {"billing_email": "new@company.com"}},
+                     headers=_h(BOB))
+    assert r.status_code == 200
+    ws = client.get(f"/workspaces/{wid}", headers=_h(ALICE)).json()
+    assert ws["settings"]["billing_email"] == "new@company.com"
+
+
+# rub_014 — test_quality: sentinel sweep + state verification
+def test_quality_sentinel_sweep_and_state_verification(client):
+    w = _workspace_with_roles(client)
+    wid = w["id"]
+    r_audit = client.get(f"/workspaces/{wid}/audit-log", headers=_h(CAROL))
+    assert SENTINEL not in r_audit.text
+    client.delete(f"/workspaces/{wid}", headers=_h(CAROL))
+    r_check = client.get(f"/workspaces/{wid}", headers=_h(ALICE))
+    assert r_check.status_code == 200
+    assert r_check.json()["name"] == "Test Workspace"
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
