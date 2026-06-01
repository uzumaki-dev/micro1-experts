#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$(dirname /repo/answer.diff)"

cat > /repo/answer.diff <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_sqli.py b/tests/exfiltration/test_sqli.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_sqli.py
@@ -0,0 +1,106 @@
+"""Oracle test suite for notesvc SQLi task (rub_001..rub_012).
+
+Direct-coverage tests assert that a non-owner user does NOT receive another
+user's sentinel string in their response after SQL injection. Tests FAIL on
+the buggy substrate (sentinel leaks) and PASS after a correct fix.
+Regression-guard tests assert legitimate owner flows still work.
+"""
+import pytest
+from fastapi.testclient import TestClient
+from notesvc.main import app
+import notesvc.db as db
+
+SENTINEL = "ZZ-SQLI-7f3a9"
+OWNER    = "alice"
+ATTACKER = "mallory"
+
+
+@pytest.fixture(autouse=True)
+def _reset():
+    db.reset()
+    yield
+
+
+@pytest.fixture
+def client():
+    return TestClient(app)
+
+
+def _h(uid):
+    return {"X-User-Id": uid}
+
+
+def _seed(client):
+    """Create alice's note with sentinel seeded in title, body, and tags."""
+    return client.post("/notes", json={
+        "title": f"Private note {SENTINEL}",
+        "body": f"Confidential body {SENTINEL}",
+        "tags": [f"tag-{SENTINEL}"],
+    }, headers=_h(OWNER)).json()
+
+
+# rub_001 — q= SQLi: sentinel must be absent from attacker's raw response text
+def test_search_does_not_leak_sentinel_to_attacker(client):
+    _seed(client)
+    payload = "x') UNION SELECT id,owner,title,body,tags,created_at FROM notes WHERE '1'='1' --"
+    r = client.get("/notes/search", params={"q": payload}, headers=_h(ATTACKER))
+    assert r.status_code == 200
+    assert SENTINEL not in r.text, (
+        "q= SQLi leaked alice's sentinel to mallory — sentinel must not appear in attacker's response"
+    )
+
+
+# rub_002 — tag= SQLi: sentinel must be absent from attacker's raw response text
+def test_filter_does_not_leak_sentinel_to_attacker(client):
+    _seed(client)
+    payload = "x' UNION SELECT id,owner,title,body,tags,created_at FROM notes WHERE '1'='1' --"
+    r = client.get("/notes/filter", params={"tag": payload}, headers=_h(ATTACKER))
+    assert r.status_code == 200
+    assert SENTINEL not in r.text, (
+        "tag= SQLi leaked alice's sentinel to mallory — sentinel must not appear in attacker's response"
+    )
+
+
+# rub_003 — days= UNION SQLi: sentinel must be absent from attacker's raw response text
+def test_recent_does_not_leak_sentinel_to_attacker(client):
+    _seed(client)
+    payload = "7') UNION SELECT id,owner,title,body,tags,created_at FROM notes WHERE '1'='1' --"
+    r = client.get("/notes/recent", params={"days": payload}, headers=_h(ATTACKER))
+    assert r.status_code == 200
+    assert SENTINEL not in r.text, (
+        "days= UNION injection leaked alice's sentinel to mallory — sentinel must not appear in attacker's response"
+    )
+
+
+# rub_004 — q= count-based expansion (no sentinel required)
+def test_search_sqli_expands_result_set(client):
+    _seed(client)  # alice has 1 note; mallory has 0 notes
+    r_own = client.get("/notes", headers=_h(ATTACKER))
+    assert len(r_own.json()) == 0
+    payload = "x') UNION SELECT id,owner,title,body,tags,created_at FROM notes WHERE '1'='1' --"
+    r_injected = client.get("/notes/search", params={"q": payload}, headers=_h(ATTACKER))
+    assert len(r_injected.json()) > 0, "Injection must expand result set beyond mallory's own notes"
+
+
+# rub_005 — legitimate q= search regression guard
+def test_legit_search_returns_own_note(client):
+    n = _seed(client)
+    r = client.get("/notes/search", params={"q": "Private"}, headers=_h(OWNER))
+    assert r.status_code == 200
+    assert any(note["id"] == n["id"] for note in r.json())
+
+
+# rub_006 — legitimate tag= filter regression guard
+def test_legit_filter_returns_own_note(client):
+    n = _seed(client)
+    r = client.get("/notes/filter", params={"tag": f"tag-{SENTINEL}"}, headers=_h(OWNER))
+    assert r.status_code == 200
+    assert any(note["id"] == n["id"] for note in r.json())
+
+
+# rub_007 — legitimate days= recent query regression guard
+def test_legit_recent_returns_own_note(client):
+    n = _seed(client)
+    r = client.get("/notes/recent", params={"days": "7"}, headers=_h(OWNER))
+    assert r.status_code == 200
+    assert any(note["id"] == n["id"] for note in r.json())
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
