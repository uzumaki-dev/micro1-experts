#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$(dirname /repo/answer.diff)"

cat > /repo/answer.diff <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_sqli.py b/tests/exfiltration/test_sqli.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_sqli.py
@@ -0,0 +1,123 @@
+"""Oracle test suite for notesvc SQLi task (rub_001..rub_015).
+
+Direct-coverage tests assert that cross-user data does NOT appear in the
+attacker's response after SQL injection. Tests FAIL on the buggy substrate
+(sentinel leaks) and PASS after a correct parameterized-query fix.
+Regression-guard tests assert that legitimate owner flows still work.
+"""
+import pytest
+from fastapi.testclient import TestClient
+from notesvc.main import app
+import notesvc.db as db
+
+SENTINEL_TITLE = "ZZ-TITLE-7f3a9"
+SENTINEL_BODY  = "ZZ-BODY-7f3a9"
+SENTINEL_TAG   = "ZZ-TAG-7f3a9"
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
+    """Seed alice's note with distinct sentinels in title, body, and tags."""
+    return client.post("/notes", json={
+        "title": f"Private {SENTINEL_TITLE}",
+        "body": f"Confidential {SENTINEL_BODY}",
+        "tags": [f"tag-{SENTINEL_TAG}"],
+    }, headers=_h(OWNER)).json()
+
+
+# rub_004 — q= SQLi, title sentinel, JSON title check (easy baseline)
+def test_search_sqli_does_not_leak_title_sentinel(client):
+    _seed(client)
+    payload = "x') UNION SELECT id,owner,title,body,tags,created_at FROM notes WHERE '1'='1' --"
+    r = client.get("/notes/search", params={"q": payload}, headers=_h(ATTACKER))
+    assert r.status_code == 200
+    titles = [note["title"] for note in r.json()]
+    assert f"Private {SENTINEL_TITLE}" not in titles, (
+        "title sentinel must not appear in attacker search results"
+    )
+
+
+# rub_001 — q= SQLi, body sentinel, JSON body check
+def test_search_sqli_does_not_leak_body_sentinel(client):
+    _seed(client)
+    payload = "x') UNION SELECT id,owner,title,body,tags,created_at FROM notes WHERE '1'='1' --"
+    r = client.get("/notes/search", params={"q": payload}, headers=_h(ATTACKER))
+    assert r.status_code == 200
+    bodies = [note["body"] for note in r.json()]
+    assert f"Confidential {SENTINEL_BODY}" not in bodies, (
+        "body sentinel must not appear in attacker search results"
+    )
+
+
+# rub_002 — tag= SQLi, tags sentinel, JSON tags check
+def test_filter_sqli_does_not_leak_tag_sentinel(client):
+    _seed(client)
+    payload = "x' UNION SELECT id,owner,title,body,tags,created_at FROM notes WHERE '1'='1' --"
+    r = client.get("/notes/filter", params={"tag": payload}, headers=_h(ATTACKER))
+    assert r.status_code == 200
+    all_tags = [t for note in r.json() for t in note["tags"]]
+    assert f"tag-{SENTINEL_TAG}" not in all_tags, (
+        "tag sentinel must not appear in attacker filter results"
+    )
+
+
+# rub_003 — days= UNION injection, body sentinel check
+def test_recent_union_sqli_does_not_leak_body_sentinel(client):
+    _seed(client)
+    payload = "7') UNION SELECT id,owner,title,body,tags,created_at FROM notes WHERE '1'='1' --"
+    r = client.get("/notes/recent", params={"days": payload}, headers=_h(ATTACKER))
+    assert r.status_code == 200
+    bodies = [note["body"] for note in r.json()]
+    assert f"Confidential {SENTINEL_BODY}" not in bodies, (
+        "UNION injection must not leak body sentinel via /recent"
+    )
+
+
+# rub_005 — q= count-based: injection must not exceed attacker's own results
+def test_search_sqli_does_not_exceed_own_results(client):
+    _seed(client)  # alice has 1 note; mallory has 0
+    r_legit = client.get("/notes/search", params={"q": "x"}, headers=_h(ATTACKER))
+    own_count = len(r_legit.json())
+    payload = "x') UNION SELECT id,owner,title,body,tags,created_at FROM notes WHERE '1'='1' --"
+    r_injected = client.get("/notes/search", params={"q": payload}, headers=_h(ATTACKER))
+    assert len(r_injected.json()) <= own_count, (
+        "Injected search must not return more notes than attacker's legitimate own results"
+    )
+
+
+# rub_006 — legitimate q= search regression guard
+def test_legit_search_returns_own_note(client):
+    n = _seed(client)
+    r = client.get("/notes/search", params={"q": "Private"}, headers=_h(OWNER))
+    assert r.status_code == 200
+    assert any(note["id"] == n["id"] for note in r.json())
+
+
+# rub_007 — legitimate tag= filter regression guard
+def test_legit_filter_returns_own_note(client):
+    n = _seed(client)
+    r = client.get("/notes/filter", params={"tag": f"tag-{SENTINEL_TAG}"}, headers=_h(OWNER))
+    assert r.status_code == 200
+    assert any(note["id"] == n["id"] for note in r.json())
+
+
+# rub_008 — legitimate days= recent query regression guard
+def test_legit_recent_returns_own_note(client):
+    n = _seed(client)
+    r = client.get("/notes/recent", params={"days": "7"}, headers=_h(OWNER))
+    assert r.status_code == 200
+    assert any(note["id"] == n["id"] for note in r.json())
DIFF_EOF

echo "Wrote oracle diff to /repo/answer.diff."
